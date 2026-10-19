import os
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm  # 폰트 관리를 위해 추가

# ==========================================
# 한글 폰트 설정 (프로젝트 내 폰트 파일 직접 연동)
# ==========================================
# GitHub 저장소에 업로드한 폰트 파일 경로 지정 (예시: 저장소 루트에 있는 경우)
font_path = "NanumGothicOTF.otf"  # 실제 업로드하신 폰트 파일명으로 수정하세요! (예: fonts/NanumGothic.otf 등)

if os.path.exists(font_path):
    # 폰트 파일을 직접 등록
    font_prop = fm.FontProperties(fname=font_path)
    font_name = font_prop.get_name()
    plt.rcParams['font.family'] = font_name
    print(f"[정보] 커스텀 폰트 로드 성공: {font_name} ({font_path})")
else:
    # 폰트 파일이 없을 경우 시스템 기본 폰트(나눔고딕 등)로 폴백 시도
    print(f"[경고] 지정한 경로에 폰트 파일이 없습니다({font_path}). 기본 폰트를 사용합니다.")
    plt.rcParams['font.family'] = 'NanumGothic'

plt.rcParams['axes.unicode_minus'] = False  # 그래프 마이너스 기호 깨짐 방지

def generate_daily_report():
    # 수집된 데이터가 저장된 폴더 경로 (기존 설정에 맞춤)
    industry = "전자부품"
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
    trade_date = latest_csv.stem  # 파일 이름(YYYY-MM-DD)이 거래일
    
    df = pd.read_csv(latest_csv)
    print(f"분석 대상 데이터: {latest_csv}")

    # reports 폴더 생성
    report_dir = Path("reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    # 1. 정적 시각화 그래프 생성 (나눔 폰트 적용)
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # 컬럼명 유연하게 매칭
    price_col = "현재가(종가)" if "현재가(종가)" in df.columns else "현재가"
    name_col = "종목명" if "종목명" in df.columns else df.columns[0]

    if name_col in df.columns and price_col in df.columns:
        prices = pd.to_numeric(df[price_col].astype(str).str.replace(",", ""), errors="coerce")
        ax.bar(df[name_col], prices, color="skyblue")
        
        # 폰트 객체가 있으면 명시적으로 전달, 없으면 기본 설정 적용
        if os.path.exists(font_path):
            ax.set_title(f"[{trade_date}] 전자장비와기기 주요 종목 현재가 현황", fontsize=14, fontproperties=font_prop)
            ax.set_ylabel("현재가 (원)", fontsize=12, fontproperties=font_prop)
            # x축 라벨 등에도 폰트가 필요할 경우 fontproperties 적용 가능
        else:
            ax.set_title(f"[{trade_date}] 전자장비와기기 주요 종목 현재가 현황", fontsize=14)
            ax.set_ylabel("현재가 (원)", fontsize=12)
            
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

    chart_path = report_dir / f"chart_{trade_date}.png"
    fig.savefig(chart_path, dpi=150)
    plt.close(fig)
    print(f"차트 생성 완료: {chart_path}")

    # 2. 마크다운 보고서(Markdown Report) 작성
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
