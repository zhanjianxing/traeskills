"""
抖音登录状态检测与续期脚本 — 基于 patchright + storage_state

功能：
1. 检测 storage_state 登录状态是否有效
2. 尝试自动续期（重新访问刷新Cookie）
3. 多账号批量检测
4. 与 douyin-publish.py 共享登录状态文件

使用方式：
  python douyin-cookie-check.py                          # 检测所有账号
  python douyin-cookie-check.py --account account-1      # 检测指定账号
  python douyin-cookie-check.py --renew                  # 尝试续期
  python douyin-cookie-check.py --login --account account-1  # 扫码登录
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from patchright.async_api import async_playwright

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("douyin-cookie-check")

WORKSPACE_DIR = Path(__file__).parent.parent
CREATOR_URL = "https://creator.douyin.com"
LOGIN_KEY_COOKIES = ["sessionid", "sessionid_ss", "sid_guard", "uid_tt", "uid_tt_ss"]


def _update_cookie_health(account_id: str, is_valid: bool):
    account_config_path = WORKSPACE_DIR / "data" / "accounts" / account_id / "account.json"
    if not account_config_path.exists():
        return
    try:
        with open(account_config_path, "r", encoding="utf-8") as f:
            account_config = json.load(f)
        account_config.setdefault("cookie_health", {})
        account_config["cookie_health"]["last_check"] = datetime.now().isoformat()
        account_config["cookie_health"]["is_valid"] = is_valid
        with open(account_config_path, "w", encoding="utf-8") as f:
            json.dump(account_config, f, ensure_ascii=False, indent=2)
        logger.info("Cookie健康状态已更新: %s → %s", account_id, "有效" if is_valid else "无效")
    except Exception as e:
        logger.warning("更新Cookie健康状态异常: %s", str(e))


def get_account_file(account_id: str) -> Path:
    return WORKSPACE_DIR / "data" / "browser-sessions" / f"{account_id}.json"


def get_all_accounts() -> list[str]:
    accounts_dir = WORKSPACE_DIR / "data" / "accounts"
    if not accounts_dir.exists():
        return []
    return [d.name for d in accounts_dir.iterdir() if d.is_dir() and (d / "account.json").exists()]


async def check_login_state(account_id: str) -> dict:
    account_file = get_account_file(account_id)
    result = {
        "account_id": account_id,
        "file_exists": account_file.exists(),
        "valid": False,
        "key_cookies": [],
        "age_hours": 0,
        "error": None,
    }

    if not account_file.exists():
        result["error"] = "登录状态文件不存在"
        return result

    try:
        file_stat = account_file.stat()
        result["age_hours"] = round((time.time() - file_stat.st_mtime) / 3600, 1)
    except Exception:
        pass

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                context = await browser.new_context(storage_state=str(account_file))
                page = await context.new_page()
                await page.goto(CREATOR_URL, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)

                page_content = await page.content()
                has_login_ui = "手机号登录" in page_content or "扫码登录" in page_content

                cookies = await context.cookies()
                cookie_names = {c["name"] for c in cookies}
                matched = [k for k in LOGIN_KEY_COOKIES if k in cookie_names]
                result["key_cookies"] = matched

                if not has_login_ui and len(matched) >= 2:
                    result["valid"] = True
                elif has_login_ui:
                    result["error"] = "登录已过期（页面显示登录按钮）"
                else:
                    result["error"] = f"关键Cookie不足（{len(matched)}/2）"
            finally:
                await browser.close()
    except Exception as e:
        result["error"] = f"检测异常: {str(e)}"

    return result


async def renew_login_state(account_id: str) -> bool:
    account_file = get_account_file(account_id)
    if not account_file.exists():
        logger.error("账号 %s 登录状态文件不存在，无法续期", account_id)
        return False

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                context = await browser.new_context(storage_state=str(account_file))
                page = await context.new_page()

                logger.info("访问创作者中心以刷新Cookie...")
                await page.goto(CREATOR_URL, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(5)

                page_content = await page.content()
                if "手机号登录" in page_content or "扫码登录" in page_content:
                    logger.error("登录已过期，无法续期，请重新扫码登录")
                    return False

                await context.storage_state(path=str(account_file))
                logger.info("登录状态已续期: %s", account_file)
                return True
            finally:
                await browser.close()
    except Exception as e:
        logger.error("续期异常: %s", str(e))
        return False


async def douyin_login(account_id: str, headless: bool = False) -> bool:
    account_file = get_account_file(account_id)
    account_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info("打开浏览器，请扫码登录（账号: %s）...", account_id)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = await context.new_page()

        try:
            await page.goto(CREATOR_URL, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(3)

            print("\n" + "=" * 60)
            print(f"  请在浏览器中扫码登录抖音（账号: {account_id}）")
            print("  登录成功后将自动保存")
            print("=" * 60 + "\n")

            login_detected = False
            for attempt in range(300):
                await asyncio.sleep(1)
                try:
                    current_url = page.url
                    if "creator.douyin.com" in current_url and "login" not in current_url.lower():
                        page_content = await page.content()
                        has_login_ui = any([
                            "手机号登录" in page_content,
                            "扫码登录" in page_content,
                        ])
                        if not has_login_ui:
                            cookies = await context.cookies()
                            cookie_names = {c["name"] for c in cookies}
                            matched = [k for k in LOGIN_KEY_COOKIES if k in cookie_names]
                            if len(matched) >= 2 or not has_login_ui:
                                logger.info("检测到登录成功！")
                                login_detected = True
                                break
                    if attempt % 10 == 0 and attempt > 0:
                        logger.info("等待扫码登录中...（已等待%d秒）", attempt)
                except Exception:
                    await asyncio.sleep(1)

            if login_detected:
                await asyncio.sleep(3)
                await context.storage_state(path=str(account_file))
                logger.info("登录状态已保存: %s", account_file)
                return True
            else:
                logger.error("等待登录超时")
                return False
        finally:
            await context.close()
            await browser.close()


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="抖音登录状态检测与续期（patchright + storage_state）")
    parser.add_argument("--account", type=str, help="指定账号ID")
    parser.add_argument("--all", action="store_true", help="检测所有账号")
    parser.add_argument("--login", action="store_true", help="扫码登录")
    parser.add_argument("--renew", action="store_true", help="尝试续期")
    parser.add_argument("--no-headless", action="store_true", help="显示浏览器窗口")

    args = parser.parse_args()

    if args.login:
        account_id = args.account or "account-1"
        success = await douyin_login(account_id, headless=not args.no_headless)
        sys.exit(0 if success else 1)

    if args.account:
        accounts = [args.account]
    elif args.all:
        accounts = get_all_accounts()
        if not accounts:
            logger.warning("未找到任何账号，请先在 data/accounts/ 下创建账号目录")
            sys.exit(1)
    else:
        accounts = get_all_accounts()
        if not accounts:
            accounts = ["account-1"]

    if args.renew:
        for account_id in accounts:
            logger.info("续期账号: %s", account_id)
            success = await renew_login_state(account_id)
            status = "成功" if success else "失败"
            logger.info("账号 %s 续期%s", account_id, status)
        return

    print("\n" + "=" * 60)
    print("  抖音登录状态检测报告")
    print("=" * 60)

    all_valid = True
    for account_id in accounts:
        result = await check_login_state(account_id)
        status = "有效" if result["valid"] else "无效"
        icon = "OK" if result["valid"] else "FAIL"

        print(f"\n  账号: {account_id}")
        print(f"  状态: {icon} {status}")
        print(f"  文件: {'存在' if result['file_exists'] else '不存在'}")
        if result["age_hours"] > 0:
            print(f"  保存时间: {result['age_hours']}小时前")
        if result["key_cookies"]:
            print(f"  关键Cookie: {', '.join(result['key_cookies'])}")
        if result["error"]:
            print(f"  错误: {result['error']}")

        if not result["valid"]:
            all_valid = False
            print(f"  修复: python douyin-cookie-check.py --login --account {account_id}")

        _update_cookie_health(account_id, result["valid"])

    print("\n" + "=" * 60)
    if all_valid:
        print("  所有账号登录状态正常")
    else:
        print("  部分账号需要重新登录")
    print("=" * 60 + "\n")

    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    asyncio.run(main())
