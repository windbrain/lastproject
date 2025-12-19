import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

def render_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Noto Sans KR', sans-serif;
        }

        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        .block-container {
            max-width: 800px;
            padding-top: 2rem;
            padding-bottom: 5rem;
        }

        .stChatMessage {
            background-color: transparent;
        }
        
        div[data-testid="stChatMessage"]:nth-child(odd) {
            background-color: transparent; 
        }

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

        div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPopover"]) {
            position: fixed;
            bottom: 105px;
            left: 50%;
            transform: translateX(-50%);
            width: auto !important;
            z-index: 9999;
            background-color: transparent;
            gap: 8px;
            justify-content: center;
            pointer-events: none;
        }

        div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPopover"]) * {
            pointer-events: auto;
        }

        div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPopover"]) div[data-testid="stColumn"] {
            width: auto !important;
            flex: 0 0 auto !important;
            min-width: auto !important;
        }
        
        [data-testid="stPopover"] > button {
            border: 1px solid #e5e7eb;
            background-color: white;
            color: #374151;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 2px 8px !important;
            font-size: 13px !important;
            min-height: unset !important;
            height: 32px !important;
            border-radius: 16px !important;
        }
        
        [data-testid="stPopover"] > button > div {
            gap: 4px !important;
        }
        </style>
    """, unsafe_allow_html=True)

@st.dialog("로그인")
def login_modal(auth_url):
    st.markdown("이전 대화기록을 계속 보고 싶다면 로그인을 해주세요")
    st.markdown("---")
    
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
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("로그인", key="login_trigger"):
            return True
    return False

def render_logout_button():
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("로그아웃", key="logout_trigger"):
            return True
    return False

def render_sidebar(sessions=None, on_session_select=None, on_new_chat=None, on_delete_session=None):
    with st.sidebar:
        if st.button("✨ 새 채팅", key="new_chat_btn", use_container_width=True):
            if on_new_chat:
                on_new_chat()
        
        st.markdown("---")

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
        st.session_state["current_persona"] = persona_map[selected_persona_name]
        
        st.markdown("---")
        
        if sessions:
            st.caption("최근 대화")
            for session in sessions:
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
    with st.sidebar:
        st.markdown("---")
        st.write(f"**{user_info['name']}**님")
        st.caption(user_info['email'])

def render_bmc_visual(bmc_data):
    st.markdown("""
    <style>
    .bmc-container {
        display: grid;
        grid-template-columns: 20% 20% 20% 20% 20%;
        grid-template-rows: auto auto auto;
        gap: 10px;
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 12px;
        color: #333;
    }
    .bmc-box {
        background: white;
        padding: 15px;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        font-size: 0.9rem;
    }
    .bmc-title {
        font-weight: bold;
        font-size: 1.1em;
        margin-bottom: 10px;
        color: #1a73e8;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    .bmc-content {
        white-space: pre-wrap;
        line-height: 1.5;
        color: #555;
    }
    
    /* Grid Positions */
    .kp { grid-column: 1; grid-row: 1 / span 2; }
    .ka { grid-column: 2; grid-row: 1; }
    .kr { grid-column: 2; grid-row: 2; }
    .vp { grid-column: 3; grid-row: 1 / span 2; background-color: #e8f0fe; border-color: #1a73e8; }
    .cr { grid-column: 4; grid-row: 1; }
    .ch { grid-column: 4; grid-row: 2; }
    .cs { grid-column: 5; grid-row: 1 / span 2; }
    .cost { grid-column: 1 / span 3; grid-row: 3; }
    .rev { grid-column: 4 / span 2; grid-row: 3; }
    
    @media (max-width: 768px) {
        .bmc-container {
            display: flex;
            flex-direction: column;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    html = f"""
    <div class="bmc-container">
        <div class="bmc-box kp">
            <div class="bmc-title">🤝 핵심 파트너</div>
            <div class="bmc-content">{bmc_data.get('key_partners', '')}</div>
        </div>
        <div class="bmc-box ka">
            <div class="bmc-title">🔑 핵심 활동</div>
            <div class="bmc-content">{bmc_data.get('key_activities', '')}</div>
        </div>
        <div class="bmc-box kr">
            <div class="bmc-title">💎 핵심 자원</div>
            <div class="bmc-content">{bmc_data.get('key_resources', '')}</div>
        </div>
        <div class="bmc-box vp">
            <div class="bmc-title">🎁 가치 제안</div>
            <div class="bmc-content">{bmc_data.get('value_propositions', '')}</div>
        </div>
        <div class="bmc-box cr">
            <div class="bmc-title">🗣️ 고객 관계</div>
            <div class="bmc-content">{bmc_data.get('customer_relationships', '')}</div>
        </div>
        <div class="bmc-box ch">
            <div class="bmc-title">🚚 채널</div>
            <div class="bmc-content">{bmc_data.get('channels', '')}</div>
        </div>
        <div class="bmc-box cs">
            <div class="bmc-title">👥 고객 세그먼트</div>
            <div class="bmc-content">{bmc_data.get('customer_segments', '')}</div>
        </div>
        <div class="bmc-box cost">
            <div class="bmc-title">💰 비용 구조</div>
            <div class="bmc-content">{bmc_data.get('cost_structure', '')}</div>
        </div>
        <div class="bmc-box rev">
            <div class="bmc-title">💵 수익원</div>
            <div class="bmc-content">{bmc_data.get('revenue_streams', '')}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_radar_chart(scores):
    # 한글 폰트 설정 (Windows/Linux/Mac 대응 필요, 일단 기본 폰트 사용하거나 영문으로)
    # Streamlit Cloud 등에서는 한글 폰트가 없을 수 있음.
    # 안전하게 영문 라벨 사용하거나, 사용자가 설치한 폰트를 찾도록 해야 함.
    # 여기서는 간단히 구현.
    
    labels = ['Marketability', 'Profitability', 'Innovation', 'Feasibility', 'Growth']
    # 점수 순서 맞추기
    values = [
        scores.get('marketability', 0),
        scores.get('profitability', 0),
        scores.get('innovation', 0),
        scores.get('feasibility', 0),
        scores.get('growth_potential', 0)
    ]
    
    # 레이더 차트 그리기
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    
    # 닫힌 도형을 위해 첫 번째 값을 마지막에 추가
    values += values[:1]
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    
    ax.fill(angles, values, color='#10a37f', alpha=0.25)
    ax.plot(angles, values, color='#10a37f', linewidth=2)
    
    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=12, fontweight='bold')
    
    # 0~100 범위 고정
    ax.set_ylim(0, 100)
    
    # 차트 배경 투명
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    
    st.pyplot(fig)

def render_panel_discussion(discussion_data):
    st.markdown("""
    <style>
    .panel-box {
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 10px;
        max-width: 85%;
        position: relative;
    }
    .panel-vc {
        background-color: #fce4ec; /* Red-ish for critic */
        border-left: 5px solid #d81b60;
        margin-right: auto;
    }
    .panel-marketer {
        background-color: #fff3e0; /* Orange for energy */
        border-left: 5px solid #fb8c00;
        margin-left: auto;
    }
    .panel-cto {
        background-color: #e3f2fd; /* Blue for tech */
        border-left: 5px solid #1e88e5;
        margin-right: auto;
    }
    .panel-mod {
        background-color: #f3e5f5; /* Purple for neutral */
        border: 2px dashed #8e24aa;
        margin: 0 auto;
        width: 100%;
        text-align: center;
    }
    .speaker-name {
        font-weight: bold;
        font-size: 0.9em;
        margin-bottom: 5px;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

    avatars = {
        "VC": "🦅",
        "Marketer": "📣",
        "CTO": "💻",
        "Moderator": "🎙️"
    }
    
    styles = {
        "VC": "panel-vc",
        "Marketer": "panel-marketer",
        "CTO": "panel-cto",
        "Moderator": "panel-mod"
    }

    for item in discussion_data:
        speaker = item.get("speaker", "Moderator")
        message = item.get("message", "")
        
        # Mapping variations
        style_key = "Moderator"
        if "VC" in speaker or "Capital" in speaker: style_key = "VC"
        elif "Market" in speaker or "마케터" in speaker: style_key = "Marketer"
        elif "CTO" in speaker or "기술" in speaker or "Tech" in speaker: style_key = "CTO"
        
        emoji = avatars.get(style_key, "👤")
        css_class = styles.get(style_key, "panel-mod")
        
        st.markdown(f"""
        <div class="panel-box {css_class}">
            <div class="speaker-name">{emoji} {speaker}</div>
            <div>{message}</div>
        </div>
        """, unsafe_allow_html=True)
