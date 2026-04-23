"""
📈 Stock Intelligence Monitor
Free RSS-based stock news monitoring with KOL weighting & 3-tier alert system.
No API key required · Deployable on Streamlit Cloud
"""

import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime, timedelta, timezone
import re
import html as _html
import requests
import hashlib
from streamlit_autorefresh import st_autorefresh

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Stock Intelligence Monitor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# STYLING — Trading terminal aesthetic
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@400;600;800&display=swap');

:root {
    --bg-deep:    #060b12;
    --bg-panel:   #0a1520;
    --bg-card:    #0d1c2e;
    --border:     #1a3a5c;
    --border-dim: #0f2035;
    --text:       #c8daea;
    --text-dim:   #5b7a96;
    --accent:     #00e5ff;
    --green:      #00e676;
    --red:        #ff1744;
    --orange:     #ff9800;
    --yellow:     #ffeb3b;
    --mono:       'JetBrains Mono', monospace;
    --display:    'Syne', sans-serif;
}

/* Global */
.stApp { background: var(--bg-deep) !important; color: var(--text) !important; }
.block-container { padding: 1rem 2rem 2rem 2rem !important; max-width: 1400px !important; }
section[data-testid="stSidebar"] { background: var(--bg-panel) !important; border-right: 1px solid var(--border) !important; }
.stMarkdown p { color: var(--text); }

/* Cards */
.card-critical {
    background: linear-gradient(135deg, rgba(120,0,0,0.85) 0%, rgba(180,0,0,0.7) 100%);
    border: 1.5px solid var(--red);
    border-left: 5px solid var(--red);
    border-radius: 10px;
    padding: 14px 18px;
    margin: 8px 0;
    font-family: var(--mono);
    animation: pulse-critical 2.5s ease-in-out infinite;
    position: relative;
}
@keyframes pulse-critical {
    0%,100% { box-shadow: 0 0 12px rgba(255,23,68,0.35); }
    50%      { box-shadow: 0 0 28px rgba(255,23,68,0.75); }
}

.card-high {
    background: linear-gradient(135deg, rgba(80,40,0,0.9) 0%, rgba(140,70,0,0.75) 100%);
    border: 1px solid var(--orange);
    border-left: 4px solid var(--orange);
    border-radius: 10px;
    padding: 13px 17px;
    margin: 6px 0;
    font-family: var(--mono);
}

.card-normal {
    background: var(--bg-card);
    border: 1px solid var(--border-dim);
    border-left: 3px solid var(--green);
    border-radius: 8px;
    padding: 11px 16px;
    margin: 5px 0;
    font-family: var(--mono);
}

.card-title {
    font-family: var(--display);
    font-size: 14.5px;
    font-weight: 600;
    line-height: 1.5;
    margin-bottom: 6px;
    color: #e8f4f8;
}
.card-title a { color: inherit !important; text-decoration: none; }
.card-title a:hover { text-decoration: underline; }

.card-summary {
    font-size: 12px;
    color: rgba(200,218,234,0.75);
    line-height: 1.55;
    margin: 6px 0;
}

.card-meta {
    font-size: 11px;
    color: var(--text-dim);
    margin-top: 7px;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
}
.card-meta a { color: var(--accent); text-decoration: none; }
.card-meta a:hover { text-decoration: underline; }

/* Badges */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    padding: 2px 9px;
    border-radius: 12px;
    font-size: 10.5px;
    font-weight: 700;
    font-family: var(--mono);
    letter-spacing: 0.5px;
    vertical-align: middle;
    margin-right: 5px;
}
.badge-critical { background: var(--red);    color: white; }
.badge-high     { background: var(--orange); color: white; }
.badge-normal   { background: #00875a;       color: white; }

.ticker-chip {
    display: inline-block;
    background: rgba(0,229,255,0.1);
    border: 1px solid rgba(0,229,255,0.35);
    color: var(--accent);
    padding: 1px 8px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 700;
    font-family: var(--mono);
    margin: 0 2px;
    vertical-align: middle;
}

.new-label {
    background: #e91e63;
    color: white;
    padding: 1px 6px;
    border-radius: 8px;
    font-size: 9.5px;
    font-weight: 800;
    letter-spacing: 1px;
    vertical-align: middle;
    margin-left: 4px;
    animation: blink 1.2s step-start infinite;
}
@keyframes blink { 50% { opacity: 0; } }

/* Stats */
.stat-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 20px; }
.stat-box {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 14px;
    text-align: center;
    font-family: var(--mono);
}
.stat-num { font-size: 26px; font-weight: 700; color: var(--accent); line-height: 1; }
.stat-lbl { font-size: 10.5px; color: var(--text-dim); margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }

