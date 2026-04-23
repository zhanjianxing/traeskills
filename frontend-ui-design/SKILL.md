---
name: "frontend-ui-design"
description: "前端UI设计规范技能。定义UI设计系统规范，确保生成美观一致的前端页面。Invoke when: 创建前端页面/组件、优化UI样式、前端代码审查、设计系统搭建、修复样式问题、或任何前端UI相关任务。"
---

# 前端UI设计规范技能

本技能定义了完整的前端UI设计规范，确保AI生成的前端页面美观、一致、专业。

**重要**：本技能必须对接需求清单，确保开发的功能完整、API接口正确。

---

## 零、触发条件

**以下场景必须调用此技能：**

### 0.1 开发场景

- 创建新的前端页面或组件
- 开发表单、表格、列表、详情等业务页面
- 实现响应式布局
- 添加新的UI组件
- 编写Vue/React组件代码

### 0.2 优化场景

- 优化页面布局和视觉层次
- 改进间距、颜色、字体等样式
- 提升页面美观度
- 优化组件样式
- 改善用户体验

### 0.3 审查场景

- 前端代码审查
- UI规范检查
- 样式代码质量检查
- 可访问性审查
- 响应式适配检查

### 0.4 设计场景

- UI设计方案制定
- 组件库设计
- 设计系统搭建
- 颜色/字体/间距规范定义
- 页面原型设计

### 0.5 修复场景

- 修复样式问题
- 修复布局问题
- 修复响应式问题
- 修复可访问性问题

### 0.6 其他前端相关场景

- 前端技术选型建议
- CSS/Tailwind使用咨询
- 组件封装建议
- 代码重构建议

---

## 零.1、需求清单对接（必须执行）

### 0.1.1 何时读取需求清单

**以下场景必须先读取需求清单：**
- 开始新的前端功能开发
- 创建新的业务页面
- 对接新的API接口
- 开发列表页、详情页、表单页

### 0.1.2 需求清单路径

```
docs/工作空间/01-项目管理/[项目名]/01-需求/需求清单.md
```

### 0.1.3 读取需求清单步骤

1. **定位项目根目录**：从当前工作目录向上查找 `docs/工作空间/01-项目管理/`
2. **查找需求清单**：在 `[项目名]/01-需求/` 目录下找到 `需求清单.md`
3. **解析需求清单内容**：
   - 提取功能列表（按模块/子模块）
   - 提取API接口信息（路径、方法、参数、响应）
   - 提取非功能需求（性能、安全要求）

### 0.1.4 从需求清单提取的关键信息

| 信息类型 | 提取内容 | 用途 |
|----------|----------|------|
| 功能ID | 如 U001、P001 | 组件/页面命名参考 |
| 功能名称 | 如 用户登录、商品列表 | 页面标题、菜单项 |
| 功能描述 | 详细业务描述 | 理解业务逻辑 |
| API接口 | /api/v1/xxx | 前端API调用 |
| HTTP方法 | GET/POST/PUT/DELETE | 对应HTTP请求 |
| 优先级 | 核心/重要/辅助 | 决定开发顺序 |
| 非功能需求 | 性能/安全/兼容性要求 | 技术选型和优化 |

### 0.1.5 基于需求清单的开发流程

1. **读取需求清单**：解析当前项目的需求清单
2. **定位相关功能**：根据开发任务找到对应的功能项
3. **提取API信息**：获取接口路径、请求参数、响应格式
4. **设计页面结构**：根据功能描述设计UI布局
5. **实现接口对接**：按照API规范实现数据交互
6. **验证功能完整**：对照需求清单检查功能是否完整

---

## 一、设计原则

### 1.1 核心原则

