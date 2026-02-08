import os
from langchain_upstage import ChatUpstage, UpstageEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage

def rag_review_node(state):
    """
    FAISS 인덱스에서 관련 리뷰를 찾아 답변을 생성하는 노드.
    """
    print("---CALLING RAG REVIEW NODE---")
    
    # 1. 사용자 질문 가져오기
    user_query = state["messages"][-1].content
    
    # 2. FAISS 인덱스 경로 설정
    current_file_path = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))
    index_path = os.path.join(project_root, "db", "faiss_index")
    
    try:
        # 3. FAISS 로드 (팀원 A가 사용한 임베딩 모델과 일치해야 함)
        embeddings = UpstageEmbeddings(model="solar-embedding-1-large")
        
        vectorstore = FAISS.load_local(
            index_path, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        
        # 4. 관련 리뷰 검색 (가장 유사한 3개 문장 추출)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        docs = retriever.invoke(user_query)
        
        # 검색된 리뷰 텍스트 합치기
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # 5. 리뷰 기반 답변 생성을 위한 프롬프트
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 스마트폰 사용 후기 전문가입니다. 
            아래 제공된 [실제 사용자 리뷰]들만을 근거로 사용자의 질문에 답변하세요. 
            리뷰에 없는 내용은 지어내지 마세요.
            
            [실제 사용자 리뷰]
            {context}"""),
            ("human", "{query}")
        ])
        
        # 6. LLM 실행 (Upstage 사용)
        llm = ChatUpstage()
        chain = prompt | llm
        response = chain.invoke({"context": context, "query": user_query})
        
        answer_text = response.content
        
    except Exception as e:
        answer_text = f"리뷰를 불러오는 중 오류가 발생했습니다: {str(e)}"
        context = ""

    # 7. 상태 업데이트
    return {
        "messages": [AIMessage(content=answer_text)],
        "context": context
    }