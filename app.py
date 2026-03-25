# app.py
import streamlit as st
import base64
import os

# --- 1. 페이지 기본 설정 (공통 필수 규칙 2) ---
st.set_page_config(page_title="녹색인증 서류 검토 Agent PRO", layout="centered", initial_sidebar_state="expanded")

# --- 2. 보안 (비밀번호) 로직 (공통 필수 규칙 3) ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 사내 시스템 로그인")
    # ⚠️ [수정 필요] .streamlit/secrets.toml 파일에 APP_PASSWORD="여기에비밀번호" 를 설정해야 합니다.
    user_pwd = st.text_input("접근 비밀번호를 입력하세요", type="password")
    if st.button("로그인", use_container_width=True):
        if user_pwd == st.secrets.get("APP_PASSWORD"):
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("비밀번호가 일치하지 않습니다.")
    st.stop()

# --- 3. UI 최적화 및 회사 로고 설정 (공통 필수 규칙 4, 6) ---
def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

# ⚠️ [수정 필요] 실제 로고 파일 경로로 맞추어 주세요. 파일이 없으면 빈 문자열 반환.
logo_base64 = get_base64_of_bin_file("company_logo.png") 

st.markdown(f"""
<style>
    /* 입력창 하단 불필요한 안내 문구 숨김 */
    [data-testid="InputInstructions"] {{display: none !important;}}
    
    /* 우측 상단 회사 로고 고정 */
    .company-logo {{
        position: fixed;
        top: 70px;
        right: 30px;
        width: 120px;
        z-index: 1000;
    }}
    @media (max-width: 768px) {{
        .company-logo {{
            top: 20px;
            right: 20px;
            width: 80px;
        }}
    }}
</style>
<img src="data:image/png;base64,{logo_base64}" class="company-logo">
""", unsafe_allow_html=True)

# --- 4. 자동 생성 문구 템플릿 초기화 (세션 유지) ---
default_templates = {
    "ceoName": "- 제출하신 서류와 시스템 상의 대표자 명이 일치하지 않습니다.",
    "corpReg_corp": "- 법인등기부등본(최근 3개월 이내 발행본, 제출용)을 첨부하여 주시기 바랍니다.",
    "corpReg_indiv": "- 개인사업자의 경우, 사업자등록증을 최근 3개월 이내 발행본으로 제출해 주시기 바랍니다.",
    "s2_1_1": "- 요약서의 기술명(또는 제품명)이 시스템 신청 정보와 일치하지 않습니다.",
    "s2_2_1": "- 요약서: 분류체계 내용이 시스템과 불일치합니다.",
    "s2_2_2": "- 요약서: 분류코드 내용이 시스템과 불일치합니다.",
    "s2_2_3": "- 요약서: 핵심요소기술 내용이 시스템과 불일치합니다.",
    "s2_2_4": "- 요약서: 기술수준 내용이 시스템과 불일치합니다.",
    "s2_3": "- 설명서 내용 누락: 서식자료실 양식을 준수하여 세부 항목({missing_tocs})을 작성해 주시기 바랍니다.",
    "s3_1": "- 출원 또는 공개 상태가 아닌 등록 완료된 특허로 제출해 주시기 바랍니다.",
    "s3_2": "- 등록된 특허기술의 '특허등록원부'를 제출해 주시기 바랍니다.",
    "s3_3": "- 최종권리자가 타기업 또는 다수인 경우, 공동권리자의 '지식재산권 활용 동의서'를 작성해 주셔야 합니다.",
    "s4_1": "- 공인된 외부기관(KOLAS 등)의 시험성적서를 제출하거나, 자체/의뢰자 제시 성적서일 경우 반드시 '사유서'를 함께 제출해 주시기 바랍니다.",
    "s4_2": "- 시험성적서 상의 의뢰인(기업) 명의가 신청 업체와 일치해야 합니다.",
    "s5_1": "- 품질경영 증빙은 KS 인증 또는 ISO 인증(ISO 9001/14001 등) 서류로 준비하여 제출해 주셔야 합니다.",
    "s5_2": "- 공장등록증, 직접생산확인서 또는 생산현장증빙서류(OEM계약서 및 세금계산서 등)를 첨부하여 주시기 바랍니다."
}

if "templates" not in st.session_state:
    st.session_state["templates"] = default_templates.copy()

def clear_form():
    # 인증 상태와 템플릿 설정값은 유지하면서 화면의 입력 폼만 초기화
    for key in list(st.session_state.keys()):
        if key not in ["authenticated", "templates"]:
            del st.session_state[key]

# --- 5. 사이드바 상단 (홈 버튼) ---
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