1. **需求驱动**：所有API接口以需求清单为准，禁止自行定义未在需求清单中的接口
2. **一致性优先**：相同功能使用相同的视觉表现
3. **层次分明**：通过大小、颜色、间距建立视觉层次
4. **留白呼吸**：合理使用间距，避免拥挤感
5. **对比突出**：重要元素使用对比色或更大尺寸
6. **响应式优先**：所有设计必须考虑多设备适配
7. **精致现代**：追求GitHub、Linear、Vercel级别的精致设计感
8. **API设计**：API接口以需求清单为准，功能完整覆盖需求清单中的所有接口

### 1.2 现代设计要素

| 要素 | 实现方式 | 效果 |
|------|----------|------|
| **渐变背景** | `bg-gradient-to-r from-primary/5 to-secondary/5` | 增加视觉深度 |
| **玻璃拟态** | `bg-white/80 backdrop-blur-xl` | 现代通透感 |
| **微妙阴影** | `shadow-lg shadow-primary/5` | 精致层次感 |
| **流畅动画** | `transition-all duration-300 ease-out` | 高级交互感 |
| **悬停效果** | `hover:scale-105 hover:shadow-xl hover:-translate-y-1` | 生动反馈 |
| **渐变边框** | `border border-transparent bg-gradient-to-r p-[1px]` | 科技感 |
| **发光效果** | `ring-2 ring-primary/20` | 聚焦引导 |
| **渐变文字** | `bg-gradient-to-r bg-clip-text text-transparent` | 品牌感 |

### 1.3 设计约束

- **禁止随意发挥**：必须遵循本规范定义的设计系统
- **禁止硬编码值**：使用设计Token而非任意数值
- **禁止无意义装饰**：每个视觉元素都应有目的，炫酷效果服务于用户体验
- **追求精致克制**：像GitHub、Linear、Vercel那样，精致但不冗余，现代但不浮夸
- **禁止自行定义API**：未在需求清单中定义的接口不得使用

---

## 二、API接口规范（以需求清单为准）

### 2.1 接口获取原则

前端开发时，API接口必须从需求清单中获取，禁止自行定义：

| 获取来源 | 说明 |
|----------|------|
| 需求清单 | 所有API接口路径、请求方法、参数、响应格式必须来自需求清单 |
| 项目文档 | 如有API文档，以文档为准（但需与需求清单一致） |
| 后端确认 | 如接口有变动，需与后端确认后同步更新需求清单 |

### 2.2 接口信息提取

从需求清单中提取以下信息用于前端开发：

```markdown
| 字段 | 用途 |
|------|------|
| API接口 | 完整的请求路径，如 /api/v1/user/login |
| 方法 | HTTP方法：GET（查询）、POST（创建）、PUT（更新）、DELETE（删除） |
| 功能描述 | 理解接口的业务用途 |
| 优先级 | 决定开发顺序：核心 > 重要 > 辅助 |
```

### 2.3 前端API层设计

基于需求清单设计API调用层：

```typescript
// API模块划分（与需求清单模块对应）
// src/api/
// ├── user.ts      // 用户模块（对应需求清单1.1用户体系）
// ├── product.ts   // 商品模块（对应需求清单1.2商品交易）
// ├── order.ts     // 订单模块（对应需求清单1.3订单管理）
// └── index.ts     // 统一导出

// 每个API文件包含对应模块的所有接口
// 接口命名与需求清单功能ID对应，如 U001、P001
```

### 2.4 接口调用规范

| 规范项 | 要求 |
|--------|------|
| 路径前缀 | 使用需求清单定义的统一前缀，如 `/api/v1/` |
| 请求方法 | 必须与需求清单一致 |
| 参数传递 | 查询参数用params，请求体用data |
| 错误处理 | 统一处理业务异常和系统异常 |
| 加载状态 | 关键接口需展示加载状态 |
| 权限header | 如需JWT Token，统一在拦截器中处理 |

---

## 三、颜色系统

### 2.1 语义化颜色（必须使用）

