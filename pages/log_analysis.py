import streamlit as st
import sqlite3
from collections import Counter, defaultdict
import pandas as pd
import numpy as np
import json
from google.cloud import language_v1
from google.oauth2 import service_account
import os

st.set_page_config(page_title="📊 대화 로그 분석", page_icon="📊")
st.title("📊 대화 로그 분석 도구")

DB_FILE = os.path.join(os.getcwd(), "chat_log.db")
# 서비스 계정 키 가져오기
credentials_info = st.secrets["google_service_account"]
credentials = service_account.Credentials.from_service_account_info(credentials_info)
client = language_v1.LanguageServiceClient(credentials=credentials)

# DB 존재 확인
try:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
except Exception as e:
    st.error(f"❌ 데이터베이스 연결 실패: {e}")
    st.stop()


# 일반대화 테이블 존재 확인
cursor.execute("""
    SELECT name FROM sqlite_master WHERE type='table' AND name='normal_logs'
""")
if not cursor.fetchone():
    st.warning("❗ 'normal_logs' 테이블이 존재하지 않습니다.")
    st.stop()

# 데이터 로딩
df = pd.read_sql_query("SELECT * FROM normal_logs", conn)

if df.empty:
    st.warning("❗ 분석할 대화 로그가 없습니다.")
    st.stop()

# 구글 감정분석 API 사용
emotion_scores = defaultdict(list)

for _, row in df.iterrows():
    text = row["assistant"]
    character = row["character"]
    if not isinstance(text, str) or not text.strip():
        continue
    document = language_v1.Document(
        content=text,
        type_=language_v1.Document.Type.PLAIN_TEXT,
        language="ko"
    )
    try:
        response = client.analyze_sentiment(request={"document": document})
        sentiment = response.document_sentiment
        emotion_scores[character].append({
            "score": sentiment.score,
            "magnitude": sentiment.magnitude
        })
    except Exception as e:
        continue


# 기본 통계
st.subheader("🗣️ 일반 대화 로그 분석")
st.markdown(f"- 👤 사용자 메시지 수: **{len(df)}**")
st.markdown(f"- 🤖 챗봇 응답 수: **{len(df)}**")

# 1. 성격별 평균 답변 길이
st.subheader("1️⃣ 성격별 평균 답변 길이")
df["assistant_length"] = df["assistant"].str.len()
avg_length = df.groupby("character")["assistant_length"].mean().sort_values(ascending=False)
st.bar_chart(avg_length)

# 2. 성격별 자주 사용하는 단어 Top 10
st.subheader("2️⃣ 성격별 자주 사용하는 단어 Top 10")
for char in df["character"].unique():
    st.markdown(f"**🧠 {char}**")
    words = " ".join(df[df["character"] == char]["assistant"]).split()
    word_counts = Counter(words)
    top_words = pd.DataFrame(word_counts.most_common(10), columns=["단어", "빈도수"])
    st.dataframe(top_words)

# 3. 감정 점수 분석 (구글 클라우드 API 기반)
st.subheader("3⃣️ 성격별 감정 점수 평균 (Google Cloud NLP)")
result_data = []
for char, scores in emotion_scores.items():
    if not scores:
        continue
    avg_score = sum(s["score"] for s in scores) / len(scores)
    avg_magnitude = sum(s["magnitude"] for s in scores) / len(scores)
    result_data.append({
        "성격" : char,
        "평균 감정 점수" : round(avg_score, 3),
        "감정 강도" : round(avg_magnitude, 3),
        "대화 수" : len(scores) 
    })

result_df = pd.DataFrame(result_data).sort_values(by="평균 감정 점수", ascending=False)
st.dataframe(result_df.set_index("성격"))
st.bar_chart(result_df.set_index("성격")[["평균 감정 점수"]])

# 4. 시간대 분포
st.subheader("4️⃣ 성격별 응답 시간대 분포")
df["created_at"] = pd.to_datetime(df["created_at"])
df["hour"] = df["created_at"].dt.hour
hourly_dist = df.groupby(["character", "hour"]).size().unstack(fill_value=0)
st.line_chart(hourly_dist.T)

# 5. 사용자 메시지 길이와 응답 길이 상관관계
st.subheader("5️⃣ 사용자 메시지 길이와 응답 길이 상관관계")
df["user_length"] = df["user"].str.len()
st.scatter_chart(df[["user_length", "assistant_length"]])

# 6. 감탄사 사용 빈도 분석
st.subheader("6️⃣ 성격별 감탄사 사용 빈도")
exclamations = ["헉", "와", "우와", "대박", "어머", "오!", "우앗", "꺄", "헐"]
def count_exclamations(text):
    return sum(text.count(e) for e in exclamations)
df["exclam_count"] = df["assistant"].apply(count_exclamations)
exc_counts = df.groupby("character")["exclam_count"].sum().sort_values(ascending=False)
st.bar_chart(exc_counts)

# 추가: 기존에 있던 사용자 메시지 Top 10 단어도 같이 출력
st.subheader("📌 사용자 메시지 Top 10 단어")
user_text = " ".join(df["user"].tolist())
word_counts = Counter(user_text.split())
top_words = word_counts.most_common(10)
st.dataframe(pd.DataFrame(top_words, columns=["단어", "빈도수"]))

# 성격별 대화 수
st.subheader("🧠 성격별 대화 수")
char_count = df["character"].value_counts().rename_axis("성격").reset_index(name="대화 수")
st.bar_chart(char_count.set_index("성격"))

conn.close()