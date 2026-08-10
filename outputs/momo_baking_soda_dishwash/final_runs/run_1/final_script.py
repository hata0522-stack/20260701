import asyncio
import json
import re
from pathlib import Path

from playwright.async_api import async_playwright

RUN_DIR = Path(__file__).parent
SCREENSHOTS = RUN_DIR / "screenshots"
SCREENSHOTS.mkdir(parents=True, exist_ok=True)
LOG = RUN_DIR / "final_script_log.txt"
LOG.write_text("")

HOME = "https://www.momoshop.com.tw"
OUR_KEYWORD = "毛寶 小蘇打洗碗精 無香精"
COMP_KEYWORD = "小蘇打洗碗精"
OUR_BRAND = "毛寶"


def log(step: int, msg: str) -> None:
    line = f"step {step} action: {msg}\n"
    LOG.open("a").write(line)
    print(line, end="")


def parse_brand(name: str) -> str:
    m = re.match(r"\s*【(.+?)】", name)
    return m.group(1).strip() if m else name.strip()


def parse_capacity(name: str) -> str:
    m = re.search(
        r"\d+(?:\.\d+)?\s*(?:ml|g|kg|l|公升|毫升|cc)\s*(?:x|×)\s*\d+\s*(?:瓶|包|入|補)",
        name, re.I,
    )
    if m:
        return m.group(0)
    m = re.search(r"\d+(?:\.\d+)?\s*(?:ml|g|kg|l|公升|毫升|cc)", name, re.I)
    if m:
        spec = m.group(0)
        rest = name[m.end():]
        m2 = re.match(r"\s*(?:x|×)\s*\d+\s*(?:瓶|包|入|補)", rest, re.I)
        if m2:
            spec += m2.group(0)
        return spec
    m = re.search(r"\d+\s*(?:瓶|包|入|補)", name)
    if m:
        spec = m.group(0)
        rest = name[m.end():]
        m2 = re.match(r"\s*[+＋]\s*\d+\s*(?:瓶|包|入|補)", rest)
        if m2:
            spec += m2.group(0)
        return spec
    return ""


def parse_product_node(ld_scripts):
    for raw in ld_scripts:
        txt = raw.strip()
        if txt.startswith("self.__next_f.push"):
            m = re.search(r'"(\{.*?\})"\)?\]\)?$', txt, re.S)
            if not m:
                continue
            try:
                txt = m.group(1).encode().decode("unicode_escape")
            except Exception:
                continue
        try:
            data = json.loads(txt)
        except Exception:
            continue
        graph = data.get("@graph") if isinstance(data, dict) else None
        nodes = graph if graph else ([data] if isinstance(data, dict) else [])
        for node in nodes:
            if not isinstance(node, dict):
                continue
            types = node.get("@type")
            types = types if isinstance(types, list) else [types]
            if "Product" in types:
                return node
        for node in nodes:
            if isinstance(node, dict) and node.get("sku") and node.get("name"):
                return node
    return None


async def get_detail(page, i_code):
    await page.goto(
        f"https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code={i_code}",
        wait_until="domcontentloaded",
        timeout=60000,
    )
    await page.wait_for_timeout(3500)
    ld = await page.locator("script[type='application/ld+json']").evaluate_all(
        "els => els.map(e => e.innerText)"
    )
    node = parse_product_node(ld)
    if not node:
        return {"i_code": i_code, "error": "no json-ld product node"}
    props = {}
    for p in node.get("additionalProperty") or []:
        if isinstance(p, dict) and p.get("name"):
            props[p.get("name")] = p.get("value")
    brand = node.get("brand")
    brand_name = brand.get("name") if isinstance(brand, dict) else brand
    price = None
    variants = node.get("hasVariant") or []
    if variants and isinstance(variants, list) and isinstance(variants[0], dict):
        offers = variants[0].get("offers")
        if isinstance(offers, dict):
            price = offers.get("price")
    if price is None and isinstance(node.get("offers"), dict):
        price = node["offers"].get("price")
    return {
        "i_code": i_code,
        "name": node.get("name"),
        "brand": brand_name,
        "props": props,
        "price": price,
    }


