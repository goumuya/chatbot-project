from openai import OpenAI
import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import av, numpy as np, tempfile, soundfile as sf

client = OpenAI(api_key=st.secrets["OPENAI_PAID_API_KEY"])

class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.recorded_frames = []

    def recv(self, frame: av.AudioFrame):
        audio = frame.to_ndarray().flatten().astype(np.int16)
        self.recorded_frames.append(audio)
        return frame

st.title("🎙️ 실시간 마이크 입력 → 텍스트")

ctx = webrtc_streamer(
    key="speech",
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
)

if ctx.audio_processor and st.button("📝 텍스트로 변환"):
    audio_data = np.concatenate(ctx.audio_processor.recorded_frames)

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
