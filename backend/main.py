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
async def read_item(request: Request, lang: str = "en"):
    t = I18N_DB.get(lang, I18N_DB["en"])
    # 核心：根据语言选择对应的数据字典传给前端
    projects = PROJECTS_ZH if lang == "zh" else PROJECTS_EN

    return templates.TemplateResponse("index.html", {
        "request": request,
        "t": t,
        "projects": projects,  # 把整个 12 个作品的数据传过去！
        "lang": lang
    })
# 4. 模拟爬虫数据接口
@app.get("/api/search")
async def get_data(request: Request, engine: str = "job", city: str = "深圳", keyword: str = "前端开发", edu: str = "不限"):
    queue = asyncio.Queue()

    async def run_scraper():
        try:
            # 路由分配
            if engine == "house":
                scraper = HouseScraper(headless=True)
                async for chunk in scraper.fetch_data_stream(keyword):
                    await queue.put(chunk)
            else:
                scraper = UniversalScraper(headless=True)
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
PROJECTS_ZH = {
    # ------ 第 1 章: CORE ARCHITECTURE & SECURITY (本站架构与防护) ------
    1: {
        "grid_title": "CI/CD Pipeline",
        "title": "CI/CD<br>PIPELINE", "client": "Personal Project", "role": "Cloud Architecture", "year": "2026",
        "text": "基于 GitHub Actions 与 Render 构建的云原生持续交付流水线。摒弃传统的手动运维，实现了“代码推送即部署”的全自动化工作流。通过容器化环境隔离与秒级构建，确保了底层双端渲染引擎与核心业务的零宕机更新。",
        "image": "/static/img/work1.jpg",
        "gallery": [
            "/static/img/work1_detail_1.jpg",
            "/static/img/work1_detail_2.jpg",
            "/static/img/work1_detail_3.jpg",
            "/static/img/work1_detail_4.jpg"
        ]
    },
    2: {
        "grid_title": "Asset Protection",
        "title": "FRONTEND<br>SANDBOX", "client": "Personal Project", "role": "Asset Protection", "year": "2026",
        "text": "激进的防御性前端架构。在内存层面植入动态 Debugger 陷阱，深度封锁开发者工具与非法调试。结合运行时 DOM 混淆与防嵌套机制，构建了一道绝对的数字护城河，确保核心 WebGL 资产与交互逻辑不被恶意逆向或窃取。",
        "image": "/static/img/work2.jpg",
        "gallery": [
            "/static/img/work2_detail_1.jpg",
            "/static/img/work2_detail_2.jpg",
            "/static/img/work2_detail_3.jpg",
            "/static/img/work2_detail_4.jpg"
        ]
    },
    3: {
        "grid_title": "Anti-Scraping Engine",
        "title": "ANTI-SCRAPING<br>ENGINE", "client": "Personal Project", "role": "Business Security", "year": "2026",
        "text": "以攻促防的动态防御引擎与多端交互矩阵。后端依托 SSE 建立高频实时数据流；前端在移动端创新性引入“层叠折叠 UI (Stacked Pills)”，利用纯 CSS 伪类打破常规，实现原生 App 级的零侵入极速交互。有效清洗恶意机器流量，同时保障真实用户的极致体验。",
        "image": "/static/img/work3.jpg",
        "gallery": [
            "/static/img/work3_detail_1.jpg",
            "/static/img/work3_detail_2.jpg",
            "/static/img/work3_detail_3.jpg",
            "/static/img/work3_detail_4.jpg"
        ]
    },
    4: {
        "grid_title": "Edge Network & WAF",
        "title": "EDGE NETWORK<br>& WAF", "client": "Personal Project", "role": "Boundary Defense", "year": "2026",
        "text": "依托 Cloudflare 部署的无服务器边缘防御盾。在网络边界层清洗 DDoS 洪水并隐藏源站真实 IP。同时针对设备算力实施了“双端物理隔离”，智能嗅探并按需分发渲染负荷——为桌面端注入 10 万级满血粒子，为移动端极致降维，在颠覆性视觉与性能间达到绝对平衡。",
        "image": "/static/img/work4.jpg",
        "gallery": [
            "/static/img/work4_detail_1.jpg",
            "/static/img/work4_detail_2.jpg",
            "/static/img/work4_detail_3.jpg",
            "/static/img/work4_detail_4.jpg"
        ]
    },

    # ------ 第 2 章: DATA INTELLIGENCE & SECURITY (5-8) ------
    5: {
        "grid_title": "CORE ARCHITECTURE<br>& WAF",
        "title": "CORE ARCHITECTURE<br>& WAF", "client": "Confidential SaaS", "role": "Backend Security", "year": "2025",
        "text": "实施了严格的 CSP 策略、环境指纹校验以及 API 接口的三重鉴权，确保服务端固若金汤。",
        "code": CODE_APP_PY,
        "filename": "app.py"
    },
    6: {
        "grid_title": "DATABASE &<br>TRANSACTIONS",
        "title": "DATABASE &<br>TRANSACTIONS", "client": "Confidential SaaS", "role": "Data Persistence", "year": "2025",
        "text": "处理数据库兼容性，管理连接池及确保高并发下的核心资产发放原子化交易安全。",
        "code": CODE_DB_PY,
        "filename": "database.py"
    },
    7: {
        "grid_title": "WEBHOOK &<br>PAYMENTS",
        "title": "WEBHOOK &<br>PAYMENTS", "client": "Confidential SaaS", "role": "API Integration", "year": "2025",
        "text": "使用 FastAPI 异步处理高并发的第三方 Webhook（Stripe），并严格验证数字签名防御伪造请求。",
        "code": CODE_WEBHOOK,
        "filename": "webhook_server.py"
    },
    8: {
        "grid_title": "ANTI-SCRAPING<br>ENGIN",
        "title": "ANTI-SCRAPING<br>ENGINE", "client": "Confidential SaaS", "role": "Frontend Security", "year": "2025",
        "text": "部署了复杂的 JavaScript 调试器陷阱（Debugger Trap）与 DOM 动态混淆，有效抵御自动化爬虫。",
        "code": CODE_JS_SEC,
        "filename": "security.js"
    },

    # ------ 第 3 章: DECOUPLED SYSTEM (9-12) 【已全部添加 gallery 结构】 ------
    9: {
        "grid_title": "BRAND<br>IDENTITY",
        "title": "BRAND<br>IDENTITY", "client": "柏魅手工饰品", "role": "Brand Designer", "year": "2025",
        "text": "主导“柏魅”品牌从 0 到 1 的视觉体系搭建。包含品牌标志设计、标准色彩规范及全套 VI 视觉识别系统。将抽象的品牌理念具象化为高辨识度的商业视觉资产，并负责产品宣传海报与包装等核心物料的视觉把控。",
        "image": "/static/img/work9.jpg",
        "gallery": [
            "/static/img/work9_detail_1.jpg",
            "/static/img/work9_detail_2.jpg",
            "/static/img/work9_detail_3.jpg",
            "/static/img/work9_detail_4.jpg"
        ]
    },
    10: {
        "grid_title": "CREATIVE<br>POSTER",
        "title": "CREATIVE<br>POSTER", "client": "Personal Project", "role": "Visual Designer", "year": "2025",
        "text": "一系列聚焦于多元主题的创意海报设计。涵盖了从创意表达、社会议题（如女性安全与反暴力）到信息可视化指南的多维度视觉探索。通过插画、排版与色彩的有机结合，将抽象概念转化为具有强烈视觉冲击力和情感共鸣的平面作品。",
        "image": "/static/img/work10.jpg",
        "gallery": [
            "/static/img/work10_detail_1.jpg",
            "/static/img/work10_detail_2.jpg",
            "/static/img/work10_detail_3.jpg",
            "/static/img/work10_detail_4.jpg"
        ]
    },
    11: {
        "grid_title": "TYPOGRAPHY<br>& POSTER",
        "title": "TYPOGRAPHY<br>& POSTER", "client": "Concept Design", "role": "Graphic Designer", "year": "2025",
        "text": "以“文物”为切入点的字体与海报视觉实验。打破传统排版束缚，将定制化字体设计与现代图形语言相融合。通过高逼真度的 3D 样机渲染（Mockup），精准预演设计在现实物理空间与印刷材质上的最终落地效果。",
        "image": "/static/img/work11.jpg",
        "gallery": [
            "/static/img/work11_detail_1.jpg",
            "/static/img/work11_detail_2.jpg",
            "/static/img/work11_detail_3.jpg",
            "/static/img/work11_detail_4.jpg"
        ]
    },
    12: {
        "grid_title": "LENS<br>& LIGHT",
        "title": "LENS<br>& LIGHT", "client": "Photography", "role": "Photographer", "year": "2023-2026",
        "text": "镜头背后的视觉探索。作为对数字设计的物理延伸，通过摄影捕捉真实世界的光影、几何与空间结构。对色彩分级（Color Grading）与构图的敏锐感知，不仅记录了生活瞬间，更深层次反哺了我在 UI/UX 设计中的审美直觉。",
        "image": "/static/img/work12.jpg",
        "gallery": [
            "/static/img/work12_detail_1.jpg",
            "/static/img/work12_detail_2.jpg",
            "/static/img/work12_detail_3.jpg",
            "/static/img/work12_detail_4.jpg"
        ]
    },
}