| 变量名 | 用途 | OKLCH值 |
|--------|------|---------|
| `--primary` | 主色，用于主要操作、品牌元素 | `oklch(0.55 0.2 250)` |
| `--primary-foreground` | 主色上的文字 | `oklch(0.98 0 0)` |
| `--secondary` | 次要色，用于次要操作 | `oklch(0.95 0.02 250)` |
| `--secondary-foreground` | 次要色上的文字 | `oklch(0.25 0.02 250)` |
| `--background` | 页面背景 | `oklch(0.99 0 0)` |
| `--foreground` | 正文文字 | `oklch(0.15 0 0)` |
| `--card` | 卡片背景 | `oklch(1 0 0)` |
| `--card-foreground` | 卡片文字 | `oklch(0.15 0 0)` |
| `--border` | 边框 | `oklch(0.9 0 0)` |
| `--ring` | 焦点环 | `oklch(0.55 0.2 250)` |
| `--destructive` | 危险/删除 | `oklch(0.55 0.22 25)` |
| `--success` | 成功状态 | `oklch(0.6 0.18 145)` |
| `--warning` | 警告状态 | `oklch(0.75 0.15 85)` |
| `--info` | 信息状态 | `oklch(0.55 0.15 230)` |
| `--muted` | 静音背景 | `oklch(0.95 0 0)` |
| `--muted-foreground` | 次要文字、禁用状态 | `oklch(0.5 0 0)` |

### 2.2 颜色使用规则

| 场景 | 颜色选择 |
|------|----------|
| 主要按钮 | `bg-primary text-primary-foreground` |
| 次要按钮 | `bg-secondary text-secondary-foreground` |
| 危险操作 | `bg-destructive text-white` |
| 成功状态 | `text-success` 或 `bg-success/10 text-success` |
| 正文文字 | `text-foreground` |
| 次要文字 | `text-muted-foreground` |
| 卡片背景 | `bg-card` |
| 边框 | `border-border` |
| 焦点环 | `ring-ring` |

### 2.3 暗色模式变量

| 变量名 | 暗色模式值 |
|--------|-----------|
| `--background` | `oklch(0.15 0.01 250)` |
| `--foreground` | `oklch(0.95 0 0)` |
| `--card` | `oklch(0.18 0.01 250)` |
| `--card-foreground` | `oklch(0.95 0 0)` |
| `--primary` | `oklch(0.65 0.2 250)` |
| `--primary-foreground` | `oklch(0.15 0 0)` |
| `--secondary` | `oklch(0.25 0.02 250)` |
| `--secondary-foreground` | `oklch(0.95 0 0)` |
| `--muted` | `oklch(0.25 0 0)` |
| `--muted-foreground` | `oklch(0.65 0 0)` |
| `--border` | `oklch(0.3 0 0)` |

---

## 三、间距系统

### 3.1 间距比例（基于4px基准）

| 变量名 | 值 | 像素 |
|--------|-----|------|
| `--spacing-0` | 0 | 0px |
| `--spacing-1` | 0.25rem | 4px |
| `--spacing-2` | 0.5rem | 8px |
| `--spacing-3` | 0.75rem | 12px |
| `--spacing-4` | 1rem | 16px |
| `--spacing-5` | 1.25rem | 20px |
| `--spacing-6` | 1.5rem | 24px |
| `--spacing-8` | 2rem | 32px |
| `--spacing-10` | 2.5rem | 40px |
| `--spacing-12` | 3rem | 48px |
| `--spacing-16` | 4rem | 64px |
| `--spacing-20` | 5rem | 80px |
| `--spacing-24` | 6rem | 96px |

### 3.2 间距使用规范

| 场景 | 推荐间距 | Tailwind类 |
|------|----------|------------|
| 图标与文字间距 | 8px | `gap-2` |
| 表单项间距 | 16px | `space-y-4` |
| 卡片内边距 | 24px | `p-6` |
| 区块间距 | 32px | `space-y-8` |
| 页面边距 | 24px | `p-6` |
| 按钮内边距 | 12px 24px | `px-6 py-3` |
| 输入框内边距 | 12px 16px | `px-4 py-3` |
| 列表项间距 | 12px | `space-y-3` |
| 卡片组间距 | 24px | `gap-6` |

