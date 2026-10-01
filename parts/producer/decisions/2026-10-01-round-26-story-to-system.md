# 2026-10-01 · 26라운드 · 스토리 → 시스템·UI 반영 범위와 교차 참조

### Q1. 교차 참조 범위
- 결정: **text-pack.md 와 층 표만, 프로듀서가 텍스트 계약으로 정리.** `contracts/story-text.md` 에 층·제국·보스 이름 표와 텍스트 키 목록을 두고, 시스템은 그 계약대로 `data/story.json` 을 만든다. UI 는 계약의 키·이벤트만 사용. 바이블은 참조 금지.

### Q2. 이번 반영 범위 (복수 선택)
- **8층 구조 + 층·보스 이름**, **텍스트 팩 연결**, **일기장 이름 입력**. 엔딩 분기 2종은 이번 범위 밖(별도 인터뷰).

## 승인 기록
- cross-references.md #3: 시스템 → 스토리 (`contracts/story-text.md` 만)
- cross-references.md #4: UI → 시스템 (계약 `ui-system-interface.md` 의 STORY 이벤트·`playerName`·층 이름 추가분)

## 시스템·UI 반영 기록 (26라운드 후속, 인터뷰 없이 둔 임시값 — 다음 인터뷰에서 확인)
- `data/story.json`: 계약 `contracts/story-text.json` 을 그대로 복사한 데이터. 시스템은 `src/systems/story.ts` 로 치환·조회만 한다.
- 8층 추가 (`data/stages.json` `stage8`): 적 HP 배율 3.2 / 공격 배율 2.5, 시련 3개, 보스 `emperor`(이전 `final` 과 동일 3페이즈, HP 800). 7층 보스는 새 변형 `stage7`(HP 640, 접촉 32, 부채꼴 11발). 이름은 모두 계약의 보스 이름.
- 일기장 이름: Setup 씬 메타 메뉴 → Enter → 이름 입력(DOM input, **최대 12자**, 빈 이름은 `―` 로 표시) → 3획. `?weapon=` 디버그 진입은 이름 없이 시작. 세이브 v4 에 `playerName` 저장.
- 자막 유지 시간: 공지 1.8초, 그 외 3.6초. 자막 위치는 보스 체력바 위.
- 결과 화면 첫 줄: 클리어 시 `endings.destroy`(엔딩 분기는 미구현이므로 임시로 '없앤다' 쪽 문장), 사망 시 `death` 치환.
- 레이아웃 수정: 캔버스 가운데 정렬을 flex 에서 Phaser autoCenter 로 바꿈 (DOM 입력란이 캔버스와 어긋나던 문제).
