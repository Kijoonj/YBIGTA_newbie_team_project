import os
import sys
from dotenv import load_dotenv
import streamlit as st

# 1. 로컬 환경 변수(.env) 로드
load_dotenv() 

# 2. 시스템 경로 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 3. API Key 설정 (로컬 + 클라우드 호환 코드)
# [수정된 부분] st.secrets가 없어도 에러나지 않게 try-except로 감쌉니다.
try:
    if "UPSTAGE_API_KEY" in st.secrets:
        os.environ["UPSTAGE_API_KEY"] = st.secrets["UPSTAGE_API_KEY"]
except FileNotFoundError:
    # 로컬에 secrets.toml 파일이 없으면 그냥 넘어갑니다. (.env를 쓰면 되니까요)
    pass
except Exception:
    pass

# 4. 키 확인 (없으면 중단)
if "UPSTAGE_API_KEY" not in os.environ:
    st.error("🚨 API Key가 없습니다! .env 파일을 확인해주세요.")
    st.stop()
from langchain_core.messages import HumanMessage, AIMessage

# B팀원의 코드 가져오기
try:
    from st_app.graph.router import create_graph
    app = create_graph()
except ImportError as e:
    st.error(f"Import Error: {e}")
    app = None
except Exception as e:
    st.error(f"Graph Init Error: {e}")
    app = None

# --- [여기서부터 UI 코드 시작] ---
st.set_page_config(page_title="스마트폰 리뷰 챗봇", page_icon="📱")
st.title("📱 스마트폰 구매 도우미 AI")
st.caption("갤럭시S24 | 아이폰15 | 픽셀8 - 리뷰, 가격, 스펙 비교")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "안녕하세요! 스마트폰에 대해 궁금한 점을 물어보세요."}
    ]

# 대화 기록 표시
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        st.chat_message("assistant").write(msg["content"])

# 입력 처리
if prompt := st.chat_input("질문을 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    if app:
        with st.spinner("AI가 답변을 생성 중입니다..."):
            try:
                # LangGraph 실행
                inputs = {"messages": [HumanMessage(content=prompt)]}
                result = app.invoke(inputs, config={"recursion_limit": 20})
                
                ai_answer = result["messages"][-1].content
                
                st.session_state.messages.append({"role": "assistant", "content": ai_answer})
                st.chat_message("assistant").write(ai_answer)
            except Exception as e:
                st.error(f"실행 중 오류 발생: {e}")