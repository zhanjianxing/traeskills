---
name: douyin-nurture
description: "抖音养号互动：通过patchright在网页端模拟真人刷抖音/点赞/评论/关注，支持多账号。Use when: (1) 养号活跃账号, (2) 自动刷抖音, (3) 模拟真人互动"
metadata:
  openclaw:
    emoji: 🤖
    requires:
      - patchright
    primaryScript: scripts/douyin-nurture.py
---

# 抖音养号互动 Skill

## 概述

通过 patchright（Playwright反检测分支）自动化脚本在抖音网页版（www.douyin.com）模拟真人刷抖音行为，包括浏览、点赞、评论、关注、收藏等互动操作，提升账号活跃度和权重。

**核心特性**：
- 使用 patchright 替代 playwright（内置反检测指纹）
- 使用 storage_state 保存/恢复登录状态（扫码一次，7-30天有效）
- 页面状态检测引擎（7种状态：首页/播放页/搜索页/搜索播放页/弹窗/登录/验证码）
- 视频时长感知观看（75-100%看完，12%概率快速划过）
- **互动重试机制**（每个操作3次重试+多选择器降级）
- **验证码检测与自动冷却**（检测到验证码自动暂停120秒）
- **自动恢复**（页面异常时自动修复，连续错误5次触发恢复）
- 诊断模式（agent可调用排查问题）
- **JSON结构化输出**（agent可解析运行结果）

**支持多账号**：通过 `--account` 参数指定账号，每个账号的数据和登录状态完全隔离。

## 快速命令参考

### Agent 调用命令

| 场景 | 命令 |
|------|------|
| 养号30分钟 | `python scripts/douyin-nurture.py --account account-1` |
| 养号自定义时长 | `python scripts/douyin-nurture.py --account account-1 --duration 60` |
| 验证登录状态 | `python scripts/douyin-nurture.py --account account-1 --verify-only` |
| **诊断问题** | `python scripts/douyin-nurture.py --account account-1 --diagnose` |
| **JSON输出（agent用）** | `python scripts/douyin-nurture.py --account account-1 --duration 5 --json-output` |
| 重新登录 | `python scripts/douyin-cookie-check.py --login --account account-1` |
| 检查所有Cookie | `python scripts/douyin-cookie-check.py --account account-1` |
| 调试模式 | `python scripts/douyin-nurture.py --account account-1 --no-headless` |

### Agent 集成流程

当agent需要执行养号任务时，按以下流程操作：

```
1. 验证登录状态
   python scripts/douyin-nurture.py --account account-1 --verify-only
   → 退出码0=有效, 1=无效

2. 如果登录无效，执行登录
   python scripts/douyin-cookie-check.py --login --account account-1
   → 等待用户扫码

3. 运行养号（JSON输出模式）
   python scripts/douyin-nurture.py --account account-1 --duration 30 --json-output
   → 运行结束后输出 JSON_RESULT:{path}
   → 读取该JSON文件获取详细结果

4. 如果运行出错，运行诊断
   python scripts/douyin-nurture.py --account account-1 --diagnose
   → 读取诊断报告 data/accounts/account-1/analytics/diagnose_*.json

5. 根据诊断结果处理（见下方问题排查流程）
```

### 问题排查流程

当养号脚本出现问题时，agent应按以下流程排查：

```
1. 运行诊断模式
   python scripts/douyin-nurture.py --account account-1 --diagnose

2. 查看诊断报告
   data/accounts/account-1/analytics/diagnose_*.json

3. 查看截图（如有）
   data/screenshots/account-1/

4. 根据诊断结果处理：
   - Cookie失效 → 重新登录
     python scripts/douyin-cookie-check.py --login --account account-1
   - 互动按钮不可见 → 检查视口大小（需>=1440宽）
   - 验证码被触发 → 降低互动概率，增加运行间隔
   - 页面状态异常 → 查看截图分析
   - 网络超时 → 重试
   - like_button.found=false → 抖音前端可能更新，需要更新选择器
```

### JSON输出格式

使用 `--json-output` 时，运行结束后会在控制台输出：
```
JSON_RESULT:data/accounts/account-1/analytics/result_20260512_120000.json
```

JSON文件内容：
```json
{
  "status": "completed",
  "data": {
    "account_id": "account-1",
    "duration_seconds": 1800,
    "exit_reason": "计划时长已到",
    "videos_watched": 25,
    "video_switch_rate": 80.0,
    "likes_given": 8,
    "likes_failed": 1,
    "comments_posted": 2,
    "collects_given": 4,
    "follows_given": 1,
    "shares_given": 0,
    "captcha_detected": 0,
    "interaction_rate": 60.0,
    "interactions_detail": [
      {"type": "like", "success": true, "verified": true, "attempt": 1, "timestamp": "..."},
      {"type": "collect", "success": true, "verified": true, "attempt": 2, "timestamp": "..."}
    ]
  }
}
```

