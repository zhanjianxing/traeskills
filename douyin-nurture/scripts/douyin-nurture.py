"""
抖音网页版自动养号脚本 — 基于 patchright + storage_state

通过 patchright（Playwright反检测分支）自动化操作 www.douyin.com，
模拟真人浏览、点赞、评论、关注、收藏等互动行为，提升账号活跃度和权重。

核心特性：
1. 使用 patchright 替代 playwright（内置反检测）
2. 使用 storage_state 保存/恢复登录状态（扫码一次，7-30天有效）
3. 页面状态检测引擎（锚点驱动，判断首页/播放页/搜索页/弹窗）
4. 视频切换验证（检测video.src是否真正变化）
5. 分类评论语料库（权重+模板填充+关键词感知）
6. 弹窗自动关闭（新手引导/广告弹窗）
7. 会话报告持久化（保存到analytics目录）
8. 优雅退出（Ctrl+C信号处理）
9. 日志文件输出（同时输出到console和文件）
10. 反检测增强（UA更新/视口随机化/行为参数化）
11. 互动重试机制（失败自动重试+多选择器降级）
12. 验证码检测与自动暂停
13. JSON结构化输出（agent可解析）
14. 自动恢复（页面异常时自动修复）

使用示例：
    # 默认配置运行（30分钟，点赞30%，评论10%，关注5%，收藏15%）
    python douyin-nurture.py --account account-1

    # 自定义时长和互动概率
    python douyin-nurture.py --account account-1 --duration 60 --like-prob 0.4

    # 指定偏好分类
    python douyin-nurture.py --account account-1 --categories "职场,美食,科技"

    # 调试模式（显示浏览器）
    python douyin-nurture.py --account account-1 --no-headless

    # 仅验证登录状态
    python douyin-nurture.py --account account-1 --verify-only

    # 诊断模式
    python douyin-nurture.py --account account-1 --diagnose

    # JSON输出（agent调用）
    python douyin-nurture.py --account account-1 --duration 5 --json-output
"""

import argparse
import asyncio
import json
import logging
import os
import random
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from patchright.async_api import async_playwright, Page, BrowserContext, TimeoutError as PlaywrightTimeoutError

WORKSPACE_DIR = Path(__file__).parent.parent
DOUYIN_URL = "https://www.douyin.com"
CREATOR_URL = "https://creator.douyin.com"
ELEMENT_TIMEOUT = 15000
NAVIGATION_TIMEOUT = 30000
LOGIN_KEY_COOKIES = ["sessionid", "sessionid_ss", "sid_guard", "uid_tt", "uid_tt_ss"]

INTERACTION_RETRY_COUNT = 3
INTERACTION_RETRY_DELAY = 2.0

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
]

VIEWPORTS = [
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
]

PAGE_ZOOM = 0.85

COMMENT_CORPUS = {
    "praise": {
        "weight": 30,
        "comments": [
            "太棒了！", "好厉害！", "学到了", "绝了", "太赞了",
            "这也太牛了吧", "厉害厉害", "高手在民间", "太强了",
            "真的绝了", "厉害了", "太有才了", "佩服佩服",
        ],
        "templates": ["{keyword}太厉害了", "这个{keyword}绝了", "{keyword}学到了"],
    },
    "emotion": {
        "weight": 20,
        "comments": [
            "感动到了", "看哭了", "太暖心了", "破防了",
            "泪目了", "太感人了", "心都化了",
        ],
        "templates": ["看{keyword}看哭了", "{keyword}破防了"],
    },
    "funny": {
        "weight": 20,
        "comments": [
            "哈哈哈笑死", "笑不活了", "太搞笑了",
            "笑出猪叫", "哈哈哈哈", "笑死我了", "太逗了",
        ],
        "templates": ["{keyword}笑死我了", "看{keyword}笑不活了"],
    },
    "curious": {
        "weight": 15,
        "comments": [
            "这是在哪里呀", "求教程", "怎么做到的", "求分享",
            "在哪买的", "什么牌子", "求链接", "怎么弄的",
        ],
        "templates": ["{keyword}怎么做到的", "求{keyword}教程"],
    },
    "agree": {
        "weight": 10,
        "comments": [
            "说得太对了", "深有同感", "就是就是", "没错没错",
            "赞同", "确实如此", "说到心坎里了",
        ],
        "templates": ["{keyword}说得太对了", "对{keyword}深有同感"],
    },
    "encourage": {
        "weight": 5,
        "comments": [
            "加油！", "继续努力", "支持你", "冲冲冲",
            "未来可期", "越来越好", "坚持住",
        ],
        "templates": [],
    },
    "serendipity": {
        "weight": 5,
        "comments": [
            "刷到了", "大数据推给我了", "缘分啊",
            "又刷到了", "首页推的", "推荐给我的",
        ],
        "templates": [],
    },
}

POPUP_DISMISS_TEXTS = ["我知道了", "关闭", "跳过", "下一步", "不再提示", "以后再说", "暂不"]

CAPTCHA_INDICATORS = [
    "[class*='captcha']", "[class*='slider-verify']",
    "[class*='puzzle-verify']", "[class*='verify-bar']",
    "[class*='captcha-verify']", "[class*='secsdk-captcha']",
    "iframe[src*='captcha']", "[class*='captcha_container']",
]

LIKE_SELECTORS = [
    "[data-e2e='video-player-digg']",
    "[data-e2e='feed-like-icon']",
    "[data-e2e='like-button']",
    "[class*='likeicon']",
    "[class*='digg']",
    "[class*='heart']",
    "[class*='praise']",
    "[class*='xgplayer-digg']",
]

COLLECT_SELECTORS = [
    "[data-e2e='video-player-collect']",
    "[data-e2e='feed-collect-icon']",
    "[data-e2e='collect-button']",
    "[class*='collecticon']",
    "[class*='star'] [class*='icon']",
    "[class*='bookmark'] [class*='icon']",
    "[class*='favorite'] [class*='icon']",
    "[class*='xgplayer-collect']",
]

COMMENT_BTN_SELECTORS = [
    "[data-e2e='feed-comment-icon']",
    "[data-e2e='video-player-comment']",
    "[data-e2e='comment-button']",
    "[class*='commenticon']",
    "[class*='comment'] [class*='icon']",
]

FOLLOW_SELECTORS = [
    "[data-e2e='feed-follow-icon']",
    "[data-e2e='follow-button']",
    "[class*='followicon']",
    "[class*='follow'] button",
    "[class*='controls-follow']",
]

SHARE_SELECTORS = [
    "[data-e2e='video-player-share']",
    "[data-e2e='feed-share-icon']",
    "[data-e2e='share-button']",
    "[class*='shareicon']",
]

NEXT_VIDEO_SELECTORS = [
    "[data-e2e='video-switch-next-arrow']",
    "[class*='switch-next']",
    "[class*='next-arrow']",
    "[class*='player-next']",
]

COMMENT_INPUT_SELECTORS = [
    "[class*='comment-input'] textarea",
    "[class*='comment'] textarea",
    "[class*='comment'] [contenteditable='true']",
    "textarea[placeholder*='评论']",
    "textarea[placeholder*='说点什么']",
    "[class*='comment'] input",
    "[contenteditable='true'][class*='editor']",
]

COMMENT_SEND_SELECTORS = [
    "[class*='comment'] button:has-text('发送')",
    "[class*='comment'] button:has-text('发布')",
    "button:has-text('发送')",
    "button:has-text('发布')",
    "[class*='submit']",
    "[class*='comment-send']",
]


def get_account_file(account_id: str) -> Path:
    return WORKSPACE_DIR / "data" / "browser-sessions" / f"{account_id}.json"


def get_log_dir(account_id: str) -> Path:
    log_dir = WORKSPACE_DIR / "data" / "logs" / account_id
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_analytics_dir(account_id: str) -> Path:
    analytics_dir = WORKSPACE_DIR / "data" / "accounts" / account_id / "analytics"
    analytics_dir.mkdir(parents=True, exist_ok=True)
    return analytics_dir


def setup_logging(account_id: str, log_level: str = "INFO") -> logging.Logger:
    log_dir = get_log_dir(account_id)
    log_file = log_dir / f"nurture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logger = logging.getLogger("douyin-nurture")
    logger.setLevel(getattr(logging, log_level))
    logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    console_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
    console_handler.setFormatter(console_fmt)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)

    logger.info("日志文件: %s", log_file)
    return logger


logger = logging.getLogger("douyin-nurture")


@dataclass
class NurtureConfig:
    account_id: str = "account-1"
    headless: bool = True
    duration: int = 30
    min_watch_time: int = 5
    max_watch_time: int = 30
    like_prob: float = 0.3
    comment_prob: float = 0.1
    follow_prob: float = 0.05
    collect_prob: float = 0.15
    share_prob: float = 0.03
    categories: list[str] = field(default_factory=lambda: ["生活", "美食", "旅行", "科技", "搞笑"])
    prefer_category_prob: float = 0.6
    min_action_delay: int = 1000
    max_action_delay: int = 5000
    pause_prob: float = 0.1
    pause_min_duration: int = 5000
    pause_max_duration: int = 20000
    scroll_back_prob: float = 0.05
    max_consecutive_likes: int = 5
    rest_after_max_likes: int = 60000
    max_likes_per_session: int = 50
    max_comments_per_session: int = 15
    max_follows_per_session: int = 8
    max_collects_per_session: int = 20
    max_shares_per_session: int = 5

    def __post_init__(self):
        if isinstance(self.categories, str):
            self.categories = [c.strip() for c in self.categories.split(",") if c.strip()]
        account_config_path = WORKSPACE_DIR / "data" / "accounts" / self.account_id / "account.json"
        if account_config_path.exists():
            with open(account_config_path, "r", encoding="utf-8") as f:
                account_config = json.load(f)
            nurture_cfg = account_config.get("nurture", {})
            if self.duration == 30:
                self.duration = nurture_cfg.get("duration_minutes", 30)
            if self.like_prob == 0.3:
                self.like_prob = nurture_cfg.get("like_prob", 0.3)
            if self.comment_prob == 0.1:
                self.comment_prob = nurture_cfg.get("comment_prob", 0.1)
            if self.follow_prob == 0.05:
                self.follow_prob = nurture_cfg.get("follow_prob", 0.05)
            if self.collect_prob == 0.15:
                self.collect_prob = nurture_cfg.get("collect_prob", 0.15)
            if self.categories == ["生活", "美食", "旅行", "科技", "搞笑"]:
                self.categories = nurture_cfg.get("categories", self.categories)


@dataclass
class SessionStats:
    is_running: bool = False
    start_time: float = 0.0
    end_time: float = 0.0
    videos_watched: int = 0
    videos_actually_switched: int = 0
    likes_given: int = 0
    likes_failed: int = 0
    comments_posted: int = 0
    comments_failed: int = 0
    follows_given: int = 0
    follows_failed: int = 0
    collects_given: int = 0
    collects_failed: int = 0
    shares_given: int = 0
    shares_failed: int = 0
    consecutive_likes: int = 0
    total_pause_time: int = 0
    popups_dismissed: int = 0
    exit_reason: str = ""
    errors_count: int = 0
    captcha_detected: int = 0
    page_states_detected: dict = field(default_factory=dict)
    interactions_detail: list = field(default_factory=list)


