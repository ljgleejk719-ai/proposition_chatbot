import streamlit as st
from google import genai
from google.genai import types
import os
from datetime import datetime

# -----------------------------------------------------
# 0. 설정 및 API 키
# -----------------------------------------------------
# ⚠️ 주의: 키를 직접 노출하지 않고 Secrets에서 가져옵니다.
API_KEY = "AIzaSyAU1iwa-OFdgFyiookp8Rcwez6rlNXajm4"
MODEL_NAME = 'gemini-2.5-flash' 

# -----------------------------------------------------
# 1. AI 튜터 시스템 프롬프트 (Chat Session용)
# -----------------------------------------------------
SYSTEM_INSTRUCTION_TUTOR = """
당신은 고등학교 수학 '필요 충분 조건' 단원의 전문 대화형 AI 튜터입니다.
당신의 목표는 학생과의 지속적인 대화를 통해 개념 이해도를 심층적으로 확인하고 논리적 사고를 유도하는 것입니다.

[대화 원칙]
1. **역할극**: 학생에게 친절하고 격려하는 말투로 대화하세요.
2. **랜덤 문제 제시 및 반복 (강화)**:
    * 대화를 시작할 때, 학생에게 **수학과 관련된 랜덤 명제 두 개(P, Q)**를 제시하고 P가 Q이기 위한 어떤 조건인지 (필요/충분/필요충분/아무것도 아님) 물어보세요.
    * 학생이 **한 문제에 대해 정확한 조건과 논리적 근거를 제시하여 이해했음이 확인되면**, 칭찬과 함께 **새로운 랜덤 명제**를 제시하며 다음 문제로 넘어가세요.
3. **사고 유도 및 진리집합 강조 (강화)**: 학생이 틀린 답변을 하거나, 정답을 맞혀도 근거가 부족하면 **정답을 바로 알려주지 마세요.**
    * 학생이 스스로 오류를 발견하고 생각할 수 있도록 **구체적이고 핵심을 짚는 질문**을 던집니다.
    * **특히, 질문을 통해 진리집합의 포함 관계 (P ⊂ Q 인지, Q ⊂ P 인지)를 스스로 추론하도록 유도하세요.**
    * 예시 질문: "P를 만족하는 진리집합이 Q를 만족하는 진리집합에 완전히 포함되나요? 그 반대의 경우는 어떤가요?"
4. **대화 지속**: 학생의 이해도를 확인하고 다음 논리 단계를 밟도록 유도하여 대화를 이어가세요.
"""

# -----------------------------------------------------
# 2. Streamlit 대화형 UI 및 세션 관리
# -----------------------------------------------------
st.set_page_config(page_title="필요 충분 조건 대화형 튜터", layout="centered")
st.title("🤝 필요 충분 조건 대화형 튜터")
st.caption("AI 튜터와 대화하며 필요 조건과 충분 조건을 마스터하세요!")

# API 키 설정 (Secrets 실패 시 API_KEY 변수를 사용하도록 수정)
try:
    api_key = st.secrets.get("GEMINI_API_KEY", API_KEY)
except KeyError:
    api_key = API_KEY

if not api_key:
    st.error("⚠️ API Key가 설정되지 않았습니다.")
    st.stop()

# Gemini 클라이언트 초기화
client = genai.Client(api_key=api_key)

# 채팅 세션 초기화 (대화 기록 저장)
if "chat_session" not in st.session_state:
    # 새로운 채팅 세션을 생성하고 시스템 인스트럭션을 설정
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION_TUTOR
    )
    st.session_state.chat_session = client.chats.create(
        model=MODEL_NAME,
        config=config
    )

# 대화 기록 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []


# -----------------------------------------------------
# 3. 다운로드 기능 구현 함수 (추가)
# -----------------------------------------------------
def format_chat_history_for_download():
    """대화 기록을 텍스트 파일로 저장하기 위해 포맷합니다."""
    history_text = [f"--- 필요 충분 조건 튜터링 기록 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---"]
    
    for message in st.session_state.messages:
        role = "학생" if message["role"] == "user" else "튜터"
        content = message["content"].replace('\n', ' ') # 줄바꿈 제거
        history_text.append(f"[{role}]: {content}")
        
    return "\n".join(history_text)

# -----------------------------------------------------
# 4. 화면에 대화 기록 출력 및 다운로드 버튼 추가
# -----------------------------------------------------

# 다운로드 버튼 추가
if st.session_state.messages:
    download_data = format_chat_history_for_download()
    
    st.sidebar.download_button(
        label="📄 대화 내용 다운로드 (.txt)",
        data=download_data,
        file_name=f"필요충분조건_튜터링_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )
    # 다운로드 버튼은 화면을 깔끔하게 유지하기 위해 사이드바에 배치했습니다.

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. 첫 시작 시 AI 튜터의 질문 유도
if not st.session_state.messages:
    # 첫 메시지를 Gemini에게 요청하여 대화를 시작
    try:
        response = st.session_state.chat_session.send_message("안녕하세요. 필요충분조건 튜터링을 시작해주세요.")
        
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        
        with st.chat_message("assistant"):
            st.markdown(response.text)
    except Exception as e:
        st.error(f"채팅 시작 중 오류가 발생했습니다: {e}")

# 6. 사용자 입력 처리
if prompt := st.chat_input("여기에 답변을 입력하세요..."):
    
    # 6-1. 사용자 메시지를 기록하고 화면에 출력
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # 6-2. AI 응답 생성 및 처리
    with st.chat_message("assistant"):
        with st.spinner("튜터가 생각 중..."):
            try:
                response = st.session_state.chat_session.send_message(prompt)
                
                st.markdown(response.text)
                
                # AI 메시지를 기록
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"답변 처리 중 오류가 발생했습니다: {e}")
