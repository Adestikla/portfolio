import asyncio
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from backend.crawlers.job_spider import UniversalScraper
import json
from starlette.responses import StreamingResponse
from backend.crawlers.house_spider import HouseScraper

app = FastAPI()

# 1. 配置静态文件路径
script_dir = os.path.dirname(__file__)
static_path = os.path.join(script_dir, "../frontend/static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# 2. 配置 HTML 模板路径
template_path = os.path.join(script_dir, "../frontend/templates")
templates = Jinja2Templates(directory=template_path)

# 3. 首页路由
@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "我的设计作品集"})

# 4. 模拟爬虫数据接口
@app.get("/api/search")
async def get_data(request: Request, engine: str = "job", city: str = "深圳", keyword: str = "前端开发", edu: str = "不限"):
    queue = asyncio.Queue()

    async def run_scraper():
        try:
            # 路由分配
            if engine == "house":
                scraper = HouseScraper(headless=True)
                # 房源爬虫传入 keyword 和 city
                async for chunk in scraper.fetch_data_stream(keyword, city):
                    await queue.put(chunk)
            else:
                scraper = UniversalScraper(headless=False)
                # 招聘爬虫传入 keyword, edu 和 city
                async for chunk in scraper.fetch_data_stream(keyword, edu, city):
                    await queue.put(chunk)

        except Exception as e:
            await queue.put({"type": "log", "msg": f"❌ 核心引擎发生致命异常: {str(e)}"})
        finally:
            await queue.put(None)

    asyncio.create_task(run_scraper())

    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            chunk = await queue.get()
            if chunk is None:
                break
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ==========================================
# 准备脱敏代码字符串 (供作品集详情页渲染)
# ==========================================

# 模块 1：主服务端逻辑与安全防护 (完整版)
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

def check_server_environment():
    '''启动自检：防止代码被窃取后在非授权服务器运行'''
    try:
        public_ip = requests.get('https://api.ipify.org', timeout=5).text.strip()
        if public_ip != EXPECTED_PUBLIC_IP:
            logger.critical("⛔ 严重安全警告: 代码运行在错误的服务器上！启动终止。")
            sys.exit(1)
    except Exception as e:
        logger.error(f"IP 检查失败: {e}")

check_server_environment()
"""

# 模块 2：数据持久化与架构管理 (完整版)
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
            password='YOUR_DATABASE_PASSWORD',
            database='bot_db',
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn, "%s"
    except Exception as e:
        logger.error(f"连接数据库失败: {e}")
        return None, None

def _safe_close(conn, cursor):
    '''确保在任何情况下连接和游标都被安全关闭，防止内存泄漏。'''
    if cursor:
        try: cursor.close()
        except: pass
    if conn:
        try: conn.close()
        except: pass

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
    finally:
        _safe_close(conn, cursor)
"""

# 模块 3：支付集成与异步处理 (完整版)
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
        logger.error(f"Stripe Webhook 签名验证失败: {e}")
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

# 模块 4：前端交互与反爬虫技巧 (完整版)
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

// 4. 图片隐身还原脚本 (防简单爬虫)
document.addEventListener("DOMContentLoaded", function() {
    var sensitiveImgs = document.querySelectorAll('img[data-src]');
    sensitiveImgs.forEach(function(img) {
        img.src = img.getAttribute('data-src');
        img.removeAttribute('data-src'); // 销毁证据
    });
});