## 环境准备

### 必需工具

| 工具 | 说明 | 安装方式 |
|------|------|---------|
| Python 3.10+ | 运行环境 | 官网下载 |
| patchright | Playwright反检测分支 | `pip install patchright && python -m patchright install chromium` |

### 首次登录

首次使用需要扫码登录，登录状态会保存到 `data/browser-sessions/{account}.json`：

```bash
python scripts/douyin-cookie-check.py --login --account account-1
```

在弹出的浏览器中扫码登录，登录成功后自动保存。之后运行养号脚本会自动加载登录状态，无需重复登录。

## 目录结构

```
douyin-nurture/
├── SKILL.md
├── scripts/
│   ├── douyin-nurture.py         # 养号主脚本
│   ├── douyin-cookie-check.py    # Cookie检查/登录脚本
│   └── test_shortcuts.py         # 快捷键测试脚本
└── data/                         # 运行时数据（自动创建）
    ├── browser-sessions/         # 登录状态文件（storage_state）
    │   ├── account-1.json
    │   └── account-2.json
    ├── accounts/
    │   ├── account-1/
    │   │   ├── account.json      # 账号配置（养号参数、Cookie健康状态）
    │   │   └── analytics/        # 会话报告 + 诊断报告 + JSON结果
    │   └── account-2/
    │       ├── account.json
    │       └── analytics/
    ├── logs/                     # 运行日志
    │   └── account-1/
    └── screenshots/              # 截图（失败时自动保存）
        └── account-1/
```

### 账号配置文件

`data/accounts/{account}/account.json`：

```json
{
  "account_id": "account-1",
  "account_name": "账号1",
  "nurture": {
    "duration_minutes": 30,
    "like_prob": 0.3,
    "comment_prob": 0.1,
    "follow_prob": 0.05,
    "collect_prob": 0.15,
    "categories": ["生活", "美食", "旅行", "科技", "搞笑"]
  },
  "cookie_health": {
    "last_check": "2026-05-12T11:00:00",
    "is_valid": true
  }
}
```

## 养号策略

### 养号阶段

| 阶段 | 时长 | 目标 | 操作频率 |
|------|------|------|---------|
| 新号期 | 第1-7天 | 建立账号标签 | 每天刷30-60分钟 |
| 成长期 | 第8-21天 | 提升账号权重 | 每天刷40-80分钟 |
| 稳定期 | 第22天+ | 维持活跃度 | 每天刷20-40分钟 |

### 视频观看行为（拟人化）

| 行为 | 概率 | 说明 |
|------|------|------|
| 看完视频 | 88% | 75-100%时长，短视频基本看完 |
| 快速划过 | 12% | 看3-6秒后划走（模拟不感兴趣） |
| 互动后停留 | 100% | 互动后额外停留2-6秒 |
| 随机发呆 | 10% | 暂停5-20秒 |
| 回滚查看 | 5% | 回滚模拟犹豫 |

### 互动参数

| 参数 | 默认值 | 说明 | 建议范围 |
|------|-------|------|---------|
| `duration` | 30 | 单次养号时长（分钟） | 20-80 |
| `like_prob` | 0.3 | 点赞概率 | 0.2-0.5 |
| `comment_prob` | 0.1 | 评论概率 | 0.02-0.15 |
| `follow_prob` | 0.05 | 关注概率 | 0.01-0.08 |
| `collect_prob` | 0.15 | 收藏概率 | 0.05-0.2 |
| `categories` | 生活,美食,旅行,科技,搞笑 | 领域偏好 | 见下方 |

### 领域偏好分类

```
职场 | 美食 | 旅游 | 健身 | 美妆 | 搞笑 | 知识 | 情感 | 科技 | 育儿 | 宠物 | AI应用 | 效率工具
```

## 脚本行为流程

```
1. 启动浏览器（patchright + storage_state）→ 验证登录
   ↓
2. 导航到抖音推荐页 → 搜索偏好分类
   ↓
3. 点击视频卡片进入播放页
   ↓
4. 等待互动按钮就绪（多选择器检测）
   ↓  ← 如果未就绪：滚动页面 → 重新检测
5. 检测验证码 → 如果触发：冷却120秒，期间仅浏览
   ↓
6. 观看视频（根据视频时长按比例观看）
   ↓
7. 按概率执行互动操作（点赞/收藏/评论/关注/分享）
   - 互动前：等待按钮出现+可见
   - 互动中：3次重试+多选择器降级
   - 互动后：检测class/aria-label变化确认状态
   - 失败时：截图+诊断
   ↓
8. 切换下一个视频（优先点击箭头，备选滚轮/键盘）
   ↓  ← 播放页内连续看多个视频（60%概率继续看下一个）
9. 重复3-8直到达到设定时长
   ↓
10. 生成会话报告（JSON）→ 优雅退出
```

