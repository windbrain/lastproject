# 이 파일은 OpenAI API를 사용하여 챗봇 응답을 생성하는 모듈입니다.
def get_ai_response(client, messages, model="gpt-4o"):
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    return response.choices[0].message.content
