---
name: "mobile-app-dev"
description: "Uni-app移动App开发技能。专注于Uni-app框架开发跨平台移动应用，支持iOS/Android/H5/小程序多端发布。Invoke when: 创建Uni-app项目、开发App页面/组件、移动端UI设计、原生API调用、App性能优化、应用发布上架。"
---

# Uni-app 移动 App 开发技能

本技能定义了完整的 Uni-app 移动应用开发规范，确保生成的移动应用美观、高性能、易维护，并支持一套代码多端发布。

**重要**：本技能必须对接需求清单，确保开发的功能完整、API接口正确。

---

## 零、触发条件

**以下场景必须调用此技能：**

### 0.1 开发场景

- 创建新的 Uni-app 移动应用项目
- 开发 App 页面或组件
- 实现移动端 UI 界面
- 对接移动端原生 API
- 开发小程序应用
- 实现移动端手势交互

### 0.2 优化场景

- 优化 App 启动速度
- 优化列表滚动性能
- 减少包体积大小
- 优化内存使用
- 优化电池消耗
- 改善用户体验

### 0.3 集成场景

- 集成推送通知
- 集成地图定位
- 集成支付功能
- 集成分享功能
- 集成第三方 SDK

### 0.4 发布场景

- 应用签名打包（APK/IPA）
- 应用商店上架
- 版本更新管理
- 热更新配置

### 0.5 调试场景

- 真机调试
- 性能分析
- 崩溃日志分析
- 网络请求调试

---

## 零.1、需求清单对接（必须执行）

### 0.1.1 何时读取需求清单

**以下场景必须先读取需求清单：**
- 开始新的移动应用功能开发
- 创建新的 App 页面
- 对接新的 API 接口
- 开发列表页、详情页、表单页

### 0.1.2 需求清单路径

```
docs/工作空间/01-项目管理/[项目名]/01-需求/需求清单.md
```

### 0.1.3 从需求清单提取的关键信息

| 信息类型 | 提取内容 | 用途 |
|----------|----------|------|
| 功能ID | 如 M001、P001 | 组件/页面命名参考 |
| 功能名称 | 如 用户登录、商品列表 | 页面标题、导航项 |
| 功能描述 | 详细业务描述 | 理解业务逻辑 |
| API接口 | /api/v1/xxx | 移动端API调用 |
| HTTP方法 | GET/POST/PUT/DELETE | 对应HTTP请求 |
| 优先级 | 核心/重要/辅助 | 决定开发顺序 |
| 平台要求 | iOS/Android/小程序 | 确定兼容性范围 |

---

## 一、Uni-app 技术栈

### 1.1 Uni-app 核心优势

| 特性 | 说明 |
|------|------|
| **一码多端** | 一套代码编译到 iOS、Android、H5、各平台小程序 |
| **Vue 语法** | 基于 Vue.js，学习成本低 |
| **丰富插件** | 插件市场有大量现成插件 |
| **原生能力** | 支持 nvue 原生渲染，性能接近原生 |
| **国内生态** | 国内文档完善，社区活跃 |

### 1.2 支持的输出平台

| 平台 | 输出格式 | 说明 |
|------|----------|------|
| **Android** | APK/AAB | 安装包 |
| **iOS** | IPA | 安装包 |
| **H5** | Web应用 | 浏览器访问 |
| **微信小程序** | 小程序包 | 微信生态 |
| **支付宝小程序** | 小程序包 | 支付宝生态 |
| **抖音小程序** | 小程序包 | 字节跳动生态 |
| **百度小程序** | 小程序包 | 百度生态 |
| **QQ小程序** | 小程序包 | QQ生态 |

### 1.3 项目结构规范

```
uni-app-project/
├── pages/                    # 页面文件
│   ├── index/               # 首页
│   │   └── index.vue
│   ├── user/                # 用户模块
│   │   ├── login.vue
│   │   ├── profile.vue
│   │   └── settings.vue
│   └── ...
├── components/              # 公共组件
│   ├── navbar/
│   │   └── custom-navbar.vue
│   └── ...
├── static/                  # 静态资源
│   ├── images/
│   └── icons/
├── store/                   # Vuex 状态管理
│   ├── index.js
│   └── modules/
│       ├── user.js
│       └── app.js
├── api/                     # API 接口
│   ├── index.js
│   ├── user.js
│   └── request.js
├── utils/                   # 工具函数
│   ├── common.js
│   ├── auth.js
│   └── validate.js
├── uni_modules/             # uni-app 插件
├── App.vue                  # 应用入口
├── main.js                  # 主入口
├── manifest.json            # 应用配置
├── pages.json               # 页面路由配置
└── uni.scss                 # 全局样式变量
```

