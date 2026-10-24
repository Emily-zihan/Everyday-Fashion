import os
import re
import random
import urllib.request
import xml.etree.ElementTree as ET

# 订阅包含 FBIF、虎嗅、广告门、SocialBeta 及 BoF 的权威营销与创新媒体源
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

# 高质感美学备用图库（当文章未自带图片时自动顶替）
FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1508296695146-257a814070b4?auto=format&fit=crop&w=800&q=80"
]

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
        type_str = enclosure.attrib.get('type', '')
        if url and ('image' in type_str or url.endswith(('.jpg', '.png', '.jpeg', '.webp'))):
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
    """根据文章标题和摘要自动判定其所属的分类标签类名"""
    text = (title + " " + desc).lower()
    
    # 关键词匹配规则
    luxury_keywords = ["奢品", "高定", "奢侈品", "珠宝", "香奈儿", "爱马仕", "ysl", "loewe", "chanel", "bain", "维多利亚", "老钱风", "高级"]
    fmcg_keywords = ["快消", "饮料", "饮料创新", "元气森林", "喜茶", "瑞幸", "咖啡", "茶饮", "瓶身", "包装", "麦肯锡", "消费", "白皮书"]
    runway_keywords = ["时装周", "秀场", "大片", "封面", "vogue", "巴黎", "装置艺术", "美学", "视觉", "色彩"]
    
    classes = ["content-card", "filter-item"]
    
    if any(kw in text for kw in luxury_keywords):
        classes.append("luxury")
    if any(kw in text for kw in fmcg_keywords):
        classes.append("fmcg")
    if any(kw in text for kw in runway_keywords):
        classes.append("runway")
        
    # 默认兜底归类
    if "fmcg" not in classes and "luxury" not in classes:
        classes.append("luxury")
        classes.append("campaign")
    else:
        classes.append("campaign")
        
    return " ".join(classes)

