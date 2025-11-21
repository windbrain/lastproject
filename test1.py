import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
from authlib.integrations.requests_client import OAuth2Session
from mongo_utils import get_mongo_collection
from datetime import datetime

# 환경 변수 로드
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
google_client_id = os.getenv("GOOGLE_CLIENT_ID")
google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
redirect_uri = "http://localhost:8501"  # 배포 시 Streamlit Cloud 주소로 변경

# 로컬 개발 시 HTTPS가 아닌 HTTP에서도 동작하도록 설정 (배포 시 제거)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# MongoDB 연결
collection = get_mongo_collection()

# 구글 OAuth 설정
auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
token_url = "https://oauth2.googleapis.com/token"
userinfo_url = "https://openidconnect.googleapis.com/v1/userinfo"
scope = "openid email profile"

# 화면 상단 로그인 버튼
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

# 로그인 요청 처리
if st.query_params.get("login") == "true" and "user_info" not in st.session_state:
    oauth = OAuth2Session(
        client_id=google_client_id,
        client_secret=google_client_secret,
        redirect_uri=redirect_uri,
        scope=scope
    )
    authorization_url, state = oauth.create_authorization_url(auth_url)
    st.session_state["oauth_state"] = state
    st.markdown(f"[🔒 구글 로그인하기]({authorization_url})")
    st.stop()

# 로그인 성공 후 토큰 교환
if "code" in st.query_params and "user_info" not in st.session_state:
    oauth = OAuth2Session(
        client_id=google_client_id,
        client_secret=google_client_secret,
        redirect_uri=redirect_uri
    )
    try:
        token = oauth.fetch_token(
            token_url=token_url,
            code=st.query_params["code"],
            client_id=google_client_id,
            client_secret=google_client_secret
        )
    except Exception as e:
        st.error("로그인 과정에서 오류가 발생했습니다. 다시 시도해주세요.")
        st.query_params.clear()
        st.stop()

    userinfo = oauth.get(userinfo_url).json()
    st.session_state["user_info"] = userinfo

    collection.insert_one({
        "email": userinfo["email"],
        "name": userinfo["name"],
        "provider": "google",
        "login_time": datetime.now()
    })

    st.query_params.clear()
    st.rerun()

# 로그인된 사용자 정보 표시 (선택)
if "user_info" in st.session_state:
    userinfo = st.session_state["user_info"]
    st.success(f"{userinfo['name']}님 환영합니다!")
    st.write(f"이메일: {userinfo['email']}")

# 사이드바 링크
with st.sidebar:
    "[테스트1](https://www.naver.com/)"
    "[테스트2](https://www.daum.net/)"

# 챗봇 초기 메시지
if "messages" not in st.session_state:
    st.session_state["messages"] = [{
        "role": "assistant",
        "content": "어떤 창업 아이템의 잠재 고객과 전망이 궁금하신가요?"
    }]

# 이전 메시지 출력
for msg in st.session_state["messages"]:
    st.chat_message(msg["role"]).write(msg["content"])

# 사용자 입력 처리
if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    client = OpenAI(api_key=openai_api_key)

    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # MongoDB 저장: 로그인 여부에 따라 사용자 정보 포함
    user = st.session_state.get("user_info", {"email": "anonymous", "name": "익명"})
    collection.insert_one({
        "role": "user",
        "content": prompt,
        "email": user["email"],
        "name": user["name"],
        "timestamp": datetime.now()
    })

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=st.session_state["messages"]
    )
    msg = response.choices[0].message.content
    st.session_state["messages"].append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)

    collection.insert_one({
        "role": "assistant",
        "content": msg,
        "email": user["email"],
        "name": user["name"],
        "timestamp": datetime.now()
    })