---

## 二、移动端设计规范

### 2.1 设计原则

1. **拇指友好**：重要操作放在拇指可达区域
2. **大触控区域**：最小点击区域 44x44 pt
3. **手势优先**：充分利用滑动手势
4. **状态反馈**：即时响应用户操作
5. **离线友好**：支持离线使用场景
6. **安全区域**：适配刘海屏、底部安全区

### 2.2 屏幕尺寸规范

#### iOS 设备

| 设备 | 尺寸 | 分辨率 | 安全区域 |
|------|------|--------|----------|
| iPhone 14 Pro Max | 6.7" | 2796×1290 | top: 59, bottom: 34 |
| iPhone 14 Pro | 6.1" | 2556×1179 | top: 59, bottom: 34 |
| iPhone 14 | 6.1" | 2532×1170 | top: 47, bottom: 34 |
| iPhone SE | 4.7" | 1334×750 | top: 20, bottom: 0 |

#### Android 设备

| 密度 | 比例 | 基准 |
|------|------|------|
| mdpi | 1x | 160dpi |
| hdpi | 1.5x | 240dpi |
| xhdpi | 2x | 320dpi |
| xxhdpi | 3x | 480dpi |
| xxxhdpi | 4x | 640dpi |

### 2.3 间距系统（rpx）

| 名称 | 值 | 用途 |
|------|-----|------|
| xs | 8rpx | 紧密元素间距 |
| sm | 16rpx | 相关元素间距 |
| md | 24rpx | 组件内间距 |
| lg | 32rpx | 卡片内边距 |
| xl | 48rpx | 区块间距 |
| xxl | 64rpx | 页面边距 |

### 2.4 字体规范

| 名称 | 大小 | 用途 |
|------|------|------|
| 大标题 | 68rpx | 页面标题 |
| 标题1 | 56rpx | 区块标题 |
| 标题2 | 44rpx | 卡片标题 |
| 标题3 | 40rpx | 小标题 |
| 正文 | 34rpx | 正文内容 |
| 次要 | 30rpx | 次要文字 |
| 辅助 | 26rpx | 辅助说明 |
| 注释 | 22rpx | 最小文字 |

### 2.5 颜色系统

```scss
// uni.scss 全局样式变量
$uni-color-primary: #007AFF;
$uni-color-success: #4cd964;
$uni-color-warning: #f0ad4e;
$uni-color-error: #dd524d;

$uni-text-color: #333333;
$uni-text-color-inverse: #ffffff;
$uni-text-color-grey: #999999;
$uni-text-color-placeholder: #808080;

$uni-bg-color: #ffffff;
$uni-bg-color-grey: #f8f8f8;
$uni-border-color: #e5e5e5;

$uni-spacing-sm: 16rpx;
$uni-spacing-md: 24rpx;
$uni-spacing-lg: 32rpx;
```

---

## 三、页面开发规范

### 3.1 页面基础结构

