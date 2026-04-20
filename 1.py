import streamlit as st
import pandas as pd
import sqlite3
import requests
from datetime import datetime
import io

# ─────────────────────────────────────────
# 설정
# ─────────────────────────────────────────
# 도로명주소 개발자센터 (juso.go.kr) API 키
# 발급: https://www.juso.go.kr/addrlink/devAddrLinkRequestGuide.do
# 무료 / 회원가입 없이 개발용 키 즉시 발급 가능
JUSO_API_KEY = st.secrets.get("JUSO_API_KEY", "devU01TX0FVVEgyMDI1MDQyMDE0MjgxNTExNTAxNTQ=")

# ─────────────────────────────────────────
# 법정동 검색 (juso.go.kr 법정동코드 API)
# ─────────────────────────────────────────
def search_beopjeongdong(keyword: str):
    """
    행정안전부 주소기반산업지원서비스 법정동코드 검색 API
    endpoint: https://business.juso.go.kr/addrlink/addrLinkApiJsonp.do
    반환: list of dict {법정동명, 시도, 시군구, 읍면동, 법정동코드}
    """
    if not keyword or len(keyword.strip()) < 1:
        return []
    try:
        url = "https://business.juso.go.kr/addrlink/addrLinkApi.do"
        params = {
            "currentPage": 1,
            "countPerPage": 30,
            "keyword": keyword.strip(),
            "confmKey": JUSO_API_KEY,
            "resultType": "json",
            "hstryYn": "N",
            "addrDetailYn": "N",
        }
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        results = data.get("results", {}).get("juso", []) or []

        seen = set()
        parsed = []
        for item in results:
            # 법정동 분리
            addr_parts = item.get("addrDetail", "") or ""
            full = item.get("roadAddr", "") or item.get("jibunAddr", "") or ""

            si_do      = item.get("siNm", "").strip()
            si_gun_gu  = item.get("sggNm", "").strip()
            eup_myeon  = item.get("emdNm", "").strip()

            if not (si_do and si_gun_gu and eup_myeon):
                continue
            key = (si_do, si_gun_gu, eup_myeon)
            if key in seen:
                continue
            seen.add(key)
            parsed.append({
                "label": f"{si_do} {si_gun_gu} {eup_myeon}",
                "시도": si_do,
                "시군구": si_gun_gu,
                "읍면동": eup_myeon,
            })
        return parsed

    except Exception as e:
        return []


def search_beopjeongdong_v2(keyword: str):
    """
    법정동코드 전용 API (행정안전부 행정표준코드관리시스템)
    endpoint: https://www.code.go.kr/stdcode/regCodeL.do (HTML) →
    대신 공공데이터포털 법정동 API 사용
    """
    if not keyword or len(keyword.strip()) < 1:
        return []
    try:
        # 공공데이터포털 법정동코드 API (자동승인 / 별도 key 불필요 테스트)
        url = "https://grpc-proxy-server-mkvo6j4wsq-du.a.run.app/v1/regcodes"
        params = {
            "regcode_pattern": f"*{keyword.strip()}*",
            "is_ignore_zero": "true"
        }
        resp = requests.get(url, params=params, timeout=5)
        items = resp.json().get("regcodes", [])

        seen = set()
        parsed = []
        for item in items:
            name = item.get("name", "").strip()
            parts = name.split()
            if len(parts) < 3:
                continue
            si_do     = parts[0]
            si_gun_gu = parts[1]
            eup_myeon = " ".join(parts[2:])
            key = (si_do, si_gun_gu, eup_myeon)
            if key in seen:
                continue
            seen.add(key)
            parsed.append({
                "label": f"{si_do} {si_gun_gu} {eup_myeon}",
                "시도": si_do,
                "시군구": si_gun_gu,
                "읍면동": eup_myeon,
                "코드": item.get("code", ""),
            })
        return parsed[:40]
    except Exception:
        return []