def generate_deep_analysis_html(title, desc, source):
    """自动生成数百字的完整结构化案例深度剖析文章 (HTML)"""
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
            <p>1. <b>视觉与空间符号重构：</b>打破常规表达，将品牌的标志性 DNA 与高质感艺术视觉进行深度绑定，构建强烈的识别资产。<br>
            2. <b>情绪价值注入：</b>围绕当下消费者的‘治愈感’与‘圈层归属’需求，将产品转译为生活方式的载体，实现高溢价与精神认同。</p>
        </div>

        <div>
            <h4 class='font-semibold text-brand-dark text-sm mb-1'>三、 全域传播路径 (Seeding & Channel Mix)</h4>
            <p>· <b>线上社交声量爆破：</b>以小红书、微信公众号为主阵地进行深度视觉种草与文案叙事，联合头部 KOL 形成多维度的口碑共振。<br>
            · <b>线下体验场域延伸：</b>依托沉浸式快闪空间/艺术展陈，将线上流量高效引导至线下触觉体验，打造社交打卡闭环。</p>
        </div>

        <div>
            <h4 class='font-semibold text-brand-dark text-sm mb-1'>四、 商业转化与长线资产沉淀 (Impact & Assets)</h4>
            <p>通过本次营销动作，品牌不仅成功占领了细分赛道的顶尖心智，更实现了全网声量与高客单复购率的双重爆发，将短期流量转化为可沉淀的品牌心智资产。</p>
        </div>
    </div>
    """

def fetch_multiple_news(limit=6):
    """抓取多源营销创新热点，并自动附加智能分类类名"""
    news_list = []
    for feed in RSS_FEEDS:
        try:
            req = urllib.request.Request(feed["url"], headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                
                for item in root.findall('.//item')[:3]:
                    title = item.find('title').text if item.find('title') is not None else ""
                    link = extract_article_link(item)
                    desc = item.find('description').text if item.find('description') is not None else ""
                    
                    if not link or not title:
                        continue

                    clean_desc = re.sub('<[^<]+?>', '', desc)[:150].strip() + "..."
                    source_name = feed["source"]
                    
                    article_img = extract_article_image(item)
                    if not article_img:
                        article_img = random.choice(FALLBACK_IMAGES)
                    
                    deep_html = generate_deep_analysis_html(title.strip(), clean_desc, source_name)
                    
                    # 核心步骤：在此处调用分类函数，为新闻赋予专属分类类名
                    auto_classes = classify_article(title.strip(), clean_desc)
                    
                    news_list.append({
                        "title": title.strip(),
                        "link": link,
                        "desc": clean_desc,
                        "deep_analysis": deep_html,
                        "source": source_name,
                        "tag": feed["tag"],
                        "image": article_img,
                        "classes": auto_classes  # 存储智能分类标签
                    })
        except Exception as e:
            print(f"抓取 {feed['source']} 失败: {e}")
            continue

    # 备用案例库
    fallback_cases = [
        ("元气森林如何用极致的年轻化包装与口味迭代占领无糖气泡水心智", "https://socialbeta.com/", "解构快消饮料如何在同质化竞争中通过视觉符号与概念创新突出重围...", "FBIF食品饮料创新"),
        ("虎嗅年度营销大赏：情绪价值与品牌长效增长的博弈", "https://www.huxiu.com/", "探讨当下品牌如何从传统的流量收割转向用户心智的深度占领...", "虎嗅网营销频道"),
        ("广告门创意金案：年度刷屏级 O2O 互动快闪空间复盘", "https://www.adquan.com/", "线下零售与美学装置如何完美结合，打造全网现象级打卡热潮...", "广告门 Adquan"),
        ("喜茶 x 顶奢/艺术 IP 联名的符号学解构与破圈密码", "https://socialbeta.com/", "新茶饮跨界联名从最初的流量狂欢走向深度美学共创的演变路径...", "FBIF食品饮料创新"),
        ("瑞幸咖啡爆品矩阵背后的数字化供应链与私域裂变逻辑", "https://www.huxiu.com/", "复盘高频快消品牌如何通过高频上新与社交裂变实现单品爆发...", "虎嗅网营销频道"),
        ("独立香氛与高定美妆的线下沉浸式零售空间叙事", "https://www.businessoffashion.com/", "小众美学品牌如何通过气味和空间美学构筑极高的品牌心智护城河...", "BoF 时尚商业")
    ]
    
    random.shuffle(fallback_cases)
    i = 0
    while len(news_list) < limit:
        f_title, f_link, f_desc, f_source = fallback_cases[i % len(fallback_cases)]
        auto_classes = classify_article(f_title, f_desc)
        news_list.append({
            "title": f_title,
            "link": f_link,
            "desc": f_desc,
            "deep_analysis": generate_deep_analysis_html(f_title, f_desc, f_source),
            "source": f_source,
            "tag": "深度研判 ↗",
            "image": FALLBACK_IMAGES[i % len(FALLBACK_IMAGES)],
            "classes": auto_classes
        })
        i += 1
        
    random.shuffle(news_list)
    return news_list[:limit]

def update_index_html(news_list):
    """将动态分类类名应用到 HTML 各个模块卡片中"""
    html_path = "index.html"
    if not os.path.exists(html_path):
        print("未找到 index.html 文件！")
        return

    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    def clean_js_str(s):
        return s.replace("'", "\\'").replace('"', '\\"').replace("\n", "")

    # 1. Module 01 灵感视觉深度卡片
    m1_pattern = r'(<!-- MODULE-01-START -->)(.*?)(<!-- MODULE-01-END -->)'
    new_m1_html = f'''<!-- MODULE-01-START -->
      <div onclick="openAutoModal('{clean_js_str(news_list[0]['title'])}', '{clean_js_str(news_list[0]['deep_analysis'])}', '{news_list[0]['link']}', '{news_list[0]['source']}')" class="{news_list[0]['classes']} gallery-card bg-brand-card p-4 border border-brand-border cursor-pointer group">
        <div class="img-zoom-container relative h-80 mb-4 bg-gray-100 overflow-hidden">
          <img src="{news_list[0]['image']}" alt="Gallery" class="w-full h-full object-cover">
          <span class="absolute top-3 left-3 px-2 py-1 bg-white/90 text-[9px] uppercase tracking-widest font-medium">点击阅读完整案例拆解 ↗</span>
        </div>
        <div class="space-y-2">
          <div class="flex justify-between items-center text-[10px] uppercase text-brand-muted tracking-widest">
            <span>{news_list[0]['source']} · 每日热点案例</span>
            <span>TODAY</span>
          </div>
          <h3 class="font-serif text-xl font-normal group-hover:text-brand-accent transition-colors">
            {news_list[0]['title']}
          </h3>
          <p class="text-xs text-brand-muted font-light line-clamp-2">
            点击展开查看背景、核心策略、传播路径与商业转化的完整分析全文 ↗
          </p>
        </div>
      </div>
      <!-- MODULE-01-END -->'''

    # 2. Module 02 营销拆解深度卡片
    m2_pattern = r'(<!-- MODULE-02-START -->)(.*?)(<!-- MODULE-02-END -->)'
    new_m2_html = f'''<!-- MODULE-02-START -->
      <div onclick="openAutoModal('{clean_js_str(news_list[1]['title'])}', '{clean_js_str(news_list[1]['deep_analysis'])}', '{news_list[1]['link']}', '{news_list[1]['source']}')" class="{news_list[1]['classes']} bg-brand-card p-6 border border-brand-border space-y-4 cursor-pointer hover:border-brand-dark transition-colors">
        <div class="flex justify-between items-center text-xs uppercase tracking-widest">
          <span class="text-brand-accent font-semibold">今日热点营销深度拆解</span>
          <span class="text-brand-muted">{news_list[1]['source']}</span>
        </div>
        <h3 class="font-serif text-2xl font-normal">
          {news_list[1]['title']}
        </h3>
        <p class="text-xs text-brand-muted font-light leading-relaxed line-clamp-2">
          {news_list[1]['desc']}
        </p>
        <div class="pt-2 flex items-center justify-between text-xs border-t border-brand-border/40">
          <span class="font-mono text-[11px] text-brand-dark">包含 4 维案例拆解</span>
          <span class="hover:text-brand-accent uppercase tracking-widest text-[10px] font-semibold">点击阅读完整案例报告 ↗</span>
        </div>
      </div>
      <!-- MODULE-02-END -->'''

    # 3. Module 03 秀场趋势深度卡片
    m3_pattern = r'(<!-- MODULE-03-START -->)(.*?)(<!-- MODULE-03-END -->)'
    new_m3_html = f'''<!-- MODULE-03-START -->
      <div onclick="openAutoModal('{clean_js_str(news_list[2]['title'])}', '{clean_js_str(news_list[2]['deep_analysis'])}', '{news_list[2]['link']}', '{news_list[2]['source']}')" class="{news_list[2]['classes']} bg-brand-card p-4 border border-brand-border flex gap-4 items-center cursor-pointer group">
        <div class="w-24 h-24 flex-shrink-0 img-zoom-container overflow-hidden">
          <img src="{news_list[2]['image']}" alt="Runway" class="w-full h-full object-cover">
        </div>
        <div class="space-y-1">
          <span class="text-[9px] uppercase tracking-widest text-brand-accent font-semibold">{news_list[2]['source']} 趋势拆解 ↗</span>
          <h4 class="font-serif text-lg leading-tight group-hover:text-brand-accent transition-colors line-clamp-1">
            {news_list[2]['title']}
          </h4>
          <p class="text-[11px] text-brand-muted font-light line-clamp-1">点击查看完整趋势分析报告与原文链接</p>
        </div>
      </div>
      <!-- MODULE-03-END -->'''

    # 4. Module 04 趋势研判深度卡片
    m4_pattern = r'(<!-- MODULE-04-START -->)(.*?)(<!-- MODULE-04-END -->)'
    new_m4_html = f'''<!-- MODULE-04-START -->
      <div onclick="openAutoModal('{clean_js_str(news_list[3]['title'])}', '{clean_js_str(news_list[3]['deep_analysis'])}', '{news_list[3]['link']}', '{news_list[3]['source']}')" class="{news_list[3]['classes']} bg-brand-card p-6 border border-brand-border space-y-4 cursor-pointer hover:border-brand-dark transition-colors">
        <div class="flex justify-between items-center text-[10px] uppercase tracking-widest text-brand-muted">
          <span>{news_list[3]['source']} · 每日精读</span>
          <span>TODAY</span>
        </div>
        <h3 class="font-serif text-xl font-normal">
          {news_list[3]['title']}
        </h3>
        <p class="text-xs text-brand-muted font-light leading-relaxed line-clamp-2">
          {news_list[3]['desc']}
        </p>
        <span class="text-xs uppercase tracking-widest font-semibold text-brand-dark inline-block text-left">
          点击展开完整研判报告 ↗
        </span>
      </div>
      <!-- MODULE-04-END -->'''

    # 5. Module 05 每日卡片
    m5_pattern = r'(<!-- AUTO-UPDATE-START -->)(.*?)(<!-- AUTO-UPDATE-END -->)'
    new_m5_html = f'''<!-- AUTO-UPDATE-START -->
      <div onclick="openAutoModal('{clean_js_str(news_list[4]['title'])}', '{clean_js_str(news_list[4]['deep_analysis'])}', '{news_list[4]['link']}', '{news_list[4]['source']}')" class="block polaroid-card bg-white p-4 border border-brand-border space-y-3 shadow-sm cursor-pointer group">
        <div class="h-48 bg-gray-100 overflow-hidden relative">
          <img src="{news_list[4]['image']}" alt="Spark" class="w-full h-full object-cover">
          <span class="absolute bottom-2 right-2 bg-black/70 text-white text-[9px] px-2 py-0.5 uppercase">TODAY AUTO</span>
        </div>
        <div class="space-y-1">
          <span class="text-[9px] font-mono text-brand-accent uppercase">{news_list[4]['source']} ↗</span>
          <p class="text-xs text-brand-dark font-medium line-clamp-2">“{news_list[4]['title']}”</p>
        </div>
        <div class="text-[10px] text-brand-muted border-t border-brand-border pt-2 group-hover:text-brand-accent">
          点击阅读案例深度解析 ↗
        </div>
      </div>
      <!-- AUTO-UPDATE-END -->'''

    # 6. 对照实验室速递
    lab_pattern = r'(<!-- LAB-UPDATE-START -->)(.*?)(<!-- LAB-UPDATE-END -->)'
    new_lab_html = f'''<!-- LAB-UPDATE-START -->
    <div onclick="openAutoModal('{clean_js_str(news_list[5]['title'])}', '{clean_js_str(news_list[5]['deep_analysis'])}', '{news_list[5]['link']}', '{news_list[5]['source']}')" class="mb-8 p-6 bg-white border border-brand-accent shadow-sm cursor-pointer hover:shadow-md transition-shadow">
      <div class="flex items-center justify-between mb-3">
        <span class="text-[10px] font-mono uppercase tracking-widest bg-brand-accent/20 text-brand-dark px-3 py-1 font-semibold">🔥 今日实时自动对标速递 ({news_list[5]['source']})</span>
        <span class="text-xs text-brand-accent font-mono">点击查看案例解析 ↗</span>
      </div>
      <h3 class="text-lg font-serif font-normal mb-2 text-brand-dark">“{news_list[5]['title']}”</h3>
      <p class="text-gray-600 text-xs leading-relaxed font-light">{news_list[5]['desc']}</p>
    </div>
    <!-- LAB-UPDATE-END -->'''

    # 7. Hero 首页头条大图与文章替换
    hero_pattern = r'(<!-- HERO-UPDATE-START -->)(.*?)(<!-- HERO-UPDATE-END -->)'
    new_hero_html = f'''<!-- HERO-UPDATE-START -->
        <div onclick="openAutoModal('{clean_js_str(news_list[0]['title'])}', '{clean_js_str(news_list[0]['deep_analysis'])}', '{news_list[0]['link']}', '{news_list[0]['source']}')" class="block relative group cursor-pointer img-zoom-container bg-brand-card p-3 border border-brand-border shadow-sm">
          <div class="relative h-[420px] md:h-[500px] overflow-hidden">
            <img src="{news_list[0]['image']}" 
                 alt="Luxury & FMCG Campaign" 
                 class="w-full h-full object-cover object-top">
            <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent"></div>
            
            <div class="absolute top-4 left-4 flex gap-2">
              <span class="px-3 py-1 bg-white/95 backdrop-blur-md text-[10px] tracking-widest uppercase font-semibold text-brand-dark">
                Featured Editorial
              </span>
              <span class="px-3 py-1 bg-brand-accent text-brand-dark backdrop-blur-md text-[10px] tracking-widest uppercase font-semibold">
                点击展开深度阅读 ↗
              </span>
            </div>

            <div class="absolute bottom-6 left-6 right-6 text-white space-y-2">
              <div class="text-xs uppercase tracking-widest text-brand-accent font-medium">Spotlight · {news_list[0]['source']} 头条精选</div>
              <h3 class="font-serif text-2xl md:text-3xl font-normal leading-tight">
                {news_list[0]['title']}
              </h3>
              <p class="text-xs text-gray-300 font-light line-clamp-2">
                {news_list[0]['desc']}
              </p>
            </div>
          </div>
        </div>
        <!-- HERO-UPDATE-END -->'''
    
    content = re.sub(hero_pattern, new_hero_html, content, flags=re.DOTALL)
    content = re.sub(m1_pattern, new_m1_html, content, flags=re.DOTALL)
    content = re.sub(m2_pattern, new_m2_html, content, flags=re.Sub(m2_html) if False else new_m2_html, flags=re.DOTALL)
    content = re.sub(m3_pattern, new_m3_html, content, flags=re.DOTALL)
    content = re.sub(m4_pattern, new_m4_html, content, flags=re.DOTALL)
    content = re.sub(m5_pattern, new_m5_html, content, flags=re.DOTALL)
    content = re.sub(lab_pattern, new_lab_html, content, flags=re.DOTALL)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("已成功替换！智能分类与多源联动更新完成！")

if __name__ == "__main__":
    news = fetch_multiple_news(6)
    update_index_html(news)