```vue
<template>
  <view class="page-container">
    <view class="page-content">
      <view class="list">
        <view 
          v-for="item in list" 
          :key="item.id" 
          class="item"
          @click="handleItemClick(item)"
        >
          <text class="item-title">{{ item.name }}</text>
          <text class="item-desc">{{ item.description }}</text>
        </view>
      </view>
      
      <uni-load-more :status="loadStatus" />
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      list: [],
      page: 1,
      pageSize: 10,
      loadStatus: 'more',
      loading: false,
    };
  },

  onLoad(options) {
    this.initData();
  },

  onShow() {
  },

  onReachBottom() {
    if (this.loadStatus !== 'noMore' && !this.loading) {
      this.loadMore();
    }
  },

  onPullDownRefresh() {
    this.refresh();
  },

  methods: {
    async initData() {
      this.page = 1;
      await this.fetchList();
    },

    async fetchList() {
      if (this.loading) return;
      
      this.loading = true;
      this.loadStatus = 'loading';
      
      try {
        const res = await this.$api.getList({
          page: this.page,
          pageSize: this.pageSize,
        });
        
        if (this.page === 1) {
          this.list = res.data || [];
        } else {
          this.list = [...this.list, ...(res.data || [])];
        }
        
        this.loadStatus = (res.data || []).length < this.pageSize ? 'noMore' : 'more';
      } catch (error) {
        this.loadStatus = 'more';
        uni.showToast({
          title: error.message || '加载失败',
          icon: 'none',
        });
      } finally {
        this.loading = false;
      }
    },

    async refresh() {
      this.page = 1;
      await this.fetchList();
      uni.stopPullDownRefresh();
    },

    async loadMore() {
      this.page++;
      await this.fetchList();
    },

    handleItemClick(item) {
      uni.navigateTo({
        url: `/pages/detail/detail?id=${item.id}`,
      });
    },
  },
};
</script>

<style lang="scss" scoped>
.page-container {
  min-height: 100vh;
  background-color: $uni-bg-color-grey;
}

.page-content {
  padding: $uni-spacing-lg;
}

.item {
  padding: $uni-spacing-lg;
  background-color: $uni-bg-color;
  border-radius: 16rpx;
  margin-bottom: $uni-spacing-md;
  
  &-title {
    font-size: 32rpx;
    color: $uni-text-color;
    font-weight: 500;
  }
  
  &-desc {
    font-size: 28rpx;
    color: $uni-text-color-grey;
    margin-top: $uni-spacing-sm;
  }
}
</style>
```

### 3.2 页面路由配置

```json
{
  "pages": [
    {
      "path": "pages/index/index",
      "style": {
        "navigationBarTitleText": "首页",
        "navigationBarBackgroundColor": "#ffffff",
        "navigationBarTextStyle": "black",
        "enablePullDownRefresh": true,
        "backgroundTextStyle": "dark"
      }
    },
    {
      "path": "pages/user/login",
      "style": {
        "navigationBarTitleText": "登录",
        "navigationStyle": "custom"
      }
    },
    {
      "path": "pages/user/profile",
      "style": {
        "navigationBarTitleText": "个人中心"
      }
    }
  ],
  "globalStyle": {
    "navigationBarTextStyle": "black",
    "navigationBarTitleText": "App名称",
    "navigationBarBackgroundColor": "#ffffff",
    "backgroundColor": "#f8f8f8"
  },
  "tabBar": {
    "color": "#999999",
    "selectedColor": "#007AFF",
    "backgroundColor": "#ffffff",
    "borderStyle": "black",
    "list": [
      {
        "pagePath": "pages/index/index",
        "text": "首页",
        "iconPath": "static/icons/home.png",
        "selectedIconPath": "static/icons/home-active.png"
      },
      {
        "pagePath": "pages/user/profile",
        "text": "我的",
        "iconPath": "static/icons/user.png",
        "selectedIconPath": "static/icons/user-active.png"
      }
    ]
  }
}
```

### 3.3 自定义导航栏

```vue
<template>
  <view class="custom-navbar" :style="{ paddingTop: statusBarHeight + 'px' }">
    <view class="navbar-content" :style="{ height: navBarHeight + 'px' }">
      <view class="navbar-left" @click="handleBack">
        <uni-icons type="left" size="20" color="#333" />
      </view>
      <view class="navbar-title">
        <text class="title-text">{{ title }}</text>
      </view>
      <view class="navbar-right">
        <slot name="right"></slot>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'CustomNavbar',
  
  props: {
    title: {
      type: String,
      default: '',
    },
  },
  
  data() {
    return {
      statusBarHeight: 20,
      navBarHeight: 44,
    };
  },
  
  created() {
    const systemInfo = uni.getSystemInfoSync();
    this.statusBarHeight = systemInfo.statusBarHeight;
  },
  
  methods: {
    handleBack() {
      const pages = getCurrentPages();
      if (pages.length > 1) {
        uni.navigateBack();
      } else {
        uni.switchTab({
          url: '/pages/index/index',
        });
      }
    },
  },
};
</script>

<style lang="scss" scoped>
.custom-navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 999;
  background-color: #ffffff;
}

.navbar-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32rpx;
}

.navbar-left {
  width: 80rpx;
  display: flex;
  align-items: center;
}

.navbar-title {
  flex: 1;
  text-align: center;
  
  .title-text {
    font-size: 34rpx;
    font-weight: 500;
    color: #333333;
  }
}

.navbar-right {
  width: 80rpx;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}
</style>
```

