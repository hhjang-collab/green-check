import streamlit as st

# --- 페이지 기본 설정 ---
st.set_page_config(page_title="녹색인증 서류 검토 Agent PRO", layout="wide", initial_sidebar_state="expanded")

# --- 상태 초기화 함수 ---
def clear_form():
    for key in st.session_state.keys():
        del st.session_state[key]

st.title("🔍 녹색인증 서류검토 Agent PRO")

# --- 1. 상단 필터 (녹색기술 vs 녹색제품) ---
st.markdown("### 📌 검토 유형")
global_type = st.radio("검토 유형 선택", ["tech", "prod"], format_func=lambda x: "🟢 녹색기술" if x == "tech" else "📦 녹색제품", horizontal=True, label_visibility="collapsed")

st.divider()

col_left, col_right = st.columns([6, 4])

# --- 결과 취합용 변수 ---
results = []
total_errors = 0

with col_left:
    st.subheader("✅ 검토 체크리스트 (오류/미제출 항목 체크)")

    # [1. 기업 정보 (공통)]
    with st.expander("1. 기업 정보 확인", expanded=True):
        sec1_errors = []
        
        if st.checkbox("대표자명 불일치", key="ceoName"):
            sec1_errors.append("- 제출하신 서류와 시스템 상의 대표자 명이 일치하지 않습니다.")
            total_errors += 1
            
        if st.checkbox("법인등기부등본 / 사업자등록증 관련 오류", key="corpReg"):
            is_indiv = st.radio("해당 기업이 개인사업자인가요?", ["선택 안됨", "예(개인)", "아니오(법인)"], horizontal=True)
            
            if is_indiv == "아니오(법인)":
                sec1_errors.append("- 법인등기부등본(최근 3개월 이내 발행본, 제출용)을 첨부하여 주시기 바랍니다.")
                total_errors += 1
            elif is_indiv == "예(개인)":
                is_recent = st.radio("사업자등록증이 최근 3개월 이내 발행본인가요?", ["선택 안됨", "예", "아니오"], horizontal=True)
                if is_recent == "아니오":
                    sec1_errors.append("- 개인사업자의 경우, 사업자등록증을 최근 3개월 이내 발행본으로 제출해 주시기 바랍니다.")
                    total_errors += 1
                    
        if sec1_errors:
            results.append("[기업 정보 보완]\n" + "\n".join(sec1_errors))

    # [2. 기술/제품 설명서 (공통)]
    with st.expander("2. 설명서 확인", expanded=True):
        sec2_errors = []
        
        st.markdown("**2-1. 시스템 정보 불일치**")
        cols2_1 = st.columns(2)
        if cols2_1[0].checkbox("기술명/제품명 불일치", key="s2_1_1"): 
            sec2_errors.append("- 요약서의 기술명(또는 제품명)이 시스템 신청 정보와 일치하지 않습니다."); total_errors += 1
        
        st.markdown("**2-2. 1p 요약서 내용 불일치**")
        cols2_2 = st.columns(4)
        if cols2_2[0].checkbox("분류체계", key="s2_2_1"): sec2_errors.append("- 요약서: 분류체계 내용이 시스템과 불일치합니다."); total_errors += 1
        if cols2_2[1].checkbox("분류코드", key="s2_2_2"): sec2_errors.append("- 요약서: 분류코드 내용이 시스템과 불일치합니다."); total_errors += 1
        if cols2_2[2].checkbox("핵심요소기술", key="s2_2_3"): sec2_errors.append("- 요약서: 핵심요소기술 내용이 시스템과 불일치합니다."); total_errors += 1
        if cols2_2[3].checkbox("기술수준", key="s2_2_4"): sec2_errors.append("- 요약서: 기술수준 내용이 시스템과 불일치합니다."); total_errors += 1

        st.markdown("**2-3. 목차 누락 (해당 번호 클릭)**")
        # 유형에 따른 목차 구성
        toc_items = ["1-1", "1-2", "1-3", "2-1", "2-2", "2-3", "2-4", "3-1", "3-2", "3-3", "4"]
        if global_type == "prod":
            toc_items.insert(3, "1-4") # 녹색제품일 경우 1-4 추가
            
        missing_tocs = []
        cols2_3 = st.columns(6)
        for idx, toc in enumerate(toc_items):
            if cols2_3[idx % 6].checkbox(f"({toc})", key=f"toc_{toc}"):
                missing_tocs.append(toc)
                total_errors += 1
                
        if missing_tocs:
            sec2_errors.append(f"- 설명서 내용 누락: 서식자료실 양식을 준수하여 세부 항목({', '.join(missing_tocs)})을 작성해 주시기 바랍니다.")
            
        if sec2_errors:
            results.append("[설명서 보완]\n" + "\n".join(sec2_errors))

    # --- 3. 녹색기술 전용 섹션 ---
    if global_type == "tech":
        with st.expander("3. 지식재산권 확인 (녹색기술)", expanded=True):
            sec3_errors = []
            if st.checkbox("등록 특허가 아님 (출원/공개 상태)", key="s3_1"):
                sec3_errors.append("- 출원 또는 공개 상태가 아닌 등록 완료된 특허로 제출해 주시기 바랍니다."); total_errors += 1
            if st.checkbox("특허등록원부 미제출", key="s3_2"):
                sec3_errors.append("- 등록된 특허기술의 '특허등록원부'를 제출해 주시기 바랍니다."); total_errors += 1
            
            if st.checkbox("공동권리자 존재 및 지재권 활용동의서 미제출", key="s3_3"):
                sec3_errors.append("- 최종권리자가 타기업 또는 다수인 경우, 공동권리자의 '지식재산권 활용 동의서'를 작성해 주셔야 합니다."); total_errors += 1
                
            if sec3_errors:
                results.append("[지식재산권 보완]\n" + "\n".join(sec3_errors))

        with st.expander("4. 시험성적서 확인 (녹색기술)", expanded=True):
            sec4_errors = []
            if st.checkbox("공인기관성적서 미제출", key="s4_1"):
                ans = st.radio("자체시험성적서 및 사유서를 대신 제출했나요?", ["선택 안됨", "예", "아니오"], horizontal=True)
                if ans == "아니오":
                    sec4_errors.append("- 공인된 외부기관(KOLAS 등)의 시험성적서를 제출하거나, 자체/의뢰자 제시 성적서일 경우 반드시 '사유서'를 함께 제출해 주시기 바랍니다.")
                    total_errors += 1
                    
            if st.checkbox("신청 기업 명의 불일치", key="s4_2"):
                sec4_errors.append("- 시험성적서 상의 의뢰인(기업) 명의가 신청 업체와 일치해야 합니다."); total_errors += 1
                
            if sec4_errors:
                results.append("[시험성적서 보완]\n" + "\n".join(sec4_errors))

    # --- 4. 녹색제품 전용 섹션 ---
    else:
        with st.expander("3. 제품 관련 서류 확인 (녹색제품)", expanded=True):
            sec5_errors = []
            if st.checkbox("품질경영인증 미제출", key="s5_1"):
                sec5_errors.append("- 품질경영 증빙은 KS 인증 또는 ISO 인증(ISO 9001/14001 등) 서류로 준비하여 제출해 주셔야 합니다."); total_errors += 1
            if st.checkbox("생산현장 증빙 미제출 (공장등록증, 직접생산 등)", key="s5_2"):
                sec5_errors.append("- 공장등록증, 직접생산확인서 또는 생산현장증빙서류(OEM계약서 및 세금계산서 등)를 첨부하여 주시기 바랍니다."); total_errors += 1
                
            if sec5_errors:
                results.append("[제품 관련 서류 보완]\n" + "\n".join(sec5_errors))

with col_right:
    st.subheader("📝 종합 보완 요청서")
    
    st.info(f"💡 현재 발견된 보완사항: **{total_errors}개**")
    
    final_output = "\n\n".join(results)
    if not final_output:
        final_output = "왼쪽 체크리스트에서 미제출 또는 오류 항목을 선택하면\n여기에 자동으로 보완 요청 텍스트가 완성됩니다."
        
    st.text_area("결과 복사 영역 (클릭 후 Ctrl+A, Ctrl+C)", value=final_output, height=500, label_visibility="collapsed")
    
    if st.button("🔄 새로운 서류 검토하기 (초기화)", use_container_width=True):
        clear_form()
        st.rerun()
