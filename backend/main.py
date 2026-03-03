import asyncio

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from backend.crawlers.job_spider import UniversalScraper
import json
from starlette.responses import StreamingResponse

app = FastAPI()

# 1. 配置静态文件路径（CSS, JS, 你的作品图片）
# 因为 main.py 在 backend 文件夹里，所以需要跳出一层找到 frontend
script_dir = os.path.dirname(__file__)
static_path = os.path.join(script_dir, "../frontend/static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# 2. 配置 HTML 模板路径
template_path = os.path.join(script_dir, "../frontend/templates")
templates = Jinja2Templates(directory=template_path)

# 3. 首页路由：渲染你的作品集首页
@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    # 这里之后可以传入你爬虫抓到的数据，比如：jobs=latest_jobs
    return templates.TemplateResponse("index.html", {"request": request, "title": "我的设计作品集"})

# 4. 模拟爬虫数据接口（先占位，方便前端调用）
@app.get("/api/search")
async def get_data(request: Request, keyword: str = "UI设计", edu: str = "不限"):
    scraper = UniversalScraper(headless=True)

    # 创建一个消息队列，作为爬虫和前端之间的“缓冲池”
    queue = asyncio.Queue()

    # 1. 生产者：定义一个独立的后台爬虫任务
    async def run_scraper():
        try:
            async for chunk in scraper.fetch_data_stream(keyword, edu):
                await queue.put(chunk)  # 把日志塞进队列
        except Exception as e:
            await queue.put({"type": "log", "msg": f"❌ 爬虫发生致命异常: {str(e)}"})
        finally:
            await queue.put(None)  # 爬虫结束时，丢入一个 None 作为结束信号

    # 2. 将爬虫丢进后台默默运行，彻底脱离 HTTP 请求的绑架！
    asyncio.create_task(run_scraper())

    # 3. 消费者：不断从队列里拿出日志，推给前台网页
    async def event_generator():
        while True:
            # 如果访客不耐烦关掉了网页，立刻停止推送，节省服务器性能
            if await request.is_disconnected():
                break

            chunk = await queue.get()  # 等待爬虫往队列里扔东西
            if chunk is None:  # 收到结束信号，停止推送
                break

            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ==========================================
# 准备脱敏代码字符串 (供作品集详情页渲染)
# ==========================================

# [cite_start]模块 1：主服务端逻辑与安全防护 [cite: 4]
CODE_APP_PY = """# _*_coding : utf-8 _*_
from flask import Flask, request, render_template, jsonify
import hashlib, hmac, logging, sys, requests

# 🔒 服务器环境指纹 (脱敏版)
EXPECTED_PUBLIC_IP = "YOUR_SERVER_PUBLIC_IP"
EXPECTED_UUID = "YOUR_CLOUDFLARE_WAF_UUID"
BOT_API_KEY = "YOUR_BOT_SECRET_API_KEY"

app = Flask(__name__)

@app.after_request
def add_security_headers(response):
    '''设置严格的安全响应头，防御 XSS、点击劫持和恶意广告注入'''
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    csp_policy = "default-src 'self'; script-src 'self' 'unsafe-inline';"
    response.headers['Content-Security-Policy'] = csp_policy
    return response

def verify_request():
    '''机器人专用远程 API 三重验证'''
    auth_header = request.headers.get('Authorization')
    if auth_header != f"Bearer {BOT_API_KEY}":
        return False, "Invalid API Key"

    req_uuid = request.headers.get('x-developer-id')
    if req_uuid != EXPECTED_UUID:
        return False, "Invalid UUID Identity"

    return True, "OK"
"""

# [cite_start]模块 2：数据持久化与架构管理 [cite: 15]
CODE_DB_PY = """# _*_coding : utf-8 _*_
import pymysql
import datetime
import logging

logger = logging.getLogger('database')

def get_db_connection():
    '''获取安全的数据库连接 (脱敏密码)'''
    try:
        conn = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='YOUR_DATABASE_PASSWORD',  # 已脱敏
            database='bot_db',
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn, "%s"
    except Exception as e:
        logger.error(f"连接数据库失败: {e}")
        return None, None

def grant_membership(user_id, days=30, tier=1):
    '''核心业务：授予会员并执行原子化的额度重置'''
    conn, cursor = None, None
    try:
        expires_date = datetime.date.today() + datetime.timedelta(days=days)
        cur_month = datetime.datetime.now().strftime("%Y-%m")
        conn, ph = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(f'''
            UPDATE users SET status = {ph}, membership_expires = {ph}, 
            membership_tier = {ph}, char_usage_count = 0, last_reset_month = {ph}
            WHERE user_id = {ph}
        ''', ('member', expires_date, tier, cur_month, user_id))

        conn.commit()
        return True
    except Exception as e:
        if conn: conn.rollback()
        return False
"""

# [cite_start]模块 3：支付集成与异步处理 [cite: 25]
CODE_WEBHOOK = """# _*_coding : utf-8 _*_
from fastapi import FastAPI, Request, Header, HTTPException
import stripe
import logging

app = FastAPI()
stripe.api_key = "YOUR_STRIPE_API_KEY"
logger = logging.getLogger("webhook_server")

@app.post("/YOUR_WEBHOOK_SECRET_PATH/stripe-notify")
async def handle_stripe_webhook(request: Request, stripe_signature: str | None = Header(None)):
    '''处理 Stripe 支付回调，验证签名并发放权益'''
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=stripe_signature, secret="YOUR_WEBHOOK_SECRET"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        telegram_user_id = session.get('client_reference_id')

        if telegram_user_id:
            # 更新共享数据库，完成发货
            database.grant_membership(int(telegram_user_id), days=30, tier=1)
            logger.info(f"Stripe 支付成功！已为 User {telegram_user_id} 发货。")

    return {"status": "received"}
"""

# [cite_start]模块 4：前端交互与反爬虫技巧 [cite: 32]
CODE_JS_SEC = """// ==========================================
// 🛡️ 前端安全防护模块 (脱敏版)
// ==========================================

// 1. 禁止右键菜单与常用开发者快捷键
document.addEventListener('contextmenu', e => e.preventDefault());
document.onkeydown = function (e) {
    if (e.keyCode == 123 || (e.ctrlKey && e.shiftKey) || (e.ctrlKey && e.keyCode == 85)) {
        return false;
    }
};

// 2. 调试器陷阱 (防扒站)
(function () {
    setInterval(function () {
        var start = new Date();
        debugger; // 陷阱：打开控制台会导致页面卡死
        var end = new Date();
        if (end - start > 100) {
            document.body.innerHTML = '<h1>⚠️ 非法调试 / Access Denied</h1>';
        }
    }, 1000);
})();

// 3. 禁止被 iframe 嵌套 (防止点击劫持)
if (window.top !== window.self) { 
    window.top.location = window.self.location; 
}
"""

# 详情页路由
PROJECTS_DB = {
    # ------ 第 1 章: UI/UX (1-4) ------
    1: {"title": "ANCIENT CHINESE<br>PHYSICS", "client": "Studio Adestikla", "role": "UI/UX & Branding", "year": "2025", "text": "这是一次将中国古代物理学理念与现代数字交互相融合的实验性项目。设计不仅关注视觉的冲击力，更深入探讨了东方哲学在赛博空间中的表达器。", "image": "/static/img/work1.jpg"},
    2: {"title": "WEREWOLF<br>CHARACTER", "client": "Personal Project", "role": "Digital Art", "year": "2026", "text": "关于狼人角色的概念设计与插画创作，探索光影、肌肉张力以及在数字艺术环境下的表现力。", "image": "/static/img/work2.jpg"},
    3: {"title": "NUADU<br>PLATFORM", "client": "Personal Project", "role": "Web Design", "year": "2026", "text": "教育平台的界面设计，重点在于信息的层级划分和用户的学习流体验优化。", "image": "/static/img/work3.jpg"},
    4: {"title": "SPACE<br>EXPLORER", "client": "Personal Project", "role": "Mobile Interface", "year": "2026", "text": "一款太空探索应用的概念设计，使用了鲜明的色彩和直观的卡片式交互。", "image": "/static/img/work4.jpg"},

    # ------ 第 2 章: DATA INTELLIGENCE & SECURITY (5-8) ------
    5: {
        "title": "CORE ARCHITECTURE<br>& WAF",
        "client": "Confidential SaaS",
        "role": "Backend Security",
        "year": "2025",
        "text": "实施了严格的 CSP 策略、环境指纹校验以及 API 接口的三重鉴权，确保服务端固若金汤。",
        "code": CODE_APP_PY,  # 使用刚定义的代码字符串
        "filename": "app.py"  # 指定黑客终端显示的文件名
    },
    6: {
        "title": "DATABASE &<br>TRANSACTIONS",
        "client": "Confidential SaaS",
        "role": "Data Persistence",
        "year": "2025",
        "text": "处理数据库兼容性，管理连接池及确保高并发下的核心资产发放原子化交易安全。",
        "code": CODE_DB_PY,
        "filename": "database.py"
    },
    7: {
        "title": "WEBHOOK &<br>PAYMENTS",
        "client": "Confidential SaaS",
        "role": "API Integration",
        "year": "2025",
        "text": "使用 FastAPI 异步处理高并发的第三方 Webhook（Stripe），并严格验证数字签名防御伪造请求。",
        "code": CODE_WEBHOOK,
        "filename": "webhook_server.py"
    },
    8: {
        "title": "ANTI-SCRAPING<br>ENGINE",
        "client": "Confidential SaaS",
        "role": "Frontend Security",
        "year": "2025",
        "text": "部署了复杂的 JavaScript 调试器陷阱（Debugger Trap）与 DOM 动态混淆，有效抵御自动化爬虫。",
        "code": CODE_JS_SEC,
        "filename": "security.js"
    },
    # ------ 第 3 章: DECOUPLED SYSTEM (9-12) ------
    9: {"title": "CLOUD<br>INFRASTRUCTURE", "client": "Cloudify", "role": "Decoupled System", "year": "2026", "text": "云端解耦架构的管理后台设计，强调操作的严谨性与模块的清晰度。", "image": "/static/img/work9.jpg"},
    10: {"title": "MICROSERVICES<br>DASHBOARD", "client": "Cloudify", "role": "Decoupled System", "year": "2026", "text": "微服务监控仪表盘，实时显示各节点的健康状态。", "image": "/static/img/work10.jpg"},
    11: {"title": "SERVERLESS<br>MANAGER", "client": "Cloudify", "role": "Decoupled System", "year": "2026", "text": "无服务器架构的部署与配置界面设计。", "image": "/static/img/work11.jpg"},
    12: {"title": "API<br>GATEWAY", "client": "Cloudify", "role": "Decoupled System", "year": "2026", "text": "API 网关的管理中枢视觉设定。", "image": "/static/img/work12.jpg"},

}


# 详情页路由
@app.get("/project/{project_id}", response_class=HTMLResponse)
async def project_detail(request: Request, project_id: int):
    # 根据 ID 获取数据，找不到就默认拿 1 号兜底
    project_data = PROJECTS_DB.get(project_id, PROJECTS_DB[1])

    # 核心算法：计算当前是本章的第几个 (1, 2, 3, 4)
    # 比如 ID 是 1, 2, 3, 4，算出来就是 1, 2, 3, 4
    # 比如 ID 是 5, 6, 7, 8，算出来依然是 1, 2, 3, 4
    current_index = ((project_id - 1) % 4) + 1

    # 判断是否是本章的最后一张（即当前 index 是 4）
    is_last = (current_index == 4)

    # 计算下一个项目的 ID
    next_id = project_id + 1

    return templates.TemplateResponse("detail.html", {
        "request": request,
        "project": project_data,
        "current_index": current_index,  # 传给前端显示页码
        "is_last": is_last,  # 传给前端判断是否到底
        "next_id": next_id  # 传给前端下一页链接
    })