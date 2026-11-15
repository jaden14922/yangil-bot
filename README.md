# 양일고 안내 챗봇

양일고등학교 급식, 시간표, 학교생활 정보를 물어보는 웹사이트예요.
급식·시간표는 나이스 교육정보 개방 포털에서 매일 새벽 자동으로 받아와요.

## 파일 구성

- `index.html` — 챗봇 화면
- `faq.json` — 학교생활 질문과 답 (여기만 고치면 답변이 바뀌어요)
- `scripts/update.py` — 나이스에서 급식·시간표를 받아오는 코드
- `.github/workflows/update.yml` — 매일 자동 실행 설정

## 처음 설정 (한 번만)

1. 저장소 **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `NEIS_KEY`
   - Secret: 나이스 인증키
2. 저장소 **Settings → Pages → Source**를 **GitHub Actions**로 선택
3. **Actions** 탭 → 왼쪽 "급식·시간표 업데이트" → **Run workflow**

## 학교 정보 추가하기

`faq.json`을 열고 연필(편집) 버튼을 누른 뒤, 아래 형식으로 한 덩어리를 추가하고 **Commit changes**를 누르세요.
몇 분 뒤 사이트에 반영돼요.

```json
  {
    "keys": ["도서관"],
    "answer": "도서관은 평일 오후 6시까지 운영해요."
  }
```

덩어리 사이에는 쉼표(,)가 있어야 하고, 마지막 덩어리 뒤에는 쉼표가 없어야 해요.

## 주의

- 인증키는 절대 파일에 직접 쓰지 말고 Secrets에만 넣으세요.
- 저장소에 60일 동안 아무 변경이 없으면 GitHub이 자동 실행을 멈춰요. 그럴 땐 Actions 탭에서 다시 켜면 돼요.
