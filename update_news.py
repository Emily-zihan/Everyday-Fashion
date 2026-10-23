import os
import re
import urllib.request
import xml.etree.ElementTree as ET

# 订阅的权威媒体 RSS 源列表
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

def fetch_latest_news():
    """抓取最新的 1 条行业新闻"""
    for feed in RSS_FEEDS:
        try:
            req = urllib.request.Request(feed["url"], headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                
                # 解析 RSS 频道中的第一篇文章
                item = root.find('.//item')
                if item is not None:
                    title = item.find('title').text if item.find('title') is not None else ""
                    link = item.find('link').text if item.find('link') is not None else ""
                    desc = item.find('description').text if item.find('description') is not None else ""
                    
                    # 清理 description HTML 标签
                    clean_desc = re.sub('<[^<]+?>', '', desc)[:120] + "..."
                    
                    return {
                        "title": title.strip(),
                        "link": link.strip(),
                        "desc": clean_desc,
                        "source": feed["source"],
                        "tag": feed["tag"]
                    }
        except Exception as e:
            print(f"抓取 {feed['source']} 失败: {e}")
            continue
            
    # 如果抓取失败的备用填充数据
    return {
        "title": "全球奢侈品集团加码美妆与香氛赛道",
        "link": "https://www.businessoffashion.com/",
        "desc": "最新行业观察：各大奢侈品巨头持续通过收购高定香氛与独立护肤品牌扩大 Entry-level 接触点...",
        "source": "BoF 时尚商业",
        "tag": "BoF 极速直达 ↗"
    }

def update_index_html(news):
    """自动将抓取的最新资讯写入 index.html 中"""
    html_path = "index.html"
    if not os.path.exists(html_path):
        print("未找到 index.html 文件！")
        return

    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 替换每日灵感/最新资讯卡片的标题与链接
    # 标注匹配点
    pattern = r'(<!-- AUTO-UPDATE-START -->)(.*?)(<!-- AUTO-UPDATE-END -->)'
    
    new_card_html = f'''<!-- AUTO-UPDATE-START -->
      <a href="{news['link']}" target="_blank" class="block polaroid-card bg-white p-4 border border-brand-border space-y-3 shadow-sm">
        <div class="h-48 bg-gray-100 overflow-hidden relative">
          <img src="https://images.unsplash.com/photo-1508296695146-257a814070b4?auto=format&fit=crop&w=500&q=80" alt="Spark Image" class="w-full h-full object-cover">
          <span class="absolute bottom-2 right-2 bg-black/70 text-white text-[9px] px-2 py-0.5 uppercase">TODAY AUTO</span>
        </div>
        <div class="space-y-1">
          <span class="text-[9px] font-mono text-brand-accent uppercase">{news['tag']}</span>
          <p class="text-xs text-brand-dark font-medium line-clamp-2">“{news['title']}”</p>
        </div>
        <div class="text-[10px] text-brand-muted border-t border-brand-border pt-2">
          {news['desc']}
        </div>
      </a>
      <!-- AUTO-UPDATE-END -->'''

    if re.search(pattern, content, flags=re.DOTALL):
        updated_content = re.sub(pattern, new_card_html, content, flags=re.DOTALL)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        print("Successfully updated index.html with latest news!")
    else:
        print("未在 index.html 中找到 <!-- AUTO-UPDATE-START --> 锚点标记。")

if __name__ == "__main__":
    latest_news = fetch_latest_news()
    print("抓取到的最新资讯:", latest_news)
    update_index_html(latest_news)
