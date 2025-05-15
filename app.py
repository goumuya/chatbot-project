import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# .env 파일에서 API 키 로드
load_dotenv()

client = OpenAI(
    api_key=st.secrets["OPENAI_PAID_API_KEY"]
)

# Streamlit 기본 설정
st.set_page_config(page_title="🧠 말동무 챗봇 연습용", page_icon="💬")
st.title("🧠 심심풀이 말동무 챗봇")
st.markdown("""
# 👋 환영합니다!
이곳은 말동무 챗봇 서비스입니다. 
성격을 고르고, 아래 입력창에서 간단한 수다를 즐겨보세요!
""")
st.caption("김현수 물어봐도 모릅니다.ㅠ")

# ▶ 성격 프롬프트 사전
system_prompts = {
    "Sweetie": "You are an AI who always talks to people in a kind and gentle way. and You must answer in Korean.",
    "Lover" : "You are an AI who always communicates with people in a sweet and loving way. Please answer in a comfortable but loving way as much as you can to your lover. and You must answer in Korean",
    "Strictly": "You're an AI that only responds to you with a firm, strict tone. and You must answer in Korean.",
    "twisted": "You're an AI who only talks in a grumpy, grumpy tone. You reply in a slightly upset tone. Instead, and You must answer in Korean.",
    "Ignore": "You're an AI who talks in a chilly, hateful way for some reason. You respond in a slightly angry way. and You must answer in Korean."
}

# 세션 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "personality" not in st.session_state:
    st.session_state.personality = "Sweetie"

# 드롭다운으로 성격 선택 가능하게
personality_list = list(system_prompts.keys())

with st.sidebar:
    st.markdown("## 🤖 AI 성격 설정")
    selected = st.selectbox("현재 성격을 선택하세요", personality_list,
                            index=personality_list.index(st.session_state.personality))
    if st.button("💬 대화 리셋"):
        st.session_state.messages = []
        st.rerun()

# 성격 변경 감지
if selected != st.session_state.personality:
    st.session_state.personality = selected
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"성격이 {selected}으로 바뀌었습니다."
    })

# 대화 기록 출력
for message in st.session_state.messages:
    if "role" in message and "content" in message:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

user_input = None

# 사용자 입력 받기
text_input = st.chat_input("메시지를 입력하세요.")
if text_input:
    user_input = text_input
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

# GPT 응답 생성
if user_input:
    assistant_message = st.chat_message("assistant")
    assistant_response = assistant_message.empty()
    full_reply = ""

    valid_messages = [
        msg for msg in st.session_state.messages
        if isinstance(msg, dict) and "role" in msg and "content" in msg
    ]

    response = client.chat.completions.create(
        model = "gpt-4o",
        messages=[{"role": "system", "content": system_prompts[st.session_state.personality]}] + valid_messages,
        stream=True
    )

    for chunk in response:
        if chunk.choices[0].delta.content:
            full_reply += chunk.choices[0].delta.content
            assistant_response.markdown(full_reply + "▌")

    assistant_response.markdown(full_reply)
    st.session_state.messages.append({"role": "assistant", "content": full_reply})