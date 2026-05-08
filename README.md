# 主流產業動能戰情室

這是一個 Streamlit 股票戰情室，用途不是自動報明牌，而是把市場整理成「可跟 AI 討論的戰情地圖」。

## 功能
- 我的持股損益
- 產業分類觀察
- 台股＋美股對照
- 真實股價抓取：yfinance
- 5日 / 10日 / 20日均線
- 強弱燈號
- 跨日價格追蹤
- 產業動能排行
- OpenAI API 戰情解讀

## Streamlit Cloud 設定
主程式檔案請設定為：

```bash
stock_app.py
```

## OpenAI API Key 設定
不要把 API Key 寫在程式裡。

到 Streamlit Cloud：App → Settings → Secrets

加入：

```toml
OPENAI_API_KEY = "你的 API KEY"
OPENAI_MODEL = "gpt-5.2"
```

若暫時不設定 API Key，其他股價與表格功能仍可使用，只有 AI 戰情解讀不能用。

## 本機執行
```bash
pip install -r requirements.txt
streamlit run stock_app.py
```