# --- 6. 메인 화면 ---
st.title("🔍 녹색인증 서류검토 Agent PRO")

# [설정] 템플릿 직접 수정 아코디언
with st.expander("⚙️ 보완 요청 문구 설정 (클릭하여 수정)"):
    st.caption("체크리스트 선택 시 자동 입력되는 문구를 우리 회사 양식에 맞게 수정할 수 있습니다.")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("**기업/설명서 공통**")
        st.session_state.templates["ceoName"] = st.text_input("대표자명 불일치", value=st.session_state.templates["ceoName"])
        st.session_state.templates["corpReg_corp"] = st.text_input("법인등기부등본 관련", value=st.session_state.templates["corpReg_corp"])
        st.session_state.templates["corpReg_indiv"] = st.text_input("개인사업자등록증 관련", value=st.session_state.templates["corpReg_indiv"])
        st.session_state.templates["s2_1_1"] = st.text_input("기술/제품명 불일치", value=st.session_state.templates["s2_1_1"])
        st.session_state.templates["s2_2_1"] = st.text_input("분류체계 불일치", value=st.session_state.templates["s2_2_1"])
        st.session_state.templates["s2_2_2"] = st.text_input("분류코드 불일치", value=st.session_state.templates["s2_2_2"])
    with col_t2:
        st.markdown("**기술/제품 전용**")
        st.session_state.templates["s3_1"] = st.text_input("[기술] 특허 상태(출원/공개)", value=st.session_state.templates["s3_1"])
        st.session_state.templates["s4_1"] = st.text_input("[기술] 시험성적서 미제출", value=st.session_state.templates["s4_1"])
        st.session_state.templates["s5_1"] = st.text_input("[제품] 품질경영인증 미제출", value=st.session_state.templates["s5_1"])
        st.session_state.templates["s5_2"] = st.text_input("[제품] 생산현장 증빙 미제출", value=st.session_state.templates["s5_2"])
    # 복잡함을 피하기 위해 일부 핵심 항목만 설정에 노출했습니다. 필요시 추가 가능합니다.

# 얇은 여백 구분선 (공통 필수 규칙 7)
st.markdown('<hr style="margin-top: 15px; margin-bottom: 15px; border: 0; border-top: 1px solid rgba(49, 51, 63, 0.2);">', unsafe_allow_html=True)

# 상단 필터 (녹색기술 vs 녹색제품)
st.markdown("### 📌 검토 유형")
global_type = st.radio("검토 유형 선택", ["tech", "prod"], format_func=lambda x: "🟢 녹색기술" if x == "tech" else "📦 녹색제품", horizontal=True, label_visibility="collapsed")

# 얇은 여백 구분선
st.markdown('<hr style="margin-top: 15px; margin-bottom: 15px; border: 0; border-top: 1px solid rgba(49, 51, 63, 0.2);">', unsafe_allow_html=True)

st.subheader("✅ 검토 체크리스트")

results = []
total_errors = 0
tpl = st.session_state.templates  # 설정된 템플릿 호출용

# [1. 기업 정보 (공통)]
with st.expander("1. 기업 정보 확인", expanded=True):
    sec1_errors = []
    
    if st.checkbox("대표자명 불일치", key="ceoName"):
        sec1_errors.append(tpl["ceoName"])
        total_errors += 1
        
    if st.checkbox("법인등기부등본 / 사업자등록증 관련 오류", key="corpReg"):
        is_indiv = st.radio("해당 기업이 개인사업자인가요?", ["선택 안됨", "예(개인)", "아니오(법인)"], horizontal=True)
        
        if is_indiv == "아니오(법인)":
            sec1_errors.append(tpl["corpReg_corp"])
            total_errors += 1
        elif is_indiv == "예(개인)":
            is_recent = st.radio("사업자등록증이 최근 3개월 이내 발행본인가요?", ["선택 안됨", "예", "아니오"], horizontal=True)
            if is_recent == "아니오":
                sec1_errors.append(tpl["corpReg_indiv"])
                total_errors += 1
                
    if sec1_errors:
        results.append("[기업 정보 보완]\n" + "\n".join(sec1_errors))

