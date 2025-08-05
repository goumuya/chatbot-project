import os
import json
import sqlite3
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
if "prev_compare_mode" not in st.session_state:
    st.session_state.prev_compare_mode = False
if "compare_input_cache" not in st.session_state:
    st.session_state.compare_input_cache = None

# 사이드바 UI
with st.sidebar:
    st.markdown("## 🤖 AI 성격 설정")
    st.selectbox(
        "현재 성격을 선택하세요", 
        list(personality_labels.keys()),
        index=list(personality_labels.keys()).index(st.session_state.selected_label),
        key="selected_label"
    )

    compare_mode = st.checkbox("📊 성격별 응답 비교 모드", value=False)

    # 비교모드 해제 감지 시 메시지 초기화
    if st.session_state.prev_compare_mode and not compare_mode:
       st.session_state.compare_input_cache = None

    st.session_state.prev_compare_mode = compare_mode

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

# 대화 기록 DB 저장
def save_message_to_db(role, content, label=None):
    conn = sqlite3.connect("chat_log.db")
    cursor = conn.cursor()

    # 테이블 생성
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS normal_logs (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user TEXT NOT NULL,
                   character TEXT NOT NULL,
                   assistant TEXT NOT NULL,
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS compare_logs (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user TEXT NOT NULL,
                   character TEXT NOT NULL,
                   assistant TEXT NOT NULL,
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    if role == "assistant":
        # 직전 user message와 assistant message 저장
        if len(st.session_state.messages) >= 2:
            user_msg = st.session_state.messages[-2]["content"]
            try:
                cursor.execute(
                    "INSERT INTO normal_logs (user, character, assistant) VALUES (?, ?, ?)",
                    (user_msg, st.session_state.selected_label, content)
                )
            except Exception as e:
                print("DB 저장 실패 : ", e)
    elif role == "compare":
        user_msg = st.session_state.get("compare_input_cache", "")
        try:
            for label, resp in content.items():
                cursor.execute(
                    "INSERT INTO compare_logs (user, character, assistant) VALUES (?, ?, ?)",
                    (user_msg, label, resp)
                )
        except Exception as e:
            print("비교모드 DB저장 실패 : ", e)

    conn.commit()
    conn.close()


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
    if compare_mode:
        # 비교 모드일 경우 세션 messages에 추가하지 않음
        st.session_state.compare_input_cache = user_input
    else:
        # 일반 모드일 경우에만 메시지를 세션에 추가
        st.session_state.messages.append({"role": "user", "content": user_input})

    # 지금까지의 메시지 출력
    if compare_mode:
        # 비교모드일 경우, 마지막 메시지만 출력
        if st.session_state.compare_input_cache:
            st.markdown(
                f"""
                <div class="chat-container" style="justify-content: flex-end;">
                    <div class="user-message">{st.session_state.compare_input_cache}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        # 일반 모드일 경우 전체 출력
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

     # 비교모드인 경우
    if compare_mode:
        st.session_state.compare_input_cache = user_input
        st.markdown("### 🤖 성격별 응답 비교")

        responses = {}

        for label, prompt_key in personality_labels.items():
            system_message = {"role": "system", "content": system_prompts[prompt_key]}
            messages = [system_message, {"role": "user", "content": user_input}]

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )

            reply = response.choices[0].message.content
            responses[label] = reply

            st.markdown(f"### 🧠 {label} 스타일")
            st.info(reply)
            
        
        # 기록 저장
        save_dialogue_to_file({
            "mode": "비교모드",
            "user": user_input,
            "response": responses
        })

        # 대화기록 다운로드
        compare_log_json = json.dumps({
            "mode": "비교모드",
            "user": user_input,
            "response": responses
        }, ensure_ascii=False, indent=2)

        # 다운로드버튼
        st.download_button(
            label="💾 비교모드 응답 다운로드",
            data=compare_log_json,
            file_name="compare_mode_log.json",
            mime="application/json"
        )

        # 비교 모드 대답 DB저장
        save_message_to_db("compare", responses)

        st.stop() # 비교모드에서는 이 후 코드 중단

    # GPT 응답 생성 (타이핑 효과 포함)
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

    # 타자치는 UI 표시
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

    # 최종 응답 표시 (커서 제거)
    placeholder.markdown(
        f"""
        <div class="chat-container" style="justify-content: flex-start;">
            <div class="assistant-message">{full_reply}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 응답 메시지 세션에 저장
    st.session_state.messages.append({"role": "assistant", "content": full_reply})
    # 대화 DB저장
    save_message_to_db("assistant", full_reply)

    # 대화기록 파일 저장
    save_dialogue_to_file({
        "user":user_input,
        "character": st.session_state.selected_label,
        "assistant": full_reply
    })

    # 새로고침으로 출력 정리
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

# 대화 로그 다운로드
chat_log_json = json.dumps(st.session_state.messages, ensure_ascii=False, indent=2)

st.download_button(
    label="💾 대화 로그 다운로드",
    data=chat_log_json,
    file_name="chat_log.json",
    mime="application/json"
)