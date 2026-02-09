from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

# LangGraph에서 노드 간 데이터를 전달하는 '택배 상자' 정의
class AgentState(TypedDict):
    # 1. 대화 기록
    messages: Annotated[List[BaseMessage], add_messages]
    
    # 2. 사용자의 의도 (chat, info, review)
    intent: str 
    
    # 3. 질문의 대상 (갤럭시S24, 아이폰15, 픽셀8)
    subject: str
    
    # 4. 검색된 참고 정보 (RAG 결과나 JSON 데이터)
    context: str
    
    # 5. 최종 답변
    answer: str