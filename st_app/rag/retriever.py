import os
from langchain_upstage import UpstageEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

load_dotenv()

class ReviewRetriever:
    """리뷰 검색기 - FAISS에서 관련 리뷰를 찾아줍니다"""
    
    def __init__(self):
        """초기화: FAISS 인덱스를 불러옵니다"""
        print("Retriever 초기화 중...")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        db_path = os.path.join(current_dir, "..", "db", "faiss_index")
        db_path = os.path.abspath(db_path)
        
        print(f"DB 경로: {db_path}")
        
        embedding_model = UpstageEmbeddings(model="solar-embedding-1-large")
        
        self.vectorstore = FAISS.load_local(
            db_path, 
            embedding_model,
            allow_dangerous_deserialization=True
        )
        
        print("Retriever 준비 완료!")
    
    def get_relevant_documents(self, query, k=3):
        """
        질문과 관련된 리뷰를 찾습니다
        
        Args:
            query (str): 사용자 질문 (예: "갤럭시 발열 어때?")
            k (int): 가져올 문서 개수 (기본값: 3개)
        
        Returns:
            list: 관련 리뷰 문서 리스트
        """
        print(f"검색 중: '{query}'")
        
        docs = self.vectorstore.similarity_search(query, k=k)
        
        print(f"{len(docs)}개 문서 발견!")
        
        return docs
    
    def get_relevant_texts(self, query, k=3):
        """
        질문과 관련된 리뷰 텍스트만 반환 (문자열 리스트)
        
        Args:
            query (str): 사용자 질문
            k (int): 가져올 문서 개수
        
        Returns:
            list[str]: 리뷰 텍스트 리스트
        """
        docs = self.get_relevant_documents(query, k)
        
        texts = [doc.page_content for doc in docs]
        
        return texts


# 테스트용 코드
if __name__ == "__main__":
    print("=" * 50)
    print("📋 Retriever 테스트 시작")
    print("=" * 50)
    
    # Retriever 생성
    retriever = ReviewRetriever()
    
    print("\n" + "=" * 50)
    
    # 테스트 질문들
    test_queries = [
        "갤럭시 발열 어때?",
        "아이폰 배터리는?",
        "픽셀 카메라 좋아?"
    ]
    
    for query in test_queries:
        print(f"\n🔍 질문: {query}")
        print("-" * 50)
        
        # 관련 리뷰 검색 (3개)
        reviews = retriever.get_relevant_texts(query, k=3)
        
        # 결과 출력
        for i, review in enumerate(reviews, 1):
            print(f"{i}. {review}")
        
        print("-" * 50)