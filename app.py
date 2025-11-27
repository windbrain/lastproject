# 이 파일은 메인 애플리케이션 파일입니다. Streamlit 앱의 진입점이며, UI, 인증, 채팅, DB 로직을 조율합니다.
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
from mongo_utils import get_mongo_collections
import auth_service
import db_service
import chat_service
import ui_components

# 환경 변수 로드
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
google_client_id = os.getenv("GOOGLE_CLIENT_ID")
google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
redirect_uri = "http://localhost:8501"  # 배포 시 Streamlit Cloud 주소로 변경

# 로컬 개발 시 HTTPS가 아닌 HTTP에서도 동작하도록 설정 (배포 시 제거)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# MongoDB 연결
login_collection, chat_collection = get_mongo_collections()

# 구글 OAuth 설정
auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
token_url = "https://oauth2.googleapis.com/token"
userinfo_url = "https://openidconnect.googleapis.com/v1/userinfo"
scope = "openid email profile"

# 커스텀 CSS 적용
ui_components.render_custom_css()

# 사이드바
ui_components.render_sidebar()

# 로그인 상태 확인
if "user_info" in st.session_state:
    ui_components.display_user_info(st.session_state["user_info"])
    # 로그아웃 버튼
    if ui_components.render_logout_button():
        st.session_state.clear()
        st.rerun()
else:
    # 로그인 버튼 렌더링 및 모달 트리거
    if ui_components.render_login_button():
        # OAuth 세션 생성 및 URL 생성
        oauth = auth_service.create_oauth_session(
            client_id=google_client_id,
            client_secret=google_client_secret,
            redirect_uri=redirect_uri,
            scope=scope
        )
        authorization_url, state = auth_service.get_authorization_url(oauth, auth_url)
        st.session_state["oauth_state"] = state
        
        # 모달 띄우기
        ui_components.login_modal(authorization_url)

# 로그인 성공 후 토큰 교환 (리다이렉트 처리)
if "code" in st.query_params and "user_info" not in st.session_state:
    oauth = auth_service.create_oauth_session(
        client_id=google_client_id,
        client_secret=google_client_secret,
        redirect_uri=redirect_uri
    )
    try:
        token = auth_service.fetch_token(
            oauth_session=oauth,
            token_url=token_url,
            code=st.query_params["code"],
            client_id=google_client_id,
            client_secret=google_client_secret
        )
        userinfo = auth_service.get_user_info(oauth, userinfo_url)
        st.session_state["user_info"] = userinfo
        db_service.log_user_login(login_collection, userinfo)
        
        # 이전 채팅 기록 불러오기
        history = db_service.get_chat_history(chat_collection, userinfo["email"])
        if history:
            st.session_state["messages"] = history
        else:
            # 기록이 없으면 초기 메시지
            st.session_state["messages"] = [{
                "role": "assistant",
                "content": "무엇을 도와드릴까요?"
            }]
            
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"로그인 과정에서 오류가 발생했습니다: {str(e)}")
        st.query_params.clear()

# 챗봇 초기 메시지
if "messages" not in st.session_state:
    st.session_state["messages"] = [{
        "role": "assistant",
        "content": "무엇을 도와드릴까요?"
    }]

# 이전 메시지 출력
ui_components.display_chat_messages(st.session_state["messages"])

# 사용자 입력 처리
if prompt := st.chat_input("무엇이든 물어보세요"):
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    client = OpenAI(api_key=openai_api_key)

    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # MongoDB 저장
    user = st.session_state.get("user_info", {"email": "anonymous", "name": "익명"})
    db_service.log_chat_message(chat_collection, "user", prompt, user)

    # AI 응답
    msg = chat_service.get_ai_response(client, st.session_state["messages"])
    
    st.session_state["messages"].append({"role": "assistant", "content": msg})
    with st.chat_message("assistant"):
        st.write(msg)

    db_service.log_chat_message(chat_collection, "assistant", msg, user)
