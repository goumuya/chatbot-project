import os
import json
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# .env 파일에서 API 키 로드
load_dotenv()

client = OpenAI(
    api_key=st.secrets["OPENAI_PAID_API_KEY"]
)

# 페이지 설정 및 말풍선 스타일
st.set_page_config(page_title="🧠 말동무 챗봇", page_icon="💬")
st.markdown("""
    <style>
    .chat-container {
        display: flex;
        width: 100%;
        margin: 8px 0;
    }
    .user-message {
        background-color: #5B9BF0;
        color: white;
        padding: 0.8em 1em;
        border-radius: 1em;
        border-top-right-radius: 0;
        max-width: 75%;
        align-self: flex-end;
        display: inline-block;
    }
    .assistant-message {
        background-color: #F1F0F0;
        color: black;
        padding: 0.8em 1em;
        border-radius: 1em;
        border-top-left-radius: 0;
        max-width: 75%;
        display: inline-block;
    }
    </style>
""", unsafe_allow_html=True)

# 타이틀 및 안내
st.title("🧠 심심풀이 말동무 챗봇")
st.markdown("""
# 👋 환영합니다!
이곳은 말동무 챗봇 서비스입니다. 
성격을 고르고, 아래 입력창에서 간단한 수다를 즐겨보세요!
""")
st.caption("김현수 물어봐도 모릅니다.ㅠ")

# 성격 프롬프트
system_prompts = {
    "Sweetie": "You are an AI who always talks to people in a kind and gentle way. and You must answer in Korean.",
    "Lover": "You are an AI who always communicates with people in a sweet and loving way. Please answer in a comfortable but loving way as much as you can to your lover. and You must answer in Korean",
    "Strictly": "You're an AI that only responds to you with a firm, strict tone. and You must answer in Korean.",
    "twisted": "You're an AI who only talks in a grumpy, grumpy tone. You reply in a slightly upset tone. Instead, and You must answer in Korean.",
    "Ignore": "You're an AI who talks in a chilly, hateful way for some reason. You respond in a slightly angry way. and You must answer in Korean."
}

# 한글 ↔ 영어 성격 매핑
personality_labels = {
    "다정한 친구": "Sweetie",
    "연인": "Lover",
    "엄격한 선생님": "Strictly",
    "투덜이": "twisted",
    "츤데레": "Ignore"
}

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "personality" not in st.session_state:
    st.session_state.personality = "Sweetie"
if "selected_label" not in st.session_state:
    st.session_state.selected_label = [k for k, v in personality_labels.items() if v == st.session_state.personality][0]

# 사이드바 UI
with st.sidebar:
    st.markdown("## 🤖 AI 성격 설정")
    st.selectbox(
        "현재 성격을 선택하세요", 
        list(personality_labels.keys()),
        index=list(personality_labels.keys()).index(st.session_state.selected_label),
        key="selected_label"
    )
    if st.button("💬 대화 리셋"):
        st.session_state.messages = []
        st.rerun()

# 대화 기록 저장
def save_dialogue_to_file(dialogue, filename="chat_log.json"):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            logs = json.load(f)
    else:
        logs = []

    logs.append(dialogue)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


# 성격 변경 감지
selected = personality_labels[st.session_state.selected_label]
if selected != st.session_state.personality:
    st.session_state.personality = selected
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"{st.session_state.selected_label}같은 성격으로 바뀌었습니다."
    })

# 사용자 입력 받기
user_input = st.chat_input("메시지를 입력하세요.")

# 사용자가 입력한 경우
if user_input:
    # 1. 사용자 메시지를 세션에 추가
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 2. 지금까지의 메시지 출력
    for message in st.session_state.messages:
        align = "flex-end" if message["role"] == "user" else "flex-start"
        css_class = "user-message" if message["role"] == "user" else "assistant-message"
        st.markdown(
            f"""
            <div class="chat-container" style="justify-content: {align};">
                <div class="{css_class}">{message['content']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 3. GPT 응답 생성 (타이핑 효과 포함)
    full_reply = ""
    valid_messages = [
        msg for msg in st.session_state.messages
        if isinstance(msg, dict) and "role" in msg and "content" in msg
    ]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompts[st.session_state.personality]}] + valid_messages,
        stream=True
    )

    # 4. 타자치는 UI 표시
    placeholder = st.empty()
    for chunk in response:
        if chunk.choices[0].delta.content:
            full_reply += chunk.choices[0].delta.content
            placeholder.markdown(
                f"""
                <div class="chat-container" style="justify-content: flex-start;">
                    <div class="assistant-message">{full_reply}▌</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # 5. 최종 응답 표시 (커서 제거)
    placeholder.markdown(
        f"""
        <div class="chat-container" style="justify-content: flex-start;">
            <div class="assistant-message">{full_reply}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 6. 응답 메시지 세션에 저장
    st.session_state.messages.append({"role": "assistant", "content": full_reply})

    # 6.1 대화기록 파일 저장
    save_dialogue_to_file({
        "user":user_input,
        "assistant": full_reply
    })

    # 7. 새로고침으로 출력 정리
    st.rerun()

# 입력이 없을 때 (처음 접속하거나 입력 대기 상태)
else:
    for message in st.session_state.messages:
        align = "flex-end" if message["role"] == "user" else "flex-start"
        css_class = "user-message" if message["role"] == "user" else "assistant-message"
        st.markdown(
            f"""
            <div class="chat-container" style="justify-content: {align};">
                <div class="{css_class}">{message['content']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
