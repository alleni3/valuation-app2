import streamlit as st
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="감정평가 탁상감정 시스템", layout="wide")

st.title("🏗️ 감정평가 탁상감정 및 견적 관리")
st.info("각 항목을 입력하면 실시간으로 예상가가 산출됩니다.")

# --- 1. 토지 평가 섹션 ---
st.header("1. 토지 평가")
col1, col2, col3 = st.columns(3)
with col1:
    land_area = st.number_input("적용면적 (㎡)", value=0.0, step=0.1, key="land_area")
with col2:
    land_unit_price = st.number_input("토지 단가 (원/㎡)", value=0, step=1000, key="land_price")
with col3:
    land_total = land_area * land_unit_price
    st.metric("토지 예상가", f"{land_total:,.0f} 원")

st.divider()

# --- 2. 건물 평가 섹션 (원가법) ---
st.header("2. 건물 평가 (원가법)")
c1, c2, c3, c4 = st.columns(4)
with c1:
    b_re_cost = st.number_input("재조달원가 (원/㎡)", value=0, step=1000)
    b_area = st.number_input("건물 면적 (㎡)", value=0.0, step=0.1)
with c2:
    b_total_life = st.number_input("내용연수 (년)", value=40, step=1)
    b_passed_years = st.number_input("적용 경과연수 (년)", value=0, step=1)
with c3:
    # 건물 단가 계산: 재조달원가 * (1 - 경과/내용)
    if b_total_life > 0:
        depreciation = 1 - (b_passed_years / b_total_life)
        b_unit_price = int(b_re_cost * max(depreciation, 0))
    else:
        b_unit_price = 0
    st.write(f"**건물 단가:** {b_unit_price:,.0f} 원")
with c4:
    b_total = b_unit_price * b_area
    st.metric("건물 예상가", f"{b_total:,.0f} 원")

st.divider()

# --- 3. 구분건물 평가 섹션 ---
st.header("3. 구분건물 평가")
u1, u2, u3 = st.columns(3)
with u1:
    u_area = st.number_input("전유면적 (㎡)", value=0.0, step=0.1)
with u2:
    u_unit_price = st.number_input("구분건물 단가 (원/㎡)", value=0, step=1000)
with u3:
    u_total = u_area * u_unit_price
    st.metric("구분건물 예상가", f"{u_total:,.0f} 원")

# --- 최종 요약 ---
st.sidebar.header("📝 견적 요약")
grand_total = land_total + b_total + u_total
st.sidebar.subheader(f"총 예상가: {grand_total:,.0f} 원")

if st.sidebar.button("견적서 생성 (준비중)"):
    st.sidebar.success("PDF 생성 기능으로 연결됩니다.")