class PageStateDetector:
    HOME = "HOME"
    PLAYER = "PLAYER"
    SEARCH = "SEARCH"
    SEARCH_PLAYER = "SEARCH_PLAYER"
    POPUP = "POPUP"
    LOGIN = "LOGIN"
    CAPTCHA = "CAPTCHA"
    UNKNOWN = "UNKNOWN"

    @staticmethod
    async def detect(page: Page) -> str:
        try:
            anchors = await PageStateDetector._collect_anchors(page)
            return PageStateDetector._classify(anchors)
        except Exception as e:
            logger.debug("页面状态检测异常: %s", str(e))
            return PageStateDetector.UNKNOWN

    @staticmethod
    async def _collect_anchors(page: Page) -> dict:
        return await page.evaluate("""() => {
            const result = {
                url: window.location.href,
                title: document.title,
                video_count: document.querySelectorAll('video').length,
                card_count: document.querySelectorAll('[class*="video-card"], [class*="feed-card"], [class*="recommend-card"], [class*="discover-video-card"], [class*="jingxuanvideocard"], [class*="waterfall"], [class*="search-result-card"]').length,
                has_search_input: !!document.querySelector('input[placeholder*="搜索"], [class*="search"] input'),
                has_login_ui: !!(document.querySelector('[class*="login-button"]') || document.querySelector('[class*="login-btn"]')),
                has_popup_close: !!document.querySelector('[class*="modal"] [class*="close"], [class*="dialog"] [class*="close"], [class*="guide"] [class*="close"]'),
                has_comment_panel: !!document.querySelector('[class*="comment-list"], [class*="comment-panel"]'),
                has_like_button: !!document.querySelector('[data-e2e="video-player-digg"], [data-e2e="like-button"], [class*="digg"]'),
                has_follow_button: !!document.querySelector('[class*="follow"] button'),
                is_live: (() => {
                    const liveIndicators = [
                        '[class*="live"] [class*="badge"]',
                        '[class*="living"]',
                        '[class*="LiveRoom"]',
                        '[data-e2e="live-card"]',
                        '[class*="broadcast"]',
                    ];
                    for (const sel of liveIndicators) {
                        const el = document.querySelector(sel);
                        if (el && el.offsetParent !== null) return true;
                    }
                    const video = document.querySelector('video');
                    if (video) {
                        const src = video.src || '';
                        if (src.includes('live') || src.includes('flv') || src.includes('pull')) return true;
                        if (video.duration === Infinity || video.duration === 0) {
                            const container = video.closest('[class*="live"], [class*="LiveRoom"]');
                            if (container) return true;
                        }
                    }
                    return false;
                })(),
                has_captcha: (() => {
                    const iframes = document.querySelectorAll('iframe[src*="captcha"]');
                    for (const iframe of iframes) {
                        if (iframe.offsetParent === null) continue;
                        const rect = iframe.getBoundingClientRect();
                        if (rect.width < 100 || rect.height < 100) continue;
                        const parent = iframe.parentElement;
                        if (parent) {
                            const ps = getComputedStyle(parent);
                            const pz = parseInt(ps.zIndex) || 0;
                            if (pz >= 1000) return true;
                            if ((ps.position === 'fixed' || ps.position === 'absolute') && pz >= 100) return true;
                        }
                    }
                    const els = document.querySelectorAll('[class*="captcha-verify"], [class*="secsdk-captcha"], [class*="slider-verify"], [class*="puzzle-verify"]');
                    for (const el of els) {
                        if (el.offsetParent === null) continue;
                        const r = el.getBoundingClientRect();
                        if (r.width > 200 && r.height > 200) return true;
                    }
                    return false;
                })(),
            };
            try {
                const v = document.querySelector('video');
                result.video_src = v ? v.src : '';
                result.video_paused = v ? v.paused : true;
                result.video_ready = v ? v.readyState : 0;
            } catch(e) {
                result.video_src = '';
                result.video_paused = true;
                result.video_ready = 0;
            }
            return result;
        }""")

    @staticmethod
    def _classify(a: dict) -> str:
        url = a.get("url", "")
        title = a.get("title", "")
        vc = a.get("video_count", 0)
        cc = a.get("card_count", 0)
        has_login = a.get("has_login_ui", False)
        has_popup = a.get("has_popup_close", False)
        has_search = a.get("has_search_input", False)
        has_captcha = a.get("has_captcha", False)

        if has_captcha:
            return PageStateDetector.CAPTCHA

        if has_login:
            return PageStateDetector.LOGIN

        if has_popup and vc == 0:
            return PageStateDetector.POPUP

        if "/search" in url or "搜索" in title:
            if vc >= 1:
                return PageStateDetector.SEARCH_PLAYER
            return PageStateDetector.SEARCH

        if vc >= 1 and "/video/" in url:
            return PageStateDetector.PLAYER

        if cc > 0 or vc == 1:
            return PageStateDetector.HOME

        if vc >= 2:
            return PageStateDetector.PLAYER

        return PageStateDetector.UNKNOWN


class CommentEngine:
    def __init__(self, corpus: dict = None):
        self._corpus = corpus or COMMENT_CORPUS
        self._used_comments = []
        self._max_repeat = 3

    def get_comment(self, keyword: str = "") -> str:
        categories = []
        for cat_key, cat_data in self._corpus.items():
            weight = cat_data.get("weight", 0)
            if weight > 0:
                categories.append((cat_key, cat_data, weight))

        if not categories:
            return "👍"

        keys, datas, weights = zip(*categories)
        chosen_key = random.choices(keys, weights=weights, k=1)[0]
        chosen_data = datas[keys.index(chosen_key)]

        comments = chosen_data.get("comments", [])
        templates = chosen_data.get("templates", [])

        if templates and random.random() < 0.35:
            template = random.choice(templates)
            comment = template.format(keyword=keyword or "这个")
        elif comments:
            comment = random.choice(comments)
        elif templates:
            template = random.choice(templates)
            comment = template.format(keyword=keyword or "这个")
        else:
            comment = "👍"

        if random.random() < 0.3:
            emojis = ["😂", "👍", "❤️", "🔥", "👏", "💯", "✨", "😊", "🤣", "💪"]
            comment += random.choice(emojis)

        repeat_count = self._used_comments.count(comment)
        if repeat_count >= self._max_repeat and len(comments) > 1:
            for _ in range(5):
                alt = random.choice(comments)
                if self._used_comments.count(alt) < self._max_repeat:
                    comment = alt
                    break

        self._used_comments.append(comment)
        if len(self._used_comments) > 100:
            self._used_comments = self._used_comments[-50:]

        return comment


def random_int(min_val: int, max_val: int) -> int:
    return random.randint(min_val, max_val)


def random_float(min_val: float, max_val: float) -> float:
    return random.uniform(min_val, max_val)


def chance(probability: float) -> bool:
    return random.random() < probability


def format_duration(ms: int) -> str:
    seconds = ms // 1000
    minutes = seconds // 60
    secs = seconds % 60
    if minutes > 0:
        return f"{minutes}分{secs}秒"
    return f"{secs}秒"


def get_time_period() -> str:
    hour = datetime.now().hour
    if 6 <= hour < 9:
        return "early_morning"
    elif 9 <= hour < 12:
        return "morning"
    elif 12 <= hour < 14:
        return "noon"
    elif 14 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 22:
        return "evening"
    else:
        return "late_night"


def get_time_adjusted_delays() -> dict:
    period = get_time_period()
    adjustments = {
        "early_morning": {"delay_mult": 1.3, "pause_mult": 1.5},
        "morning": {"delay_mult": 1.0, "pause_mult": 1.0},
        "noon": {"delay_mult": 0.9, "pause_mult": 0.8},
        "afternoon": {"delay_mult": 1.0, "pause_mult": 1.0},
        "evening": {"delay_mult": 0.8, "pause_mult": 0.7},
        "late_night": {"delay_mult": 1.5, "pause_mult": 2.0},
    }
    return adjustments.get(period, {"delay_mult": 1.0, "pause_mult": 1.0})


async def cookie_auth(account_file: Path) -> bool:
    if not account_file.exists():
        logger.info("登录状态文件不存在: %s", account_file)
        return False
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                context = await browser.new_context(storage_state=str(account_file))
                page = await context.new_page()
                try:
                    await page.goto(CREATOR_URL, wait_until="domcontentloaded", timeout=30000)
                except PlaywrightTimeoutError:
                    await asyncio.sleep(3)
                await asyncio.sleep(5)
                page_content = await page.content()
                if "手机号登录" in page_content or "扫码登录" in page_content:
                    return False
                cookies = await context.cookies()
                cookie_names = {c["name"] for c in cookies}
                matched = [k for k in LOGIN_KEY_COOKIES if k in cookie_names]
                return len(matched) >= 2
            finally:
                await browser.close()
    except Exception as e:
        logger.warning("Cookie验证异常: %s", str(e))
        return False


async def ensure_login(account_id: str, headless: bool = False) -> Path:
    account_file = get_account_file(account_id)
    if await cookie_auth(account_file):
        logger.info("登录状态有效，使用已保存的状态")
        return account_file

    logger.warning("登录状态已失效或不存在，需要重新扫码登录")
    account_file.parent.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent=random.choice(USER_AGENTS),
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
                            if len(matched) >= 2:
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
                return account_file
            else:
                raise RuntimeError("等待登录超时")
        finally:
            await context.close()
            await browser.close()


