import os
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일 불러오기
load_dotenv()

# 클라이언트 객체 생성
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# 대화 기록 저장
messages = []

print("🤖 챗봇을 시작합니다! (종료하려면 'exit' 입력하세요.)")

while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        print("챗봇을 종료합니다. 👋")
        break

    # 유저 메시지 추가
    messages.append({"role": "user", "content": user_input})

    # 새로운 방식: client.chat.completions.create
    response = client.chat.completions.create(
        model="gpt-4o",   # 또는 "gpt-3.5-turbo"
        messages=messages
    )

    reply = response.choices[0].message.content
    print(f"Bot: {reply}")

    # 챗봇 응답 추가
    messages.append({"role": "assistant", "content": reply})
