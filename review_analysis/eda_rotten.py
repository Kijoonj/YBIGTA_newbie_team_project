import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# =========================
# 설정
# =========================
INPUT_PATH = "./database/reviews_rotten.csv"
PLOT_DIR = "./review_analysis/plots"
os.makedirs(PLOT_DIR, exist_ok=True)

# =========================
# 1) 데이터 로드
# =========================
df = pd.read_csv(INPUT_PATH)

# 컬럼명 표준화(혹시 review로 되어있으면 content로 변경)
if "review" in df.columns and "content" not in df.columns:
    df = df.rename(columns={"review": "content"})

# =========================
# 2) 기본 정리
# =========================
df["date"] = df["date"].fillna("").astype(str).str.strip()
df["content"] = df["content"].fillna("").astype(str)

df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
df["char_len"] = df["content"].str.len()
df["word_len"] = df["content"].apply(lambda x: len(str(x).split()))

print("\n===== BASIC =====")
print("rows:", len(df))
print("missing date:", int((df["date"] == "").sum()))
print("\n===== date(raw) TOP 30 =====")
print(df["date"].value_counts().head(30))

# =========================
# 3) 날짜 파싱 (과거 확장 핵심)
# =========================
df["date_parsed"] = pd.NaT

# (A) 1순위: MM/DD/YYYY (Rotten CSV에 많음)
mask_full = df["date"].str.match(r"^\d{1,2}/\d{1,2}/\d{4}$")
df.loc[mask_full, "date_parsed"] = pd.to_datetime(
    df.loc[mask_full, "date"],
    format="%m/%d/%Y",
    errors="coerce"
)

# base_year 추정: 파싱된 year 중 최빈값
base_year: int
if df.loc[mask_full, "date_parsed"].notna().sum() > 0:
    base_year = int(df.loc[mask_full, "date_parsed"].dt.year.mode()[0])
else:
    # fallback: 현재 연도
    base_year = pd.Timestamp.today().year

# (B) 2순위: "Jan 29" 처럼 연도 없는 포맷
mask_md = df["date"].str.match(r"^[A-Za-z]{3}\s+\d{1,2}$")

temp_md = df.loc[mask_md, "date"] + f" {base_year}"
df.loc[mask_md, "date_parsed"] = pd.to_datetime(
    temp_md,
    format="%b %d %Y",
    errors="coerce"
)

# (C) 상대시간(11h, 1d, 2mo)는 날짜 분석에서는 제외
# (원하면 나중에 absolute로 변환도 가능)
df_ts = df[df["date_parsed"].notna()].copy()

print("\n===== DATE PARSE RESULT =====")
print("base_year:", base_year)
print("parsed success:", len(df_ts))
print("parsed fail:", len(df) - len(df_ts))
print("date range:", df_ts["date_parsed"].min(), "~", df_ts["date_parsed"].max())

# =========================
# 4) 시각화: Rating / Length
# =========================
plt.figure(figsize=(10, 4))
df["rating"].dropna().hist(bins=20)
plt.title("rating(Rotten Tomato)")
plt.xlabel("rating")
plt.ylabel("count")
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "rating(Rotten Tomato).png"))
plt.close()

plt.figure(figsize=(10, 4))
df["char_len"].hist(bins=30)
plt.title("review_length(Rotten Tomato)")
plt.xlabel("char_len")
plt.ylabel("count")
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "review_length(Rotten Tomato).png"))
plt.close()

# =========================
# 5) 시각화: Daily / Weekly Counts
# =========================
if len(df_ts) > 0:
    # Daily
    df_ts["date_only"] = df_ts["date_parsed"].dt.date
    daily_counts = df_ts["date_only"].value_counts().sort_index()

    plt.figure(figsize=(14, 4))
    plt.plot(daily_counts.index, daily_counts.values)
    plt.title("review_counts(Rotten Tomato)")
    plt.xlabel("date")
    plt.ylabel("count")

    ax = plt.gca()
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))  # ✅ 2개월 간격
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "review_counts(Rotten Tomato).png"))
    plt.close()


    

# =========================
# 6) 이상치 요약
# =========================
rating_outliers = df[(df["rating"].notna()) & ((df["rating"] < 0) | (df["rating"] > 10))]
short_reviews = df[df["char_len"] < 3]
long_reviews = df[df["char_len"] > df["char_len"].quantile(0.99)]

summary = {
    "n_total": [len(df)],
    "n_parsed_date_success": [len(df_ts)],
    "n_parsed_date_fail": [len(df) - len(df_ts)],
    "n_rating_outliers": [len(rating_outliers)],
    "n_short_reviews": [len(short_reviews)],
    "n_long_reviews_top1pct": [len(long_reviews)],
    "rating_mean": [float(df["rating"].mean(skipna=True)) if df["rating"].notna().sum() > 0 else 0.0],
    "rating_std": [float(df["rating"].std(skipna=True)) if df["rating"].notna().sum() > 0 else 0.0],
    "char_len_mean": [float(df["char_len"].mean())],
    "char_len_std": [float(df["char_len"].std())],
}

summary_path = os.path.join(PLOT_DIR, "eda_summary.csv")
pd.DataFrame(summary).to_csv(summary_path, index=False, encoding="utf-8-sig")

print("\n✅ EDA plots saved to:", PLOT_DIR)
print("✅ EDA summary saved:", summary_path)