class DouyinNurturer:
    def __init__(self, config: NurtureConfig):
        self.config = config
        self.stats = SessionStats()
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._account_file = None
        self._comment_engine = CommentEngine()
        self._shutdown_requested = False
        self._current_video_src = ""
        self._time_adjustments = get_time_adjusted_delays()
        self._json_output = False
        self._captcha_cooldown_until = 0

    def request_shutdown(self):
        logger.info("收到退出信号，正在优雅退出...")
        self._shutdown_requested = True
        self.stats.is_running = False
        self.stats.exit_reason = "用户手动退出"

    async def _init_browser(self):
        logger.info("初始化浏览器（patchright + storage_state）...")
        self._account_file = await ensure_login(self.config.account_id, headless=False)

        viewport = random.choice(VIEWPORTS)
        user_agent = random.choice(USER_AGENTS)
        logger.info("视口: %dx%d, UA: %s", viewport["width"], viewport["height"], user_agent[:60])

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.config.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-infobars",
                "--disable-extensions",
            ],
        )
        self._context = await self._browser.new_context(
            storage_state=str(self._account_file),
            viewport=viewport,
            user_agent=user_agent,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )
        self._page = await self._context.new_page()
        self._page.set_default_timeout(ELEMENT_TIMEOUT)
        self._page.set_default_navigation_timeout(NAVIGATION_TIMEOUT)
        logger.info("浏览器初始化完成（已加载登录状态）")

    async def _verify_login(self) -> bool:
        logger.info("验证登录状态...")
        try:
            if not await self._safe_goto(DOUYIN_URL):
                logger.error("导航到抖音首页失败")
                return False
            await asyncio.sleep(5)
            await self._dismiss_popups()

            state = await PageStateDetector.detect(self._page)
            if state == PageStateDetector.LOGIN:
                logger.error("登录验证失败：检测到登录页面")
                return False

            if state in (PageStateDetector.HOME, PageStateDetector.PLAYER,
                         PageStateDetector.SEARCH, PageStateDetector.SEARCH_PLAYER):
                logger.info("登录验证成功（页面状态: %s）", state)
                return True

            try:
                login_btn = await self._page.query_selector("[class*='login-button']")
                if login_btn:
                    is_visible = await login_btn.is_visible()
                    if is_visible:
                        logger.error("登录验证失败：检测到登录按钮")
                        return False
                logger.info("登录验证通过")
                return True
            except Exception:
                page_content = await self._page.content()
                if "登录" in page_content and "注册" in page_content:
                    logger.error("登录验证失败：检测到登录/注册按钮")
                    return False
                logger.info("登录验证通过（兜底）")
                return True
        except Exception as e:
            logger.error("登录验证异常: %s", str(e))
            return False

    async def _dismiss_popups(self):
        try:
            for text in POPUP_DISMISS_TEXTS:
                try:
                    btn = self._page.locator(f'button:has-text("{text}")').first
                    if await btn.count() > 0 and await btn.is_visible():
                        await btn.click()
                        await asyncio.sleep(0.3)
                        self.stats.popups_dismissed += 1
                        logger.info("关闭弹窗: %s", text)
                except Exception:
                    continue

            try:
                close_icons = await self._page.query_selector_all(
                    "[class*='modal'] [class*='close'], [class*='dialog'] [class*='close'], "
                    "[class*='guide'] [class*='close'], [class*='popup'] [class*='close']"
                )
                for icon in close_icons[:3]:
                    if await icon.is_visible():
                        await icon.click()
                        await asyncio.sleep(0.3)
                        self.stats.popups_dismissed += 1
                        logger.info("关闭弹窗图标")
            except Exception:
                pass

            await self._dismiss_guide_mask()
        except Exception as e:
            logger.debug("弹窗关闭异常: %s", str(e))

    async def _ensure_video_focus(self):
        try:
            await self._page.evaluate("""() => {
                const video = document.querySelector('video');
                if (video) {
                    video.click();
                    return;
                }
                const player = document.querySelector('[class*="xgplayer"], [class*="player-container"]');
                if (player) {
                    player.click();
                    return;
                }
                const slideItem = document.querySelector('[class*="slideItem"], [class*="feed-item"]');
                if (slideItem) {
                    slideItem.setAttribute('tabindex', '0');
                    slideItem.focus();
                }
            }""")
            await asyncio.sleep(0.3)
        except Exception:
            pass

    async def _detect_live(self) -> bool:
        try:
            return await self._page.evaluate("""() => {
                const liveIndicators = [
                    '[class*="live"] [class*="badge"]',
                    '[class*="living"]',
                    '[class*="LiveRoom"]',
                    '[data-e2e="live-card"]',
                    '[class*="broadcast"]',
                    '[class*="live-icon"]',
                ];
                for (const sel of liveIndicators) {
                    const el = document.querySelector(sel);
                    if (el && el.offsetParent !== null) return true;
                }
                const video = document.querySelector('video');
                if (video) {
                    const src = video.src || '';
                    if (src.includes('live') || src.includes('flv') || src.includes('pull')) return true;
                    if (!isFinite(video.duration) || video.duration === 0) {
                        const container = video.closest('[class*="live"], [class*="LiveRoom"], [class*="broadcast"]');
                        if (container) return true;
                    }
                }
                return false;
            }""")
        except Exception:
            return False

    async def _dismiss_guide_mask(self):
        try:
            mask = await self._page.query_selector(
                "[data-e2e='recommend-guide-mask'], #douyin-web-recommend-guide-mask"
            )
            if mask:
                is_visible = await mask.is_visible()
                if is_visible:
                    logger.info("检测到推荐引导遮罩，尝试关闭...")
                    try:
                        close_btn = await mask.query_selector(
                            "[class*='close'], [class*='dismiss'], button"
                        )
                        if close_btn:
                            await close_btn.click()
                            await asyncio.sleep(0.5)
                            logger.info("已关闭推荐引导遮罩（点击关闭按钮）")
                            self.stats.popups_dismissed += 1
                            return
                    except Exception:
                        pass
                    try:
                        await self._page.evaluate("""() => {
                            const mask = document.querySelector('[data-e2e="recommend-guide-mask"], #douyin-web-recommend-guide-mask');
                            if (mask) {
                                mask.style.display = 'none';
                                mask.style.pointerEvents = 'none';
                                mask.remove();
                            }
                        }""")
                        logger.info("已移除推荐引导遮罩（DOM移除）")
                        self.stats.popups_dismissed += 1
                    except Exception as e:
                        logger.debug("移除引导遮罩异常: %s", str(e))
        except Exception:
            pass

    async def _scroll_to_interaction_buttons(self):
        try:
            scroll_info = await self._page.evaluate("""() => {
                const video = document.querySelector('video');
                const digg = document.querySelector('[data-e2e="video-player-digg"]');
                if (!video) return null;
                const videoRect = video.getBoundingClientRect();
                const vh = window.innerHeight;
                const vw = window.innerWidth;
                
                let buttonInfo = null;
                if (digg) {
                    const diggRect = digg.getBoundingClientRect();
                    buttonInfo = {
                        visible: digg.offsetParent !== null,
                        y: diggRect.y,
                        height: diggRect.height,
                        inViewport: diggRect.y >= 0 && diggRect.y + diggRect.height <= vh
                    };
                }
                
                return {
                    videoY: videoRect.y,
                    videoHeight: videoRect.height,
                    videoTop: videoRect.top,
                    viewportHeight: vh,
                    viewportWidth: vw,
                    scrollY: window.scrollY,
                    buttonInfo: buttonInfo
                };
            }""")
            if not scroll_info:
                return
            
            video_y = scroll_info.get("videoY", 0)
            video_height = scroll_info.get("videoHeight", 0)
            vh = scroll_info.get("viewportHeight", 1200)
            
            # 检查视频是否在合理位置
            video_bottom = video_y + video_height
            # 如果视频已经在视口内大部分可见，不滚动
            if video_y >= -100 and video_bottom <= vh + 100:
                return
            
            # 如果视频位置偏离太多，适当调整，但不要滚得太猛
            if video_y > vh * 0.8:  # 视频在视口下方太多
                scroll_needed = -vh * 0.6  # 向上滚60%
                logger.info("视频在视口下方，向上滚动约%.0f像素", abs(scroll_needed))
                await self._page.evaluate(f"window.scrollBy(0, {scroll_needed})")
            elif video_bottom < vh * 0.2:  # 视频在视口上方太多
                scroll_needed = vh * 0.6  # 向下滚60%
                logger.info("视频在视口上方，向下滚动约%.0f像素", scroll_needed)
                await self._page.evaluate(f"window.scrollBy(0, {scroll_needed})")
            
            await asyncio.sleep(1.0)
                    
        except Exception as e:
            logger.debug("滚动到互动按钮异常: %s", str(e))

    async def _detect_captcha(self) -> bool:
        try:
            has_blocking_captcha = await self._page.evaluate("""() => {
                const iframes = document.querySelectorAll('iframe[src*="captcha"]');
                for (const iframe of iframes) {
                    if (iframe.offsetParent === null) continue;
                    const rect = iframe.getBoundingClientRect();
                    if (rect.width < 100 || rect.height < 100) continue;
                    const style = getComputedStyle(iframe);
                    if (style.display === 'none' || style.visibility === 'hidden') continue;
                    const parent = iframe.parentElement;
                    if (parent) {
                        const parentStyle = getComputedStyle(parent);
                        const parentZIndex = parseInt(parentStyle.zIndex) || 0;
                        if (parentZIndex >= 1000) return true;
                        if (parentStyle.position === 'fixed' || parentStyle.position === 'absolute') {
                            if (parentZIndex >= 100) return true;
                        }
                    }
                    const overlay = document.querySelector('[class*="captcha"] [class*="mask"], [class*="captcha"] [class*="overlay"], [class*="captcha"] [class*="backdrop"]');
                    if (overlay && overlay.offsetParent !== null) return true;
                }
                const captchaEls = document.querySelectorAll('[class*="captcha-verify"], [class*="secsdk-captcha"], [class*="slider-verify"], [class*="puzzle-verify"]');
                for (const el of captchaEls) {
                    if (el.offsetParent === null) continue;
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 200 && rect.height > 200) return true;
                }
                return false;
            }""")
            if has_blocking_captcha:
                logger.warning("⚠️ 检测到阻塞式验证码")
                self.stats.captcha_detected += 1
                return True
            return False
        except Exception:
            return False

    async def _handle_captcha(self):
        logger.warning("⚠️ 检测到验证码，暂停操作等待冷却...")
        self._captcha_cooldown_until = time.time() + 120
        await self._take_screenshot("captcha_detected")
        cooldown = random_float(30.0, 60.0)
        logger.info("验证码冷却 %.0f 秒，期间仅浏览不互动", cooldown)
        await asyncio.sleep(cooldown)

    async def _detect_page_state(self) -> str:
        state = await PageStateDetector.detect(self._page)
        self.stats.page_states_detected[state] = self.stats.page_states_detected.get(state, 0) + 1
        return state

    async def _get_video_src(self) -> str:
        try:
            src = await self._page.evaluate(
                "() => { const v = document.querySelector('video'); return v ? v.src : ''; }"
            )
            return src or ""
        except Exception:
            return ""

    async def _verify_video_switched(self, before_src: str) -> bool:
        await asyncio.sleep(random_float(1.5, 3.0))
        after_src = await self._get_video_src()
        if after_src and before_src and after_src != before_src:
            logger.debug("视频已切换（src变化确认）")
            return True

        await asyncio.sleep(1.0)
        after_src2 = await self._get_video_src()
        if after_src2 and before_src and after_src2 != before_src:
            logger.debug("视频已切换（二次确认）")
            return True

        try:
            current_time = await self._get_video_current_time()
            duration = await self._get_video_duration()
            if current_time is not None and current_time < 3.0 and duration and duration > 5:
                logger.debug("视频已切换（播放时间<3s且时长>5s，说明是新视频）")
                return True
        except Exception:
            pass

        try:
            result = await self._page.evaluate("""() => {
                const video = document.querySelector('video');
                if (!video) return {switched: false};
                const ct = video.currentTime;
                const d = video.duration;
                const paused = video.paused;
                const ready = video.readyState;
                const src = video.src || '';
                return {
                    switched: (ct < 3 && d > 5 && ready >= 2) || (!paused && ct < 5 && d > 10),
                    currentTime: ct,
                    duration: d,
                    paused: paused,
                    readyState: ready,
                    srcChanged: src !== '',
                };
            }""")
            if result.get("switched"):
                logger.debug("视频已切换（JS检测确认: ct=%.1f, d=%.1f, ready=%d）",
                            result.get("currentTime", 0), result.get("duration", 0), result.get("readyState", 0))
                return True
        except Exception:
            pass

        logger.debug("视频未切换")
        return False

    async def _random_delay(self, min_ms: int = None, max_ms: int = None):
        min_ms = min_ms or self.config.min_action_delay
        max_ms = max_ms or self.config.max_action_delay
        delay = random_int(min_ms, max_ms) / 1000.0
        delay *= self._time_adjustments["delay_mult"]
        delay = max(0.3, delay + random_float(-0.05, 0.05))
        logger.debug("随机延迟 %.1f 秒", delay)
        await asyncio.sleep(delay)

    async def _random_mouse_move(self):
        viewport = self._page.viewport_size
        max_x = (viewport or {"width": 1920})["width"] - 100
        max_y = (viewport or {"height": 1080})["height"] - 100
        x = random_int(100, max(200, max_x))
        y = random_int(100, max(200, max_y))
        steps = random_int(5, 15)
        await self._page.mouse.move(x, y, steps=steps)
        logger.debug("随机鼠标移动到 (%d, %d)", x, y)

    async def _random_scroll(self, direction: str = "down", distance: int = None):
        if distance is None:
            distance = random_int(200, 600)
        await self._random_mouse_move()
        delta_y = distance if direction == "down" else -distance
        await self._page.mouse.wheel(0, delta_y)
        logger.debug("随机滚动 %s %d 像素", direction, distance)
        await asyncio.sleep(random_float(0.3, 0.8))

    async def _maybe_pause(self):
        if chance(self.config.pause_prob * self._time_adjustments["pause_mult"]):
            pause_ms = random_int(self.config.pause_min_duration, self.config.pause_max_duration)
            pause_sec = (pause_ms / 1000.0) * self._time_adjustments["pause_mult"]
            logger.info("随机暂停 %.1f 秒（模拟发呆）", pause_sec)
            await asyncio.sleep(pause_sec)
            self.stats.total_pause_time += pause_ms

    async def _take_screenshot(self, label: str) -> Optional[str]:
        try:
            ss_dir = WORKSPACE_DIR / "data" / "screenshots" / self.config.account_id
            ss_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%H%M%S")
            path = str(ss_dir / f"{label}_{ts}.png")
            await self._page.screenshot(path=path, full_page=False)
            logger.info("截图已保存: %s", path)
            return path
        except Exception as e:
            logger.debug("截图失败: %s", str(e))
            return None

    async def _diagnose_page(self, context: str = "") -> dict:
        try:
            result = await self._page.evaluate("""() => {
                const info = {
                    url: window.location.href,
                    title: document.title,
                    video_count: document.querySelectorAll('video').length,
                    viewport: { width: window.innerWidth, height: window.innerHeight },
                };
                const e2eButtons = ['video-player-digg', 'feed-comment-icon',
                    'video-player-collect', 'video-player-share',
                    'feed-follow-icon', 'video-switch-next-arrow',
                    'video-desc', 'video-avatar', 'feed-active-video',
                    'feed-like-icon', 'feed-collect-icon', 'feed-share-icon',
                    'like-button', 'collect-button', 'follow-button',
                    'comment-button', 'share-button'];
                info.buttons = {};
                for (const name of e2eButtons) {
                    const el = document.querySelector(`[data-e2e="${name}"]`);
                    info.buttons[name] = el ? {
                        exists: true,
                        visible: el.offsetParent !== null,
                        rect: (() => { const r = el.getBoundingClientRect();
                            return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)};
                        })()
                    } : { exists: false };
                }
                const sideButtons = document.querySelectorAll('[class*="xgplayer"] [class*="digg"], [class*="xgplayer"] [class*="collect"], [class*="xgplayer"] [class*="share"]');
                info.side_button_count = sideButtons.length;
                const rightPanel = document.querySelector('[class*="video-player"] [class*="sidebar"], [class*="player"] [class*="sidebar"], [class*="xgplayer"] [class*="sidebar"]');
                info.has_right_sidebar = !!rightPanel;
                return info;
            }""")
            if context:
                logger.info("诊断[%s]: url=%s, videos=%d, viewport=%dx%d",
                            context, result.get("url", "")[:50], result.get("video_count", 0),
                            result.get("viewport", {}).get("width", 0),
                            result.get("viewport", {}).get("height", 0))
                for name, status in result.get("buttons", {}).items():
                    if status.get("exists"):
                        vis = "V" if status.get("visible") else "X"
                        r = status.get("rect", {})
                        logger.debug("  %s %s: (%d,%d,%d,%d)", vis, name,
                                     r.get("x", 0), r.get("y", 0), r.get("w", 0), r.get("h", 0))
            return result
        except Exception as e:
            logger.debug("页面诊断异常: %s", str(e))
            return {"error": str(e)}

    async def _find_visible_element(self, selectors: list[str], timeout: int = 5000) -> Optional[object]:
        for selector in selectors:
            try:
                elements = await self._page.query_selector_all(selector)
                for element in elements:
                    try:
                        is_visible = await element.is_visible()
                        if not is_visible:
                            continue
                        box = await element.bounding_box()
                        if not box:
                            continue
                        if box["width"] < 5 or box["height"] < 5:
                            continue
                        return element
                    except Exception:
                        continue
            except Exception:
                continue
        for selector in selectors:
            try:
                element = await self._page.wait_for_selector(selector, timeout=timeout)
                if not element:
                    continue
                is_visible = await element.is_visible()
                if not is_visible:
                    continue
                box = await element.bounding_box()
                if not box:
                    continue
                if box["width"] < 5 or box["height"] < 5:
                    continue
                return element
            except PlaywrightTimeoutError:
                continue
            except Exception:
                continue
        return None

    async def _wait_for_interaction_ready(self, timeout: float = 10.0) -> bool:
        try:
            start = time.time()
            while time.time() - start < timeout:
                result = await self._page.evaluate("""() => {
                    const selectors = [
                        '[data-e2e="video-player-digg"]', '[data-e2e="feed-like-icon"]',
                        '[data-e2e="like-button"]', '[class*="digg"]',
                        '[data-e2e="video-player-collect"]', '[data-e2e="feed-collect-icon"]',
                        '[data-e2e="collect-button"]', '[class*="collecticon"]',
                    ];
                    for (const sel of selectors) {
                        const el = document.querySelector(sel);
                        if (el && el.offsetParent !== null) {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 5 && rect.height > 5) {
                                return true;
                            }
                        }
                    }
                    return false;
                }""")
                if result:
                    logger.debug("互动按钮已就绪")
                    return True
                await asyncio.sleep(0.5)
            logger.debug("等待互动按钮超时(%.0fs)", timeout)
            return False
        except Exception:
            return False

    async def _human_click(self, selector: str, timeout: int = 5000) -> bool:
        try:
            element = await self._page.wait_for_selector(selector, timeout=timeout)
            if not element:
                return False
            try:
                await element.scroll_into_view_if_needed(timeout=3000)
            except Exception:
                pass
            is_visible = await element.is_visible()
            if not is_visible:
                return False
            box = await element.bounding_box()
            if not box:
                return False

            await self._dismiss_guide_mask()

            x = box["x"] + box["width"] / 2
            y = box["y"] + box["height"] / 2
            await self._page.mouse.move(
                x + random_int(-5, 5),
                y + random_int(-5, 5),
                steps=random_int(5, 10),
            )
            await asyncio.sleep(random_float(0.08, 0.25))
            await self._page.mouse.click(x, y)
            logger.debug("人类点击: %s (%.0f, %.0f)", selector, x, y)
            return True
        except PlaywrightTimeoutError:
            logger.debug("点击超时: %s", selector)
            return False
        except Exception as e:
            logger.debug("点击异常: %s - %s", selector, str(e))
            return False

    async def _human_click_element(self, element, label: str = "") -> bool:
        try:
            is_visible = await element.is_visible()
            if not is_visible:
                return False
            box = await element.bounding_box()
            if not box:
                return False

            await self._dismiss_guide_mask()

            vh = (self._page.viewport_size or {}).get("height", 1080)
            vw = (self._page.viewport_size or {}).get("width", 1920)
            in_viewport = (box["y"] >= 0 and box["y"] + box["height"] <= vh and
                          box["x"] >= 0 and box["x"] + box["width"] <= vw)

            if in_viewport:
                x = box["x"] + box["width"] / 2
                y = box["y"] + box["height"] / 2
                await self._page.mouse.move(
                    x + random_int(-3, 3),
                    y + random_int(-3, 3),
                    steps=random_int(3, 8),
                )
                await asyncio.sleep(random_float(0.1, 0.3))
                await self._page.mouse.click(x, y)
                logger.debug("人类点击元素: %s (%.0f, %.0f)", label, x, y)
                return True
            else:
                await element.dispatch_event("click")
                logger.debug("dispatch_event点击(视口外): %s", label)
                return True
        except Exception as e:
            logger.debug("点击元素异常: %s - %s", label, str(e))
            try:
                await element.dispatch_event("click")
                logger.debug("dispatch_event备选点击: %s", label)
                return True
            except Exception as e2:
                logger.debug("dispatch_event也失败: %s - %s", label, str(e2))
                return False

    async def _safe_goto(self, url: str) -> bool:
        try:
            await self._page.goto(url, timeout=NAVIGATION_TIMEOUT, wait_until="domcontentloaded")
            return True
        except Exception:
            pass
        try:
            await self._page.evaluate(f"window.location.href = '{url}'")
            await asyncio.sleep(3)
            return True
        except Exception:
            pass
        try:
            await self._page.goto(url, timeout=NAVIGATION_TIMEOUT, wait_until="commit")
            return True
        except Exception:
            return False

    async def _navigate_to_feed(self):
        logger.info("导航到抖音推荐页...")
        try:
            recommend_clicked = False
            try:
                recommend_link = self._page.locator("a[href*='recommend=1']").first
                if await recommend_link.count() > 0 and await recommend_link.is_visible():
                    await recommend_link.click()
                    recommend_clicked = True
                    logger.info("点击推荐导航链接")
                    await asyncio.sleep(5)
            except Exception:
                pass

            if not recommend_clicked:
                if not await self._safe_goto("https://www.douyin.com/?recommend=1"):
                    if not await self._safe_goto(DOUYIN_URL):
                        logger.error("导航到抖音首页失败")
                        return
                await asyncio.sleep(5)

            await self._dismiss_popups()

            try:
                await self._page.evaluate(f"""() => {{
                    document.body.style.zoom = '{PAGE_ZOOM}';
                }}""")
                logger.debug("页面缩放设置为%.0f%%", PAGE_ZOOM * 100)
            except Exception:
                pass

            current_url = self._page.url
            if "/recommend" in current_url or "recommend=1" in current_url:
                logger.info("已在推荐页")
                return

            tab_selectors = [
                "a[href*='recommend=1']",
                "[data-e2e='alink-item']:has-text('推荐')",
                "a:has-text('推荐')",
            ]
            for selector in tab_selectors:
                try:
                    if await self._human_click(selector, timeout=3000):
                        logger.info("已切换到推荐页")
                        await asyncio.sleep(3)
                        return
                except Exception:
                    continue
            logger.info("未找到推荐标签，继续当前页面")
        except Exception as e:
            logger.error("导航到推荐页异常: %s", str(e))

    async def _search_category(self, category: str) -> bool:
        logger.info("搜索分类: %s", category)
        try:
            search_selectors = [
                "[class*='search'] input",
                "input[placeholder*='搜索']",
                "[class*='search-input']",
                "[class*='search'] [class*='input']",
            ]
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = await self._page.wait_for_selector(selector, timeout=3000)
                    if search_input:
                        is_visible = await search_input.is_visible()
                        if is_visible:
                            break
                        search_input = None
                except PlaywrightTimeoutError:
                    continue

            if not search_input:
                search_icon_selectors = [
                    "[class*='search-icon']",
                    "[class*='search-btn']",
                    "button:has(svg)",
                ]
                for selector in search_icon_selectors:
                    if await self._human_click(selector, timeout=2000):
                        await asyncio.sleep(1)
                        for s in search_selectors:
                            try:
                                search_input = await self._page.wait_for_selector(s, timeout=3000)
                                if search_input:
                                    break
                            except PlaywrightTimeoutError:
                                continue
                        if search_input:
                            break

            if not search_input:
                logger.warning("未找到搜索输入框，跳过分类搜索")
                return False

            await search_input.click()
            await asyncio.sleep(random_float(0.3, 0.6))
            await search_input.fill("")
            await asyncio.sleep(random_float(0.2, 0.4))

            for char in category:
                await self._page.keyboard.type(char, delay=random_int(80, 200))

            await asyncio.sleep(random_float(0.5, 1.0))
            await self._page.keyboard.press("Enter")
            await asyncio.sleep(random_float(2.0, 3.0))

            await self._dismiss_popups()

            video_tab_selectors = [
                "text=视频",
                "[class*='tab'] >> text=视频",
                "a:has-text('视频')",
            ]
            for selector in video_tab_selectors:
                try:
                    if await self._human_click(selector, timeout=2000):
                        await asyncio.sleep(1)
                        break
                except Exception:
                    continue

            logger.info("分类搜索完成: %s", category)
            return True
        except Exception as e:
            logger.warning("搜索分类失败: %s - %s", category, str(e))
            return False

    async def _scroll_to_next_video(self) -> bool:
        before_src = await self._get_video_src()

        switched = False

        # 方法1：用ArrowDown键切换视频（最像真人）
        try:
            await self._ensure_video_focus()
            await asyncio.sleep(random_float(0.2, 0.5))
            await self._page.keyboard.press("ArrowDown")
            await asyncio.sleep(random_float(2.5, 4.0))
            switched = await self._verify_video_switched(before_src)
        except Exception:
            pass

        # 方法2：如果ArrowDown失败，尝试点击下一个视频按钮
        if not switched:
            next_el = await self._find_visible_element(NEXT_VIDEO_SELECTORS, timeout=2000)
            if next_el:
                try:
                    cls = await next_el.get_attribute("class") or ""
                    if "disabled" not in cls:
                        await self._dismiss_guide_mask()
                        box = await next_el.bounding_box()
                        if box:
                            x = box["x"] + box["width"] / 2
                            y = box["y"] + box["height"] / 2
                            await self._page.mouse.move(x, y, steps=random_int(4, 8))
                            await asyncio.sleep(random_float(0.3, 0.7))
                            await self._page.mouse.click(x, y)
                            await asyncio.sleep(random_float(2.5, 4.0))
                            switched = await self._verify_video_switched(before_src)
                            if not switched:
                                await next_el.dispatch_event("click")
                                await asyncio.sleep(random_float(2.0, 3.0))
                                switched = await self._verify_video_switched(before_src)
                except Exception as e:
                    logger.debug("点击切换按钮异常: %s", str(e))

        # 方法3：如果还没切换，尝试用滚轮向下滚动
        if not switched:
            try:
                await self._page.mouse.wheel(0, 600)
                await asyncio.sleep(random_float(2.5, 4.0))
                switched = await self._verify_video_switched(before_src)
            except Exception:
                pass

        if switched:
            self.stats.videos_actually_switched += 1
            self._current_video_src = await self._get_video_src()
            logger.info("切换到下一个视频")
        else:
            logger.debug("视频切换未成功")

        return switched

    async def _scroll_back(self):
        await self._random_mouse_move()
        distance = random_int(100, 300)
        await self._page.mouse.wheel(0, -distance)
        await asyncio.sleep(random_float(1.0, 3.0))
        logger.info("回滚查看（模拟犹豫行为）")

    async def _click_into_video(self) -> bool:
        try:
            await self._random_scroll("down", random_int(100, 300))
            await asyncio.sleep(random_float(0.5, 1.0))

            video_selectors = [
                "[class*='search-result-card']",
                "[class*='discover-video-card']",
                "[class*='jingxuanvideocard']",
                "[class*='waterfall']",
                "[class*='video-card']",
                "[class*='feed-card']",
                "[class*='recommend-card']",
                "[class*='video-item']",
                "a[href*='/video/']",
                "[class*='cover']",
            ]
            for selector in video_selectors:
                try:
                    elements = await self._page.query_selector_all(selector)
                    if not elements:
                        continue

                    visible_elements = []
                    for el in elements:
                        try:
                            if await el.is_visible():
                                box = await el.bounding_box()
                                if box and box["width"] > 50 and box["height"] > 50:
                                    visible_elements.append((el, box))
                        except Exception:
                            continue

                    if not visible_elements:
                        continue

                    idx = random_int(0, min(len(visible_elements) - 1, 4))
                    element, box = visible_elements[idx]

                    try:
                        await element.scroll_into_view_if_needed(timeout=2000)
                    except Exception:
                        pass

                    box = await element.bounding_box()
                    if not box:
                        continue

                    x = box["x"] + box["width"] / 2
                    y = box["y"] + box["height"] / 2
                    await self._page.mouse.move(x, y, steps=random_int(5, 10))
                    await asyncio.sleep(random_float(0.2, 0.5))
                    await self._page.mouse.click(x, y)
                    await asyncio.sleep(random_float(2.0, 4.0))
                    await self._dismiss_popups()

                    state = await self._detect_page_state()
                    if state in (PageStateDetector.PLAYER, PageStateDetector.SEARCH_PLAYER):
                        logger.info("已点击进入视频详情页（状态: %s）", state)
                        self._current_video_src = await self._get_video_src()
                        return True
                except Exception:
                    continue
            logger.warning("未找到可点击的视频卡片")
            return False
        except Exception as e:
            logger.warning("点击视频异常: %s", str(e))
            return False

    async def _is_in_video_detail(self) -> bool:
        state = await self._detect_page_state()
        return state in (PageStateDetector.PLAYER, PageStateDetector.SEARCH_PLAYER)

    async def _exit_video_detail(self):
        try:
            back_selectors = [
                "[class*='back']",
                "[class*='close']",
                "button[aria-label='返回']",
                "svg[class*='back']",
            ]
            for selector in back_selectors:
                if await self._human_click(selector, timeout=2000):
                    await asyncio.sleep(random_float(1.0, 2.0))
                    if not await self._is_in_video_detail():
                        logger.debug("已退出视频详情页")
                        return
            await self._page.go_back()
            await asyncio.sleep(random_float(1.0, 2.0))
            logger.debug("通过浏览器后退退出视频详情页")
        except Exception as e:
            logger.warning("退出视频详情页异常: %s", str(e))
            await self._safe_goto(DOUYIN_URL)
            await asyncio.sleep(2)

    async def _like_video(self) -> bool:
        if self.stats.likes_given >= self.config.max_likes_per_session:
            logger.info("已达到单次点赞上限: %d/%d", self.stats.likes_given, self.config.max_likes_per_session)
            return False
        if self.stats.consecutive_likes >= self.config.max_consecutive_likes:
            rest_sec = self.config.rest_after_max_likes / 1000.0
            logger.info("连续点赞达到上限，休息 %.1f 秒", rest_sec)
            await asyncio.sleep(rest_sec)
            self.stats.consecutive_likes = 0
            self.stats.total_pause_time += self.config.rest_after_max_likes

        element = await self._find_visible_element(LIKE_SELECTORS, timeout=3000)
        if not element:
            logger.debug("点赞按钮未找到")
            self.stats.likes_failed += 1
            return False

        try:
            before_class = await element.get_attribute("class") or ""
            before_aria = await element.get_attribute("aria-label") or ""

            await self._ensure_video_focus()
            await asyncio.sleep(random_float(0.2, 0.5))
            await self._page.keyboard.press("z")
            await asyncio.sleep(random_float(0.8, 1.5))

            after_class = await element.get_attribute("class") or ""
            after_aria = await element.get_attribute("aria-label") or ""

            liked = (after_class != before_class or
                     "active" in after_class.lower() or
                     after_aria != before_aria)

            if not liked:
                await self._human_click_element(element, "like")
                await asyncio.sleep(random_float(0.5, 1.0))
                after_class = await element.get_attribute("class") or ""
                after_aria = await element.get_attribute("aria-label") or ""
                liked = (after_class != before_class or after_aria != before_aria)

            self.stats.likes_given += 1
            self.stats.consecutive_likes += 1
            if liked:
                logger.info("V 点赞成功（第 %d 次，状态已变化）", self.stats.likes_given)
            else:
                logger.info("点赞操作完成（第 %d 次，状态变化未确认）", self.stats.likes_given)

            self.stats.interactions_detail.append({
                "type": "like", "success": True, "verified": liked,
                "timestamp": datetime.now().isoformat(),
            })
            await asyncio.sleep(random_float(0.3, 0.8))
            return True
        except Exception as e:
            logger.debug("点赞异常: %s", str(e))
            self.stats.likes_failed += 1
            return False

    async def _comment_video(self) -> bool:
        if self.stats.comments_posted >= self.config.max_comments_per_session:
            logger.info("已达到单次评论上限: %d/%d", self.stats.comments_posted, self.config.max_comments_per_session)
            return False

        for attempt in range(INTERACTION_RETRY_COUNT):
            try:
                comment_btn = await self._find_visible_element(COMMENT_BTN_SELECTORS, timeout=3000)
                if not comment_btn:
                    if attempt < INTERACTION_RETRY_COUNT - 1:
                        logger.debug("评论按钮未找到，重试 %d/%d", attempt + 1, INTERACTION_RETRY_COUNT)
                        await asyncio.sleep(INTERACTION_RETRY_DELAY)
                        continue
                    logger.warning("未找到评论按钮")
                    self.stats.comments_failed += 1
                    return False

                if not await self._human_click_element(comment_btn, "comment-btn"):
                    if attempt < INTERACTION_RETRY_COUNT - 1:
                        await asyncio.sleep(INTERACTION_RETRY_DELAY)
                        continue
                    self.stats.comments_failed += 1
                    return False

                await asyncio.sleep(random_float(1.0, 2.0))

                comment_input = await self._find_visible_element(COMMENT_INPUT_SELECTORS, timeout=3000)
                if not comment_input:
                    logger.debug("未找到评论输入框，尝试Escape关闭")
                    await self._page.keyboard.press("Escape")
                    await asyncio.sleep(0.5)
                    if attempt < INTERACTION_RETRY_COUNT - 1:
                        await asyncio.sleep(INTERACTION_RETRY_DELAY)
                        continue
                    self.stats.comments_failed += 1
                    return False

                await comment_input.click()
                await asyncio.sleep(random_float(0.3, 0.6))

                video_keyword = ""
                try:
                    video_keyword = await self._page.evaluate(
                        "() => { const el = document.querySelector('[data-e2e=\"video-desc\"], [class*=\"title\"], [class*=\"desc\"]'); return el ? el.textContent.trim().slice(0, 6) : ''; }"
                    )
                except Exception:
                    pass

                comment = self._comment_engine.get_comment(keyword=video_keyword)

                for char in comment:
                    delay = random_int(50, 150)
                    if char in "，。！？、；：":
                        delay = random_int(150, 350)
                    await self._page.keyboard.type(char, delay=delay)

                await asyncio.sleep(random_float(0.5, 1.5))

                sent = False
                for selector in COMMENT_SEND_SELECTORS:
                    if await self._human_click(selector, timeout=3000):
                        sent = True
                        break

                if not sent:
                    await self._page.keyboard.press("Enter")
                    sent = True

                if sent:
                    self.stats.comments_posted += 1
                    logger.info("V 评论成功: %s（第 %d 次）", comment, self.stats.comments_posted)
                    self.stats.interactions_detail.append({
                        "type": "comment", "success": True, "content": comment,
                        "attempt": attempt + 1, "timestamp": datetime.now().isoformat(),
                    })

                await asyncio.sleep(random_float(1.0, 2.0))
                await self._page.keyboard.press("Escape")
                await asyncio.sleep(random_float(0.5, 1.0))
                return sent
            except Exception as e:
                logger.debug("评论尝试 %d 异常: %s", attempt + 1, str(e))
                if attempt < INTERACTION_RETRY_COUNT - 1:
                    await asyncio.sleep(INTERACTION_RETRY_DELAY)
                    continue

        self.stats.comments_failed += 1
        logger.warning("评论失败（已重试 %d 次）", INTERACTION_RETRY_COUNT)
        return False

    async def _follow_creator(self) -> bool:
        if self.stats.follows_given >= self.config.max_follows_per_session:
            logger.info("已达到单次关注上限: %d/%d", self.stats.follows_given, self.config.max_follows_per_session)
            return False

        for attempt in range(INTERACTION_RETRY_COUNT):
            try:
                element = await self._find_visible_element(FOLLOW_SELECTORS, timeout=3000)
                if not element:
                    if attempt < INTERACTION_RETRY_COUNT - 1:
                        await asyncio.sleep(INTERACTION_RETRY_DELAY)
                        continue
                    logger.debug("未找到关注按钮（可能已关注）")
                    self.stats.follows_failed += 1
                    return False

                text = await element.text_content()
                if text and ("已关注" in text or "互相关注" in text):
                    logger.debug("已关注该创作者，跳过")
                    return False

                if await self._human_click_element(element, "follow"):
                    self.stats.follows_given += 1
                    logger.info("V 关注成功（第 %d 次）", self.stats.follows_given)
                    self.stats.interactions_detail.append({
                        "type": "follow", "success": True,
                        "attempt": attempt + 1, "timestamp": datetime.now().isoformat(),
                    })

                    if chance(0.5):
                        await asyncio.sleep(random_float(1.0, 2.0))
                        avatar_selectors = [
                            "[data-e2e='video-avatar']",
                            "[class*='avatar']",
                            "[class*='author'] img",
                        ]
                        for avatar_sel in avatar_selectors:
                            if await self._human_click(avatar_sel, timeout=2000):
                                await asyncio.sleep(random_float(2.0, 5.0))
                                if chance(0.4):
                                    await self._random_scroll()
                                    await asyncio.sleep(random_float(1.0, 3.0))
                                await self._page.go_back()
                                await asyncio.sleep(random_float(1.0, 2.0))
                                break
                    return True
            except Exception as e:
                logger.debug("关注尝试 %d 异常: %s", attempt + 1, str(e))
                if attempt < INTERACTION_RETRY_COUNT - 1:
                    await asyncio.sleep(INTERACTION_RETRY_DELAY)
                    continue

        self.stats.follows_failed += 1
        logger.warning("关注失败（已重试 %d 次）", INTERACTION_RETRY_COUNT)
        return False

    async def _collect_video(self) -> bool:
        if self.stats.collects_given >= self.config.max_collects_per_session:
            logger.info("已达到单次收藏上限: %d/%d", self.stats.collects_given, self.config.max_collects_per_session)
            return False

        for attempt in range(INTERACTION_RETRY_COUNT):
            element = await self._find_visible_element(COLLECT_SELECTORS, timeout=3000)
            if not element:
                if attempt < INTERACTION_RETRY_COUNT - 1:
                    logger.debug("收藏按钮未找到，重试 %d/%d", attempt + 1, INTERACTION_RETRY_COUNT)
                    await asyncio.sleep(INTERACTION_RETRY_DELAY)
                    continue
                else:
                    logger.debug("收藏按钮重试 %d 次仍未找到", INTERACTION_RETRY_COUNT)
                    self.stats.collects_failed += 1
                    return False

            try:
                before_class = await element.get_attribute("class") or ""
                before_aria = await element.get_attribute("aria-label") or ""

                if await self._human_click_element(element, "collect"):
                    await asyncio.sleep(random_float(0.8, 1.5))

                    after_class = await element.get_attribute("class") or ""
                    after_aria = await element.get_attribute("aria-label") or ""

                    collected = (after_class != before_class or
                                 "active" in after_class.lower() or
                                 "collect" in after_class.lower() or
                                 after_aria != before_aria)

                    self.stats.collects_given += 1
                    if collected:
                        logger.info("V 收藏成功（第 %d 次，状态已变化）", self.stats.collects_given)
                    else:
                        logger.info("收藏操作完成（第 %d 次，状态变化未确认）", self.stats.collects_given)

                    self.stats.interactions_detail.append({
                        "type": "collect", "success": True, "verified": collected,
                        "attempt": attempt + 1, "timestamp": datetime.now().isoformat(),
                    })

                    try:
                        confirm_selectors = [
                            "button:has-text('确认')",
                            "button:has-text('确定')",
                            "button:has-text('完成')",
                        ]
                        for sel in confirm_selectors:
                            if await self._human_click(sel, timeout=1000):
                                break
                    except Exception:
                        pass
                    return True
            except Exception as e:
                logger.debug("收藏尝试 %d 异常: %s", attempt + 1, str(e))
                await asyncio.sleep(INTERACTION_RETRY_DELAY)
                continue

        self.stats.collects_failed += 1
        logger.warning("收藏失败（已重试 %d 次）", INTERACTION_RETRY_COUNT)
        return False

    async def _share_video(self) -> bool:
        if self.stats.shares_given >= self.config.max_shares_per_session:
            return False

        for attempt in range(INTERACTION_RETRY_COUNT):
            try:
                element = await self._find_visible_element(SHARE_SELECTORS, timeout=2000)
                if not element:
                    if attempt < INTERACTION_RETRY_COUNT - 1:
                        await asyncio.sleep(INTERACTION_RETRY_DELAY)
                        continue
                    return False

                if await self._human_click_element(element, "share"):
                    await asyncio.sleep(random_float(1.0, 2.0))
                    try:
                        copy_selectors = [
                            "text=复制链接",
                            "[class*='share'] text=复制",
                        ]
                        for sel in copy_selectors:
                            try:
                                if await self._human_click(sel, timeout=2000):
                                    break
                            except Exception:
                                continue
                    except Exception:
                        pass

                    await asyncio.sleep(random_float(0.5, 1.0))
                    await self._page.keyboard.press("Escape")
                    await asyncio.sleep(random_float(0.5, 1.0))

                    self.stats.shares_given += 1
                    logger.info("V 分享成功（第 %d 次）", self.stats.shares_given)
                    self.stats.interactions_detail.append({
                        "type": "share", "success": True,
                        "attempt": attempt + 1, "timestamp": datetime.now().isoformat(),
                    })
                    return True
            except Exception as e:
                logger.debug("分享尝试 %d 异常: %s", attempt + 1, str(e))
                if attempt < INTERACTION_RETRY_COUNT - 1:
                    await asyncio.sleep(INTERACTION_RETRY_DELAY)
                    continue

        self.stats.shares_failed += 1
        return False

    async def _get_video_duration(self) -> float:
        try:
            duration = await self._page.evaluate("""() => {
                const v = document.querySelector('video');
                if (v && v.duration && isFinite(v.duration) && v.duration > 0) {
                    return v.duration;
                }
                const timeEl = document.querySelector('[class*="xgplayer-time"]');
                if (timeEl) {
                    const parts = timeEl.textContent.trim().split(':');
                    if (parts.length === 2) {
                        return parseInt(parts[0]) * 60 + parseInt(parts[1]);
                    } else if (parts.length === 3) {
                        return parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseInt(parts[2]);
                    }
                }
                return 0;
            }""")
            return float(duration) if duration and duration > 0 else 0
        except Exception:
            return 0

    async def _get_video_current_time(self) -> float:
        try:
            t = await self._page.evaluate("""() => {
                const v = document.querySelector('video');
                return (v && v.currentTime && isFinite(v.currentTime)) ? v.currentTime : 0;
            }""")
            return float(t) if t else 0
        except Exception:
            return 0

    async def _watch_video(self):
        self.stats.videos_watched += 1
        video_idx = self.stats.videos_watched

        video_duration = await self._get_video_duration()
        quick_swipe = random.random() < 0.12

        if quick_swipe and video_duration > 0:
            watch_time = random_float(3.0, min(6.0, video_duration * 0.3))
            logger.info("快速划过视频（第 %d 个，时长%.0fs，看%.1fs）", video_idx, video_duration, watch_time)
            await asyncio.sleep(watch_time)
            return

        if video_duration > 0:
            watch_ratio = random_float(0.75, 1.0)
            if chance(0.15):
                watch_ratio = random_float(0.5, 0.75)
            target_watch = video_duration * watch_ratio
            current_time = await self._get_video_current_time()
            remaining = max(0, target_watch - current_time)
            logger.info("开始观看视频（第 %d 个，时长%.0fs，计划看%.0fs/%.0f%%）",
                        video_idx, video_duration, remaining + current_time, watch_ratio * 100)
        else:
            remaining = random_float(15.0, 45.0)
            logger.info("开始观看视频（第 %d 个，时长未知，计划看%.0fs）", video_idx, remaining)

        watch_start = time.time()

        pre_interact_wait = remaining * random_float(0.3, 0.5)
        if pre_interact_wait > 3:
            pre_interact_wait = random_float(3.0, min(8.0, pre_interact_wait))
        pre_interact_wait = max(2.0, pre_interact_wait)
        await asyncio.sleep(pre_interact_wait)

        interaction_ready = await self._wait_for_interaction_ready(timeout=8.0)
        if not interaction_ready:
            await self._dismiss_guide_mask()
            await asyncio.sleep(2.0)
            interaction_ready = await self._wait_for_interaction_ready(timeout=5.0)
            if not interaction_ready:
                logger.warning("互动按钮未就绪，尝试诊断...")
                await self._diagnose_page("互动按钮未就绪")
                await self._take_screenshot("interaction_not_ready")
                await asyncio.sleep(2.0)
                interaction_ready = await self._wait_for_interaction_ready(timeout=5.0)

        is_captcha_cooldown = time.time() < self._captcha_cooldown_until

        if is_captcha_cooldown:
            logger.info("验证码冷却中，跳过互动")
        else:
            if await self._detect_captcha():
                await self._handle_captcha()
                is_captcha_cooldown = True

        if not is_captcha_cooldown:
            actions = []
            if chance(self.config.like_prob):
                actions.append(self._like_video)
            if chance(self.config.collect_prob):
                actions.append(self._collect_video)
            if chance(self.config.comment_prob):
                actions.append(self._comment_video)
            if chance(self.config.follow_prob):
                actions.append(self._follow_creator)
            if chance(self.config.share_prob):
                actions.append(self._share_video)

            if random.random() < 0.3 and len(actions) > 1:
                random.shuffle(actions)

            has_interaction = False
            interaction_failures = 0
            for action in actions:
                if self._shutdown_requested:
                    break
                if not interaction_ready and action not in (self._like_video, self._collect_video):
                    continue
                try:
                    result = await action()
                    if result:
                        has_interaction = True
                    else:
                        interaction_failures += 1
                    await self._random_delay()
                except Exception as e:
                    interaction_failures += 1
                    logger.debug("互动操作异常: %s", str(e))

            if interaction_failures >= 2:
                logger.warning("多次互动失败，截图诊断")
                await self._take_screenshot("interaction_failures")
                await self._diagnose_page("互动失败")

            if not chance(self.config.like_prob):
                self.stats.consecutive_likes = 0

            if has_interaction:
                linger = random_float(2.0, 6.0)
                logger.info("互动后停留 %.1f 秒", linger)
                await asyncio.sleep(linger)

        await self._maybe_pause()

        elapsed = time.time() - watch_start
        still_remaining = (remaining - elapsed) if video_duration > 0 else 0
        if still_remaining > 0:
            await asyncio.sleep(min(still_remaining, 30))

        actual_time = time.time() - watch_start
        if video_duration > 0:
            logger.info("视频观看完成，实际 %.1fs / 总长 %.0fs", actual_time, video_duration)
        else:
            logger.info("视频观看完成，实际 %.1fs", actual_time)

    async def _recover_page(self) -> bool:
        logger.info("尝试恢复页面状态...")
        try:
            current_url = self._page.url
            if "douyin.com" not in current_url:
                logger.info("不在抖音页面，重新导航")
                return await self._safe_goto(DOUYIN_URL)

            state = await self._detect_page_state()
            if state == PageStateDetector.CAPTCHA:
                await self._handle_captcha()
                return True

            if state == PageStateDetector.LOGIN:
                logger.error("登录状态丢失，无法自动恢复")
                return False

            if state == PageStateDetector.POPUP:
                await self._dismiss_popups()
                return True

            if state == PageStateDetector.UNKNOWN:
                logger.info("未知页面状态，重新导航到首页")
                return await self._safe_goto(DOUYIN_URL)

            return True
        except Exception as e:
            logger.error("页面恢复失败: %s", str(e))
            return False

    async def _run_session(self):
        retry_count = 0
        while retry_count < 3:
            try:
                if retry_count > 0:
                    logger.info("第 %d 次重试", retry_count + 1)
                    await asyncio.sleep(5 * retry_count)

                await self._init_browser()

                login_ok = await self._verify_login()
                if not login_ok:
                    logger.error("登录验证失败，请重新登录: python douyin-cookie-check.py --login --account %s", self.config.account_id)
                    self.stats.exit_reason = "登录验证失败"
                    return

                await self._navigate_to_feed()

                self.stats.is_running = True
                self.stats.start_time = time.time()
                session_duration_sec = self.config.duration * 60
                self.stats.end_time = self.stats.start_time + session_duration_sec

                logger.info("=" * 50)
                logger.info("养号会话开始，计划运行 %d 分钟", self.config.duration)
                logger.info("时间段: %s, 延迟系数: %.1f, 暂停系数: %.1f",
                            get_time_period(),
                            self._time_adjustments["delay_mult"],
                            self._time_adjustments["pause_mult"])
                logger.info("=" * 50)

                loop_count = 0
                consecutive_errors = 0
                while self.stats.is_running and time.time() < self.stats.end_time:
                    if self._shutdown_requested:
                        break

                    loop_count += 1
                    try:
                        current_url = self._page.url
                        if "douyin.com" not in current_url:
                            logger.warning("不在抖音页面，尝试恢复")
                            if not await self._recover_page():
                                break
                            await asyncio.sleep(2)
                            continue

                        await self._dismiss_popups()

                        state = await self._detect_page_state()

                        if state == PageStateDetector.CAPTCHA:
                            await self._handle_captcha()
                            continue

                        if state == PageStateDetector.LOGIN:
                            logger.error("检测到登录页面，会话终止")
                            self.stats.exit_reason = "登录状态丢失"
                            break

                        if state == PageStateDetector.POPUP:
                            await self._dismiss_popups()
                            await asyncio.sleep(1)
                            continue

                        consecutive_errors = 0

                        if state in (PageStateDetector.HOME, PageStateDetector.PLAYER):
                            is_live = await self._detect_live()
                            if is_live:
                                logger.info("检测到直播入口，跳过")
                                await self._ensure_video_focus()
                                await asyncio.sleep(random_float(0.3, 0.8))
                                await self._page.keyboard.press("ArrowDown")
                                await asyncio.sleep(random_float(1.5, 2.5))
                                continue
                            await self._watch_video()
                            if await self._scroll_to_next_video():
                                await asyncio.sleep(random_float(0.5, 1.5))
                            else:
                                logger.info("视频切换失败，回到推荐页")
                                await self._navigate_to_feed()
                        elif state in (PageStateDetector.SEARCH, PageStateDetector.SEARCH_PLAYER):
                            logger.info("不在推荐页，回到推荐页")
                            await self._navigate_to_feed()
                        else:
                            logger.info("未知页面状态(%s)，回到推荐页", state)
                            await self._navigate_to_feed()
                            await asyncio.sleep(random_float(2.0, 4.0))

                        await self._random_delay()

                        if loop_count % 10 == 0:
                            remaining = (self.stats.end_time - time.time()) / 60
                            switch_rate = (self.stats.videos_actually_switched / max(self.stats.videos_watched, 1)) * 100
                            logger.info(
                                "运行中 - 剩余约 %.1f 分钟，已看 %d 个视频（切换率%.0f%%），点赞 %d 次，评论 %d 次，收藏 %d 次",
                                max(0, remaining),
                                self.stats.videos_watched,
                                switch_rate,
                                self.stats.likes_given,
                                self.stats.comments_posted,
                                self.stats.collects_given,
                            )
                    except Exception as e:
                        consecutive_errors += 1
                        self.stats.errors_count += 1
                        logger.error("循环内错误: %s", str(e))

                        if consecutive_errors >= 5:
                            logger.error("连续错误过多，尝试恢复页面")
                            if not await self._recover_page():
                                logger.error("恢复失败，重新初始化")
                                break
                            consecutive_errors = 0

                        await asyncio.sleep(random_float(2.0, 5.0))
                        try:
                            current_url = self._page.url
                            if "douyin.com" not in current_url:
                                if not await self._recover_page():
                                    break
                        except Exception:
                            logger.error("恢复失败，尝试重新初始化")
                            break

                self.stats.is_running = False
                if not self.stats.exit_reason:
                    self.stats.exit_reason = "计划时长已到"

                logger.info("养号会话结束: %s", self.stats.exit_reason)
                return

            except PlaywrightTimeoutError as e:
                retry_count += 1
                logger.error("操作超时: %s", str(e))
            except RuntimeError as e:
                retry_count += 1
                logger.error("运行时错误: %s", str(e))
            except Exception as e:
                retry_count += 1
                logger.error("会话异常: %s", str(e))
            finally:
                await self._cleanup()

        logger.error("养号失败，已重试 %d 次", retry_count)

    def generate_report(self) -> str:
        if self.stats.start_time == 0:
            return "未执行养号会话"

        duration_ms = int((time.time() - self.stats.start_time) * 1000)
        duration_str = format_duration(duration_ms)
        interaction_total = self.stats.likes_given + self.stats.comments_posted + self.stats.follows_given + self.stats.collects_given
        interaction_rate = (interaction_total / self.stats.videos_watched * 100) if self.stats.videos_watched > 0 else 0
        switch_rate = (self.stats.videos_actually_switched / max(self.stats.videos_watched, 1)) * 100

        report_lines = [
            "",
            "=" * 50,
            "       抖音养号会话报告",
            "=" * 50,
            f"  账号ID: {self.config.account_id}",
            f"  运行时长: {duration_str}",
            f"  退出原因: {self.stats.exit_reason}",
            f"  时间段: {get_time_period()}",
            "-" * 50,
            f"  观看视频: {self.stats.videos_watched} 个",
            f"  视频切换率: {switch_rate:.1f}%",
            f"  点赞次数: {self.stats.likes_given} 次 (失败: {self.stats.likes_failed})",
            f"  评论次数: {self.stats.comments_posted} 次 (失败: {self.stats.comments_failed})",
            f"  关注次数: {self.stats.follows_given} 次 (失败: {self.stats.follows_failed})",
            f"  收藏次数: {self.stats.collects_given} 次 (失败: {self.stats.collects_failed})",
            f"  分享次数: {self.stats.shares_given} 次 (失败: {self.stats.shares_failed})",
            f"  弹窗关闭: {self.stats.popups_dismissed} 次",
            f"  验证码检测: {self.stats.captcha_detected} 次",
            f"  暂停时长: {format_duration(self.stats.total_pause_time)}",
            f"  错误次数: {self.stats.errors_count} 次",
            "-" * 50,
            f"  互动率: {interaction_rate:.1f}%",
            "-" * 50,
            "  页面状态分布:",
        ]

        for state, count in sorted(self.stats.page_states_detected.items(), key=lambda x: -x[1]):
            report_lines.append(f"    {state}: {count} 次")

        report_lines.append("=" * 50)

        report = "\n".join(report_lines)
        logger.info(report)
        return report

    def save_report(self):
        report_text = self.generate_report()
        if self.stats.start_time == 0:
            return

        analytics_dir = get_analytics_dir(self.config.account_id)
        report_file = analytics_dir / f"nurture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        duration_ms = int((time.time() - self.stats.start_time) * 1000)
        interaction_total = self.stats.likes_given + self.stats.comments_posted + self.stats.follows_given + self.stats.collects_given
        interaction_rate = (interaction_total / self.stats.videos_watched * 100) if self.stats.videos_watched > 0 else 0
        switch_rate = (self.stats.videos_actually_switched / max(self.stats.videos_watched, 1)) * 100

        report_data = {
            "account_id": self.config.account_id,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration_ms // 1000,
            "exit_reason": self.stats.exit_reason,
            "time_period": get_time_period(),
            "videos_watched": self.stats.videos_watched,
            "videos_actually_switched": self.stats.videos_actually_switched,
            "video_switch_rate": round(switch_rate, 1),
            "likes_given": self.stats.likes_given,
            "likes_failed": self.stats.likes_failed,
            "comments_posted": self.stats.comments_posted,
            "comments_failed": self.stats.comments_failed,
            "follows_given": self.stats.follows_given,
            "follows_failed": self.stats.follows_failed,
            "collects_given": self.stats.collects_given,
            "collects_failed": self.stats.collects_failed,
            "shares_given": self.stats.shares_given,
            "shares_failed": self.stats.shares_failed,
            "popups_dismissed": self.stats.popups_dismissed,
            "captcha_detected": self.stats.captcha_detected,
            "interaction_rate": round(interaction_rate, 1),
            "errors_count": self.stats.errors_count,
            "page_states_detected": self.stats.page_states_detected,
            "interactions_detail": self.stats.interactions_detail,
            "config": {
                "duration_minutes": self.config.duration,
                "like_prob": self.config.like_prob,
                "comment_prob": self.config.comment_prob,
                "follow_prob": self.config.follow_prob,
                "collect_prob": self.config.collect_prob,
                "categories": self.config.categories,
            },
        }

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        logger.info("会话报告已保存: %s", report_file)
        return report_data

    def update_cookie_health(self, valid: bool):
        account_config_path = WORKSPACE_DIR / "data" / "accounts" / self.config.account_id / "account.json"
        if not account_config_path.exists():
            return
        try:
            with open(account_config_path, "r", encoding="utf-8") as f:
                account_config = json.load(f)
            account_config.setdefault("cookie_health", {})
            account_config["cookie_health"]["last_check"] = datetime.now().isoformat()
            account_config["cookie_health"]["is_valid"] = valid
            with open(account_config_path, "w", encoding="utf-8") as f:
                json.dump(account_config, f, ensure_ascii=False, indent=2)
            logger.debug("Cookie健康状态已更新: %s", "有效" if valid else "无效")
        except Exception as e:
            logger.warning("更新Cookie健康状态异常: %s", str(e))

    async def _cleanup(self):
        try:
            if self._page:
                await self._page.close()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            logger.warning("清理浏览器资源异常: %s", str(e))
        finally:
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None

    async def run(self):
        try:
            await self._run_session()
        finally:
            await self._cleanup()
            report_data = self.save_report()
            if self._json_output and report_data:
                json_path = get_analytics_dir(self.config.account_id) / f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump({"status": "completed", "data": report_data}, f, ensure_ascii=False, indent=2)
                print(f"JSON_RESULT:{json_path}")

    async def verify_only(self) -> bool:
        account_file = get_account_file(self.config.account_id)
        valid = await cookie_auth(account_file)
        self.update_cookie_health(valid)
        if valid:
            logger.info("登录验证通过，Cookie有效")
        else:
            logger.error("登录验证失败，请重新登录: python douyin-cookie-check.py --login --account %s", self.config.account_id)
        return valid

    async def diagnose(self) -> dict:
        logger.info("========== 诊断模式 ==========")
        report = {"account_id": self.config.account_id, "timestamp": datetime.now().isoformat(), "checks": {}}

        account_file = get_account_file(self.config.account_id)
        report["checks"]["storage_state_file"] = {
            "exists": account_file.exists(),
            "path": str(account_file),
        }
        if account_file.exists():
            try:
                data = json.loads(account_file.read_text(encoding="utf-8"))
                cookies = data.get("cookies", [])
                cookie_names = {c.get("name") for c in cookies}
                matched = [k for k in LOGIN_KEY_COOKIES if k in cookie_names]
                report["checks"]["storage_state_file"]["cookie_count"] = len(cookies)
                report["checks"]["storage_state_file"]["key_cookies_found"] = matched
                report["checks"]["storage_state_file"]["key_cookies_missing"] = [k for k in LOGIN_KEY_COOKIES if k not in cookie_names]
            except Exception as e:
                report["checks"]["storage_state_file"]["error"] = str(e)

        account_config_path = WORKSPACE_DIR / "data" / "accounts" / self.config.account_id / "account.json"
        report["checks"]["account_config"] = {"exists": account_config_path.exists()}
        if account_config_path.exists():
            try:
                with open(account_config_path, "r", encoding="utf-8") as f:
                    ac = json.load(f)
                report["checks"]["account_config"]["cookie_health"] = ac.get("cookie_health", {})
                report["checks"]["account_config"]["nurture_config"] = ac.get("nurture", {})
            except Exception as e:
                report["checks"]["account_config"]["error"] = str(e)

        logger.info("1. 检查Cookie文件: %s", "OK" if report["checks"]["storage_state_file"]["exists"] else "FAIL")

        logger.info("2. 启动浏览器检查页面状态...")
        try:
            await self._init_browser()
            login_ok = await self._verify_login()
            report["checks"]["login"] = {"valid": login_ok}

            if login_ok:
                await self._navigate_to_feed()
                state = await self._detect_page_state()
                report["checks"]["page_state"] = {"state": state}

                diag = await self._diagnose_page("诊断模式")
                report["checks"]["page_dom"] = diag

                ss_path = await self._take_screenshot("diagnose")
                report["checks"]["screenshot"] = ss_path

                if self.config.categories:
                    category = self.config.categories[0]
                    search_ok = await self._search_category(category)
                    report["checks"]["search"] = {"category": category, "success": search_ok}
                    if search_ok:
                        click_ok = await self._click_into_video()
                        report["checks"]["click_video"] = {"success": click_ok}
                        if click_ok:
                            await asyncio.sleep(3)
                            player_diag = await self._diagnose_page("播放页诊断")
                            report["checks"]["player_dom"] = player_diag
                            player_ss = await self._take_screenshot("diagnose_player")
                            report["checks"]["player_screenshot"] = player_ss

                            interaction_ready = await self._wait_for_interaction_ready(timeout=5.0)
                            report["checks"]["interaction_ready"] = interaction_ready

                            like_el = await self._find_visible_element(LIKE_SELECTORS, timeout=3000)
                            report["checks"]["like_button"] = {"found": like_el is not None}

                            collect_el = await self._find_visible_element(COLLECT_SELECTORS, timeout=3000)
                            report["checks"]["collect_button"] = {"found": collect_el is not None}

                            comment_el = await self._find_visible_element(COMMENT_BTN_SELECTORS, timeout=3000)
                            report["checks"]["comment_button"] = {"found": comment_el is not None}

                            follow_el = await self._find_visible_element(FOLLOW_SELECTORS, timeout=3000)
                            report["checks"]["follow_button"] = {"found": follow_el is not None}

                            captcha = await self._detect_captcha()
                            report["checks"]["captcha"] = {"detected": captcha}
            else:
                report["checks"]["login"] = {"valid": False, "message": "需要重新登录"}
        except Exception as e:
            report["checks"]["browser_error"] = str(e)
            logger.error("浏览器诊断异常: %s", str(e))
        finally:
            await self._cleanup()

        report_file = WORKSPACE_DIR / "data" / "accounts" / self.config.account_id / "analytics" / f"diagnose_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info("诊断报告已保存: %s", report_file)
        logger.info("========== 诊断完成 ==========")
        return report


