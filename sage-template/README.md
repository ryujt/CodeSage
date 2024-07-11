# Code Sage

Code Sage는 OpenAI의 API를 활용하여 프로젝트 코드베이스에 대한 질문에 답변하는 AI 기반 도구입니다. 
이 도구는 개발자들이 프로젝트의 구조와 기능을 빠르게 이해하고, 코드 관련 질문에 대한 답변을 얻는 데 도움을 줍니다.

## 주요 기능

- 프로젝트 파일의 임베딩 생성 및 관리
- 사용자 질문에 대한 관련 코드 검색
- OpenAI GPT 모델을 사용한 지능형 응답 생성
- 코드 구문 강조 및 다이어그램 렌더링 지원
- PDF 문서의 텍스트 검색

## 설치 방법

1. 이 저장소를 클론하거나 다운받습니다:
   ```
   git clone https://github.com/your-username/code-sage.git
   cd code-sage
   ```

2. 다운받은 모든 파일을 분석 대상이 되는 폴더로 복사합니다.
   * 복사한 파일이 있는 폴더와 그 밑에 있는 모든 폴더의 파일을 검핵하게 됩니다.
   * 설정에 의해서 참조되는 파일의 확장자를 결정할 수 있습니다.
   * 설정 초기 값들을 확인하세요.

3. 필요한 패키지를 설치합니다:
   ```
   pip install -r requirements.txt
   ```
   or
   ```
   pip3 install -r requirements.txt
   ```

4. OpenAI API 키를 설정합니다:
   - `sage-settings.json` 파일을 열고 your_openai_api_key 대신 OpenAI의 API 키를 입력합니다:
     ```json
     {
       "api_key": "your_openai_api_key",
       "extensions": ".md, .js, .html, .css, .json, .py, .java, .ts, .jsx, .tsx, .php, .c, .cpp, .h, .cs, .swift, .rb, .go, .vue, .kt, .sql, .hpp, .m, .mm",
       "ignore_folders": "sage-template, node_modules, cypress, .gradle, .idea, build, test, bin, dist, .vscode, .git, .github, .expo",
       "ignore_files": "CodeSage.py, CodeSage-Claude.py, sage-settings.json, package-lock.json",
       "essential_files": "README.md, package.json, src/router/index.js"
     }
     ```

## 사용 방법

1. 애플리케이션을 실행합니다:
   ```
   python CodeSage.py
   ```
   or
   ```
   python3 CodeSage.py
   ```

2. 웹 브라우저에서 `http://localhost:8080`에 접속합니다.

3. "Refresh Embeddings" 버튼을 클릭하여 프로젝트 파일의 임베딩을 생성합니다.
   * 참조 대상이 되는 모든 파일을 찾아서 벡터로 변환하여 인공지능이 이해할 수 있도록 준비합니다.
   * 이미 한 번 처리한 파일은 중복처리하지 않고 무시합니다. 버튼을 자주 눌러서 최신 상태를 유지하세요.

4. 질문을 입력하고 제출하여 AI의 답변을 받습니다.

## 설정 변경

- 설정 페이지(`http://localhost:8080/settings`)에서 다음 항목을 수정할 수 있습니다:
  - API 키
  - 처리할 파일 확장자
  - 무시할 폴더 및 파일
  - 필수 파일

### 지원되는 파일 형식

Code Sage는 다음과 같은 파일 확장자를 지원합니다:
.md, .js, .html, .css, .json, .py, .java, .ts, .jsx, .tsx, .php, .c, .cpp, .h, .cs, .swift, .rb, .go, .vue, .kt, .sql, .hpp, .m, .mm

### 무시되는 폴더 및 파일

기본적으로 다음 폴더와 파일은 처리에서 제외됩니다:

- 폴더: sage-template, node_modules, cypress, .gradle, .idea, build, test, bin, dist, .vscode, .git, .github, .expo
- 파일: CodeSage.py, CodeSage-Claude.py, sage-settings.json, package-lock.json

### 필수 파일

다음 파일들은 항상 처리됩니다:
README.md, package.json, src/router/index.js

## 스크린샷

### 홈 화면

![](./pic-01.png)

### 답변 화면

![](./pic-02.png)

### Mermaid 다이어그램 지원

![](./pic-03.png)
