import streamlit as st
import json
import os
from collections import Counter
import pandas as pd

st.set_page_config(page_title="📊 대화 로그 분석", page_icon="📊")
st.title("📊 대화 로그 분석 도구")

# 로그 파일 경로
LOG_FILE = "chat_log.json"

# 로그 파일 존재 여부 확인
if not os.path.exists(LOG_FILE):
    st.warning("❗ chat_log.json 파일이 존재하지 않습니다.")
    st.stop()

# 로그 파일 로딩
with open(LOG_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)


if isinstance(data, list):
    # 일반 메시지: user, assistant 키 모두 존재하는 항목이 하나라도 있으면 분석
    if any("user" in m and "assistant" in m for m in data):
        st.subheader("🗣️ 일반 대화 로그 분석")

        user_msgs = [m["user"] for m in data if "user" in m and "assistant" in m]
        assistant_msgs = [m["assistant"] for m in data if "user" in m and "assistant" in m]

        st.markdown(f"- 👤 사용자 메시지 수: **{len(user_msgs)}**")
        st.markdown(f"- 🤖 챗봇 응답 수: **{len(assistant_msgs)}**")

        all_text = " ".join(user_msgs)
        word_counts = Counter(all_text.split())
        top_words = word_counts.most_common(10)

        st.subheader("📌 사용자 메시지 Top 10 단어")
        st.dataframe(pd.DataFrame(top_words, columns=["단어", "빈도수"]))

    # 비교모드 메시지: mode, user, response 키가 모두 있는 항목이 하나라도 있으면 분석
    if any("mode" in m and "user" in m and "response" in m for m in data):
        st.subheader("📊 비교 모드 로그 분석")

        compare_logs = [m for m in data if m.get("mode") == "비교모드"]
        st.markdown(f"총 비교모드 기록 수: **{len(compare_logs)}**")

        label_counter = Counter()
        for entry in compare_logs:
            for label in entry["response"]:
                label_counter[label] += 1

        st.subheader("🧠 성격별 응답 수")
        st.bar_chart(pd.DataFrame.from_dict(label_counter, orient="index", columns=["응답 수"]))
else:
    st.warning("❗ 지원되지 않는 로그 형식입니다.")