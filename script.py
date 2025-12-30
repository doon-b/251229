import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import koreanize_matplotlib  # 한글 깨짐 방지 라이브러리

# 1. 데이터 로드 및 전처리 함수
@st.cache_data
def load_data():
    # 파일명은 실제 GitHub에 올린 이름과 정확히 일치해야 합니다.
    df = pd.read_csv('21118 정하린 프로젝트용 개인정보조회로그.csv', encoding='cp949')
    
    # 빈 행 제거 (104만 건 오류 방지)
    df = df.dropna(subset=['직원번호', '처리시각']) 
    
    # 데이터 타입 변환
    df['처리시각'] = pd.to_numeric(df['처리시각'], errors='coerce').fillna(0).astype(int)
    df['길이'] = pd.to_numeric(df['길이'], errors='coerce').fillna(0).astype(int)
    df['직원번호'] = df['직원번호'].astype(str)
    
    return df

# 2. 메인 분석 함수
def run_analysis():
    st.set_page_config(page_title="개인정보 유출 예방 시스템", layout="wide")
    st.title("🛡️ 개인정보 보호: 이상 징후 선제적 탐지기")
    
    df = load_data()

    # --- [시나리오] 위험도 스코어링 로직 ---
    def calculate_risk(row):
        score = 0
        if row['마스크해제여부'] == 'Y': score += 50
        if row['야간 근무 여부'] == '보안취약(야간)': score += 30
        if row['길이'] >= 300: score += 20
        return score

    df['총_위험점수'] = df.apply(calculate_risk, axis=1)

    # --- [개선] 사이드바: 분석 모드 선택 (라디오 버튼) ---
    st.sidebar.header("🎯 집중 점검 시나리오")
    mode = st.sidebar.radio(
        "분석할 시나리오를 선택하세요",
        ["전체 로그 보기", "🚨 즉시 점검 대상", "📂 대량조회 의심", "🌙 야간 접근 로그"]
    )

    # 선택된 모드에 따른 필터링 및 정렬 기준 설정
    if mode == "🚨 즉시 점검 대상":
        df_display = df[df['총_위험점수'] >= 80]
        sort_col = '총_위험점수'
        description = "⚠️ **위험 점수가 80점 이상**인 고위험군입니다. 즉각적인 확인이 필요합니다."
    elif mode == "📂 대량조회 의심":
        df_display = df[df['길이'] >= 300]
        sort_col = '길이'
        description = "📂 **조회 조건 길이**가 비정상적으로 길어 대량 추출이 의심되는 로그입니다."
    elif mode == "🌙 야간 접근 로그":
        df_display = df[df['야간 근무 여부'] == '보안취약(야간)']
        sort_col = '처리시각'
        description = "🌙 **업무 외 시간(야간)**에 접근한 기록입니다. 마스크 해제 여부를 함께 확인하세요."
    else:
        df_display = df
        sort_col = '총_위험점수'
        description = "📊 시스템에서 수집된 모든 로그의 전반적인 상태입니다."

    # --- 메인 상단 지표 (Metric) ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("현재 모드 로그 수", f"{len(df_display)}건")
    with col2:
        high_risk_sum = len(df[df['총_위험점수'] >= 80])
        st.metric("🚨 전체 고위험", f"{high_risk_sum}건")
    with col3:
        massive_sum = len(df[df['길이'] >= 300])
        st.metric("📂 전체 대량조회", f"{massive_sum}건")
    with col4:
        night_sum = len(df[df['야간 근무 여부'] == '보안취약(야간)'])
        st.metric("🌙 전체 야간접근", f"{night_sum}건")

    st.divider()

    # --- 시각화 영역 ---
    left_col, right_col = st.columns(2)
    with left_col:
        st.subheader("📍 시간대별 위험 발생 분포")
        risk_by_time = df_display.groupby('처리시각')['총_위험점수'].mean()
        fig, ax = plt.subplots(figsize=(10, 5))
        risk_by_time.plot(kind='bar', color='salmon', ax=ax)
        ax.set_ylabel("평균 위험 점수")
        st.pyplot(fig)

    with right_col:
        st.subheader("👤 직원별 누적 위험도")
        user_risk = df_display.groupby('직원번호')['총_위험점수'].sum().sort_values(ascending=False).head(5)
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        user_risk.plot(kind='barh', color='orange', ax=ax2)
        ax2.set_xlabel("누적 위험 점수")
        st.pyplot(fig2)

    st.divider()

    # --- [핵심 기능] 상세 리스트 및 색상 강조 ---
    st.subheader(f"📋 {mode} 상세 분석 리포트")
    st.markdown(description)

    # 데이터 정렬: 선택한 모드의 핵심 컬럼이 위로 오게 함
    df_sorted = df_display[['직원번호', '처리시각', '업무 분류', '화면명', '야간 근무 여부', '마스크해제여부', '길이', '총_위험점수']].sort_values(by=sort_col, ascending=False)

    # 특정 컬럼 색상 강조 함수
    def highlight_cols(x):
        df_style = pd.DataFrame('', index=x.index, columns=x.columns)
        if mode == "🚨 즉시 점검 대상":
            df_style['총_위험점수'] = 'background-color: #fc4242' # 빨강
        elif mode == "📂 대량조회 의심":
            df_style['길이'] = 'background-color: #fc4242' 
        elif mode == "🌙 야간 접근 로그":
            df_style['야간 근무 여부'] = 'background-color: #fc4242' 
        return df_style

    # 표 출력
    st.dataframe(df_sorted.style.apply(highlight_cols, axis=None), use_container_width=True)

    # CSV 다운로드 버튼
    csv = df_sorted.to_csv(index=False).encode('cp949')
    st.download_button(label="📥 분석 결과 보고서 다운로드", data=csv, file_name=f'{mode}_report.csv', mime='text/csv')

if __name__ == "__main__":
    run_analysis()




