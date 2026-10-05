/**
 * 61라운드 단계 2·3 UI 문구 (서사 표시 틀 · 보스 UI 틀). 전부 임시값(도영 님·스토리 검수 대상).
 * 서사 문장 자체(원한의 한마디·만취 대사·단서·이벤트)는 시스템이 STORY 로 내려준다 — 여기는 UI 가 붙이는 틀 낱말만.
 * 텍스트 팩 조회는 `text.ts` 의 `storyText`(팩 `hud.<키>` 우선). 데이터만 둔다(순수 계산 모듈이 import).
 */
export const STORY_TEXT = {
  // ---- 조사 기록 쪽지
  clueTitle: '조사 기록',
  clueClose: 'Enter · Esc 덮는다',
  clueMore: '…',
  // ---- 신규 적 소개 (설명이 없을 때 이름만)
  enemyIntroTag: '처음 보는 적',
  // ---- 보스 이름 카드·국면
  /** 국면 이름을 모를 때 '{n}국면' */
  phaseN: '{n}국면',
  /** 국면 카드 위 작은 줄 '2국면' */
  phaseOrdinal: '{n}국면',
  /** 보스 막대 이름 줄 '만취 · 얼큰' */
  barName: '{name} · {phase}',
  /** 3국면(어둠) 국면 카드 아래 안내 — E 는 시스템이 읽는 상호작용 키 */
  darkHint: '어둠 — 쓰러진 촛대를 [E] 로 다시 켠다',
  /** 화면 밖 촛대 화살 옆 */
  candleMark: '촛대',
  // ---- 파훼·결정타
  breakHead: '파훼',
  breakCup: '잔 깨기',
  breakPillar: '기둥 충돌',
  breakCask: '술통 되치기',
  breakStumble: '취권 넘어짐',
  breakAny: '무너졌다',
  /** 무너진 동안 받는 피해 증가 (61 P6) */
  breakSub: '무너진 동안 더 아프다',
  finisherHead: '결정타',
  finisherSub: '무너진 틈을 끝냈다',
  /** 보스 막대 옆 무너짐 표지 */
  brokenTag: '무너짐',
  // ---- 처치 카드
  defeatLine: '쓰러졌다',
  defeatFinisher: '결정타로 쓰러졌다',
} as const;
export type StoryTextKey = keyof typeof STORY_TEXT;
