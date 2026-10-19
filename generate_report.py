import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# 한글 폰트 설정 (리눅스 환경 대응)
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def generate_daily_report():
    industry = "전자부품"
    data_dir = Path("data") / industry
    
    if not data_dir.exists():
        print("수집된 데이터 폴더가 없습니다.")
        return

    # 가장 최근에 수집된 CSV 파일 찾기
    csv_files = sorted(list(data_dir.glob("*.csv")))
    if not csv_files:
        print("수집된 CSV 파일이 없습니다.")
        return

    latest_csv = csv_files[-1]
    trade_date = latest_csv.stem  # 파일 이름(YYYY-MM-DD)이 거래일
    
    df = pd.read_csv(latest_csv)
    print(f"분석 대상 데이터: {latest_csv}")

    # 1. 간단한 정적 시각화 그래프 생성 (현재가 기준 막대 그래프)
    fig, ax = plt.subplots(figsize=(10, 5))
    if "종목명" in df.columns and "현재가(종가)" in df.columns:
        ax.bar(df["종목명"], df["현재가(종가)"], color="skyblue")
        ax.set_title(f"[{trade_date}] 전자부품 주요 종목 현재가 현황")
        ax.set_ylabel("현재가 (원)")
        plt.xticks(rotation=45)
        plt.tight_layout()

    # reports 폴더에 이미지 저장
    report_dir = Path("reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    
    chart_path = report_dir / f"chart_{trade_date}.png"
    fig.savefig(chart_path)
    plt.close(fig)

    # 2. 마크다운 보고서(Markdown Report) 작성
    md_path = report_dir / f"report_{trade_date}.md"
    
    md_content = f"# [{trade_date}] 전자부품 업종 일일 분석 보고서\n\n"
    md_content += f"수집된 종목 수: **{len(df)}개**\n\n"
    md_content += "## 📊 종목별 요약 테이블\n\n"
    md_content += df[["종목명", "종목코드", "현재가(종가)", "등락률(%)", "거래량"]].to_markdown(index=False)
    md_content += "\n\n## 📈 시각화 차트\n\n"
    md_content += f"![일일 차트](../reports/{chart_path.name})\n"

    md_path.write_text(md_content, encoding="utf-8")
    print(f"보고서 생성 완료: {md_path}")

if __name__ == "__main__":
    generate_daily_report()