### 3.3 间距黄金法则

1. **8px基础单位**：所有间距应为8的倍数（4、8、12、16、24、32...）
2. **相关元素间距小**：紧密相关的元素使用较小间距
3. **独立区块间距大**：不同功能区块使用较大间距
4. **避免随意数值**：禁止使用 `p-[13px]` 这类任意值

---

## 四、字体排版系统

### 4.1 字体大小比例

| 变量名 | 值 | 像素 | 用途 |
|--------|-----|------|------|
| `--text-xs` | 0.75rem | 12px | 辅助文字、标签 |
| `--text-sm` | 0.875rem | 14px | 次要文字、表单标签 |
| `--text-base` | 1rem | 16px | 正文文字 |
| `--text-lg` | 1.125rem | 18px | 小标题 |
| `--text-xl` | 1.25rem | 20px | 标题 |
| `--text-2xl` | 1.5rem | 24px | 大标题 |
| `--text-3xl` | 1.875rem | 30px | 页面标题 |
| `--text-4xl` | 2.25rem | 36px | 主标题 |
| `--text-5xl` | 3rem | 48px | 特大标题 |

### 4.2 行高规范

| 变量名 | 值 | 用途 |
|--------|-----|------|
| `--leading-tight` | 1.25 | 标题行高 |
| `--leading-snug` | 1.375 | 紧凑行高 |
| `--leading-normal` | 1.5 | 正常行高 |
| `--leading-relaxed` | 1.625 | 宽松行高 |

### 4.3 字重规范

| 变量名 | 值 | 用途 |
|--------|-----|------|
| `--font-normal` | 400 | 正文 |
| `--font-medium` | 500 | 强调文字 |
| `--font-semibold` | 600 | 标题、按钮 |
| `--font-bold` | 700 | 重要标题 |

### 4.4 排版使用规范

| 元素 | 字号 | 字重 | 行高 | Tailwind类 |
|------|------|------|------|------------|
| 页面主标题 | 30px/36px | 700 | 1.25 | `text-3xl md:text-4xl font-bold leading-tight` |
| 区块标题 | 24px | 600 | 1.25 | `text-2xl font-semibold leading-tight` |
| 卡片标题 | 18px/20px | 600 | 1.25 | `text-lg md:text-xl font-semibold leading-tight` |
| 正文文字 | 16px | 400 | 1.5 | `text-base leading-normal` |
| 次要文字 | 14px | 400 | 1.5 | `text-sm text-muted-foreground` |
| 辅助标签 | 12px | 500 | 1.25 | `text-xs font-medium` |
| 按钮文字 | 14px | 500 | 1 | `text-sm font-medium` |

---

## 五、布局规范

### 5.1 页面布局结构

- **Header**：固定高度，顶部导航
- **Sidebar**（可选）：侧边栏，固定宽度
- **Main Content**：主内容区，自适应宽度
- **Right Panel**（可选）：右侧面板
- **Footer**（可选）：页脚

### 5.2 容器宽度

| 变量名 | 值 |
|--------|-----|
| `--container-sm` | 640px |
| `--container-md` | 768px |
| `--container-lg` | 1024px |
| `--container-xl` | 1280px |
| `--container-2xl` | 1536px |

### 5.3 栅格系统

- **标准栅格**：`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6`
- **侧边栏布局**：侧边栏 `w-64 shrink-0`，主内容 `flex-1`

### 5.4 响应式断点

| 断点 | 值 | 设备 |
|------|-----|------|
| `sm` | 640px | 手机横屏 |
| `md` | 768px | 平板 |
| `lg` | 1024px | 小屏电脑 |
| `xl` | 1280px | 桌面 |
| `2xl` | 1536px | 大屏 |

