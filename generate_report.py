import os
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm  # 폰트 관리를 위해 추가
import squarify  # 트리맵 시각화를 위해 필요

# ==========================================
# 한글 폰트 설정 (프로젝트 내 폰트 파일 직접 연동)
# ==========================================
font_path = "NanumGothic.otf"  

if os.path.exists(font_path):
    font_prop = fm.FontProperties(fname=font_path)
    font_name = font_prop.get_name()
    plt.rcParams['font.family'] = font_name
    print(f"[정보] 커스텀 폰트 로드 성공: {font_name} ({font_path})")
else:
    print(f"[경고] 지정한 경로에 폰트 파일이 없습니다({font_path}). 기본 폰트를 사용합니다.")
    plt.rcParams['font.family'] = 'NanumGothic'

plt.rcParams['axes.unicode_minus'] = False  # 그래프 마이너스 기호 깨짐 방지

def generate_daily_report():
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

    # 컬럼명 유연하게 매칭
    price_col = "현재가(종가)" if "현재가(종가)" in df.columns else "현재가"
    name_col = "종목명" if "종목명" in df.columns else df.columns[0]

    if name_col in df.columns and price_col in df.columns:
        # 데이터 정제 (숫자형 변환)
        df['cleaned_price'] = pd.to_numeric(df[price_col].astype(str).str.replace(",", ""), errors="coerce")
        df_clean = df.dropna(subset=['cleaned_price']).sort_values(by='cleaned_price', ascending=False).reset_index(drop=True)

        # ==========================================
        # 1. 기존 전체 정적 시각화 그래프 생성
        # ==========================================
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(df_clean[name_col], df_clean['cleaned_price'], color="skyblue")
        
        if os.path.exists(font_path):
            ax.set_title(f"[{trade_date}] 전자장비와기기 주요 종목 현재가 현황", fontsize=14, fontproperties=font_prop)
            ax.set_ylabel("현재가 (원)", fontsize=12, fontproperties=font_prop)
            plt.xticks(
                ticks=range(len(df_clean[name_col])), 
                labels=df_clean[name_col], 
                rotation=45, 
                ha="right", 
                fontproperties=font_prop
            )
        else:
            ax.set_title(f"[{trade_date}] 전자장비와기기 주요 종목 현재가 현황", fontsize=14)
            ax.set_ylabel("현재가 (원)", fontsize=12)
            plt.xticks(rotation=45, ha="right")
            
        plt.tight_layout()
        chart_path = report_dir / f"chart_{trade_date}.png"
        fig.savefig(chart_path, dpi=150)
        plt.close(fig)
        print(f"기본 차트 생성 완료: {chart_path}")

        # ==========================================
        # 2. 상하위 집중 비교 차트 (Top N / Bottom N) 생성
        # ==========================================
        n = min(5, len(df_clean)) # 종목 수가 5개 미만일 경우 대비
        top_n = df_clean.head(n)
        bottom_n = df_clean.tail(n).sort_values(by='cleaned_price', ascending=True)

        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        # 상위 종목 가로 바 그래프
        axes[0].barh(top_n[name_col], top_n['cleaned_price'], color="#4C72B0")
        axes[0].set_title(f"현재가 상위 Top {n} 종목", fontsize=13, fontproperties=font_prop if os.path.exists(font_path) else None)
        axes[0].set_xlabel("현재가 (원)", fontsize=11)
        axes[0].invert_yaxis()

        # 하위 종목 가로 바 그래프
        axes[1].barh(bottom_n[name_col], bottom_n['cleaned_price'], color="#DD8452")
        axes[1].set_title(f"현재가 하위 Bottom {n} 종목", fontsize=13, fontproperties=font_prop if os.path.exists(font_path) else None)
        axes[1].set_xlabel("현재가 (원)", fontsize=11)

        plt.tight_layout()
        top_bottom_chart_path = report_dir / f"top_bottom_chart_{trade_date}.png"
        fig.savefig(top_bottom_chart_path, dpi=150)
        plt.close(fig)
        print(f"상하위 비교 차트 생성 완료: {top_bottom_chart_path}")

        # ==========================================
        # 3. 트리맵 (Treemap) 차트 생성
        # ==========================================
        fig, ax = plt.subplots(figsize=(10, 6))
        try:
            # squarify를 이용한 트리맵 시각화 (현재가 기준 면적 배분)
            labels = [f"{row[name_col]}\n({row['cleaned_price']:,}원)" for _, row in df_clean.iterrows()]
            squarify.plot(
                sizes=df_clean['cleaned_price'], 
                label=labels, 
                alpha=0.7, 
                ax=ax, 
                text_kwargs={'fontproperties': font_prop if os.path.exists(font_path) else None, 'fontsize': 9}
            )
            ax.set_title(f"[{trade_date}] 종목별 현재가 규모 비중 (트리맵)", fontsize=14, fontproperties=font_prop if os.path.exists(font_path) else None)
            ax.axis('off')
        except Exception as e:
            print(f"[경고] 트리맵 생성 중 오류 발생: {e}")

        plt.tight_layout()
        treemap_path = report_dir / f"treemap_{trade_date}.png"
        fig.savefig(treemap_path, dpi=150)
        plt.close(fig)
        print(f"트리맵 차트 생성 완료: {treemap_path}")

    # ==========================================
    # 4. 마크다운 보고서(Markdown Report) 작성
    # ==========================================
    md_path = report_dir / f"report_{trade_date}.md"
    
    md_content = f"# [{trade_date}] 전자장비와기기 업종 일일 분석 보고서\n\n"
    md_content += f"수집된 종목 수: **{len(df)}개**\n\n"
    
    md_content += "## 📊 종목별 요약 테이블\n\n"
    display_cols = [c for c in ["종목명", "종목코드", price_col, "등락률(%)", "거래량"] if c in df.columns]
    md_content += df[display_cols].to_markdown(index=False)
    
    md_content += "\n\n## 📈 시각화 차트 목록\n\n"
    md_content += f"### 1. 전체 종목 현재가 현황\n"
    md_content += f"![일일 차트](./chart_{trade_date}.png)\n\n"
    
    md_content += f"### 2. 상하위 집중 비교 차트 (Top / Bottom)\n"
    md_content += f"![상하위 비교 차트](./top_bottom_chart_{trade_date}.png)\n\n"
    
    md_content += f"### 3. 종목별 규모 비중 (트리맵)\n"
    md_content += f"![트리맵 차트](./treemap_{trade_date}.png)\n"

    md_path.write_text(md_content, encoding="utf-8")
    print(f"보고서 생성 완료: {md_path}")

if __name__ == "__main__":
    generate_daily_report()
