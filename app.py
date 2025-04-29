import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# .env 파일에서 API 키 로드
load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# Streamlit 기본 설정
st.set_page_config(page_title="🧠 나만의 챗봇 (스트리밍)", page_icon="💬")
st.title("🧠 나만의 Groq Streaming 챗봇")
st.caption("Streamlit + Groq API(streaming)")

# 세션 상태로 대화 기록 관리
if "messages" not in st.session_state:
    st.session_state.messages = []

# 대화 기록 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력 받기
user_input = st.chat_input("메시지를 입력하세요.")

if user_input:
    # 유저 메시지 화면에 표시
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 빈 챗 메시지를 미리 생성 (스트리밍 중 실시간 업데이트 용)
    assistant_message = st.chat_message("assistant")
    assistant_response = assistant_message.empty()

    full_reply = ""

    # 스트리밍 응답 받기
    response = client.chat.completions.create(
        #model = "gpt-4o",
        #model = "llama3-70b-8192", # Groq 모델
        model = "gemma2-9b-it",
        messages=st.session_state.messages,
        stream=True # 스트리밍 활성화
    )

    for chunk in response:
        if chunk.choices[0].delta.content:
            full_reply += chunk.choices[0].delta.content
            assistant_response.markdown(full_reply + "▌") # 커서 느낌

    # 스트리밍 끝난 후 최종 메시지 표시
    assistant_response.markdown(full_reply)
    st.session_state.messages.append({"role": "assistant", "content": full_reply})