### 健壮性机制

| 机制 | 说明 |
|------|------|
| 互动重试 | 每个操作3次重试，每次重试间隔2秒 |
| 多选择器降级 | 每个按钮8个备选选择器（data-e2e → CSS class → 语义匹配） |
| 验证码检测 | 检测6种验证码元素，触发后冷却120秒 |
| 自动恢复 | 页面异常时自动修复，连续错误5次触发恢复 |
| 视频切换二次确认 | src未变化时1秒后再检测一次 |
| 互动按钮滚动恢复 | 按钮不可见时自动滚动页面再检测 |
| 连续错误计数 | 超过5次连续错误自动恢复页面 |

### 反检测机制

- patchright 内置反检测指纹
- 随机视口（1440-1920宽）+ 随机UA（Chrome 129-131）
- 时间感知延迟（深夜慢、傍晚快）
- 随机鼠标移动（点击前先移动到附近位置）
- 逐字输入评论（50-150ms/字，标点150-350ms）
- 连续点赞5次后强制休息60秒
- 会话上限：点赞50/评论15/关注8/收藏20/分享5

### 互动按钮定位（多选择器降级）

| 操作 | 首选选择器 | 备选数量 |
|------|-----------|---------|
| 点赞 | `[data-e2e='video-player-digg']` | 8个 |
| 评论 | `[data-e2e='feed-comment-icon']` | 5个 |
| 收藏 | `[data-e2e='video-player-collect']` | 8个 |
| 分享 | `[data-e2e='video-player-share']` | 4个 |
| 关注 | `[data-e2e='feed-follow-icon']` | 5个 |
| 下一个 | `[data-e2e='video-switch-next-arrow']` | 4个 |

### 页面状态检测

| 状态 | 判断条件 |
|------|---------|
| HOME | card_count>0 或 video_count==1 |
| PLAYER | video_count>=1 且 /video/ 在URL中 |
| SEARCH | URL含 /search/ 或标题含"搜索" |
| SEARCH_PLAYER | 搜索页+有视频播放 |
| POPUP | 有弹窗关闭按钮且无视频 |
| LOGIN | 有登录UI |
| CAPTCHA | 有验证码元素 |

## 诊断模式详解

`--diagnose` 模式会执行以下检查并生成JSON报告：

1. **Cookie文件检查** — storage_state文件是否存在、Cookie数量、关键Cookie是否齐全
2. **账号配置检查** — account.json是否存在、cookie_health状态
3. **浏览器启动** — 验证登录状态
4. **页面状态检测** — 当前页面处于什么状态
5. **DOM诊断** — 17个data-e2e按钮的存在性/可见性/位置 + 侧边栏检测
6. **截图** — 首页截图 + 播放页截图
7. **搜索测试** — 搜索分类是否成功
8. **互动按钮逐一检测** — 点赞/收藏/评论/关注按钮是否可找到
9. **验证码检测** — 是否存在验证码元素

诊断报告保存路径：`data/accounts/{account}/analytics/diagnose_*.json`

截图保存路径：`data/screenshots/{account}/`

## 风险提示

> ⚠️ **重要警告**：养号脚本存在封号风险，请严格遵守以下规则：

1. **频率控制**：不要设置过高的互动概率，真人行为是低频随机的
2. **时间分散**：不要在凌晨等非正常时间段运行
3. **评论质量**：评论内容必须自然，避免重复使用同一评论
4. **渐进养号**：新号前3天只刷不互动，第4天开始低频互动
5. **定期暂停**：每周至少暂停1-2天，模拟真人休息
6. **IP稳定**：尽量在同一网络环境下操作
7. **免责声明**：本工具仅供学习研究，使用产生的后果由使用者自行承担

## 注意事项

- 首次使用需扫码登录：`python scripts/douyin-cookie-check.py --login --account account-1`
- Cookie有效期有限（7-30天），过期后需重新登录
- 遇到问题先运行诊断：`python scripts/douyin-nurture.py --account account-1 --diagnose`
- 建议首次使用 `--no-headless` 模式确认操作正常
- 脚本运行期间不要手动操作同一浏览器
- 日志文件：`data/logs/{account}/nurture_*.log`
- agent调用时使用 `--json-output` 获取结构化结果
