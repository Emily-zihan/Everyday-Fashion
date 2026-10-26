import os
import re
import json
import random
import urllib.request
import xml.etree.ElementTree as ET

# ==================== 1. RSS 订阅源配置 ====================
RSS_FEEDS = [
    {
        "source": "FBIF食品饮料创新",
        "url": "https://www.fbif.com/feed",
        "tag": "FBIF 创新速递 ↗"
    },
    {
        "source": "虎嗅网营销频道",
        "url": "https://www.huxiu.com/rss/0.xml",
        "tag": "虎嗅 ↗"
    },
    {
        "source": "广告门 Adquan",
        "url": "https://www.adquan.com/rss.php",
        "tag": "广告门创意 ↗"
    },
    {
        "source": "SocialBeta 营销案例",
        "url": "https://socialbeta.com/feed",
        "tag": "SocialBeta ↗"
    },
    {
        "source": "BoF 时尚商业",
        "url": "https://www.businessoffashion.com/feed",
        "tag": "BoF 极速直达 ↗"
    }
]

# ==================== 2. 主题分类高清美学图库 ====================
THEMED_IMAGES = {
    "fmcg": [  # 快消、饮料、包装、茶饮、咖啡类专属视觉
        "https://images.unsplash.com/photo-1554118811-1e0d58224f24?auto=format&fit=crop&w=1000&q=80",
        "https://images.unsplash.com/photo-1534482421-64566f976cfa?auto=format&fit=crop&w=1000&q=80"
    ],
    "luxury": [  # 奢侈品、高定美妆、香氛、珠宝类专属视觉
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=1000&q=80",
        "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?auto=format&fit=crop&w=1000&q=80"
    ],
    "runway": [  # 秀场、时装周、大片、空间美学类专属视觉
        "https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=1000&q=80",
        "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=1000&q=80"
    ],
    "campaign": [  # 营销大赏、快闪空间、全案复盘类专属视觉
        "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=1000&q=80",
        "https://images.unsplash.com/photo-1508296695146-257a814070b4?auto=format&fit=crop&w=1000&q=80"
    ]
}

# ==================== 3. 辅助解析函数 ====================
def extract_article_link(item):
    """精准提取 RSS 节点中的文章具体 URL"""
    link = ""
    link_node = item.find('link')
    if link_node is not None and link_node.text:
        link = link_node.text.strip()
    if not link:
        guid_node = item.find('guid')
        if guid_node is not None and guid_node.text and guid_node.text.startswith("http"):
            link = guid_node.text.strip()
    return link

def extract_article_image(item):
    """尝试多途径提取 RSS 文章自带的官方配图"""
    for child in item:
        if 'media' in child.tag.lower() or 'thumbnail' in child.tag.lower():
            img_url = child.attrib.get('url')
            if img_url and img_url.startswith('http'):
                return img_url

    enclosure = item.find('enclosure')
    if enclosure is not None:
        url = enclosure.attrib.get('url')
        if url and url.endswith(('.jpg', '.png', '.jpeg', '.webp')):
            return url

    raw_html = ""
    desc_node = item.find('description')
    if desc_node is not None and desc_node.text:
        raw_html += desc_node.text
        
    for child in item:
        if 'content' in child.tag.lower() and child.text:
            raw_html += child.text

    if raw_html:
        img_match = re.search(r'<img[^>]+src=["\'](http[^\"\']+)["\']', raw_html, re.IGNORECASE)
        if img_match:
            return img_match.group(1)

    return None

def classify_article(title, desc):
    """根据文章标题和摘要自动判定其所属分类并提取主题 Key"""
    text = (title + " " + desc).lower()
    
    luxury_keywords = ["奢品", "高定", "奢侈品", "珠宝", "香奈儿", "爱马仕", "ysl", "loewe", "chanel", "bain", "老钱风", "高级", "美妆"]
    fmcg_keywords = ["快消", "饮料", "饮料创新", "元气森林", "喜茶", "瑞幸", "咖啡", "茶饮", "瓶身", "包装", "麦肯锡", "消费", "白皮书"]
    runway_keywords = ["时装周", "秀场", "大片", "封面", "vogue", "巴黎", "装置艺术", "美学", "视觉", "色彩"]
    
    classes = ["content-card", "filter-item"]
    category_key = "campaign"
    
    if any(kw in text for kw in luxury_keywords):
        classes.append("luxury")
        category_key = "luxury"
    elif any(kw in text for kw in fmcg_keywords):
        classes.append("fmcg")
        category_key = "fmcg"
    elif any(kw in text for kw in runway_keywords):
        classes.append("runway")
        category_key = "runway"
    else:
        classes.append("luxury")
        classes.append("campaign")
        
    return " ".join(classes), category_key

