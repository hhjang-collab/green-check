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
            font-size: 14px; cursor: pointer; transition: all 0.2s ease;
        }}
        .copy-btn:hover {{ opacity: 1; border-color: #FF4B4B; color: #FF4B4B; }}
    </style>
    <button class="copy-btn" id="{button_id}" onclick="copyToClipboard()">
        📋 클릭하여 복사하기
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
                setTimeout(() => {{ btn.innerText = '📋 클릭하여 복사하기'; }}, 2000);
            }} catch (err) {{  /* 👈 이 부분의 중괄호를 }} 로 수정했습니다 */
                console.error("복사 실패", err);
            }}
        }}
    </script>
    """
    components.html(html_str, height=45)
