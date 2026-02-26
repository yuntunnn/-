# 通过 GitHub Pages 部署网页指南

> 本文档整理了将 HTML Demo 文件通过 GitHub 部署为在线网页的完整流程，方便日后查阅。

---

## 一、前置条件

| 条件 | 说明 |
|------|------|
| GitHub 账号 | 已注册并登录 |
| Git 仓库 | 项目已推送到 GitHub 仓库 |
| 仓库可见性 | **必须为 Public（公开）**，免费账户的私有仓库无法使用 GitHub Pages |

> ⚠️ 如果你的仓库是 Private（私有），需要先改为 Public，或者升级到 GitHub Enterprise 付费计划。

---

## 二、将仓库改为公开（如果是私有仓库）

1. 打开你的 GitHub 仓库页面
2. 点击顶部的 **Settings** 标签
3. 在左侧菜单选择 **General**
4. 向下滚动到最底部的 **Danger Zone** 区域
5. 点击 **"Change repository visibility"**
6. 选择 **Public**
7. 输入仓库名称确认，点击 **"I understand, change repository visibility"**

---

## 三、开启 GitHub Pages

### 步骤1：进入 Pages 设置

打开仓库的 Pages 设置页面：

```
https://github.com/你的用户名/你的仓库名/settings/pages
```

例如：`https://github.com/yuntunnn/-/settings/pages`

### 步骤2：配置部署源

在 **"Build and deployment"** 区域：

1. **Source** 下拉菜单 → 选择 **"Deploy from a branch"**
2. **Branch** 下拉菜单 → 选择 **`main`**（或你的默认分支名）
3. **Folder** 下拉菜单 → 选择 **`/ (root)`**
4. 点击 **Save** 按钮

### 步骤3：等待部署完成

- 保存后，GitHub 会自动开始构建和部署
- 通常需要 **1~2 分钟**
- 部署完成后，页面顶部会显示：**"Your site is live at https://你的用户名.github.io/仓库名/"**

### 步骤4：查找你的 Pages 链接

部署完成后，有**两种方式**找到你的 Pages 在线链接：

#### 方式A：在 Pages 设置页查看

回到设置页面 `https://github.com/你的用户名/你的仓库名/settings/pages`，部署成功后**页面顶部**会出现一个绿色区域：

```
✅ Your site is live at https://yuntunnn.github.io/-/
                                                    [ Visit site ]
```

点击 **"Visit site"** 按钮即可直接打开你的网站。

> 如果看不到绿色提示，说明还在部署中，稍等 1~2 分钟后刷新页面即可。

#### 方式B：从仓库主页查看

打开你的仓库主页（如 `https://github.com/yuntunnn/-`），在页面**右侧栏**的 **About** 区域，部署成功后会显示一个 🔗 链接图标，直接指向你的 GitHub Pages 网址。

### 步骤5：拼接具体文件的链接

GitHub Pages 给你的是一个**根地址**，要访问具体的 HTML 文件，需要在根地址后面拼上文件路径：

```
根地址：    https://yuntunnn.github.io/-/
+
文件路径：  4.弹窗Demo/弹窗方案A_多图轮播型.html
=
完整链接：  https://yuntunnn.github.io/-/4.弹窗Demo/弹窗方案A_多图轮播型.html
```

文件路径就是该文件在项目文件夹中的**相对路径**，和你在本地看到的目录结构一致。

---

## 四、访问你的网页

部署成功后，你的文件会自动映射为在线URL，规则如下：

```
本地文件路径:  项目根目录/文件夹/文件名.html
在线访问URL:  https://用户名.github.io/仓库名/文件夹/文件名.html
```

### 当前项目的在线链接

以仓库 `yuntunnn/-` 为例，部署后的访问链接为：

| 文件 | 在线链接 |
|------|---------|
| 方案A 轮播型 | `https://yuntunnn.github.io/-/4.弹窗Demo/弹窗方案A_多图轮播型.html` |
| 方案B 活动营销型 | `https://yuntunnn.github.io/-/4.弹窗Demo/弹窗方案B_活动营销型.html` |
| 方案B 网盘SVIP | `https://yuntunnn.github.io/-/4.弹窗Demo/弹窗方案B_网盘SVIP会员.html` |
| 方案B AI会员 | `https://yuntunnn.github.io/-/4.弹窗Demo/弹窗方案B_AI会员.html` |
| 方案B 扫描王 | `https://yuntunnn.github.io/-/4.弹窗Demo/弹窗方案B_扫描王会员.html` |
| 方案C 融合型 | `https://yuntunnn.github.io/-/4.弹窗Demo/弹窗方案C_融合轮播营销型.html` |