_nurturer_instance: Optional[DouyinNurturer] = None


def _signal_handler(sig, frame):
    global _nurturer_instance
    if _nurturer_instance:
        _nurturer_instance.request_shutdown()
    else:
        sys.exit(0)


async def async_main():
    global _nurturer_instance

    parser = argparse.ArgumentParser(description="抖音网页版自动养号脚本（patchright + storage_state）")
    parser.add_argument("--account", type=str, default="account-1", help="账号ID")
    parser.add_argument("--no-headless", action="store_true", help="显示浏览器窗口")
    parser.add_argument("--verify-only", action="store_true", help="仅验证登录状态")
    parser.add_argument("--diagnose", action="store_true", help="诊断模式：检查Cookie/页面/互动按钮状态")
    parser.add_argument("--duration", type=int, help="养号时长（分钟），默认30")
    parser.add_argument("--like-prob", type=float, help="点赞概率（0-1），默认0.3")
    parser.add_argument("--comment-prob", type=float, help="评论概率（0-1），默认0.1")
    parser.add_argument("--follow-prob", type=float, help="关注概率（0-1），默认0.05")
    parser.add_argument("--collect-prob", type=float, help="收藏概率（0-1），默认0.15")
    parser.add_argument("--categories", type=str, help="偏好分类，逗号分隔")
    parser.add_argument("--min-watch", type=int, help="最少观看秒数，默认5")
    parser.add_argument("--max-watch", type=int, help="最多观看秒数，默认30")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--json-output", action="store_true", help="输出JSON结果文件路径（agent调用用）")

    args = parser.parse_args()

    setup_logging(args.account, args.log_level)

    config_kwargs = {"account_id": args.account}
    if args.duration is not None:
        config_kwargs["duration"] = args.duration
    if args.like_prob is not None:
        config_kwargs["like_prob"] = args.like_prob
    if args.comment_prob is not None:
        config_kwargs["comment_prob"] = args.comment_prob
    if args.follow_prob is not None:
        config_kwargs["follow_prob"] = args.follow_prob
    if args.collect_prob is not None:
        config_kwargs["collect_prob"] = args.collect_prob
    if args.categories:
        config_kwargs["categories"] = args.categories
    if args.min_watch is not None:
        config_kwargs["min_watch_time"] = args.min_watch
    if args.max_watch is not None:
        config_kwargs["max_watch_time"] = args.max_watch
    config_kwargs["headless"] = not args.no_headless

    config = NurtureConfig(**config_kwargs)
    nurturer = DouyinNurturer(config)
    nurturer._json_output = args.json_output
    _nurturer_instance = nurturer

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    if args.verify_only:
        login_ok = await nurturer.verify_only()
        sys.exit(0 if login_ok else 1)

    if args.diagnose:
        report = await nurturer.diagnose()
        sys.exit(0 if report.get("checks", {}).get("login", {}).get("valid") else 1)

    await nurturer.run()
    _nurturer_instance = None


if __name__ == "__main__":
    asyncio.run(async_main())