---

## 六、组件设计规范

### 6.1 按钮规范

| 类型 | 背景色 | 文字色 | 悬停效果 |
|------|--------|--------|----------|
| 主要按钮 | `bg-primary` | `text-primary-foreground` | `hover:bg-primary/90` |
| 次要按钮 | `bg-secondary` | `text-secondary-foreground` | `hover:bg-secondary/80` |
| 轮廓按钮 | `bg-background` | `text-foreground` | `hover:bg-accent` |
| 幽灵按钮 | 透明 | `text-foreground` | `hover:bg-accent` |
| 危险按钮 | `bg-destructive` | `text-white` | `hover:bg-destructive/90` |

**按钮尺寸**：
- 小：`px-3 py-1.5 text-xs`
- 中：`px-4 py-2 text-sm`
- 大：`px-6 py-3 text-base`

**按钮必备样式**：`rounded-lg`、`transition-colors`、焦点环、禁用状态

### 6.2 输入框规范

- 高度：`h-10`
- 圆角：`rounded-lg`
- 边框：`border border-input`
- 内边距：`px-4 py-3`
- 字号：`text-sm`
- 占位符颜色：`placeholder:text-muted-foreground`
- 焦点样式：`focus-visible:ring-2 focus-visible:ring-ring`

### 6.3 卡片/容器规范

#### 6.3.1 基础容器结构

GitHub风格的容器包含三个核心区域：

```
┌─────────────────────────────────────────┐
│ 标题区（Header）                          │
│ - 标题 + 描述 + 操作按钮                   │
├─────────────────────────────────────────┤
│ 内容区（Content）                         │
│ - 主要内容                                │
├─────────────────────────────────────────┤
│ 操作区（Footer，可选）                     │
│ - 操作按钮                                │
└─────────────────────────────────────────┘
```

#### 6.3.2 容器样式规范

| 属性 | 值 | Tailwind类 |
|------|-----|-----------|
| 圆角 | 12px | `rounded-xl` 或 `rounded-lg` |
| 边框 | 1px | `border border-border` |
| 背景 | 卡片色 | `bg-card` |
| 内边距 | 24px | `p-6` |
| 阴影 | 微妙 | `shadow-sm` |

#### 6.3.3 标题区规范

| 元素 | 样式 |
|------|------|
| 容器 | `flex items-center justify-between pb-4 border-b border-border` |
| 标题 | `text-lg font-semibold` |
| 描述 | `text-sm text-muted-foreground mt-1` |
| 操作按钮 | `flex items-center gap-2` |

#### 6.3.4 内容区规范

| 场景 | 样式 |
|------|------|
| 默认 | `py-4` 或 `pt-4` |
| 表单内容 | `space-y-4` |
| 列表内容 | `divide-y divide-border` |
| 信息展示 | `space-y-3` |

#### 6.3.5 操作区规范

| 场景 | 样式 |
|------|------|
| 默认 | `flex items-center justify-end gap-3 pt-4 border-t border-border` |
| 左对齐 | `flex items-center gap-3 pt-4 border-t border-border` |
| 两端对齐 | `flex items-center justify-between pt-4 border-t border-border` |

#### 6.3.6 常见容器类型

| 类型 | 用途 | 特点 |
|------|------|------|
| **信息容器** | 展示静态信息 | 标题区 + 内容区 |
| **表单容器** | 表单提交 | 标题区 + 表单区 + 操作区 |
| **列表容器** | 列表数据 | 标题区 + 列表区 + 分页区 |
| **详情容器** | 详情展示 | 标题区 + 信息网格 |
| **设置容器** | 设置项分组 | 标题区 + 设置项列表 |

#### 6.3.7 容器组合模式

**嵌套容器**：大容器内嵌小容器
- 外层：`rounded-xl border border-border bg-card p-6`
- 内层：`rounded-lg border border-border bg-muted/30 p-4`