/* Section headers */
.section-hdr {
    font-family: var(--display);
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--text-dim);
    padding: 14px 0 8px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 12px;
}

/* Page title */
.page-title {
    font-family: var(--display);
    font-size: 26px;
    font-weight: 800;
    color: var(--accent);
    margin-bottom: 2px;
    letter-spacing: -0.5px;
}
.page-sub {
    font-family: var(--mono);
    font-size: 12px;
    color: var(--text-dim);
    margin-bottom: 16px;
}

/* Fear & Greed gauge */
.fg-box {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 14px;
    text-align: center;
    font-family: var(--mono);
}
.fg-score { font-size: 30px; font-weight: 700; line-height: 1; }
.fg-lbl { font-size: 10px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1px; margin-top: 3px; }
.fg-rating { font-size: 11px; margin-top: 3px; font-weight: 600; }

/* Score meter */
.score-bar-wrap { display: flex; align-items: center; gap: 6px; }
.score-bar { height: 4px; border-radius: 2px; flex-grow: 1; max-width: 60px; }

/* Keyword chips */
.kw-chip {
    display: inline-block;
    background: rgba(255,235,59,0.12);
    border: 1px solid rgba(255,235,59,0.3);
    color: #ffe57f;
    padding: 0 6px;
    border-radius: 8px;
    font-size: 10px;
    margin: 0 2px;
    vertical-align: middle;
}

/* Sidebar refinements */
.sidebar-section {
    font-family: var(--display);
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--text-dim);
    margin: 14px 0 6px 0;
    padding-bottom: 4px;
    border-bottom: 1px solid var(--border-dim);
}

.stCheckbox label { font-family: var(--mono) !important; font-size: 13px !important; }
.stTextArea textarea { font-family: var(--mono) !important; font-size: 13px !important; background: var(--bg-card) !important; border-color: var(--border) !important; color: var(--text) !important; }
.stSlider { font-family: var(--mono) !important; }

/* Status dot */
.live-dot {
    display: inline-block;
    width: 8px; height: 8px;
    background: var(--green);
    border-radius: 50%;
    margin-right: 6px;
    animation: blink 1.5s ease-in-out infinite;
    vertical-align: middle;
}

/* No results */
.no-results {
    text-align: center;
    padding: 40px;
    color: var(--text-dim);
    font-family: var(--mono);
    font-size: 13px;
    border: 1px dashed var(--border);
    border-radius: 10px;
}

/* Scrollable news section */
.news-scroll { max-height: 800px; overflow-y: auto; padding-right: 4px; }
.news-scroll::-webkit-scrollbar { width: 4px; }
.news-scroll::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

/* Source tag */
.src-tag { display: inline-flex; align-items: center; gap: 3px; font-size: 11px; color: var(--text-dim); }

