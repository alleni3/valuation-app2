import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- DB 설정 및 테이블 생성 ---
def init_db():
    conn = sqlite3.connect('valuation_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS evaluations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  reg_date TEXT,
                  ref_date TEXT,
                  land_addr TEXT, land_area REAL, land_price INTEGER, land_total INTEGER,
                  b_addr TEXT, b_re_cost INTEGER, b_area REAL, b_total_life INTEGER, b_passed INTEGER, b_total INTEGER,
                  u_addr TEXT, u_area REAL, u_price INTEGER, u_total INTEGER,
                  grand_total INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# --- 페이지 설정 ---
st.set_page_config(page_title="탁상감정 기록 관리 시스템", layout="wide")

# --- 사이드바: 기록 목록 조회 ---
st.sidebar.header("📁 탁상감정 기록 목록")

def get_list():
    conn = sqlite3.connect('valuation_data.db')
    df = pd.read_sql_query("SELECT id, reg_date, land_addr, grand_total FROM evaluations ORDER BY id DESC", conn)
    conn.close()
    return df

history_df = get_list()

# 목록에서 선택
selected_id = None
if not history_df.empty:
    # 목록 표시용 포맷팅
    list_options = history_df.apply(lambda x: f"[{x['id']}] {x['reg_date']} | {x['land_addr'][:15]}...", axis=1).tolist()
    selected_option = st.sidebar.selectbox("과거 기록 불러오기", ["새로 작성"] + list_options)
    
    if selected_option != "새로 작성":
        selected_id = int(selected_option.split(']')[0][1:])

# --- 데이터 불러오기 로직 ---
load_data = {}
if selected_id:
    conn = sqlite3.connect('valuation_data.db')
    row = pd.read_sql_query(f"SELECT * FROM evaluations WHERE id={selected_id}", conn).iloc[0]
    conn.close()
    load_data = row.to_dict()

# --- 메인 화면 ---
st.title("🏗️ 감정평가 탁상감정 시스템")

# --- 0. 기본 정보 ---
st.sidebar.divider()
ref_date = st.sidebar.date_input("기준시점", 
                               datetime.strptime(load_data['ref_date'], '%Y-%m-%d') if selected_id else datetime.now())

# --- 1. 토지 평가 ---
with st.expander("1. 토지 평가", expanded=True):
    l_addr = st.text_input("토지 소재지", value=load_data.get('land_addr', ""), key="l_addr")
    col1, col2, col3 = st.columns(3)
    l_area = col1.number_input("적용면적 (㎡)", value=float(load_data.get('land_area', 0.0)), step=0.1)
    l_price = col2.number_input("토지 단가 (원/㎡)", value=int(load_data.get('land_price', 0)), step=1000)
    l_total = l_area * l_price
    col3.metric("토지 예상가", f"{l_total:,.0f} 원")

# --- 2. 건물 평가 ---
with st.expander("2. 건물 평가 (원가법)", expanded=True):
    b_addr = st.text_input("건물 소재지", value=load_data.get('b_addr', ""), key="b_addr")
    c1, c2, c3, c4 = st.columns(4)
    b_re_cost = c1.number_input("재조달원가 (원/㎡)", value=int(load_data.get('b_re_cost', 0)))
    b_area = c1.number_input("건물 면적 (㎡)", value=float(load_data.get('b_area', 0.0)))
    b_life = c2.number_input("내용연수 (년)", value=int(load_data.get('b_total_life', 40)))
    b_passed = c2.number_input("적용 경과연수 (년)", value=int(load_data.get('b_passed', 0)))
    
    b_unit_price = int(b_re_cost * (1 - b_passed/b_life)) if b_life > 0 else 0
    c3.write(f"**건물 단가:** {b_unit_price:,.0f} 원")
    b_total = b_unit_price * b_area
    c4.metric("건물 예상가", f"{b_total:,.0f} 원")

# --- 3. 구분건물 평가 ---
with st.expander("3. 구분건물 평가", expanded=True):
    u_addr = st.text_input("구분건물 소재지", value=load_data.get('u_addr', ""), key="u_addr")
    u1, u2, u3 = st.columns(3)
    u_area = u1.number_input("전유면적 (㎡)", value=float(load_data.get('u_area', 0.0)))
    u_price = u2.number_input("구분건물 단가 (원/㎡)", value=int(load_data.get('u_price', 0)))
    u_total = u_area * u_price
    u3.metric("구분건물 예상가", f"{u_total:,.0f} 원")

# --- 저장 기능 ---
grand_total = l_total + b_total + u_total
st.sidebar.subheader(f"총 예상가: {grand_total:,.0f} 원")

if st.sidebar.button("💾 탁상감정 결과 저장/완료"):
    conn = sqlite3.connect('valuation_data.db')
    c = conn.cursor()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    c.execute('''INSERT INTO evaluations (reg_date, ref_date, land_addr, land_area, land_price, land_total, 
                 b_addr, b_re_cost, b_area, b_total_life, b_passed, b_total, u_addr, u_area, u_price, u_total, grand_total)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (now_str, ref_date.strftime('%Y-%m-%d'), l_addr, l_area, l_price, l_total, 
               b_addr, b_re_cost, b_area, b_life, b_passed, b_total, u_addr, u_area, u_price, u_total, grand_total))
    conn.commit()
    conn.close()
    st.sidebar.success("성공적으로 저장되었습니다!")
    st.rerun() # 목록 새로고침