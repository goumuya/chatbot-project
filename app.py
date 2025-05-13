import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# .env 파일에서 API 키 로드
load_dotenv()

client = OpenAI(
    #api_key=os.getenv("GROQ_API_KEY"),
    #api_key=os.getenv("OPENAI_PAID_API_KEY"),
    api_key=st.secrets["OPENAI_PAID_API_KEY"],
    #base_url="https://api.groq.com/openai/v1"
)

# Streamlit 기본 설정
st.set_page_config(page_title="🧠 김현수 챗봇 갖다붙이기 연습용", page_icon="💬")
st.title("🧠 Gemma2-9B-it 모델 API 챗봇")
st.markdown("""
# 👋 환영합니다!
이곳은 챗봇 서비스입니다. \n
아래 입력창에 질문을 입력해보세요!\n
한국어가 서툴러서 오타 혹은 갑작스런 언어변경이 종종 발생합니다.
""")
st.caption("김현수 물어봐도 모름 / 한국어 서툼")

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

# ▶ 성격 선택 화면 (초기 1회)
# if st.session_state.personality is None:
#     st.subheader("🤖 AI 성격을 골라주세요!")
#     selected = st.radio("원하는 성격을 선택하세요:", ["Sweetie", "Lover", "Strictly", "twisted", "Ignore"])
#     if st.button("선택 완료"):
#         st.session_state.personality = selected
#         st.session_state.messages.append({
#             "role": "assistant",
#             "content": f"안녕하세요! {selected}한 AI입니다. 무엇을 도와드릴까요?"
#         })
#         st.rerun()
#     st.stop()

# 드롭다운으로 성격 선택 가능하게
personality_list = list(system_prompts.keys())

selected = st.selectbox("🤖 현재 AI 성격 : ", personality_list, 
                        index=personality_list.index(st.session_state.personality))

#성격 변경 감지
if selected != st.session_state.personality:
    st.session_state.personality = selected
    st.session_state.messages.append({
        "role": "assistant",
        "conetent": f"성격이 {selected}으로 바뀌었습니다."
    })



# 대화 기록 출력
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])
for message in st.session_state.messages:
    if "role" in message and "content" in message:
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
        model = "gpt-4o",
        #model = "gpt-3.5-turbo",
        #model = "llama3-70b-8192", # Groq 모델
        #model = "gemma2-9b-it",
        messages=[{"role": "system", "content": system_prompts[st.session_state.personality]}] + st.session_state.messages,
        stream=True # 스트리밍 활성화
    )

    for chunk in response:
        if chunk.choices[0].delta.content:
            full_reply += chunk.choices[0].delta.content
            assistant_response.markdown(full_reply + "▌") # 커서 느낌

    # 스트리밍 끝난 후 최종 메시지 표시
    assistant_response.markdown(full_reply)
    st.session_state.messages.append({"role": "assistant", "content": full_reply})
