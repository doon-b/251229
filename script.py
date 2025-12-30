import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import koreanize-matplotlib

plt.rcParams['axes.unicode_minus'] = False


@st.cache_data
def load_data():
    # 1. 인코딩 해결 및 데이터 로드
    df = pd.read_csv('21118 정하린 프로젝트용 개인정보조회로그.csv', encoding='cp949')

    # 2. 빈 행(104만 건 에러) 방지: 핵심 데이터가 없는 행은 즉시 삭제
    df = df.dropna(subset=['직원번호', '처리시각'])

    # 3. 데이터 타입 변환 (분석 최적화)
    df['처리시각'] = pd.to_numeric(df['처리시각'], errors='coerce')
    df['길이'] = pd.to_numeric(df['길이'], errors='coerce').fillna(0)

    return df


def run_analysis():
    st.set_page_config(page_title="개인정보 유출 예방 시스템", layout="wide")
    st.title("🛡️ 개인정보 보호: 이상 징후 선제적 탐지기")

    df = load_data()

    # --- [시나리오 1] 위험도 스코어링 로직 구축 ---
    # 범죄 이용 가능성이 높은 '마스크 해제 + 특정 화면' 조합 가중치 부여
    def calculate_risk(row):
        score = 0
        # 마스크 해제 시 기본 50점
        if row['마스크해제여부'] == 'Y': score += 50
        # 야간 시간일 경우 30점 추가
        if row['야간 근무 여부'] == '보안취약(야간)': score += 30
        # 조회 조건이 대량(300자 이상)일 경우 20점 추가
        if row['길이'] >= 300: score += 20
        return score

    df['총_위험점수'] = df.apply(calculate_risk, axis=1)

    # --- [신규 추가] 사이드바 위험 시나리오 선택 필터 ---
    st.sidebar.header("🎯 집중 점검 시나리오 선택")

    # 체크박스를 통해 중복 선택 가능하도록 설정
    show_high_risk = st.sidebar.checkbox("🚨 즉시 점검 대상 (위험점수 80↑)", value=True)
    show_massive = st.sidebar.checkbox("📂 대량조회 의심 (길이 300↑)")
    show_night = st.sidebar.checkbox("🌙 야간 접근 로그 (보안취약시간)")

    # 필터링 조건 설정
    filters = []
    if show_high_risk:
        filters.append(df['총_위험점수'] >= 80)
    if show_massive:
        filters.append(df['길이'] >= 300)
    if show_night:
        filters.append(df['야간 근무 여부'] == '보안취약(야간)')

    # 선택된 조건이 있으면 합치고(OR 연산), 없으면 전체 데이터 표시
    if filters:
        df_display = df[pd.concat(filters, axis=1).any(axis=1)]
    else:
        df_display = df

    # --- 메인 대시보드 지표 ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("실제 분석 로그 수", f"{len(df)}건")
    with col2:
        high_risk = df[df['총_위험점수'] >= 80]
        st.metric("🚨 즉시 점검 대상", f"{len(high_risk)}건")
    with col3:
        scraping_suspect = len(df[df['길이'] >= 500])
        st.metric("📂 대량조회 의심", f"{scraping_suspect}건")
    with col4:
        night_access = len(df[df['야간 근무 여부'] == '보안취약(야간)'])
        st.metric("🌙 야간 접근", f"{night_access}건")

    st.divider()

    # --- [시나리오 2 & 3] 시각화 분석 ---
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("📍 시간대별 위험 발생 분포")
        # 야간 시간 모니터링 시각화
        risk_by_time = df.groupby('처리시각')['총_위험점수'].mean()
        fig, ax = plt.subplots()
        risk_by_time.plot(kind='bar', color='salmon', ax=ax)
        ax.set_title("시간대별 평균 위험도 (18시 이후 주의)")
        st.pyplot(fig)

    with right_col:
        st.subheader("👤 직무 외 대량조회 의심자 (TOP 5)")
        # 스크래핑 행위 탐지: 특정 직원의 조회 길이 합계
        user_scraping = df.groupby('직원번호')['길이'].sum().sort_values(ascending=False).head(5)
        fig2, ax2 = plt.subplots()
        user_scraping.plot(kind='barh', color='orange', ax=ax2)
        ax2.set_title("직원별 누적 조회 데이터 양")
        st.pyplot(fig2)

    st.divider()

    # --- [시나리오 4 & 5] 위험 리포트 및 상세 리스트 ---
    st.subheader("📋 고위험 이상 징후 상세 리포트")
    st.info("이 리스트는 '마스크 해제'와 '야간 시간'이 결합된 사고 전조 현상을 우선적으로 보여줍니다.")

    # 보고서용 필터링
    report_df = df[df['총_위험점수'] >= 50].sort_values(by='총_위험점수', ascending=False)

    # 보기 편하게 컬럼 정리
    st.dataframe(report_df[['직원번호', '업무 분류', '화면명', '야간 근무 여부', '마스크해제여부', '길이', '총_위험점수']])

    # --- 예측형 경고 문구 ---
    if len(high_risk) > 0:
        st.error(f"⚠️ 경고: 현재 {len(high_risk)}건의 고위험 로그가 탐지되었습니다. 특히 야간 시간대 마스크 해제 조회가 반복되고 있어 실제 사고로 이어질 가능성이 매우 높습니다.")
    else:
        st.success("✅ 현재 특이 지점은 없으나 지속적인 모니터링이 필요합니다.")


if __name__ == "__main__":

    run_analysis()

