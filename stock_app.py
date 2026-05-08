
import os
from typing import Dict, List, Tuple, Optional

import pandas as pd
import streamlit as st
import yfinance as yf

try:
    import plotly.graph_objects as go
except Exception:
    go = None

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

st.set_page_config(page_title="主流產業動能戰情室", page_icon="📈", layout="wide")

TRADER_PROFILE = """
使用者是「產業輪動＋動能波段」型交易者，不是純當沖或超短線。
偏好：右側交易、主升段、強勢股、題材股、資金輪動、回測10日線後轉強。
如果進場點不錯、產業趨勢成立，可以抱波段。
不喜歡：無腦追高、弱勢股攤平、沒量股票、純價值長抱。
系統需提醒：過熱、假突破、爆量長黑K、跌破10日線、跌破20日線、弱於大盤。
"""

MY_HOLDINGS = {
    "2383.TW": {"名稱": "台光電", "成本": 2445.97, "股數": 120},
    "6515.TW": {"名稱": "穎崴", "成本": 6104.97, "股數": 75},
    "6274.TW": {"名稱": "台燿", "成本": 1311.87, "股數": 200},
    "2408.TW": {"名稱": "南亞科", "成本": 287.41, "股數": 1000},
    "2330.TW": {"名稱": "台積電", "成本": 2328.31, "股數": 100},
    "3017.TW": {"名稱": "奇鋐", "成本": 2307.78, "股數": 200},
    "3533.TW": {"名稱": "嘉澤", "成本": 1355.82, "股數": 74},
    "4958.TW": {"名稱": "臻鼎-KY", "成本": 381.54, "股數": 1400},
    "6213.TW": {"名稱": "聯茂", "成本": 263.37, "股數": 1000},
    "2454.TW": {"名稱": "聯發科", "成本": 3474.94, "股數": 100},
    "2327.TW": {"名稱": "國巨", "成本": 327.97, "股數": 1000},
    "8046.TW": {"名稱": "南電", "成本": 581.43, "股數": 500},
}

WATCHLIST: Dict[str, List[Tuple[str, str]]] = {
    "AI伺服器": [("2382.TW", "廣達"), ("3231.TW", "緯創"), ("2376.TW", "技嘉"), ("2317.TW", "鴻海"), ("6669.TW", "緯穎"), ("NVDA", "NVIDIA"), ("SMCI", "Super Micro"), ("DELL", "Dell")],
    "散熱": [("3017.TW", "奇鋐"), ("3324.TW", "雙鴻"), ("3653.TW", "健策"), ("2421.TW", "建準"), ("8996.TW", "高力"), ("VRT", "Vertiv")],
    "PCB / CCL": [("2383.TW", "台光電"), ("6274.TW", "台燿"), ("2368.TW", "金像電"), ("6213.TW", "聯茂"), ("3037.TW", "欣興"), ("4958.TW", "臻鼎-KY"), ("8358.TW", "金居")],
    "CPO / 光通訊": [("3450.TW", "聯鈞"), ("4979.TWO", "華星光"), ("6442.TW", "光聖"), ("3163.TWO", "波若威"), ("3363.TWO", "上詮"), ("3081.TWO", "聯亞"), ("AAOI", "AAOI"), ("AVGO", "Broadcom"), ("MRVL", "Marvell")],
    "記憶體": [("2408.TW", "南亞科"), ("2344.TW", "華邦電"), ("3260.TWO", "威剛"), ("3006.TW", "晶豪科"), ("2337.TW", "旺宏"), ("MU", "Micron"), ("WDC", "Western Digital")],
    "半導體設備 / 材料": [("1560.TW", "中砂"), ("3583.TW", "辛耘"), ("3131.TW", "弘塑"), ("6187.TWO", "萬潤"), ("2404.TW", "漢唐"), ("6196.TW", "帆宣"), ("AMAT", "Applied Materials"), ("LRCX", "Lam Research"), ("KLAC", "KLA"), ("ASML", "ASML")],
    "測試介面": [("6515.TW", "穎崴"), ("6223.TWO", "旺矽"), ("6510.TW", "精測"), ("TER", "Teradyne"), ("FORM", "FormFactor")],
    "機器人 / 自動化": [("2049.TW", "上銀"), ("2359.TW", "所羅門"), ("8374.TW", "羅昇"), ("2464.TW", "盟立"), ("7750.TW", "新代"), ("1590.TW", "亞德客-KY")],
    "低基期 / 新觀察": [("6831.TW", "邁科"), ("2367.TW", "燿華"), ("8150.TW", "南茂"), ("6443.TW", "元晶"), ("2331.TW", "精英"), ("4977.TW", "眾達-KY")],
}

