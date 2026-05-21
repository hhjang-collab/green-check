import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime
import base64
import streamlit.components.v1 as components

# 1. 페이지 기본 설정 및 보안 설정
st.set_page_config(page_title="서류 검토 자동화 시스템", layout="wide")

# UI 최적화용 CSS 주입
st.markdown("""
    <style>
        /* 입력창 내부 안내 문구 숨기기 */
        .stTextArea textarea::placeholder { color: transparent !important; }
        .stInput input::placeholder { color: transparent !important; }
        
        /* 라디오 버튼 가로 정렬 시 줄바꿈 방지 */
        div[data-testid="stRadio"] > div { flex-direction: row !important; gap: 20px; }
        div[data-testid="stRadio"] label { white-space: nowrap !important; }
        
        /* 사이드바 글자 크기 조정 */
        [data-testid="stSidebar"] { font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

# 비밀번호 및 세션 상태 초기화
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "save_success" not in st.session_state:
    st.session_state["save_success"] = False

def check_password():
    if st.session_state["authenticated"]:
        return True
    
    st.title("🔒 시스템 접속 인증")
    password_input = st.text_input("접속 비밀번호를 입력하세요.", type="password")
    
    # st.secrets에서 관리자 비밀번호 가져오기 (없으면 기본값 "1234")
    correct_password = st.secrets.get("APP_PASSWORD", "1234")
    
    if st.button("인증하기", type="primary"):
        if password_input == correct_password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("❌ 비밀번호가 일치하지 않습니다.")
    return False

if not check_password():
    st.stop()

# 2. 구글 시트 연동 기능 정의
def save_to_google_sheets(global_type, req_type, total_errors, results):
    try:
        # Streamlit Secrets에서 GCP 서비스 계정 정보 로드
        if "gcp_service_account" not in st.secrets:
            st.error("GCP 서비스 계정 설정(Secrets)을 찾을 수 없습니다.")
            return False
            
        service_account_info = dict(st.secrets["gcp_service_account"])
        
        # 구글 시트 및 드라이브 API 권한 스코프 설정 (403 에러 원천 방지)
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
        gc = gspread.authorize(credentials)
        
        # 대상 구글 시트 열기
        sheet_name = st.secrets.get("GOOGLE_SHEET_NAME", "녹색인증_검토이력")
        sh = gc.open(sheet_name)
        worksheet = sh.get_worksheet(0) # 첫 번째 탭 선택
        
        # 저장할 데이터 구성
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        details_str = ", ".join(results) if results else "보완 사항 없음"
        
        # 구글 시트에 행 추가 (일시, 검토유형, 신청구분, 보완개수, 상세내용)
        row_data = [current_time, global_type, req_type, total_errors, details_str]
        worksheet.append_row(row_data)
        return True
    except Exception as e:
        st.error(f"❌ 구글 시트 저장 실패: {e}")
        return False

# 클립보드 복사용 컴포넌트 함수 정의
def render_copy_button(text_to_copy):
    b64_text = base64.b64encode(text_to_copy.encode("utf-8")).decode("utf-8")
    button_id = "copyButton"
    html_str = f"""
    <style>
        body {{ margin: 0; padding: 0; font-family: "Source Sans Pro", sans-serif; }}
        .copy-btn {{
            display: flex; align-items: center; justify-content: center;
            width: 100%; height: 38px;
            background-color: transparent; color: inherit;
            border: 1px solid rgba(49, 51, 63, 0.2); border-radius: 8px;
            font-size: 16px; font-weight: 400; cursor: pointer; transition: all 0.2s ease;
        }}
        .copy-btn:hover {{ border-color: #FF4B4B; color: #FF4B4B; }}
    </style>
    <button class="copy-btn" id="{button_id}" onclick="copyToClipboard()">
        📋 2단계: 보완 문구 복사하기
    </button>
    <script>
        function copyToClipboard() {{
            const text = decodeURIComponent(escape(window.atob('{b64_text}')));
            navigator.clipboard.writeText(text).then(() => {{
                alert("📝 보완 문구가 클립보드에 성공적으로 복사되었습니다!");
            }}).catch(err => {{
                const el = document.createElement('textarea');
                el.value = text;
                document.body.appendChild(el);
                el.select();
                document.execCommand('copy');
                document.body.removeChild(el);
                alert("📝 보완 문구가 복사되었습니다! (우회 방식)");
            }});
        }}
    </script>
    """
    components.html(html_str, height=45)

# 3. 데이터 및 템플릿 문구 정의
default_templates = {
    "ceo_err": "신청서 상의 대표자 성명과 법인등기사항증명서 상의 대표자 성명이 일치하지 않습니다. 대표자 성명을 확인하시어 일치하도록 수정 및 보완하여 주시기 바랍니다.",
    "doc_missing": "제출서류 중 일부가 누락되었습니다. 필수 제출서류 목록을 확인하시어 누락된 서류(예: 사업자등록증, 재무제표 등)를 추가로 제출하여 주시기 바랍니다.",
    "ip_open_err": "공개된 지식재산권(특허 등)의 명세서 내용 중 핵심 기술 부분이 식별 불가능하거나 누락되어 있습니다. 해당 지식재산권의 기술 내용을 명확히 파악할 수 있는 증빙 자료를 추가 제출하여 주시기 바랍니다.",
    "doc_core_tech_err": "제출하신 기술설명서 내 핵심요소기술에 대한 설명이 미흡하거나 구체적인 데이터가 누락되어 있습니다. 해당 기술의 독창성과 우수성을 입증할 수 있는 상세 데이터 및 보완 자료를 제출하여 주시기 바랍니다."
}

def clear_form():
    # 모든 체크박스 상태 초기화
    for key in st.session_state.keys():
        if key.startswith("ch_"):
            st.session_state[key] = False

# 4. 메인 화면 레이아웃 (좌측 입력 및 선택 영역)
col_main, col_spacer = st.columns([12, 1])

with col_main:
    # 우측 상단 회사 로고 출력 예시 공간 (필요시 markdown 이미지 태그 활용)
    st.markdown("<div style='text-align: right; color: #888; font-size: 12px;'>주식회사 녹색인증</div>", unsafe_allow_html=True)
    st.title("🌱 녹색인증 서류 검토 시스템")
    
    # 공통 대분류 및 신청구분 선택
    global_type = st.radio("검토 유형 선택", ["기술", "제품", "기업"], key="global_type")
    req_type = st.radio("신청 구분", ["신규", "연장"], key="req_type")
    
    st.write("---")
    
    results = []
    total_errors = 0
    
    # [분기 1] 기술 검토 화면
    if global_type == "기술":
        st.subheader("💡 기술성 검토 세부 항목")
        
        with st.expander("1. 신청서 및 기본 서류 상태", expanded=True):
            if st.checkbox("대표자 불일치 오류", key="ch_tech_ceo"):
                results.append(default_templates["ceo_err"])
                total_errors += 1
            if st.checkbox("필수 서류 누락", key="ch_tech_missing"):
                results.append(default_templates["doc_missing"])
                total_errors += 1
                
        with st.expander("2. 지식재산권 및 기술 명세", expanded=True):
            if st.checkbox("지식재산권 공개 내용 미흡", key="ch_tech_ip"):
                results.append(default_templates["ip_open_err"])
                total_errors += 1
            if st.checkbox("핵심요소기술 설명 및 데이터 미흡", key="ch_tech_core"):
                results.append(default_templates["doc_core_tech_err"])
                total_errors += 1

    # [분기 2] 제품 검토 화면
    elif global_type == "제품":
        st.subheader("📦 제품성 검토 세부 항목")
        
        with st.expander("1. 기본 서류 및 품질 증빙", expanded=True):
            if st.checkbox("대표자 불일치 오류", key="ch_prod_ceo"):
                results.append(default_templates["ceo_err"])
                total_errors += 1
            if st.checkbox("필수 서류 누락", key="ch_prod_missing"):
                results.append(default_templates["doc_missing"])
                total_errors += 1

    # [분기 3] 기업 검토 화면
    elif global_type == "기업":
        st.subheader("🏢 기업성 검토 세부 항목")
        
        with st.expander("1. 경영 안정성 및 증빙", expanded=True):
            if st.checkbox("대표자 불일치 오류", key="ch_corp_ceo"):
                results.append(default_templates["ceo_err"])
                total_errors += 1
            if st.checkbox("필수 서류 누락", key="ch_corp_missing"):
                results.append(default_templates["doc_missing"])
                total_errors += 1

# 5. 사이드바 레이아웃 (우측 실시간 결과창 및 액션 영역)
with st.sidebar:
    st.header("📋 실시간 검토 결과")
    st.write(f"**현재 유형:** {global_type} / {req_type}")
    st.write(f"**검지된 보완 필요 건수:** {total_errors}건")
    st.write("---")
    
    # 실시간 조합 문구 생성
    if total_errors > 0:
        final_output = f"[{global_type} 검토 - {req_type} 신청 보완 요청사항]\n\n"
        for idx, text in enumerate(results, 1):
            final_output += f"{idx}. {text}\n\n"
        final_output += "감사합니다."
    else:
        final_output = "선택된 보완 항목이 없습니다. 모든 서류가 양호합니다."
        
    st.text_area("결과 확인", value=final_output, height=430, label_visibility="collapsed")
    
    # 📌 [핵심 개선] 브라우저 보안 에러가 완벽하게 우회되는 2단계 연속 버튼 액션
    if not st.session_state["save_success"]:
        if st.button("💾 1단계: 구글 시트 저장하기", type="primary", use_container_width=True):
            if total_errors > 0 or results:
                with st.spinner("구글 시트에 기록 중..."):
                    success = save_to_google_sheets(global_type, req_type, total_errors, results)
                if success:
                    st.session_state["save_success"] = True
                    st.rerun()
            else:
                st.warning("⚠️ 선택된 보완 항목이 없습니다.")
    else:
        st.success("✅ 구글 시트 저장 완료!")
        
        # 2단계: 저장 성공 시에만 노출되는 직접 클릭 복사 버튼 (보안 정책 100% 통과)
        render_copy_button(final_output)
        st.caption("💡 문구 복사까지 완료하신 후 아래 '초기화'를 눌러주세요.")
        
    st.markdown('<hr style="margin-top: 15px; margin-bottom: 15px; border: 0; border-top: 1px solid rgba(49, 51, 63, 0.2);">', unsafe_allow_html=True)
    
    # 초기화 및 다음 검토 프로세스 진입
    if st.button("🔄 다음 검토 시작 (초기화)", use_container_width=True):
        st.session_state["save_success"] = False
        clear_form()
        st.rerun()