// 5. 动态邮箱混淆 (防垃圾邮件扫描)
document.addEventListener("DOMContentLoaded", function() {
    const p1 = "contact", p2 = "yourdomain", p3 = "com";
    const container = document.getElementById('contact-email-placeholder');
    if (container) {
        const mailLink = document.createElement('a');
        mailLink.href = `mailto:${p1}@${p2}.${p3}`;
        mailLink.innerText = `${p1}@${p2}.${p3}`;
        container.appendChild(mailLink);
    }
});
"""

# ==========================================
# 数据库：存储所有作品集信息
# ==========================================
PROJECTS_DB = {
    # ------ 第 1 章: UI/UX (1-4) 【已全部添加 gallery 结构】 ------
    1: {
        "title": "ANCIENT CHINESE<br>PHYSICS", "client": "Studio Adestikla", "role": "UI/UX & Branding", "year": "2025",
        "text": "这是一次将中国古代物理学理念与现代数字交互相融合的实验性项目。设计不仅关注视觉的冲击力，更深入探讨了东方哲学在赛博空间中的表达器。",
        "image": "/static/img/work1.jpg",
        "gallery": [
            "/static/img/work1_detail_1.jpg",
            "/static/img/work1_detail_2.jpg",
            "/static/img/work1_detail_3.jpg",
            "/static/img/work1_detail_4.jpg"
        ]
    },
    2: {
        "title": "WEREWOLF<br>CHARACTER", "client": "Personal Project", "role": "Digital Art", "year": "2026",
        "text": "关于狼人角色的数字艺术创作，重点展示了肌肉纹理与光影的极致刻画。",
        "image": "/static/img/work2.jpg",
        "gallery": [
            "/static/img/work2_detail_1.jpg",
            "/static/img/work2_detail_2.jpg",
            "/static/img/work2_detail_3.jpg",
            "/static/img/work2_detail_4.jpg"

        ]
    },
    3: {
        "title": "NUADU<br>PLATFORM", "client": "Personal Project", "role": "Web Design", "year": "2026",
        "text": "NUADU 在线教育平台的网页设计重构，提升了暗色模式下的阅读体验和交互反馈。",
        "image": "/static/img/work3.jpg",
        "gallery": [
            "/static/img/work3_detail_1.jpg",
            "/static/img/work3_detail_2.jpg",
            "/static/img/work3_detail_3.jpg",
            "/static/img/work3_detail_4.jpg"
        ]
    },
    4: {
        "title": "SPACE<br>EXPLORER", "client": "Personal Project", "role": "Mobile Interface", "year": "2026",
        "text": "太空探索主题的移动端 UI 设计，采用了玻璃拟态与 3D 悬浮元素的结合。",
        "image": "/static/img/work4.jpg",
        "gallery": [
            "/static/img/work4_detail_1.jpg",
            "/static/img/work4_detail_2.jpg",
            "/static/img/work4_detail_3.jpg",
            "/static/img/work4_detail_4.jpg"
        ]
    },

    # ------ 第 2 章: DATA INTELLIGENCE & SECURITY (5-8) 【代码展示组】 ------
    5: {
        "title": "CORE ARCHITECTURE<br>& WAF", "client": "Confidential SaaS", "role": "Backend Security", "year": "2025",
        "text": "实施了严格的 CSP 策略、环境指纹校验以及 API 接口的三重鉴权，确保服务端固若金汤。",
        "code": CODE_APP_PY,
        "filename": "app.py"
    },
    6: {
        "title": "DATABASE &<br>TRANSACTIONS", "client": "Confidential SaaS", "role": "Data Persistence", "year": "2025",
        "text": "处理数据库兼容性，管理连接池及确保高并发下的核心资产发放原子化交易安全。",
        "code": CODE_DB_PY,
        "filename": "database.py"
    },
    7: {
        "title": "WEBHOOK &<br>PAYMENTS", "client": "Confidential SaaS", "role": "API Integration", "year": "2025",
        "text": "使用 FastAPI 异步处理高并发的第三方 Webhook（Stripe），并严格验证数字签名防御伪造请求。",
        "code": CODE_WEBHOOK,
        "filename": "webhook_server.py"
    },
    8: {
        "title": "ANTI-SCRAPING<br>ENGINE", "client": "Confidential SaaS", "role": "Frontend Security", "year": "2025",
        "text": "部署了复杂的 JavaScript 调试器陷阱（Debugger Trap）与 DOM 动态混淆，有效抵御自动化爬虫。",
        "code": CODE_JS_SEC,
        "filename": "security.js"
    },

    # ------ 第 3 章: DECOUPLED SYSTEM (9-12) 【已全部添加 gallery 结构】 ------
    9: {
        "title": "CLOUD<br>INFRASTRUCTURE", "client": "Cloudify", "role": "Decoupled System", "year": "2026",
        "text": "云端解耦架构的管理后台设计，强调操作的严谨性与模块的清晰度。",
        "image": "/static/img/work9.jpg",
        "gallery": [
            "/static/img/work9_detail_1.jpg",
            "/static/img/work9_detail_2.jpg",
            "/static/img/work9_detail_3.jpg",
            "/static/img/work9_detail_4.jpg"
        ]
    },
    10: {
        "title": "MICROSERVICES<br>DASHBOARD", "client": "Cloudify", "role": "Decoupled System", "year": "2026",
        "text": "微服务监控仪表盘，实时显示各节点的健康状态与流量分发情况。",
        "image": "/static/img/work10.jpg",
        "gallery": [
            "/static/img/work10_detail_1.jpg",
            "/static/img/work10_detail_2.jpg",
            "/static/img/work10_detail_3.jpg",
            "/static/img/work10_detail_4.jpg"

        ]
    },
    11: {
        "title": "SERVERLESS<br>MANAGER", "client": "Cloudify", "role": "Decoupled System", "year": "2026",
        "text": "无服务器架构的部署与配置界面设计，简化了开发者的发布流程。",
        "image": "/static/img/work11.jpg",
        "gallery": [
            "/static/img/work11_detail_1.jpg",
            "/static/img/work11_detail_2.jpg",
            "/static/img/work11_detail_3.jpg",
            "/static/img/work11_detail_4.jpg"

        ]

    },
    12: {
        "title": "API<br>GATEWAY", "client": "Cloudify", "role": "Decoupled System", "year": "2026",
        "text": "API 网关的管理中枢视觉设定，提供了直观的限流与鉴权配置看板。",
        "image": "/static/img/work12.jpg",
        "gallery": [
            "/static/img/work12_detail_1.jpg",
            "/static/img/work12_detail_2.jpg",
            "/static/img/work12_detail_3.jpg",
            "/static/img/work12_detail_4.jpg"
        ]
    },
}


# ==========================================
# 详情页路由
# ==========================================
@app.get("/project/{project_id}", response_class=HTMLResponse)
async def project_detail(request: Request, project_id: int):
    # 根据 ID 获取数据，找不到就默认拿 1 号兜底
    project_data = PROJECTS_DB.get(project_id, PROJECTS_DB[1])

    # 核心算法：计算当前是本章的第几个 (1, 2, 3, 4)
    current_index = ((project_id - 1) % 4) + 1
    # 判断是否是本章的最后一张（即当前 index 是 4）
    is_last = (current_index == 4)
    # 计算下一个项目的 ID
    next_id = project_id + 1

    return templates.TemplateResponse("detail.html", {
        "request": request,
        "project": project_data,
        "current_index": current_index,
        "is_last": is_last,
        "next_id": next_id
    })