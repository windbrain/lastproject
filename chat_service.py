ANALYSIS_FORMAT = """
[분석 가이드라인]
사용자가 창업 아이템을 제시하면, 다음 4가지 항목에 맞춰 체계적으로 분석해 주세요.

1. 📊 잠재 고객 분석 (Target Audience): 주요 타겟층의 페르소나 정의 및 니즈 분석
2. 🔮 시장 전망 (Market Outlook): 시장 규모, 성장 가능성, 주요 트렌드
3. ⚖️ SWOT 분석: 강점(S), 약점(W), 기회(O), 위협(T)
4. 💡 성공 전략 (Success Strategy): 초기 진입 전략 및 마케팅 제안

반드시 위 소제목(이모지 포함)을 사용하여 가독성 좋은 마크다운 형식으로 작성하세요.
데이터에 기반한 논리적인 추론을 하고, 예비 창업자에게 실질적인 도움이 되는 구체적인 조언을 제공하세요.
"""

def get_ai_response(client, messages, persona="general", model="gpt-4o"):
    persona_prompts = {
        "general": """
        당신은 균형 잡힌 시각을 가진 '전문 창업 컨설턴트'입니다.
        말투: 전문적이고 격려하는, 정중한 해요체.
        태도: 전반적인 사업 타당성을 골고루, 객관적으로 분석합니다.
        """,
        "vc": """
        당신은 냉철하고 비판적인 '벤처 캐피탈리스트(VC)'입니다.
        말투: 직설적이고 날카로운, 팩트 중심의 해요체. (빈말 절대 금지, 뼈 때리는 조언)
        태도: 
        - 수익 모델(BM)과 시장 규모(TAM/SAM/SOM)를 최우선으로 검증합니다.
        - 리스크와 경쟁 우위를 집요하게 파고듭니다.
        - 분석 마지막 줄에 💰 **투자 매력도 점수 (0~100점)**와 그 이유를 한 줄로 냉정하게 평가하세요.
        """,
        "marketer": """
        당신은 트렌드에 민감한 '바이럴 마케팅 전문가'입니다.
        말투: 활기차고 통통 튀는, 에너지 넘치는 해요체. (유행어 활용 가능)
        태도:
        - 타겟 고객의 숨겨진 욕망(Needs)과 바이럴 포인트(Hook)를 찾아냅니다.
        - 경쟁사와 차별화된 브랜딩 및 킬러 콘텐츠 전략을 제안합니다.
        - 분석 마지막 줄에 🔥 **시장광/바이럴 점수 (0~100점)**와 그 이유를 한 줄로 유쾌하게 평가하세요.
        """
    }

    selected_identity = persona_prompts.get(persona, persona_prompts["general"])
    
    full_system_prompt = f"{selected_identity}\n\n{ANALYSIS_FORMAT}"

    messages_with_system = [{"role": "system", "content": full_system_prompt}] + messages
    
    response = client.chat.completions.create(
        model=model,
        messages=messages_with_system
    )
    return response.choices[0].message.content

def generate_bmc(client, messages, model="gpt-4o"):
    bmc_system_prompt = """
    당신은 스타트업 비즈니스 모델 분석가입니다.
    지금까지의 대화 내용을 바탕으로 '비즈니스 모델 캔버스(Business Model Canvas)'의 9가지 요소를 정리해 주세요.
    
     반드시 아래 JSON 포맷으로 출력해야 합니다 (Markdown 코드 블록 없이 순수 JSON만 출력):
    {
        "key_partners": "핵심 파트너 내용...",
        "key_activities": "핵심 활동 내용...",
        "key_resources": "핵심 자원 내용...",
        "value_propositions": "가치 제안 내용...",
        "customer_relationships": "고객 관계 내용...",
        "channels": "채널 내용...",
        "customer_segments": "고객 세그먼트 내용...",
        "cost_structure": "비용 구조 내용...",
        "revenue_streams": "수익원 내용..."
    }

    각 항목은 핵심만 요약해서 작성하세요.
    """
    
    messages_with_system = [{"role": "system", "content": bmc_system_prompt}] + messages
    
    response = client.chat.completions.create(
        model=model,
        messages=messages_with_system,
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content

def analyze_ratings(client, messages, model="gpt-4o"):
    rating_system_prompt = """
    당신은 스타트업 평가 위원입니다.
    지금까지의 대화 내용을 바탕으로 다음 5가지 항목에 대해 0~100점 사이의 점수를 매겨주세요.
    
    평가 항목:
    1. 시장성 (Marketability): 시장의 크기 및 수요
    2. 수익성 (Profitability): BM의 타당성 및 수익 창출 능력
    3. 혁신성 (Innovation): 기존 솔루션 대비 차별점
    4. 실행 가능성 (Feasibility): 팀 역량 및 기술적 구현 가능성
    5. 성장 잠재력 (Growth Potential): 스케일업 가능성

    반드시 아래 JSON 포맷으로 출력하세요 (Markdown 없이):
    {
        "discussion": [
            {"speaker": "VC", "message": "이거 수익 모델이..."},
            {"speaker": "Marketer", "message": "에이, 요즘은..."},
            {"speaker": "CTO", "message": "기술적으로는..."},
            {"speaker": "Moderator", "message": "종합해보면..."}
        ]
    }
    """
    
    messages_with_system = [{"role": "system", "content": rating_system_prompt}] + messages
    
    response = client.chat.completions.create(
        model=model,
        messages=messages_with_system,
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content