CROSS_DAY_PRICES = [
    {"商品名稱":"加權指","4/28":39521.73,"5/5":40769.29,"5/6":41138.85,"5/8":41603.94,"產業":"大盤"},
    {"商品名稱":"台指近","4/28":39749,"5/5":41035,"5/6":41503,"5/8":41937,"產業":"大盤"},
    {"商品名稱":"台積電","4/28":2215,"5/5":2250,"5/6":2250,"5/8":2290,"產業":"權值"},
    {"商品名稱":"廣達","4/28":321,"5/5":321,"5/6":346.5,"5/8":340.5,"產業":"AI伺服器"},
    {"商品名稱":"南亞科","4/28":237.5,"5/5":256.5,"5/6":282,"5/8":274,"產業":"記憶體"},
    {"商品名稱":"群聯","4/28":1970,"5/5":2115,"5/6":2325,"5/8":2430,"產業":"記憶體"},
    {"商品名稱":"台光電","4/28":4375,"5/5":4730,"5/6":4950,"5/8":4750,"產業":"PCB / CCL"},
    {"商品名稱":"穎崴","4/28":10135,"5/5":10055,"5/6":10130,"5/8":9630,"產業":"測試介面"},
    {"商品名稱":"奇鋐","4/28":2780,"5/5":2705,"5/6":2435,"5/8":2445,"產業":"散熱"},
    {"商品名稱":"高力","4/28":1175,"5/5":1190,"5/6":1165,"5/8":1015,"產業":"散熱"},
    {"商品名稱":"聯鈞","4/28":305.5,"5/5":365,"5/6":343.5,"5/8":410,"產業":"CPO / 光通訊"},
    {"商品名稱":"華星光","4/28":561,"5/5":718,"5/6":703,"5/8":660,"產業":"CPO / 光通訊"},
    {"商品名稱":"光聖","4/28":1905,"5/5":2060,"5/6":2060,"5/8":1965,"產業":"CPO / 光通訊"},
    {"商品名稱":"達發","4/28":570,"5/5":596,"5/6":655,"5/8":753,"產業":"IC設計"},
    {"商品名稱":"NVDA","4/28":209.25,"5/5":198.48,"5/6":204.11,"5/8":211.5,"產業":"AI伺服器"},
    {"商品名稱":"INTC","4/28":81.73,"5/5":95.78,"5/6":108.33,"5/8":109.62,"產業":"半導體"},
    {"商品名稱":"環球晶","4/28":580,"5/5":666,"5/6":721,"5/8":802,"產業":"半導體材料"},
    {"商品名稱":"世芯-KY","4/28":4000,"5/5":4150,"5/6":4565,"5/8":4890,"產業":"IC設計"},
    {"商品名稱":"勤誠","4/28":1170,"5/5":1265,"5/6":1325,"5/8":1415,"產業":"AI伺服器"},
    {"商品名稱":"華邦電","4/28":95.5,"5/5":98.8,"5/6":108.5,"5/8":107,"產業":"記憶體"},
    {"商品名稱":"漢唐","4/28":969,"5/5":977,"5/6":984,"5/8":1015,"產業":"半導體設備 / 材料"},
    {"商品名稱":"旺矽","4/28":4880,"5/5":5000,"5/6":4950,"5/8":5025,"產業":"測試介面"},
    {"商品名稱":"健策","4/28":4950,"5/5":4780,"5/6":4305,"5/8":3650,"產業":"散熱"},
    {"商品名稱":"台燿","4/28":966,"5/5":1220,"5/6":1315,"5/8":1370,"產業":"PCB / CCL"},
    {"商品名稱":"雙鴻","4/28":1145,"5/5":1170,"5/6":1105,"5/8":1065,"產業":"散熱"},
    {"商品名稱":"聯茂","4/28":253.5,"5/5":284,"5/6":285,"5/8":287.5,"產業":"PCB / CCL"},
    {"商品名稱":"聯發科","4/28":2615,"5/5":3155,"5/6":3430,"5/8":3630,"產業":"IC設計"},
    {"商品名稱":"AAOI","4/28":137.51,"5/5":172.98,"5/6":175.59,"5/8":157.55,"產業":"CPO / 光通訊"},
    {"商品名稱":"金居","4/28":362,"5/5":433,"5/6":458.5,"5/8":454.5,"產業":"PCB / CCL"},
    {"商品名稱":"南茂","4/28":None,"5/5":84.1,"5/6":89.2,"5/8":92.7,"產業":"低基期 / 新觀察"},
    {"商品名稱":"燿華","4/28":None,"5/5":61.2,"5/6":60.9,"5/8":61.7,"產業":"低基期 / 新觀察"},
    {"商品名稱":"邁科","4/28":None,"5/5":520,"5/6":561,"5/8":540,"產業":"低基期 / 新觀察"},
    {"商品名稱":"元晶","4/28":None,"5/5":37.5,"5/6":37.85,"5/8":39.95,"產業":"低基期 / 新觀察"},
    {"商品名稱":"精英","4/28":None,"5/5":21.4,"5/6":21.1,"5/8":20.35,"產業":"低基期 / 新觀察"},
    {"商品名稱":"眾達-KY","4/28":None,"5/5":232,"5/6":223,"5/8":None,"產業":"低基期 / 新觀察"},
    {"商品名稱":"亞德客","4/28":None,"5/5":1440,"5/6":1435,"5/8":1505,"產業":"機器人 / 自動化"},
    {"商品名稱":"新代","4/28":None,"5/5":2670,"5/6":2595,"5/8":2545,"產業":"機器人 / 自動化"},
]

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_price(symbol: str, period: str = "6mo") -> Optional[pd.DataFrame]:
    try:
        raw = yf.download(symbol, period=period, progress=False, auto_adjust=False)
        if raw is None or raw.empty:
            return None
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        raw = raw.reset_index()
        raw["MA5"] = raw["Close"].rolling(5).mean()
        raw["MA10"] = raw["Close"].rolling(10).mean()
        raw["MA20"] = raw["Close"].rolling(20).mean()
        raw["VOL_MA5"] = raw["Volume"].rolling(5).mean()
        return raw
    except Exception:
        return None

