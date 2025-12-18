# 이 파일은 Streamlit UI 컴포넌트(로그인 버튼, 사이드바, 채팅 메시지 등)를 렌더링하는 모듈입니다.
import streamlit as st

def render_custom_css():
    st.markdown("""
        <style>
        /* 기본 폰트 설정 */
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Noto Sans KR', sans-serif;
        }

        /* 헤더, 푸터 숨기기 */
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* 메인 컨테이너 너비 조정 */
        .block-container {
            max-width: 800px;
            padding-top: 2rem;
            padding-bottom: 5rem;
        }

        /* 채팅 메시지 스타일 */
        .stChatMessage {
            background-color: transparent;
        }
        
        /* 유저 메시지 배경 */
        div[data-testid="stChatMessage"]:nth-child(odd) {
            background-color: transparent; 
        }

        /* 로그인 버튼 스타일 */
        .login-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.5rem 1rem;
            font-size: 0.875rem;
            font-weight: 500;
            border-radius: 0.375rem;
            background-color: #10a37f;
            color: white;
            border: none;
            cursor: pointer;
            text-decoration: none;
            transition: background-color 0.2s;
        }
        .login-btn:hover {
            background-color: #0d8a6a;
        }

        /* 모달 스타일 (Streamlit dialog 내부) */
        .modal-button {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            padding: 12px;
            margin-bottom: 10px;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            background-color: white;
            color: #374151;
            font-weight: 500;
            text-decoration: none;
            transition: background-color 0.2s;
        }
        .modal-button:hover {
            background-color: #f9fafb;
        }

        .modal-button:hover {
            background-color: #f9fafb;
        }

        /* 팝오버 버튼 위치 조정 (중앙 하단 고정, 반응형) */
        /* 팝오버 버튼 위치 조정 제거 (컬럼 레이아웃 사용) */
        /* [data-testid="stPopover"] {
            position: fixed;
            bottom: 120px;
            left: 50%;
            transform: translateX(-50%);
            width: fit-content !important;
            min-width: auto !important;
            z-index: 1000;
        } */
        
        /* 팝오버 버튼 컨테이너 (Horizontal Block) 타겟팅 및 위치 고정 */
        div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPopover"]) {
            position: fixed;
            bottom: 105px; /* 채팅 입력창과 겹치지 않도록 높이 상향 조정 */
            left: 50%;
            transform: translateX(-50%);
            width: auto !important;
            z-index: 9999;
            background-color: transparent;
            gap: 8px;
            justify-content: center;
            pointer-events: none;
        }

        /* 내부 요소 클릭 가능하게 복구 */
        div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPopover"]) * {
            pointer-events: auto;
        }

        /* 내부 컬럼 너비 자동 조정 */
        div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPopover"]) div[data-testid="stColumn"] {
            width: auto !important;
            flex: 0 0 auto !important;
            min-width: auto !important;
        }
        
        /* 팝오버 버튼 자체 스타일 (작게) */
        [data-testid="stPopover"] > button {
            border: 1px solid #e5e7eb;
            background-color: white;
            color: #374151;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 2px 8px !important;
            font-size: 13px !important;
            min-height: unset !important;
            height: 32px !important;
            border-radius: 16px !important; /* 둥근 모서리 */
        }
        
        /* 팝오버 아이콘과 텍스트 간격 조정 */
        [data-testid="stPopover"] > button > div {
            gap: 4px !important;
        }
        </style>
    """, unsafe_allow_html=True)

@st.dialog("로그인")
def login_modal(auth_url):
    st.markdown("이전 대화기록을 계속 보고 싶다면 로그인을 해주세요")
    st.markdown("---")
    
    # 구글 로그인 버튼
    st.markdown(
        f"""
        <a href="{auth_url}" target="_blank" class="modal-button" style="text-decoration:none; color:inherit;">
            <div style="display:flex; align-items:center; gap:10px;">
                <img src="https://www.google.com/favicon.ico" width="20" height="20">
                <span>Google로 계속하기 (새 창)</span>
            </div>
        </a>
        """,
        unsafe_allow_html=True
    )

def render_login_button():
    # 상단 우측에 배치
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("로그인", key="login_trigger"):
            return True
    return False

def render_logout_button():
    # 상단 우측에 배치 (로그인 버튼과 동일한 위치)
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("로그아웃", key="logout_trigger"):
            return True
    return False

def render_sidebar(sessions=None, on_session_select=None, on_new_chat=None, on_delete_session=None):
    with st.sidebar:
        # 새 채팅 버튼
        if st.button("✨ 새 채팅", key="new_chat_btn", use_container_width=True):
            if on_new_chat:
                on_new_chat()
        
        st.markdown("---")

        # 분석가 페르소나 선택
        st.subheader("🕵️ 분석가 선택")
        persona_map = {
            "🧥 일반 컨설턴트 (밸런스)": "general",
            "🦅 냉철한 VC (비판적/수익)": "vc",
            "📣 마케팅 전문가 (트렌드)": "marketer"
        }
        selected_persona_name = st.selectbox(
            "누구에게 평가받으시겠어요?",
            list(persona_map.keys()),
            key="selected_persona_ui"
        )
        # 선택된 페르소나 코드 반환 (세션 상태 등 외부에서 사용 가능하도록)
        st.session_state["current_persona"] = persona_map[selected_persona_name]
        
        st.markdown("---")
        
        # 채팅 기록 목록
        if sessions:
            st.caption("최근 대화")
            for session in sessions:
                # 제목이 너무 길면 자르기
                title = session['title']
                if len(title) > 15:
                    title = title[:15] + "..."
                
                col1, col2 = st.columns([5, 1])
                with col1:
                    if st.button(f"💬 {title}", key=f"session_{session['id']}", use_container_width=True):
                        if on_session_select:
                            on_session_select(session['id'])
                with col2:
                    if st.button("🗑️", key=f"del_{session['id']}", help="삭제"):
                        if on_delete_session:
                            on_delete_session(session['id'])
        else:
            st.caption("대화 기록이 없습니다.")

        st.markdown("---")
        # st.title("Poten.Ai") # 상단으로 이동
     

def render_header():
    st.markdown("""
        <h1 style='color: #4F8BF9; font-size: 24px; margin-bottom: 20px;'>Poten.Ai</h1>
    """, unsafe_allow_html=True)

def display_chat_messages(messages):
    for msg in messages:
        with st.chat_message(msg["role"]):
            if isinstance(msg["content"], list):
                for item in msg["content"]:
                    if item["type"] == "text":
                        st.write(item["text"])
                    elif item["type"] == "image_url":
                        st.image(item["image_url"]["url"])
            else:
                st.write(msg["content"])

def display_user_info(user_info):
    # 사이드바 하단이나 적절한 곳에 표시
    with st.sidebar:
        st.markdown("---")
        st.write(f"**{user_info['name']}**님")
        st.caption(user_info['email'])