**并排容器**：多个容器水平排列
- 容器组：`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6`
- 单个容器：标准容器样式

**分组容器**：带分组的容器
- 分组标题：`text-sm font-medium text-muted-foreground mb-3`
- 分组内容：`space-y-2`

#### 6.3.8 现代感增强

| 效果 | 实现方式 |
|------|----------|
| 悬停提升 | `hover:shadow-lg hover:shadow-primary/5 hover:-translate-y-0.5 transition-all duration-200` |
| 玻璃效果 | `bg-card/80 backdrop-blur-sm` |
| 渐变边框 | 外层渐变背景 + 内层白色背景 |
| 发光边框 | `ring-1 ring-primary/10` |

### 6.4 表格规范

- 容器：`rounded-lg border border-border`
- 表头：`h-12 px-4 bg-muted/50 border-b border-border`
- 表头文字：`text-sm font-medium text-muted-foreground`
- 行悬停：`hover:bg-muted/50`
- 单元格：`px-4 py-3 text-sm`

### 6.5 表单布局规范

- 表单间距：`space-y-6`
- 字段组间距：`space-y-4`
- 标签与输入框间距：`space-y-2`
- 双列布局：`grid grid-cols-1 md:grid-cols-2 gap-4`
- 操作区：`flex items-center justify-end gap-3 pt-4`

---

## 七、圆角规范

### 7.1 圆角大小

| 变量名 | 值 | 像素 | 用途 |
|--------|-----|------|------|
| `--radius-sm` | 0.25rem | 4px | 小元素 |
| `--radius-md` | 0.375rem | 6px | 输入框 |
| `--radius-lg` | 0.5rem | 8px | 按钮 |
| `--radius-xl` | 0.75rem | 12px | 卡片 |
| `--radius-2xl` | 1rem | 16px | 大卡片 |
| `--radius-full` | 9999px | 圆形 | 头像 |

### 7.2 圆角使用规则

| 元素 | 圆角大小 | Tailwind类 |
|------|----------|------------|
| 按钮 | 8px | `rounded-lg` |
| 输入框 | 6px | `rounded-md` |
| 卡片 | 12px | `rounded-xl` |
| 标签/Badge | 4px | `rounded-sm` |
| 头像 | 圆形 | `rounded-full` |
| 模态框 | 12px | `rounded-xl` |
| 下拉菜单 | 8px | `rounded-lg` |

---

## 八、阴影规范

### 8.1 阴影层级

| 变量名 | 值 |
|--------|-----|
| `--shadow-sm` | `0 1px 2px 0 rgb(0 0 0 / 0.05)` |
| `--shadow-md` | `0 4px 6px -1px rgb(0 0 0 / 0.1)` |
| `--shadow-lg` | `0 10px 15px -3px rgb(0 0 0 / 0.1)` |
| `--shadow-xl` | `0 20px 25px -5px rgb(0 0 0 / 0.1)` |

### 8.2 阴影使用规则

| 元素 | 阴影 | Tailwind类 |
|------|------|------------|
| 卡片默认 | sm | `shadow-sm` |
| 卡片悬停 | lg + 色彩阴影 | `hover:shadow-lg hover:shadow-primary/5` |
| 下拉菜单 | lg | `shadow-lg` |
| 模态框 | xl | `shadow-xl` |
| 悬浮按钮 | lg + 色彩阴影 | `shadow-lg shadow-primary/10` |
| 高亮卡片 | xl + 色彩阴影 | `shadow-xl shadow-primary/5` |

**现代阴影技巧**：使用带颜色的阴影（如 `shadow-primary/5`）增加精致感

---

## 九、动画过渡规范

### 9.1 过渡时长

| 变量名 | 值 | 用途 |
|--------|-----|------|
| `--duration-150` | 150ms | 快速 - 按钮状态 |
| `--duration-200` | 200ms | 标准 - 悬停效果 |
| `--duration-300` | 300ms | 中等 - 展开/收起 |
| `--duration-500` | 500ms | 慢速 - 页面切换 |

