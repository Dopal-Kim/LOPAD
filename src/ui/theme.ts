/**
 * UI 테마 (41라운드, 계약 `contracts/ui-art-kit.md` v0.4).
 * 색은 팔레트 사본 `assets/ui/kit/palette.json` 의 값만 쓴다 — 무채 G00~G15, 세피아 S0~S5, 층 강조 램프 16~27.
 * 글자는 1.2절 발광 규칙(`TEXT_STYLES`)만 쓴다. 새 색을 만들지 않는다 (알파 0.5 / 0.55 만 허용).
 */

/** 무채 16칸 (G00~G15) — 팔레트 고정값 */
export const GRAY = [
  '#000000',
  '#141516',
  '#212224',
  '#2f3033',
  '#3e3f42',
  '#4d4f52',
  '#5c5e62',
  '#6c6f73',
  '#7d8084',
  '#8e9195',
  '#a0a2a6',
  '#b2b4b8',
  '#c5c6c9',
  '#d8d9db',
  '#ebeced',
  '#ffffff',
] as const;

/** UI 전용 세피아 램프 S0~S5 (`ui.ramp`, v0.4) */
export const SEPIA = ['#1f1813', '#30261e', '#403227', '#503f32', '#6a5645', '#c6a58b'] as const;

/** 1층 '잔' 강조 램프 (슬롯 16~27 → 인덱스 0~11). 팔레트 JSON 을 못 읽었을 때의 폴백 */
export const FLOOR1_RAMP = [
  '#1a110f',
  '#3f271d',
  '#653b24',
  '#8b4d22',
  '#b0611a',
  '#d67a11',
  '#dc8e23',
  '#e2a33c',
  '#e8b858',
  '#eecc78',
  '#f4de9b',
  '#faeec0',
] as const;

/** 강조 램프 슬롯 번호 → 램프 배열 인덱스 */
export const ACCENT_FIRST_SLOT = 16;

/** 글꼴 (34·39라운드: Galmuri 단일, Bold 금지). 11 은 한자 포함 가능, 14 는 한자 없는 고정 제목만 */
export const FONT = {
  body: { family: 'Galmuri11', px: 11, lineHeight: 12 },
  title: { family: 'Galmuri14', px: 14, lineHeight: 15 },
} as const;
export type FontKind = keyof typeof FONT;

/** 글꼴 파일 (UI 소유). Galmuri11 은 `public/style.css` 의 @font-face 가 먼저 선언한다 */
export const FONT_FILES: Record<string, string> = {
  Galmuri11: 'assets-game/ui/fonts/Galmuri11.woff2',
  Galmuri14: 'assets-game/ui/fonts/Galmuri14.woff2',
};

/**
 * 발광 글자 스타일 (계약 1.2절 표). `halo`/`shade` 가 없으면 그 ring 을 그리지 않는다.
 * `accentSlot` 이 있으면 현재 층 강조 램프의 그 슬롯 색을 쓴다 (문자열 색은 무시).
 */
export interface GlowStyle {
  body: string | { accentSlot: number };
  bodyAlpha: number;
  halo?: { color: string | { accentSlot: number }; alpha: number };
  shade?: { color: string; alpha: number };
}

export const TEXT_STYLES = {
  /** 종이 본문 */
  page_body: {
    body: SEPIA[5],
    bodyAlpha: 1,
    halo: { color: SEPIA[4], alpha: 1 },
    shade: { color: SEPIA[2], alpha: 1 },
  },
  /** 종이 제목 */
  page_title: {
    body: GRAY[15],
    bodyAlpha: 1,
    halo: { color: SEPIA[4], alpha: 1 },
    shade: { color: SEPIA[2], alpha: 1 },
  },
  /** 선택 항목 (커서 옆): 할로 = 층 강조 20 (α0.5) */
  page_selected: {
    body: GRAY[15],
    bodyAlpha: 1,
    halo: { color: { accentSlot: 20 }, alpha: 0.5 },
    shade: { color: SEPIA[2], alpha: 1 },
  },
  /** 비선택 항목 */
  page_unsel: {
    body: GRAY[13],
    bodyAlpha: 1,
    halo: { color: SEPIA[4], alpha: 1 },
    shade: { color: SEPIA[2], alpha: 1 },
  },
  /** 흐린 글·안내 (할로·그늘 없음) */
  page_faint: { body: SEPIA[5], bodyAlpha: 0.55 },
  /** 잉크 HUD 본문·자막·층 제목 */
  ink_body: {
    body: GRAY[14],
    bodyAlpha: 1,
    halo: { color: { accentSlot: 20 }, alpha: 0.5 },
    shade: { color: GRAY[0], alpha: 1 },
  },
  /** HUD 흐림 (개성 수치·조작 안내·M) */
  ink_faint: { body: GRAY[11], bodyAlpha: 1, shade: { color: GRAY[0], alpha: 1 } },
  /** 공지·보스 이름 */
  ink_accent: {
    body: { accentSlot: 22 },
    bodyAlpha: 1,
    halo: { color: { accentSlot: 20 }, alpha: 0.5 },
    shade: { color: GRAY[0], alpha: 1 },
  },
} as const satisfies Record<string, GlowStyle>;
export type TextStyleName = keyof typeof TEXT_STYLES;

/** 선택 목록·레이아웃 공통 수치 (정수) */
export const LAYOUT = {
  /** 화면 가장자리 안쪽 여백 (32라운드 권장 16 이상) */
  edge: 16,
  /** 선택 목록 줄 간격: 글꼴 높이 12 + 할로·그늘 4 + 여백 2 */
  row: 18,
  /** detail 줄 간격 */
  detail: 16,
  /** 항목 사이 추가 간격 (detail 있는 항목 뒤) */
  gap: 4,
  /** 비활성 항목 알파 */
  disabledAlpha: 0.45,
  /** 도장 알파 (계약 2.5절 권장) */
  stampAlpha: 0.85,
  /** 미니맵 한 칸 */
  miniCell: 12,
} as const;

export function hexToNum(hex: string): number {
  return parseInt(hex.replace('#', ''), 16);
}
