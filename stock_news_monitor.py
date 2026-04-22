import streamlit as st
import feedparser
import time
import re
from datetime import datetime, timezone
from collections import Counter
import html

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="股票新聞監控",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .news-card {
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
    background: #ffffff;
  }
  .badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    margin-right: 6px;
  }
  .bull  { background: #d4edda; color: #155724; }
  .bear  { background: #f8d7da; color: #721c24; }
  .neu   { background: #e2e3e5; color: #383d41; }
  .high  { background: #fff3cd; color: #856404; }
  .med   { background: #d1ecf1; color: #0c5460; }
  .low   { background: #f1f1f1; color: #6c757d; }
  .ticker-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 5px;
    font-size: 12px;
    font-weight: 700;
    background: #e8f4fd;
    color: #1565c0;
    margin-right: 6px;
  }
  .news-title { font-size: 15px; font-weight: 600; margin: 6px 0 4px; }
  .news-meta  { font-size: 12px; color: #888; }
  .metric-container { text-align: center; padding: 10px; }
  .stProgress > div > div > div > div { background-color: #1D9E75; }
</style>
""", unsafe_allow_html=True)

# ── Sentiment keywords ────────────────────────────────────────────────────────
BULLISH_WORDS = [
    "beat", "beats", "surge", "surges", "rally", "rallies", "jump", "jumps",
    "soar", "soars", "gain", "gains", "growth", "grows", "record", "upgrade",
    "upbeat", "positive", "profit", "profits", "strong", "outperform",
    "buy", "bullish", "milestone", "breakthrough", "win", "wins",
]
BEARISH_WORDS = [
    "miss", "misses", "fall", "falls", "drop", "drops", "decline", "declines",
    "cut", "cuts", "loss", "losses", "downgrade", "warning", "concern",
    "weak", "bearish", "lawsuit", "probe", "investigation", "fine", "layoff",
    "layoffs", "recall", "fraud", "fail", "fails",
]
HIGH_IMPACT_WORDS = [
    "earnings", "revenue", "guidance", "merger", "acquisition", "sec",
    "ceo", "bankruptcy", "ipo", "split", "buyback", "dividend", "federal",
    "fed", "rate", "antitrust", "investigation", "recall",
]

def analyze_sentiment(text: str):
    text_lower = text.lower()
    bull_count = sum(1 for w in BULLISH_WORDS if w in text_lower)
    bear_count = sum(1 for w in BEARISH_WORDS if w in text_lower)
    impact_count = sum(1 for w in HIGH_IMPACT_WORDS if w in text_lower)

    if bull_count > bear_count:
        sentiment, sent_class = "看漲 🟢", "bull"
    elif bear_count > bull_count:
        sentiment, sent_class = "看跌 🔴", "bear"
    else:
        sentiment, sent_class = "中性 ⚪", "neu"

    if impact_count >= 2:
        impact, imp_class = "高影響", "high"
    elif impact_count == 1:
        impact, imp_class = "中影響", "med"
    else:
        impact, imp_class = "低影響", "low"

    return sentiment, sent_class, impact, imp_class

def time_ago(published_parsed):
    try:
        pub = datetime(*published_parsed[:6], tzinfo=timezone.utc)
        diff = datetime.now(timezone.utc) - pub
        minutes = int(diff.total_seconds() / 60)
        if minutes < 1:
            return "剛剛"
        elif minutes < 60:
            return f"{minutes} 分鐘前"
        elif minutes < 1440:
            return f"{minutes // 60} 小時前"
        else:
            return f"{minutes // 1440} 天前"
    except Exception:
        return ""

# ── RSS feeds (no API key needed) ────────────────────────────────────────────
RSS_FEEDS = {
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
    "Yahoo Finance Markets": "https://finance.yahoo.com/rss/topstories",
    "Seeking Alpha": "https://seekingalpha.com/market_currents.xml",
    "Investopedia": "https://www.investopedia.com/feedbuilder/feed/getfeed/?feedName=rss_headline",
    "CNBC Top News": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
    "MarketWatch": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
}

@st.cache_data(ttl=60)
def fetch_news(tickers: list[str], max_per_feed: int = 30):
    """Fetch RSS feeds and filter by ticker symbols."""
    all_articles = []
    tickers_upper = [t.upper() for t in tickers]

    for source_name, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_per_feed]:
                title = html.unescape(entry.get("title", ""))
                summary = html.unescape(entry.get("summary", ""))
                full_text = (title + " " + summary).upper()

                matched = [t for t in tickers_upper if t in full_text]
                if not matched:
                    continue

                link = entry.get("link", "#")
                pub = entry.get("published_parsed", None)
                time_str = time_ago(pub) if pub else ""

                sentiment, sent_class, impact, imp_class = analyze_sentiment(title + " " + summary)

                all_articles.append({
                    "tickers": matched,
                    "title": title,
                    "summary": summary[:200] + ("..." if len(summary) > 200 else ""),
                    "link": link,
                    "source": source_name,
                    "time": time_str,
                    "pub": pub,
                    "sentiment": sentiment,
                    "sent_class": sent_class,
                    "impact": impact,
                    "imp_class": imp_class,
                })
        except Exception:
            continue

    # Sort by publication time (newest first)
    all_articles.sort(key=lambda x: x["pub"] or (2000,), reverse=True)
    # Deduplicate by title
    seen = set()
    unique = []
    for a in all_articles:
        key = a["title"][:60]
        if key not in seen:
            seen.add(key)
            unique.append(a)
    return unique

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ 設定")

    st.subheader("📌 監控股票")
    default_tickers = "TSLA, AAPL, AMZN, NVDA, MSFT"
    ticker_input = st.text_area(
        "輸入股票代碼（逗號分隔）",
        value=default_tickers,
        height=80,
        help="例：TSLA, AAPL, AMZN, GOOGL, META"
    )
    tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

    st.subheader("🕐 更新頻率")
    interval = st.slider(
        "每幾分鐘更新一次",
        min_value=1, max_value=60, value=5, step=1
    )
    st.caption(f"下次更新：{interval} 分鐘後")

    st.subheader("🔍 篩選條件")
    sentiment_filter = st.multiselect(
        "情緒篩選",
        ["看漲 🟢", "看跌 🔴", "中性 ⚪"],
        default=["看漲 🟢", "看跌 🔴", "中性 ⚪"],
    )
    impact_filter = st.multiselect(
        "影響程度篩選",
        ["高影響", "中影響", "低影響"],
        default=["高影響", "中影響", "低影響"],
    )
    ticker_filter = st.multiselect(
        "只看特定股票",
        options=tickers,
        default=tickers,
    )

    st.subheader("📊 顯示設定")
    max_articles = st.slider("最多顯示幾篇", 10, 100, 30, step=5)
    show_summary = st.toggle("顯示新聞摘要", value=True)

    st.markdown("---")
    manual_refresh = st.button("🔄 立即刷新", use_container_width=True)
    st.caption("資料來源：Yahoo Finance / CNBC / MarketWatch RSS（無需 API）")

# ── Auto-refresh logic ────────────────────────────────────────────────────────
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if manual_refresh or (time.time() - st.session_state.last_refresh > interval * 60):
    st.cache_data.clear()
    st.session_state.last_refresh = time.time()

# ── Main content ──────────────────────────────────────────────────────────────
st.title("📈 股票新聞監控儀表板")
st.caption("新聞是股價波動的主要驅動力，本工具幫你即時掌握重要資訊")

# Countdown display
elapsed = time.time() - st.session_state.last_refresh
remaining = max(0, interval * 60 - elapsed)
progress_val = 1.0 - (remaining / (interval * 60))
col_prog, col_time = st.columns([4, 1])
with col_prog:
    st.progress(progress_val)
with col_time:
    st.caption(f"⏱ {int(remaining // 60)}:{int(remaining % 60):02d} 後刷新")

# Fetch news
with st.spinner("載入最新新聞..."):
    articles = fetch_news(tickers)

# Apply filters
filtered = [
    a for a in articles
    if a["sentiment"] in sentiment_filter
    and a["impact"] in impact_filter
    and any(t in ticker_filter for t in a["tickers"])
]

# ── Metrics ───────────────────────────────────────────────────────────────────
total = len(filtered)
bull_count = sum(1 for a in filtered if a["sent_class"] == "bull")
bear_count = sum(1 for a in filtered if a["sent_class"] == "bear")
high_count = sum(1 for a in filtered if a["imp_class"] == "high")

m1, m2, m3, m4 = st.columns(4)
m1.metric("📰 篩選後新聞", total)
m2.metric("🟢 看漲訊號", bull_count)
m3.metric("🔴 看跌訊號", bear_count)
m4.metric("⚡ 高影響新聞", high_count)

st.markdown("---")

# ── Per-ticker tabs ───────────────────────────────────────────────────────────
if ticker_filter:
    tab_labels = ["🌐 全部"] + ticker_filter
    tabs = st.tabs(tab_labels)

    def render_articles(articles_to_show):
        if not articles_to_show:
            st.info("目前沒有符合條件的新聞")
            return
        for a in articles_to_show[:max_articles]:
            ticker_html = "".join(f'<span class="ticker-badge">{t}</span>' for t in a["tickers"])
            sent_html   = f'<span class="badge {a["sent_class"]}">{a["sentiment"]}</span>'
            imp_html    = f'<span class="badge {a["imp_class"]}">{a["impact"]}</span>'
            summary_html = f'<div style="font-size:13px;color:#555;margin-top:4px;">{a["summary"]}</div>' if show_summary else ""
            card = f"""
            <div class="news-card">
              <div>{ticker_html}{sent_html}{imp_html}</div>
              <div class="news-title"><a href="{a['link']}" target="_blank" style="text-decoration:none;color:inherit;">{a['title']}</a></div>
              {summary_html}
              <div class="news-meta">{a['source']} · {a['time']}</div>
            </div>"""
            st.markdown(card, unsafe_allow_html=True)

    with tabs[0]:
        render_articles(filtered)

    for i, ticker in enumerate(ticker_filter):
        with tabs[i + 1]:
            ticker_articles = [a for a in filtered if ticker in a["tickers"]]
            st.caption(f"共 {len(ticker_articles)} 篇關於 {ticker} 的新聞")
            render_articles(ticker_articles)

# ── Sentiment summary chart ───────────────────────────────────────────────────
if filtered:
    st.markdown("---")
    st.subheader("📊 各股票情緒分佈")

    import pandas as pd

    rows = []
    for ticker in ticker_filter:
        ta = [a for a in filtered if ticker in a["tickers"]]
        rows.append({
            "股票": ticker,
            "看漲": sum(1 for a in ta if a["sent_class"] == "bull"),
            "中性": sum(1 for a in ta if a["sent_class"] == "neu"),
            "看跌": sum(1 for a in ta if a["sent_class"] == "bear"),
        })

    df = pd.DataFrame(rows).set_index("股票")
    st.bar_chart(df, color=["#1D9E75", "#888780", "#D85A30"])

# ── Auto-rerun ────────────────────────────────────────────────────────────────
time.sleep(1)
st.rerun()
