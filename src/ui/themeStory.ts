/**
 * 61라운드 단계 2·3 UI 수치 — 서사 표시(P8: 원한의 한마디 · 군주 대사 · 조사 기록 · 이벤트 문장 · 신규 적 소개)와
 * 보스 UI(P10: 이름 카드 · 국면 카드 · 파훼·결정타 · 촛대 안내 · 국면 눈금 · 처치 카드). 전부 임시값(도영 님 검토 대상).
 * 색은 팔레트 안에서만 — 층 강조 램프 슬롯(16~27)·무채 G·세피아 S. 위치는 논리 960×540 px, 정수. 순수 계산 모듈도 import 한다.
 */

/** 무기 id (kit `WEAPON_ICON_IDS` 값과 같다) */
export type VoiceWeaponId = 'katana' | 'greatsword' | 'dagger' | 'bow';

/** 자막 차례 (하단 가운데 · 무기 옆 · 공지) */
export const STORY_UI = {
  /** HUD 안 깊이 (배너·자막과 같은 층) */
  depth: 50,
  /** 하단 자막 줄바꿈 폭 */
  captionWrap: 720,
  /** 공지(notice) 1.8초 · 그 밖 기존 자막 3.6초 */
  noticeHoldMs: 1800,
  captionHoldMs: 3600,
  /** 사라짐 */
  fadeMs: 300,
  /** 쌓아 두는 자막 상한 (넘치면 오래된 기존 자막부터 버린다) */
  queueMax: 6,
} as const;

/**
 * 원한의 한마디 (STORY kind 'voice'): 전투 묶음 바로 위, 무기 아이콘 줄 왼쪽 끝에서 시작하는 한 줄. 무기마다 글씨 색·떨림·등장이 다르다.
 * 길이에 따라 머무는 시간 (위기 장면은 짧게 — 텍스트 팩 B1 '1.5초').
 */
export const VOICE_UI = {
  /** 전투 묶음 위 끝과의 간격 */
  gapAboveBundle: 6,
  /** 머묾 = 기본 + 글자당, 하한·상한 */
  baseMs: 1500,
  perCharMs: 55,
  minMs: 2000,
  maxMs: 3200,
  crisisMs: 1500,
  inMs: 140,
  /** 따옴표 */
  open: '“',
  close: '”',
  /** 왼쪽 세로 줄 (무기 빛 색) 폭·글과의 간격 */
  barW: 2,
  barGap: 5,
} as const;

/**
 * 무기별 목소리 모양 (텍스트 팩 B0 말투표):
 *  칼 = 차가운 해라체 → 서늘한 회백(G13), 떨림 없음, 왼쪽에서 한 번에 베어 들어온다(slide).
 *  대검 = 투박한 반말 → 잉걸 주황(강조 21), 크게 내려앉고(drop) 처음 0.6초 묵직하게 흔들린다.
 *  단검 = 속삭이는 반말 → 흐린 회색(G10, 할로 없음), 한 글자씩(type) + 내내 잘게 떨린다.
 *  활 = 세는 해요체 → 세피아 S5, 낱말 하나씩 센다(word), 떨림 없음.
 */
export interface VoiceLook {
  /** `TEXT_STYLES` 의 목소리 스타일 */
  style: 'voice_katana' | 'voice_greatsword' | 'voice_dagger' | 'voice_bow';
  /** 왼쪽 세로 줄 색 */
  bar: { slot: number } | { gray: number } | { sepia: number };
  /** 등장: slide 왼쪽에서 밀려옴 · drop 위에서 내려앉음 · type 한 글자씩 · word 낱말씩 */
  enter: 'slide' | 'drop' | 'type' | 'word';
  /** 등장 거리(px, slide·drop) 또는 글자·낱말 간격(ms, type·word) */
  enterValue: number;
  /** 떨림 진폭(px, 정수)·바뀌는 간격(ms)·떨리는 시간(ms, 0 = 내내) */
  jitterAmp: number;
  jitterEveryMs: number;
  jitterForMs: number;
}
export const VOICE_LOOK: Record<VoiceWeaponId, VoiceLook> = {
  katana: {
    style: 'voice_katana',
    bar: { gray: 13 },
    enter: 'slide',
    enterValue: 10,
    jitterAmp: 0,
    jitterEveryMs: 0,
    jitterForMs: 0,
  },
  greatsword: {
    style: 'voice_greatsword',
    bar: { slot: 21 },
    enter: 'drop',
    enterValue: 6,
    jitterAmp: 1,
    jitterEveryMs: 70,
    jitterForMs: 600,
  },
  dagger: {
    style: 'voice_dagger',
    bar: { gray: 10 },
    enter: 'type',
    enterValue: 45,
    jitterAmp: 1,
    jitterEveryMs: 90,
    jitterForMs: 0,
  },
  bow: {
    style: 'voice_bow',
    bar: { sepia: 5 },
    enter: 'word',
    enterValue: 150,
    jitterAmp: 0,
    jitterEveryMs: 0,
    jitterForMs: 0,
  },
};
/** 무기를 모를 때 (시험장 밖 다른 무기 등) */
export const VOICE_DEFAULT: VoiceWeaponId = 'katana';

