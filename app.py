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
import uuid

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
google_client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
redirect_uri = os.getenv("REDIRECT_URI", "").strip()

if not google_client_id or not google_client_secret:
    st.error("🚨 오류: Google Client ID 또는 Secret이 설정되지 않았습니다. Streamlit Cloud의 Secrets 설정을 확인해주세요.")
    st.stop()
if google_client_id == "your_client_id_here":
    st.error("🚨 오류: Google Client ID가 기본값입니다. 올바른 값으로 설정해주세요.")
    st.stop()

if platform.system() == "Windows":
    redirect_uri = "http://localhost:8501"
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
else:
    pass

login_collection, chat_collection = get_mongo_collections()

auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
token_url = "https://oauth2.googleapis.com/token"
userinfo_url = "https://openidconnect.googleapis.com/v1/userinfo"
scope = "openid email profile"

ui_components.render_custom_css()

def on_new_chat():
    st.session_state["messages"] = [{
        "role": "assistant",
        "content": "안녕하세요! 예비 창업자님. 💡 **창업 아이템**을 알려주시면 **잠재 고객**, **시장 전망**, **SWOT**, **성공 전략**을 상세히 분석해 드릴게요!"
    }]
    st.session_state["session_id"] = None

def on_session_select(session_id):
    st.session_state["session_id"] = session_id
    messages = db_service.get_session_messages(chat_collection, session_id)
    if messages:
        st.session_state["messages"] = messages
    else:
        st.session_state["messages"] = [{
            "role": "assistant",
            "content": "안녕하세요! 예비 창업자님. 💡 **창업 아이템**을 알려주시면 **잠재 고객**, **시장 전망**, **SWOT**, **성공 전략**을 상세히 분석해 드릴게요!"
        }]

def on_delete_session(session_id):
    db_service.delete_chat_session(chat_collection, session_id)
    if st.session_state.get("session_id") == session_id:
        on_new_chat()
    st.rerun()

if "session_id" not in st.session_state:
    st.session_state["session_id"] = None

if "user_info" in st.session_state:
    current_user_id = st.session_state["user_info"]["email"]
    current_user_name = st.session_state["user_info"]["name"]
    is_guest = False
else:
    if "guest_id" not in st.session_state:
        if "guest_id" in st.query_params:
            st.session_state["guest_id"] = st.query_params["guest_id"]
        else:
            st.session_state["guest_id"] = str(uuid.uuid4())[:8]
            st.query_params["guest_id"] = st.session_state["guest_id"]
    
    current_user_id = st.session_state["guest_id"]
    current_user_name = "게스트"
    is_guest = True

sessions = db_service.get_user_sessions(chat_collection, current_user_id)

ui_components.render_sidebar(sessions, on_session_select, on_new_chat, on_delete_session)

ui_components.render_header()

if "user_info" not in st.session_state:
    if "token" in st.query_params:
        token = st.query_params["token"]
        user_info = db_service.validate_login_token(login_collection, token)
        if user_info:
            st.session_state["user_info"] = user_info

if "user_info" in st.session_state:
    ui_components.display_user_info(st.session_state["user_info"])
    if ui_components.render_logout_button():
        if "token" in st.query_params:
            db_service.delete_login_token(login_collection, st.query_params["token"])
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()
else:
    if ui_components.render_login_button():
        oauth = auth_service.create_oauth_session(
            client_id=google_client_id,
            client_secret=google_client_secret,
            redirect_uri=redirect_uri,
            scope=scope
        )
        authorization_url, state = auth_service.get_authorization_url(oauth, auth_url)
        st.session_state["oauth_state"] = state
        
        ui_components.login_modal(authorization_url)

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
        
        login_token = db_service.create_login_token(login_collection, userinfo)
        st.query_params["token"] = login_token
        
        if "code" in st.query_params:
            del st.query_params["code"]
        if "state" in st.query_params:
            del st.query_params["state"]
        
        on_new_chat()
            
        st.rerun()
    except Exception as e:
        st.error(f"로그인 과정에서 오류가 발생했습니다: {str(e)}")
        
        with st.expander("디버깅 정보 (403 오류 시 확인)"):
            st.write(f"**Redirect URI:** `{redirect_uri}`")
            if google_client_id:
                masked_id = google_client_id[:5] + "..." + google_client_id[-5:]
                st.write(f"**Client ID:** `{masked_id}`")
            st.info("Google Cloud Console의 '승인된 리디렉션 URI' 설정과 위 URI가 정확히 일치해야 합니다.")

        if st.button("로그인 다시 시도"):
            st.query_params.clear()
            st.rerun()

if "messages" not in st.session_state:
    st.session_state["messages"] = [{
        "role": "assistant",
        "content": "안녕하세요! 예비 창업자님. 💡 **창업 아이템**을 알려주시면 **잠재 고객**, **시장 전망**, **SWOT**, **성공 전략**을 상세히 분석해 드릴게요!"
    }]

tab_chat, tab_bmc = st.tabs(["💬 채팅 분석", "📋 원클릭 비즈니스 캔버스"])

