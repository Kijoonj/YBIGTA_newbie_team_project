import os
from langchain_upstage import ChatUpstage, UpstageEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage

def rag_review_node(state):
    print("\n--- 🔵 RAG Review Node 진입 ---")
    
    user_query = state["messages"][-1].content
    
    # 1. 경로 설정
    current_file_path = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))
    index_path = os.path.join(project_root, "db", "faiss_index")
    
    try:
        # 2. FAISS 로드
        embeddings = UpstageEmbeddings(model="solar-embedding-1-large")
        vectorstore = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
        
        # 3. 검색 (k=3 -> k=5로 늘려서 더 많은 문맥 확보)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        docs = retriever.invoke(user_query)
        
        # [디버깅] 검색된 내용 터미널에 출력 (필수 확인!)
        print(f"🔍 '{user_query}'에 대한 검색 결과:")
        for i, doc in enumerate(docs):
            print(f"[{i+1}] {doc.page_content}")

        # 4. 검색 결과가 없거나 부실할 경우 처리
        if not docs:
            return {"messages": [AIMessage(content="관련된 리뷰 데이터를 찾을 수 없습니다.")], "intent": "review"}

        context = "\n".join([f"- {doc.page_content}" for doc in docs])
        
        # 5. 프롬프트 (접속사 금지 & 사실 기반 강제)
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 냉철한 리뷰 분석가입니다.
            제공된 [검색된 리뷰] 목록을 읽고 질문에 답하세요.

            **절대 지켜야 할 규칙:**
            1. **"또한", "하지만", "그리고"** 같은 접속사로 문장을 시작하지 마세요. 바로 결론부터 말하세요.
            2. [검색된 리뷰]에 없는 내용은 절대 지어내지 마세요.
            3. 긍정/부정 의견이 있다면 가감 없이 그대로 전달하세요. (예: "발열이 있다는 의견이 있습니다.")
            4. 만약 질문과 관련된 리뷰가 목록에 하나도 없다면, 솔직하게 "관련된 리뷰 정보가 부족합니다"라고 답하세요.

            [검색된 리뷰]
            {context}"""),
            ("human", "{query}")
        ])
        
        # 6. LLM 실행
        llm = ChatUpstage(model="solar-pro", temperature=0)
        chain = prompt | llm
        response = chain.invoke({"context": context, "query": user_query})
        
        answer_text = response.content
        
    except Exception as e:
        print(f"❌ 에러: {e}")
        answer_text = "리뷰 시스템에 오류가 발생했습니다."

    return {
        "messages": [AIMessage(content=answer_text)], 
        "intent": "review"
    }