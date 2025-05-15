import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
from openai import OpenAI
import av, numpy as np, tempfile, soundfile as sf
import queue

client = OpenAI(api_key=st.secrets["OPENAI_PAID_API_KEY"])

# 오디오 프로세서 클래스
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.volume = 0
        self.recording = False  # 내부 상태 직접 유지

    def recv_queued(self, frames):
        if self.recording:
            for frame in frames:
                audio = frame.to_ndarray().flatten().astype(np.int16)
                self.audio_queue.put(audio)
                max_vol = np.max(np.abs(audio))
                self.volume = int(np.linalg.norm(audio) / len(audio) * 10)
                print(f"🎧 프레임 수신됨 - 길이: {len(audio)}, 최대 볼륨: {max_vol}")
        return frames[-1]

# Streamlit UI 시작
st.title("🎙️ 실시간 음성 입력 → 텍스트 변환 (최종버전)")

# WebRTC 시작
ctx = webrtc_streamer(
    key="speech-final",
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
)

# 버튼 UI
if ctx.audio_processor is not None and ctx.state.playing:
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🟢 녹음 시작"):
            ctx.audio_processor.audio_queue = queue.Queue()  # 큐 초기화
            ctx.audio_processor.recording = True
            st.success("녹음 시작됨")

    with col2:
        if st.button("⏹ 녹음 종료 및 변환"):
            ctx.audio_processor.recording = False
            frames = []

            q = ctx.audio_processor.audio_queue
            while not q.empty():
                frames.append(q.get())

            st.write(f"🧪 프레임 수: {len(frames)}")

            if frames:
                audio_data = np.concatenate(frames)
                audio_duration = len(audio_data) / 48000
                max_volume = np.max(np.abs(audio_data))

                st.markdown("### 📊 오디오 수치 정보")
                st.write({
                    "길이": len(audio_data),
                    "샘플링 레이트": 48000,
                    "총 지속시간 (초)": round(audio_duration, 3),
                    "최대값": int(np.max(audio_data)),
                    "최소값": int(np.min(audio_data)),
                    "평균값": round(float(np.mean(audio_data)), 2),
                    "표준편차": round(float(np.std(audio_data)), 2)
                })

                if max_volume < 300:
                    st.warning("⚠️ 감지된 음성이 없습니다.")
                elif audio_duration < 0.5:
                    st.warning("⚠️ 음성 길이가 너무 짧습니다.")
                else:
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
                        sf.write(tmpfile.name, audio_data, 48000)
                        with open(tmpfile.name, "rb") as f:
                            try:
                                transcript = client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=f,
                                    language="ko"
                                )
                                st.success("🗣️ 결과:")
                                st.write(transcript.text)
                            except Exception as e:
                                st.error(f"❌ 변환 실패: {e}")
            else:
                st.warning("⚠️ 프레임이 없습니다. 먼저 말을 해보세요.")

    # 실시간 볼륨 시각화
    level = ctx.audio_processor.volume
    bar = "🔊" * level + "▫️" * (10 - level)
    st.markdown(f"**실시간 볼륨:** {bar} (수치: {level})")
else:
    st.info("🎙️ 마이크 연결 대기 중입니다...")
