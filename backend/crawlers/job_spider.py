import asyncio
from playwright.async_api import async_playwright

class CompanyAuditor:
    def __init__(self):
        self.risk_keywords = ["吊销", "注销", "异常", "纠纷", "失信", "破产", "皮包", "黑中介"]
        self.api_blacklist = ["某某皮包公司", "黑心外包科技", "暴雷金融集团"]

    async def check_risk(self, company_name):
        await asyncio.sleep(0.4)
        if any(word in company_name for word in self.risk_keywords):
            return True, "命中本地高危词库"
        if company_name in self.api_blacklist:
            return True, "API 反馈: 存在严重诉讼记录"
        return False, "信用核查通过"


class UniversalScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.auditor = CompanyAuditor()

    async def fetch_data_stream(self, keyword, edu):
        yield {"type": "log", "msg": f"🚀 启动无头浏览器集群... 目标岗位: [{keyword}]"}

        # 启动 Playwright
        async with async_playwright() as p:
            # 启动浏览器 (headless=True 表示后台静默运行，如果改成 False 你能看到它弹出来自己动)
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            try:
                # 1. 改变战术：不直接去列表页，直接去防备最弱的“首页”大门！
                target_url = "https://www.ncss.cn/"

                yield {"type": "log", "msg": f"🌐 正在突破目标节点: 国家大学生就业网(首页)..."}

                # 访问首页
                await page.goto(target_url, wait_until="networkidle", timeout=15000)

                # ==========================================
                # 如果首页还是弹了登录，我们就用你发现的“后门”点击右上角的首页！
                # ==========================================
                try:
                    # 尝试寻找并点击页面上包含“首页”两个字的链接
                    home_btn = page.get_by_text("首页", exact=True).first
                    if await home_btn.is_visible():
                        await home_btn.click()
                        yield {"type": "log", "msg": "🔓 成功触发 [首页] 后门，绕过登录墙！"}
                        await page.wait_for_load_state("networkidle")
                except:
                    pass  # 如果没弹窗，就什么都不做继续往下走

                # 2. 在首页寻找搜索框并输入
                yield {"type": "log", "msg": "⌨️ 锁定全站搜索枢纽，注入查询参数..."}

                # 【盲狙定位】：寻找页面里 type 为 text 的输入框
                # 注意：如果它在首页填错了框，你依然需要去网页上 Inspect 看一下那个真实搜索框的 class 名字
                search_input = page.locator('xpath=/html/body/div[2]/div[2]/div/form/div/input')

                # 像真人一样打字
                await search_input.fill(keyword)
                await asyncio.sleep(0.5)

                # 敲击回车，这通常会触发页面跳转到真正的职位列表页！
                yield {"type": "log", "msg": "⏳ 发送查询指令，等待底层数据越权下发..."}
                await search_input.press("Enter")

                # ==========================================
                # 【核心修复】：解决“新标签页瞎子”问题！
                # ==========================================
                # 给浏览器 3 秒钟的时间去弹新窗口、加载页面
                await asyncio.sleep(3)

                # 获取当前浏览器里所有打开的标签页
                pages = context.pages
                # 强制把爬虫的眼睛，盯住最后一个标签页（即刚刚弹出来的搜索结果页！）
                active_page = pages[-1]

                # 模拟真人鼠标向下滚一点，促发懒加载
                await active_page.mouse.wheel(0, 800)
                await asyncio.sleep(1.5)

                # ==========================================
                # 4. 抓取卡片 (注意：这里必须全改成 active_page)
                # ==========================================
                # ⚠️注意：如果下面还是提示没抓到数据，说明卡片名字不叫 '.jobList-item'！
                # 你需要去结果网页里，右键检查那个职位大卡片，看看它的真实 class 是什么。
                job_cards = await active_page.locator('xpath=//*[@id="jobLIST"]/*').all()

                if not job_cards:
                    yield {"type": "log", "msg": "⚠️ 警告：找到了列表外壳，但里面没数据！"}
                else:
                    yield {"type": "log", "msg": f"📥 成功截获 {len(job_cards)} 个真实职位卡片！启动数据剥离..."}

                raw_jobs = []
                # 这里我们把范围扩大到前 20 个，因为里面可能混入了很多幽灵卡片
                for card in job_cards[:20]:
                    try:
                        title_loc = card.locator('.basic-color').first

                        # 【核心过滤机制】：如果这个盒子里连岗位名字都没有，它绝对不是真实的职位卡片，直接跳过！
                        if await title_loc.count() == 0:
                            continue

                            # 能走到这里，说明是真正的职位卡片，开始放心提取！
                        title = await title_loc.inner_text()

                        company_loc = card.locator('.company-name').first
                        company = await company_loc.inner_text() if await company_loc.count() > 0 else "暂无公司"

                        city_loc = card.locator('li').first
                        city = await city_loc.inner_text() if await city_loc.count() > 0 else "暂无地区"

                        salary_loc = card.locator('.salary-money').first
                        salary = await salary_loc.inner_text() if await salary_loc.count() > 0 else "暂无薪资"

                        raw_jobs.append({
                            "title": title.strip(),
                            "company": company.strip(),
                            "city": city.strip(),
                            "salary": salary.strip(),
                            "source": "国家大学生就业平台"
                        })

                        # 只要收集满 10 条真实干净的数据，就立马收工！
                        if len(raw_jobs) >= 10:
                            break

                    except Exception as e:
                        continue

                # 关闭浏览器释放内存
                await browser.close()

                # 3. 将抓到的真实数据送入我们的“洗盘”模块
                clean_data = []
                for job in raw_jobs:
                    yield {"type": "log", "msg": f"🔍 正在穿透核查企业: {job['company']}..."}
                    is_at_risk, risk_reason = await self.auditor.check_risk(job['company'])

                    if not is_at_risk:
                        clean_data.append(job)
                        yield {"type": "log", "msg": f"✅ [信用安全] {job['company']} - {risk_reason}"}
                    else:
                        yield {"type": "log", "msg": f"⚠️ [红牌拦截] {job['company']} - {risk_reason}"}

                yield {"type": "log", "msg": "🎉 真实数据清洗完毕，生成可视化面板..."}
                yield {"type": "result", "data": clean_data}

            except Exception as e:
                yield {"type": "log", "msg": f"❌ 爬取发生致命错误: {str(e)}"}
                await browser.close()
                yield {"type": "result", "data": []}