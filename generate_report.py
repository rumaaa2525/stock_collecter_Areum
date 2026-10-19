import os
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def generate_daily_report():
    # 실제 수집된 폴더 이름인 '전자장비와기기'로 지정
    industry = "전자부품" # 폴더명이 '전자장비와기기'라면 아래 줄을 수정하세요
    data_dir = Path("data") / "전자장비와기기"
    
    if not data_dir.exists():
        print(f"[오류] 데이터 폴더가 존재하지 않습니다: {data_dir}")
        return

    # 가장 최근에 수집된 CSV 파일 찾기
    csv_files = sorted(list(data_dir.glob("*.csv")))
    if not csv_files:
        print("[오류] 수집된 CSV 파일이 없습니다.")
        return

    latest_csv = csv_files[-1]
    trade_date = latest_csv.stem  # 파일 이름(YYYY-MM-DD)
    
    df = pd.read_csv(latest_csv)
    print(f"분석 대상 데이터: {latest_csv}")
    print(df.columns)  # 컬럼 확인용 출력

    # reports 폴더 강제 생성 (파일이 없어도 폴더가 무조건 생성되도록 보장)
    report_dir = Path("reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    # 1. 정적 시각화 그래프 생성
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # 컬럼명에 맞춰 현재가 필드 지정
    price_col = "현재가(종가)" if "현재가(종가)" in df.columns else "현재가"
    name_col = "종목명" if "종목명" in df.columns else df.columns[0]

    if name_col in df.columns and price_col in df.columns:
        # 숫자로 변환
        prices = pd.to_numeric(df[price_col].astype(str).str.replace(",", ""), errors="coerce")
        ax.bar(df[name_col], prices, color="skyblue")
        ax.set_title(f"[{trade_date}] 전자장비와기기 주요 종목 현재가 현황")
        ax.set_ylabel("현재가 (원)")
        plt.xticks(rotation=45)
        plt.tight_layout()

    chart_path = report_dir / f"chart_{trade_date}.png"
    fig.savefig(chart_path)
    plt.close(fig)
    print(f"차트 생성 완료: {chart_path}")

    # 2. 마크다운 보고서 작성
    md_path = report_dir / f"report_{trade_date}.md"
    
    md_content = f"# [{trade_date}] 전자장비와기기 업종 일일 분석 보고서\n\n"
    md_content += f"수집된 종목 수: **{len(df)}개**\n\n"
    md_content += "## 📊 종목별 요약 테이블\n\n"
    
    display_cols = [c for c in ["종목명", "종목코드", price_col, "등락률(%)", "거래량"] if c in df.columns]
    md_content += df[display_cols].to_markdown(index=False)
    md_content += "\n\n## 📈 시각화 차트\n\n"
    md_content += f"![일일 차트](./chart_{trade_date}.png)\n"

    md_path.write_text(md_content, encoding="utf-8")
    print(f"보고서 생성 완료: {md_path}")

if __name__ == "__main__":
    generate_daily_report()