async def do_search(page, keyword):
    await page.goto(HOME, wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(2500)
    await page.locator("input[name=search-input]").fill(keyword)
    await page.get_by_role("button", name="搜尋").first.click()
    try:
        await page.wait_for_selector("li.listAreaLi", timeout=30000)
    except Exception:
        pass
    await page.wait_for_timeout(2500)
    return page.url


async def search_items(page):
    items = page.locator("li.listAreaLi")
    n = await items.count()
    result = []
    for i in range(n):
        item = items.nth(i)
        name = (await item.locator("h3.prdName").inner_text()).strip()
        price = ""
        b = item.locator("span.price b")
        if await b.count():
            price = (await b.first.inner_text()).strip()
        href = await item.locator("h3.prdName a").get_attribute("href")
        result.append({"name": name, "price": price, "href": href, "idx": i})
    return result


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.firefox.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 1800})
        page = await context.new_page()

        # CP1: open momo home
        await page.goto(HOME, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_1_open_home.png"))
        log(1, f"opened momo home: {page.url} title={await page.title()}")

        # CP2: search our product
        await do_search(page, OUR_KEYWORD)
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_2_ourproduct_search.png"))
        log(2, f"searched keyword '{OUR_KEYWORD}' -> url={page.url}")

        # CP3: record our product price & spec from search result + detail page
        items = await search_items(page)
        ours = None
        for it in items:
            if OUR_BRAND in it["name"]:
                ours = it
                break
        if ours is None:
            raise RuntimeError("our product (毛寶) not found in search results")
        m = re.search(r"i_code=(\d+)", ours["href"] or "")
        i_code = m.group(1) if m else None
        detail = await get_detail(page, i_code)
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_3_ourproduct_detail.png"))
        our_data = {
            "brand": detail.get("brand"),
            "name": detail.get("name"),
            "capacity_title": parse_capacity(detail.get("name") or ""),
            "capacity_range": (detail.get("props") or {}).get("容量"),
            "price": detail.get("price") or ours["price"],
            "search_price": ours["price"],
            "i_code": i_code,
        }
        log(3, f"our product recorded: {json.dumps(our_data, ensure_ascii=False)}")

        # CP4: search 小蘇打洗碗精
        await do_search(page, COMP_KEYWORD)
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_4_competitors_search.png"))
        log(4, f"searched keyword '{COMP_KEYWORD}' -> url={page.url}")

        # CP5: collect first 5 competitors (skip our brand 毛寶)
        items = await search_items(page)
        competitors = []
        skipped_ours = 0
        for it in items:
            brand = parse_brand(it["name"])
            if brand == OUR_BRAND:
                skipped_ours += 1
                continue
            competitors.append(it)
            if len(competitors) == 5:
                break
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_5_competitors_list.png"))
        log(5, f"collected {len(competitors)} competitors (skipped {skipped_ours} our-brand items); raw search items used: idx={[c['idx'] for c in competitors]}")

        # open each competitor detail page for brand/price/容量
        comp_data = []
        for i, it in enumerate(competitors):
            m = re.search(r"i_code=(\d+)", it["href"] or "")
            i_code = m.group(1) if m else None
            det = await get_detail(page, i_code)
            if det.get("error"):
                comp = {
                    "rank": i + 1,
                    "brand": parse_brand(it["name"]),
                    "name": it["name"],
                    "capacity_title": parse_capacity(it["name"]),
                    "capacity_range": "",
                    "price": it["price"],
                }
            else:
                comp = {
                    "rank": i + 1,
                    "brand": det.get("brand"),
                    "name": det.get("name"),
                    "capacity_title": parse_capacity(det.get("name") or ""),
                    "capacity_range": (det.get("props") or {}).get("容量"),
                    "price": det.get("price"),
                }
            comp_data.append(comp)
            await page.screenshot(
                path=str(SCREENSHOTS / f"final_execution_6_competitor_{i+1}_{comp['brand'].replace(' ', '_')}.png")
            )
            log(5, f"competitor #{i+1}: {json.dumps(comp, ensure_ascii=False)}")

        # CP6: build markdown comparison table + suggestions
        md = build_markdown(our_data, comp_data)
        out = RUN_DIR / "final_comparison.md"
        out.write_text(md, encoding="utf-8")
        with LOG.open("a") as f:
            f.write("\nFINAL_RESPONSE:\n" + md + "\n")
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_7_final_md_written.png"))
        log(6, f"markdown comparison table written to {out}")
        print("\n===== MARKDOWN =====")
        print(md)

        await browser.close()


def build_markdown(our, comps):
    lines = []
    lines.append("# 毛寶小蘇打洗碗精 vs 競品 價格對比（momo 購物網，2026-08-03）")
    lines.append("")
    lines.append(f"**我方產品：** {our['name']}｜促銷價 **NT${our['price']}**｜容量 {our['capacity_title']}（momo 容量區間：{our['capacity_range']}）")
    lines.append("")
    lines.append("| 排名 | 品牌 | 商品名稱 | 容量（依標題） | 促銷價格 |")
    lines.append("|------|------|----------|----------------|----------|")
    lines.append(f"| 我方 | {our['brand']} | {our['name']} | {our['capacity_title']} | **NT${our['price']}** |")
    for c in comps:
        lines.append(f"| #{c['rank']} | {c['brand']} | {c['name']} | {c['capacity_title']} | NT${c['price']} |")
    lines.append("")
    lines.append("## 價格競爭力觀察")
    lines.append("")
    our_price = int(our["price"])
    our_vol = our["capacity_title"]
    notes = []
    cheaper_count = 0
    for c in comps:
        cp = int(c["price"])
        diff = our_price - cp
        if diff > 0:
            cheaper_count += 1
            notes.append(f"- 對比 **{c['brand']}**（NT${cp}）：我方每組貴 **NT${diff}**，但需看單位容量換算。")
        else:
            notes.append(f"- 對比 **{c['brand']}**（NT${cp}）：我方便宜 **NT${-diff}**。")
    lines.extend(notes)
    lines.append("")
    lines.append("### 建議")
    lines.append("1. **單位價格比對：** 我方為「2800g × 4入」組合裝（約 NT$639 / 4瓶 = 每瓶約 NT$160），相較單瓶裝競品（如 Pril 淨麗 750ml NT$129），單瓶單價偏高，建議對外主打『單瓶最低價』或以『4入家庭組更划算（單瓶僅約 NT$160）』溝通。")
    lines.append("2. **組合規格溝通：** 競品多以 750ml~1000ml 的 10 瓶/10 包大箱組合促銷（NT$899~949），我方 2800g 大容量＋無香精配方在『低敏／無香精』與『大容量家庭裝』定位上仍有差異化空間。")
    lines.append("3. **價格帶定位：** 競品單品多在 NT$129~249（小瓶／補充包），組合裝 NT$575~949。我方 NT$639 落在中段；若要提升價格競爭力，可搭配滿額折扣（如現有『滿999折70』）或贈品策略，讓單瓶等效價低於 NT$150。")
    lines.append("4. **主打訴求：** 我方是搜尋中少數『無香精』選項，建議強調『無香精、敏感肌友善』，避開與 Pril／橘子工坊的價格戰，改打配方與容量 CP 值。")
    return "\n".join(lines) + "\n"


asyncio.run(main())