/** 군주 대사 (STORY kind 'speech'): 하단 자막 + 왼쪽 위 화자 이름표 (잉크 패널) */
export const SPEECH_UI = {
  baseMs: 1600,
  perCharMs: 75,
  minMs: 2400,
  maxMs: 4600,
  /** 이름표 안쪽 여백·높이, 대사 글과의 간격 */
  platePadX: 6,
  plateH: 20,
  plateGap: 2,
} as const;

/** 이벤트 문장 (STORY kind 'event'): 하단 가운데 종이 띠 (지문체 — 일기장에 적힌 기록처럼) */
export const EVENT_UI = {
  wrap: 440,
  padX: 22,
  padY: 10,
  lineGap: 2,
  baseMs: 2000,
  perCharMs: 60,
  minMs: 3000,
  maxMs: 6000,
} as const;

/** 조사 기록 (STORY kind 'clue'): 가운데 위 일기장 쪽지 — 줄이 하나씩 적히고, 읽고 닫는다 */
export const CLUE_UI = {
  w: 380,
  top: 104,
  pad: 18,
  /** 제목 아래 괘선까지 · 줄 간격 */
  titleGap: 6,
  lineGap: 6,
  /** 줄이 하나씩 적히는 간격·한 줄 나타남 */
  lineEveryMs: 520,
  lineInMs: 220,
  /** 같은 단서의 줄이 따로 와도 같은 쪽지에 잇는 시간 */
  joinMs: 1500,
  /** 아무것도 안 하면 저절로 닫힘 (전투가 시작되거나 메뉴가 열려도 닫힘) */
  autoCloseMs: 30000,
  depth: 58,
  /** 닫기 안내 위 여백 */
  footGap: 10,
} as const;

/** 신규 적 첫 등장 소개 (화면 위쪽 짧은 이름 자막) — 성과 칩(34)·도장 카드(92) 사이 */
export const ENEMY_INTRO_UI = {
  top: 58,
  /** 이름 양옆 괘선 길이·간격 */
  ruleW: 36,
  ruleGap: 8,
  inMs: 160,
  holdMs: 2200,
  fadeMs: 300,
  /** 이어서 오면 쌓아 두는 상한 */
  queueMax: 3,
  /** 괘선 색 (강조 20) */
  ruleSlot: 20,
} as const;

/** 보스 UI (P6·P10) */
export const BOSS_UI = {
  /** 보스 막대 (아래 가운데) 폭·전투 묶음과 띄울 최소 간격 — 61 단계 1 값 그대로 */
  barW: 320,
  barGap: 12,
  barBottom: 12,
  /** 국면 눈금: 막대 위로 튀어나오는 길이·색 (강조 22) / 지난 눈금 무채 G06 */
  tickOut: 3,
  tickSlot: 22,
  tickPassedGray: 6,
  /** '무너짐' 표지 깜빡임 */
  brokenBlinkMs: 220,
  /** 이름 카드 (등장) */
  nameCard: { top: 96, inMs: 260, holdMs: 1900, outMs: 400, ruleW: 180 },
  /** 국면 카드 (전환) */
  phaseCard: { top: 92, inMs: 200, holdMs: 1500, outMs: 350, drop: 6 },
  /** 국면 띠 '얼큰 → 만취 → 인사불성': 낱말과 픽셀 화살 사이·화살 폭·화살 색(무채 G09) */
  stripGap: 6,
  stripArrowW: 9,
  stripArrowGray: 9,
  /** 이름·국면 카드 뒤 어둠 띠 위아래 여백 */
  bandPad: 8,
  /** 파훼·결정타 문구 */
  breakStamp: { top: 84, inMs: 120, holdMs: 1100, outMs: 260, drop: 8, shakeAmp: 2, shakeMs: 40, shakeForMs: 240 },
  /** 처치 카드 + 어둠 띠 */
  defeat: { top: 196, bandH: 84, inMs: 300, holdMs: 2200, outMs: 450, ruleW: 220 },
  /** 처치 카드가 끝나기 전 메뉴는 기다린다 (보스 대사·한마디가 이어지면 늘이되 처치 시점에서 이만큼까지) */
  menuWaitMaxMs: 4500,
  /** 촛대 안내: 화면 가장자리 여백·화살 크기·화면 안 표지가 촛대 위로 뜨는 높이·까딱임 */
  candle: { edge: 22, arrow: 7, markUp: 20, bobMs: 260, slot: 22, hintSlot: 25 },
  depth: 52,
} as const;

/** 1층 보스 국면 이름 (54 Q1 · 61 P6) — 시스템이 국면 이름을 주지 않을 때 */
export const BOSS_PHASE_NAMES_BY_FLOOR: Record<number, readonly string[]> = {
  0: ['얼큰', '만취', '인사불성'],
};
/** 1층 보스 국면 경계 (체력 비율, 61 P6 설계 점검 SY-8: 65% · 30%) — 시스템이 경계를 주지 않을 때 */
export const BOSS_PHASE_MARKS_BY_FLOOR: Record<number, readonly number[]> = {
  0: [0.65, 0.3],
};
/** 어둠(촛대) 국면 — 이 국면부터 촛대 안내 (1층 '인사불성' 등불 끄기) */
export const BOSS_DARK_PHASE_BY_FLOOR: Record<number, number> = {
  0: 3,
};
