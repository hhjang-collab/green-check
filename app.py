import streamlit as st
import streamlit.components.v1 as components
import base64
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- 1. 페이지 기본 설정 ---
st.set_page_config(page_title="녹색인증 서류 검토", layout="centered", initial_sidebar_state="expanded")

# --- [수정] 구글 스프레드시트 누적 저장 함수 ---
def save_to_google_sheets(global_type, req_type, total_errors, selected_items):
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        
        sheet_name = st.secrets.get("GOOGLE_SHEET_NAME", "녹색인증_검토이력")
        sheet = client.open(sheet_name).sheet1
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        type_kor = "기술" if global_type == "tech" else ("제품" if global_type == "prod" else "전문기업")
        req_kor = "신규" if req_type == "new" else "연장"
        
        # 📌 수정된 부분: 긴 문장 대신 선택된 항목 이름들을 쉼표로 연결하여 저장
        items_str = ", ".join(selected_items) if selected_items else "오류 없음"
        
        sheet.append_row([current_time, type_kor, req_kor, total_errors, items_str])
        return True
    except Exception as e:
        st.error(f"❌ 구글 시트 저장 실패: {e}")
        return False

# --- 2. 보안 (비밀번호) 로직 ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.warning("🔒 보안을 위해 비밀번호를 입력해주세요.")
    with st.form("login_form"):
        pwd = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("확인")
        
        if submitted:
            expected_pwd = st.secrets.get("APP_PASSWORD", "1234") 
            if pwd == expected_pwd:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("비밀번호가 일치하지 않습니다.")
    st.stop()

# --- 3. UI 최적화 및 회사 로고 설정 ---
def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

logo_base64 = get_base64_of_bin_file("company_logo.png") 

custom_css = f"""
<style>
    [data-testid="InputInstructions"] {{display: none !important;}}
    
    [data-testid="stRadio"] > div[role="radiogroup"] {{
        flex-wrap: nowrap !important;
        gap: 0.8rem !important;
    }}
    
    [data-testid="stSidebar"] textarea {{
        font-size: 13px !important;
        line-height: 1.6 !important;
    }}
    
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
"""
if logo_base64:
    custom_css += f'<img src="data:image/png;base64,{logo_base64}" class="company-logo">'

st.markdown(custom_css, unsafe_allow_html=True)

