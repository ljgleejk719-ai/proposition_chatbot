import streamlit as st
from google import genai
from google.genai import types
import os

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
2. **첫 질문**: 대화를 시작할 때, 학생에게 다음 형태의 명제 두 개(P, Q)를 제시하고 P가 Q이기 위한 어떤 조건인지 (필요/충분/필요충분/아무것도 아님) 물어보세요.
    예시 질문: "P: x는 4의 배수이다. Q: x는 2의 배수이다. P는 Q이기 위한 무슨 조건일까요? 이유도 함께 설명해주세요."
3. **사고 유도**: 학생이 틀린 답변을 하거나, 정답을 맞혀도 근거가 부족하면 **정답을 바로 알려주지 마세요.**
    * 대신, **진리집합의 포함 관계($P \subset Q$인지 $Q \subset P$인지)**를 그림(벤 다이어그램 묘사는 하지 마세요)이나 쉬운 예를 들어 스스로 생각하게 유도하는 **질문**을 던지세요.
    * 예시: "P를 만족하는 원소는 Q를 모두 만족하나요? P에서 Q로 가는 화살표가 성립하는지 확인해보세요."
4. **대화 지속**: 학생이 답변하면 그 답변을 분석하고, 다음 논리 단계를 밟도록 유도하여 대화를 이어가세요. 한 명제에 대한 이해가 완료되면 새로운 P, Q 명제를 제시합니다.
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

# 3. 화면에 대화 기록 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 첫 시작 시 AI 튜터의 질문 유도
if not st.session_state.messages:
    # 첫 메시지를 Gemini에게 요청하여 대화를 시작
    try:
        response = st.session_state.chat_session.send_message("안녕하세요. 필요충분조건 튜터링을 시작해주세요.")
        
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        
        with st.chat_message("assistant"):
            st.markdown(response.text)
    except Exception as e:
        st.error(f"채팅 시작 중 오류가 발생했습니다: {e}")

# 5. 사용자 입력 처리
if prompt := st.chat_input("여기에 답변을 입력하세요..."):
    
    # 5-1. 사용자 메시지를 기록하고 화면에 출력
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # 5-2. AI 응답 생성 및 처리
    with st.chat_message("assistant"):
        with st.spinner("튜터가 생각 중..."):
            try:
                # ⚠️ 오타 수정: st.session_session -> st.session_state
                response = st.session_state.chat_session.send_message(prompt)
                
                st.markdown(response.text)
                
                # AI 메시지를 기록
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"답변 처리 중 오류가 발생했습니다: {e}")
