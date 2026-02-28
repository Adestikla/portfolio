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
async def get_data(keyword: str = "UI设计", edu: str = "不限"):
    scraper = UniversalScraper(headless=True)

    # 构建 SSE 事件流生成器，把用户输入的岗位和学历传给爬虫
    async def event_generator():
        async for chunk in scraper.fetch_data_stream(keyword, edu):
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# 详情页路由
PROJECTS_DB = {
    # ------ 第 1 章: UI/UX (1-4) ------
    1: {"title": "ANCIENT CHINESE<br>PHYSICS", "client": "Studio Adestikla", "role": "UI/UX & Branding", "year": "2025", "text": "这是一次将中国古代物理学理念与现代数字交互相融合的实验性项目。设计不仅关注视觉的冲击力，更深入探讨了东方哲学在赛博空间中的表达器。", "image": "/static/img/work1.jpg"},
    2: {"title": "WEREWOLF<br>CHARACTER", "client": "Personal Project", "role": "Digital Art", "year": "2026", "text": "关于狼人角色的概念设计与插画创作，探索光影、肌肉张力以及在数字艺术环境下的表现力。", "image": "/static/img/work2.jpg"},
    3: {"title": "NUADU<br>PLATFORM", "client": "Personal Project", "role": "Web Design", "year": "2026", "text": "教育平台的界面设计，重点在于信息的层级划分和用户的学习流体验优化。", "image": "/static/img/work3.jpg"},
    4: {"title": "SPACE<br>EXPLORER", "client": "Personal Project", "role": "Mobile Interface", "year": "2026", "text": "一款太空探索应用的概念设计，使用了鲜明的色彩和直观的卡片式交互。", "image": "/static/img/work4.jpg"},

    # ------ 第 2 章: DATA INTELLIGENCE (5-8) ------
    5: {"title": "DATA<br>VISUALIZATION", "client": "Tech Corp", "role": "Data Intelligence", "year": "2026", "text": "复杂数据的可视化呈现，让枯燥的数据报表变成充满科技感的互动面板。", "image": "/static/img/work5.jpg"},
    6: {"title": "USER<br>BEHAVIOR", "client": "Tech Corp", "role": "Data Intelligence", "year": "2026", "text": "基于用户行为数据的分析系统界面设计。", "image": "/static/img/work6.jpg"},
    7: {"title": "MARKET<br>TRENDS", "client": "Tech Corp", "role": "Data Intelligence", "year": "2026", "text": "全球市场趋势的实时监控大屏设计。", "image": "/static/img/work7.jpg"},
    8: {"title": "SALES<br>PREDICTION", "client": "Tech Corp", "role": "Data Intelligence", "year": "2026", "text": "结合 AI 算法的销量预测平台 UI 界面。", "image": "/static/img/work8.jpg"},

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