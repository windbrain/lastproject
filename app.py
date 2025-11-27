# 이 파일은 메인 애플리케이션 파일입니다. Streamlit 앱의 진입점이며, UI, 인증, 채팅, DB 로직을 조율합니다.
import streamlit as st
import base64
from openai import OpenAI
from dotenv import load_dotenv
import os
from mongo_utils import get_mongo_collections
import auth_service
import db_service
import chat_service
import ui_components
import pandas as pd
from pypdf import PdfReader
import io

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

# 이미지 및 파일 업로드 (채팅 입력창 위)
# CSS로 위치를 고정하기 위해 별도의 컨테이너로 묶음 (실제로는 columns가 컨테이너 역할)
col1, col2 = st.columns(2)
with col1:
    with st.popover("📁 이미지", use_container_width=True):
        uploaded_file = st.file_uploader("이미지를 드래그하거나 선택하세요", type=["png", "jpg", "jpeg"], key="chat_image_uploader")
with col2:
    with st.popover("📄 파일", use_container_width=True):
        uploaded_doc = st.file_uploader("파일을 선택하세요", type=["pdf", "csv", "xlsx"], key="chat_file_uploader")

# 사용자 입력 처리
if prompt := st.chat_input("무엇이든 물어보세요"):
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    client = OpenAI(api_key=openai_api_key)

    # 메시지 내용 구성
    message_content = []
    
    # 텍스트 추가
    message_content.append({"type": "text", "text": prompt})
    
    # 이미지 처리
    if uploaded_file:
        # 이미지를 base64로 인코딩
        image_bytes = uploaded_file.getvalue()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # 이미지 추가
        message_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        })
        
        # UI에 이미지 표시 (사용자 메시지)
        with st.chat_message("user"):
            st.image(uploaded_file)

    # 파일 처리
    if uploaded_doc:
        file_text = ""
        try:
            if uploaded_doc.type == "application/pdf":
                reader = PdfReader(uploaded_doc)
                for page in reader.pages:
                    file_text += page.extract_text() + "\n"
            elif uploaded_doc.type == "text/csv":
                try:
                    df = pd.read_csv(uploaded_doc)
                except UnicodeDecodeError:
                    # UTF-8 실패 시 CP949(한글)로 재시도
                    uploaded_doc.seek(0)
                    df = pd.read_csv(uploaded_doc, encoding='cp949')
                file_text = df.to_markdown(index=False)
            elif "excel" in uploaded_doc.type or uploaded_doc.name.endswith(".xlsx"):
                df = pd.read_excel(uploaded_doc)
                file_text = df.to_markdown(index=False)
            
            if file_text:
                # 텍스트 내용에 파일 내용 추가
                message_content[0]["text"] += f"\n\n[첨부 파일 내용 ({uploaded_doc.name})]:\n{file_text}"
                
                # UI에 파일 첨부 표시
                with st.chat_message("user"):
                    st.caption(f"📎 파일 첨부: {uploaded_doc.name}")
        except Exception as e:
            st.error(f"파일 처리 중 오류 발생: {e}")

    # 세션 상태에 메시지 추가 (OpenAI API 형식에 맞게)
    # 텍스트만 있는 경우와 이미지 포함된 경우 구분 없이 리스트 형태로 저장해도 됨
    # 하지만 기존 텍스트만 있는 경우와의 호환성을 위해 텍스트만 있으면 문자열로 저장할 수도 있으나,
    # 일관성을 위해 리스트로 저장하거나, ui_components에서 처리했으므로 리스트로 저장.
    
    # 다만, 기존 로직이 문자열을 기대하는 부분이 있을 수 있으므로 확인 필요.
    # ui_components.display_chat_messages는 리스트/문자열 모두 처리하도록 수정함.
    # chat_service.get_ai_response는 messages 리스트를 그대로 전달하므로 문제 없음.
    
    # 사용자 메시지 UI 표시 (텍스트) - 이미지는 위에서 표시함
    with st.chat_message("user"):
        st.write(prompt)

    # 세션에 저장할 메시지 객체
    # 주의: OpenAI API는 content가 string 또는 list of content parts일 수 있음.
    # 복잡성을 줄이기 위해 이미지가 없으면 그냥 string으로, 있으면 list로 저장.
    if uploaded_file:
        user_msg_obj = {"role": "user", "content": message_content}
    else:
        # 이미지가 없더라도 파일이 첨부되었을 수 있으므로 message_content의 텍스트를 사용
        user_msg_obj = {"role": "user", "content": message_content[0]["text"]}

    st.session_state["messages"].append(user_msg_obj)

    # MongoDB 저장
    user = st.session_state.get("user_info", {"email": "anonymous", "name": "익명"})
    try:
        # MongoDB에는 구조화된 데이터를 저장해야 나중에 복원 시 문제 없음
        # db_service.log_chat_message는 content를 그대로 저장한다고 가정
        db_service.log_chat_message(chat_collection, "user", user_msg_obj["content"], user)
    except Exception as e:
        st.error(f"메시지 저장 실패: {str(e)}")

    # AI 응답
    try:
        msg = chat_service.get_ai_response(client, st.session_state["messages"])
    except Exception as e:
        st.error(f"AI 응답 생성 실패: {str(e)}")
        st.stop()
    
    st.session_state["messages"].append({"role": "assistant", "content": msg})
    with st.chat_message("assistant"):
        st.write(msg)

    try:
        db_service.log_chat_message(chat_collection, "assistant", msg, user)
    except Exception as e:
        st.error(f"AI 응답 저장 실패: {str(e)}")
