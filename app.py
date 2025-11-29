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

import platform

# 환경 변수 로드
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
google_client_id = os.getenv("GOOGLE_CLIENT_ID")
google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
redirect_uri = os.getenv("REDIRECT_URI")

# 로컬 개발 환경(Windows)과 배포 환경(Linux/Streamlit Cloud) 구분
if platform.system() == "Windows":
    # 로컬 개발 시에는 .env 설정과 무관하게 localhost 강제
    redirect_uri = "http://localhost:8501"
    # 로컬에서는 HTTP 허용
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
else:
    # 배포 환경에서는 환경 변수(Secrets)의 REDIRECT_URI 사용
    # HTTPS 강제 (OAUTHLIB_INSECURE_TRANSPORT 설정 안 함)
    pass

# MongoDB 연결
login_collection, chat_collection = get_mongo_collections()

# 구글 OAuth 설정
auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
token_url = "https://oauth2.googleapis.com/token"
userinfo_url = "https://openidconnect.googleapis.com/v1/userinfo"
scope = "openid email profile"

# 커스텀 CSS 적용
ui_components.render_custom_css()

# 사이드바 및 세션 관리 로직
def on_new_chat():
    st.session_state["messages"] = [{
        "role": "assistant",
        "content": "안녕하세요! 예비 창업자님. 창업하고 싶은 아이템이 있으신가요? 아이템을 알려주시면 잠재 고객과 전망을 분석해 드릴게요."
    }]
    st.session_state["session_id"] = None

def on_session_select(session_id):
    st.session_state["session_id"] = session_id
    messages = db_service.get_session_messages(chat_collection, session_id)
    if messages:
        st.session_state["messages"] = messages
    else:
        # 메시지가 없는 세션일 경우 (예외 처리)
        st.session_state["messages"] = [{
            "role": "assistant",
            "content": "안녕하세요! 예비 창업자님. 창업하고 싶은 아이템이 있으신가요? 아이템을 알려주시면 잠재 고객과 전망을 분석해 드릴게요."
        }]

def on_delete_session(session_id):
    db_service.delete_chat_session(chat_collection, session_id)
    # 현재 보고 있는 세션을 삭제했다면 초기화
    if st.session_state.get("session_id") == session_id:
        on_new_chat()
    st.rerun()

# 세션 ID 초기화
if "session_id" not in st.session_state:
    st.session_state["session_id"] = None

# 사용자 세션 목록 가져오기 (로그인 상태일 때만)
sessions = []
if "user_info" in st.session_state:
    sessions = db_service.get_user_sessions(chat_collection, st.session_state["user_info"]["email"])

# 사이드바 렌더링
ui_components.render_sidebar(sessions, on_session_select, on_new_chat, on_delete_session)

# 헤더 렌더링 (메인 영역 상단)
ui_components.render_header()

# 로그인 상태 확인
if "user_info" not in st.session_state:
    # URL 토큰 확인
    if "token" in st.query_params:
        token = st.query_params["token"]
        user_info = db_service.validate_login_token(login_collection, token)
        if user_info:
            st.session_state["user_info"] = user_info
            # 토큰 유효하면 별도 리다이렉트 없이 진행 (URL에 토큰 유지)

if "user_info" in st.session_state:
    ui_components.display_user_info(st.session_state["user_info"])
    # 로그아웃 버튼
    if ui_components.render_logout_button():
        # 토큰 삭제
        if "token" in st.query_params:
            db_service.delete_login_token(login_collection, st.query_params["token"])
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()
else:
    # 로그인 버튼 렌더링 및 모달 트리거
    # 디버깅용: 배포 환경에서 리다이렉트 URI가 제대로 설정되었는지 확인
    # st.write(f"Debug: Redirect URI is {redirect_uri}") 
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
        
        # 로그인 토큰 생성 및 URL 설정
        login_token = db_service.create_login_token(login_collection, userinfo)
        st.query_params["token"] = login_token
        
        # 인증 코드 등 불필요한 파라미터 제거 (새로고침 시 재사용 방지)
        if "code" in st.query_params:
            del st.query_params["code"]
        if "state" in st.query_params:
            del st.query_params["state"]
        
        # 로그인 직후에는 새 채팅 화면으로 시작 (기존 기록은 사이드바에 있음)
        on_new_chat()
            
        st.rerun()
    except Exception as e:
        st.error(f"로그인 과정에서 오류가 발생했습니다: {str(e)}")
        
        # 디버깅 정보 표시 (403 에러 등 해결용)
        with st.expander("디버깅 정보 (403 오류 시 확인)"):
            st.write(f"**Redirect URI:** `{redirect_uri}`")
            if google_client_id:
                masked_id = google_client_id[:5] + "..." + google_client_id[-5:]
                st.write(f"**Client ID:** `{masked_id}`")
            st.info("Google Cloud Console의 '승인된 리디렉션 URI' 설정과 위 URI가 정확히 일치해야 합니다.")

        # 재시도 버튼 (쿼리 파라미터 초기화)
        if st.button("로그인 다시 시도"):
            st.query_params.clear()
            st.rerun()



