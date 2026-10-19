import os
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import squarify  # 트리맵 시각화를 위해 필요

# ==========================================
# 한글 폰트 설정 (시스템에 설치된 NanumGothic 전역 적용)
# ==========================================
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
    change_col = next((c for c in ["등락률(%)", "등락률"] if c in df.columns), None)

    if name_col in df.columns and price_col in df.columns:
        # 데이터 정제 (숫자형 변환)
        df['cleaned_price'] = pd.to_numeric(df[price_col].astype(str).str.replace(",", ""), errors="coerce")
        df_clean = df.dropna(subset=['cleaned_price']).sort_values(by='cleaned_price', ascending=False).reset_index(drop=True)

        # ==========================================
        # 1. 기존 전체 정적 시각화 그래프 생성
        # ==========================================
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(df_clean[name_col], df_clean['cleaned_price'], color="skyblue")
        
        ax.set_title(f"[{trade_date}] 전자장비와기기 주요 종목 현재가 현황", fontsize=14)
        ax.set_ylabel("현재가 (원)", fontsize=12)
        plt.xticks(
            ticks=range(len(df_clean[name_col])), 
            labels=df_clean[name_col], 
            rotation=45, 
            ha="right"
        )
            
        plt.tight_layout()
        chart_filename = f"chart_{trade_date}.png"
        chart_path = report_dir / chart_filename
        fig.savefig(chart_path, dpi=150)
        plt.close(fig)
        print(f"기본 차트 생성 완료: {chart_path}")

        # ==========================================
        # 2. 상하위 집중 비교 차트 (Top N / Bottom N) 생성
        # ==========================================
        n = min(5, len(df_clean))
        top_n = df_clean.head(n)
        bottom_n = df_clean.tail(n).sort_values(by='cleaned_price', ascending=True)

        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        # 상위 종목 가로 바 그래프
        axes[0].barh(top_n[name_col], top_n['cleaned_price'], color="#4C72B0")
        axes[0].set_title(f"현재가 상위 Top {n} 종목", fontsize=13)
        axes[0].set_xlabel("현재가 (원)", fontsize=11)
        axes[0].invert_yaxis()

        # 하위 종목 가로 바 그래프
        axes[1].barh(bottom_n[name_col], bottom_n['cleaned_price'], color="#DD8452")
        axes[1].set_title(f"현재가 하위 Bottom {n} 종목", fontsize=13)
        axes[1].set_xlabel("현재가 (원)", fontsize=11)

        plt.tight_layout()
        top_bottom_filename = f"top_bottom_chart_{trade_date}.png"
        top_bottom_chart_path = report_dir / top_bottom_filename
        fig.savefig(top_bottom_chart_path, dpi=150)
        plt.close(fig)
        print(f"상하위 비교 차트 생성 완료: {top_bottom_chart_path}")

        # ==========================================
        # 3. 등락률(%) 기준 바 차트 생성 (추가)
        # ==========================================
        change_filename = None
        if change_col:
            fig, ax = plt.subplots(figsize=(10, 5))
            
            # 등락률 데이터 정제 (문자열 제거 및 숫자형 변환)
            df['cleaned_change'] = pd.to_numeric(
                df[change_col].astype(str).str.replace("%", "").str.replace("+", "").str.replace(",", ""), 
                errors="coerce"
            )
            df_change = df.dropna(subset=['cleaned_change']).sort_values(by='cleaned_change', ascending=True)
            
            # 상승(빨간색 계열), 하락(파란색 계열) 색상 자동 지정
            colors = ['#d9534f' if x > 0 else ('#5bc0de' if x < 0 else '#999999') for x in df_change['cleaned_change']]
            
            ax.barh(df_change[name_col], df_change['cleaned_change'], color=colors)
            ax.axvline(0, color='gray', linestyle='--', linewidth=0.8) # 기준선(0%) 표시
            
            ax.set_title(f"[{trade_date}] 종목별 등락률(%) 현황", fontsize=14)
            ax.set_xlabel("등락률 (%)", fontsize=12)
            
            plt.tight_layout()
            change_filename = f"change_chart_{trade_date}.png"
            change_path = report_dir / change_filename
            fig.savefig(change_path, dpi=150)
            plt.close(fig)
            print(f"등락률 차트 생성 완료: {change_path}")

        # ==========================================
        # 4. 트리맵 (Treemap) 차트 생성
        # ==========================================
        fig, ax = plt.subplots(figsize=(10, 6))
        try:
            labels = [f"{row[name_col]}\n({row['cleaned_price']:,}원)" for _, row in df_clean.iterrows()]
            squarify.plot(
                sizes=df_clean['cleaned_price'], 
                label=labels, 
                alpha=0.7, 
                ax=ax, 
                text_kwargs={'fontsize': 9}
            )
            ax.set_title(f"[{trade_date}] 종목별 현재가 규모 비중 (트리맵)", fontsize=14)
            ax.axis('off')
        except Exception as e:
            print(f"[경고] 트리맵 생성 중 오류 발생: {e}")

        plt.tight_layout()
        treemap_filename = f"treemap_{trade_date}.png"
        treemap_path = report_dir / treemap_filename
        fig.savefig(treemap_path, dpi=150)
        plt.close(fig)
        print(f"트리맵 차트 생성 완료: {treemap_path}")

    # ==========================================
    # 5. 마크다운 대시보드 리포트 작성
    # ==========================================
    md_path = report_dir / f"report_{trade_date}.md"
    
    md_content = f"# [{trade_date}] 전자장비와기기 업종 일일 대시보드 보고서\n\n"
    md_content += f"> 수집된 총 종목 수: **{len(df)}개** | 데이터 기준일: **{trade_date}**\n\n"
    
    md_content += "---\n\n"
    md_content += "## 📊 대시보드 시각화 요약\n\n"
    
    md_content += f"### 1. 전체 종목 현재가 현황\n"
    md_content += f"![일일 차트](./{chart_filename})\n\n"
    
    md_content += f"### 2. 상하위 집중 비교 분석 (Top / Bottom)\n"
    md_content += f"![상하위 비교 차트](./{top_bottom_filename})\n\n"
    
    if change_col and change_filename:
        md_content += f"### 3. 종목별 등락률(%) 현황\n"
        md_content += f"![등락률 차트](./{change_filename})\n\n"
        
    md_content += f"### 4. 종목별 규모 비중 (트리맵)\n"
    md_content += f"![트리맵 차트](./{treemap_filename})\n\n"
    
    md_content += "---\n\n"
    md_content += "## 📋 상세 종목 데이터 테이블\n\n"
    display_cols = [c for c in ["종목명", "종목코드", price_col, "등락률(%)", "거래량"] if c in df.columns]
    md_content += df[display_cols].to_markdown(index=False)

    md_path.write_text(md_content, encoding="utf-8")
    print(f"대시보드 보고서 생성 완료: {md_path}")

if __name__ == "__main__":
    generate_daily_report()