with tab_chat:
    ui_components.display_chat_messages(st.session_state["messages"])
    
    col1, col2 = st.columns(2)
    with col1:
        with st.popover("📁 이미지", use_container_width=True):
            uploaded_file = st.file_uploader("이미지를 드래그하거나 선택하세요", type=["png", "jpg", "jpeg"], key="chat_image_uploader")
    with col2:
        with st.popover("📄 파일", use_container_width=True):
            uploaded_doc = st.file_uploader("파일을 선택하세요", type=["pdf", "csv", "xlsx"], key="chat_file_uploader")

    if prompt := st.chat_input("무엇이든 물어보세요"):
        if not openai_api_key:
            st.info("Please add your OpenAI API key to continue.")
            st.stop()

        client = OpenAI(api_key=openai_api_key)

        message_content = []
        
        message_content.append({"type": "text", "text": prompt})
        
        if uploaded_file:
            image_bytes = uploaded_file.getvalue()
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            message_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            })
            
            with st.chat_message("user"):
                st.image(uploaded_file)

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
                    message_content[0]["text"] += f"\n\n[첨부 파일 내용 ({uploaded_doc.name})]:\n{file_text}"
                    
                    with st.chat_message("user"):
                        st.caption(f"📎 파일 첨부: {uploaded_doc.name}")
                        if "⚠️" in file_text:
                            st.caption("※ 토큰 제한으로 인해 데이터 일부만 전송되었습니다.")
            except Exception as e:
                st.error(f"파일 처리 중 오류 발생: {e}")

        with st.chat_message("user"):
            st.write(prompt)

        if uploaded_file:
            user_msg_obj = {"role": "user", "content": message_content}
        else:
            user_msg_obj = {"role": "user", "content": message_content[0]["text"]}

        st.session_state["messages"].append(user_msg_obj)

        try:
            user_data = {
                "email": current_user_id,
                "name": current_user_name
            }
            
            if st.session_state["session_id"] is None:
                title = prompt[:30] + "..." if len(prompt) > 30 else prompt
                st.session_state["session_id"] = db_service.create_chat_session(chat_collection, current_user_id, title)

            db_service.log_chat_message(chat_collection, "user", user_msg_obj["content"], user_data, st.session_state["session_id"])
        except Exception as e:
            print(f"메시지 저장 실패: {str(e)}")

        try:
            with st.spinner("분석 중입니다... 잠시만 기다려주세요..."):
                persona = st.session_state.get("current_persona", "general")
                msg = chat_service.get_ai_response(client, st.session_state["messages"], persona=persona)
        except Exception as e:
            st.error(f"AI 응답 생성 실패: {str(e)}")
            st.stop()
        
        st.session_state["messages"].append({"role": "assistant", "content": msg})
        with st.chat_message("assistant"):
            st.write(msg)
            
            persona_labels = {
                "general": "🧥 일반 컨설턴트",
                "vc": "🦅 냉철한 VC",
                "marketer": "📣 마케팅 전문가"
            }
            current_persona = st.session_state.get("current_persona", "general")
            st.caption(f"Momentary Analysis by {persona_labels.get(current_persona, 'AI')}")

        try:
            db_service.log_chat_message(chat_collection, "assistant", msg, user_data, st.session_state["session_id"])
        except Exception as e:
            print(f"AI 응답 저장 실패: {str(e)}")

with tab_bmc:
    st.markdown("### 📋 비즈니스 모델 캔버스 (Business Model Canvas)")
    st.markdown("지금까지 나누었던 대화 내용을 바탕으로 **사업의 핵심 9가지 요소**를 정리해드립니다. 투자 유치나 사업 계획서 작성 시 활용하세요!")
    
    if st.button("🚀 원클릭 BMC 생성하기", key="generate_bmc_btn", type="primary", use_container_width=True):
        if not openai_api_key:
            st.info("Please add your OpenAI API key to continue.")
        elif not st.session_state["messages"] or len(st.session_state["messages"]) < 2:
            st.warning("⚠️ 먼저 채팅으로 아이템에 대해 충분히 이야기를 나누어 주세요.")
        else:
            client = OpenAI(api_key=openai_api_key)
            try:
                with st.spinner("대화 내용을 분석하여 비즈니스 캔버스를 그리고 있습니다..."):
                    bmc_json_str = chat_service.generate_bmc(client, st.session_state["messages"])
                    import json
                    bmc_data = json.loads(bmc_json_str)
                
                st.success("✅ 비즈니스 캔버스 생성이 완료되었습니다!")
                
                ui_components.render_bmc_visual(bmc_data)
                
                # 다운로드용 텍스트 변환
                markdown_content = f"""
# Business Model Canvas

| 구분 | 내용 |
|---|---|
| 🤝 핵심 파트너 | {bmc_data.get('key_partners')} |
| 🔑 핵심 활동 | {bmc_data.get('key_activities')} |
| 💎 핵심 자원 | {bmc_data.get('key_resources')} |
| 🎁 가치 제안 | {bmc_data.get('value_propositions')} |
| 🗣️ 고객 관계 | {bmc_data.get('customer_relationships')} |
| 🚚 채널 | {bmc_data.get('channels')} |
| 👥 고객 세그먼트 | {bmc_data.get('customer_segments')} |
| 💰 비용 구조 | {bmc_data.get('cost_structure')} |
| 💵 수익원 | {bmc_data.get('revenue_streams')} |
"""
                
                st.download_button(
                    label="📥 캔버스 내용 다운로드 (Markdown)",
                    data=markdown_content,
                    file_name=f"BMC_Analysis_{st.session_state.get('guest_id', 'user')}.md",
                    mime="text/markdown"
                )
                
            except Exception as e:
                st.error(f"BMC 생성 중 오류 발생: {str(e)}")
