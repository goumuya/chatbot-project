from google.cloud import language_v1

# 클라이언트 객체 생성
client = language_v1.LanguageServiceClient()

# 테스트할 문장
text = "이 서비스 정말 마음에 들어요!"

# 문서 정의
document = language_v1.Document(
    content=text,
    type_=language_v1.Document.Type.PLAIN_TEXT,
    language="ko"
)

# 감정 분석 요청
response = client.analyze_sentiment(request={"document": document})

# 결과 출력
sentiment = response.document_sentiment
print(f"감정 점수: {sentiment.score:.2f}, 감정 확신도: {sentiment.magnitude:.2f}")