PROJECTS_EN = {
    # ------ Chapter 1: CORE ARCHITECTURE & SECURITY ------
    1: {
        "grid_title": "CI/CD Pipeline",
        "title": "CI/CD<br>PIPELINE", "client": "Personal Project", "role": "Cloud Architecture", "year": "2026",
        "text": "A cloud-native continuous delivery pipeline built on GitHub Actions and Render. Discarding traditional manual operations, it achieves a fully automated 'push-to-deploy' workflow. Through containerized environment isolation and rapid builds, it ensures zero-downtime updates for the dual-end rendering engine and core logic.",
        "image": "/static/img/work1.jpg",
        "gallery": [
            "/static/img/work1_detail_1.jpg",
            "/static/img/work1_detail_2.jpg",
            "/static/img/work1_detail_3.jpg",
            "/static/img/work1_detail_4.jpg"
        ]
    },
    2: {
        "grid_title": "Asset Protection",
        "title": "FRONTEND<br>SANDBOX", "client": "Personal Project", "role": "Asset Protection", "year": "2026",
        "text": "Radical defensive front-end architecture. Embedding dynamic Debugger traps at the memory level to heavily lock down developer tools and illegal debugging. Combined with runtime DOM obfuscation and anti-iframe mechanisms, it establishes an absolute digital moat, ensuring core WebGL assets and interactive logic cannot be maliciously reverse-engineered or stolen.",
        "image": "/static/img/work2.jpg",
        "gallery": [
            "/static/img/work2_detail_1.jpg",
            "/static/img/work2_detail_2.jpg",
            "/static/img/work2_detail_3.jpg",
            "/static/img/work2_detail_4.jpg"
        ]
    },
    3: {
        "grid_title": "Anti-Scraping Engine",
        "title": "ANTI-SCRAPING<br>ENGINE", "client": "Personal Project", "role": "Business Security", "year": "2026",
        "text": "A dynamic defense engine and multi-platform interactive matrix driven by an offensive mindset. The backend relies on SSE for high-frequency real-time data streaming; the frontend introduces an innovative 'Stacked Pills UI' on mobile, utilizing pure CSS pseudo-classes to achieve a zero-intrusion, native-app-level interactive experience. Effectively scrubs malicious bot traffic while ensuring ultimate user experience.",
        "image": "/static/img/work3.jpg",
        "gallery": [
            "/static/img/work3_detail_1.jpg",
            "/static/img/work3_detail_2.jpg",
            "/static/img/work3_detail_3.jpg",
            "/static/img/work3_detail_4.jpg"
        ]
    },
    4: {
        "grid_title": "Edge Network & WAF",
        "title": "EDGE NETWORK<br>& WAF", "client": "Personal Project", "role": "Boundary Defense", "year": "2026",
        "text": "Serverless edge defense shield deployed via Cloudflare. It scrubs DDoS floods and masks the origin server IP at the network boundary. Simultaneously, it implements 'dual-end physical isolation' based on device compute power—intelligently sniffing and distributing rendering loads. It delivers 100,000 full-blooded particles to desktop while optimizing for mobile, achieving an absolute balance between disruptive visuals and performance.",
        "image": "/static/img/work4.jpg",
        "gallery": [
            "/static/img/work4_detail_1.jpg",
            "/static/img/work4_detail_2.jpg",
            "/static/img/work4_detail_3.jpg",
            "/static/img/work4_detail_4.jpg"
        ]
    },

    # ------ Chapter 2: DATA INTELLIGENCE & SECURITY (5-8) [Code Display Group] ------
    5: {
        "grid_title": "CORE ARCHITECTURE<br>& WAF",
        "title": "CORE ARCHITECTURE<br>& WAF", "client": "Confidential SaaS", "role": "Backend Security", "year": "2025",
        "text": "Implemented strict CSP policies, environmental fingerprint verification, and triple authentication for API interfaces to ensure an impenetrable backend server.",
        "code": CODE_APP_PY,
        "filename": "app.py"
    },
    6: {
        "grid_title": "DATABASE &<br>TRANSACTIONS",
        "title": "DATABASE &<br>TRANSACTIONS", "client": "Confidential SaaS", "role": "Data Persistence", "year": "2025",
        "text": "Handled database compatibility, managed connection pools, and ensured the security of atomic transactions for core asset distribution under high concurrency.",
        "code": CODE_DB_PY,
        "filename": "database.py"
    },
    7: {
        "grid_title": "WEBHOOK &<br>PAYMENTS",
        "title": "WEBHOOK &<br>PAYMENTS", "client": "Confidential SaaS", "role": "API Integration", "year": "2025",
        "text": "Used FastAPI to asynchronously process high-concurrency third-party Webhooks (Stripe), and strictly verified digital signatures to defend against forged requests.",
        "code": CODE_WEBHOOK,
        "filename": "webhook_server.py"
    },
    8: {
        "grid_title": "ANTI-SCRAPING<br>ENGINE",
        "title": "ANTI-SCRAPING<br>ENGINE", "client": "Confidential SaaS", "role": "Frontend Security", "year": "2025",
        "text": "Deployed complex JavaScript Debugger Traps and dynamic DOM obfuscation to effectively resist automated scrapers.",
        "code": CODE_JS_SEC,
        "filename": "security.js"
    },

    # ------ Chapter 3: DECOUPLED SYSTEM (9-12) [Gallery structure added to all] ------
    9: {
        "grid_title": "BRAND<br>IDENTITY",
        "title": "BRAND<br>IDENTITY", "client": "Baimei Handmade Jewelry", "role": "Brand Designer", "year": "2025",
        "text": "Led the 0-to-1 visual system construction for the 'Baimei' brand. This includes brand logo design, standard color specifications, and a complete VI (Visual Identity) system. Materialized abstract brand concepts into highly recognizable commercial visual assets, and took charge of the visual control for core materials like product promotional posters and packaging.",
        "image": "/static/img/work9.jpg",
        "gallery": [
            "/static/img/work9_detail_1.jpg",
            "/static/img/work9_detail_2.jpg",
            "/static/img/work9_detail_3.jpg",
            "/static/img/work9_detail_4.jpg"
        ]
    },
    10: {
        "grid_title": "CREATIVE<br>POSTER",
        "title": "CREATIVE<br>POSTER", "client": "Personal Project", "role": "Visual Designer", "year": "2025",
        "text": "A series of creative poster designs focusing on diverse themes. It covers multi-dimensional visual explorations from creative expression and social issues (such as female safety and anti-violence) to infographic guides. Through the organic combination of illustration, typography, and color, abstract concepts are transformed into graphic works with strong visual impact and emotional resonance.",
        "image": "/static/img/work10.jpg",
        "gallery": [
            "/static/img/work10_detail_1.jpg",
            "/static/img/work10_detail_2.jpg",
            "/static/img/work10_detail_3.jpg",
            "/static/img/work10_detail_4.jpg"
        ]
    },
    11: {
        "grid_title": "TYPOGRAPHY<br>& POSTER",
        "title": "TYPOGRAPHY<br>& POSTER", "client": "Concept Design", "role": "Graphic Designer", "year": "2025",
        "text": "A visual experiment in typography and posters starting from the concept of 'cultural relics'. Breaking the constraints of traditional typesetting, I integrated customized font design with modern graphic language. Through high-fidelity 3D mockup rendering, I accurately previewed the final implementation effect of the design in real physical spaces and on printing materials.",
        "image": "/static/img/work11.jpg",
        "gallery": [
            "/static/img/work11_detail_1.jpg",
            "/static/img/work11_detail_2.jpg",
            "/static/img/work11_detail_3.jpg",
            "/static/img/work11_detail_4.jpg"
        ]
    },
    12: {
        "grid_title": "LENS<br>& LIGHT",
        "title": "LENS<br>& LIGHT", "client": "Photography", "role": "Photographer", "year": "2023-2026",
        "text": "Visual exploration behind the lens. As a physical extension of digital design, I capture light, shadow, geometry, and spatial structures of the real world through photography. A keen perception of Color Grading and composition not only records moments of life but also deeply feeds back into my aesthetic intuition in UI/UX design.",
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
async def project_detail(request: Request, project_id: int, lang: str = "en"):  # 【关键修复 1】：接收语言参数
    # 【关键修复 2】：获取对应的语言字典包
    t = I18N_DB.get(lang, I18N_DB["en"])

    # 【关键修复 3】：根据语言，智能选择对应语言的作品数据库！
    current_db = PROJECTS_ZH if lang == "zh" else PROJECTS_EN

    # 从当前语言的数据库里获取作品数据
    project_data = current_db.get(project_id, current_db[1])

    # 保留你原本极其优雅的翻页计算逻辑
    current_index = ((project_id - 1) % 4) + 1
    is_last = (current_index == 4)
    next_id = project_id + 1

    return templates.TemplateResponse("detail.html", {
        "request": request,
        "project": project_data,
        "current_index": current_index,
        "is_last": is_last,
        "next_id": next_id,
        "t": t,  # 【关键修复 4】：把多语言包喂给前端！
        "lang": lang  # 【关键修复 5】：告诉前端当前是什么语言！
    })

from fastapi import Response

@app.post("/my-api/")
async def silence_mysterious_requests():
    # 返回 204 状态码，代表“收到请求，但不予理会”
    return Response(status_code=204)

@app.get("/my-api/")
async def silence_mysterious_get():
    return Response(status_code=204)

I18N_DB = {
    "zh": {
        # 1. 系统警告与全局提示
        "title_detail": "项目详情 - Adestikla",
        "system_locked": "⚠️ 系统已锁定",
        "ban_warning": "本网站禁止一切爬虫、AI 及第三方插件的引用。",
        "dom_destroyed": "[ DOM 树已摧毁 & 网络已切断 ]",
        "initializing": "初始化中",

        # 2. 导航与界面通用词
        "btn_back": "← 返回首页",
        "end_section": "本节结束 (返回首页) →",
        "next_project": "下一个项目 →",
        "explore_more": "探索更多",
        "meta_client": "客户",
        "meta_role": "角色",
        "meta_year": "年份",
        "meta_awards": "奖项 / 类型",
        "default_awards": "独立作品",
        "project_overview": "项目<br>概述",

        # 3. 首页头部与目录
        "portfolio_title": "Adestikla 作品集",
        "creative_portfolio": "创意作品集",
        "design_dev": "设计与开发",
        "dir_title_1": "系统工程",
        "dir_1_1": "CI/CD 流水线",
        "dir_1_2": "资产保护",
        "dir_1_3": "反爬虫引擎",
        "dir_1_4": "边缘网络与 WAF",
        "dir_title_2": "创意愿景",
        "dir_2_1": "品牌视觉",
        "dir_2_2": "创业海报",
        "dir_2_3": "字体与海报",
        "dir_2_4": "镜头与光影",
        "rotate_tip": "建议横屏查看以获得最佳体验 ↺",

        # 4. 个人信息与引言
        "bio_quote": "“设计不仅关乎视觉——它在于解决问题并激发共鸣。”",
        "bio_role": "Adestikla，设计师",
        "bio_name": "柴坤阳",  # 依照文档规范
        "bio_label_degree": "学历",
        "bio_val_degree": "全日制大专",
        "bio_label_birthday": "生日",
        "bio_label_contact": "电话",
        "bio_label_gmail": "邮箱",
        "contact_title": "联系方式",
        "contact_links": "GMAIL / 微信 / GitHub",

        # 5. 项目经验长文本
        "exp_title": "项目经验",
        "exp_1_time": "2026 // UI/UX 与创意开发",
        "exp_1_title": "沉浸式 3D 作品集",
        "exp_1_desc": "一个包含流畅 GSAP 滚动视差和 SVG 动画的交互式网页体验。在 AI 协助下构建，利用解耦后端和 Cloudflare 实现最佳性能。",
        "exp_2_time": "2025 // 前端与安全",
        "exp_2_title": "安全 SaaS 平台",
        "exp_2_desc": "为一款全球 SaaS 工具进行前端架构与安全部署。集成了解耦 API 并配置了 Cloudflare WAF，在保密协议下确保安全、高性能的数据渲染。",
        "exp_3_time": "2025 // 品牌视觉",
        "exp_3_title": "柏魅视觉系统",
        "exp_3_desc": "一个全面的视觉识别系统，包含 Logo 设计、色彩规范和产品包装。通过连贯且富有冲击力的视觉叙事提升了品牌认知度。",

        # 6. 网格标签与滚动提示字
        "snap_1": "云端|安全|CI/CD|流水线",
        "role_1_1": "云架构",
        "role_1_2": "资产保护",
        "role_1_3": "业务安全",
        "role_1_4": "边界防御",

        "snap_2": "数据|智能|分析|系统",
        "role_2_1": "后端安全",
        "role_2_2": "数据持久化",
        "role_2_3": "API 集成",
        "role_2_4": "前端安全",

        "snap_3": "视觉|设计|创意|愿景",
        "role_3_1": "品牌设计师",
        "role_3_2": "视觉插画师",
        "role_3_3": "平面设计师",
        "role_3_4": "摄影师",

        # 7. 3D 爬虫演示与交互终端
        "snap_4": "赛博|安全|爬虫|网络",
        "stage_1_title": "阶段 01 / 数据采集",
        "stage_1_desc": "在去中心化网络中部署自动化爬虫，对原始的非结构化数据节点进行索引。",
        "stage_2_title": "阶段 02 / 网络映射",
        "stage_2_desc": "构建关系图谱以识别集群、安全漏洞及加密路径。",
        "stage_3_title": "阶段 03 / 数据处理",
        "stage_3_desc": "通过解耦云架构过滤噪音，并构建高度可用的情报矩阵。",
        "exp_explore": "探索 ↗",

        # 8. 爬虫界面与日志
        "crawler_title": "全网数据穿透矩阵",
        "crawler_subtitle": "重构网络的混沌",
        "opt_job": "招聘",
        "opt_house": "租房",
        "placeholder_city": "城市",
        "placeholder_target": "输入目标 (如：前端开发 / 南山一居室)...",
        "opt_edu_1": "全学历",
        "opt_edu_2": "大专",
        "opt_edu_3": "本科",
        "opt_edu_4": "硕士",
        "btn_initiate": "启动",
        "log_title": "系统.日志.流 _",
        "nav_link": "链接已建立...",
        "log_secure": "> 正在建立安全连接...",
        "log_retrieved": "[ 成功获取安全数据 | 分布式多节点数据汇编 ]",
        "table_header": "公司 / 职位 / 地点 / 薪资",
        "btn_failed": "抓取失败 / 重试",
        "log_halted": "> [SYSTEM HALTED] 数据流中断，未能抓取到有效节点。"
    },

    "en": {
        # 1. System & Global
        "title_detail": "Project Detail - Adestikla",
        "system_locked": "⚠️ SYSTEM LOCKED",
        "ban_warning": "This website prohibits all scraping, AI, and third-party plugin references.",
        "dom_destroyed": "[ DOM Destroyed & Network Terminated ]",
        "initializing": "INITIALIZING",

        # 2. Navigation & UI
        "btn_back": "← BACK TO INDEX",
        "end_section": "END OF SECTION (BACK TO INDEX) →",
        "next_project": "NEXT PROJECT →",
        "explore_more": "EXPLORE MORE",
        "meta_client": "CLIENT",
        "meta_role": "ROLE",
        "meta_year": "YEAR",
        "meta_awards": "AWARDS / TYPE",
        "default_awards": "Independent Work",
        "project_overview": "PROJECT<br>OVERVIEW",
        "exp_explore": "EXPLORE ↗",
        "rotate_tip": "Rotate device for better view ↺",

        # 3. Hero & Directory
        "portfolio_title": "Adestikla Portfolio",
        "creative_portfolio": "Creative Portfolio",
        "design_dev": "DESIGN & DEVELOPMENT",
        "dir_title_1": "SYSTEM ENGINEERING",
        "dir_1_1": "CI/CD Pipeline",
        "dir_1_2": "Asset Protection",
        "dir_1_3": "Anti-Scraping Engine",
        "dir_1_4": "Edge Network & WAF",
        "dir_title_2": "CREATIVE VISION",
        "dir_2_1": "Brand Identity",
        "dir_2_2": "Creative Poster",
        "dir_2_3": "Typography & Poster",
        "dir_2_4": "Lens & Light",

        # 4. Bio & Quote
        "bio_quote": "\"Design goes beyond the visual—it’s about solving problems and inspiring emotion.\"",
        "bio_role": "Adestikla, Designer",
        "bio_name": "CHAI KUNYANG",
        "bio_label_degree": "DEGREE",
        "bio_val_degree": "Full-time Junior College",
        "bio_label_birthday": "BIRTHDAY",
        "bio_label_contact": "CONTACT",
        "bio_label_gmail": "GMAIL",
        "contact_title": "CONTACT",
        "contact_links": "GMAIL / WECHAT / GitHub",

        # 5. Project Experience
        "exp_title": "PROJECT EXPERIENCE",
        "exp_1_time": "2026 // UI/UX & CREATIVE DEV",
        "exp_1_title": "IMMERSIVE 3D PORTFOLIO",
        "exp_1_desc": "An interactive web experience featuring smooth GSAP scroll parallax and SVG animations. Built with AI assistance, utilizing a decoupled backend and Cloudflare for optimal performance.",
        "exp_2_time": "2025 // FRONT-END & SECURITY",
        "exp_2_title": "SECURE SAAS PLATFORM",
        "exp_2_desc": "Front-end architecture and security deployment for a global SaaS tool. Integrated decoupled APIs and configured Cloudflare WAF to ensure secure, high-performance data rendering under NDA.",
        "exp_3_time": "2025 // BRAND IDENTITY",
        "exp_3_title": "BOMEI VISUAL SYSTEM",
        "exp_3_desc": "A comprehensive visual identity system including logo design, color guidelines, and product packaging. Elevated brand recognition through cohesive and impactful visual storytelling.",

        # 6. Grid Tags & Scroll Text
        "snap_1": "CLOUD|SECURITY|CI/CD|PIPELINE",
        "role_1_1": "Cloud Architecture",
        "role_1_2": "Asset Protection",
        "role_1_3": "Business Security",
        "role_1_4": "Boundary Defense",

        "snap_2": "DATA|INTELLIGENCE|ANALYSIS|SYSTEM",
        "role_2_1": "Backend Security",
        "role_2_2": "Data Persistence",
        "role_2_3": "API Integration",
        "role_2_4": "Frontend Security",

        "snap_3": "VISUAL|DESIGN|CREATIVE|VISION",
        "role_3_1": "Brand Designer",
        "role_3_2": "Visual Illustrator",
        "role_3_3": "Graphic Designer",
        "role_3_4": "Photographer",

        # 7. 3D Crawler & Terminal
        "snap_4": "CYBER|SECURITY|CRAWLER|NETWORK",
        "stage_1_title": "STAGE 01 / DATA GATHERING",
        "stage_1_desc": "Deploying automated spiders across the decentralized web to index raw, unstructured data nodes.",
        "stage_2_title": "STAGE 02 / NETWORK MAPPING",
        "stage_2_desc": "Constructing relational graphs to identify clusters, security vulnerabilities, and encrypted pathways.",
        "stage_3_title": "STAGE 03 / DATA PROCESSING",
        "stage_3_desc": "Filtering noise through decoupled cloud architectures and structuring highly usable intel matrices.",

        # 8. Others
        "crawler_title": "WEB CRAWLER MATRIX",
        "crawler_subtitle": "Structuring the Chaos of the Web",
        "opt_job": "JOBS",
        "opt_house": "HOUSING",
        "placeholder_city": "City",
        "placeholder_target": "Enter target (e.g., Frontend Dev / Nanshan 1B1B)...",
        "opt_edu_1": "NDR",
        "opt_edu_2": "A.A",
        "opt_edu_3": "B.A",
        "opt_edu_4": "MBA",
        "btn_initiate": "START",
        "log_title": "SYS.LOG.STREAM _",
        "nav_link": "LINK ESTABLISHED...",
        "log_secure": "> ESTABLISHING SECURE CONNECTION...",
        "log_retrieved": "[ SECURE DATA RETRIEVED | Distributed Multi-node Data Compilation ]",
        "table_header": "COMPANY / POSITION / LOCATION / SALARY",
        "btn_failed": "CRAWL FAILED / RETRY",
        "log_halted": "> [SYSTEM HALTED] Data stream interrupted, failed to fetch valid nodes."
    }
}