# 챗봇 초기 메시지
if "messages" not in st.session_state:
    st.session_state["messages"] = [{
        "role": "assistant",
        "content": "안녕하세요! 예비 창업자님. 창업하고 싶은 아이템이 있으신가요? 아이템을 알려주시면 잠재 고객과 전망을 분석해 드릴게요."
    }]

# 이전 메시지 출력
ui_components.display_chat_messages(st.session_state["messages"])

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
                max_pages = 5
                for i, page in enumerate(reader.pages):
                    if i >= max_pages:
                        file_text += f"\n\n[...내용이 너무 길어 {max_pages}페이지만 표시합니다...]"
                        break
                    file_text += page.extract_text() + "\n"
            elif uploaded_doc.type == "text/csv":
                try:
                    df = pd.read_csv(uploaded_doc)
                except UnicodeDecodeError:
                    # UTF-8 실패 시 CP949(한글)로 재시도
                    uploaded_doc.seek(0)
                    df = pd.read_csv(uploaded_doc, encoding='cp949')
                
                if len(df) > 50:
                    file_text = f"⚠️ 데이터가 너무 많아 상위 50행만 분석에 사용합니다 (총 {len(df)}행).\n"
                    file_text += df.head(50).to_markdown(index=False)
                else:
                    file_text = df.to_markdown(index=False)
            elif "excel" in uploaded_doc.type or uploaded_doc.name.endswith(".xlsx"):
                df = pd.read_excel(uploaded_doc)
                if len(df) > 50:
                    file_text = f"⚠️ 데이터가 너무 많아 상위 50행만 분석에 사용합니다 (총 {len(df)}행).\n"
                    file_text += df.head(50).to_markdown(index=False)
                else:
                    file_text = df.to_markdown(index=False)
            
            if file_text:
                # 텍스트 내용에 파일 내용 추가
                message_content[0]["text"] += f"\n\n[첨부 파일 내용 ({uploaded_doc.name})]:\n{file_text}"
                
                # UI에 파일 첨부 표시
                with st.chat_message("user"):
                    st.caption(f"📎 파일 첨부: {uploaded_doc.name}")
                    if "⚠️" in file_text:
                        st.caption("※ 토큰 제한으로 인해 데이터 일부만 전송되었습니다.")
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
    
    # 세션 ID가 없으면 새로 생성 (첫 메시지인 경우)
    if st.session_state["session_id"] is None and "user_info" in st.session_state:
        # 제목 생성 (첫 메시지 내용으로)
        title = prompt[:30] + "..." if len(prompt) > 30 else prompt
        st.session_state["session_id"] = db_service.create_chat_session(chat_collection, user["email"], title)
        # 사이드바 갱신을 위해 rerun 필요할 수 있음 (하지만 메시지 처리 후 자연스럽게 갱신될 것)
        
    try:
        # MongoDB에는 구조화된 데이터를 저장해야 나중에 복원 시 문제 없음
        # db_service.log_chat_message는 content를 그대로 저장한다고 가정
        db_service.log_chat_message(chat_collection, "user", user_msg_obj["content"], user, st.session_state["session_id"])
    except Exception as e:
        # DB 저장 실패는 사용자에게 치명적이지 않으므로 경고만 표시하거나 로그로 남김
        print(f"메시지 저장 실패: {str(e)}")
        # st.warning("채팅 기록 저장에 실패했습니다. (네트워크 연결 확인 필요)")

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
        db_service.log_chat_message(chat_collection, "assistant", msg, user, st.session_state["session_id"])
    except Exception as e:
        print(f"AI 응답 저장 실패: {str(e)}")