---

## 四、组件开发规范

### 4.1 组件基础结构

```vue
<template>
  <view class="custom-card" :class="{ 'is-active': active }" @click="handleClick">
    <view v-if="title" class="card-header">
      <text class="card-title">{{ title }}</text>
      <text v-if="subtitle" class="card-subtitle">{{ subtitle }}</text>
    </view>
    <view class="card-body">
      <slot></slot>
    </view>
    <view v-if="$slots.footer" class="card-footer">
      <slot name="footer"></slot>
    </view>
  </view>
</template>

<script>
export default {
  name: 'CustomCard',
  
  props: {
    title: {
      type: String,
      default: '',
    },
    subtitle: {
      type: String,
      default: '',
    },
    active: {
      type: Boolean,
      default: false,
    },
  },
  
  emits: ['click'],
  
  methods: {
    handleClick() {
      this.$emit('click');
    },
  },
};
</script>

<style lang="scss" scoped>
.custom-card {
  background-color: #ffffff;
  border-radius: 16rpx;
  overflow: hidden;
  
  &.is-active {
    border: 2rpx solid $uni-color-primary;
  }
}

.card-header {
  padding: 24rpx 32rpx;
  border-bottom: 1rpx solid $uni-border-color;
}

.card-title {
  font-size: 32rpx;
  font-weight: 500;
  color: $uni-text-color;
}

.card-subtitle {
  font-size: 26rpx;
  color: $uni-text-color-grey;
  margin-top: 8rpx;
}

.card-body {
  padding: 32rpx;
}

.card-footer {
  padding: 24rpx 32rpx;
  border-top: 1rpx solid $uni-border-color;
}
</style>
```

### 4.2 表单组件

```vue
<template>
  <view class="form-item">
    <view class="form-label" v-if="label">
      <text class="label-text">{{ label }}</text>
      <text v-if="required" class="required-mark">*</text>
    </view>
    <view class="form-content">
      <input
        class="form-input"
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :maxlength="maxlength"
        :disabled="disabled"
        @input="handleInput"
        @focus="handleFocus"
        @blur="handleBlur"
      />
      <view v-if="clearable && modelValue" class="clear-btn" @click="handleClear">
        <uni-icons type="clear" size="18" color="#ccc" />
      </view>
    </view>
    <view v-if="error" class="form-error">
      <text class="error-text">{{ error }}</text>
    </view>
  </view>
</template>

<script>
export default {
  name: 'FormItem',
  
  props: {
    label: {
      type: String,
      default: '',
    },
    modelValue: {
      type: [String, Number],
      default: '',
    },
    type: {
      type: String,
      default: 'text',
    },
    placeholder: {
      type: String,
      default: '请输入',
    },
    maxlength: {
      type: Number,
      default: 140,
    },
    required: {
      type: Boolean,
      default: false,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    clearable: {
      type: Boolean,
      default: false,
    },
    error: {
      type: String,
      default: '',
    },
  },
  
  emits: ['update:modelValue', 'focus', 'blur'],
  
  methods: {
    handleInput(event) {
      this.$emit('update:modelValue', event.detail.value);
    },
    
    handleFocus(event) {
      this.$emit('focus', event);
    },
    
    handleBlur(event) {
      this.$emit('blur', event);
    },
    
    handleClear() {
      this.$emit('update:modelValue', '');
    },
  },
};
</script>

<style lang="scss" scoped>
.form-item {
  margin-bottom: 32rpx;
}

.form-label {
  margin-bottom: 16rpx;
  
  .label-text {
    font-size: 28rpx;
    color: $uni-text-color;
  }
  
  .required-mark {
    color: $uni-color-error;
    margin-left: 8rpx;
  }
}

.form-content {
  display: flex;
  align-items: center;
  background-color: #f5f5f5;
  border-radius: 12rpx;
  padding: 0 24rpx;
  height: 88rpx;
}

.form-input {
  flex: 1;
  font-size: 30rpx;
  color: $uni-text-color;
}

.clear-btn {
  padding: 8rpx;
}

.form-error {
  margin-top: 12rpx;
  
  .error-text {
    font-size: 24rpx;
    color: $uni-color-error;
  }
}
</style>
```

