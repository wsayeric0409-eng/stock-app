import yfinance as yf
import pandas as pd
import streamlit as st

st.set_page_config(page_title="我的股票戰情室", layout="wide", page_icon="📊")

# ── 我的持股（含成本均價）──────────────────────────
MY_HOLDINGS = {
    "2383.TW": {"名稱": "台光電",   "成本": 2445.97, "股數": 120},
    "6515.TW": {"名稱": "穎崴",     "成本": 6104.97, "股數": 75},
    "6274.TW": {"名稱": "台燿",     "成本": 1311.87, "股數": 200},
    "2408.TW": {"名稱": "南亞科",   "成本": 287.41,  "股數": 1000},
    "2303.TW": {"名稱": "聯電",     "成本": 0,       "股數": 0},   # 補成本
    "3037.TW": {"名稱": "欣興",     "成本": 0,       "股數": 0},
    "2330.TW": {"名稱": "台積電",   "成本": 2328.31, "股數": 100},
    "3017.TW": {"名稱": "奇鋐",     "成本": 2307.78, "股數": 200},
    "2369.TW": {"名稱": "嘉澤",     "成本": 1355.82, "股數": 74},
    "4958.TW": {"名稱": "臻鼎-KY", "成本": 381.54,  "股數": 1400},
    "6500.TW": {"名稱": "聯茂",     "成本": 263.37,  "股數": 1000},
    "2344.TW": {"名稱": "華邦電",   "成本": 0,       "股數": 0},
    "2317.TW": {"名稱": "鴻海",     "成本": 0,       "股數": 0},
    "2454.TW": {"名稱": "聯發科",   "成本": 3474.94, "股數": 100},
    "3515.TW": {"名稱": "國巨",     "成本": 327.97,  "股數": 1000},
    "2337.TW": {"名稱": "南電",     "成本": 581.43,  "股數": 500},
}

# ── 自選觀察股 ──────────────────────────────────────
WATCHLIST = {
    "AI伺服器": {
        "台股": [("2382.TW","廣達"),("3231.TW","緯創"),("3491.TW","緯穎"),("2356.TW","英業達")],
        "美股": [("NVDA","NVIDIA"),("SMCI","Super Micro"),("DELL","Dell")]
    },
    "散熱": {
        "台股": [("3017.TW","奇鋐"),("3324.TW","雙鴻"),("3653.TW","健策")],
        "美股": [("VRT","Vertiv")]
    },
    "PCB / CCL": {
        "台股": [("2383.TW","台光電"),("6274.TW","台燿"),("4958.TW","臻鼎"),("3037.TW","欣興"),("6500.TW","聯茂")],
        "美股": []
    },
    "記憶體": {
        "台股": [("2408.TW","南亞科"),("2344.TW","華邦電")],
        "美股": [("MU","Micron")]
    },
    "IC設計": {
        "台股": [("2454.TW","聯發科"),("3034.TW","聯詠"),("3515.TW","國巨")],
        "美股": [("AVGO","Broadcom"),("MRVL","Marvell")]
    },
    "測試介面": {
        "台股": [("6515.TW","穎崴"),("6223.TW","旺矽"),("6510.TW","精測")],
        "美股": [("TER","Teradyne")]
    },
}

# ── 抓股價 ──────────────────────────────────────────
@st.cache_data(ttl=1800)
def fetch(symbol, period="3mo"):
    try:
        df = yf.download(symbol, period=period, progress=False, auto_adjust=False)
        if df.empty:
            return None
        df = df.reset_index()
        df["MA5"]  = df["Close"].rolling(5).mean()
        df["MA10"] = df["Close"].rolling(10).mean()
        df["MA20"] = df["Close"].rolling(20).mean()
        df["VOL_MA5"] = df["Volume"].rolling(5).mean()
        return df
    except:
        return None

def last_price(df):
    cols = [c for c in ["MA5","MA10","MA20"] if c in df.columns]
    row = df.dropna(subset=cols).iloc[-1]
    close = float(row["Close"].iloc[0] if hasattr(row["Close"], "iloc") else row["Close"])
    ma5   = float(row["MA5"].iloc[0]   if hasattr(row["MA5"],   "iloc") else row["MA5"])
    ma10  = float(row["MA10"].iloc[0]  if hasattr(row["MA10"],  "iloc") else row["MA10"])
    ma20  = float(row["MA20"].iloc[0]  if hasattr(row["MA20"],  "iloc") else row["MA20"])
    vol   = float(row["Volume"].iloc[0]    if hasattr(row["Volume"],    "iloc") else row["Volume"])
    vol5  = float(row["VOL_MA5"].iloc[0]   if hasattr(row["VOL_MA5"],   "iloc") else row["VOL_MA5"])
    return close, ma5, ma10, ma20, vol, vol5

