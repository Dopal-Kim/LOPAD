/**
 * 61 단계 6 (P14 §2, 아트 §28) 무기 색 정체성 — UI 의 무기 강조색(개성 카드 테두리 · 원한의 한마디 세로 줄·할로 ·
 * Tab 성장도 지나온 길 · 성장 카드 키 밑줄·길 점·단련 눈금 · HUD 각성 게이지 채움 · 각성 배너 띠).
 * 주 색 = 아트 무기 색표 그대로(칼 '서리' #8fe3ff · 대검 '용암' #ff5a2a · 단검 '독' #c060ff · 활 '비취' #40e0a0).
 * 보조 색은 UI 가 팔레트 안에서 고른 값(은백 G12 · 검붉은 재 = 체력 막대 어두운 적 · 먹빛 G02 · 바랜 금 S5).
 * HUD·메뉴의 테두리·글자 기본색은 그대로 기본 팔레트 하나(§17.1) — 무기 색은 무기와 이어진 표시에만 쓴다.
 * (Phaser 없음 — 순수 모듈도 import)
 */
export type WeaponHueId = 'katana' | 'greatsword' | 'dagger' | 'bow';

export interface WeaponHue {
  /** 색 이름 (아트 색표) */
  name: string;
  /** 주 색 — 테두리·줄·채움 */
  main: string;
  /** 보조 색 — 어두운 쪽·바탕 띠 */
  sub: string;
}

export const WEAPON_HUE: Readonly<Record<WeaponHueId, WeaponHue>> = {
  katana: { name: '서리', main: '#8fe3ff', sub: '#c5c6c9' },
  greatsword: { name: '용암', main: '#ff5a2a', sub: '#751f33' },
  dagger: { name: '독', main: '#c060ff', sub: '#212224' },
  bow: { name: '비취', main: '#40e0a0', sub: '#c6a58b' },
};
