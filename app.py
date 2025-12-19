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

tab_chat, tab_bmc, tab_panel = st.tabs(["💬 채팅 분석", "📋 원클릭 BMC & 진단", "👥 가상 자문단 회의"])

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

# BMC 및 진단 탭 내용
with tab_bmc:
    st.markdown("### 📊 스타트업 진단 및 모델링")
    st.markdown("AI가 당신의 사업 아이템을 **5가지 핵심 지표**로 분석하고, **비즈니스 모델 캔버스**를 그려줍니다.")

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 1. 🩺 아이템 건강검진 (Radar Chart)")
        if st.button("📈 진단 차트 생성하기", key="generate_chart_btn", use_container_width=True):
             if not st.session_state["messages"] or len(st.session_state["messages"]) < 2:
                st.warning("⚠️ 먼저 채팅으로 아이템에 대해 충분히 이야기를 나누어 주세요.")
             else:
                client = OpenAI(api_key=openai_api_key)
                try:
                    with st.spinner("5가지 핵심 지표를 분석 중입니다..."):
                        ratings_json = chat_service.analyze_ratings(client, st.session_state["messages"])
                        # JSON 전처리
                        if ratings_json.startswith("```json"):
                            ratings_json = ratings_json.replace("```json", "").replace("```", "")
                        elif ratings_json.startswith("```"):
                            ratings_json = ratings_json.replace("```", "")
                        
                        import json
                        scores = json.loads(ratings_json)
                    
                    st.success("진단 완료!")
                    # 차트 렌더링
                    ui_components.render_radar_chart(scores)
                    
                    # 총평 출력
                    st.info(f"**총평**: {scores.get('comment', '')}")
                    
                except Exception as e:
                    st.error(f"진단 중 오류 발생: {str(e)}")

    with col2:
        st.markdown("#### 2. 📋 비즈니스 모델 캔버스 (BMC)")
        if st.button("🚀 BMC 생성하기", key="generate_bmc_btn", type="primary", use_container_width=True):
            if not openai_api_key:
                st.info("Please add your OpenAI API key to continue.")
            elif not st.session_state["messages"] or len(st.session_state["messages"]) < 2:
                st.warning("⚠️ 먼저 채팅으로 아이템에 대해 충분히 이야기를 나누어 주세요.")
            else:
                client = OpenAI(api_key=openai_api_key)
                try:
                    with st.spinner("비즈니스 캔버스를 그리는 중..."):
                        bmc_json_str = chat_service.generate_bmc(client, st.session_state["messages"])
                        
                        if bmc_json_str.startswith("```json"):
                            bmc_json_str = bmc_json_str.replace("```json", "").replace("```", "")
                        elif bmc_json_str.startswith("```"):
                            bmc_json_str = bmc_json_str.replace("```", "")
                        
                        import json
                        try:
                            bmc_data = json.loads(bmc_json_str)
                        except json.JSONDecodeError:
                            st.error("데이터 파싱 실패. 다시 시도해주세요.")
                            st.stop()
                    
                    st.success("생성 완료!")
                    st.session_state["bmc_data"] = bmc_data # 임시 저장 (화면 리프레시 대응용)
                    
                except Exception as e:
                    st.error(f"오류 발생: {str(e)}")

    # BMC 결과가 있으면 하단에 표시 (버튼 클릭 후에도 유지되도록 세션 활용하면 좋지만 일단 직접 렌더링)
    # 위 코드에서 bmc_data는 지역변수라 사라짐. 세션에 저장하는게 좋음.
    # 간단히 구현하기 위해 바로 렌더링하도록 함. (다만 컬럼 밖으로 빼기 위해 로직 조정 필요)
    
    # 여기서는 간단히 버튼 누른 직후에만 표시 (Streamlit 특성상 리런되면 사라짐, 세션 저장 권장)
    # 일단 직관성을 위해 col2 안이 아닌 아래 넓은 영역에 표시
    
    if "bmc_data" in st.session_state:
        st.markdown("---")
        st.markdown("#### 🏗️ 비즈니스 모델 캔버스 결과")
        ui_components.render_bmc_visual(st.session_state["bmc_data"])
        
        # 다운로드 버튼 (Markdown)
        bmc_data = st.session_state["bmc_data"]
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
            label="📥 Markdown 다운로드",
            data=markdown_content,
            file_name=f"BMC_{st.session_state.get('guest_id', 'user')}.md",
            mime="text/markdown",
            use_container_width=True
        )

# 가상 자문단 탭 내용
with tab_panel:
    st.markdown("### 👥 가상 자문단 회의 (Virtual Advisory Board)")
    st.markdown("내 창업 아이템을 두고 **VC(투자자)**, **마케터**, **CTO(기술책임자)**가 벌이는 **끝장 토론**을 엿보세요.")
    
    if st.button("🔥 자문단 회의 소집하기", key="start_panel_btn", type="primary", use_container_width=True):
        if not st.session_state["messages"] or len(st.session_state["messages"]) < 2:
            st.warning("⚠️ 먼저 채팅으로 아이템에 대해 충분히 이야기를 나누어 주세요.")
        else:
            client = OpenAI(api_key=openai_api_key)
            try:
                with st.spinner("전문가들을 소집하고 있습니다... (약 10~20초 소요)"):
                    panel_json_str = chat_service.generate_panel_discussion(client, st.session_state["messages"])
                    
                    if panel_json_str.startswith("```json"):
                        panel_json_str = panel_json_str.replace("```json", "").replace("```", "")
                    elif panel_json_str.startswith("```"):
                        panel_json_str = panel_json_str.replace("```", "")
                    
                    import json
                    panel_data_obj = json.loads(panel_json_str)
                    # "discussion" 키 유무 확인 (프롬프트에 따라 최상위 리스트일수도, 객체일수도 있음. 프롬프트는 객체로 수정함)
                    discussion_list = panel_data_obj.get("discussion", [])
                
                st.success("회의가 시작됩니다!")
                st.markdown("---")
                
                # 렌더링
                ui_components.render_panel_discussion(discussion_list)
                
            except Exception as e:
                st.error(f"회의 생성 중 오류 발생: {str(e)}")
