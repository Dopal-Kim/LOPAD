/**
 * 62 루프 2 UI F 문구 (시스템 D 계약 2차 패스 — 사연 메뉴 · 결과 컷 · 숨은 보상 · 장터 노점 카드 · 상인과 말하기 · 팻말 · 무리 방향).
 * 머리말은 시스템이 내려 주는 스토리 63 팩 `events.ui`(`UiEventScene.heads`)가 먼저다 — 여기 값은 그것이 없을 때의 대체(같은 문구).
 * 장터 문구는 63 팩 `shop.stall` 을 옮겼다 (가격은 아이콘 + 수치로 따로 그려 '[E] 산다' 만). 데이터만 둔다(순수 계산 모듈이 import).
 */
export const LOOP2F_TEXT = {
  // ---- 사연 (events.ui)
  costHead: '내준다',
  gainHead: '얻는다',
  unknown: '?',
  pick: '하나를 고른다',
  /** 결과 컷 닫기 ('[E] 계속' — 키는 설정의 상호작용 키) */
  cutContinue: '[{key}] 계속',
  /** 사연·상인 메뉴 아래 안내 */
  eventHint: '{keys} 또는 ↑↓ 고르기 · Enter · 클릭 고른다',
  eventHintCancel: ' · Esc {label}',
  // ---- 숨은 보상 알림
  hiddenLater: '다음에 받는다',
  hiddenPaid: '받았다',
  // ---- 장터 노점 카드 (shop.stall)
  stallBuy: '[{key}] 산다',
  stallSold: '팔렸다',
  stallPrice: '전표 {n}',
  stallFree: '값 없음',
  // ---- 산 뒤 전표 줄어듦
  goldSpent: '−{n}',
} as const;

export type Loop2FTextKey = keyof typeof LOOP2F_TEXT;

export function l2fText(k: Loop2FTextKey): string {
  return LOOP2F_TEXT[k];
}
