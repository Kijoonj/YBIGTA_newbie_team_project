import json
import os
from langchain_upstage import ChatUpstage
from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate

# [1] LLM 설정
def get_local_llm():
    # temperature=0: 사실 기반 답변을 위해 창의성 최소화
    return ChatUpstage(model="solar-pro", temperature=0)

# [2] 프롬프트 개선 (데이터 포맷팅 반영 & 답변 양식 강제)
INFO_PROMPT = """
당신은 스마트폰 정보 안내 AI입니다.
아래 [제품 스펙]을 참고하여 사용자의 질문에 답변하세요.

**지시사항:**
1. [제품 스펙]에 있는 내용만 사용하여 답변하세요.
2. "가격"을 물어보면 숫자를 포함하여 정확히 답변하세요.
3. 답변은 "출처" 같은 말로 시작하지 말고, 바로 결론부터 말하세요.
4. 정보가 없으면 "해당 내용은 데이터에 없습니다."라고 하세요.

[제품 스펙]
{info}

질문: {question}
답변:
"""

# [3] 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "../../db/subject_information/subjects.json")

def subject_info_node(state):
    print("\n--- 🟢 Subject Info Node 진입 ---")
    
    question = state["messages"][-1].content
    
    # JSON 로드
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return {"messages": [AIMessage(content="데이터베이스 오류")]}

    # 키워드 매칭
    target_info = None
    target_product = None
    
    normalized_question = question.replace(" ", "").lower()
    
    for product_name, info in data.items():
        normalized_product = product_name.replace(" ", "").lower()
        if normalized_product in normalized_question:
            # [핵심 수정] 딕셔너리를 보기 좋은 텍스트로 변환 (Dict -> Formatted String)
            # 예: "{'price': '100원'}" -> "- price: 100원"
            target_info = "\n".join([f"- {key}: {value}" for key, value in info.items()])
            target_product = product_name
            break
            
    if not target_info:
        return {"messages": [AIMessage(content="갤럭시S24, 아이폰15, 픽셀8 중에서 질문해주세요.")]}

    print(f"✅ 제품 찾음: {target_product}")
    print(f"📝 프롬프트 입력 데이터:\n{target_info}") # 터미널에서 데이터가 예쁘게 나오는지 확인!

    # LLM 호출
    llm = get_local_llm()
    prompt_template = PromptTemplate.from_template(INFO_PROMPT)
    chain = prompt_template | llm
    
    response = chain.invoke({"info": target_info, "question": question})
    
    return {
        "messages": [response], 
        "answer": response.content,
        "intent": "info"
    }