---

## 五、API 请求封装

### 5.1 请求工具封装

```javascript
import store from '@/store';

const BASE_URL = 'https://api.example.com';

const request = (options) => {
  return new Promise((resolve, reject) => {
    const token = store.state.user.token;
    
    uni.showLoading({
      title: '加载中...',
      mask: true,
    });
    
    uni.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        ...options.header,
      },
      timeout: options.timeout || 30000,
      success: (res) => {
        uni.hideLoading();
        
        if (res.statusCode === 200) {
          if (res.data.code === 0 || res.data.code === 200) {
            resolve(res.data);
          } else if (res.data.code === 401) {
            store.commit('user/logout');
            uni.navigateTo({
              url: '/pages/user/login',
            });
            reject(new Error('登录已过期，请重新登录'));
          } else {
            uni.showToast({
              title: res.data.message || '请求失败',
              icon: 'none',
            });
            reject(new Error(res.data.message || '请求失败'));
          }
        } else {
          uni.showToast({
            title: '网络请求失败',
            icon: 'none',
          });
          reject(new Error('网络请求失败'));
        }
      },
      fail: (err) => {
        uni.hideLoading();
        uni.showToast({
          title: '网络连接失败',
          icon: 'none',
        });
        reject(err);
      },
    });
  });
};

export const get = (url, data, options = {}) => {
  return request({
    url,
    method: 'GET',
    data,
    ...options,
  });
};

export const post = (url, data, options = {}) => {
  return request({
    url,
    method: 'POST',
    data,
    ...options,
  });
};

export const put = (url, data, options = {}) => {
  return request({
    url,
    method: 'PUT',
    data,
    ...options,
  });
};

export const del = (url, data, options = {}) => {
  return request({
    url,
    method: 'DELETE',
    data,
    ...options,
  });
};

export default {
  get,
  post,
  put,
  del,
};
```

### 5.2 API 模块化

```javascript
import { get, post } from './request';

export default {
  getUserInfo() {
    return get('/api/v1/user/info');
  },
  
  login(data) {
    return post('/api/v1/user/login', data);
  },
  
  logout() {
    return post('/api/v1/user/logout');
  },
  
  getList(params) {
    return get('/api/v1/list', params);
  },
  
  getDetail(id) {
    return get(`/api/v1/detail/${id}`);
  },
};
```

### 5.3 全局挂载

```javascript
import api from './api';

const app = createSSRApp(App);

app.config.globalProperties.$api = api;

app.use(store);
app.mount('#app');
```

---

## 六、状态管理

### 6.1 Vuex Store 配置

```javascript
import { createStore } from 'vuex';
import user from './modules/user';
import app from './modules/app';

const store = createStore({
  modules: {
    user,
    app,
  },
  
  getters: {
    token: (state) => state.user.token,
    userInfo: (state) => state.user.userInfo,
    isLoggedIn: (state) => !!state.user.token,
  },
});

export default store;
```

### 6.2 User 模块

```javascript
const STORAGE_KEY = 'user_info';

const getDefaultState = () => ({
  token: uni.getStorageSync(STORAGE_KEY)?.token || '',
  userInfo: uni.getStorageSync(STORAGE_KEY)?.userInfo || null,
});

export default {
  namespaced: true,
  
  state: getDefaultState(),
  
  mutations: {
    SET_TOKEN(state, token) {
      state.token = token;
    },
    
    SET_USER_INFO(state, userInfo) {
      state.userInfo = userInfo;
    },
    
    login(state, { token, userInfo }) {
      state.token = token;
      state.userInfo = userInfo;
      uni.setStorageSync(STORAGE_KEY, { token, userInfo });
    },
    
    logout(state) {
      Object.assign(state, getDefaultState());
      uni.removeStorageSync(STORAGE_KEY);
    },
    
    updateUserInfo(state, userInfo) {
      state.userInfo = { ...state.userInfo, ...userInfo };
      uni.setStorageSync(STORAGE_KEY, {
        token: state.token,
        userInfo: state.userInfo,
      });
    },
  },
  
  actions: {
    async login({ commit }, loginData) {
      try {
        const res = await this.$api.login(loginData);
        commit('login', {
          token: res.data.token,
          userInfo: res.data.userInfo,
        });
        return res;
      } catch (error) {
        throw error;
      }
    },
    
    async logout({ commit }) {
      try {
        await this.$api.logout();
      } finally {
        commit('logout');
      }
    },
    
    async getUserInfo({ commit }) {
      const res = await this.$api.getUserInfo();
      commit('SET_USER_INFO', res.data);
      return res.data;
    },
  },
};
```

