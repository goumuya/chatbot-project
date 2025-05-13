import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import numpy as np
import tempfile
import soundfile as sf
import av

# .env 파일에서 API 키 로드
load_dotenv()

client = OpenAI(
    api_key=st.secrets["OPENAI_PAID_API_KEY"]
)

# 마이크 처리 클래스
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.recorded_frames = []
        self.volume = 0

    def recv_queued(self, frames):
        for frame in frames:
            audio = frame.to_ndarray().flatten().astype(np.int16)
            self.recorded_frames.append(audio)
            self.volume = int(np.linalg.norm(audio) / len(audio) * 10)
        return frames[-1]

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
if "mic_on" not in st.session_state:
    st.session_state.mic_on = False

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

# 🎤 마이크 on/off 토글 및 표시
st.markdown("## 🎤 마이크 입력")
st.session_state.mic_on = st.toggle("🎙 마이크 켜기 / 끄기", value=st.session_state.mic_on)

user_input = None

if st.session_state.mic_on:
    st.success("🔴 마이크가 켜졌습니다. 말을 시작하세요.")
    ctx = webrtc_streamer(
        key="speech",
        audio_processor_factory=AudioProcessor,
        media_stream_constraints={"audio": True, "video": False},
        async_processing=True,
    )

    if ctx.audio_processor:
        level = ctx.audio_processor.volume
        bar = "🔊" * level + "▫️" * (10 - level)
        st.markdown(f"**소리 입력 상태:** {bar}")

        if st.button("📝 말한 내용으로 질문하기"):
            if ctx.audio_processor.recorded_frames:
                audio_data = np.concatenate(ctx.audio_processor.recorded_frames)
                audio_duration = len(audio_data) / 48000

                if audio_duration < 0.1:
                    st.warning("⚠️ 음성 길이가 너무 짧습니다. 좀 더 길게 말해보세요.")
                else:
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
                        sf.write(tmpfile.name, audio_data, 48000)

                        with open(tmpfile.name, "rb") as f:
                            transcript = client.audio.transcriptions.create(
                                model="whisper-1",
                                file=f,
                                language="ko"
                            )
                            user_input = transcript.text
                            st.chat_message("user").markdown(user_input)
                            st.session_state.messages.append({"role": "user", "content": user_input})
            else:
                st.warning("⚠️ 아직 음성이 입력되지 않았습니다. 말을 하고 나서 다시 눌러주세요.")
else:
    ctx = None

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