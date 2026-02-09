from langchain_upstage import ChatUpstage
from langchain_core.messages import AIMessage

def chat_node(state):
    """
    일상적인 대화나 분류되지 않은 일반 질문에 대해 답변하는 노드.
    """
    print("---CALLING CHAT NODE---")
    
    # 1. 대화 기록 가져오기
    messages = state["messages"]
    
    # 2. LLM 설정 (Upstage 사용)
    llm = ChatUpstage()
    
    # 3. LLM 호출 (그동안의 대화 맥락을 모두 전달하여 자연스러운 답변 유도)
    response = llm.invoke(messages)
    
    # 4. 상태 업데이트 (AI의 답변을 메시지 리스트에 추가)
    return {
        "messages": [response],
        "answer": response.content
    }