# ─────────────────────────────────────────
# DB 초기화
# ─────────────────────────────────────────
def init_db():
    conn = sqlite3.connect('valuation_data.db')
    c = conn.cursor()
    try:
        c.execute("SELECT si_do FROM evaluations LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("DROP TABLE IF EXISTS evaluations")
    c.execute('''CREATE TABLE IF NOT EXISTS evaluations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  reg_date TEXT, ref_date TEXT,
                  client_name TEXT, purpose TEXT, evaluator TEXT, memo TEXT,
                  si_do TEXT, si_gun_gu TEXT, eup_myeon_dong TEXT,
                  bun_type TEXT, main_bun TEXT, sub_bun TEXT,
                  land_area REAL, land_price INTEGER, land_total INTEGER,
                  b_addr TEXT, b_re_cost INTEGER, b_area REAL,
                  b_total_life INTEGER, b_passed INTEGER, b_total INTEGER,
                  u_addr TEXT, u_area REAL, u_price INTEGER, u_total INTEGER,
                  grand_total INTEGER)''')
    conn.commit(); conn.close()

init_db()

# ─────────────────────────────────────────
# CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=IBM+Plex+Mono:wght@400;600&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.main-header {
    background: linear-gradient(135deg, #1a2332 0%, #2d3f55 100%);
    color: white; padding: 1.5rem 2rem; border-radius: 12px;
    margin-bottom: 1.5rem; display: flex; align-items: center; gap: 1rem;
}
.main-header h1 { margin: 0; font-size: 1.6rem; font-weight: 700; }
.main-header p  { margin: 0.2rem 0 0; opacity: 0.7; font-size: 0.85rem; }
.metric-card {
    background: white; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 1rem 1.2rem; text-align: center;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}
.metric-card .label { font-size: 0.75rem; color: #64748b; margin-bottom: 0.3rem; }
.metric-card .value { font-family: 'IBM Plex Mono', monospace; font-size: 1.1rem;
    font-weight: 600; color: #1e3a5f; }
.metric-card .value.total { color: #c0392b; font-size: 1.3rem; }
.section-header {
    background: #f0f4f8; border-left: 4px solid #2d6a9f;
    padding: 0.5rem 1rem; border-radius: 0 8px 8px 0;
    font-weight: 600; font-size: 0.95rem; color: #1a2332; margin-bottom: 1rem;
}
.addr-preview {
    background: #e8f4fd; border: 1.5px solid #2d6a9f; border-radius: 8px;
    padding: 0.6rem 1rem; font-size: 0.92rem; margin: 0.4rem 0 0.8rem;
}
.tag-chip {
    display: inline-block; background: #e0f0ff; color: #1a6bcc;
    border-radius: 20px; padding: 0.15rem 0.7rem;
    font-size: 0.75rem; font-weight: 500; margin: 0.15rem;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# DB 유틸
# ─────────────────────────────────────────
def get_conn(): return sqlite3.connect('valuation_data.db')

def get_list(search="", si_do_filter="전체", date_from=None, date_to=None):
    conn = get_conn()
    query = """SELECT id, reg_date, ref_date, client_name, purpose,
                      si_do, si_gun_gu, eup_myeon_dong,
                      main_bun, sub_bun, grand_total
               FROM evaluations WHERE 1=1"""
    params = []
    if search:
        query += " AND (si_do||si_gun_gu||eup_myeon_dong||main_bun||client_name LIKE ?)"
        params.append(f"%{search}%")
    if si_do_filter != "전체":
        query += " AND si_do = ?"; params.append(si_do_filter)
    if date_from:
        query += " AND ref_date >= ?"; params.append(str(date_from))
    if date_to:
        query += " AND ref_date <= ?"; params.append(str(date_to))
    query += " ORDER BY id DESC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close(); return df

def delete_entry(eid):
    conn = get_conn(); conn.cursor().execute("DELETE FROM evaluations WHERE id=?", (eid,))
    conn.commit(); conn.close()

def update_entry(eid, data):
    conn = get_conn(); c = conn.cursor()
    c.execute('''UPDATE evaluations SET
                 ref_date=?, client_name=?, purpose=?, evaluator=?, memo=?,
                 si_do=?, si_gun_gu=?, eup_myeon_dong=?, bun_type=?,
                 main_bun=?, sub_bun=?,
                 land_area=?, land_price=?, land_total=?,
                 b_addr=?, b_re_cost=?, b_area=?, b_total_life=?, b_passed=?, b_total=?,
                 u_addr=?, u_area=?, u_price=?, u_total=?, grand_total=?
                 WHERE id=?''', (*data, eid))
    conn.commit(); conn.close()

def insert_entry(data):
    conn = get_conn(); c = conn.cursor()
    c.execute('''INSERT INTO evaluations
                 (reg_date, ref_date, client_name, purpose, evaluator, memo,
                  si_do, si_gun_gu, eup_myeon_dong, bun_type, main_bun, sub_bun,
                  land_area, land_price, land_total,
                  b_addr, b_re_cost, b_area, b_total_life, b_passed, b_total,
                  u_addr, u_area, u_price, u_total, grand_total)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', data)
    conn.commit(); conn.close()

def to_excel(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='탁상감정목록')
    return buf.getvalue()

# ─────────────────────────────────────────
# 법정동 검색 위젯
# ─────────────────────────────────────────
def address_search_widget(load_data):
    si_do          = str(load_data.get('si_do', '') or '')
    si_gun_gu      = str(load_data.get('si_gun_gu', '') or '')
    eup_myeon_dong = str(load_data.get('eup_myeon_dong', '') or '')

    st.markdown('<div class="section-header">📍 소재지 — 법정동 검색</div>', unsafe_allow_html=True)

    # 검색창
    col_kw, col_btn = st.columns([4, 1])
    kw = col_kw.text_input(
        "법정동 검색",
        placeholder="예) 역삼동, 분당, 해운대, 송도동",
        key="addr_kw",
        label_visibility="collapsed"
    )
    search_clicked = col_btn.button("🔍 검색", use_container_width=True, key="addr_search_btn")

    # 검색 실행
    if search_clicked and kw.strip():
        with st.spinner("법정동 검색 중..."):
            results = search_beopjeongdong_v2(kw.strip())
            if not results:
                results = search_beopjeongdong(kw.strip())
        st.session_state["addr_results"] = results
        st.session_state["addr_selected_idx"] = 0

    results = st.session_state.get("addr_results", [])

    if results:
        options = [r["label"] for r in results]

        # 수정 모드에서 기존값 기본 선택
        current = f"{si_do} {si_gun_gu} {eup_myeon_dong}".strip()
        default_idx = 0
        for i, o in enumerate(options):
            if o.strip() == current:
                default_idx = i; break

        chosen_label = st.selectbox(
            f"검색 결과 ({len(results)}건) — 선택하세요",
            options,
            index=default_idx,
            key="addr_select"
        )
        chosen = next((r for r in results if r["label"] == chosen_label), None)
        if chosen:
            si_do          = chosen["시도"]
            si_gun_gu      = chosen["시군구"]
            eup_myeon_dong = chosen["읍면동"]

    elif search_clicked and kw.strip():
        st.warning("검색 결과가 없습니다. 다른 키워드로 다시 검색해 보세요.")

    # 현재 선택 주소 미리보기
    if si_do:
        full = " ".join(filter(None, [si_do, si_gun_gu, eup_myeon_dong]))
        st.markdown(
            f'<div class="addr-preview">📌 <strong>소재지:</strong> &nbsp;{full}</div>',
            unsafe_allow_html=True
        )
    else:
        st.caption("법정동명을 검색하면 시도/시군구/읍면동이 자동으로 입력됩니다.")

    return si_do, si_gun_gu, eup_myeon_dong


# ─────────────────────────────────────────
# 앱 헤더
# ─────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <span style="font-size:2rem">🏗️</span>
  <div>
    <h1>탁상감정 기록 관리 시스템</h1>
    <p>부동산 감정평가 탁상감정 전산화 · 입력 / 조회 / 수정 / 출력</p>
  </div>
</div>
""", unsafe_allow_html=True)

tab_input, tab_list, tab_report = st.tabs(["✏️ 신규 / 수정 입력", "📋 기록 조회 · 검색", "📄 보고서 출력"])

# ═══════════════════════════════════════
# TAB 1: 입력 / 수정
# ═══════════════════════════════════════
with tab_input:
    edit_id = st.session_state.get("edit_id", None)
    load_data = {}
    if edit_id:
        conn = get_conn()
        row = pd.read_sql_query(f"SELECT * FROM evaluations WHERE id={edit_id}", conn)
        conn.close()
        if not row.empty:
            load_data = row.iloc[0].to_dict()
        st.info(f"📝 수정 모드 — ID #{edit_id}")
        if st.button("➕ 새로 작성"):
            st.session_state.edit_id = None
            st.session_state.pop("addr_results", None)
            st.rerun()

    # ── 0. 기본 정보 ──
    st.markdown('<div class="section-header">📌 기본 정보</div>', unsafe_allow_html=True)
    r0c1, r0c2, r0c3, r0c4 = st.columns(4)
    ref_date = r0c1.date_input("기준시점",
        datetime.strptime(load_data['ref_date'], '%Y-%m-%d') if load_data.get('ref_date') else datetime.now())
    client_name = r0c2.text_input("의뢰인", value=load_data.get('client_name', ''))
    purpose_opts = ["담보","매매참고","소송","상속/증여","기타"]
    purpose = r0c3.selectbox("감정목적", purpose_opts,
        index=purpose_opts.index(load_data['purpose']) if load_data.get('purpose') in purpose_opts else 0)
    evaluator = r0c4.text_input("담당자", value=load_data.get('evaluator', ''))
    memo = st.text_area("메모 / 특이사항", value=load_data.get('memo', ''), height=60)

    # ── 1. 토지 ──
    st.markdown('<div class="section-header">🌏 1. 토지 평가</div>', unsafe_allow_html=True)

    si_do, si_gun_gu, eup_myeon_dong = address_search_widget(load_data)

    st.write("")
    a4, a5, a6 = st.columns(3)
    bun_type_opts = ["대지", "산"]
    bun_type = a4.selectbox("지번구분", bun_type_opts,
        index=bun_type_opts.index(load_data['bun_type']) if load_data.get('bun_type') in bun_type_opts else 0)
    main_bun = a5.text_input("본번", value=str(load_data.get('main_bun', '') or ''))
    sub_bun  = a6.text_input("부번", value=str(load_data.get('sub_bun', '0') or '0'))

    lc1, lc2, lc3 = st.columns(3)
    l_area  = lc1.number_input("적용면적 (㎡)",    value=float(load_data.get('land_area', 0.0) or 0), step=0.1)
    l_price = lc2.number_input("토지 단가 (원/㎡)", value=int(load_data.get('land_price', 0) or 0),   step=1000)
    l_total = l_area * l_price
    lc3.markdown(f'<div class="metric-card"><div class="label">토지 예상가</div><div class="value">₩ {l_total:,.0f}</div></div>', unsafe_allow_html=True)

    # ── 2. 건물 ──
    st.markdown('<div class="section-header">🏢 2. 건물 평가 (원가법)</div>', unsafe_allow_html=True)
    b_addr    = st.text_input("건물 비고(명칭 등)", value=str(load_data.get('b_addr', '') or ''))
    bc1, bc2, bc3, bc4 = st.columns(4)
    b_re_cost = bc1.number_input("재조달원가 (원/㎡)", value=int(load_data.get('b_re_cost', 0) or 0))
    b_area    = bc2.number_input("건물 면적 (㎡)",     value=float(load_data.get('b_area', 0.0) or 0))
    b_life    = bc3.number_input("내용연수 (년)",       value=int(load_data.get('b_total_life', 40) or 40))
    b_passed  = bc4.number_input("경과연수 (년)",       value=int(load_data.get('b_passed', 0) or 0))
    b_unit    = int(b_re_cost * (1 - b_passed / b_life)) if b_life > 0 else 0
    b_total   = b_unit * b_area
    bm1, bm2  = st.columns(2)
    bm1.markdown(f'<div class="metric-card"><div class="label">건물 단가</div><div class="value">₩ {b_unit:,.0f} / ㎡</div></div>', unsafe_allow_html=True)
    bm2.markdown(f'<div class="metric-card"><div class="label">건물 예상가</div><div class="value">₩ {b_total:,.0f}</div></div>', unsafe_allow_html=True)

    # ── 3. 구분건물 ──
    st.markdown('<div class="section-header">🏬 3. 구분건물 평가</div>', unsafe_allow_html=True)
    u_addr  = st.text_input("구분건물 비고(단지명/호수)", value=str(load_data.get('u_addr', '') or ''))
    uc1, uc2, uc3 = st.columns(3)
    u_area  = uc1.number_input("전유면적 (㎡)",        value=float(load_data.get('u_area', 0.0) or 0))
    u_price = uc2.number_input("구분건물 단가 (원/㎡)", value=int(load_data.get('u_price', 0) or 0))
    u_total = u_area * u_price
    uc3.markdown(f'<div class="metric-card"><div class="label">구분건물 예상가</div><div class="value">₩ {u_total:,.0f}</div></div>', unsafe_allow_html=True)

    # ── 합계 + 저장 ──
    grand_total = l_total + b_total + u_total
    st.divider()
    st.markdown(f'<div class="metric-card" style="max-width:360px;margin:0 auto"><div class="label">📊 총 감정 예상가</div><div class="value total">₩ {grand_total:,.0f}</div></div>', unsafe_allow_html=True)
    st.write("")
    save_col, _ = st.columns([1, 3])
    with save_col:
        if st.button("💾 수정 저장" if edit_id else "💾 신규 저장", type="primary", use_container_width=True):
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
            row_data = (
                ref_date.strftime('%Y-%m-%d'), client_name, purpose, evaluator, memo,
                si_do, si_gun_gu, eup_myeon_dong, bun_type, main_bun, sub_bun,
                l_area, l_price, l_total,
                b_addr, b_re_cost, b_area, b_life, b_passed, b_total,
                u_addr, u_area, u_price, u_total, grand_total
            )
            if edit_id:
                update_entry(edit_id, row_data)
                st.success(f"✅ ID #{edit_id} 수정 완료!")
                st.session_state.edit_id = None
            else:
                insert_entry((now_str,) + row_data)
                st.success("✅ 신규 저장 완료!")
            st.session_state.pop("addr_results", None)
            st.rerun()

# ═══════════════════════════════════════
# TAB 2: 조회 / 검색
# ═══════════════════════════════════════
with tab_list:
    st.markdown('<div class="section-header">🔍 검색 · 필터</div>', unsafe_allow_html=True)
    fc1, fc2, fc3, fc4 = st.columns([2,1,1,1])
    search_kw = fc1.text_input("검색어 (주소·의뢰인)", placeholder="예: 강남구, 홍길동")
    conn = get_conn()
    sido_list_db = pd.read_sql_query("SELECT DISTINCT si_do FROM evaluations WHERE si_do!=''", conn)['si_do'].tolist()
    conn.close()
    sido_filter = fc2.selectbox("시도 필터", ["전체"] + sido_list_db)
    date_from   = fc3.date_input("시작 기준일", value=None, key="list_df")
    date_to     = fc4.date_input("종료 기준일", value=None, key="list_dt")

    df = get_list(search_kw, sido_filter, date_from, date_to)
    if df.empty:
        st.info("조회된 기록이 없습니다.")
    else:
        st.markdown(f"**{len(df)}건** 조회됨")
        st.download_button("⬇️ 엑셀 내보내기", data=to_excel(df),
                           file_name=f"탁상감정_{datetime.now().strftime('%Y%m%d')}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.divider()
        for _, row in df.iterrows():
            addr = f"{row['si_do']} {row['si_gun_gu']} {row['eup_myeon_dong']} {row['main_bun']}-{row['sub_bun']}"
            pt = f'<span class="tag-chip">{row.get("purpose","")}</span>' if row.get("purpose") else ""
            ca, cb, cc, cd = st.columns([4,2,1,1])
            ca.markdown(f"**#{row['id']}** {addr} {pt}", unsafe_allow_html=True)
            ca.caption(f"기준: {row['ref_date']}  |  등록: {row['reg_date']}  |  의뢰인: {row.get('client_name','')}")
            cb.markdown(f'<div style="text-align:right;font-family:IBM Plex Mono,monospace;font-weight:600;color:#c0392b">₩ {int(row["grand_total"]):,}</div>', unsafe_allow_html=True)
            if cc.button("✏️ 수정", key=f"edit_{row['id']}"):
                st.session_state.edit_id = int(row['id'])
                st.session_state.pop("addr_results", None)
                st.rerun()
            if cd.button("🗑️ 삭제", key=f"del_{row['id']}"):
                delete_entry(int(row['id'])); st.rerun()
            st.divider()

# ═══════════════════════════════════════
# TAB 3: 보고서 출력
# ═══════════════════════════════════════
with tab_report:
    st.markdown('<div class="section-header">📄 탁상감정 보고서 출력</div>', unsafe_allow_html=True)
    conn = get_conn()
    all_df = pd.read_sql_query(
        "SELECT id, si_do, si_gun_gu, eup_myeon_dong, main_bun, sub_bun, grand_total FROM evaluations ORDER BY id DESC", conn)
    conn.close()

    if all_df.empty:
        st.info("저장된 기록이 없습니다.")
    else:
        all_df['label'] = all_df.apply(
            lambda x: f"[{x['id']}] {x['si_do']} {x['si_gun_gu']} {x['eup_myeon_dong']} {x['main_bun']}-{x['sub_bun']}", axis=1)
        chosen = st.selectbox("보고서를 출력할 건 선택", all_df['label'].tolist())
        chosen_id = int(chosen.split(']')[0][1:])
        conn = get_conn()
        r = pd.read_sql_query(f"SELECT * FROM evaluations WHERE id={chosen_id}", conn).iloc[0]
        conn.close()
        full_addr = " ".join(filter(None, [
            str(r['si_do']), str(r['si_gun_gu']), str(r['eup_myeon_dong']),
            str(r['bun_type']), f"{r['main_bun']}-{r['sub_bun']}"]))

        html_report = f"""
        <div style="font-family:'Noto Sans KR',sans-serif;max-width:720px;margin:0 auto;
                    border:2px solid #1a2332;border-radius:12px;overflow:hidden;">
          <div style="background:#1a2332;color:white;padding:1.5rem 2rem;">
            <h2 style="margin:0;font-size:1.4rem">탁상감정 평가서</h2>
            <p style="margin:0.3rem 0 0;opacity:0.7;font-size:0.85rem">부동산 탁상감정 결과 보고서</p>
          </div>
          <div style="padding:1.5rem 2rem;background:white">
            <table style="width:100%;border-collapse:collapse;font-size:0.9rem">
              <tr style="background:#f8fafc">
                <td style="padding:0.5rem 0.8rem;color:#64748b;width:25%;font-weight:500">기준시점</td>
                <td style="padding:0.5rem 0.8rem">{r['ref_date']}</td>
                <td style="padding:0.5rem 0.8rem;color:#64748b;width:25%;font-weight:500">감정목적</td>
                <td style="padding:0.5rem 0.8rem">{r.get('purpose','')}</td>
              </tr>
              <tr>
                <td style="padding:0.5rem 0.8rem;color:#64748b;font-weight:500">의뢰인</td>
                <td style="padding:0.5rem 0.8rem">{r.get('client_name','')}</td>
                <td style="padding:0.5rem 0.8rem;color:#64748b;font-weight:500">담당자</td>
                <td style="padding:0.5rem 0.8rem">{r.get('evaluator','')}</td>
              </tr>
              <tr style="background:#f8fafc">
                <td style="padding:0.5rem 0.8rem;color:#64748b;font-weight:500">소재지</td>
                <td colspan="3" style="padding:0.5rem 0.8rem">{full_addr}</td>
              </tr>
            </table>
            <div style="height:1px;background:#e2e8f0;margin:1rem 0"></div>
            <table style="width:100%;border-collapse:collapse;font-size:0.9rem">
              <tr style="background:#eef4fb">
                <th style="padding:0.6rem 0.8rem;text-align:left;color:#1a2332">구분</th>
                <th style="padding:0.6rem 0.8rem;text-align:right;color:#1a2332">면적(㎡)</th>
                <th style="padding:0.6rem 0.8rem;text-align:right;color:#1a2332">단가(원)</th>
                <th style="padding:0.6rem 0.8rem;text-align:right;color:#1a2332">금액(원)</th>
              </tr>
              <tr>
                <td style="padding:0.5rem 0.8rem;border-bottom:1px solid #f1f5f9">토지</td>
                <td style="padding:0.5rem 0.8rem;text-align:right;border-bottom:1px solid #f1f5f9">{r['land_area']:,.1f}</td>
                <td style="padding:0.5rem 0.8rem;text-align:right;border-bottom:1px solid #f1f5f9">{int(r['land_price']):,}</td>
                <td style="padding:0.5rem 0.8rem;text-align:right;border-bottom:1px solid #f1f5f9">{int(r['land_total']):,}</td>
              </tr>
              <tr style="background:#fafafa">
                <td style="padding:0.5rem 0.8rem;border-bottom:1px solid #f1f5f9">건물</td>
                <td style="padding:0.5rem 0.8rem;text-align:right;border-bottom:1px solid #f1f5f9">{r['b_area']:,.1f}</td>
                <td style="padding:0.5rem 0.8rem;text-align:right;border-bottom:1px solid #f1f5f9">-</td>
                <td style="padding:0.5rem 0.8rem;text-align:right;border-bottom:1px solid #f1f5f9">{int(r['b_total']):,}</td>
              </tr>
              <tr>
                <td style="padding:0.5rem 0.8rem;border-bottom:1px solid #f1f5f9">구분건물</td>
                <td style="padding:0.5rem 0.8rem;text-align:right;border-bottom:1px solid #f1f5f9">{r['u_area']:,.1f}</td>
                <td style="padding:0.5rem 0.8rem;text-align:right;border-bottom:1px solid #f1f5f9">{int(r['u_price']):,}</td>
                <td style="padding:0.5rem 0.8rem;text-align:right;border-bottom:1px solid #f1f5f9">{int(r['u_total']):,}</td>
              </tr>
              <tr style="background:#1a2332;color:white">
                <td colspan="3" style="padding:0.7rem 0.8rem;font-weight:700">총 감정 예상가</td>
                <td style="padding:0.7rem 0.8rem;text-align:right;font-family:IBM Plex Mono,monospace;font-size:1.1rem;font-weight:700">
                  ₩ {int(r['grand_total']):,}
                </td>
              </tr>
            </table>
            {'<div style="margin-top:1rem;padding:0.8rem;background:#fffbea;border-radius:8px;font-size:0.85rem;color:#92400e"><strong>메모:</strong> '+str(r.get('memo',''))+'</div>' if r.get('memo') else ''}
            <p style="text-align:right;color:#94a3b8;font-size:0.75rem;margin-top:1rem">
              등록일: {r['reg_date']} &nbsp;|&nbsp; 시스템 출력본 (탁상감정용 참고자료)
            </p>
          </div>
        </div>
        """
        st.markdown(html_report, unsafe_allow_html=True)
        st.write("")
        st.info("💡 브라우저에서 Ctrl+P (또는 Cmd+P) 를 누르면 PDF로 저장/인쇄할 수 있습니다.")