def sf(value) -> float:
    try:
        if pd.isna(value): return 0.0
        if hasattr(value, "iloc"): return float(value.iloc[0])
        return float(value)
    except Exception:
        return 0.0

def latest_snapshot(df: pd.DataFrame) -> Optional[dict]:
    valid = df.dropna(subset=["Close", "MA5", "MA10", "MA20", "Volume", "VOL_MA5"])
    if valid.empty: return None
    last = valid.iloc[-1]
    prev = valid.iloc[-2] if len(valid) >= 2 else last
    close, prev_close = sf(last["Close"]), sf(prev["Close"])
    return {
        "close": close,
        "change_pct": ((close - prev_close) / prev_close * 100) if prev_close else 0,
        "ma5": sf(last["MA5"]), "ma10": sf(last["MA10"]), "ma20": sf(last["MA20"]),
        "volume": sf(last["Volume"]), "vol_ma5": sf(last["VOL_MA5"]),
    }

def technical_signal(d: dict):
    c, ma5, ma10, ma20, vol, vol_ma5 = d["close"], d["ma5"], d["ma10"], d["ma20"], d["volume"], d["vol_ma5"]
    vol_up = vol > vol_ma5 * 1.2 if vol_ma5 else False
    dist20 = (c - ma20) / ma20 * 100 if ma20 else 0
    if c > ma5 > ma10 > ma20 and vol_up:
        if dist20 > 18:
            return "🟢 過熱強勢", "主升段但乖離偏大", "可抱不宜重壓追"
        return "🟢 強勢", "右側突破，量價配合", "短線追蹤 / 波段續抱"
    if c > ma10 and c > ma20:
        return "🟡 偏多", "中期架構仍偏多", "等回檔 / 波段續抱"
    if c < ma5 and c > ma20:
        return "🟠 回測", "跌破5日但仍守月線", "觀察10日/20日支撐"
    if c < ma20:
        return "🔴 轉弱", "跌破20日線", "暫避 / 降低部位"
    return "⚪ 震盪", "方向不清", "先觀察"

