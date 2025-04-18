import os
import pandas as pd
from transformers import pipeline
import torchvision  # 避免 Beta 版警告

# 關閉 torchvision 測試版警告
torchvision.disable_beta_transforms_warning()

# 設定檔案路徑
news_file = os.path.join(os.path.dirname(__file__), "../news/coindesk_news.csv")

# 讀取新聞 CSV
df = pd.read_csv(news_file)

# 確保 `Title` 和 `Body` 欄位存在
if "Title" not in df.columns or "Body" not in df.columns:
    raise ValueError("❌ 找不到 'Title' 或 'Body' 欄位，請檢查 CSV 格式！")

# 下載並加載 `T5` 總結模型
summarization_pipeline = pipeline("summarization", model="t5-small")  # 修正模型名稱

# 下載並加載 `FinBERT` 分析模型
sentiment_pipeline = pipeline("text-classification", model="yiyanghkust/finbert-tone")

# 內文摘要
def summarize_text(text):
    if len(text.split()) < 30:  # 如果內文太短，不需要摘要
        return text
    summary = summarization_pipeline(text, max_length=50, min_length=10, do_sample=False)
    return summary[0]["summary_text"]

# 對 `Body` 做摘要
df["Summary"] = df["Body"].apply(summarize_text)

# 對 `Summary` 進行情緒分析
df["Sentiment"] = df["Summary"].apply(lambda summary: sentiment_pipeline(summary)[0]["label"])

# 選擇要輸出的欄位（不包含 `Timestamp` 和 `Body`）
df_output = df[["Published Time", "Title", "Summary", "Sentiment"]]

# 儲存結果回 CSV
output_file = os.path.join(os.path.dirname(__file__), "../news/coindesk_news_with_summary_sentiment.csv")
df_output.to_csv(output_file, index=False)

print(f"✅ 分析完成，結果已存入 {output_file}")