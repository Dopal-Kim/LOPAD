/**
 * 61라운드 플레이 점검 #3: 메뉴 줄에 내부 id·영문 등급이 보이지 않게 — 표시명은 여기(희귀도). 가격은 줄 label 에 넣지 않고
 * `UiMenuLine.price` 로만 넘긴다 (UI 가 한 번 그린다). UI 렌더러가 없을 때의 임시 텍스트 메뉴(TextMenu)만 이 표로 덧붙인다.
 */
export const RARITY_LABEL: Readonly<Record<string, string>> = {
  common: '일반',
  rare: '희귀',
  epic: '영웅',
  legendary: '전설',
};
