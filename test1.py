import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

with st.sidebar:
    openai_api_key = os.getenv('OPENAI_API_KEY') 

    # 스트림릿의 마크다운 문법
    "[테스트1](https://www.naver.com/)"
    "[테스트2](https://www.daum.net/)"

st.title("💬 Vistor")

# (1) st.session_state에 "messages"가 없으면 초기값을 설정
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "어떤 창업 아이템의 잠재 고객과 전망이 궁금하신가요?"}]

# (2) 대화 기록을 출력
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    client = OpenAI(api_key=openai_api_key)

    #사용자 메시지를 대화 기록에 추가 
    st.session_state.messages.append({"role": "user", "content": prompt}) 

    #질문 출력
    st.chat_message("user").write(prompt) 
    response = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages) 
    msg = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": msg}) 
    #응답 출력
    st.chat_message("assistant").write(msg)