import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os

# MongoDB 모듈 불러오기
from mongo_utils import get_mongo_collection, save_message_to_mongo

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')

#  MongoDB 컬렉션 연결
collection = get_mongo_collection()

with st.sidebar:
    "[테스트1](https://www.naver.com/)"
    "[테스트2](https://www.daum.net/)"

st.title("💬 Vistor")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "어떤 창업 아이템의 잠재 고객과 전망이 궁금하신가요?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    client = OpenAI(api_key=openai_api_key)

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    save_message_to_mongo(collection, "user", prompt)  #  MongoDB 저장

    response = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages)
    msg = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
    save_message_to_mongo(collection, "assistant", msg)  #  MongoDB 저장
