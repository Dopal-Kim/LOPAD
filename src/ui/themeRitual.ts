/**
 * 62 루프 1 P0-2 첫 생 의식 UI 배치·색 (계약 §20). 논리 960×540, 정수. 임시값 — 62 전권 위임, 프로듀서 검토 대상.
 * 색은 팔레트 안에서: 종이 = 키트 panel_paper, 먹 = 세피아 S0 보다 어둡게, 낙관 = 수련장 도장과 같은 붉은 인주.
 */
export const RITUAL_UI = {
  /**
   * 아트 그림 (art 계약 §30 — `assets/sprites/ritual/*`, 시스템은 읽지 않는다 → UI 가 같은 키로 읽는다).
   * 메타 JSON 은 `<키>.json` 캐시 키 (nameField·strokeArea·strokeClip·slice 등은 그 값을 쓴다).
   */
  art: {
    page: 'ritual/diary_first_page',
    back: 'ritual/back_canvas',
    glow: 'ritual/back_canvas_glow',
    brush: 'ritual/ink_brush',
    frame: 'ritual/fate_frame',
  },
  artUrl: 'assets-game/sprites/ritual/',
  /** 무기 미리보기 (계약 §20 lookKey 가 없을 때 UI 가 읽는 `looks/<무기>_base`) */
  lookUrl: 'assets-game/sprites/looks/',
  depth: 10,
  /** 바깥 어둠 */
  dimAlpha: 0.88,
  /** 일기장 첫 장 (이름·덧쓰기) */
  page: {
    w: 460,
    h: 320,
    cy: 252,
    pad: 26,
    /** 이름 칸 (괘선 위에 쓴다) */
    fieldW: 300,
    fieldTop: 150,
    /** 칸 글씨(먹) 배율 — Galmuri14 정수 확대 */
    inkScale: 2,
    /** 글자가 새로 적힐 때 번지는 먹 점 수·퍼짐·시간 */
    bleedDots: 7,
    bleedR: 9,
    bleedMs: 420,
    caretBlinkMs: 480,
    /** 장이 열린 뒤 숨은 칸에 포커스를 주기까지 (앞 장의 키가 글자로 들어가지 않게) */
    focusDelayMs: 120,
  },
  /** 3획: 등 그림 칸 — 아트가 없을 때의 코드 그림 (아트가 있으면 json strokeArea·strokeClip) */
  back: { x: 230, y: 92, w: 500, h: 448 },
  /** 등 그림 아트: 1920 렌더 그림을 논리 0.5 배, 붓 자국은 640×360 도트 화폭(논리 1.5 배) */
  canvas: { renderScale: 0.5, dotW: 640, dotH: 360, dotScale: 1.5, glowBreathMs: 4200 },
  /** 붓 스탬프 (art §30 ink_brush) — 긋는 중 먹 · 판정 난 획 불씨 먹 · 빛무리 */
  stamp: { ink: 0x141516, ember: 0xe8b858, halo: 0xd67a11, haloAlpha: 0.35, slow: 0.12, fast: 0.75, step: 1.2 },
  /** 먹 붓 점 모으기: 점 사이 최소 거리 · 최대 점 수 · 속도 부드럽게 */
  brush: { minDist: 2, maxPoints: 600, smooth: 0.35 },
  /** 획 ↔ 무기 규칙 종이 (오른쪽) */
  legend: { x: 748, y: 120, w: 196, rowH: 22, pad: 10 },
  /** 3획 낙관 칸 (위 가운데 — 아트 uiSafe 위 띠 안) */
  seals: { top: 28, size: 16, gap: 10 },
  /** 회피 시험 과제 목록 (오른쪽 위) */
  tasks: { right: 944, top: 16, w: 210, rowH: 20, pad: 10, box: 9 },
  /** 과제 이름 카드 (위 가운데) */
  taskCard: { top: 96 },
  /** 운명 공개 액자 (art §30 fate_frame 9-slice 40 · inner 36 · 264 — 화면 (348,96), 아래 글 372~) */
  fate: { x: 348, y: 92, size: 264, slice: 40, inner: 36, textTop: 364, inMs: 420, pulseMs: 600 },
  /** 아래 안내 줄 */
  hintBottom: 14,
  /** 먹 색 (낙관 인주는 수련장 도장과 같은 HEALTH_BAR.fill) */
  ink: '#0d0a08',
  inkBleed: '#2b2119',
} as const;
