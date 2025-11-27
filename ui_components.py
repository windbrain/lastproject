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
        </style>
    """, unsafe_allow_html=True)

@st.dialog("로그인 또는 회원 가입")
def login_modal(auth_url):
    st.markdown("더 스마트한 응답, 파일 및 이미지 업로드 등을 이용할 수 있습니다.")
    st.markdown("---")
    
    # 구글 로그인 버튼
    st.markdown(
        f"""
        <a href="{auth_url}" target="_self" class="modal-button" style="text-decoration:none; color:inherit;">
            <div style="display:flex; align-items:center; gap:10px;">
                <img src="https://www.google.com/favicon.ico" width="20" height="20">
                <span>Google로 계속하기</span>
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

def render_sidebar():
    with st.sidebar:
        st.title("Poten")
        st.markdown("---")
        st.markdown("[테스트1](https://www.naver.com/)")
        st.markdown("[테스트2](https://www.daum.net/)")

def display_chat_messages(messages):
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

def display_user_info(user_info):
    # 사이드바 하단이나 적절한 곳에 표시
    with st.sidebar:
        st.markdown("---")
        st.write(f"**{user_info['name']}**님")
        st.caption(user_info['email'])
