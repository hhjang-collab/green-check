import streamlit as st
import base64
import os

# 1 & 2. 페이지 기본 설정 (항상 최상단)
st.set_page_config(page_title="녹색인증 서류검토 도우미", layout="centered")

# 3. 보안 (비밀번호) 및 로그인 로직
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 사내 시스템 로그인")
    st.markdown('<hr style="margin-top: 15px; margin-bottom: 15px; border: 0; border-top: 1px solid rgba(49, 51, 63, 0.2);">', unsafe_allow_html=True)
    
    password = st.text_input("접근 비밀번호를 입력하세요.", type="password")
    if st.button("로그인"):
        # 📌 Streamlit Cloud 설정에서 Secrets에 APP_PASSWORD를 설정해 주세요.
        if password == st.secrets.get("APP_PASSWORD", "default_password"):  
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("비밀번호가 일치하지 않습니다.")
    st.stop() # 로그인 전에는 아래 메인 화면이 렌더링되지 않도록 차단

# 4. 회사 로고 (우측 상단 고정) 및 6. UI 최적화 CSS
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return ""

# 📌 로고 파일이 앱과 같은 경로에 있는지 확인해 주세요 ("company_logo.png")
logo_base64 = get_base64_of_bin_file("company_logo.png") 

custom_css = f'''
<style>
    /* 우측 상단 회사 로고 고정 (모바일 대응 포함) */
    .company-logo {{
        position: fixed;
        top: 70px;
        right: 30px;
        width: 100px;
        z-index: 9999;
    }}
    @media (max-width: 768px) {{
        .company-logo {{
            top: 50px;
            right: 15px;
            width: 70px;
        }}
    }}
    /* Streamlit 불필요한 안내 문구(Press Enter to apply 등) 숨김 처리 */
    [data-testid="InputInstructions"] {{
        display: none !important;
    }}
</style>
'''

if logo_base64:
    custom_css += f'<img src="data:image/png;base64,{logo_base64}" class="company-logo">'
st.markdown(custom_css, unsafe_allow_html=True)


# 5. 홈 버튼 (포털 복귀) 및 얇은 여백 구분선 (사이드바)
with st.sidebar:
    st.markdown(
        '''
        <div style="margin-top: 5px;">
            <a href="https://ip2b-work-tools.streamlit.app/" target="_blank" style="text-decoration: none; color: #31333F; font-size: 15px; font-weight: 600;">
                🏠 홈으로
            </a>
        </div>
        <hr style="margin-top: 10px; margin-bottom: 15px; border: 0; border-top: 1px solid rgba(49, 51, 63, 0.2);">
        ''', 
        unsafe_allow_html=True
    )
    
    # 추가 사이드바 요소 배치
    st.subheader("검토 가이드")
    st.info("녹색인증 신청 대상 기업의 제출 서류가 모두 구비되었는지 좌측 체크리스트를 통해 확인하세요.")


# === 메인 화면 구성 ===
st.title("🌿 녹색인증 서류검토 도우미")
# 7. 여백이 얇은 구분선 활용
st.markdown('<hr style="margin-top: 15px; margin-bottom: 15px; border: 0; border-top: 1px solid rgba(49, 51, 63, 0.2);">', unsafe_allow_html=True)

st.subheader("1. 제출 서류 업로드")
# 📌 추후 PDF 텍스트 추출이나 OCR 모듈을 연결할 수 있는 엔트리포인트
uploaded_files = st.file_uploader("검토할 서류를 업로드해 주세요 (PDF, 이미지, 문서 등)", accept_multiple_files=True)

st.markdown('<hr style="margin-top: 15px; margin-bottom: 15px; border: 0; border-top: 1px solid rgba(49, 51, 63, 0.2);">', unsafe_allow_html=True)

st.subheader("2. 필수 서류 체크리스트")
col1, col2 = st.columns(2)
with col1:
    st.checkbox("사업자등록증명원")
    st.checkbox("녹색인증 신청서")
    st.checkbox("기술설명서 및 요약서")
with col2:
    st.checkbox("공인기관 시험성적서")
    st.checkbox("지식재산권(특허 등) 증빙")
    st.checkbox("최근 결산 재무제표 (매출증빙)")

st.markdown('<hr style="margin-top: 15px; margin-bottom: 15px; border: 0; border-top: 1px solid rgba(49, 51, 63, 0.2);">', unsafe_allow_html=True)

st.subheader("3. 종합 검토 의견")
review_note = st.text_area("보완이 필요한 사항이나 최종 검토 의견을 자유롭게 작성해 주세요.", height=150)

if st.button("검토 결과 저장 및 보고서 생성", use_container_width=True):
    if not uploaded_files:
        st.warning("업로드된 서류가 없습니다. 서류 확인 없이 결과를 저장하시겠습니까?")
    else:
        # 📌 추후 DB 저장 로직이나 문서 생성(Word/PDF) 로직 추가
        st.success("성공적으로 검토 내용이 저장되었습니다!")
