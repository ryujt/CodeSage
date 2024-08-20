# Python 3.9 이미지를 사용
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 패키지 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY . .

# 8080 포트 노출
EXPOSE 8080

# 애플리케이션 실행 명령
CMD ["python", "CodeSage.py"]