/* Weight label */
.weight-x { color: var(--yellow); font-weight: 700; font-size: 10px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

TICKER_CIK = {
    "TSLA": "1318605", "AAPL": "320193", "AMZN": "1018724",
    "GOOGL": "1652044", "GOOG": "1652044", "MSFT": "789019",
    "META": "1326801", "NVDA": "1045810", "NFLX": "1065280",
    "AMD": "2488", "BABA": "1577552", "JPM": "19617",
    "GS": "886982", "COIN": "1679273", "GME": "1326380",
    "AMC": "1411579", "PLTR": "1321655", "RIVN": "1874178",
    "LCID": "1836935", "NIO": "1736541", "UBER": "1543151",
    "LYFT": "1759509", "SNAP": "1564408", "HOOD": "1783879",
    "SOFI": "1818874", "BA": "12927", "DIS": "1001039",
    "WMT": "104169", "INTC": "50863", "QCOM": "804328",
    "V": "1403161", "MA": "1141391", "XOM": "34088",
    "CVX": "93410", "PFE": "78003", "JNJ": "200406",
    "MRNA": "1682852", "BNTX": "1776985", "CSCO": "858877",
    "ORCL": "1341439", "CRM": "1108524", "SHOP": "1594805",
    "ROKU": "1428439", "PYPL": "1633917", "SQ": "1512673",
    "ABNB": "1559720", "DASH": "1792789", "RBLX": "1315098",
    "U": "1580560",  # Unity
}

NITTER_INSTANCES = [
    "https://nitter.poast.org/{user}/rss",
    "https://nitter.privacydev.net/{user}/rss",
    "https://nitter.1d4.us/{user}/rss",
    "https://nitter.cz/{user}/rss",
]

# Impact keywords with multipliers
IMPACT_KEYWORDS = {
    # ── Existential threats (highest impact) ──
    "bankruptcy": 4.5, "chapter 11": 4.5, "chapter 7": 4.5, "insolvent": 4.0,
    "delisted": 4.0, "delist": 3.5, "trading halt": 3.5, "halted": 3.0,
    "sec investigation": 4.0, "sec charges": 4.0, "fraud": 4.0,
    "restatement": 3.5, "accounting irregularities": 3.5, "going concern": 3.5,
    # ── M&A ──
    "acquisition": 3.0, "merger": 3.0, "takeover": 3.0, "buyout": 3.0,
    "acquired by": 3.0, "going private": 3.0, "tender offer": 3.0,
    # ── Leadership ──
    "ceo resign": 3.0, "ceo fired": 3.0, "ceo steps down": 3.0,
    "cfo resign": 2.5, "coo resign": 2.5, "board ousted": 3.0,
    # ── Regulatory ──
    "fda approved": 3.0, "fda approval": 3.0, "fda rejected": 3.0,
    "fda denied": 3.0, "fda clearance": 2.5,
    "tariff": 2.5, "sanction": 2.5, "ban": 2.0, "trade war": 2.5,
    "antitrust": 3.0, "doj": 2.5, "ftc": 2.5,
    # ── Earnings & guidance ──
    "earnings beat": 2.5, "beat expectations": 2.5, "guidance raised": 2.5,
    "earnings miss": 2.5, "missed expectations": 2.5, "guidance cut": 2.5,
    "profit warning": 3.0, "revenue warning": 3.0, "guidance lowered": 2.5,
    # ── Corporate actions ──
    "stock split": 2.0, "reverse split": 2.5, "dividend cut": 2.5,
    "dividend increase": 1.8, "buyback": 1.8, "share repurchase": 1.8,
    # ── Analyst ──
    "upgrade": 1.8, "downgrade": 1.8, "price target raised": 1.8,
    "price target cut": 1.8, "buy rating": 1.5, "sell rating": 1.5,
    "outperform": 1.4, "underperform": 1.4, "overweight": 1.4, "underweight": 1.4,
    # ── Controversy / risk ──
    "short seller": 2.5, "short report": 2.5, "recall": 2.0,
    "lawsuit": 1.8, "layoffs": 1.8, "data breach": 2.0,
    "whistleblower": 2.5, "class action": 2.5,
    # ── Positive catalysts ──
    "partnership": 1.5, "deal": 1.4, "contract won": 1.5,
    "record revenue": 2.0, "record earnings": 2.0, "ipo": 1.8,
    # ── General financial ──
    "earnings": 1.4, "revenue": 1.3, "profit": 1.3,
}

USER_AGENT = "Mozilla/5.0 (compatible; StockIntelligenceMonitor/1.0; educational)"

# ─────────────────────────────────────────────────────────────────────────────
# DATA LAYER
# ─────────────────────────────────────────────────────────────────────────────

def build_sources(tickers: list, cfg: dict) -> list:
    """Construct all source configs to fetch based on user settings."""
    sources = []

    # ── Per-ticker sources ──────────────────────────────────────────────────
    for ticker in tickers:
        t = ticker.upper().strip()
        if not t:
            continue

        sources.append(dict(
            name=f"Yahoo Finance · {t}", icon="📰",
            url=f"https://finance.yahoo.com/rss/headline?s={t}",
            weight=2.0, ticker=t, category="financial_media",
        ))
        sources.append(dict(
            name=f"Google News · {t}", icon="🔍",
            url=(f"https://news.google.com/rss/search?q={t}+stock+news"
                 f"&hl=en-US&gl=US&ceid=US:en"),
            weight=1.5, ticker=t, category="news",
        ))
        # SEC EDGAR per-company (use CIK if known, else company name search)
        cik = TICKER_CIK.get(t)
        if cik:
            sources.append(dict(
                name=f"SEC EDGAR 8-K · {t}", icon="⚖️",
                url=(f"https://www.sec.gov/cgi-bin/browse-edgar"
                     f"?action=getcompany&CIK={cik}&type=8-K"
                     f"&dateb=&owner=include&count=10&output=atom"),
                weight=3.0, ticker=t, category="regulatory",
            ))
            sources.append(dict(
                name=f"SEC Form 4 · {t}", icon="🏛️",
                url=(f"https://www.sec.gov/cgi-bin/browse-edgar"
                     f"?action=getcompany&CIK={cik}&type=4"
                     f"&dateb=&owner=include&count=10&output=atom"),
                weight=2.5, ticker=t, category="regulatory",
            ))

    # ── Global KOL sources ──────────────────────────────────────────────────
    if cfg.get("trump"):
        sources.append(dict(
            name="Trump · Truth Social", icon="🇺🇸",
            url="https://truthsocial.com/@realDonaldTrump.rss",
            weight=3.0, ticker=None, category="kol",
        ))
    if cfg.get("musk"):
        sources.append(dict(
            name="Elon Musk · X/Twitter", icon="🚀",
            url=NITTER_INSTANCES[0].format(user="elonmusk"),
            fallbacks=[u.format(user="elonmusk") for u in NITTER_INSTANCES[1:]],
            weight=3.0, ticker=None, category="kol",
        ))
    if cfg.get("cramer"):
        sources.append(dict(
            name="Jim Cramer · X/Twitter", icon="📺",
            url=NITTER_INSTANCES[0].format(user="jimcramer"),
            fallbacks=[u.format(user="jimcramer") for u in NITTER_INSTANCES[1:]],
            weight=1.5, ticker=None, category="kol",
        ))

    # ── Global regulatory ───────────────────────────────────────────────────
    if cfg.get("sec_8k"):
        sources.append(dict(
            name="SEC EDGAR 8-K · All", icon="⚖️",
            url=("https://www.sec.gov/cgi-bin/browse-edgar"
                 "?action=getcurrent&type=8-K&dateb=&owner=include&count=40&output=atom"),
            weight=3.0, ticker=None, category="regulatory",
        ))
    if cfg.get("sec_form4"):
        sources.append(dict(
            name="SEC Form 4 · All Insiders", icon="🏛️",
            url=("https://www.sec.gov/cgi-bin/browse-edgar"
                 "?action=getcurrent&type=4&dateb=&owner=include&count=40&output=atom"),
            weight=2.5, ticker=None, category="regulatory",
        ))

    # ── Financial media ─────────────────────────────────────────────────────
    if cfg.get("marketwatch"):
        sources.append(dict(
            name="MarketWatch", icon="📊",
            url="https://www.marketwatch.com/rss/topstories",
            weight=2.0, ticker=None, category="financial_media",
        ))
    if cfg.get("yahoo_general"):
        sources.append(dict(
            name="Yahoo Finance · Market News", icon="📰",
            url="https://finance.yahoo.com/news/rssindex",
            weight=1.8, ticker=None, category="financial_media",
        ))

    # ── Social / Reddit ─────────────────────────────────────────────────────
    if cfg.get("wsb"):
        sources.append(dict(
            name="Reddit · WallStreetBets", icon="🦍",
            url="https://www.reddit.com/r/wallstreetbets/new/.rss?sort=new",
            weight=0.8, ticker=None, category="social",
        ))
    if cfg.get("r_stocks"):
        sources.append(dict(
            name="Reddit · r/stocks", icon="💬",
            url="https://www.reddit.com/r/stocks/new/.rss?sort=new",
            weight=0.9, ticker=None, category="social",
        ))
    if cfg.get("r_investing"):
        sources.append(dict(
            name="Reddit · r/investing", icon="💰",
            url="https://www.reddit.com/r/investing/new/.rss?sort=new",
            weight=0.9, ticker=None, category="social",
        ))

    return sources


@st.cache_data(ttl=60, show_spinner=False)
def fetch_feed(url: str, name: str) -> list:
    """Fetch an RSS/Atom feed, return list of raw dicts."""
    try:
        feed = feedparser.parse(url, request_headers={"User-Agent": USER_AGENT})
        if not feed.entries:
            return []
        items = []
        for entry in feed.entries[:30]:
            title   = (getattr(entry, "title", "") or "").strip()
            summary = (getattr(entry, "summary", "")
                       or getattr(entry, "description", "") or "").strip()
            summary = re.sub(r"<[^>]*>", " ", summary, flags=re.DOTALL)
            summary = _html.unescape(summary)
            summary = re.sub(r"\s+", " ", summary).strip()[:400]
            link    = (getattr(entry, "link", "") or "").strip() or "#"

            pub = None
            for attr in ("published_parsed", "updated_parsed"):
                t = getattr(entry, attr, None)
                if t:
                    try:
                        pub = datetime(*t[:6], tzinfo=timezone.utc)
                        break
                    except Exception:
                        pass
            if pub is None:
                pub = datetime.now(timezone.utc)

            if title:
                items.append(dict(title=title, summary=summary, link=link, published=pub))
        return items
    except Exception:
        return []


@st.cache_data(ttl=300, show_spinner=False)
def fetch_fear_greed():
    """CNN Fear & Greed Index — free, no auth."""
    try:
        r = requests.get(
            "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
            timeout=6, headers={"User-Agent": USER_AGENT},
        )
        d = r.json()["fear_and_greed"]
        score  = round(d["score"])
        rating = d["rating"].replace("_", " ").title()
        return score, rating
    except Exception:
        return None, None


def score_item(item: dict, tickers: list, source_weight: float,
               per_stock: bool, primary_ticker: str | None) -> dict | None:
    """Score a news item. Returns None if irrelevant (for global sources)."""
    text_low = (item["title"] + " " + item["summary"]).lower()
    tickers_up = [t.upper() for t in tickers]
    tickers_lo = [t.lower() for t in tickers]

    # ── Ticker detection ────────────────────────────────────────────────────
    found_tickers = []
    for tu, tl in zip(tickers_up, tickers_lo):
        if (f" {tl} " in f" {text_low} " or f"${tl}" in text_low
                or f"({tl})" in text_low or f"/{tl}" in text_low
                or re.search(rf'\b{re.escape(tl)}\b', text_low)):
            found_tickers.append(tu)

    # For global (non-per-stock) feeds: discard if no ticker match
    if not per_stock and not found_tickers:
        return None

    # For per-stock: always include, inject primary ticker
    if per_stock and primary_ticker and primary_ticker not in found_tickers:
        found_tickers.insert(0, primary_ticker)

    # ── Scoring ─────────────────────────────────────────────────────────────
    score = source_weight

    # Ticker match bonus
    if found_tickers:
        score *= 2.0

    # Keyword multiplier (highest wins)
    best_kw_mult = 1.0
    matched_kws  = []
    for kw, mult in IMPACT_KEYWORDS.items():
        if kw in text_low:
            matched_kws.append(kw)
            if mult > best_kw_mult:
                best_kw_mult = mult
    score *= best_kw_mult

    # Recency bonus
    now = datetime.now(timezone.utc)
    age = now - item["published"]
    if age < timedelta(minutes=15):
        score *= 2.0
    elif age < timedelta(minutes=30):
        score *= 1.7
    elif age < timedelta(hours=2):
        score *= 1.3
    elif age < timedelta(hours=6):
        score *= 1.1

    # Tier
    if score >= 6.0:
        tier = "critical"
    elif score >= 3.0:
        tier = "high"
    else:
        tier = "normal"

    return {
        **item,
        "score":    round(score, 2),
        "tier":     tier,
        "found_tickers": found_tickers,
        "matched_keywords": matched_kws[:4],
        "uid": hashlib.md5(item["title"].encode()).hexdigest()[:10],
    }


# ─────────────────────────────────────────────────────────────────────────────
# RENDER HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def age_string(pub: datetime) -> str:
    age = datetime.now(timezone.utc) - pub
    if age < timedelta(minutes=1):
        return "just now"
    if age < timedelta(hours=1):
        return f"{int(age.total_seconds() / 60)}m ago"
    if age < timedelta(hours=24):
        return f"{int(age.total_seconds() / 3600)}h ago"
    return pub.strftime("%b %d %H:%M UTC")


def score_bar_color(score: float) -> str:
    if score >= 6:   return "#ff1744"
    if score >= 3:   return "#ff9800"
    return "#00e676"


def render_card(item: dict, is_new: bool, icon: str = "📰"):
    tier        = item["tier"]
    css_class   = f"card-{tier}"
    badge_class = f"badge-{tier}"
    tier_labels = {"critical": "🔴 CRITICAL", "high": "🟡 HIGH", "normal": "🟢 NORMAL"}
    tier_label  = tier_labels[tier]

    tickers_html = "".join(
        f'<span class="ticker-chip">{t}</span>'
        for t in item.get("found_tickers", [])
    )
    kw_html = "".join(
        f'<span class="kw-chip">{kw}</span>'
        for kw in item.get("matched_keywords", [])[:3]
    )
    new_html  = '<span class="new-label">NEW</span>' if is_new else ""
    title_esc = item["title"].replace("<", "&lt;").replace(">", "&gt;")
    summ_esc  = item["summary"].replace("<", "&lt;").replace(">", "&gt;")
    summ_esc  = summ_esc[:220] + ("…" if len(item["summary"]) > 220 else "")

    bar_w   = min(100, int(item["score"] / 12 * 100))
    bar_col = score_bar_color(item["score"])

    st.markdown(f"""
    <div class="{css_class}">
        <div class="card-title">
            <span class="badge {badge_class}">{tier_label}</span>
            {tickers_html}{new_html}
            <a href="{item['link']}" target="_blank">{title_esc}</a>
        </div>
        {"" if not summ_esc else f'<div class="card-summary">{summ_esc}</div>'}
        <div class="card-meta">
            <span class="src-tag">{icon} <b>{item['source']}</b></span>
            <span>⏱ {age_string(item['published'])}</span>
            <span class="score-bar-wrap">
                📊 <b>{item['score']}</b>
                <span class="score-bar" style="background:linear-gradient(90deg,{bar_col} {bar_w}%,rgba(255,255,255,0.08) {bar_w}%)"></span>
            </span>
            {kw_html}
            <a href="{item['link']}" target="_blank">Read →</a>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        '<div style="font-family:\'Syne\',sans-serif;font-size:18px;font-weight:800;'
        'color:#00e5ff;margin-bottom:4px;">⚡ Stock Monitor</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div style="font-size:10px;color:#5b7a96;margin-bottom:16px;">No API key required</div>', unsafe_allow_html=True)
    st.markdown("---")

    # Tickers
    st.markdown('<div class="sidebar-section">📊 Stocks to Monitor</div>', unsafe_allow_html=True)
    ticker_raw = st.text_area(
        "Tickers",
        value="TSLA\nAAPL\nAMZN\nNVDA\nMSFT",
        height=115, label_visibility="collapsed",
        help="One ticker per line or comma-separated",
    )
    tickers = sorted(set(
        t.strip().upper()
        for t in re.split(r"[,\n\s]+", ticker_raw) if t.strip()
    ))
    if tickers:
        chips = " ".join(f"`{t}`" for t in tickers[:12])
        st.caption(f"Watching: {chips}")

    # Refresh
    st.markdown('<div class="sidebar-section">⏱ Auto-Refresh</div>', unsafe_allow_html=True)
    refresh_min = st.select_slider(
        "Interval", options=[1, 2, 3, 5, 10, 15, 30, 60],
        value=5, format_func=lambda x: f"Every {x} min",
        label_visibility="collapsed",
    )

    # Sources
    st.markdown('<div class="sidebar-section">📡 Data Sources</div>', unsafe_allow_html=True)
    st.caption("🎯 KOL — weight ×3")
    c1, c2 = st.columns(2)
    with c1: en_trump  = st.checkbox("🇺🇸 Trump",  value=True)
    with c2: en_musk   = st.checkbox("🚀 Musk",   value=True)
    en_cramer = st.checkbox("📺 Cramer (Nitter)", value=False)

    st.caption("⚖️ Regulatory — weight ×3 / ×2.5")
    c3, c4 = st.columns(2)
    with c3: en_sec_8k    = st.checkbox("SEC 8-K",   value=True)
    with c4: en_sec_form4 = st.checkbox("Form 4",    value=True)

    st.caption("📰 Financial Media — weight ×2")
    c5, c6 = st.columns(2)
    with c5: en_marketwatch   = st.checkbox("MarketWatch", value=True)
    with c6: en_yahoo_general = st.checkbox("Yahoo Mkt",   value=False)

    st.caption("🦍 Social — weight ×0.8–0.9")
    c7, c8, c9 = st.columns(3)
    with c7: en_wsb       = st.checkbox("WSB",      value=True)
    with c8: en_r_stocks  = st.checkbox("r/stocks", value=True)
    with c9: en_r_inv     = st.checkbox("r/invest", value=False)

    # Filters
    st.markdown('<div class="sidebar-section">🔔 Alert Filters</div>', unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)
    with f1: show_crit   = st.checkbox("🔴", value=True, help="Critical")
    with f2: show_high   = st.checkbox("🟡", value=True, help="High")
    with f3: show_normal = st.checkbox("🟢", value=True, help="Normal")

    max_age = st.slider("Max age (hours)", 1, 72, 24)

    # Sort
    st.markdown('<div class="sidebar-section">🗂 Sort</div>', unsafe_allow_html=True)
    sort_opt = st.radio(
        "Sort",
        ["📊 Score (highest)", "🕐 Time (newest)"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    if st.button("🔄 Force Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown(
        '<div style="font-size:10px;color:#3a5a7a;text-align:center;line-height:1.6;">'
        'Sources: Yahoo Finance · Google News<br>'
        'SEC EDGAR · Truth Social · Nitter<br>'
        'Reddit · MarketWatch · CNN F&G<br><br>'
        '⚠️ Not financial advice.</div>',
        unsafe_allow_html=True,
    )

source_cfg = dict(
    trump=en_trump, musk=en_musk, cramer=en_cramer,
    sec_8k=en_sec_8k, sec_form4=en_sec_form4,
    marketwatch=en_marketwatch, yahoo_general=en_yahoo_general,
    wsb=en_wsb, r_stocks=en_r_stocks, r_investing=en_r_inv,
)

# ─────────────────────────────────────────────────────────────────────────────
# AUTO REFRESH
# ─────────────────────────────────────────────────────────────────────────────

_refresh_count = st_autorefresh(interval=refresh_min * 60 * 1000, key="autorefresh_main")

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────

col_title, col_clock, col_fg = st.columns([4, 1.4, 1.4])

with col_title:
    watching_str = " · ".join(tickers[:8]) + (" …" if len(tickers) > 8 else "")
    st.markdown(f"""
    <div class="page-title">
        <span class="live-dot"></span>Stock Intelligence Monitor
    </div>
    <div class="page-sub">
        Watching: {watching_str} &nbsp;·&nbsp; Refresh: every {refresh_min} min
    </div>
    """, unsafe_allow_html=True)

with col_clock:
    now_utc = datetime.now(timezone.utc)
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-num" style="font-size:18px;">{now_utc.strftime('%H:%M:%S')}</div>
        <div class="stat-lbl">UTC · {now_utc.strftime('%b %d %Y')}</div>
    </div>
    """, unsafe_allow_html=True)

with col_fg:
    fg_score, fg_label = fetch_fear_greed()
    if fg_score is not None:
        if fg_score <= 25:   fg_col, fg_emoji = "#ff1744", "😨"
        elif fg_score <= 45: fg_col, fg_emoji = "#ff9800", "😟"
        elif fg_score <= 55: fg_col, fg_emoji = "#ffeb3b", "😐"
        elif fg_score <= 75: fg_col, fg_emoji = "#69f0ae", "😊"
        else:                fg_col, fg_emoji = "#00e676", "🤑"
        st.markdown(f"""
        <div class="fg-box">
            <div class="fg-score" style="color:{fg_col}">{fg_score}</div>
            <div class="fg-rating" style="color:{fg_col}">{fg_emoji} {fg_label}</div>
            <div class="fg-lbl">CNN Fear & Greed</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="fg-box"><div class="fg-lbl">Fear & Greed<br>unavailable</div></div>', unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# FETCH ALL FEEDS
# ─────────────────────────────────────────────────────────────────────────────

all_sources = build_sources(tickers, source_cfg)
all_items   = []
failed      = []

fetch_bar = st.progress(0, text="⚡ Fetching intelligence feeds…")

for i, src in enumerate(all_sources):
    fetch_bar.progress((i + 1) / max(len(all_sources), 1),
                       text=f"⚡ {src['name']}…")

    raw = fetch_feed(src["url"], src["name"])

    # Try fallbacks (Nitter etc.)
    if not raw:
        for fb_url in src.get("fallbacks", []):
            raw = fetch_feed(fb_url, src["name"])
            if raw:
                break

    if not raw:
        failed.append(src["name"])
        continue

    per_stock = src.get("ticker") is not None

    # Annotate raw items with source metadata
    for item in raw:
        item["source"] = src["name"]
        item["icon"]   = src.get("icon", "📰")

    # Score and filter
    for item in raw:
        scored = score_item(
            item, tickers,
            source_weight  = src["weight"],
            per_stock      = per_stock,
            primary_ticker = src.get("ticker"),
        )
        if scored:
            all_items.append(scored)

fetch_bar.empty()

# ── Deduplicate by title ───────────────────────────────────────────────────
seen_uids: set = set()
unique: list   = []
for item in all_items:
    if item["uid"] not in seen_uids:
        seen_uids.add(item["uid"])
        unique.append(item)

# ── Age filter ─────────────────────────────────────────────────────────────
cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age)
unique = [i for i in unique if i["published"] >= cutoff]

# ── Tier filter ────────────────────────────────────────────────────────────
allowed_tiers = set()
if show_crit:   allowed_tiers.add("critical")
if show_high:   allowed_tiers.add("high")
if show_normal: allowed_tiers.add("normal")
unique = [i for i in unique if i["tier"] in allowed_tiers]

# ── Sort ───────────────────────────────────────────────────────────────────
if "Score" in sort_opt:
    unique.sort(key=lambda x: -x["score"])
else:
    unique.sort(key=lambda x: -x["published"].timestamp())

# ── New-item tracking ──────────────────────────────────────────────────────
if "seen_ids" not in st.session_state:
    st.session_state.seen_ids = set()

current_uids = {i["uid"] for i in unique}
new_uids     = current_uids - st.session_state.seen_ids
st.session_state.seen_ids = current_uids

# ── Partition by tier ──────────────────────────────────────────────────────
crits   = [i for i in unique if i["tier"] == "critical"]
highs   = [i for i in unique if i["tier"] == "high"]
normals = [i for i in unique if i["tier"] == "normal"]

# ─────────────────────────────────────────────────────────────────────────────
# STATS ROW
# ─────────────────────────────────────────────────────────────────────────────

s1, s2, s3, s4, s5 = st.columns(5)
for col, (num, lbl, col_override) in zip(
    [s1, s2, s3, s4, s5],
    [
        (len(unique),  "Total Articles",  "#00e5ff"),
        (len(crits),   "🔴 Critical",      "#ff1744"),
        (len(highs),   "🟡 High Priority", "#ff9800"),
        (len(normals), "🟢 Normal",        "#00e676"),
        (len(new_uids),"✨ New This Pass",  "#e91e63"),
    ],
):
    with col:
        st.markdown(
            f'<div class="stat-box">'
            f'<div class="stat-num" style="color:{col_override}">{num}</div>'
            f'<div class="stat-lbl">{lbl}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

if failed:
    st.caption(f"⚠️ Unavailable: {', '.join(failed[:6])}")

st.markdown("---")

# Toast for new critical items
new_crit_count = sum(1 for i in crits if i["uid"] in new_uids)
if new_crit_count > 0:
    st.toast(f"🚨 {new_crit_count} new CRITICAL alert(s)!", icon="🔴")

# ─────────────────────────────────────────────────────────────────────────────
# CRITICAL SECTION
# ─────────────────────────────────────────────────────────────────────────────

if crits:
    st.markdown('<div class="section-hdr">🚨 Critical Alerts</div>', unsafe_allow_html=True)
    for item in crits[:8]:
        render_card(item, is_new=item["uid"] in new_uids, icon=item.get("icon", "📰"))

# ─────────────────────────────────────────────────────────────────────────────
# HIGH PRIORITY SECTION
# ─────────────────────────────────────────────────────────────────────────────

if highs:
    st.markdown(
        f'<div class="section-hdr">⚡ High Priority &nbsp;'
        f'<span style="font-weight:400;color:#5b7a96">({len(highs)} items)</span></div>',
        unsafe_allow_html=True,
    )
    for item in highs[:20]:
        render_card(item, is_new=item["uid"] in new_uids, icon=item.get("icon", "📰"))

# ─────────────────────────────────────────────────────────────────────────────
# NORMAL FEED — collapsible
# ─────────────────────────────────────────────────────────────────────────────

if normals:
    auto_expand = len(crits) + len(highs) == 0
    with st.expander(
        f"📰 General News Feed — {len(normals)} items",
        expanded=auto_expand,
    ):
        for item in normals[:40]:
            render_card(item, is_new=item["uid"] in new_uids, icon=item.get("icon", "📰"))

# ── Empty state ────────────────────────────────────────────────────────────
if not unique:
    st.markdown("""
    <div class="no-results">
        <div style="font-size:32px;margin-bottom:12px;">📭</div>
        <div>No relevant news found for your tickers.</div>
        <div style="margin-top:8px;font-size:11px;color:#3a5a7a;">
            Try adjusting your ticker list, increasing max age, or checking source availability.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("""
<div style="text-align:center;font-family:'JetBrains Mono',monospace;font-size:10.5px;
            color:#2a4a6a;line-height:1.8;padding:8px 0;">
    📈 Stock Intelligence Monitor &nbsp;·&nbsp; Free RSS feeds only &nbsp;·&nbsp; No API key required<br>
    Sources: Yahoo Finance · Google News · SEC EDGAR · Truth Social · Nitter (X mirror) · Reddit · MarketWatch · CNN Fear & Greed<br>
    KOL weighting: Trump/Musk ×3 · Financial media ×2 · Reddit ×0.8–0.9 · Regulatory ×2.5–3.0<br><br>
    ⚠️ For informational purposes only. Not financial advice. Always do your own research.
</div>
""", unsafe_allow_html=True)
