import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_upstage import ChatUpstage

from langgraph.graph import StateGraph, END
from utils.state import AgentState  # 경로 확인 필요
from graph.nodes.chat_node import chat_node
from graph.nodes.subject_info_node import subject_info_node
from graph.nodes.rag_review_node import rag_review_node

def route_question(state):
    """
    사용자의 질문을 분석하여 intent와 subject 결정하는 라우터 노드
    """
    print("---ROUTING QUESTION---")
    
    # 1. 상태에서 마지막 메시지 가져오기
    user_query = state["messages"][-1].content
    
    # 2. 의도와 대상을 추출하기 위한 시스템 프롬프트 설정
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 사용자의 질문 의도를 분류하는 라우팅 전문가입니다.
        반드시 아래의 JSON 형식으로만 답변하세요.
        
        분류 기준:
        1. intent:
           - 'chat': 인사, 잡담, 스마트폰과 관련 없는 일반 대화
           - 'info': 스마트폰의 가격, 스펙, 출시일 등 공식 정보 질문
           - 'review': 스마트폰의 사용 후기, 장단점, 리뷰 관련 질문
        
        2. subject:
           - '갤럭시S24', '아이폰15', '픽셀8' 중 하나 (언급이 없으면 'none')
        
        JSON 예시: {{"intent": "review", "subject": "갤럭시S24"}} """),
        ("human", "{query}")
    ])
    
    # 3. LLM 설정 
    llm = ChatUpstage()
    chain = prompt | llm | JsonOutputParser()
    
    # 4. LLM 판단 실행 
    response = chain.invoke({"query": user_query})
    
    # 5. 상태(State) 업데이트
    return {
        "intent": response.get("intent", "chat"),
        "subject": response.get("subject", "none")
    }

# LangGraph에서 조건부 엣지로 사용할 함수
def decide_next_node(state):
    """
    라우팅 결과(intent)에 따라 어느 노드로 갈지 결정 
    """
    intent = state["intent"]
    
    if intent == "info":
        return "subject_info_node"
    elif intent == "review":
        return "rag_review_node"
    else:
        return "chat_node"
    
def create_graph():
    # 그래프 초기화
    workflow = StateGraph(AgentState)

    # 노드들 추가
    workflow.add_node("router", route_question)
    workflow.add_node("chat_node", chat_node)
    workflow.add_node("subject_info_node", subject_info_node)
    workflow.add_node("rag_review_node", rag_review_node)

    # 시작점 설정
    workflow.set_entry_point("router")

    # 조건부 라우팅 연결
    workflow.add_conditional_edges(
        "router",
        decide_next_node,
        {
            "chat_node": "chat_node",
            "subject_info_node": "subject_info_node",
            "rag_review_node": "rag_review_node"
        }
    )

    # 답변 완료 후 다시 Chat Node로 복귀
    workflow.add_edge("subject_info_node", "chat_node")
    workflow.add_edge("rag_review_node", "chat_node")
    workflow.add_edge("chat_node", END)

    return workflow.compile()