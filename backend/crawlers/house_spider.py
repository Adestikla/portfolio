import asyncio
from playwright.async_api import async_playwright


class HouseScraper:
    def __init__(self, headless=True):
        self.headless = headless

    async def fetch_data_stream(self, keyword):
        yield {"type": "log", "msg": f"🏠 启动 唯心所寓 (Wellcee) 侦测网... 目标: [{keyword}]"}

        async with async_playwright() as p:
            # headless=True 静默运行，如果想看浏览器自己操作，可以改为 headless=False
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            try:
                # 1. 跳转到唯心所寓首页
                target_url = "https://www.wellcee.com/rent-apartment/shenzhen"
                yield {"type": "log", "msg": f"🌐 正在接入 Wellcee 深圳节点..."}

                await page.goto(target_url, wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(2)

                # 2. 定位搜索框并输入 (使用你提供的精确 XPath)
                yield {"type": "log", "msg": f"⌨️ 锁定全站搜索枢纽，注入关键词: [{keyword}]"}

                # 点击外层 div 激活焦点
                search_box = page.locator('xpath=//*[@id="app"]/div[1]/div[2]/div[1]/div')
                await search_box.click()
                await asyncio.sleep(0.5)

                # 尝试找到里面真正的 input 并填入，如果结构变了就直接模拟键盘盲打
                input_el = search_box.locator('input').first
                if await input_el.count() > 0:
                    await input_el.fill(keyword)
                else:
                    await page.keyboard.type(keyword)

                await asyncio.sleep(1)

                # 3. 点击搜索按钮 (使用你提供的精确 XPath)
                search_btn = page.locator('xpath=//*[@id="app"]/div[1]/div[2]/div[2]/a')
                await search_btn.click()

                yield {"type": "log", "msg": "⏳ 发送查询指令，等待房源数据越权下发..."}
                await asyncio.sleep(4)  # 多等几秒，让 Vue 框架渲染完新列表

                # 模拟鼠标向下滚动，触发图片和文字的懒加载
                await page.mouse.wheel(0, 1500)
                await asyncio.sleep(2)

                # 4. 暴力提取房源卡片 (无视 Class 的变化)
                # 策略：寻找页面里所有的超链接 <a>，只要链接指向了租房详情页，就抓过来
                all_links = await page.locator('a[href*="/rent-apartment/"]').all()

                job_cards = []
                for link in all_links:
                    text = await link.inner_text()
                    # 过滤掉顶部的空链接或导航，只保留文字丰富、且包含价格符号的“真卡片”
                    if len(text.strip()) > 15 and ("￥" in text or "¥" in text or "元" in text or "/" in text):
                        job_cards.append(link)

                if not job_cards:
                    yield {"type": "log", "msg": "⚠️ 警告：指令已发送，但未捕捉到对应的房源(可能是该区没房，或被盾拦截)。"}
                    yield {"type": "result", "data": []}
                    await browser.close()
                    return

                yield {"type": "log", "msg": f"📥 截获 {len(job_cards)} 个疑似房源数据包！启动智能剥离..."}

                clean_data = []
                seen_titles = set()  # 用来防止抓到重复的卡片

                for card in job_cards:
                    if len(clean_data) >= 8:  # 限制只拿前 8 个
                        break

                    try:
                        text_content = await card.inner_text()
                        lines = [line.strip() for line in text_content.split('\n') if line.strip()]

                        if len(lines) >= 2:
                            price = "解析中..."
                            title = lines[0]  # 第一行通常是标题或商圈名

                            if title in seen_titles:
                                continue
                            seen_titles.add(title)

                            # 遍历文字找带钱符号的那一行
                            for line in lines:
                                if '￥' in line or '¥' in line or '元' in line or '/' in line:
                                    price = line
                                    break

                            clean_data.append({
                                "title": title[:20] + "..." if len(title) > 20 else title,  # 截断太长的标题
                                "company": "Wellcee 唯心所寓",
                                "salary": price,
                                "city": "深圳"
                            })
                    except:
                        continue

                yield {"type": "log", "msg": "🎉 数据降维打击完毕！渲染最终面板..."}
                yield {"type": "result", "data": clean_data}

            except Exception as e:
                yield {"type": "log", "msg": f"❌ 操作发生致命错误: {str(e)}"}
                yield {"type": "result", "data": []}
            finally:
                await browser.close()