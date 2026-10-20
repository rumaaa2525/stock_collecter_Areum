import os
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import squarify

# 1. 폰트 설정 (NanumGothic)
plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False

# 2. 경로 설정 및 최신 CSV 파일 찾기
data_dir = Path("data") / "전자장비와기기"
reports_dir = Path("reports")
reports_dir.mkdir(exist_ok=True)

csv_files = sorted(list(data_dir.glob("*.csv"))) if data_dir.exists() else []
if not csv_files:
    print("수집된 CSV 데이터가 없습니다.")
    exit()

latest_csv = csv_files[-1]
trade_date = latest_csv.stem  # 예: "2026-10-19"
print(f"최신 데이터 파일 분석 중: {latest_csv} (기준일: {trade_date})")

# 3. 데이터 로드 및 정제
df = pd.read_csv(latest_csv)

price_col = "현재가(종가)" if "현재가(종가)" in df.columns else "현재가"
name_col = "종목명" if "종목명" in df.columns else df.columns[0]
change_col = next((c for c in ["등락률(%)", "등락률"] if c in df.columns), None)

if name_col in df.columns and price_col in df.columns:
    df['cleaned_price'] = pd.to_numeric(df[price_col].astype(str).str.replace(",", ""), errors="coerce")

if change_col:
    df['cleaned_change'] = pd.to_numeric(
        df[change_col].astype(str).str.replace("%", "").str.replace("+", "").str.replace(",", ""), 
        errors="coerce"
    )

# 4. 차트 1: 전체 종목 현재가 현황 (고정 파일명 저장)
if 'cleaned_price' in df.columns:
    df_sorted = df.dropna(subset=['cleaned_price']).sort_values(by='cleaned_price', ascending=False).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df_sorted[name_col], df_sorted['cleaned_price'], color="skyblue")
    ax.set_ylabel("현재가 (원)")
    ax.set_title(f"전체 종목 현재가 현황 ({trade_date})")
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.tight_layout()
    plt.savefig(reports_dir / "latest_chart.png")
    plt.close(fig)

# 5. 차트 2: 상하위 집중 비교 (Top/Bottom) (고정 파일명 저장)
if 'cleaned_price' in df.columns and len(df_sorted) >= 5:
    top_bottom = pd.concat([df_sorted.head(5), df_sorted.tail(5)])
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(top_bottom[name_col], top_bottom['cleaned_price'], color="orange")
    ax.set_ylabel("현재가 (원)")
    ax.set_title("상위 및 하위 종목 비교")
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.tight_layout()
    plt.savefig(reports_dir / "latest_top_bottom.png")
    plt.close(fig)

# 6. 차트 3: 종목별 등락률(%) 현황 (고정 파일명 저장)
if 'cleaned_change' in df.columns:
    df_change = df.dropna(subset=['cleaned_change']).sort_values(by='cleaned_change', ascending=True)
    colors = ['#d9534f' if x > 0 else ('#5bc0de' if x < 0 else '#999999') for x in df_change['cleaned_change']]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(df_change[name_col], df_change['cleaned_change'], color=colors)
    ax.axvline(0, color='gray', linestyle='--', linewidth=0.8)
    ax.set_xlabel("등락률 (%)")
    ax.set_title(f"종목별 등락률 현황 ({trade_date})")
    plt.tight_layout()
    plt.savefig(reports_dir / "latest_change_chart.png")
    plt.close(fig)

# 7. 차트 4: 종목별 규모 비중 트리맵 (고정 파일명 저장)
if 'cleaned_price' in df.columns:
    df_clean = df.dropna(subset=['cleaned_price']).sort_values(by='cleaned_price', ascending=False)
    fig, ax = plt.subplots(figsize=(10, 5))
    try:
        labels = [f"{row[name_col]}\n({int(row['cleaned_price']):,}원)" for _, row in df_clean.iterrows()]
        squarify.plot(sizes=df_clean['cleaned_price'], label=labels, alpha=0.7, ax=ax, text_kwargs={'fontsize': 8})
        ax.axis('off')
        ax.set_title(f"종목별 규모 비중 트리맵 ({trade_date})")
    except Exception as e:
        ax.text(0.5, 0.5, f"트리맵 생성 오류: {e}", ha='center', va='center')
    plt.tight_layout()
    plt.savefig(reports_dir / "latest_treemap.png")
    plt.close(fig)

print("모든 시각화 리포트가 성공적으로 갱신되었습니다!")