def get_matched_image(article_img, category_key):
    """确保图片与案例主题契合，无抓取图片时从对应主题图库随机挑选"""
    if article_img and article_img.startswith('http'):
        return article_img
    
    pool = THEMED_IMAGES.get(category_key, THEMED_IMAGES["campaign"])
    return random.choice(pool)

def load_fallback_cases():
    """备份数据库，保证 RSS 网络异常时也能有高质量数据填充"""
    json_path = "fallback_cases.json"
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [(item["title"], item["link"], item["desc"], item["source"], item.get("category", "campaign")) for item in data]
        except Exception as e:
            print(f"读取 fallback_cases.json 失败: {e}")
            
    return [
        ("元气森林如何用极致的年轻化包装与口味迭代占领无糖气泡水心智", "https://socialbeta.com/", "解构快消饮料如何在同质化竞争中通过视觉符号与概念创新突出重围...", "FBIF食品饮料创新", "fmcg"),
        ("虎嗅年度营销大赏：情绪价值与品牌长效增长的博弈", "https://www.huxiu.com/", "探讨当下品牌如何从传统的流量收割转向用户心智的深度占领...", "虎嗅网营销频道", "campaign"),
        ("广告门创意金案：年度刷屏级 O2O 互动快闪空间复盘", "https://www.adquan.com/", "线下零售与美学装置如何完美结合，打造全网现象级打卡热潮...", "广告门 Adquan", "campaign"),
        ("喜茶 x 顶奢/艺术 IP 联名的符号学解构与破圈密码", "https://socialbeta.com/", "新茶饮跨界联名从最初的流量狂欢走向深度美学共创的演变路径...", "FBIF食品饮料创新", "fmcg"),
        ("瑞幸咖啡爆品矩阵背后的数字化供应链与私域裂变逻辑", "https://www.huxiu.com/", "复盘高频快消品牌如何通过高频上新与社交裂变实现单品爆发...", "虎嗅网营销频道", "fmcg"),
        ("独立香氛与高定美妆的线下沉浸式零售空间叙事", "https://www.businessoffashion.com/", "小众美学品牌如何通过气味和空间美学构筑极高的品牌心智护城河...", "BoF 时尚商业", "luxury"),
        ("2026 全球高端消费品市场趋势与 VIC 客户留存研判", "https://www.businessoffashion.com/", "深度剖析头部品牌如何在高净值客户运营中构建高阶情感链接...", "BoF 时尚商业", "luxury")
    ]

def generate_deep_analysis_html(title, desc, source):
    """自动构建可直接在 Modal 弹窗渲染的深度结构化剖析文章 HTML"""
    return f"""
    <div class='space-y-4 text-xs font-light text-gray-700 leading-relaxed'>
        <div class='p-3 bg-brand-champagne/40 border-l-2 border-brand-accent font-serif italic text-brand-dark'>
            “{title}” —— {source} 每日深度案例研判
        </div>
        <div>
            <h4 class='font-semibold text-brand-dark text-sm mb-1'>一、 案例背景与商业痛点 (Background & Challenge)</h4>
            <p>在当前消费市场同质化加剧与流量成本企高的大背景下，品牌亟需跳出传统的低价促销或单一功能宣导。{desc} 面对激烈的市场竞争，如何建立高阶美学溢价并实现用户的高频复购与情绪认同，成为本次营销策划的关键突破口。</p>
        </div>
        <div>
            <h4 class='font-semibold text-brand-dark text-sm mb-1'>二、 核心创意策略 (Big Idea & Visual Strategy)</h4>
            <p>1. <b>视觉与空间符号重构：</b>打破常规表达，将品牌的标志性 DNA 与高质感艺术视觉进行深度绑定。<br>
            2. <b>情绪价值注入：</b>围绕消费者的治愈感与圈层归属需求，将产品转译为生活方式的载体。</p>
        </div>
        <div>
            <h4 class='font-semibold text-brand-dark text-sm mb-1'>三、 全域传播路径 (Seeding & Channel Mix)</h4>
            <p>· <b>线上社交声量爆破：</b>以小红书、微信公众号为主阵地进行深度视觉种草与文案叙事。<br>
            · <b>线下体验场域延伸：</b>依托沉浸式快闪空间或艺术展陈，将线上流量高效引导至线下触觉体验。</p>
        </div>
    </div>
    """

