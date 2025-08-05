import sqlite3
import json

# JSON 파일 열기
with open("chat_log.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# DB 연결
conn = sqlite3.connect("chat_log.db")
cur = conn.cursor()

# 테이블 생성
cur.execute("""
CREATE TABLE IF NOT EXISTS normal_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            assistant TEXT NOT NULL
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS compare_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            label TEXT NOT NULL,
            response TEXT NOT NULL
)
""")

# 데이터 삽입
for entry in data:
    if "mode" in entry and entry["mode"] == "비교모드":
        for label, resp in entry["response"].items():
            cur.execute("INSERT INTO compare_logs (user, label, response) VALUES (?, ?, ?)",
                        (entry["user"], label, resp)
                        )
    elif "user" in entry and "assistant" in entry:
        cur.execute(
            "INSERT INTO normal_logs (user, assistant) VALUES (?, ?)",
            (entry["user"], entry["assistant"])
        )

conn.commit()
conn.close()
print("SQLITE DB에 저장완료")