def cross_day_df():
    df = pd.DataFrame(CROSS_DAY_PRICES)
    for a,b,col in [("4/28","5/8","4/28→5/8%"),("5/5","5/8","5/5→5/8%"),("5/6","5/8","5/6→5/8%")]:
        df[col] = df.apply(lambda r: round((r[b]-r[a])/r[a]*100,2) if pd.notna(r[a]) and pd.notna(r[b]) and r[a] else None, axis=1)
    def trend(r):
        p428,p55,p56,p58 = r["4/28"],r["5/5"],r["5/6"],r["5/8"]
        if pd.notna(p428) and pd.notna(p55) and pd.notna(p56) and pd.notna(p58):
            if p428 < p55 < p56 < p58: return "連續墊高 / 主升段候選"
            if p56 > p55 and p56 > p58 and (r["5/6→5/8%"] or 0) < -5: return "高檔轉弱警示"
            if p58 > p55 and p56 > p55: return "趨勢偏多"
            if p58 < p55: return "短線轉弱"
        if pd.notna(p55) and pd.notna(p56) and pd.notna(p58):
            if p55 < p56 < p58: return "短線連續轉強"
            if p56 > p58: return "5/6後回落"
        return "資料不足 / 觀察"
    df["趨勢判斷"] = df.apply(trend, axis=1)
    return df

def sector_momentum(df: pd.DataFrame):
    res = df.dropna(subset=["5/5→5/8%"]).groupby("產業", as_index=False).agg(
        平均短期漲幅=("5/5→5/8%", "mean"),
        強勢檔數=("5/5→5/8%", lambda s: int((s > 3).sum())),
        轉弱檔數=("5/5→5/8%", lambda s: int((s < -3).sum())),
        檔數=("商品名稱", "count"),
    ).sort_values("平均短期漲幅", ascending=False)
    res["平均短期漲幅"] = res["平均短期漲幅"].round(2)
    return res

def build_watchlist_table(sector: str):
    rows=[]
    for symbol,name in WATCHLIST[sector]:
        df=fetch_price(symbol)
        if df is None:
            rows.append({"股票":name,"代號":symbol,"現價":None,"漲跌%":None,"MA5":None,"MA10":None,"MA20":None,"量比":None,"燈號":"資料失敗","判斷":"yfinance抓不到","適合打法":"手動確認"})
            continue
        snap=latest_snapshot(df)
        if snap is None: continue
        light,reason,style=technical_signal(snap)
        rows.append({"股票":name,"代號":symbol,"現價":round(snap["close"],2),"漲跌%":round(snap["change_pct"],2),"MA5":round(snap["ma5"],2),"MA10":round(snap["ma10"],2),"MA20":round(snap["ma20"],2),"量比":round(snap["volume"]/snap["vol_ma5"],2) if snap["vol_ma5"] else None,"燈號":light,"判斷":reason,"適合打法":style})
    return pd.DataFrame(rows)

