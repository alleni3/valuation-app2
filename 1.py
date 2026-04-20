import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# ─────────────────────────────────────────
# 법정동 데이터 로드
# ─────────────────────────────────────────
@st.cache_data(show_spinner="법정동 데이터 로딩 중...")
def load_beopjeongdong():
    """
    행정표준코드관리시스템 법정동코드 TXT 로드.
    네트워크 불가 시 내장 샘플로 폴백.
    
    ※ 전체 데이터 사용법:
      1. https://www.code.go.kr/stdcode/regCodeL.do 에서 '법정동코드 전체자료.zip' 다운로드
      2. 압축 해제 후 '법정동코드 전체자료.txt' 를 앱과 같은 폴더에 저장
      3. 아래 로컬 파일 로드 코드가 자동으로 해당 파일을 우선 사용합니다.
    """
    import os

    # ① 로컬 TXT 파일 우선 (전체 법정동 데이터)
    local_path = "법정동코드 전체자료.txt"
    if os.path.exists(local_path):
        try:
            df = pd.read_csv(local_path, sep="\t", dtype=str, encoding="cp949", on_bad_lines="skip")
            df.columns = df.columns.str.strip()
            if "법정동코드" in df.columns and "법정동명" in df.columns:
                df = df[df["폐지여부"].str.strip() == "존재"].copy()
                df["법정동명"] = df["법정동명"].str.strip()
                def parse_addr(name):
                    parts = name.split()
                    return (parts[0] if len(parts)>0 else "",
                            parts[1] if len(parts)>1 else "",
                            " ".join(parts[2:]) if len(parts)>2 else "")
                df[["시도","시군구","읍면동리"]] = df["법정동명"].apply(lambda x: pd.Series(parse_addr(x)))
                return df
        except Exception:
            pass

    # ② GitHub 공개 미러 시도
    try:
        df = pd.read_csv(
            "https://raw.githubusercontent.com/raqoon886/Local_HangJeongDong/master/hangjeongdong_master.csv",
            dtype=str, encoding="utf-8"
        )
        # 컬럼: 시도명, 시군구명, 읍면동명, 법정동코드 등
        if "시도명" in df.columns:
            df = df.rename(columns={"시도명":"시도","시군구명":"시군구","읍면동명":"읍면동리"})
            df["법정동명"] = df["시도"] + " " + df["시군구"] + " " + df["읍면동리"]
            df["폐지여부"] = "존재"
            return df[["법정동명","시도","시군구","읍면동리","폐지여부"]].dropna()
    except Exception:
        pass

    # ③ 내장 샘플 (오프라인 폴백 — 주요 법정동 150여건)
    sample = [
        ("서울특별시 종로구 청운동","서울특별시","종로구","청운동"),
        ("서울특별시 종로구 삼청동","서울특별시","종로구","삼청동"),
        ("서울특별시 종로구 인사동","서울특별시","종로구","인사동"),
        ("서울특별시 종로구 혜화동","서울특별시","종로구","혜화동"),
        ("서울특별시 중구 명동","서울특별시","중구","명동"),
        ("서울특별시 중구 을지로동","서울특별시","중구","을지로동"),
        ("서울특별시 용산구 이태원동","서울특별시","용산구","이태원동"),
        ("서울특별시 용산구 한남동","서울특별시","용산구","한남동"),
        ("서울특별시 성동구 성수동1가","서울특별시","성동구","성수동1가"),
        ("서울특별시 성동구 왕십리동","서울특별시","성동구","왕십리동"),
        ("서울특별시 광진구 자양동","서울특별시","광진구","자양동"),
        ("서울특별시 광진구 화양동","서울특별시","광진구","화양동"),
        ("서울특별시 마포구 합정동","서울특별시","마포구","합정동"),
        ("서울특별시 마포구 상수동","서울특별시","마포구","상수동"),
        ("서울특별시 마포구 서교동","서울특별시","마포구","서교동"),
        ("서울특별시 마포구 망원동","서울특별시","마포구","망원동"),
        ("서울특별시 서대문구 연희동","서울특별시","서대문구","연희동"),
        ("서울특별시 서대문구 신촌동","서울특별시","서대문구","신촌동"),
        ("서울특별시 은평구 응암동","서울특별시","은평구","응암동"),
        ("서울특별시 강서구 화곡동","서울특별시","강서구","화곡동"),
        ("서울특별시 강서구 마곡동","서울특별시","강서구","마곡동"),
        ("서울특별시 양천구 목동","서울특별시","양천구","목동"),
        ("서울특별시 구로구 신도림동","서울특별시","구로구","신도림동"),
        ("서울특별시 구로구 구로동","서울특별시","구로구","구로동"),
        ("서울특별시 금천구 가산동","서울특별시","금천구","가산동"),
        ("서울특별시 영등포구 여의도동","서울특별시","영등포구","여의도동"),
        ("서울특별시 영등포구 영등포동","서울특별시","영등포구","영등포동"),
        ("서울특별시 영등포구 당산동","서울특별시","영등포구","당산동"),
        ("서울특별시 동작구 노량진동","서울특별시","동작구","노량진동"),
        ("서울특별시 동작구 상도동","서울특별시","동작구","상도동"),
        ("서울특별시 관악구 봉천동","서울특별시","관악구","봉천동"),
        ("서울특별시 관악구 신림동","서울특별시","관악구","신림동"),
        ("서울특별시 서초구 서초동","서울특별시","서초구","서초동"),
        ("서울특별시 서초구 반포동","서울특별시","서초구","반포동"),
        ("서울특별시 서초구 잠원동","서울특별시","서초구","잠원동"),
        ("서울특별시 서초구 방배동","서울특별시","서초구","방배동"),
        ("서울특별시 서초구 양재동","서울특별시","서초구","양재동"),
        ("서울특별시 강남구 역삼동","서울특별시","강남구","역삼동"),
        ("서울특별시 강남구 논현동","서울특별시","강남구","논현동"),
        ("서울특별시 강남구 압구정동","서울특별시","강남구","압구정동"),
        ("서울특별시 강남구 청담동","서울특별시","강남구","청담동"),
        ("서울특별시 강남구 삼성동","서울특별시","강남구","삼성동"),
        ("서울특별시 강남구 대치동","서울특별시","강남구","대치동"),
        ("서울특별시 강남구 도곡동","서울특별시","강남구","도곡동"),
        ("서울특별시 강남구 개포동","서울특별시","강남구","개포동"),
        ("서울특별시 강남구 일원동","서울특별시","강남구","일원동"),
        ("서울특별시 강남구 수서동","서울특별시","강남구","수서동"),
        ("서울특별시 강남구 신사동","서울특별시","강남구","신사동"),
        ("서울특별시 송파구 잠실동","서울특별시","송파구","잠실동"),
        ("서울특별시 송파구 가락동","서울특별시","송파구","가락동"),
        ("서울특별시 송파구 문정동","서울특별시","송파구","문정동"),
        ("서울특별시 송파구 방이동","서울특별시","송파구","방이동"),
        ("서울특별시 강동구 천호동","서울특별시","강동구","천호동"),
        ("서울특별시 강동구 암사동","서울특별시","강동구","암사동"),
        ("서울특별시 노원구 상계동","서울특별시","노원구","상계동"),
        ("서울특별시 강북구 미아동","서울특별시","강북구","미아동"),
        ("서울특별시 도봉구 쌍문동","서울특별시","도봉구","쌍문동"),
        ("서울특별시 성북구 길음동","서울특별시","성북구","길음동"),
        ("부산광역시 해운대구 우동","부산광역시","해운대구","우동"),
        ("부산광역시 해운대구 중동","부산광역시","해운대구","중동"),
        ("부산광역시 해운대구 좌동","부산광역시","해운대구","좌동"),
        ("부산광역시 수영구 민락동","부산광역시","수영구","민락동"),
        ("부산광역시 남구 대연동","부산광역시","남구","대연동"),
        ("부산광역시 부산진구 전포동","부산광역시","부산진구","전포동"),
        ("부산광역시 동래구 온천동","부산광역시","동래구","온천동"),
        ("부산광역시 북구 구포동","부산광역시","북구","구포동"),
        ("부산광역시 강서구 명지동","부산광역시","강서구","명지동"),
        ("부산광역시 기장군 기장읍 기장리","부산광역시","기장군","기장읍 기장리"),
        ("대구광역시 수성구 범어동","대구광역시","수성구","범어동"),
        ("대구광역시 수성구 황금동","대구광역시","수성구","황금동"),
        ("대구광역시 달서구 월성동","대구광역시","달서구","월성동"),
        ("대구광역시 북구 칠성동","대구광역시","북구","칠성동"),
        ("대구광역시 중구 동성로","대구광역시","중구","동성로"),
        ("인천광역시 연수구 송도동","인천광역시","연수구","송도동"),
        ("인천광역시 연수구 연수동","인천광역시","연수구","연수동"),
        ("인천광역시 남동구 간석동","인천광역시","남동구","간석동"),
        ("인천광역시 부평구 부평동","인천광역시","부평구","부평동"),
        ("인천광역시 서구 청라동","인천광역시","서구","청라동"),
        ("인천광역시 미추홀구 주안동","인천광역시","미추홀구","주안동"),
        ("광주광역시 북구 용봉동","광주광역시","북구","용봉동"),
        ("광주광역시 광산구 수완동","광주광역시","광산구","수완동"),
        ("광주광역시 서구 치평동","광주광역시","서구","치평동"),
        ("대전광역시 유성구 봉명동","대전광역시","유성구","봉명동"),
        ("대전광역시 서구 둔산동","대전광역시","서구","둔산동"),
        ("울산광역시 남구 삼산동","울산광역시","남구","삼산동"),
        ("세종특별자치시 어진동","세종특별자치시","세종시","어진동"),
        ("세종특별자치시 보람동","세종특별자치시","세종시","보람동"),
        ("경기도 수원시 장안구 율전동","경기도","수원시 장안구","율전동"),
        ("경기도 수원시 팔달구 인계동","경기도","수원시 팔달구","인계동"),
        ("경기도 수원시 영통구 영통동","경기도","수원시 영통구","영통동"),
        ("경기도 성남시 분당구 분당동","경기도","성남시 분당구","분당동"),
        ("경기도 성남시 분당구 서현동","경기도","성남시 분당구","서현동"),
        ("경기도 성남시 분당구 정자동","경기도","성남시 분당구","정자동"),
        ("경기도 용인시 수지구 풍덕천동","경기도","용인시 수지구","풍덕천동"),
        ("경기도 용인시 기흥구 구갈동","경기도","용인시 기흥구","구갈동"),
        ("경기도 고양시 일산동구 장항동","경기도","고양시 일산동구","장항동"),
        ("경기도 고양시 일산서구 주엽동","경기도","고양시 일산서구","주엽동"),
        ("경기도 부천시 원미구 중동","경기도","부천시 원미구","중동"),
        ("경기도 안양시 동안구 평촌동","경기도","안양시 동안구","평촌동"),
        ("경기도 남양주시 다산동","경기도","남양주시","다산동"),
        ("경기도 화성시 동탄동","경기도","화성시","동탄동"),
        ("경기도 평택시 고덕동","경기도","평택시","고덕동"),
        ("경기도 파주시 운정동","경기도","파주시","운정동"),
        ("경기도 김포시 장기동","경기도","김포시","장기동"),
        ("충청북도 청주시 상당구 중앙동","충청북도","청주시 상당구","중앙동"),
        ("충청북도 청주시 흥덕구 복대동","충청북도","청주시 흥덕구","복대동"),
        ("충청남도 천안시 동남구 신부동","충청남도","천안시 동남구","신부동"),
        ("충청남도 천안시 서북구 불당동","충청남도","천안시 서북구","불당동"),
        ("충청남도 아산시 배방읍 장재리","충청남도","아산시","배방읍 장재리"),
        ("전라북도 전주시 완산구 효자동","전라북도","전주시 완산구","효자동"),
        ("전라북도 전주시 덕진구 금암동","전라북도","전주시 덕진구","금암동"),
        ("전라남도 목포시 상동","전라남도","목포시","상동"),
        ("전라남도 순천시 조례동","전라남도","순천시","조례동"),
        ("경상북도 포항시 남구 대도동","경상북도","포항시 남구","대도동"),
        ("경상북도 구미시 형곡동","경상북도","구미시","형곡동"),
        ("경상남도 창원시 성산구 상남동","경상남도","창원시 성산구","상남동"),
        ("경상남도 김해시 내외동","경상남도","김해시","내외동"),
        ("제주특별자치도 제주시 노형동","제주특별자치도","제주시","노형동"),
        ("제주특별자치도 제주시 연동","제주특별자치도","제주시","연동"),
        ("제주특별자치도 서귀포시 서귀동","제주특별자치도","서귀포시","서귀동"),
    ]
    df = pd.DataFrame(sample, columns=["법정동명","시도","시군구","읍면동리"])
    df["폐지여부"] = "존재"
    return df


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
.metric-card .value { font-family: 'IBM Plex Mono', monospace; font-size: 1.1rem; font-weight: 600; color: #1e3a5f; }
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
def address_search_widget(load_data, bj_df):
    """
    두 가지 모드:
      - 🔍 키워드 검색: 동명 일부 입력 → 결과 목록 선택
      - 📂 단계별 선택: 시도 → 시군구 → 읍면동 순차 드롭다운
    반환: (si_do, si_gun_gu, eup_myeon_dong)
    """
    si_do = str(load_data.get('si_do', '') or '')
    si_gun_gu = str(load_data.get('si_gun_gu', '') or '')
    eup_myeon_dong = str(load_data.get('eup_myeon_dong', '') or '')

    mode = st.radio("주소 입력 방식", ["🔍 키워드 검색", "📂 단계별 선택"],
                    horizontal=True, key="addr_mode")

    if mode == "🔍 키워드 검색":
        kw = st.text_input("동·읍·면·리 검색",
                           placeholder="예) 역삼동, 분당, 송도, 해운대",
                           key="addr_kw")
        if kw.strip():
            hits = bj_df[bj_df["법정동명"].str.contains(kw.strip(), na=False)].head(40)
            if hits.empty:
                st.warning("검색 결과가 없습니다. 다른 키워드를 입력해 보세요.")
                st.caption("💡 전체 법정동이 필요하면 code.go.kr 에서 '법정동코드 전체자료.txt' 를 다운로드하여 앱 폴더에 저장하세요.")
            else:
                options = hits["법정동명"].tolist()
                default_idx = 0
                current_full = f"{si_do} {si_gun_gu} {eup_myeon_dong}".strip()
                for i, o in enumerate(options):
                    if o.strip() == current_full:
                        default_idx = i; break
                chosen = st.selectbox(f"검색 결과 ({len(hits)}건)", options,
                                      index=default_idx, key="addr_kw_sel")
                row = hits[hits["법정동명"] == chosen].iloc[0]
                si_do = row["시도"]
                si_gun_gu = row["시군구"]
                eup_myeon_dong = row["읍면동리"]
        else:
            st.caption("동·읍·면·리 이름 일부를 입력하면 법정동 목록이 표시됩니다.")

    else:  # 단계별 선택
        sido_list = sorted(bj_df["시도"].dropna().unique().tolist())
        sido_idx = sido_list.index(si_do) if si_do in sido_list else 0
        c1, c2, c3 = st.columns(3)
        sel_sido = c1.selectbox("시 / 도", sido_list, index=sido_idx, key="addr_sido")

        sgg = sorted(bj_df[bj_df["시도"] == sel_sido]["시군구"].dropna().unique().tolist())
        sgg = [s for s in sgg if s]
        sgg_idx = sgg.index(si_gun_gu) if si_gun_gu in sgg else 0
        sel_sgg = c2.selectbox("시 / 군 / 구", sgg, index=sgg_idx, key="addr_sgg") if sgg else ""

        emd = sorted(bj_df[(bj_df["시도"]==sel_sido) & (bj_df["시군구"]==sel_sgg)]["읍면동리"].dropna().unique().tolist())
        emd = [e for e in emd if e]
        emd_idx = emd.index(eup_myeon_dong) if eup_myeon_dong in emd else 0
        sel_emd = c3.selectbox("읍 / 면 / 동 / 리", emd, index=emd_idx, key="addr_emd") if emd else ""

        si_do, si_gun_gu, eup_myeon_dong = sel_sido, sel_sgg, sel_emd

    # 선택 주소 미리보기
    if si_do:
        full = " ".join(filter(None, [si_do, si_gun_gu, eup_myeon_dong]))
        st.markdown(f'<div class="addr-preview">📌 <strong>선택 소재지:</strong> &nbsp;{full}</div>',
                    unsafe_allow_html=True)

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

bj_df = load_beopjeongdong()

# ─────────────────────────────────────────
# 탭
# ─────────────────────────────────────────
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
            st.session_state.edit_id = None; st.rerun()

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

    # 법정동 검색
    si_do, si_gun_gu, eup_myeon_dong = address_search_widget(load_data, bj_df)

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
    b_addr = st.text_input("건물 비고(명칭 등)", value=str(load_data.get('b_addr', '') or ''))
    bc1, bc2, bc3, bc4 = st.columns(4)
    b_re_cost = bc1.number_input("재조달원가 (원/㎡)", value=int(load_data.get('b_re_cost', 0) or 0))
    b_area    = bc2.number_input("건물 면적 (㎡)",     value=float(load_data.get('b_area', 0.0) or 0))
    b_life    = bc3.number_input("내용연수 (년)",       value=int(load_data.get('b_total_life', 40) or 40))
    b_passed  = bc4.number_input("경과연수 (년)",       value=int(load_data.get('b_passed', 0) or 0))
    b_unit = int(b_re_cost * (1 - b_passed / b_life)) if b_life > 0 else 0
    b_total = b_unit * b_area
    bm1, bm2 = st.columns(2)
    bm1.markdown(f'<div class="metric-card"><div class="label">건물 단가</div><div class="value">₩ {b_unit:,.0f} / ㎡</div></div>', unsafe_allow_html=True)
    bm2.markdown(f'<div class="metric-card"><div class="label">건물 예상가</div><div class="value">₩ {b_total:,.0f}</div></div>', unsafe_allow_html=True)

    # ── 3. 구분건물 ──
    st.markdown('<div class="section-header">🏬 3. 구분건물 평가</div>', unsafe_allow_html=True)
    u_addr  = st.text_input("구분건물 비고(단지명/호수)", value=str(load_data.get('u_addr', '') or ''))
    uc1, uc2, uc3 = st.columns(3)
    u_area  = uc1.number_input("전유면적 (㎡)",         value=float(load_data.get('u_area', 0.0) or 0))
    u_price = uc2.number_input("구분건물 단가 (원/㎡)",  value=int(load_data.get('u_price', 0) or 0))
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
            st.rerun()

# ═══════════════════════════════════════
# TAB 2: 조회 / 검색
# ═══════════════════════════════════════
with tab_list:
    st.markdown('<div class="section-header">🔍 검색 · 필터</div>', unsafe_allow_html=True)
    fc1, fc2, fc3, fc4 = st.columns([2,1,1,1])
    search_kw   = fc1.text_input("검색어 (주소·의뢰인)", placeholder="예: 강남구, 홍길동")
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
            purpose_tag = f'<span class="tag-chip">{row.get("purpose","")}</span>' if row.get("purpose") else ""
            ca, cb, cc, cd = st.columns([4,2,1,1])
            ca.markdown(f"**#{row['id']}** {addr} {purpose_tag}", unsafe_allow_html=True)
            ca.caption(f"기준: {row['ref_date']}  |  등록: {row['reg_date']}  |  의뢰인: {row.get('client_name','')}")
            cb.markdown(f'<div style="text-align:right;font-family:IBM Plex Mono,monospace;font-weight:600;color:#c0392b">₩ {int(row["grand_total"]):,}</div>', unsafe_allow_html=True)
            if cc.button("✏️ 수정", key=f"edit_{row['id']}"):
                st.session_state.edit_id = int(row['id']); st.rerun()
            if cd.button("🗑️ 삭제", key=f"del_{row['id']}"):
                delete_entry(int(row['id'])); st.rerun()
            st.divider()

# ═══════════════════════════════════════
# TAB 3: 보고서 출력
# ═══════════════════════════════════════
with tab_report:
    st.markdown('<div class="section-header">📄 탁상감정 보고서 출력</div>', unsafe_allow_html=True)
    conn = get_conn()
    all_df = pd.read_sql_query("SELECT id, si_do, si_gun_gu, eup_myeon_dong, main_bun, sub_bun, grand_total FROM evaluations ORDER BY id DESC", conn)
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
        full_addr = " ".join(filter(None,[str(r['si_do']),str(r['si_gun_gu']),str(r['eup_myeon_dong']),str(r['bun_type']),f"{r['main_bun']}-{r['sub_bun']}"]))
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
