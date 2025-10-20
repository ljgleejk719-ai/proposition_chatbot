# app.py (v3)

import streamlit as st
import google.generativeai as genai
import os

# -----------------------------------------------------------------
# 1. 챗봇의 '뇌' (시스템 프롬프트) - (이전과 동일)
# -----------------------------------------------------------------
SYSTEM_PROMPT = """
너는 고등학교 수학 선생님이야. 학생에게 '필요조건'과 '충분조건'을 가르쳐야 해.
다음 규칙을 반드시 지켜:

1.  모든 설명은 '진리집합의 포함관계'($\mathbb{P}$, $\mathbb{Q}$)를 통해서만 설명해야 해.
2.  절대 정답을 먼저 알려주지 마. 학생이 스스로 답을 찾도록 '열린 질문'만 던져.
3.  대화는 다음 순서로 진행해.
    a. 학생이 $P, Q$를 만들면, $P$의 진리집합 $\mathbb{P}$가 무엇인지 질문한다.
    b. $\mathbb{Q}$의 진리집합이 무엇인지 질문한다.
    c. 두 집합 $\mathbb{P}$와 $\mathbb{Q}$ 사이에 어떤 포함관계($\subseteq$ 또는 $\supseteq$)가 성립하는지 질문한다.
    d. 학생이 포함관계를 맞히면, 그제야 그 관계가 '필요조건'인지 '충분조건'인지 연결해서 설명해 준다.
    e. 학생이 "$\mathbb{Q} \subseteq \mathbb{P}$"라고 답하면, "맞아! $\mathbb{Q}$가 $\mathbb{P}$에 쏙 들어가지? 이럴 때 $Q$는 $P$이기 위한 '충분조건'이라고 불러."라고 응답한다.
4.  학생이 중간에 틀리면, 힌트를 주거나 더 쉬운 질문으로 유도해.
5.  LaTeX 문법을 사용해서 수학 기호($\mathbb{P}$, $\mathbb{Q}$, $\subseteq$)를 명확하게 표시해.
"""

# -----------------------------------------------------------------
# 2. Streamlit 웹페이지 설정
# -----------------------------------------------------------------
st.set_page_config(
    page_title="진리집합 튜터 🤖",
    page_icon="🤖"
)

st.title("진리집합으로 배우는 필요충분조건 💬")
st.caption("AI 튜터와 함께 진리집합의 포함관계를 탐색해 보세요.")

# -----------------------------------------------------------------
# 3. AI 모델 및 채팅 세션 초기화
# -----------------------------------------------------------------

# [로컬 테스트용] 
# ⚠️ genai.configure... 이 부분에 선생님의 API 키를 직접 넣어주세요.
# ⚠️ GitHub에 올리기 전에는 이 부분을 지우고 'Secrets' 방식으로 되돌려야 합니다.
#
# (이전 코드와 동일한 부분입니다. 여기에 키를 넣어주세요.)
try:
    # ❗️ 로컬 테스트 시 이 줄에 키를 직접 입력하세요.
    genai.configure(api_key="여기에_선생님의_API_키를_붙여넣으세요")
except AttributeError:
    # ❗️ 배포 시에는 Streamlit Secrets를 사용합니다.
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    except TypeError:
        st.error("Streamlit Secrets에 GEMINI_API_KEY가 설정되지 않았습니다.")
        st.stop()


# 챗봇 모델 설정 (시스템 프롬프트 적용)
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash', # 👈 속도 개선을 위해 'flash' 모델로 변경!
    system_instruction=SYSTEM_PROMPT
)

# Streamlit의 st.session_state를 사용해 채팅 기록 저장
if "chat_session" not in st.session_state:
    # 새 채팅 세션 시작
    st.session_state.chat_session = model.start_chat(history=[])

if "messages" not in st.session_state:
    # 앱 시작 시 첫 메시지
    st.session_state.messages = [{
        "role": "assistant",
        "content": "안녕하세요! 필요충분조건, 진리집합으로 같이 공부해 볼까요?"
    }]

# -----------------------------------------------------------------
# 4. 채팅 대화창 구현 (대대적 수정!)
# -----------------------------------------------------------------

# 이전 대화 기록 모두 표시
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# --- 입력 방식 분기 ---
# 1. 맨 처음 (대화가 1개 = AI 인사말만 있을 때): P/Q 입력 상자 표시
if len(st.session_state.messages) == 1:
    p_input = st.text_input("조건 P:", placeholder="예: a=0 이고 b=0 이다")
    q_input = st.text_input("조건 Q:", placeholder="예: ab=0 이다")

    if st.button("AI 튜터에게 질문하기 🚀"):
        if not p_input or not q_input:
            st.warning("P와 Q 조건을 모두 입력해야 합니다!")
        else:
            # 1. 사용자가 입력한 P/Q를 챗봇에 "user" 메시지로 전달
            formatted_prompt = f"P: {p_input}\nQ: {q_input}"
            st.session_state.messages.append({"role": "user", "content": formatted_prompt})
            
            # 2. AI에게 P/Q 전달 및 답변 요청 (로딩 스피너 포함)
            with st.spinner("AI가 조건을 분석 중입니다..."):
                try:
                    response = st.session_state.chat_session.send_message(formatted_prompt)
                    bot_response = response.text
                    st.session_state.messages.append({"role": "assistant", "content": bot_response})
                    
                    # P/Q 입력창을 숨기고 채팅창으로 넘어가기 위해 페이지 새로고침
                    st.rerun() 
                except Exception as e:
                    st.error(f"AI 응답 중 오류가 발생했습니다: {e}")
                    # 오류 발생 시 P/Q 입력을 다시 받도록 마지막 메시지 삭제
                    st.session_state.messages.pop() 


# 2. 대화가 시작된 후 (대화가 2개 이상일 때): 일반 채팅 입력창 표시
else:
    if prompt := st.chat_input("진리집합을 입력하거나 질문해 보세요..."):
        # 1. 사용자 메시지를 기록하고 화면에 표시
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. AI에게 답변 요청 (로딩 스피너 포함)
        with st.spinner("답변 생성중..."):
            try:
                response = st.session_state.chat_session.send_message(prompt)
                
                # 3. AI 응답을 기록하고 화면에 표시
                bot_response = response.text
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
                with st.chat_message("assistant"):
                    st.markdown(bot_response)

            except Exception as e:
                st.error(f"AI 응답 중 오류가 발생했습니다: {e}")