# --- 4. 자동 생성 문구 템플릿 정의 ---
default_templates = {
    "ceo_err": "제출하신 서류와 시스템 상의 대표자 명이 일치하지 않습니다.",
    "corp_reg_main": "사업자등록증, 법인등기부등본은 기업으로 로그인하여 회원정보 수정란에서 첨부해 주시기 바랍니다.",
    "corp_biz_miss": " - 사업자등록증을 제출하여 주시기 바랍니다.",
    "corp_biz_old": " - 개인사업자의 경우, 사업자등록증을 최근 3개월 이내 발행본으로 제출해 주시기 바랍니다.",
    "corp_reg_miss": " - 법인등기부등본을 최근 3개월 이내 발행본으로 제출해 주시기 바랍니다.",
    "corp_reg_view": " - 법인등기부등본을 열람용이 아닌 제출용으로 첨부해주셔야 합니다.",
    
    "ext_tech_cert": "기존 녹색기술인증서와 녹색성과보고서(서식자료실)을 제출해 주시기 바랍니다.",
    "ext_tech_name": "기존 녹색기술인증서의 기술명과 연장신청하는 녹색기술의 기술명이 일치하지 않습니다.\n - 변경을 원하시면 신규로 신청해 주시고, 연장을 하시려면 기존 기술명으로 설명서와 신청서 모두 일치시켜주시기 바랍니다.",
    "ext_prod_cert": "기존 녹색기술제품확인서와 녹색성과보고서(서식자료실)을 제출해 주시기 바랍니다.",
    "ext_prod_name": "기존 녹색제품확인서의 제품명과 연장신청하는 녹색기술제품의 제품명이 일치하지 않습니다.\n - 변경을 원하시면 신규로 신청해 주시고, 연장을 하시려면 기존 제품명으로 설명서와 신청서 모두 일치시켜주시기 바랍니다.",
    "ext_prod_model": "연장신청시 모델 추가/변경은 불가능합니다. 모델 추가/변경 시 신규로 신청해주셔야 합니다.",
    
    "ext_comp_cert": "기존 녹색전문기업확인서와 성과분석보고서를 제출해 주시기 바랍니다.",
    "ext_comp_name": "기존 녹색전문기업확인서의 기업명과 연장신청하는 기업명이 일치하지 않습니다.",

    "doc_open_err": "신청 {type} 설명서 파일이 열리지 않습니다. 다시 올려주시기 바랍니다.",
    "doc_missing": "녹색인증 홈페이지의 \"규정/서식 > 서식자료실\"에서 \"녹색기술(제품)신청서 및 작성가이드라인(2024)\" 다운로드하여 작성 후 제출해 주시기 바랍니다.",
    "doc_name_err": "{type}명 불일치: {type} 설명서와 시스템 신청서 간 {type}명이 일치하지 않습니다.",
    "doc_level_err": "설명서 상 기술수준의 내용이 온라인신청서의 내용과 일치하지 않습니다.",
    "doc_comp_err": "설명서 상 기업명은 시스템과 동일하게 기재되어야 합니다.",
    
    "doc_core_tech_err": "설명서(1p): 핵심요소기술의 내용이 온라인신청서의 내용과 일치하지 않습니다.",
    
    "doc_toc_err": "서식자료실의 신청{type} 설명서 양식을 준수하여 세부 항목을 모두 작성해 주시기 바랍니다. ({tocs} 누락, 서식자료실의 작성가이드라인 참조)",
    
    "tech_as_prod": "본 신청서는 녹색기술인증 건으로, 기술설명서 양식에 제품명이 아닌 기술명을 시스템과 동일하게 작성해 주시기 바랍니다. \n * 작성 예) OOOO 기술, OOOO 방법",
    "prod_as_tech": "본 신청서는 녹색기술제품확인 건으로, 제품 설명서 양식에 기술명이 아닌 제품명을 시스템과 동일하게 작성해 주시기 바랍니다.",
    "prod_inc_tech": " - 제품명 오류: 신청 기술 설명서 상 제품명에 기술명이 함께 기재되어 있습니다. 기술명을 제외하고 제품명을 시스템 상의 제품명과 동일하게 작성해주시기 바랍니다.",
    "prod_inc_model": " - 신청 제품 설명서 상 제품명에 모델명이 함께 기재되어 있습니다. 모델명을 제외하고 제품명을 시스템 상의 제품명과 동일하게 작성해주시기 바랍니다.",
    "prod_model_info": "모델정보 누락: 신청모델별 차이를 확인할 수 있는 정보(스펙, 치수, 용량 등)을 작성해 주시기 바랍니다. (설명서 또는 붙임)",

    "ip_open_err": "파일이 오류가 있어 열람할 수 없습니다.",
    "ip_docs_err": "지식재산권 등록은 특허등록원부로 제출해 주시기 바랍니다.",
    "ip_owner_err": "지식재산권 상의 권리자는 반드시 신청 기업명 이어야 합니다. 이전 기업명이면 수정하여 제출해 주셔야 합니다.",
    "ip_not_reg": "등록된 특허로 된 기술의 등록원부로 제출되어야 합니다. (공지사항 내 \"2025년 FAQ 매뉴얼\" 73p. 참조)",
    "ip_lic_err": "특허등록원부의 전용/통상실시권자에 [{comp}]이 존재하지 않습니다.\n ※ 지식재산권 상의 권리자는 반드시 신청 기업명이어야 합니다. [공지사항 내 \"2025 녹색인증 FAQ 매뉴얼\", p.74 참조]",
    "ip_agree_err": "지식재산권 활용동의서: 최종권리자가 다수인 경우 공동권리자의 동의서(서식자료실의 지식재산권 활용 동의서)를 작성해 주셔야 합니다.\n ※ 통상/전용실시권을 받은 경우, 지식재산권 활용동의서의 작성이 필요없음",
    "ip_ceo_patent": "지식재산권 상의 권리자는 반드시 신청 기업명 이어야 합니다. 기업법인과 대표자 명의의 특허일지라도 녹색인증 신청 시, 지식재산권 보유에 대한 권리를 양도, 위임에 대한 계약서를 별첨하거나 실시권을 받아야 합니다.",

    "test_kolas": "시험성적서는 KOLAS 등 공인 시험성적기관에서 진행한 서류로 제출해주시기 바랍니다.\n - 공인된 외부기관이 아닌 자체 시험성적서 혹은 의뢰자 제시 시험성적서를 제출하셔야 할 경우, 사유서와 함께 제출해 주시기 바랍니다.",
    "test_old": "최근 3년이내 자료로 제출해주시기 바랍니다. (공지사항 내 \"2025 녹색인증 FAQ 매뉴얼\", 10p. 참조)",
    "test_self": "공인된 외부기관이 아닌 자체 시험성적서 혹은 의뢰자 제시 시험성적서를 제출하셔야 할 경우, 사유서와 함께 제출해 주시기 바랍니다.",
    "test_client": "시험성적서 상에 모든 신청 업체가 의뢰인(기업)으로 확인되야 합니다. 시험성적서 관련해서 자세한 사항은 평가기관에 문의바랍니다.",

    "prod_iso": "품질경영 증빙은 KS 인증 또는 ISO 인증 서류로 준비/제출해 주셔야 합니다. (공지사항 내 \"2025 녹색인증 FAQ 매뉴얼\", 56p. 참조)\n - ISO/KS/NET/NEP/JIS/GOST/CCC 등",
    "fac_ceo": "사업자등록증과 공장등록증의 대표자 명이 불일치 합니다.",
    "fac_missing": "공장등록증 또는 직접생산증명서를 제출해 주시기 바랍니다. OEM 생산인 경우 OEM계약서 또는 OEM 제조의뢰사실을 증빙할 수 있는 증빙 문서를 제출해 주시기 바랍니다.",
    
    "comp_sales_err": "녹색기술 매출비중내역서를 제출해 주시기 바랍니다.",
    "comp_cpa_err": "공인회계사 확인서를 지정된 양식으로 작성해주시기 바랍니다.\n - 서식자료실의 녹색전문기업확인 구비서류 중 매출비중내역서 및 공인회계사(세무사) 확인서 작성예시 참조",
    "comp_fin_err": "최근 결산이 완료된 재무제표를 제출해 주시기 바랍니다."
}

