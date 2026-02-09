import json
import os
from langchain_core.messages import AIMessage

def subject_info_node(state):
    """
    subjects.json 파일에서 스마트폰의 공식 정보를 찾아 답변하는 노드.
    """
    print("---CALLING SUBJECT INFO NODE---")
    
    # 1. 상태에서 분석된 대상(subject) 가져오기
    target_subject = state.get("subject", "none")
    
    # 2. subjects.json 파일 읽기
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(os.path.dirname(current_dir)) # st_app/ 까지 올라감
    json_path = os.path.join(base_dir, "db", "subject_information", "subjects.json")
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 3. 해당 스마트폰 정보가 있는지 확인
        if target_subject in data:
            info = data[target_subject]
            answer_text = (
                f"문의하신 {target_subject}에 대한 공식 정보입니다.\n\n"
                f"📱 설명: {info['description']}\n"
                f"💰 가격: {info['price']}\n"
                f"⚙️ 주요 스펙: {info['specs']}"
            )
        else:
            answer_text = f"죄송합니다. {target_subject}에 대한 상세 정보를 찾을 수 없습니다."
            
    except Exception as e:
        answer_text = f"데이터를 읽는 중 오류가 발생했습니다: {str(e)}"

    # 4. 답변을 메시지 형태로 추가하고, context도 업데이트
    return {
        "messages": [AIMessage(content=answer_text)],
        "context": answer_text  # 나중에 참조할 수 있게 저장
    }