# ==================== 4. 抓取与组合新闻逻辑 ====================
def fetch_multiple_news(limit=7):
    """抓取 7 条最新的新闻/案例，分别供给 7 个板块自动替换"""
    news_list = []
    for feed in RSS_FEEDS:
        try:
            req = urllib.request.Request(feed["url"], headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=10) as response:
                root = ET.fromstring(response.read())
                for item in root.findall('.//item')[:3]:
                    title = item.find('title').text if item.find('title') is not None else ""
                    link = extract_article_link(item)
                    desc = item.find('description').text if item.find('description') is not None else ""
                    if not link or not title:
                        continue

                    clean_desc = re.sub('<[^<]+?>', '', desc)[:150].strip() + "..."
                    auto_classes, category_key = classify_article(title.strip(), clean_desc)
                    raw_img = extract_article_image(item)
                    final_img = get_matched_image(raw_img, category_key)
                    
                    news_list.append({
                        "title": title.strip(),
                        "link": link,
                        "desc": clean_desc,
                        "deep_analysis": generate_deep_analysis_html(title.strip(), clean_desc, feed["source"]),
                        "source": feed["source"],
                        "tag": feed["tag"],
                        "image": final_img,
                        "classes": auto_classes
                    })
        except Exception as e:
            print(f"抓取 RSS [{feed['source']}] 发生错误: {e}")
            continue

    # 补充备用案例库，保证获取满 7 条内容
    fallback_cases = load_fallback_cases()
    random.shuffle(fallback_cases)
    i = 0
    while len(news_list) < limit:
        f_title, f_link, f_desc, f_source, f_cat = fallback_cases[i % len(fallback_cases)]
        auto_classes, category_key = classify_article(f_title, f_desc)
        final_img = get_matched_image(None, f_cat)
        
        news_list.append({
            "title": f_title,
            "link": f_link,
            "desc": f_desc,
            "deep_analysis": generate_deep_analysis_html(f_title, f_desc, f_source),
            "source": f_source,
            "tag": "深度研判 ↗",
            "image": final_img,
            "classes": auto_classes
        })
        i += 1
        
    random.shuffle(news_list)
    return news_list[:limit]

