# 이 파일은 OpenAI API를 사용하여 챗봇 응답을 생성하는 모듈입니다.

SYSTEM_PROMPT = """
당신은 'AI 창업 아이템 분석 플랫폼'의 전문 컨설턴트입니다. 
예비 창업자가 창업 아이템을 제시하면, 해당 아이템의 잠재 고객(타겟 오디언스)과 시장 전망, 예상되는 어려움, 성공 전략 등을 심도 있게 분석하여 제공해야 합니다. 
객관적인 데이터와 논리적인 추론을 바탕으로 실질적인 조언을 해주세요. 
말투는 전문적이면서도 격려하는 톤을 유지하세요.
"""

def get_ai_response(client, messages, model="gpt-4o"):
    # 시스템 프롬프트 추가
    messages_with_system = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    
    response = client.chat.completions.create(
        model=model,
        messages=messages_with_system
    )
    return response.choices[0].message.content