# --- 완벽한 체크박스 강제 초기화 로직 (Foolproof) ---
def clear_form():
    keep_keys = ["authenticated", "global_type", "req_type"]
    for key in list(st.session_state.keys()):
        if key not in keep_keys:
            if isinstance(st.session_state[key], bool):
                st.session_state[key] = False
            else:
                del st.session_state[key]

# --- 커스텀 스마트 복사 버튼 (JS 활용) ---
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
            border: 1px solid currentColor; border-radius: 8px; opacity: 0.7;
            font-size: 16px; cursor: pointer; transition: all 0.2s ease;
        }}
        .copy-btn:hover {{ opacity: 1; border-color: #FF4B4B; color: #FF4B4B; }}
    </style>
    <button class="copy-btn" id="{button_id}" onclick="copyToClipboard()">
        📋 클릭하여 문구 복사
    </button>
    <script>
        const style = window.getComputedStyle(window.parent.document.body);
        const btn = document.getElementById('{button_id}');
        btn.style.color = style.color;
        
        function copyToClipboard() {{
            try {{
                const text = decodeURIComponent(escape(window.atob('{b64_text}')));
                const el = document.createElement('textarea');
                el.value = text;
                document.body.appendChild(el);
                el.select();
                document.execCommand('copy');
                document.body.removeChild(el);
                
                btn.innerText = '✅ 복사 완료!';
                setTimeout(() => {{ btn.innerText = '📋 클릭하여 문구 복사하기'; }}, 2000);
            }} catch (err) {{
                console.error("복사 실패", err);
            }}
        }}
    </script>
    """
    components.html(html_str, height=45)

# --- [신규 추가] 저장 및 복사 통합 모달 팝업창 UI ---
@st.dialog("💾 검토 결과 내보내기")
def export_dialog(global_type, req_type, total_errors, results, final_output):
    st.write("📝 **생성된 보완 요청 문구를 구글 시트에 백업하고 복사하세요.**")
    
    # 1. 구글 스프레드시트 저장 영역
    st.markdown("### 1. 데이터 저장")
    if st.button("💾 내역을 시트에 기록", use_container_width=True, type="secondary"):
        with st.spinner("시트에 기록 중..."):
            success = save_to_google_sheets(global_type, req_type, total_errors, results)
        if success:
            st.success("✅ 구글 스프레드시트에 무사히 저장되었습니다!")
            
    st.write("")
    
    # 2. 클립보드 복사 영역
    st.markdown("### 2. 텍스트 복사")
    render_copy_button(final_output)
    
    st.write("")
    st.caption("💡 팁: 데이터 백업 후 텍스트 복사하기를 눌러주세요.")

# --- 5. 사이드바 상단 구성 ---
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
    
    st.subheader("📝 보완 요청")
    error_count_placeholder = st.empty()

# --- 6. 메인 화면 ---
st.title("📄 녹색인증 신청 서류 검토")

col1, col2 = st.columns(2)
with col1:
    global_type = st.radio(
        "검토 유형", 
        ["tech", "prod", "company"], 
        format_func=lambda x: "기술" if x == "tech" else ("제품" if x == "prod" else "기업"), 
        horizontal=True, key="global_type"
    )
with col2:
    req_type = st.radio(
        "신청 구분", 
        ["new", "ext"], 
        format_func=lambda x: "신규" if x == "new" else "연장", 
        horizontal=True, key="req_type"
    )

st.markdown('<hr style="margin-top: 5px; margin-bottom: 15px; border: 0; border-top: 1px solid rgba(49, 51, 63, 0.2);">', unsafe_allow_html=True)

results = []
total_errors = 0
tpl = default_templates 

type_str = "기술" if global_type == "tech" else ("제품" if global_type == "prod" else "전문기업")

# [1. 기업 정보 (공통)]
with st.expander("1. 기업 정보 오류", expanded=True):
    if st.checkbox("대표자명 불일치", key="ceo_err"):
        results.append(tpl["ceo_err"]); total_errors += 1
        
    corp_sub_errors = []
    if st.checkbox("사업자등록증 미제출", key="biz_miss"): corp_sub_errors.append(tpl["corp_biz_miss"]); total_errors += 1
    if st.checkbox("(개인) 사업자등록증 3개월 초과", key="biz_old"): corp_sub_errors.append(tpl["corp_biz_old"]); total_errors += 1
    if st.checkbox("(법인) 법인등기부등본 미제출(3개월 초과)", key="reg_miss"): corp_sub_errors.append(tpl["corp_reg_miss"]); total_errors += 1
    if st.checkbox("법인등기부등본(열람용)", key="reg_view"): corp_sub_errors.append(tpl["corp_reg_view"]); total_errors += 1
        
    if corp_sub_errors:
        results.append(tpl["corp_reg_main"] + "\n" + "\n".join(corp_sub_errors))

# [2. 연장 서류 (연장 선택 시에만)]
if req_type == "ext":
    with st.expander(f"2. {type_str} 연장 서류", expanded=True):
        if global_type == "tech":
            if st.checkbox("인증서/성과보고서 누락", key="ext_t_cert"): results.append(tpl["ext_tech_cert"]); total_errors += 1
            if st.checkbox("기술명 불일치", key="ext_t_name"): results.append(tpl["ext_tech_name"]); total_errors += 1
        elif global_type == "prod":
            if st.checkbox("확인서/성과보고서 누락", key="ext_p_cert"): results.append(tpl["ext_prod_cert"]); total_errors += 1
            if st.checkbox("제품명 불일치", key="ext_p_name"): results.append(tpl["ext_prod_name"]); total_errors += 1
            if st.checkbox("모델 추가/변경", key="ext_p_model"): results.append(tpl["ext_prod_model"]); total_errors += 1
        elif global_type == "company":
            if st.checkbox("확인서/성과분석보고서 누락", key="ext_c_cert"): results.append(tpl["ext_comp_cert"]); total_errors += 1
            if st.checkbox("기업명 불일치", key="ext_c_name"): results.append(tpl["ext_comp_name"]); total_errors += 1

# [3. 설명서 (공통 - 기술, 제품 전용)]
if global_type in ["tech", "prod"]:
    with st.expander(f"3. {type_str} 설명서", expanded=True):
        st.markdown("**🔹 설명서 파일**")
        cols_doc_err = st.columns(2)
        if cols_doc_err[0].checkbox("파일 오류", key="doc_open"): results.append(tpl["doc_open_err"].replace("{type}", type_str)); total_errors += 1
        if cols_doc_err[1].checkbox("설명서 미제출", key="doc_miss"): results.append(tpl["doc_missing"]); total_errors += 1
            
        st.write("") 
        st.markdown("**🔹 내용 오류**")
        
        if global_type == "tech":
            cols_mismatch_tech = st.columns(2)
            if cols_mismatch_tech[0].checkbox("기술수준", key="doc_lvl"): results.append(tpl["doc_level_err"]); total_errors += 1
            if cols_mismatch_tech[1].checkbox("기업명", key="doc_comp"): results.append(tpl["doc_comp_err"]); total_errors += 1
            
            with cols_mismatch_tech[0]:
                tech_err = st.checkbox("기술명", key="tech_err")
            if tech_err:
                ans = st.radio("오류 내용", ["명칭 불일치", "제품명 작성"], horizontal=True, key="tech_err_type")
                if ans == "명칭 불일치": results.append(tpl["doc_name_err"].replace("{type}", type_str)); total_errors += 1
                elif ans == "제품명 작성": results.append(tpl["tech_as_prod"]); total_errors += 1
            
            if cols_mismatch_tech[1].checkbox("핵심요소기술", key="doc_core_tech"): 
                results.append(tpl["doc_core_tech_err"]); total_errors += 1

        else:
            cols_mismatch_1 = st.columns(2)
            if cols_mismatch_1[0].checkbox("기술수준", key="doc_lvl"): results.append(tpl["doc_level_err"]); total_errors += 1
            if cols_mismatch_1[1].checkbox("기업명", key="doc_comp"): results.append(tpl["doc_comp_err"]); total_errors += 1
                
            cols_mismatch_2 = st.columns(2)
            with cols_mismatch_2[0]:
                prod_err = st.checkbox("제품명", key="prod_err")
            with cols_mismatch_2[1]:
                if st.checkbox("모델별 정보 누락", key="prod_model_info"): results.append(tpl["prod_model_info"]); total_errors += 1
                
            if prod_err:
                ans = st.radio("오류 내용", ["명칭 불일치", "기술명 포함", "모델명 포함"], horizontal=True, key="prod_err_type")
                if ans == "명칭 불일치": results.append(tpl["doc_name_err"].replace("{type}", type_str)); total_errors += 1
                elif ans == "기술명 포함": results.append(tpl["prod_as_tech"] + "\n" + tpl["prod_inc_tech"]); total_errors += 1
                elif ans == "모델명 포함": results.append(tpl["prod_as_tech"] + "\n" + tpl["prod_inc_model"]); total_errors += 1

        st.write("") 
        st.markdown("**🔹 목차 누락**")
        toc_items = ["1-1", "1-2", "1-3", "2-1", "2-2", "2-3", "2-4", "3-1", "3-2", "3-3", "4"]
        if global_type == "prod": toc_items.insert(3, "1-4")
            
        missing_tocs = []
        cols_tocs = st.columns(4) 
        for idx, toc in enumerate(toc_items):
            if cols_tocs[idx % 4].checkbox(f"({toc})", key=f"toc_{toc}"):
                missing_tocs.append(toc); total_errors += 1
        if missing_tocs:
            results.append(tpl["doc_toc_err"].replace("{type}", type_str).replace("{tocs}", ", ".join(missing_tocs)))

# [4. 지식재산권 (기술 전용)]
if global_type == "tech":
    with st.expander("4. 지식재산권 검토", expanded=True):
        cols4 = st.columns(2)
        if cols4[0].checkbox("파일 오류", key="ip_op"): results.append(tpl["ip_open_err"]); total_errors += 1
        if cols4[1].checkbox("등록원부 누락", key="ip_docs"): results.append(tpl["ip_docs_err"]); total_errors += 1
        
        if cols4[0].checkbox("출원/공개 특허", key="ip_notreg"): results.append(tpl["ip_not_reg"]); total_errors += 1
        if cols4[1].checkbox("권리자 기업명 불일치", key="ip_own"): results.append(tpl["ip_owner_err"]); total_errors += 1
        
        if cols4[0].checkbox("다수권리자 활용동의서 누락", key="ip_agr"): results.append(tpl["ip_agree_err"]); total_errors += 1
        if cols4[1].checkbox("대표자 명의 특허", key="ip_ceo_pat"): results.append(tpl["ip_ceo_patent"]); total_errors += 1
        
        if st.checkbox("실시권자 누락 (업체명 기입)", key="ip_lic"):
            comp_name = st.text_input("누락된 업체명 입력", key="ip_lic_name")
            if comp_name: results.append(tpl["ip_lic_err"].replace("{comp}", f"업체명:{comp_name}")); total_errors += 1
            else: results.append(tpl["ip_lic_err"].replace("{comp}", "업체명")); total_errors += 1

# [5. 시험성적서 (기술 전용)]
if global_type == "tech":
    with st.expander("5. 시험성적서 검토", expanded=True):
        st.caption("※ 환경표시인증이 있는 경우 시험성적서 대체 가능")
        cols5 = st.columns(2)
        if cols5[0].checkbox("공인시험기관 아님", key="t_kolas"): results.append(tpl["test_kolas"]); total_errors += 1
        if cols5[1].checkbox("3년 초과 자료", key="t_old"): results.append(tpl["test_old"]); total_errors += 1
        if cols5[0].checkbox("자체성적서 사유서 누락", key="t_self"): results.append(tpl["test_self"]); total_errors += 1
        if cols5[1].checkbox("의뢰인 불일치", key="t_client"): results.append(tpl["test_client"]); total_errors += 1

# [6. 제품 추가 서류 (제품 전용)]
if global_type == "prod":
    with st.expander("4. 녹색제품 필수 서류", expanded=True):
        if st.checkbox("품질경영 증빙 누락", key="p_iso"): results.append(tpl["prod_iso"]); total_errors += 1
        if st.checkbox("공장등록증 대표자 불일치", key="fac_ceo"): results.append(tpl["fac_ceo"]); total_errors += 1
        if st.checkbox("공장등록증/직접생산증명서/OEM계약서 누락", key="fac_miss"): results.append(tpl["fac_missing"]); total_errors += 1

# [7. 전문기업 필수 서류 (전문기업 전용)]
if global_type == "company":
    with st.expander("3. 전문기업 필수 서류", expanded=True):
        if st.checkbox("매출비중내역서 누락", key="c_sales"): results.append(tpl["comp_sales_err"]); total_errors += 1
        if st.checkbox("공인회계사/세무사 확인서 누락", key="c_cpa"): results.append(tpl["comp_cpa_err"]); total_errors += 1
        if st.checkbox("재무제표 누락", key="c_fin"): results.append(tpl["comp_fin_err"]); total_errors += 1

# --- 사이드바 하단 버튼 로직 ---
with st.sidebar:
    # ... (결과 텍스트 출력 부분은 기존과 동일) ...
    
    # 세션 스테이트에 저장 완료 상태를 기록 (최상단에 선언 필요: st.session_state.setdefault("is_saved", False))
    if not st.session_state.get("is_saved", False):
        if st.button("💾 검토 결과 시트에 기록", type="primary", use_container_width=True):
            if total_errors > 0 or results:
                with st.spinner("구글 시트에 저장 중..."):
                    # 1번 질문에서 수정한 통계용 데이터 저장 로직 실행
                    selected_item_names = [label for key, label in checkbox_labels.items() if st.session_state.get(key)]
                    success = save_to_google_sheets(global_type, req_type, total_errors, selected_item_names)
                    
                    if success:
                        st.session_state["is_saved"] = True
                        st.rerun() # 화면을 새로고침하여 복사 버튼을 띄움
            else:
                st.warning("⚠️ 선택된 보완 항목이 없습니다.")
    else:
        # 저장이 완료된 상태면 복사 버튼만 보여줌
        st.success("✅ 시트 저장 완료! 텍스트를 복사하세요.")
        render_copy_button(final_output) # 기존에 만들어두신 훌륭한 JS 복사 버튼 재활용
        
        st.write("")
        if st.button("🔄 새로운 검토 시작", use_container_width=True):
            st.session_state["is_saved"] = False
            clear_form()
            st.rerun()