### 9.2 缓动函数

| 变量名 | 值 |
|--------|-----|
| `--ease-in` | `cubic-bezier(0.4, 0, 1, 1)` |
| `--ease-out` | `cubic-bezier(0, 0, 0.2, 1)` |
| `--ease-in-out` | `cubic-bezier(0.4, 0, 0.2, 1)` |

### 9.3 常用过渡

- 颜色过渡：`transition-colors duration-200`
- 阴影过渡：`transition-shadow duration-200`
- 全属性过渡：`transition-all duration-300`
- 变换过渡：`transition-transform duration-200 hover:scale-105`

### 9.4 现代动画效果

| 效果 | 实现方式 | 用途 |
|------|----------|------|
| **悬停上浮** | `hover:-translate-y-1 transition-transform duration-200` | 卡片交互 |
| **悬停放大** | `hover:scale-105 transition-transform duration-200` | 按钮反馈 |
| **点击缩小** | `active:scale-95` | 按钮点击 |
| **淡入淡出** | `transition-opacity duration-300` | 显示/隐藏 |
| **滑入动画** | `animate-in fade-in slide-in-from-bottom-4` | 页面切换 |
| **骨架屏** | `animate-pulse` | 加载占位 |
| **旋转加载** | `animate-spin` | 加载状态 |
| **弹跳效果** | `animate-bounce` | 引导注意 |

---

## 十、图标规范

### 10.1 图标尺寸

| 变量名 | 值 | 像素 | 用途 |
|--------|-----|------|------|
| `--size-3` | 0.75rem | 12px | 行内图标 |
| `--size-4` | 1rem | 16px | 按钮图标 |
| `--size-5` | 1.25rem | 20px | 列表图标 |
| `--size-6` | 1.5rem | 24px | 标题图标 |
| `--size-8` | 2rem | 32px | 大图标 |

### 10.2 图标使用规范

- 按钮图标：`size-4`，与文字间距 `gap-2`
- 输入框图标：`size-4 text-muted-foreground`，定位 `absolute left-3 top-1/2 -translate-y-1/2`
- 纯图标按钮：容器 `size-10`，图标 `size-4`

---

## 十一、状态样式规范

### 11.1 交互状态

| 状态 | 样式 |
|------|------|
| 悬停 | `hover:bg-primary/90` |
| 焦点 | `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring` |
| 激活 | `active:scale-95` |
| 禁用 | `disabled:opacity-50 disabled:pointer-events-none disabled:cursor-not-allowed` |
| 加载 | 禁用状态 + 旋转图标 `animate-spin` |

### 11.2 表单验证状态

| 状态 | 边框颜色 | 焦点环 | 提示文字 |
|------|----------|--------|----------|
| 错误 | `border-destructive` | `focus-visible:ring-destructive` | `text-destructive` |
| 成功 | `border-success` | `focus-visible:ring-success` | `text-success` |

---

## 十二、可访问性规范

### 12.1 必须遵守

1. **语义化标签**：使用正确的HTML标签（`<button>`、`<nav>`、`<main>`等）
2. **ARIA属性**：为交互元素添加适当的ARIA属性
3. **焦点管理**：确保键盘可访问，焦点顺序合理
4. **颜色对比度**：文字与背景对比度至少4.5:1
5. **点击区域**：可点击元素最小44x44px

### 12.2 常用ARIA属性

- 图标按钮：`aria-label="操作描述"`，图标 `aria-hidden="true"`
- 输入框：`<label for="id">` 关联，提示文字 `aria-describedby="hint-id"`
- 导航：`<nav aria-label="导航名称">`，列表 `role="list"`

---

## 十三、常见页面模板

### 13.1 列表页面结构