# [2. 기술/제품 설명서 (공통)]
with st.expander("2. 설명서 확인", expanded=True):
    sec2_errors = []
    
    st.markdown("**2-1. 시스템 정보 불일치**")
    cols2_1 = st.columns(2)
    if cols2_1[0].checkbox("기술명/제품명 불일치", key="s2_1_1"): 
        sec2_errors.append(tpl["s2_1_1"]); total_errors += 1
    
    st.markdown("**2-2. 1p 요약서 내용 불일치**")
    cols2_2 = st.columns(2)
    if cols2_2[0].checkbox("분류체계", key="s2_2_1"): sec2_errors.append(tpl["s2_2_1"]); total_errors += 1
    if cols2_2[1].checkbox("분류코드", key="s2_2_2"): sec2_errors.append(tpl["s2_2_2"]); total_errors += 1
    if cols2_2[0].checkbox("핵심요소기술", key="s2_2_3"): sec2_errors.append(tpl["s2_2_3"]); total_errors += 1
    if cols2_2[1].checkbox("기술수준", key="s2_2_4"): sec2_errors.append(tpl["s2_2_4"]); total_errors += 1

    st.markdown("**2-3. 목차 누락 (해당 번호 클릭)**")
    toc_items = ["1-1", "1-2", "1-3", "2-1", "2-2", "2-3", "2-4", "3-1", "3-2", "3-3", "4"]
    if global_type == "prod":
        toc_items.insert(3, "1-4")
        
    missing_tocs = []
    cols2_3 = st.columns(4) 
    for idx, toc in enumerate(toc_items):
        if cols2_3[idx % 4].checkbox(f"({toc})", key=f"toc_{toc}"):
            missing_tocs.append(toc)
            total_errors += 1
            
    if missing_tocs:
        sec2_errors.append(tpl["s2_3"].replace("{missing_tocs}", ", ".join(missing_tocs)))
        
    if sec2_errors:
        results.append("[설명서 보완]\n" + "\n".join(sec2_errors))

# [3, 4. 녹색기술 전용 섹션]
if global_type == "tech":
    with st.expander("3. 지식재산권 확인 (녹색기술)", expanded=True):
        sec3_errors = []
        if st.checkbox("등록 특허가 아님 (출원/공개 상태)", key="s3_1"):
            sec3_errors.append(tpl["s3_1"]); total_errors += 1
        if st.checkbox("특허등록원부 미제출", key="s3_2"):
            sec3_errors.append(tpl["s3_2"]); total_errors += 1
        if st.checkbox("공동권리자 존재 및 동의서 미제출", key="s3_3"):
            sec3_errors.append(tpl["s3_3"]); total_errors += 1
            
        if sec3_errors:
            results.append("[지식재산권 보완]\n" + "\n".join(sec3_errors))

    with st.expander("4. 시험성적서 확인 (녹색기술)", expanded=True):
        sec4_errors = []
        if st.checkbox("공인기관성적서 미제출", key="s4_1"):
            ans = st.radio("자체시험성적서 및 사유서를 대신 제출했나요?", ["선택 안됨", "예", "아니오"], horizontal=True)
            if ans == "아니오":
                sec4_errors.append(tpl["s4_1"])
                total_errors += 1
        if st.checkbox("신청 기업 명의 불일치", key="s4_2"):
            sec4_errors.append(tpl["s4_2"]); total_errors += 1
            
        if sec4_errors:
            results.append("[시험성적서 보완]\n" + "\n".join(sec4_errors))

# [3. 녹색제품 전용 섹션]
else:
    with st.expander("3. 제품 관련 서류 확인 (녹색제품)", expanded=True):
        sec5_errors = []
        if st.checkbox("품질경영인증 미제출", key="s5_1"):
            sec5_errors.append(tpl["s5_1"]); total_errors += 1
        if st.checkbox("생산현장 증빙 미제출", key="s5_2"):
            sec5_errors.append(tpl["s5_2"]); total_errors += 1
            
        if sec5_errors:
            results.append("[제품 관련 서류 보완]\n" + "\n".join(sec5_errors))

# --- 7. 사이드바 하단 (결과 출력 및 초기화) ---
# 메인 화면의 체크리스트 결과를 수집한 뒤 사이드바에 출력합니다.
with st.sidebar:
    st.subheader("📝 보완 요청 내용")
    st.info(f"💡 발견된 보완사항: **{total_errors}개**")
    
    final_output = "\n\n".join(results)
    if not final_output:
        final_output = "메인 화면에서 누락/오류 항목을 체크하시면,\n여기에 자동으로 보완 요청 텍스트가 완성됩니다."
        
    st.text_area("결과 복사 (Ctrl+A, Ctrl+C)", value=final_output, height=450, label_visibility="collapsed")
    
    st.markdown('<hr style="margin-top: 15px; margin-bottom: 15px; border: 0; border-top: 1px solid rgba(49, 51, 63, 0.2);">', unsafe_allow_html=True)
    
    if st.button("🔄 초기화 및 새 검토", use_container_width=True):
        clear_form()
        st.rerun()
