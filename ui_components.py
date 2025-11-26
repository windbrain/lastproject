import streamlit as st

def render_login_button():
    st.markdown(
        """
        <div style='text-align: right'>
            <a href="?login=true">
                <button style='font-size:16px;padding:6px 12px'>회원가입 / 로그인</button>
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_sidebar():
    with st.sidebar:
        st.markdown("[테스트1](https://www.naver.com/)")
        st.markdown("[테스트2](https://www.daum.net/)")

def display_chat_messages(messages):
    for msg in messages:
        st.chat_message(msg["role"]).write(msg["content"])

def display_user_info(user_info):
    st.success(f"{user_info['name']}님 환영합니다!")
    st.write(f"이메일: {user_info['email']}")
