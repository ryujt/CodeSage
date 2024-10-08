
# Code Sage

Code Sage는 OpenAI 또는 Claude API를 활용하여 프로젝트 코드베이스에 대한 질문에 답변하는 AI 기반 도구입니다. 이 도구는 개발자들이 프로젝트의 구조와 기능을 빠르게 이해하고, 코드 관련 질문에 대한 답변을 얻는 데 도움을 줍니다.

## 주요 기능

- 프로젝트 파일의 임베딩 생성 및 관리
- 사용자 질문에 대한 관련 코드 검색
- OpenAI GPT 또는 Claude 모델을 사용한 지능형 응답 생성
- 코드 구문 강조 및 다이어그램 렌더링 지원
- PDF 문서의 텍스트 검색
- Analyze from main branch: main 브랜치부터 현재 커밋된 내용까지의 변화에 대한 분석
- Analyze Recent Commit: 가장 최근 커밋의 변화에 대한 분석

## 설치 및 사용 방법

### 1. 수동 설치 방법

1. 이 저장소를 클론하거나 다운받습니다:
   ```
   git clone https://github.com/your-repo/CodeSage.git
   cd CodeSage
   ```

2. 다운받은 모든 파일을 분석 대상이 되는 폴더로 복사합니다.
   * 복사한 파일이 있는 폴더와 그 하위 폴더의 모든 파일을 검색합니다.
   * 설정에서 참조할 파일의 확장자를 지정할 수 있습니다.

3. 필요한 패키지를 설치합니다:
   ```
   pip install -r requirements.txt
   ```

4. 애플리케이션을 실행합니다:
   ```
   python CodeSage.py
   ```

5. 웹 브라우저에서 `http://localhost:8080`에 접속합니다.

6. 설정 버튼을 클릭하시고 OpenAI API 키를 입력합니다.
   * 기타 설정을 확인 후 `Save Settings` 버튼을 클릭합니다.

7. 폴더 버튼을 클릭하고 분석하고자 하는 전체 경로를 입력하여 추가합니다.
   * 입력된 경로 중에 사용할 경로의 체크박스를 선택해야 합니다.
   * 경로는 여러 개를 동시에 선택할 수 있습니다.

8. "Refresh Embeddings" 버튼을 클릭하여 프로젝트 파일의 임베딩을 생성합니다.
   * 참조 대상이 되는 모든 파일을 찾아서 벡터로 변환하여 AI가 이해할 수 있도록 준비합니다.
   * 이미 처리된 파일은 중복 처리하지 않습니다. 버튼을 주기적으로 눌러 최신 상태를 유지하세요.

9. 질문을 입력하고 제출하여 AI의 답변을 받습니다.

10. "Analyze from main branch" 또는 "Analyze Recent Commit" 버튼을 사용하여 코드 변경사항을 분석할 수 있습니다.
    * 코드 변경사항 분석은 하나의 폴더만 지정할 수 있습니다.

### 2. Docker를 이용한 설치 방법

Docker를 사용하면 Code Sage를 간단하게 배포하고 실행할 수 있습니다. 아래 단계에 따라 도커를 사용하여 애플리케이션을 실행할 수 있습니다.

1. 이 저장소를 클론하거나 다운받습니다:
   ```
   git clone https://github.com/your-repo/CodeSage.git
   cd CodeSage
   ```

2. 프로젝트 루트 디렉토리에 있는 `Dockerfile`을 사용하여 도커 이미지를 빌드합니다:
   ```
   docker build -t codesage:latest .
   ```

3. 도커 컨테이너를 실행합니다:
   ```
   docker run -d -p 8080:8080 --name codesage_container codesage:latest
   ```

   이 명령어는 Code Sage를 백그라운드에서 실행하며, 로컬 머신의 8080 포트를 컨테이너의 8080 포트에 매핑합니다.

4. 웹 브라우저에서 `http://localhost:8080`에 접속합니다.

5. 설정 버튼을 클릭하시고 OpenAI API 키를 입력합니다.
   * 기타 설정을 확인 후 `Save Settings` 버튼을 클릭합니다.

6. 나머지 설정 및 사용 방법은 수동 설치 방법과 동일합니다.

## 설정 변경

- 설정 페이지(`http://localhost:8080/settings`)에서 다음 항목을 수정할 수 있습니다:
  - OpenAI API 키
  - Claude API 키 (선택사항)
  - 처리할 파일 확장자
  - 무시할 폴더 및 파일
  - 필수 파일

## 주요 컴포넌트

- `CodeSage.py`: 메인 애플리케이션 파일
- `SageLibs/`: 핵심 기능을 포함하는 라이브러리 폴더
  - `config.py`: 설정 관리
  - `web_requests.py`: API 요청 처리
  - `utilities.py`: 유틸리티 함수
  - `questions.py`: 질문 처리 및 저장
- `SageTemplate/`: HTML 템플릿 파일
- `SageSettings.json`: 사용자 설정 파일
- `embeddings.jsonl`: 생성된 임베딩 저장 파일
- `question_history.json`: 질문 기록 저장 파일

## 개발자 가이드

Code Sage의 기능을 확장하거나 수정하려면 다음 파일을 참조하세요:

- 새로운 API 엔드포인트 추가: `CodeSage.py`
- 임베딩 생성 로직 수정: `utilities.py`의 `get_embedding` 함수
- 질문 처리 로직 변경: `questions.py`
- AI 모델 응답 처리 수정: `web_requests.py`의 `get_chat_response` 함수

## 지원되는 파일 형식

Code Sage는 `SageSettings.json`에 지정된 파일 확장자를 지원합니다. 기본적으로 다음과 같은 확장자를 포함합니다:
.md, .vue, .js, .json, .css, .html, .py, .java, .ts, .jsx, .tsx, .php, .c, .cpp, .h, .cs, .swift, .rb, .go, .kt, .sql, .hpp, .m, .mm
