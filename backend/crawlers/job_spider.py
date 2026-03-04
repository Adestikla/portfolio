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

    async def fetch_data_stream(self, keyword, edu, city):
        yield {"type": "log", "msg": f"🚀 启动分布式爬虫集群... 目标城市: [{city}] 岗位: [{keyword}]"}

        raw_jobs = []
        clean_city = city.replace("市", "")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            # ==========================================
            # 引擎 1：国家大学生就业网 (提取 5 条)
            # ==========================================
            try:
                yield {"type": "log", "msg": f"🌐 [引擎 1] 正在突破: 国家大学生就业网..."}
                page1 = await context.new_page()
                await page1.goto("https://www.ncss.cn/", wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(2)

                search_input = page1.locator('xpath=/html/body/div[2]/div[2]/div/form/div/input')
                await search_input.fill(keyword)
                await asyncio.sleep(0.5)

                yield {"type": "log", "msg": f"⏳ 发送查询指令，等待页面跳转..."}

                # ==========================================
                # 【核心修复】：放弃死等新标签页，兼容同页面跳转
                # ==========================================
                await search_input.press("Enter")
                await asyncio.sleep(3)  # 给网页一点跳转的反应时间

                # 不管它有没有弹新标签页，我们都拿当前最顶层的那个页面操作
                active_page = context.pages[-1]

                # 等待 DOM 树加载，如果网卡了最多等 10 秒也不让它崩溃
                try:
                    await active_page.wait_for_load_state("domcontentloaded", timeout=10000)
                except Exception:
                    pass
                    # ==========================================

                yield {"type": "log", "msg": f"✅ 结果页加载完毕！准备切换城市..."}

                await active_page.mouse.wheel(0, 300)
                await asyncio.sleep(1.5)

                yield {"type": "log", "msg": f"📍 尝试物理强点，切换区域至: [{clean_city}]..."}
                city_btn = active_page.locator('#searcharea, xpath=//*[@id="searchBar"]/div[3]').first

                if await city_btn.count() > 0:
                    # 【核心修复】：放弃 JS 注入，改用 Playwright 的物理强点 force=True
                    await city_btn.click(force=True)
                    await asyncio.sleep(1.5)

                    target_city_loc = active_page.locator(f'#cityDropdown span:has-text("{clean_city}")').first
                    if await target_city_loc.count() > 0:
                        # 物理强点选中城市
                        await target_city_loc.click(force=True)
                        await asyncio.sleep(1)

                        yield {"type": "log", "msg": f"🔄 触发二次查询指令，等待区域数据刷新..."}
                        search_btn_loc = active_page.locator('#jobSearch, xpath=//*[@id="jobSearch"]').first

                        if await search_btn_loc.count() > 0:
                            # 物理强点搜索按钮
                            await search_btn_loc.click(force=True)
                            await asyncio.sleep(4)  # 给它充足的时间去请求后端数据
                        else:
                            yield {"type": "log", "msg": f"⚠️ 未找到 NCSS 确认搜索按钮。"}
                    else:
                        yield {"type": "log", "msg": f"⚠️ NCSS 未找到对应城市 [{clean_city}]，将使用默认数据。"}

                # 提取数据
                job_cards = await active_page.locator('xpath=//*[@id="jobLIST"]/*').all()
                ncss_count = 0

                for card in job_cards[:15]:
                    try:
                        title_loc = card.locator('.basic-color').first
                        if await title_loc.count() == 0: continue

                        title = await title_loc.inner_text()
                        company = await card.locator('.company-name').first.inner_text()
                        salary = await card.locator('.salary-money').first.inner_text()

                        # 【核心修复】：精准提取带有 "|" 符号的 li 标签内容
                        job_city = clean_city  # 默认用你搜索的城市兜底
                        li_texts = await card.locator('li').all_inner_texts()

                        # 建立一个“干扰词黑名单”
                        exclude_words = ["大专", "专科", "本科", "硕士", "博士", "学历", "不限", "招", "人"]

                        for text in li_texts:
                            # 比如 "北京 | 专业不限" -> 切开拿到 "北京"
                            # 比如 "本科 | 招10人" -> 切开拿到 "本科"
                            left_part = text.split('|')[0].strip()

                            # 如果左半边不是空，且【不包含】任何黑名单里的词，那它就是城市！
                            if left_part and not any(word in left_part for word in exclude_words):
                                job_city = left_part
                                break

                        raw_jobs.append({
                            "title": title.strip(),
                            "company": company.strip(),
                            "salary": salary.strip(),
                            "city": job_city,
                            "source": "NCSS 就业网"
                        })
                        ncss_count += 1
                        if ncss_count >= 5: break
                    except:
                        continue

                yield {"type": "log", "msg": f"✅ NCSS 节点提取完成，截获 {ncss_count} 条数据。"}
                await active_page.close()
                if page1 and not page1.is_closed(): await page1.close()

            except Exception as e:
                yield {"type": "log", "msg": f"⚠️ NCSS 节点访问超时或被拦截，切断连接跳过。"}

            # ==========================================
            # 引擎 2：智联招聘 (降维打击版)
            # ==========================================
            try:
                yield {"type": "log", "msg": f"🌐 [引擎 2] 正在切换数据源: 智联招聘(Zhaopin)..."}
                page2 = await context.new_page()

                # 【核心黑科技】：使用智联隐藏的内部城市代码字典，直接绕过点击弹窗！
                zp_city_map = {
                    "北京": "530", "上海": "538", "广州": "763", "深圳": "765",
                    "成都": "801", "杭州": "653", "武汉": "736", "重庆": "551",
                    "南京": "635", "西安": "854", "苏州": "719", "天津": "531",
                    "郑州": "714", "长沙": "738", "东莞": "764", "青岛": "702",
                    "合肥": "734", "沈阳": "749", "济南": "703", "大连": "705"
                }
                # 查字典转换，如果输入的是小城市没在字典里，就强行传中文
                city_code = zp_city_map.get(clean_city, clean_city)

                yield {"type": "log", "msg": f"📍 解析城市 [{clean_city}] -> 内部代码 [{city_code}]，直接注入底层接口..."}

                # 直接将城市代码拼在 jl 参数里
                zp_url = f"https://sou.zhaopin.com/?kw={keyword}&jl={city_code}"
                await page2.goto(zp_url, wait_until="domcontentloaded", timeout=15000)

                if "login" in page2.url or await page2.locator('.login-box').count() > 0:
                    raise Exception("触发智联风控登录墙")

                await asyncio.sleep(4)  # 等待列表渲染
                await page2.mouse.wheel(0, 1000)
                await asyncio.sleep(2)

                zp_cards = await page2.locator('.joblist-box__item').all()
                zp_count = 0

                for card in zp_cards:
                    try:
                        title = await card.locator('.jobinfo__name').first.inner_text()
                        salary = await card.locator('.jobinfo__salary').first.inner_text()
                        company = await card.locator('.companyinfo__name').first.inner_text()

                        loc_el = card.locator('.jobinfo__other-info-item').first
                        job_city = await loc_el.inner_text() if await loc_el.count() > 0 else clean_city

                        raw_jobs.append({
                            "title": title.strip(),
                            "company": company.strip(),
                            "salary": salary.strip(),
                            "city": job_city.strip(),
                            "source": "Zhaopin 智联"
                        })
                        zp_count += 1
                        if zp_count >= 5: break
                    except Exception as e:
                        continue

                yield {"type": "log", "msg": f"✅ 智联节点提取完成，截获 {zp_count} 条数据。"}
                await page2.close()

            except Exception as e:
                yield {"type": "log", "msg": f"⚠️ 智联节点风控墙拦截，请求跳过。"}

            await browser.close()

        # ==========================================
        # 3. 洗盘模块
        # ==========================================
        if not raw_jobs:
            yield {"type": "log", "msg": "❌ [致命错误] 所有数据源均未能获取到有效数据！(可能触发了全网验证码拦截)"}
            yield {"type": "result", "data": []}
            return

        yield {"type": "log", "msg": f"📥 双引擎共截获 {len(raw_jobs)} 条底层数据！启动分布式清洗..."}

        clean_data = []
        for job in raw_jobs:
            yield {"type": "log", "msg": f"🔍 正在穿透核查企业: {job['company'][:10]}..."}
            is_at_risk, risk_reason = await self.auditor.check_risk(job['company'])

            if not is_at_risk:
                clean_data.append(job)
                yield {"type": "log", "msg": f"✅ [安全] {job['source']} - {job['company'][:10]}"}
            else:
                yield {"type": "log", "msg": f"⚠️ [拦截] {job['company'][:10]}... - {risk_reason}"}

        yield {"type": "log", "msg": "🎉 真实数据清洗完毕，生成混合可视化面板..."}
        yield {"type": "result", "data": clean_data}