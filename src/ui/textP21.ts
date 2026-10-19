/**
 * P21 어두운 톤 · 잔혹 전투 UI 문구 (contracts/dark-brutal §1·§10). 기본값 = 스토리 66 팩(`parts/story/text-pack-66-dark.json`)의
 * `goreNotice`·`goreSetting`·`title.pressPrompt`·`reactPops.streak` 문구. 텍스트 팩 `hud.<키>` 가 있으면 그 문구가 앞선다
 * (`text.ts` 의 `p21Text`). 문구는 이 파일 한곳에만 둔다.
 */
export const P21_TEXT = {
  // ---- 첫 실행 잔혹 묘사 안내 (한 번) — 66 goreNotice
  goreNoticeTitle: '잔혹한 장면이 있다',
  goreNoticeBody:
    '이 일기장에는 피와 잘린 몸, 불에 탄 시체가 적혀 있다.\n싸움은 실제처럼 아프고, 그 흔적은 오래 남는다.\n견디기 힘들면 줄이거나 끌 수 있다. 설정에서 언제든 다시 바꾼다.',
  goreNoticeFull: '그대로 본다',
  goreNoticeReduced: '줄인다',
  goreNoticeOff: '끈다',
  /** UI 안내 (팩에 없음) */
  goreNoticeHint: '←→ 고르기 · Enter 고른다',
  // ---- 잔혹 묘사 설정 (설정 화면 '화면' 탭) — 66 goreSetting
  gore: '잔혹 묘사',
  goreFull: '전체',
  goreReduced: '줄임',
  goreOff: '끔',
  goreFullDesc: '베인 곳은 갈라지고 잘린 것은 떨어진다. 피와 시체는 그곳을 떠날 때까지 남는다.',
  goreReducedDesc: '몸이 잘리지 않는다. 피는 적고 어둡게 남는다.',
  goreOffDesc: '피 대신 먹과 재가 흩어진다. 바닥에 자국이 남지 않는다.',
  // ---- 타이틀 — 66 title.pressPrompt
  pressPrompt: '아무 키나 누르면 일어난다',
  // ---- 연속 처치 단계 낱말 — 66 reactPops.streak (2 · 4 · 7 부터)
  streak2: '고인다',
  streak4: '차오른다',
  streak7: '넘친다',
} as const;
export type P21TextKey = keyof typeof P21_TEXT;
