import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
import pandas as pd

# 환경변수 로드
load_dotenv()

# 사이드바: API 키 입력 안내 및 링크
with st.sidebar:
    openai_api_key = os.getenv('OPENAI_API_KEY')
    "[네이버](https://www.naver.com/)"
    "[다음](https://www.daum.net/)"

# 타이틀
st.title("💬 Vistor")

# CSV 파일 로드 함수
@st.cache_data
def load_population_data():
    pop = pd.read_csv("./csv/population_202510.csv", encoding="cp949")
    gender = pd.read_csv("./csv/gender_population_202510.csv", encoding="cp949")
    men = pd.read_csv("./csv/men_population_202510.csv", encoding="cp949")
    women = pd.read_csv("./csv/women_population_202510.csv", encoding="cp949")
    for df in [pop, gender, men, women]:
        df.columns = df.columns.str.strip()
    return pop, gender, men, women

# 데이터프레임 로딩
population_df, gender_df, men_df, women_df = load_population_data()

# 성별 매핑
gender_map = {
    "여성": women_df,
    "여자": women_df,
    "남성": men_df,
    "남자": men_df,
    "전체": gender_df
}

# 대화 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "어떤 창업 아이템의 잠재 고객과 전망이 궁금하신가요?"}]

# 대화 출력
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 사용자 입력 처리
if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    # 사용자 메시지 저장 및 출력
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # 기본 인구수 질문 처리
    korea_row = population_df[population_df["area"].str.contains("한국")]

    if "대한민국 인구수" in prompt:
        if not korea_row.empty:
            total_pop = korea_row.iloc[0]["total"]
            msg = f"2025년 10월 기준 대한민국의 총인구는 약 {total_pop}명입니다."
        else:
            msg = "죄송합니다. 대한민국 인구 데이터를 찾을 수 없습니다."

    elif "대한민국 남자 인구수" in prompt:
        if not korea_row.empty:
            men_pop = korea_row.iloc[0]["men"]
            msg = f"2025년 10월 기준 대한민국의 남자 인구는 약 {men_pop}명입니다."
        else:
            msg = "죄송합니다. 대한민국 남자 인구 데이터를 찾을 수 없습니다."

    elif "대한민국 여자 인구수" in prompt:
        if not korea_row.empty:
            women_pop = korea_row.iloc[0]["women"]
            msg = f"2025년 10월 기준 대한민국의 여자 인구는 약 {women_pop}명입니다."
        else:
            msg = "죄송합니다. 대한민국 여자 인구 데이터를 찾을 수 없습니다."

    else:
        # 연령대 키워드 추출 (열 이름 그대로 사용)
        age_key = None
        for keyword in gender_df.columns:
            if keyword in prompt and any(x in keyword for x in ["10대", "20대", "30대", "40대", "50대", "60대", "70대", "80대", "90대", "100세 이상"]):
                age_key = keyword
                break

        # 성별 추출
        gender_label = None
        for gender_key in gender_map:
            if gender_key in prompt:
                gender_label = gender_key
                break

        # 지역 추출
        region_label = None
        for region in population_df["area"]:
            if region in prompt:
                region_label = region
                break

        # 지역 + 성별 + 연령대
        if age_key and gender_label and region_label:
            df = gender_map[gender_label]
            region_row = df[df["area"].str.contains(region_label)]

            if not region_row.empty and age_key in df.columns:
                value = region_row.iloc[0][age_key]
                value = int(str(value).replace(",", "").strip())
                msg = f"2025년 10월 기준 {region_label}의 {gender_label} {age_key} 인구는 약 {value:,}명입니다."
            else:
                msg = f"{region_label}의 {age_key} 인구 데이터를 찾을 수 없습니다."

        # 대한민국 + 성별 + 연령대
        elif age_key and gender_label:
            df = gender_map[gender_label]
            korea_row = df[df["area"].str.contains("한국")]

            if not korea_row.empty and age_key in df.columns:
                value = korea_row.iloc[0][age_key]
                value = int(str(value).replace(",", "").strip())
                msg = f"2025년 10월 기준 대한민국의 {gender_label} {age_key} 인구는 약 {value:,}명입니다."
            else:
                msg = f"대한민국의 {age_key} 인구 데이터를 찾을 수 없습니다."

        # 기타 질문 → OpenAI 응답
        else:
            client = OpenAI(api_key=openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=st.session_state.messages
            )
            msg = response.choices[0].message.content

    # 응답 저장 및 출력
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)