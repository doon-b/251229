import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 한글 폰트 설정 (Windows 기준, Mac은 'AppleGothic' 사용)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 1. 데이터 로드 및 기초 전처리
@st.cache_data
def load_data():
    # 파일명을 본인의 파일명으로 수정하세요.
    df = pd.read_csv('21118 정하린 프로젝트용 개인정보조회로그.csv', encoding='utf-8')
    # 전처리 과정에서 생긴 공백 열 제거
    df = df.dropna(axis=1, how='all')
    return df

def run_analysis():
    st.set_page_config(page_title="개인정보 보안 이상징후 탐지기", layout="wide")
    
    st.title("🛡️ 사전 예방형 로그 분석 시스템")
    st.markdown("""
    **SKT 개인정보 유출 사고**와 같은 비극을 방지하기 위해, 
    단순 적발이 아닌 **'위험 전조 현상'**을 탐지하는 대시보드입니다.
    """)

    df = load_data()

    # --- 사이드바: 필터링 ---
    st.sidebar.header("🔍 분석 필터")
    target_dept = st.sidebar.multiselect("분석 대상 업무 영역", options=df['업무 분류'].unique(), default=df['업무 분류'].unique())
    df_filtered = df[df['업무 분류'].isin(target_dept)]

    # --- 핵심 지표 (Metric) ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("전체 로그 수", f"{len(df_filtered)}건")
    with col2:
        high_risk_cnt = len(df_filtered[df_filtered['위험지수'].str.contains('1단계|심각', na=False)])
        st.metric("⚠️ 고위험 로그", f"{high_risk_cnt}건", delta="점검 필요", delta_color="inverse")
    with col3:
        night_logs = len(df_filtered[df_filtered['야간 근무 여부'] == '보안취약(야간)'])
        st.metric("🌙 야간 조회 건수", f"{night_logs}건")

    st.divider()

    # --- 핵심 기능 1: 시간대별 위험도 시각화 ---
    st.subheader("1. 시간대별 보안 취약 지수")
    time_series = df_filtered.groupby('처리시각').size()
    
    fig, ax = plt.subplots(figsize=(10, 4))
    time_series.plot(kind='line', marker='o', color='red', ax=ax)
    ax.set_title("시간대별 접근 빈도 (야간 집중 모니터링)")
    ax.set_xlabel("시간 (Hour)")
    ax.set_ylabel("로그 발생 건수")
    st.pyplot(fig)

    # --- 핵심 기능 2: 위험 인물 TOP 5 (위험 누적) ---
    st.subheader("2. 사전 주의 대상자 (위험 지수 누적 TOP 5)")
    # 위험지수를 점수로 변환 (심각=100, 주의=50, 보통=0)
    risk_map = {'1단계_심각': 100, '2단계_주의': 50, '보통': 0}
    df_filtered['Risk_Score'] = df_filtered['위험지수'].map(risk_map).fillna(0)
    
    user_risk = df_filtered.groupby('직원번호')['Risk_Score'].sum().sort_values(ascending=False).head(5)
    
    col_chart, col_data = st.columns([2, 1])
    with col_chart:
        fig2, ax2 = plt.subplots()
        user_risk.plot(kind='barh', color='orange', ax=ax2)
        ax2.set_title("직원별 누적 위험 점수")
        st.pyplot(fig2)
    with col_data:
        st.write("📊 상세 수치")
        st.dataframe(user_risk)

    # --- 핵심 기능 3: 대량 조회 의심 사례 (LEN 기반) ---
    st.subheader("3. 대량 정보 유출 의심 로그 (조회 조건 길이 기준)")
    threshold = st.slider("조회 조건 길이 임계치 설정", 100, 1000, 300)
    massive_logs = df_filtered[df_filtered['길이'] >= threshold][['직원번호', '화면명', '길이', '고객ID', '위험지수']]
    st.warning(f"조회 조건이 {threshold}자 이상인 로그는 대량 유출 시도로 의심될 수 있습니다.")
    st.table(massive_logs)

    # --- 마침표: 분석가 의견 ---
    st.info("""
    **💡 분석가 코멘트:** 현재 특정 직원에게 야간 시간대 마스크 해제가 집중되고 있습니다. 
    해당 직원이 업무 범위를 벗어난 '고객ID'를 반복 조회하는지 추가 조사가 필요합니다.
    """)

if __name__ == "__main__":
    run_analysis()
