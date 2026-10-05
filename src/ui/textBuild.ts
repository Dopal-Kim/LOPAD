import type { UiChoiceKind, UiNodeRewardKind, UiRarity, UiTagId } from '../contract/ui';

/**
 * 57·60라운드 계약 §14 (빌드 축·2차 묶음) UI 문구 — 전부 임시값(도영 님·스토리 검수 대상).
 * 태그·패시브·저주·이벤트·접두어·소모품 이름은 시스템이 준 자리표시 문자열을 그대로 쓰고, 여기는 UI 가 그리는 틀·범례·
 * 시스템 값이 비었을 때의 기본 이름만 둔다. 이 파일은 데이터만(순수 계산 모듈이 import) — 텍스트 팩 조회는
 * `text.ts` 의 `r60Text`(팩 `hud.<키>` 우선).
 */
export const R60_TEXT = {
  // ---- §14.1 태그·세트 (HUD 칩·일기장)
  /** 세트 단계 — {stage} = 2·4·6 */
  setStage: '{stage}단',
  /** 다음 임계까지 — {n} = 다음 임계 */
  setNext: '다음 {n}',
  setMax: '최대',
  /** 세트 단계 바뀜 토스트 */
  setUp: '{name} 세트 {stage}단 — {effect}',
  setUpPlain: '{name} 세트 {stage}단',
  setDown: '{name} 세트가 {stage}단으로 내려갔다',
  setOff: '{name} 세트가 꺼졌다',
  // ---- §14.2 이중 개성
  dualGained: '이중 개성 — {name}',
  dualPair: '짝 {branch} · {tag} {tier}단',
  // ---- §14.3 저주
  curseHead: '저주',
  curseNodes: '{n}노드 남음',
  curseKills: '{n}처치 남음',
  curseGained: '저주를 받았다 — {name}',
  curseEnded: '저주가 풀렸다 — {name}',
  // ---- §14.4 메뉴 줄
  locked: '잠김 — {condition}',
  lockedNote: '(잠김)',
  soldOutNote: '(팔림)',
  disabledNote: '(불가)',
  /** 상점 묶음 머리글 (§14.6) */
  groupFixed: '늘 파는 것',
  groupDisplay: '오늘의 진열',
  groupReroll: '진열 바꾸기',
  groupChest: '덤',
  groupMapInfo: '지도 정보',
  // ---- 60 Q38 3지선다 카드 (개성·보상·패시브 3택)
  /** 카드 조작 안내 — {keys} = '1·2·3' */
  choiceHint: '{keys} 또는 ←→ 고르기 · Enter 고른다',
  /** 그만두기 줄이 있을 때 덧붙임 — {key} = 그만두기 키 */
  choiceHintCancel: ' · {key}·Esc 그만두기',
  // ---- §14.11 완벽 성공 (HUD 연출)
  perfectParry: 'PARRY',
  perfectGuard: 'PERFECT GUARD',
  perfectRelease: 'PERFECT RELEASE',
  perfectEvade: 'PERFECT EVADE',
  // ---- §14.5 노드 지도
  rewardHead: '보상 {name}',
  riskHead: '위험 {name}',
  riskElite: '엘리트 길',
  riskCurse: '저주 길',
  prefixHead: '접두어 {list}',
  eventHead: '내용 {name}',
  gradeHead: '도장 {name}',
  hiddenSmudge: '얼룩진 자국 — 어딘가 숨은 길이 있다',
  hiddenLocated: '숨은 길 — 단서를 찾으면 열린다',
  hiddenFound: '숨은 길',
  intelHead: '산 지도 정보',
  intelNextTier: '다음 단',
  intelFullFloor: '층 전체',
  intelHidden: '숨은 길 위치',
  rewardLegend: '보상 표시',
  // ---- §14.10 성과 등급
  gradePerfect: '완',
  gradeGood: '양',
  gradeNone: '도장 없음',
  /** 도장 글자 (한자 — Galmuri11) */
  stampPerfect: '完',
  stampGood: '良',
  trialLeft: '{sec}초',
  trialOver: '시간 지남',
  trialNoHit: '무피격',
  trialHit: '피격',
  gradeNoHit: '무피격',
  gradeInTime: '제한 시간',
  gradeOk: '○',
  gradeNg: '×',
  deltaGold: '+{n} {gold}',
  deltaPersonality: '+{n} 개성',
  // ---- §14.8 소모품
  consumableEmpty: '빈 칸',
  consumableUsed: '{name} — 남은 {left}',
  // ---- §14.11 숨은 길
  hiddenFoundToast: '숨은 길이 지도에 드러났다',
  // ---- 일기장 빌드 쪽
  buildTitle: '빌드',
  buildTags: '태그·세트',
  buildDual: '이중 개성',
  buildCurse: '저주',
  buildPassives: '패시브',
  buildConsumable: '소모품',
  buildNone: '―',
  passiveLevel: 'Lv{level}/{max}',
} as const;
export type R60TextKey = keyof typeof R60_TEXT;