### 6.3 页面中使用

```vue
<template>
  <view class="page">
    <view v-if="isLoggedIn">
      <text>{{ userInfo.nickname }}</text>
      <button @click="handleLogout">退出登录</button>
    </view>
    <view v-else>
      <button @click="goLogin">去登录</button>
    </view>
  </view>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';

export default {
  computed: {
    ...mapGetters(['isLoggedIn', 'userInfo']),
  },
  
  methods: {
    ...mapActions('user', ['logout']),
    
    goLogin() {
      uni.navigateTo({
        url: '/pages/user/login',
      });
    },
    
    async handleLogout() {
      try {
        await this.logout();
        uni.showToast({
          title: '已退出登录',
          icon: 'success',
        });
      } catch (error) {
        console.error(error);
      }
    },
  },
};
</script>
```

---

## 七、原生API调用

### 7.1 相机与相册

```javascript
export function chooseImage(options = {}) {
  return new Promise((resolve, reject) => {
    uni.chooseImage({
      count: options.count || 1,
      sizeType: options.sizeType || ['compressed'],
      sourceType: options.sourceType || ['album', 'camera'],
      success: (res) => {
        resolve(res.tempFilePaths);
      },
      fail: (err) => {
        reject(err);
      },
    });
  });
}

export function previewImage(urls, current = 0) {
  uni.previewImage({
    urls,
    current,
  });
}
```

### 7.2 定位服务

```javascript
export function getLocation() {
  return new Promise((resolve, reject) => {
    uni.getLocation({
      type: 'gcj02',
      success: (res) => {
        resolve({
          latitude: res.latitude,
          longitude: res.longitude,
          accuracy: res.accuracy,
        });
      },
      fail: (err) => {
        reject(err);
      },
    });
  });
}

export function openLocation(latitude, longitude, name, address) {
  uni.openLocation({
    latitude,
    longitude,
    name,
    address,
    scale: 18,
  });
}
```

### 7.3 扫码功能

```javascript
export function scanCode() {
  return new Promise((resolve, reject) => {
    uni.scanCode({
      onlyFromCamera: false,
      scanType: ['qrCode', 'barCode'],
      success: (res) => {
        resolve({
          result: res.result,
          scanType: res.scanType,
        });
      },
      fail: (err) => {
        reject(err);
      },
    });
  });
}
```

### 7.4 推送通知

```javascript
export function getPushClientId() {
  return new Promise((resolve, reject) => {
    const clientInfo = plus.push.getClientInfo();
    if (clientInfo && clientInfo.clientid) {
      resolve(clientInfo.clientid);
    } else {
      reject(new Error('获取推送ID失败'));
    }
  });
}

export function createPushMessage(title, content, payload = {}) {
  plus.push.createMessage(content, JSON.stringify(payload), {
    title,
  });
}
```

### 7.5 支付功能

```javascript
export function requestPayment(provider, orderInfo) {
  return new Promise((resolve, reject) => {
    uni.requestPayment({
      provider,
      orderInfo,
      success: (res) => {
        resolve(res);
      },
      fail: (err) => {
        reject(err);
      },
    });
  });
}

export function wxPay(orderInfo) {
  return requestPayment('wxpay', orderInfo);
}

export function aliPay(orderInfo) {
  return requestPayment('alipay', orderInfo);
}
```

### 7.6 权限管理

```javascript
export function checkPermission(permission) {
  return new Promise((resolve, reject) => {
    if (uni.getSystemInfoSync().platform === 'android') {
      plus.android.requestPermissions(
        [permission],
        (result) => {
          if (result.granted.length > 0) {
            resolve(true);
          } else if (result.deniedPresent.length > 0) {
            resolve(false);
          } else {
            resolve(false);
          }
        },
        (error) => {
          reject(error);
        }
      );
    } else {
      resolve(true);
    }
  });
}

export async function requestCameraPermission() {
  const permission = 'android.permission.CAMERA';
  const hasPermission = await checkPermission(permission);
  if (!hasPermission) {
    uni.showModal({
      title: '提示',
      content: '需要相机权限才能使用此功能',
      success: (res) => {
        if (res.confirm) {
          plus.runtime.openURL('android.settings.APPLICATION_DETAILS_SETTINGS');
        }
      },
    });
  }
  return hasPermission;
}
```

