# 🌌 ADESTIKLA PORTFOLIO & CRAWLER MATRIX
> "Structuring the Chaos of the Web." 
> 
> 一个极致的 3D 沉浸式作品集与全网数据穿透矩阵。

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128.5-009688.svg)
![Three.js](https://img.shields.io/badge/Three.js-WebGL-black.svg)
![Playwright](https://img.shields.io/badge/Playwright-Web_Scraping-2EAD33.svg)
![GSAP](https://img.shields.io/badge/GSAP-Animations-88CE02.svg)
![Render](https://img.shields.io/badge/Render-CI%2FCD-000000.svg)

---

## 👁️ 项目概述 (Project Overview)

这不仅仅是一个展示设计作品的静态简历，而是一个**防御性极强、包含 3D 加速渲染、且底接真实 Python 自动化数据引擎**的全栈沙盒系统。
本项目通过解耦的云原生架构，在展示个人 UI/UX 与平面设计作品的同时，对外提供了一个真实的“全网数据爬虫终端（招聘/租房）”。配合极具赛博朋克风格的终端实时日志流（Server-Sent Events），将“后端硬核技术”与“前端先锋视觉”进行了完美融合。

<br>

## 🚀 核心架构与黑科技 (Core Features)

### 1. 🌌 双端隔离的 WebGL 粒子引擎
基于 `Three.js` 与自定义 GLSL Shader 编写的 3D 粒子系统。
- **PC 端满血释放**：渲染高达 **100,000 颗** 具有物理抖动和引力汇聚效果的发光粒子，配合 GSAP 实现多阶段（星空 -> 网页 -> 网络 -> 数据流 -> A字 Logo）的滚动视差动画。
- **移动端物理降维**：通过硬件嗅探进行端侧物理隔离，移动端自动降级为 **1,500 颗** 氛围粒子，在保证横滑抽卡极其丝滑的同时，保留顶级视觉质感。

### 2. 🕷️ 实时异步数据穿透矩阵 (SSE)
- 放弃传统的 HTTP 等待响应，采用 **FastAPI + Server-Sent Events (SSE)** 实现后端数据的实时单向推送。
- 底层挂载 **Playwright 无头浏览器集群**，突破现代站点的防爬机制。抓取到的数据与反爬日志会像黑客电影一样，逐行实时打印在前端的绿色代码终端上。

### 3. 🛡️ 激进的防御性前端沙盒
- **DOM 爆破与内存陷阱**：利用 `setInterval` 在内存中埋入高频的动态 `debugger` 陷阱。一旦系统嗅探到访客强制打开 F12 开发者工具，将在 100 毫秒内熔断网络发包能力，并**强行摧毁重写整个页面的 DOM 树**，弹出 `⚠️ SYSTEM LOCKED` 黑客警告屏。
- **防反向工程**：彻底封锁右键菜单及所有常见的调试快捷键（Ctrl+Shift+I / Ctrl+U）。

### 4. 📱 原生级的“层叠折叠 (Stacked Pills)” UI
完全抛弃臃肿的 JS 交互库，利用现代 CSS 的 `:has()` 伪类和 `:focus-within`，为移动端独立创造了极具 App 质感的“层叠表单展开”动画，确保键盘弹出时页面绝对稳定。

### 5. 🌐 自动化 CI/CD 流水线
深度集成 GitHub Actions 与 Render 平台，实现 `Push-to-Deploy`（推即部署）的云原生持续交付工作流。

<br>

## 🛠️ 技术栈 (Tech Stack)

* **Backend (后端)**: `FastAPI`, `Python 3.11+`, `Playwright` (Headless Chromium), `Uvicorn`, `Jinja2`
* **Frontend (前端)**: `HTML5`, `CSS3` (原生高级伪类引擎), `Vanilla JavaScript`
* **Graphics & Animation (图形与动画)**: `Three.js` (GLSL Shaders), `GSAP` (ScrollTrigger)
* **Deployment (部署)**: `Render`, `Gunicorn`, `Cloudflare`
<br>