> 💡 如果链接中包含中文导致无法访问，可以在浏览器中打开后从地址栏复制已编码的URL。

---

## 五、更新网页内容

GitHub Pages 的内容会**自动跟随你的 Git 推送同步更新**。

当你修改了 HTML 文件后，只需执行以下命令：

```bash
# 1. 暂存所有改动
git add -A

# 2. 提交一个版本（写清楚这次改了什么）
git commit -m "这里写改动描述"

# 3. 推送到 GitHub
git push
```

推送后等待约 1~2 分钟，在线网页就会自动更新为最新内容。

---

## 六、国内访问注意事项

> ⚠️ **重要提醒**：GitHub Pages（`github.io` 域名）在中国大陆的访问并不稳定，分享给同事前请注意以下情况。

### 6.1 访问现状

| 情况 | 说明 |
|------|------|
| 部分地区/运营商 | 可以直接打开，但加载速度较慢 |
| 部分地区/运营商 | 完全无法访问（DNS污染或间歇性屏蔽） |
| 企业/公司网络 | 很多企业防火墙会屏蔽 GitHub 相关域名 |

**结论**：如果同事**没有网络代理（VPN）工具**，很可能无法打开 `github.io` 链接。

### 6.2 分享方式推荐

根据不同场景，推荐以下分享方式：

| 场景 | 推荐方式 | 是否需要翻墙 |
|------|---------|-------------|
| **日常分享给同事** | 直接发 HTML 文件（钉钉/飞书/微信） | ❌ 不需要 |
| **开会现场展示** | 本地端口分享（同一WiFi） | ❌ 不需要 |
| **异地协作（同事有VPN）** | GitHub Pages 链接 | ✅ 需要 |
| **个人在线备份** | GitHub Pages | ✅ 需要 |

### 6.3 如果需要国内可访问的在线部署

以下平台可作为替代，部署方式类似，但国内访问无障碍：

| 平台 | 说明 | 网址 |
|------|------|------|
| **Gitee Pages** | 国内版 GitHub，访问速度快 | https://gitee.com |
| **Vercel** | 自动部署，国内多数地区可访问 | https://vercel.com |
| **Netlify** | 类似 Vercel，免费额度足够 | https://netlify.com |

---

## 七、其他分享方式（不需要公开仓库）

如果你不方便将仓库公开，还有以下替代方案：

### 方式1：本地端口分享（适合现场评审）

在项目目录下启动一个临时 HTTP 服务器：

```bash
# 进入项目目录
cd /Users/jennifer/LDS/26-Q1/AI应用推广模块

# 启动服务器（端口8080）
python3 -m http.server 8080 --bind 0.0.0.0
```

然后查看你的局域网 IP：

```bash
ipconfig getifaddr en0
```

同事在**同一WiFi**下，访问 `http://你的IP:8080/` 即可看到所有文件。

| 属性 | 说明 |
|------|------|
| 优点 | 无需公开仓库，即开即用 |
| 限制 | 你和同事必须在同一局域网，且你的电脑需保持运行 |
| 停止服务 | 在终端按 `Ctrl + C` 即可停止 |

### 方式2：直接发送HTML文件

将 HTML 文件通过钉钉/飞书/微信/邮件直接发给同事，同事下载后双击即可在浏览器中打开。

> ⚠️ 注意：如果 HTML 引用了外部图片资源（如 `assets/` 文件夹中的图片），需要把整个 `4.弹窗Demo` 文件夹一起打包发送。

---

## 八、常用 Git 命令速查

| 命令 | 作用 |
|------|------|
| `git status` | 查看哪些文件有改动 |
| `git add -A` | 暂存所有改动 |
| `git commit -m "描述"` | 提交一个版本 |
| `git push` | 推送到 GitHub |
| `git log --oneline` | 查看版本历史 |
| `git pull` | 从 GitHub 拉取最新代码 |

