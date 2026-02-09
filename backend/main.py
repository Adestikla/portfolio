from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os

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
async def get_data(type: str = "jobs"):
    if type == "jobs":
        return {"data": [{"title": "电商美工", "city": "深圳", "salary": "8k-12k"}]}
    return {"data": [{"title": "南山区公寓", "price": "3000"}]}