# ==================== 5. HTML 替换与更新逻辑 ====================
def update_index_html(news_list):
    """将抓取到的内容替换到 index.html 中指定的 7 大板块锚点位置"""
    html_path = "index.html"
    if not os.path.exists(html_path):
        print("错误：未能在当前目录找到 index.html 文件！")
        return

    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    def clean_js_str(s):
        return s.replace("'", "\\'").replace('"', '\\"').replace("\n", "")

    # 1. 替换 Hero 首页头条区
    n0 = news_list[0]
    new_hero = f'''<!-- HERO-UPDATE-START -->
        <div onclick="openAutoModal('{clean_js_str(n0['title'])}', '{clean_js_str(n0['deep_analysis'])}', '{n0['link']}', '{n0['source']}')" class="block relative group cursor-pointer img-zoom-container bg-brand-card p-3 border border-brand-border shadow-sm">
          <div class="relative h-[420px] md:h-[500px] overflow-hidden">
            <img src="{n0['image']}" alt="Hero" class="w-full h-full object-cover object-top">
            <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent"></div>
            <div class="absolute top-4 left-4 flex gap-2">
              <span class="px-3 py-1 bg-white/95 backdrop-blur-md text-[10px] tracking-widest uppercase font-semibold text-brand-dark">Featured Editorial</span>
            </div>
            <div class="absolute bottom-6 left-6 right-6 text-white space-y-2">
              <div class="text-xs uppercase tracking-widest text-brand-accent font-medium">Spotlight · {n0['source']} 头条精选</div>
              <h3 class="font-serif text-2xl md:text-3xl font-normal leading-tight">{n0['title']}</h3>
              <p class="text-xs text-gray-300 font-light line-clamp-2">{n0['desc']}</p>
            </div>
          </div>
        </div>
        <!-- HERO-UPDATE-END -->'''
    content = re.sub(r'(<!-- HERO-UPDATE-START -->)(.*?)(<!-- HERO-UPDATE-END -->)', new_hero, content, flags=re.DOTALL)

    # 2. 替换 Module 01 (灵感视觉与快闪空间)
    n1 = news_list[1]
    new_m1 = f'''<!-- MODULE-01-START -->
    <div onclick="openAutoModal('{clean_js_str(n1['title'])}', '{clean_js_str(n1['deep_analysis'])}', '{n1['link']}', '{n1['source']}')" class="{n1['classes']} gallery-card bg-brand-card p-4 border border-brand-border cursor-pointer group">
      <div class="img-zoom-container relative h-80 mb-4 bg-gray-100 overflow-hidden">
        <img src="{n1['image']}" alt="Gallery" class="w-full h-full object-cover">
        <span class="absolute top-3 left-3 px-2 py-1 bg-white/90 text-[9px] uppercase tracking-widest font-medium">点击展开阅读 ↗</span>
      </div>
      <div class="space-y-2">
        <div class="flex justify-between items-center text-[10px] uppercase text-brand-muted tracking-widest">
          <span>{n1['source']} · 每日热点案例</span>
          <span>TODAY</span>
        </div>
        <h3 class="font-serif text-xl font-normal group-hover:text-brand-accent transition-colors">{n1['title']}</h3>
        <p class="text-xs text-brand-muted font-light line-clamp-2">{n1['desc']}</p>
      </div>
    </div>
    <!-- MODULE-01-END -->'''
    content = re.sub(r'(<!-- MODULE-01-START -->)(.*?)(<!-- MODULE-01-END -->)', new_m1, content, flags=re.DOTALL)

    # 3. 替换 Module 02 (经典/爆款营销拆解)
    n2 = news_list[2]
    new_m2 = f'''<!-- MODULE-02-START -->
    <div onclick="openAutoModal('{clean_js_str(n2['title'])}', '{clean_js_str(n2['deep_analysis'])}', '{n2['link']}', '{n2['source']}')" class="{n2['classes']} bg-brand-card p-6 border border-brand-border space-y-4 cursor-pointer hover:border-brand-dark transition-colors">
      <div class="flex justify-between items-center text-xs uppercase tracking-widest">
        <span class="text-brand-accent font-semibold">今日热点营销深度拆解</span>
        <span class="text-brand-muted">{n2['source']}</span>
      </div>
      <h3 class="font-serif text-2xl font-normal">{n2['title']}</h3>
      <p class="text-xs text-brand-muted font-light leading-relaxed line-clamp-2">{n2['desc']}</p>
      <div class="pt-2 flex items-center justify-between text-xs border-t border-brand-border/40">
        <span class="font-mono text-[11px] text-brand-dark">包含 4 维案例拆解</span>
        <span class="hover:text-brand-accent uppercase tracking-widest text-[10px] font-semibold">点击阅读完整案例报告 ↗</span>
      </div>
    </div>
    <!-- MODULE-02-END -->'''
    content = re.sub(r'(<!-- MODULE-02-START -->)(.*?)(<!-- MODULE-02-END -->)', new_m2, content, flags=re.DOTALL)

    # 4. 替换 Module 03 (秀场趋势与情绪板)
    n3 = news_list[3]
    new_m3 = f'''<!-- MODULE-03-START -->
    <div onclick="openAutoModal('{clean_js_str(n3['title'])}', '{clean_js_str(n3['deep_analysis'])}', '{n3['link']}', '{n3['source']}')" class="{n3['classes']} bg-brand-card p-4 border border-brand-border flex gap-4 items-center cursor-pointer group">
      <div class="w-24 h-24 flex-shrink-0 img-zoom-container overflow-hidden">
        <img src="{n3['image']}" alt="Runway" class="w-full h-full object-cover">
      </div>
      <div class="space-y-1">
        <span class="text-[9px] uppercase tracking-widest text-brand-accent font-semibold">{n3['source']} 趋势拆解 ↗</span>
        <h4 class="font-serif text-lg leading-tight group-hover:text-brand-accent transition-colors line-clamp-1">{n3['title']}</h4>
        <p class="text-[11px] text-brand-muted font-light line-clamp-1">点击查看完整趋势分析报告与原文链接</p>
      </div>
    </div>
    <!-- MODULE-03-END -->'''
    content = re.sub(r'(<!-- MODULE-03-START -->)(.*?)(<!-- MODULE-03-END -->)', new_m3, content, flags=re.DOTALL)

    # 5. 替换 Module 04 (趋势研判与品牌 DNA)
    n4 = news_list[4]
    new_m4 = f'''<!-- MODULE-04-START -->
    <div onclick="openAutoModal('{clean_js_str(n4['title'])}', '{clean_js_str(n4['deep_analysis'])}', '{n4['link']}', '{n4['source']}')" class="{n4['classes']} bg-brand-card p-6 border border-brand-border space-y-4 cursor-pointer hover:border-brand-dark transition-colors">
      <div class="flex justify-between items-center text-[10px] uppercase tracking-widest text-brand-muted">
        <span>{n4['source']} · 每日精读</span>
        <span>TODAY</span>
      </div>
      <h3 class="font-serif text-xl font-normal">{n4['title']}</h3>
      <p class="text-xs text-brand-muted font-light leading-relaxed line-clamp-2">{n4['desc']}</p>
      <span class="text-xs uppercase tracking-widest font-semibold text-brand-dark inline-block text-left">点击展开完整研判报告 ↗</span>
    </div>
    <!-- MODULE-04-END -->'''
    content = re.sub(r'(<!-- MODULE-04-START -->)(.*?)(<!-- MODULE-04-END -->)', new_m4, content, flags=re.DOTALL)

    # 6. 替换 Module 05 (每日灵感卡片)
    n5 = news_list[5]
    new_m5 = f'''<!-- AUTO-UPDATE-START -->
    <div onclick="openAutoModal('{clean_js_str(n5['title'])}', '{clean_js_str(n5['deep_analysis'])}', '{n5['link']}', '{n5['source']}')" class="block polaroid-card bg-white p-4 border border-brand-border space-y-3 shadow-sm cursor-pointer group">
      <div class="h-48 bg-gray-100 overflow-hidden relative">
        <img src="{n5['image']}" alt="Spark" class="w-full h-full object-cover">
        <span class="absolute bottom-2 right-2 bg-black/70 text-white text-[9px] px-2 py-0.5 uppercase">TODAY AUTO</span>
      </div>
      <div class="space-y-1">
        <span class="text-[9px] font-mono text-brand-accent uppercase">{n5['source']} ↗</span>
        <p class="text-xs text-brand-dark font-medium line-clamp-2">“{n5['title']}”</p>
      </div>
      <div class="text-[10px] text-brand-muted border-t border-brand-border pt-2 group-hover:text-brand-accent">
        点击阅读案例深度解析 ↗
      </div>
    </div>
    <!-- AUTO-UPDATE-END -->'''
    content = re.sub(r'(<!-- AUTO-UPDATE-START -->)(.*?)(<!-- AUTO-UPDATE-END -->)', new_m5, content, flags=re.DOTALL)

    # 7. 替换 Interactive Counterpoint Lab 对照实验室速递
    n6 = news_list[6]
    new_lab = f'''<!-- LAB-UPDATE-START -->
    <div onclick="openAutoModal('{clean_js_str(n6['title'])}', '{clean_js_str(n6['deep_analysis'])}', '{n6['link']}', '{n6['source']}')" class="mb-8 p-6 bg-white border border-brand-accent shadow-sm cursor-pointer hover:shadow-md transition-shadow text-left">
      <div class="flex items-center justify-between mb-3">
        <span class="text-[10px] font-mono uppercase tracking-widest bg-brand-accent/20 text-brand-dark px-3 py-1 font-semibold">🔥 今日实时自动对标速递 ({n6['source']})</span>
        <span class="text-xs text-brand-accent font-mono">点击查看案例解析 ↗</span>
      </div>
      <h3 class="text-lg font-serif font-normal mb-2 text-brand-dark">“{n6['title']}”</h3>
      <p class="text-gray-600 text-xs leading-relaxed font-light">{n6['desc']}</p>
    </div>
    <!-- LAB-UPDATE-END -->'''
    content = re.sub(r'(<!-- LAB-UPDATE-START -->)(.*?)(<!-- LAB-UPDATE-END -->)', new_lab, content, flags=re.DOTALL)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("已成功写入 index.html！7 大板块内容、美学图片与结构化解析更新完成。")

# ==================== 6. 主程序入口 ====================
if __name__ == "__main__":
    news = fetch_multiple_news(limit=7)
    update_index_html(news)
