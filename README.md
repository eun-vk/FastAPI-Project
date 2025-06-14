# 🧠상담일지 기반 GPT 상담 도우미 서비스

## ➡️ 프로젝트 목적
- 현재까지 학습한 Python, CSS, HTML, JavaScript, FastAPI, 그리고 인공지능(AI) 기술을 활용하여, ChatGPT와 연동되는 채팅 서비스를 개발하는 것이 최종 목표입니다.

## ➡️ 프로젝트 설명  
이 웹 서비스는 사회복지사가 상담 내용을 더욱 효율적으로 기록할 수 있도록 돕고, ChatGPT를 활용하여 전문적인 조언과 분석을 제공함으로써 상담 일지의 질을 크게 향상시키는 웹 서비스입니다.

---

## 📌 1. 기획 및 설계

### 📍 사용자 인증 및 GPT 연동 기능 

⚙️ **사용자 인증 API 기능**

- **회원가입**: 새로운 사용자 계정을 만듭니다 (사용자명, 이메일, 비밀번호 사용).
- **로그인**: 등록된 사용자가 로그인하며, 성공 시 세션 쿠키를 발급해 인증 상태를 유지합니다.
- **사용자 확인**: 세션 쿠키로 현재 로그인된 사용자 정보를 조회하여 인증 상태를 확인합니다.
- **로그아웃**: 현재 세션을 안전하게 종료하고 세션 쿠키를 제거합니다.


  
⚙️ **상담일지 & GPT 연동 기능**  

- **상담일지 등록**: GPT 대화 내용을 상담 일지 형태로 저장하고 관리합니다.
- **GPT와 대화**: 사용자의 질문을 GPT 프록시 서비스로 전달하고 답변을 받습니다. 이전 대화 내용을 컨텍스트로 활용해 자연스러운 상담을 지원합니다.
- **GPT 대화 내용 조회**: 사용자별 채팅 세션 및 각 세션의 대화 내용을 조회합니다.
- **대화 내용 삭제**: 불필요한 특정 대화 메시지를 개별적으로 삭제합니다.

---

## 📌2. 개발환경 
### 📍 개발환경  
- HTML, CSS, JavaScript
- 서비스 배포 환경 : GitHub Page

### 📍 배포 URL
- http://127.0.0.1:8000/login
  
| App      | URL             | HTML File Name     | Note                |
|----------|------------------|---------------------|---------------------|
| auth     | /login           | login.html          | 로그인 화면         |
| auth     | /register        | register.html       | 회원가입 화면       |
| main     | /                | main.html           | 메인 화면           |
| journals | /journals-page   | journals_page.html  | 상담 일지 조회 화면 |

---

## 📌UI/UX 구조 계획  
📁 project_root  
├── 📄 main.py  
├── 📄 models.py  
├── 📄 auth.py  
├── 📁 templates  
│   ├── 📄 index.html  
│   ├── 📄 login.html  
│   └── 📄 register.html  
├── 📁 static  
│   ├── 📄 styles.css  
│   └── 📄 script.js  
└── 📄 .env  


---

## 📌 개발 일정(WBS)
![스크린샷 2025-06-13 030014](https://github.com/user-attachments/assets/052dc0bc-d0c0-4c60-9756-f413d88386c2)


---

## 📌 와이어프레임 / UI

### 📍 와이어프레임
![와이어프레임](https://github.com/user-attachments/assets/45b74c1f-7968-4dd4-9f3d-5e956ed2dd01)


---

### 📍 화면 설계
- 메인 화면
![메인화면](https://github.com/user-attachments/assets/6a79d0c3-0344-4a91-804a-8ffe4de10074)


---

## 📌 프로젝트 느낀점
⚙️ **좋았던 점**
- 이론만 배울 때와 달리 실제 동작하는 애플리케이션을 만들어보니 각 기술의 역할과 연결점을 조금이나마 이해할 수 있었고, 서버 구동부터 화면 구성, API 구현까지 전체 개발 플로우를 경험하면서 웹 개발의 큰 그림을 그릴 수 있었습니다. AI 도움을 받아 복잡한 부분들을 완성할 수 있었습니다.
- 
⚙️ **아쉬웠던 점**
- 완전한 이해 없이 개발을 시작해서 많은 시행착오가 발생했고, 문제 발견 능력이 부족해 AI에게 과도하게 의존하여 코드를 재작성하는 일이 반복되었습니다.
- 처음에 생각했던 것은 ai와의 대화 후 일지에 그 내용을 요약해서 일지를 등록하는 서비스였는데 하다보니 기존의 의도와 다르게 흘러갔던 것이 아쉬웠습니다. 
  