---

## 八、性能优化

### 8.1 列表优化

```vue
<template>
  <scroll-view
    scroll-y
    :style="{ height: scrollHeight + 'px' }"
    @scrolltolower="loadMore"
  >
    <view v-for="item in list" :key="item.id" class="item">
      {{ item.name }}
    </view>
    <uni-load-more :status="loadStatus" />
  </scroll-view>
</template>

<script>
export default {
  data() {
    return {
      list: [],
      page: 1,
      pageSize: 20,
      loadStatus: 'more',
      scrollHeight: 500,
    };
  },
  
  mounted() {
    this.calcScrollHeight();
    this.fetchList();
  },
  
  methods: {
    calcScrollHeight() {
      const systemInfo = uni.getSystemInfoSync();
      this.scrollHeight = systemInfo.windowHeight - 100;
    },
    
    async loadMore() {
      if (this.loadStatus === 'noMore') return;
      this.page++;
      await this.fetchList();
    },
    
    async fetchList() {
      this.loadStatus = 'loading';
      try {
        const res = await this.$api.getList({
          page: this.page,
          pageSize: this.pageSize,
        });
        
        this.list = this.page === 1 
          ? res.data 
          : [...this.list, ...res.data];
        
        this.loadStatus = res.data.length < this.pageSize ? 'noMore' : 'more';
      } catch (error) {
        this.loadStatus = 'more';
      }
    },
  },
};
</script>
```

### 8.2 图片优化

```vue
<template>
  <image
    :src="imageSrc"
    :mode="mode"
    :lazy-load="lazyLoad"
    :webp="true"
    class="optimized-image"
    @load="handleLoad"
    @error="handleError"
  />
</template>

<script>
export default {
  props: {
    src: {
      type: String,
      default: '',
    },
    mode: {
      type: String,
      default: 'aspectFill',
    },
    lazyLoad: {
      type: Boolean,
      default: true,
    },
    placeholder: {
      type: String,
      default: '/static/images/placeholder.png',
    },
  },
  
  data() {
    return {
      imageSrc: this.placeholder,
      loaded: false,
    };
  },
  
  watch: {
    src: {
      immediate: true,
      handler(val) {
        if (val) {
          this.imageSrc = val;
        }
      },
    },
  },
  
  methods: {
    handleLoad() {
      this.loaded = true;
    },
    
    handleError() {
      this.imageSrc = this.placeholder;
    },
  },
};
</script>

<style lang="scss" scoped>
.optimized-image {
  width: 100%;
  height: 100%;
  background-color: #f5f5f5;
}
</style>
```

### 8.3 分包加载

```json
{
  "pages": [
    {
      "path": "pages/index/index",
      "style": {
        "navigationBarTitleText": "首页"
      }
    }
  ],
  "subPackages": [
    {
      "root": "pages/user",
      "pages": [
        {
          "path": "login",
          "style": {
            "navigationBarTitleText": "登录"
          }
        },
        {
          "path": "profile",
          "style": {
            "navigationBarTitleText": "个人中心"
          }
        }
      ]
    },
    {
      "root": "pages/order",
      "pages": [
        {
          "path": "list",
          "style": {
            "navigationBarTitleText": "订单列表"
          }
        },
        {
          "path": "detail",
          "style": {
            "navigationBarTitleText": "订单详情"
          }
        }
      ]
    }
  ],
  "preloadRule": {
    "pages/index/index": {
      "network": "all",
      "packages": ["pages/user"]
    }
  }
}
```

---

## 九、发布规范

### 9.1 Android 打包

#### 云打包（推荐）

1. 在 HBuilderX 中打开项目
2. 点击「发行」→「原生App-云打包」
3. 选择 Android 平台
4. 配置证书（可使用测试证书）
5. 点击打包，等待完成

#### 本地打包

