from openai import OpenAI
import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import av, numpy as np, tempfile, soundfile as sf

client = OpenAI(api_key=st.secrets["OPENAI_PAID_API_KEY"])

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

st.title("🎙️ 실시간 마이크 입력 → 텍스트")

ctx = webrtc_streamer(
    key="speech",
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
)

# 실시간 볼륨 시각화
if ctx.audio_processor:
    level = ctx.audio_processor.volume
    bar = "🔊" * level + "▫️" * (10 - level)
    st.markdown(f"**소리 입력 상태:** {bar}")

# 텍스트로 변환 버튼
if ctx.audio_processor and st.button("📝 텍스트로 변환"):
    if ctx.audio_processor.recorded_frames:
        audio_data = np.concatenate(ctx.audio_processor.recorded_frames)
        audio_duration = len(audio_data) / 48000  # 초 단위

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
                    st.success("🗣️ 결과:")
                    st.write(transcript.text)
    else:
        st.warning("⚠️ 아직 음성이 입력되지 않았습니다. 말을 하고 나서 다시 눌러주세요.")