1. **页面标题区**：标题 + 描述 + 操作按钮，`flex items-center justify-between`
2. **筛选区**：搜索框 + 筛选器，`rounded-lg border bg-card p-4`
3. **列表区**：表格或卡片列表，`rounded-lg border bg-card`
4. **分页区**：总数 + 分页组件，`flex items-center justify-between`

### 13.2 表单页面结构

1. **页面标题**：标题 + 描述
2. **表单卡片**：`max-w-2xl mx-auto rounded-xl border bg-card p-6`
3. **表单字段**：`space-y-6`
4. **操作区**：`flex items-center justify-end gap-3 pt-4 border-t`

### 13.3 详情页面结构

1. **面包屑导航**：列表链接 / 详情
2. **信息卡片**：标题 + 描述 + 操作按钮
3. **详细信息**：`grid grid-cols-1 md:grid-cols-2 gap-6`
4. **字段展示**：`<dl>` 定义列表，`flex justify-between`

---

## 十四、代码规范

### 14.1 类名顺序

1. **布局**：`flex`, `grid`, `block`, `hidden`
2. **定位**：`relative`, `absolute`, `fixed`
3. **尺寸**：`w-*`, `h-*`, `size-*`
4. **间距**：`p-*`, `m-*`, `gap-*`
5. **边框**：`border`, `rounded-*`
6. **背景**：`bg-*`
7. **文字**：`text-*`, `font-*`
8. **效果**：`shadow-*`, `opacity-*`
9. **过渡**：`transition-*`, `duration-*`
10. **状态**：`hover:*`, `focus:*`, `disabled:*`
11. **响应式**：`sm:*`, `md:*`, `lg:*`

### 14.2 组件提取

重复使用的样式必须提取为组件，避免重复的类名。

---

## 十五、禁止事项

### 15.1 绝对禁止

1. **禁止内联样式**：不使用 `style="..."`
2. **禁止任意值**：不使用 `p-[13px]`、`text-[17px]`
3. **禁止魔法数字**：不使用未定义的颜色值
4. **禁止过度嵌套**：DOM层级不超过5层
5. **禁止!important**：除非覆盖第三方库

### 15.2 不推荐

1. **不推荐固定宽度**：使用 `max-w-*` 而非 `w-[500px]`
2. **不推荐固定高度**：让内容决定高度
3. **不推荐无层次阴影**：阴影应有层次，服务于视觉深度
4. **不推荐无目的动画**：动画应服务于交互反馈，避免纯装饰性动画

---

## 十六、检查清单

开发完成后，必须检查以下项目：

### 16.1 需求清单对接检查（必须检查）

- [ ] 已读取并理解当前项目的需求清单
- [ ] 所有功能页面均对应需求清单中的功能项
- [ ] 所有API接口均使用需求清单中定义的接口路径
- [ ] HTTP方法（GET/POST/PUT/DELETE）与需求清单一致
- [ ] 请求参数与需求清单中的API定义匹配
- [ ] 响应数据结构与需求清单中的接口规范一致
- [ ] 功能完整覆盖需求清单中的核心功能
- [ ] 功能完整覆盖需求清单中的重要功能
- [ ] 辅助功能按优先级实现

### 16.2 UI设计规范检查

- [ ] 所有颜色使用语义化变量
- [ ] 所有间距使用设计系统值
- [ ] 所有圆角使用规范值
- [ ] 所有字体大小使用规范值
- [ ] 响应式布局正确
- [ ] 暗色模式支持
- [ ] 焦点状态可见
- [ ] 禁用状态正确
- [ ] 加载状态正确
- [ ] 错误状态正确
- [ ] 无障碍属性完整
- [ ] 无内联样式
- [ ] 无任意值
- [ ] 类名顺序规范

---

## 十七、参考资源

- [Tailwind CSS 文档](https://tailwindcss.com/docs)
- [shadcn/ui 组件库](https://ui.shadcn.com)
- [Radix UI 原语](https://www.radix-ui.com)
- [Material Design](https://m3.material.io)
- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines)
