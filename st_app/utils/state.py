from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

# LangGraph에서 노드 간 데이터를 전달하는 '택배 상자' 정의
class AgentState(TypedDict):
    # 1. messages: 대화 기록 (필수)
    # add_messages: 새 메시지가 오면 기존 리스트를 덮어쓰지 않고 '추가(append)'하라는 명령
    messages: Annotated[List[BaseMessage], add_messages]
    
    # 2. intent: 사용자의 의도 (Router가 판단한 결과)
    # 예: "review", "info", "chat" 중 하나가 저장됨
    intent: str 
    
    # 3. context: 검색된 문서나 정보 (RAG Node나 Info Node가 채우는 곳)
    # 예: "갤럭시 S24의 가격은 115만원입니다..." 등의 텍스트가 저장됨
    context: str
    
    # 4. answer: 최종 답변 (선택 사항)
    # LLM이 생성한 최종 응답 텍스트를 저장
    answer: str