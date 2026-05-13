"""
抖音快捷键测试脚本 - 测试视频详情页和推荐页的快捷键交互
Usage:
  python test_shortcuts.py
  python test_shortcuts.py --help
"""

import argparse
import asyncio
from pathlib import Path
from patchright.async_api import async_playwright

WORKSPACE_DIR = Path(__file__).parent.parent


async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context(
            storage_state=str(WORKSPACE_DIR / "data" / "browser-sessions" / "account-1.json"),
            viewport={"width": 1440, "height": 900}
        )
        page = await ctx.new_page()
        page.set_default_timeout(15000)

        print("=== 视频详情页测试快捷键 ===")
        await page.goto("https://www.douyin.com", timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(5)

        try:
            rec_link = page.locator("a[href*='recommend=1']").first
            if await rec_link.count() > 0:
                await rec_link.click()
                await asyncio.sleep(5)
        except:
            pass

        cards = await page.query_selector_all("[class*='search-result']")
        if not cards:
            cards = await page.query_selector_all("a[href*='/video/']")

        if cards:
            for card in cards[:3]:
                try:
                    if await card.is_visible():
                        box = await card.bounding_box()
                        if box and box["width"] > 50:
                            await card.click()
                            await asyncio.sleep(5)
                            break
                except:
                    continue

        print(f"当前URL: {page.url}")
        is_detail = "/video/" in page.url
        print(f"是否视频详情页: {is_detail}")

        for key in ["z", "l"]:
            print(f"\n=== 测试按键 '{key}' 点赞 ===")
            like_el = await page.query_selector("[data-e2e='video-player-digg']")
            if like_el:
                before = await like_el.get_attribute("class") or ""
                video = await page.query_selector("video")
                if video:
                    vbox = await video.bounding_box()
                    if vbox:
                        await page.mouse.click(vbox["x"] + vbox["width"]/2, vbox["y"] + vbox["height"]/2)
                        await asyncio.sleep(0.5)
                await page.keyboard.press(key)
                await asyncio.sleep(1.5)
                after = await like_el.get_attribute("class") or ""
                if before != after:
                    print(f"  ✅ 按键 '{key}' 点赞成功！")
                    await page.keyboard.press(key)
                    await asyncio.sleep(1)
                else:
                    print(f"  ❌ 按键 '{key}' 点赞未生效")

        print("\n=== 推荐页双击视频点赞 ===")
        await page.goto("https://www.douyin.com/?recommend=1", timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(5)

        video = await page.query_selector("video")
        if video:
            vbox = await video.bounding_box()
            if vbox:
                vx = vbox["x"] + vbox["width"] / 2
                vy = vbox["y"] + vbox["height"] / 2
                like_el = await page.query_selector("[data-e2e='video-player-digg']")
                before = ""
                if like_el:
                    before = await like_el.get_attribute("class") or ""
                await page.mouse.dblclick(vx, vy)
                await asyncio.sleep(1.5)
                if like_el:
                    after = await like_el.get_attribute("class") or ""
                    if before != after:
                        print("  ✅ 双击视频点赞成功！")
                    else:
                        print("  ❌ 双击视频点赞未生效")

        await asyncio.sleep(3)
        await browser.close()


def main():
    parser = argparse.ArgumentParser(description="抖音快捷键测试脚本")
    parser.add_argument("--account", type=str, default="account-1", help="账号ID")
    args = parser.parse_args()
    asyncio.run(test())


if __name__ == "__main__":
    main()
