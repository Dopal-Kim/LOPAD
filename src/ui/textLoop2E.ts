/**
 * 62 루프 2 UI E 문구 (시스템 C 계약 2차 패스 — 유품 카드 · 결산 · 기억 장 · 운명 공개 뒤 고르기 · 출구 화살표).
 * 화면 글 대부분은 시스템이 스토리 63 팩에서 채워 내려 준다(계약 `UiRelic`·`UiRunSummary`·`UiFloorEnd`·`UiMemoryBook`).
 * 여기 둔 것은 계약에 칸이 없는 버튼·안내·대체 글뿐 — 문장은 스토리 63 팩(`relics.ui`·`deathSummary.buttons`·`memory.chapter`)을 옮겼다.
 * 데이터만 둔다(순수 계산 모듈이 import).
 */
export const LOOP2E_TEXT = {
  // ---- 유품 카드 (relics.ui)
  relicHead: '유품',
  relicOwned: '지닌 유품 — 한 단계 깊어진다',
  relicMaxed: '더 깊어지지 않는다',
  // ---- 결산 (deathSummary.buttons · floorEnd.summary.buttons)
  reborn: '다시 태어난다',
  memory: '기억을 떠올린다',
  closeDiary: '일기장을 덮는다',
  detailClosed: '세부 보기 (D)',
  detailOpen: '세부 · 시드 {seed}',
  killerUnknown: '알 수 없는 것',
  closingFallback: '여기까지 적었다. 다음 장은 아직 그려지지 않았다.',
  diedTitle: '이 생의 기록',
  lbKiller: '마지막 상대',
  lbPath: '지나온 길',
  lbTime: '걸린 시간',
  lbKills: '쓰러뜨린 적',
  lbDamage: '받은 피해',
  lbBuild: '지닌 것',
  soulsGained: '영혼 +{n}',
  // ---- 기억 장 (memory.chapter)
  bookTitle: '기억',
  recalled: '떠올렸다 — {name}. 다음 생부터 함께한다.',
  equipped: '지니고 태어난다',
  equip: '[Enter] 지니고 태어난다',
  unequip: '[Enter] 내려놓는다',
  recall: '[Enter] 떠올린다',
  nextLeft: '다음 기억까지 영혼 {n}',
  nextReady: '떠올릴 수 있는 기억이 있다.',
  nextAll: '떠올릴 기억이 더 없다.',
  bookHint: '방향키 고르기 · Enter · 클릭 떠올린다 · Esc 덮는다',
  stepLevel: '{n}단계 / {max}',
  chapterKeepsake: '기억의 소품',
  chapterAspect: '손이 기억한 모양',
  chapterPool: '떠올릴 개성',
  chapterShop: '장터에 놓일 것',
  chapterStat: '몸의 기억',
  // ---- 타이틀
  titleItem: '기억',
  titleItemHint: '영혼으로 잊은 것을 떠올린다',
  // ---- 운명 공개 뒤 고르기 · 운명 공개 줄
  aspectHead: '손이 기억한 모양',
  keepsakeHead: '기억의 소품',
  emptyHand: '빈손',
  fateAspect: '손이 기억한 모양 · {name}',
  fateKeepsake: '지니고 태어난다 · {name}',
} as const;

export type Loop2ETextKey = keyof typeof LOOP2E_TEXT;

/** 문구 하나 (팩 조회 없음 — 계약에 칸이 없는 글만 여기 둔다) */
export function l2eText(k: Loop2ETextKey): string {
  return LOOP2E_TEXT[k];
}
