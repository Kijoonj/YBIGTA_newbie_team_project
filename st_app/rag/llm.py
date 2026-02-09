import os
from langchain_upstage import ChatUpstage, UpstageEmbeddings

# [1] LLM 모델 가져오기 (Router, Info, Review 노드 공통)
def get_llm(model_name="solar-pro"):
    """
    모든 노드에서 공통으로 사용할 LLM 객체를 반환합니다.
    temperature=0 으로 설정하여 일관된 답변을 유도합니다.
    """
    return ChatUpstage(
        model=model_name,
        temperature=0, 
    )

# [2] 임베딩 모델 가져오기 (Embedder, Retriever 공통)
def get_embeddings():
    """
    FAISS 구축 및 검색에 사용할 임베딩 모델을 반환합니다.
    """
    return UpstageEmbeddings(model="solar-embedding-1-large")