# 2026-10-01 · 26라운드 · 스토리 → 시스템·UI 반영 범위와 교차 참조

### Q1. 교차 참조 범위
- 결정: **text-pack.md 와 층 표만, 프로듀서가 텍스트 계약으로 정리.** `contracts/story-text.md` 에 층·제국·보스 이름 표와 텍스트 키 목록을 두고, 시스템은 그 계약대로 `data/story.json` 을 만든다. UI 는 계약의 키·이벤트만 사용. 바이블은 참조 금지.

### Q2. 이번 반영 범위 (복수 선택)
- **8층 구조 + 층·보스 이름**, **텍스트 팩 연결**, **일기장 이름 입력**. 엔딩 분기 2종은 이번 범위 밖(별도 인터뷰).

## 승인 기록
- cross-references.md #3: 시스템 → 스토리 (`contracts/story-text.md` 만)
- cross-references.md #4: UI → 시스템 (계약 `ui-system-interface.md` 의 STORY 이벤트·`playerName`·층 이름 추가분)
