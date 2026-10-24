import os
import re
import random
import urllib.request
import xml.etree.ElementTree as ET

# 订阅的权威媒体源列表
RSS_FEEDS = [
    {
        "source": "BoF 时尚商业",
        "url": "https://www.businessoffashion.com/feed",
        "tag": "BoF 极速直达 ↗"
    },
    {
        "source": "SocialBeta 营销案例",
        "url": "https://socialbeta.com/feed",
        "tag": "SocialBeta ↗"
    }
]

# 随机美学图片库 (保证图片每天也不同)
CURATED_IMAGES = [
    "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1508296695146-257a814070b4?auto=format&fit=crop&w=800&q=80"
]

def fetch_multiple_news(limit=6):
    """批量抓取多条最新的行业新闻"""
    news_list = []
    for feed in RSS_FEEDS:
        try:
            req = urllib.request.Request(feed["url"], headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                
                for item in root.findall('.//item')[:4]:
                    title = item.find('title').text if item.find('title') is not None else ""
                    link = item.find('link').text if item.find('link') is not None else ""
                    desc = item.find('description').text if item.find('description') is not None else ""
                    
                    clean_desc = re.sub('<[^<]+?>', '', desc)[:120].strip() + "..."
                    
                    news_list.append({
                        "title": title.strip(),
                        "link": link.strip(),
                        "desc": clean_desc,
                        "source": feed["source"],
                        "tag": feed["tag"],
                        "image": random.choice(CURATED_IMAGES)
                    })
        except Exception as e:
            print(f"抓取 {feed['source']} 失败: {e}")
            continue
            
    # 备用池（带有随机洗牌机制，保证备用内容也不重复）
    fallback = [
        {"title": "全球奢侈品集团加码高定美妆与独立香氛赛道", "link": "https://www.businessoffashion.com/", "desc": "最新行业观察：各大奢侈品巨头持续通过收购高定香氛与独立护肤品牌扩大接触点...", "source": "BoF 时尚商业", "tag": "BoF ↗", "image": CURATED_IMAGES[0]},
        {"title": "快闪店设计中的嗅觉符号学与沉浸空间叙事", "link": "https://socialbeta.com/", "desc": "探讨线下零售如何通过独特的空间陈列与气味记忆延长顾客驻留时间...", "source": "SocialBeta", "tag": "SocialBeta ↗", "image": CURATED_IMAGES[1]},
        {"title": "解构主义美学在当代品牌视觉中的重构与表达", "link": "https://www.businessoffashion.com/", "desc": "从时装周看老钱风与解构剪裁如何碰撞出全新的年轻消费共鸣...", "source": "BoF 时尚商业", "tag": "BoF ↗", "image": CURATED_IMAGES[2]},
        {"title": "DTC 品牌如何通过深度文本美学构建心智护城河", "link": "https://socialbeta.com/", "desc": "摆脱价格战泥潭，探讨高客单品牌如何利用叙事美学提升复购率...", "source": "SocialBeta", "tag": "SocialBeta ↗", "image": CURATED_IMAGES[3]},
        {"title": "新奢品牌如何平衡数字营销与专柜尊享体验", "link": "https://www.businessoffashion.com/", "desc": "后流量时代，如何利用私域高定服务锁住顶尖 VIC 客户群...", "source": "BoF 时尚商业", "tag": "BoF ↗", "image": CURATED_IMAGES[4]},
        {"title": "快消品牌的极简包装视觉升级策略与溢价推演", "link": "https://socialbeta.com/", "desc": "字体间距微调与包材留白如何提升产品在货架上的视觉占有率...", "source": "SocialBeta", "tag": "SocialBeta ↗", "image": CURATED_IMAGES[5]}
    ]
    
    random.shuffle(fallback)
    while len(news_list) < limit:
        news_list.extend(fallback)
        
    return news_list[:limit]

def update_index_html(news_list):
    """将抓取的多条新闻动态注入到 index.html 各个模块的锚点中"""
    html_path = "index.html"
    if not os.path.exists(html_path):
        print("未找到 index.html 文件！")
        return

    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. 动态更新 Module 01 灵感视觉卡片
    m1_pattern = r'(<!-- MODULE-01-START -->)(.*?)(<!-- MODULE-01-END -->)'
    new_m1_html = f'''<!-- MODULE-01-START -->
      <div onclick="openAutoModal('{news_list[0]['title']}', '{news_list[0]['desc']}', '{news_list[0]['link']}', '{news_list[0]['source']}')" class="content-card filter-item luxury gallery-card bg-brand-card p-4 border border-brand-border cursor-pointer group">
        <div class="img-zoom-container relative h-80 mb-4 bg-gray-100 overflow-hidden">
          <img src="{news_list[0]['image']}" alt="Gallery" class="w-full h-full object-cover">
          <span class="absolute top-3 left-3 px-2 py-1 bg-white/90 text-[9px] uppercase tracking-widest font-medium">今日热点速递 ↗</span>
        </div>
        <div class="space-y-2">
          <div class="flex justify-between items-center text-[10px] uppercase text-brand-muted tracking-widest">
            <span>{news_list[0]['source']} · 实时速递</span>
            <span>TODAY</span>
          </div>
          <h3 class="font-serif text-xl font-normal group-hover:text-brand-accent transition-colors">
            {news_list[0]['title']}
          </h3>
          <p class="text-xs text-brand-muted font-light line-clamp-2">
            {news_list[0]['desc']}
          </p>
        </div>
      </div>
      <!-- MODULE-01-END -->'''

    # 2. 动态更新 Module 02 营销拆解卡片
    m2_pattern = r'(<!-- MODULE-02-START -->)(.*?)(<!-- MODULE-02-END -->)'
    new_m2_html = f'''<!-- MODULE-02-START -->
      <div onclick="openAutoModal('{news_list[1]['title']}', '{news_list[1]['desc']}', '{news_list[1]['link']}', '{news_list[1]['source']}')" class="content-card filter-item fmcg campaign bg-brand-card p-6 border border-brand-border space-y-4 cursor-pointer hover:border-brand-dark transition-colors">
        <div class="flex justify-between items-center text-xs uppercase tracking-widest">
          <span class="text-brand-accent font-semibold">今日营销动态拆解</span>
          <span class="text-brand-muted">{news_list[1]['source']}</span>
        </div>
        <h3 class="font-serif text-2xl font-normal">
          {news_list[1]['title']}
        </h3>
        <p class="text-xs text-brand-muted font-light leading-relaxed">
          {news_list[1]['desc']}
        </p>
        <div class="pt-2 flex items-center justify-between text-xs border-t border-brand-border/40">
          <span class="font-mono text-[11px] text-brand-dark">AI 策略洞察</span>
          <span class="hover:text-brand-accent uppercase tracking-widest text-[10px] font-semibold">点击阅读原文与深度分析 ↗</span>
        </div>
      </div>
      <!-- MODULE-02-END -->'''

    # 3. 动态更新 Module 03 秀场趋势卡片
    m3_pattern = r'(<!-- MODULE-03-START -->)(.*?)(<!-- MODULE-03-END -->)'
    new_m3_html = f'''<!-- MODULE-03-START -->
      <div onclick="openAutoModal('{news_list[2]['title']}', '{news_list[2]['desc']}', '{news_list[2]['link']}', '{news_list[2]['source']}')" class="content-card filter-item runway luxury bg-brand-card p-4 border border-brand-border flex gap-4 items-center cursor-pointer group">
        <div class="w-24 h-24 flex-shrink-0 img-zoom-container overflow-hidden">
          <img src="{news_list[2]['image']}" alt="Runway" class="w-full h-full object-cover">
        </div>
        <div class="space-y-1">
          <span class="text-[9px] uppercase tracking-widest text-brand-accent font-semibold">{news_list[2]['source']} 趋势 ↗</span>
          <h4 class="font-serif text-lg leading-tight group-hover:text-brand-accent transition-colors line-clamp-1">
            {news_list[2]['title']}
          </h4>
          <p class="text-[11px] text-brand-muted font-light line-clamp-1">{news_list[2]['desc']}</p>
        </div>
      </div>
      <!-- MODULE-03-END -->'''

    # 4. 动态更新 Module 04 趋势研判卡片
    m4_pattern = r'(<!-- MODULE-04-START -->)(.*?)(<!-- MODULE-04-END -->)'
    new_m4_html = f'''<!-- MODULE-04-START -->
      <div onclick="openAutoModal('{news_list[3]['title']}', '{news_list[3]['desc']}', '{news_list[3]['link']}', '{news_list[3]['source']}')" class="content-card filter-item luxury bg-brand-card p-6 border border-brand-border space-y-4 cursor-pointer hover:border-brand-dark transition-colors">
        <div class="flex justify-between items-center text-[10px] uppercase tracking-widest text-brand-muted">
          <span>{news_list[3]['source']} · 行业报告精读</span>
          <span>TODAY</span>
        </div>
        <h3 class="font-serif text-xl font-normal">
          {news_list[3]['title']}
        </h3>
        <p class="text-xs text-brand-muted font-light leading-relaxed line-clamp-3">
          {news_list[3]['desc']}
        </p>
        <span class="text-xs uppercase tracking-widest font-semibold text-brand-dark inline-block text-left">
          点击查看 AI 洞察摘要与原文 ↗
        </span>
      </div>
      <!-- MODULE-04-END -->'''

    # 5. 动态更新 Module 05 每日灵感卡片
    m5_pattern = r'(<!-- AUTO-UPDATE-START -->)(.*?)(<!-- AUTO-UPDATE-END -->)'
    new_m5_html = f'''<!-- AUTO-UPDATE-START -->
      <div onclick="openAutoModal('{news_list[4]['title']}', '{news_list[4]['desc']}', '{news_list[4]['link']}', '{news_list[4]['source']}')" class="block polaroid-card bg-white p-4 border border-brand-border space-y-3 shadow-sm cursor-pointer group">
        <div class="h-48 bg-gray-100 overflow-hidden relative">
          <img src="{news_list[4]['image']}" alt="Spark" class="w-full h-full object-cover">
          <span class="absolute bottom-2 right-2 bg-black/70 text-white text-[9px] px-2 py-0.5 uppercase">TODAY AUTO</span>
        </div>
        <div class="space-y-1">
          <span class="text-[9px] font-mono text-brand-accent uppercase">{news_list[4]['source']} ↗</span>
          <p class="text-xs text-brand-dark font-medium line-clamp-2">“{news_list[4]['title']}”</p>
        </div>
        <div class="text-[10px] text-brand-muted border-t border-brand-border pt-2 group-hover:text-brand-accent">
          点击阅读详细策略摘要 ↗
        </div>
      </div>
      <!-- AUTO-UPDATE-END -->'''

    # 6. 动态更新 对照实验室上方速递
    lab_pattern = r'(<!-- LAB-UPDATE-START -->)(.*?)(<!-- LAB-UPDATE-END -->)'
    new_lab_html = f'''<!-- LAB-UPDATE-START -->
    <div onclick="openAutoModal('{news_list[5]['title']}', '{news_list[5]['desc']}', '{news_list[5]['link']}', '{news_list[5]['source']}')" class="mb-8 p-6 bg-white border border-brand-accent shadow-sm cursor-pointer hover:shadow-md transition-shadow">
      <div class="flex items-center justify-between mb-3">
        <span class="text-[10px] font-mono uppercase tracking-widest bg-brand-accent/20 text-brand-dark px-3 py-1 font-semibold">🔥 今日实时自动对标速递 ({news_list[5]['source']})</span>
        <span class="text-xs text-brand-accent font-mono">点击查看详情 ↗</span>
      </div>
      <h3 class="text-lg font-serif font-normal mb-2 text-brand-dark">“{news_list[5]['title']}”</h3>
      <p class="text-gray-600 text-xs leading-relaxed font-light">{news_list[5]['desc']}</p>
    </div>
    <!-- LAB-UPDATE-END -->'''

    # 执行替换
    content = re.sub(m1_pattern, new_m1_html, content, flags=re.DOTALL)
    content = re.sub(m2_pattern, new_m2_html, content, flags=re.DOTALL)
    content = re.sub(m3_pattern, new_m3_html, content, flags=re.DOTALL)
    content = re.sub(m4_pattern, new_m4_html, content, flags=re.DOTALL)
    content = re.sub(m5_pattern, new_m5_html, content, flags=re.DOTALL)
    content = re.sub(lab_pattern, new_lab_html, content, flags=re.DOTALL)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("全站各模块内容与动态图片已成功更新！")

if __name__ == "__main__":
    news = fetch_multiple_news(6)
    update_index_html(news)