/** 태그 기본 이름 (계약 §14.1 주석의 자리표시 이름) — 스냅샷 `build.tags[].name` 이 있으면 그것을 쓴다 */
export const TAG_NAME: Record<UiTagId, string> = {
  insight: '간파',
  breach: '돌파',
  vital: '급소',
  scar: '상흔',
  chain: '연쇄',
  ranged: '원격',
  weight: '중량',
  mark: '표식',
  endure: '버팀',
  drunk: '취기',
};

/** 개성·보상 칸 종류 이름 (§14.4) */
export const CHOICE_KIND_NAME: Record<UiChoiceKind, string> = {
  branchA: '갈래 A',
  branchB: '갈래 B',
  reinforce: '강화',
  bloodPact: '피의 계약',
  awaken: '각성',
  dual: '이중 개성',
  passive: '패시브',
  curse: '저주',
};

/** 3지선다 카드 머리표 — 줄에 `kind` 가 없을 때 메뉴 id 로 (60 Q38) */
export const CHOICE_MENU_HEAD: Readonly<Record<string, string>> = {
  evolve: '개성',
  reward: '보상',
  passive: '패시브',
};

/** 패시브 희귀도 이름 (§14.4) */
export const RARITY_NAME: Record<UiRarity, string> = {
  common: '일반',
  rare: '희귀',
  epic: '영웅',
  legendary: '전설',
};

/** 노드 보상 이름 (§14.5) */
export const REWARD_NAME: Record<UiNodeRewardKind, string> = {
  gold: '전표 주머니',
  passive: '패시브',
  personality: '개성',
  consumable: '소모품',
  statPoint: '능력치 포인트',
  curse: '저주',
  unknown: '알 수 없음',
};

/**
 * 노드 보상 임시 글리프 (아이콘 7종이 오기 전 — 아트 요청 목록). 한 글자를 작은 표 안에 그린다.
 * 전표 주머니 '전' · 패시브 '패' · 개성 '개' · 소모품 '병' · 능력치 포인트 '점' · 저주 '저' · 미상 '?'
 */
export const REWARD_GLYPH: Record<UiNodeRewardKind, string> = {
  gold: '전',
  passive: '패',
  personality: '개',
  consumable: '병',
  statPoint: '점',
  curse: '저',
  unknown: '?',
};

/** 위험 노드 임시 글리프 (아이콘 2종 대기): 엘리트 길 '투'(투구) · 저주 길 '잔'(깨진 잔) */
export const RISK_GLYPH: Record<'elite' | 'curse', string> = { elite: '투', curse: '잔' };

/**
 * 60라운드 Q32 등 E 안내의 기본 이름·행동 문구 — 시스템이 `interactable.name`/`action` 을 비워 보냈을 때만 쓴다
 * (계약 §9.8: 문구는 시스템이 준다). `clue`·`eventProp`·`mapSeller` 는 계약 코드에 kind 가 생기면 바로 쓰인다.
 */
export const STRUCT_KIND_TEXT: Readonly<Record<string, { name: string; action: string }>> = {
  warFlag: { name: '전장 깃발', action: '깃발을 세운다' },
  clue: { name: '수상한 자국', action: '살펴본다' },
  eventProp: { name: '눈길 가는 것', action: '다가간다' },
  mapSeller: { name: '지도 장수', action: '지도를 본다' },
};