```bash
# 1. 生成签名密钥
keytool -genkeypair -v -keystore my-release-key.keystore -alias my-key-alias -keyalg RSA -keysize 2048 -validity 10000

# 2. 在 manifest.json 中配置
{
  "app-plus": {
    "android": {
      "keystore": "my-release-key.keystore",
      "alias": "my-key-alias",
      "password": "your-password"
    }
  }
}

# 3. 本地打包
# 在 HBuilderX 中：发行 → 原生App-本地打包
```

### 9.2 iOS 打包

1. 在 Apple Developer 创建 App ID
2. 创建开发/发布证书
3. 创建 Provisioning Profile
4. 在 HBuilderX 中配置证书
5. 云打包或本地打包生成 IPA
6. 上传到 App Store Connect

### 9.3 应用配置

```json
{
  "name": "应用名称",
  "appid": "__UNI__XXXXXXX",
  "description": "应用描述",
  "versionName": "1.0.0",
  "versionCode": "100",
  "app-plus": {
    "splashscreen": {
      "alwaysShowBeforeRender": true,
      "waiting": true,
      "autoclose": true,
      "delay": 0
    },
    "statusbar": {
      "immersed": true,
      "style": "dark"
    },
    "android": {
      "permissions": [
        "<uses-permission android:name=\"android.permission.CAMERA\"/>",
        "<uses-permission android:name=\"android.permission.ACCESS_FINE_LOCATION\"/>"
      ],
      "minSdkVersion": 21,
      "targetSdkVersion": 30
    },
    "ios": {
      "idfa": false,
      "capabilities": {
        "entitlements": {
          "com.apple.developer.associated-domains": []
        }
      }
    }
  }
}
```

### 9.4 版本号规范

| 版本类型 | 格式 | 说明 |
|----------|------|------|
| 主版本 | X.0.0 | 重大更新、不兼容变更 |
| 次版本 | 1.X.0 | 新功能、向后兼容 |
| 修订版本 | 1.0.X | Bug修复、小改进 |
| 构建号 | 自增整数 | 每次构建递增 |

---

## 十、检查清单

### 10.1 需求清单对接检查

- [ ] 已读取并理解当前项目的需求清单
- [ ] 所有功能页面均对应需求清单中的功能项
- [ ] 所有API接口均使用需求清单中定义的接口路径
- [ ] HTTP方法与需求清单一致
- [ ] 请求参数与需求清单中的API定义匹配
- [ ] 响应数据结构与需求清单中的接口规范一致
- [ ] 功能完整覆盖需求清单中的核心功能

### 10.2 UI设计规范检查

- [ ] 所有颜色使用设计系统定义的颜色
- [ ] 所有间距使用规范值
- [ ] 所有字体大小使用规范值
- [ ] 适配安全区域（刘海屏、底部安全区）
- [ ] 适配深色模式
- [ ] 适配横屏模式（如需要）

### 10.3 性能优化检查

- [ ] 列表使用虚拟滚动或分页加载
- [ ] 图片使用懒加载和缓存
- [ ] 避免不必要的重渲染
- [ ] 分包加载配置
- [ ] 包体积优化

### 10.4 安全检查

- [ ] 敏感数据使用安全存储
- [ ] 网络请求使用HTTPS
- [ ] Token 存储安全
- [ ] 权限请求合理

### 10.5 兼容性检查

- [ ] iOS版本兼容性测试
- [ ] Android版本兼容性测试
- [ ] 不同屏幕尺寸适配
- [ ] 深色模式适配
- [ ] 各平台小程序兼容性测试

---

## 十一、参考资源

### 11.1 官方文档

- [Uni-app 官方文档](https://uniapp.dcloud.io/)
- [Vue.js 官方文档](https://cn.vuejs.org/)
- [Vuex 官方文档](https://vuex.vuejs.org/zh/)
- [Uni-app 插件市场](https://ext.dcloud.net.cn/)

### 11.2 设计规范

- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [Material Design](https://m3.material.io/)
- [微信小程序设计指南](https://developers.weixin.qq.com/miniprogram/design/)

### 11.3 工具推荐

- [HBuilderX](https://www.dcloud.io/hbuilderx.html) - Uni-app 开发工具
- [微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
- [Android Studio](https://developer.android.com/studio) - Android 本地打包
- [Xcode](https://developer.apple.com/xcode/) - iOS 本地打包