def render_chart(symbol: str, name: str):
    df=fetch_price(symbol)
    if df is None:
        st.warning("這檔目前抓不到走勢資料。")
        return
    cd=df.dropna(subset=["Close","MA5","MA10","MA20"])
    if cd.empty:
        st.warning("走勢資料不足。")
        return
    if go:
        fig=go.Figure()
        for col in ["Close","MA5","MA10","MA20"]:
            fig.add_trace(go.Scatter(x=cd["Date"], y=cd[col], mode="lines", name=col))
        fig.update_layout(height=430, title=f"{name} 技術線", margin=dict(l=10,r=10,t=45,b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.line_chart(cd.set_index("Date")[["Close","MA5","MA10","MA20"]], use_container_width=True)

def get_secret(key: str):
    try:
        if key in st.secrets: return st.secrets[key]
    except Exception: pass
    return os.getenv(key)

def ai_analysis(prompt: str):
    api_key=get_secret("OPENAI_API_KEY")
    if not api_key: return "尚未設定 OPENAI_API_KEY。請到 Streamlit Cloud → App settings → Secrets 設定。"
    if OpenAI is None: return "尚未安裝 openai 套件，請確認 requirements.txt 有 openai。"
    client=OpenAI(api_key=api_key)
    resp=client.responses.create(
        model=get_secret("OPENAI_MODEL") or "gpt-5.2",
        instructions="你是台股與美股產業輪動分析師。請用繁體中文，語氣直接，符合使用者的產業輪動＋動能波段風格。不可保證獲利，需提醒風險。",
        input=prompt,
    )
    return resp.output_text

st.title("📈 主流產業動能戰情室")
st.caption("整理市場地圖，不是自動報明牌。核心是產業輪動、動能波段、右側交易、風險控管。")
with st.expander("我的交易風格設定", expanded=False):
    st.write(TRADER_PROFILE)

tab_home, tab_holdings, tab_sector, tab_cross, tab_ai = st.tabs(["戰情首頁", "我的持股", "產業觀察", "跨日趨勢", "AI戰情解讀"])

with tab_home:
    cd=cross_day_df(); sec=sector_momentum(cd)
    c1,c2,c3,c4=st.columns(4)
    top_sector=sec.iloc[0]["產業"] if not sec.empty else "-"
    top_stock=cd.dropna(subset=["5/5→5/8%"]).sort_values("5/5→5/8%", ascending=False).iloc[0]
    weak_stock=cd.dropna(subset=["5/5→5/8%"]).sort_values("5/5→5/8%", ascending=True).iloc[0]
    c1.metric("短期最強產業", top_sector)
    c2.metric("短期最強個股", top_stock["商品名稱"], f'{top_stock["5/5→5/8%"]:.2f}%')
    c3.metric("短期轉弱警示", weak_stock["商品名稱"], f'{weak_stock["5/5→5/8%"]:.2f}%')
    c4.metric("觀察檔數", f"{len(cd)} 檔")
    st.subheader("產業動能排行")
    st.dataframe(sec, use_container_width=True, hide_index=True)
    col_a,col_b=st.columns(2)
    with col_a:
        st.write("偏強候選")
        strong=cd[cd["趨勢判斷"].str.contains("主升段|連續轉強|趨勢偏多", na=False)]
        st.dataframe(strong[["商品名稱","產業","4/28→5/8%","5/5→5/8%","趨勢判斷"]], use_container_width=True, hide_index=True)
    with col_b:
        st.write("轉弱 / 回落警示")
        weak=cd[cd["趨勢判斷"].str.contains("轉弱|回落|警示", na=False)]
        st.dataframe(weak[["商品名稱","產業","5/6→5/8%","趨勢判斷"]], use_container_width=True, hide_index=True)

with tab_holdings:
    st.subheader("持股損益總覽")
    rows=[]
    for sym,info in MY_HOLDINGS.items():
        df=fetch_price(sym); snap=latest_snapshot(df) if df is not None else None
        if snap is None: continue
        cost,shares=info["成本"],info["股數"]
        pnl=(snap["close"]-cost)*shares
        pnl_pct=(snap["close"]-cost)/cost*100 if cost else 0
        light,reason,style=technical_signal(snap)
        rows.append({"股票":info["名稱"],"代號":sym,"現價":round(snap["close"],2),"成本":round(cost,2),"損益%":round(pnl_pct,2),"未實損益":int(pnl),"市值":int(snap["close"]*shares),"MA5":round(snap["ma5"],2),"MA10":round(snap["ma10"],2),"MA20":round(snap["ma20"],2),"燈號":light,"判斷":reason,"適合打法":style})
    if rows:
        dfh=pd.DataFrame(rows)
        c1,c2,c3=st.columns(3)
        c1.metric("總市值", f'{dfh["市值"].sum():,.0f}')
        c2.metric("未實現損益", f'{dfh["未實損益"].sum():+,.0f}')
        c3.metric("持股數", f"{len(dfh)} 檔")
        st.dataframe(dfh[["股票","現價","成本","損益%","未實損益","MA5","MA10","MA20","燈號","判斷","適合打法"]], use_container_width=True, hide_index=True)
        picked=st.selectbox("點選持股看走勢", dfh["股票"].tolist())
        row=dfh[dfh["股票"]==picked].iloc[0]
        render_chart(row["代號"], row["股票"])
    else:
        st.info("目前沒有持股資料，或 yfinance 暫時抓不到資料。")

with tab_sector:
    st.subheader("產業觀察")
    sector=st.selectbox("選擇產業", list(WATCHLIST.keys()))
    dfs=build_watchlist_table(sector)
    st.dataframe(dfs, use_container_width=True, hide_index=True)
    if not dfs.empty:
        picked=st.selectbox("點選個股看走勢", dfs["股票"].tolist())
        row=dfs[dfs["股票"]==picked].iloc[0]
        render_chart(row["代號"], row["股票"])
        st.markdown("#### 這檔的操作提醒")
        st.write(f"**燈號：** {row['燈號']}")
        st.write(f"**判斷：** {row['判斷']}")
        st.write(f"**適合打法：** {row['適合打法']}")

with tab_cross:
    st.subheader("跨日價格追蹤")
    cd=cross_day_df()
    col1,col2=st.columns([1,2])
    with col1:
        selected=st.multiselect("篩選產業", sorted(cd["產業"].dropna().unique().tolist()), default=[])
    with col2:
        keyword=st.text_input("搜尋股票名稱", "")
    filtered=cd.copy()
    if selected: filtered=filtered[filtered["產業"].isin(selected)]
    if keyword: filtered=filtered[filtered["商品名稱"].str.contains(keyword, case=False, na=False)]
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.subheader("4/28 → 5/8 漲幅排行")
    st.dataframe(cd.dropna(subset=["4/28→5/8%"]).sort_values("4/28→5/8%", ascending=False).head(20)[["商品名稱","產業","4/28→5/8%","趨勢判斷"]], use_container_width=True, hide_index=True)
    st.subheader("5/5 → 5/8 短期動能排行")
    st.dataframe(cd.dropna(subset=["5/5→5/8%"]).sort_values("5/5→5/8%", ascending=False).head(20)[["商品名稱","產業","5/5→5/8%","趨勢判斷"]], use_container_width=True, hide_index=True)

with tab_ai:
    st.subheader("AI 戰情解讀")
    cd=cross_day_df(); sec=sector_momentum(cd)
    prompt=f"""
使用者交易風格：
{TRADER_PROFILE}

短期產業動能排行：
{sec.head(10).to_string(index=False)}

5/5→5/8短期強勢前10：
{cd.dropna(subset=["5/5→5/8%"]).sort_values("5/5→5/8%", ascending=False).head(10)[["商品名稱","產業","5/5→5/8%","趨勢判斷"]].to_string(index=False)}

5/5→5/8轉弱前10：
{cd.dropna(subset=["5/5→5/8%"]).sort_values("5/5→5/8%", ascending=True).head(10)[["商品名稱","產業","5/5→5/8%","趨勢判斷"]].to_string(index=False)}

請幫我判斷：
1. 目前主流產業在哪裡？
2. 哪些族群是主升段？
3. 哪些族群是高檔轉弱？
4. 哪些股票適合等回檔？
5. 哪些股票不該追？
6. 依照我的風格，明天盤前該注意什麼？
"""
    prompt=st.text_area("AI 分析提示詞", prompt, height=360)
    if st.button("產生 AI 戰情解讀"):
        with st.spinner("AI 分析中..."):
            try: st.write(ai_analysis(prompt))
            except Exception as e: st.error(f"AI 分析失敗：{e}")
    st.info("若尚未設定 API Key，請到 Streamlit Cloud → App settings → Secrets，加入 OPENAI_API_KEY。")