def signal(close, ma5, ma10, ma20, vol, vol_ma5):
    a5, a10, a20 = close>ma5, close>ma10, close>ma20
    vol_up = vol > vol_ma5*1.2 if vol_ma5>0 else False
    if a5 and a10 and a20 and vol_up: return "🟢 強勢追蹤", "右側突破，量價配合"
    if a10 and a20:                   return "🟡 波段續抱", "中期偏多，等回檔"
    if close>ma20 and not a5:         return "🟠 回測觀察", "月線上，短線轉弱"
    if not a20:                       return "🔴 弱勢暫避", "跌破月線，保守"
    return "⚪ 震盪不明", "方向不清，不重倉"

# ═══════════════════════════════════════════════════
# 頁面主體
# ═══════════════════════════════════════════════════
st.title("📊 我的股票戰情室")

tab1, tab2 = st.tabs(["💼 我的持股", "🔍 產業觀察"])

# ── TAB 1：我的持股 ──────────────────────────────────
with tab1:
    st.subheader("持股損益總覽")
    rows = []
    for sym, info in MY_HOLDINGS.items():
        if info["股數"] == 0:
            continue
        df = fetch(sym)
        if df is None or "MA5" not in df.columns or len(df.dropna(subset=["MA5"])) < 5:
            continue
        close, ma5, ma10, ma20, vol, vol_ma5 = last_price(df)
        cost = info["成本"]
        shares = info["股數"]
        mkt_val = close * shares
        pnl = (close - cost) * shares
        pnl_pct = (close - cost) / cost * 100 if cost > 0 else 0
        sig, reason = signal(close, ma5, ma10, ma20, vol, vol_ma5)
        rows.append({
            "股票": info["名稱"],
            "代號": sym,
            "現價": round(close, 2),
            "成本": round(cost, 2),
            "損益%": round(pnl_pct, 1),
            "未實損益": int(pnl),
            "市值": int(mkt_val),
            "MA5": round(ma5, 1),
            "MA20": round(ma20, 1),
            "燈號": sig,
            "判斷": reason,
        })

    if rows:
        df_show = pd.DataFrame(rows)
        total_mkt = df_show["市值"].sum()
        total_pnl = df_show["未實損益"].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("總市值", f"{total_mkt:,.0f}")
        c2.metric("未實現損益", f"{total_pnl:+,.0f}")
        c3.metric("持股數", f"{len(rows)} 檔")

        st.dataframe(
            df_show[["股票","現價","成本","損益%","未實損益","MA5","MA20","燈號","判斷"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "損益%": st.column_config.NumberColumn(format="%.1f%%"),
                "未實損益": st.column_config.NumberColumn(format="%+,.0f"),
            }
        )

        st.divider()
        picked = st.selectbox("點選個股看走勢", [f"{r['股票']} ({r['代號']})" for r in rows])
        sym_pick = picked.split("(")[-1].rstrip(")")
        df_chart = fetch(sym_pick)
        if df_chart is not None:
            chart_data = df_chart.set_index("Date")[["Close","MA5","MA10","MA20"]].dropna()
            st.line_chart(chart_data, use_container_width=True)
    else:
        st.warning("抓取股價中，請稍候...")

# ── TAB 2：產業觀察 ──────────────────────────────────
with tab2:
    sector = st.selectbox("產業", list(WATCHLIST.keys()))
    market = st.radio("市場", ["全部","台股","美股"], horizontal=True)

    sec = WATCHLIST[sector]
    if market == "台股":   symbols = sec["台股"]
    elif market == "美股": symbols = sec["美股"]
    else:                  symbols = sec["台股"] + sec["美股"]

    rows2 = []
    for sym, name in symbols:
        df = fetch(sym)
        if df is None or "MA5" not in df.columns or len(df.dropna(subset=["MA5"])) < 5:
            continue
        close, ma5, ma10, ma20, vol, vol_ma5 = last_price(df)
        prev_row = df.dropna(subset=["MA5"]).iloc[-2]["Close"]; prev = float(prev_row.iloc[0] if hasattr(prev_row, 'iloc') else prev_row)
        chg = (close - prev) / prev * 100
        sig, reason = signal(close, ma5, ma10, ma20, vol, vol_ma5)
        rows2.append({
            "股票": name, "代號": sym,
            "現價": round(close,2),
            "漲跌%": round(chg,2),
            "MA5": round(ma5,1), "MA10": round(ma10,1), "MA20": round(ma20,1),
            "燈號": sig, "判斷": reason
        })

    if rows2:
        df2 = pd.DataFrame(rows2)
        st.dataframe(
            df2[["股票","現價","漲跌%","MA5","MA10","MA20","燈號","判斷"]],
            use_container_width=True,
            hide_index=True,
            column_config={"漲跌%": st.column_config.NumberColumn(format="%.2f%%")}
        )
    else:
        st.info("載入中...")
