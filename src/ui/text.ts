import { uiCommands, type UiText } from '../contract/ui';
import { firstSentence } from './regionView';
import { replaceMuteHint } from './resourceView';
import { withControlExtras } from './structView';

/**
 * 세계관 문구 조회 (계약 §4 getUiText, 29라운드). 키가 없거나 비면 기본 문구를 쓴다.
 * 채택 범위는 결정 로그 round-29 자율 결정 B 를 따른다 (보류 항목은 호출하지 않는다).
 */
type Section = Exclude<keyof UiText, 'controls'>;

export function uiText(section: Section, key: string, fallback: string): string {
  const v = uiCommands.getUiText()[section]?.[key];
  return typeof v === 'string' && v.length > 0 ? v : fallback;
}

/** `{name}` 꼴 치환자를 채운다. 값이 없는 치환자는 그대로 둔다 */
export function fill(template: string, vars: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (m, k: string) => (k in vars ? String(vars[k]) : m));
}

const DEFAULT_CONTROLS = 'WASD 이동 · 좌클릭 공격 · 우클릭 {secondary} · 스페이스 대쉬 · Q 물약 · Esc 일시정지';

/**
 * 47라운드: 조작법 줄에 빠져 있으면 덧붙이는 키 (임시 문구, 텍스트 팩 `hud.<키>` 가 있으면 그 문구).
 * `token` 이 조작법 줄에 이미 있으면(텍스트 팩이 이미 적었으면) 덧붙이지 않는다.
 */
const CONTROL_EXTRAS: { token: RegExp; key: string; fallback: string }[] = [
  // 53라운드(51라운드 §4): F = 넣기/뽑기
  { token: /(^|[\s·])F(\s|$)/, key: 'controlCarry', fallback: 'F 넣기·뽑기' },
  { token: /(^|[\s·])E(\s|$)/, key: 'controlInteract', fallback: 'E 상호작용' },
  { token: /Shift/i, key: 'controlSprint', fallback: 'Shift 달리기' },
  { token: /Tab/i, key: 'warpKeyHint', fallback: 'Tab 워프' },
];

/**
 * 조작법 한 줄. `{secondary}` 는 스냅샷의 우클릭 보조 동작 이름으로, 비면 '보조 동작'. 47라운드: E·Shift·Tab 이 없으면 덧붙인다.
 * 49라운드: 'M 지도' 를 덧붙이고(팩의 'M 음소거' 는 바꾼다), 노드 지도 층·무기 시험장(`routeMode`)에서는 'Tab 워프' 를 뺀다
 * (노드 지도 층은 M·Tab 이 같은 지도).
 */
export function controlsLine(secondaryName: string, routeMode = false): string {
  const tpl = uiCommands.getUiText().controls || DEFAULT_CONTROLS;
  // 49라운드: M 은 지도 (음소거는 Esc 일기장). 팩에 'M 음소거' 가 남아 있으면 바꾼다
  const mapHint = routeText('mapKeyHintM');
  const line = replaceMuteHint(fill(tpl, { secondary: secondaryName || '보조 동작' }), mapHint);
  const extras = CONTROL_EXTRAS.filter((e) => !(e.key === 'warpKeyHint' && routeMode)).map((e) => ({
    token: e.token,
    text: uiText('hud', e.key, e.fallback),
  }));
  // 노드 지도 층은 M·Tab 이 같은 지도라 'M 지도' 하나만, 그 외 층은 'M 지도' + 'Tab 워프'
  extras.push({ token: /(^|[\s·])M(\s|$)/, text: mapHint });
  return withControlExtras(line, extras);
}

/** 45라운드 워프 문구 (임시값, 도영 님 검수 대상). 텍스트 팩 `hud.<키>` 가 있으면 그 문구를 쓴다 */
export const WARP_TEXT = {
  warpTitle: '지나온 길',
  warpHint: 'WASD·방향키 고르기 · Enter·Space·클릭 건너가기 · Tab·Esc 닫기',
  warpEmpty: '아직 건너갈 곳이 없다. 마친 방만 다시 찾아갈 수 있다',
  warpPick: '건너갈 곳을 고른다',
  warpHere: '지금 여기',
  warpCan: '건너갈 수 있다',
  warpCannot: '아직 마치지 않았다',
  warpKeyHint: 'Tab 워프',
  warpDone: '건너왔다 — {room}',
  warpDeniedCombat: '싸움이 끝나야 건너갈 수 있다',
  warpDeniedBusy: '지금은 건너갈 수 없다',
  warpDeniedUnknown: '그런 곳은 없다',
  warpDeniedNotCleared: '아직 마치지 않은 곳이다',
  warpDeniedCurrent: '이미 여기 있다',
  roomStart: '시작한 곳',
  roomTrial: '시련',
  roomRest: '쉼터',
  roomBoss: '본영',
} as const;
export type WarpTextKey = keyof typeof WARP_TEXT;

export function warpText(key: WarpTextKey): string {
  return uiText('hud', key, WARP_TEXT[key]);
}

/**
 * 47라운드 상호작용 구조물 — UI 가 그리는 조작 틀 문구 (임시값, 도영 님 검수 대상).
 * 구조물 이름·행동·사유·결과 문장은 시스템이 내려준다(계약 §9.8). 여기는 키 틀·범례·닫기 같은 UI 문구만.
 * 텍스트 팩 `hud.<키>` 가 있으면 그 문구를 쓴다.
 */
export const STRUCT_TEXT = {
  /** 안내 키 틀: 누르기 */
  keyTap: '[{key}]',
  /** 안내 키 틀: 길게 누르기 ({sec} = 초) */
  keyHold: '[{key} {sec}초]',
  /** 구조물 메뉴 닫기 버튼 */
  menuClose: 'Esc 닫기',
  /** 패 탁자 카드 뒷면 */
  cardBack: '?',
  /** 패 탁자 조작 안내 */
  cardHint: '1·2·3 또는 ←→ 고르기 · Enter 뒤집기 · 0·Esc 그만두기',
  /** 워프 지도 범례: 구조물 점 */
  legendStructure: '쓸 것이 남은 곳',
  /** 도전 남은 시간 ({sec} = 초, 소수 1자리) */
  challengeTime: '{sec}초',
} as const;
export type StructTextKey = keyof typeof STRUCT_TEXT;

export function structText(key: StructTextKey): string {
  return uiText('hud', key, STRUCT_TEXT[key]);
}

/**
 * 48라운드 노드 지도 문구 (임시값, 도영 님 검수 대상). 노드 이름은 시스템이 준 자리표시 그대로.
 * 텍스트 팩 `hud.<키>` 가 있으면 그 문구를 쓴다.
 */
export const ROUTE_TEXT = {
  /** 지도 제목 (Galmuri14 — 한자 없는 고정 제목) */
  mapTitle: '가는 길',
  /** 고르기 모드 안내 */
  chooseHint: '←→↑↓ 고르기 · Enter·클릭 그리로 간다 · Esc 물러나기',
  /** 보기 모드 안내 */
  viewHint: '←→↑↓ 둘러보기 · M·Tab·Esc 닫기',
  /** 고르기 모드 제목 옆 한 줄 */
  choosePrompt: '다음 갈 곳을 고른다',
  /** 노드 상태 설명 */
  stateCurrent: '지금 여기',
  stateAvailable: '갈 수 있다',
  stateCleared: '지나온 곳',
  statePassed: '지나친 갈래',
  stateLocked: '아직 멀다',
  /** chooseNode 거부 */
  chooseDenied: '지금은 그리로 갈 수 없다',
  /** 노드 종류 이름 (상점은 스냅샷 names.shop 우선) */
  typeJourney: '여정',
  typeBattle: '전투',
  typeShop: '상점',
  typeRest: '쉼터',
  typeEvent: '이벤트',
  typeBoss: '본영',
  /** HUD */
  mapKeyHint: 'Tab 지도',
  /** 49라운드: M = 지도 (HUD 우상단·조작법 줄) */
  mapKeyHintM: 'M 지도',
  stripRemain: '남은 길 {n}',
  stripLast: '마지막',
  /** 탄생 연출 중 건너뛰기 안내 */
  birthSkip: '아무 키나 눌러 건너뛰기',
  /** 49라운드 위치 정보 칸 머리글 */
  hereTitle: '지금 있는 곳',
  lookTitle: '살펴보는 곳',
  pickTitle: '고른 곳',
  /** 49라운드 넘어가기 확인 (원문 결정 문구) */
  confirmTitle: '넘어가시겠습니까?',
  confirmYes: '예',
  confirmNo: '아니오',
  confirmHint: '←→ 고르기 · Enter 정하기 · Esc 아니오',
} as const;
export type RouteTextKey = keyof typeof ROUTE_TEXT;

export function routeText(key: RouteTextKey): string {
  return uiText('hud', key, ROUTE_TEXT[key]);
}

/**
 * 49라운드 문구 (임시값, 도영 님 검수 대상): 무기 시험장·소리 설정·무기 자원 상태.
 * 텍스트 팩 `hud.<키>` 가 있으면 그 문구를 쓴다.
 */
export const R49_TEXT = {
  /** 타이틀 항목 */
  titleLab: '무기 시험장',
  /** 시험장 HUD 좌상단 (L 은 시스템이 정할 열기 키의 임시 제안) */
  labHud: '무기 시험장 · L 무기 고르기 · Esc 일기장',
  /** 시험장 일시정지 일기장 */
  labPauseTitle: '무기 시험장',
  labContinue: '계속한다',
  labLeave: '시험장을 나간다',
  /** Esc 일기장 설정: 소리 */
  soundOff: '소리 끄기',
  soundOn: '소리 켜기',
  /** 무기 자원 상태 (값 옆 짧은 글). low 는 색만 바꾼다 */
  resExhausted: '지침',
  resReloading: '장전',
  resOverheat: '과열',
} as const;
export type R49TextKey = keyof typeof R49_TEXT;

export function r49Text(key: R49TextKey): string {
  return uiText('hud', key, R49_TEXT[key]);
}

/**
 * 50라운드 지역 카드 문구 (임시값, 도영 님·스토리 검수 대상). 지역 키아트 키별 짧은 설명 한 줄.
 * 텍스트 팩 `hud.region_<키>` 가 있으면 그 문구를 쓴다. 키가 없는 지역은 노드 설명(`desc`)의 첫 문장.
 */
export const REGION_TEXT: Record<string, string> = {
  waste: '부러진 창과 깃발만 남은 옛 싸움터',
  gate: "술독 제국 '잔'으로 드는 문",
  outer: '술 냄새가 골목마다 밴 성 밖 거리',
  brewery: '증류탑이 밤낮없이 끓는 곳',
  hall: '취한 지배자가 잔치를 벌이는 곳',
};

export function regionText(key: string | null, fallbackDesc?: string): string {
  if (key && REGION_TEXT[key]) return uiText('hud', `region_${key}`, REGION_TEXT[key]);
  return firstSentence(fallbackDesc);
}

/**
 * 53라운드 문구 (임시값, 도영 님 검수 대상): Esc 한 단계 뒤로(51라운드 §6), F 넣기/뽑기(51라운드 §4),
 * 튜토리얼 안내 패널·적 등장 경고(51라운드 §3). 텍스트 팩 `hud.<키>` 가 있으면 그 문구를 쓴다.
 */
export const R53_TEXT = {
  /** 반드시 골라야 하는 메뉴에서 Esc */
  escStay: '하나를 골라야 덮을 수 있다',
  /** HUD 넣기/뽑기 (3행 오른쪽) */
  carrySheathed: '넣음',
  carryDrawn: '뽑음',
  /** 넣은 상태 첫 타 준비 — {name} = 발도·끌어내기 */
  carryReady: '{name} 준비',
  /** 조작법 줄 */
  controlCarry: 'F 넣기·뽑기',
  /** 튜토리얼 안내 패널 */
  tutTitle: '싸우는 법',
  tutMove: '이동',
  tutAttack: '공격 (커서 방향)',
  tutSecondary: '{secondary}',
  tutDash: '대쉬 — 대쉬 중엔 맞지 않는다',
  tutCarry: '넣기·뽑기 — 넣은 채 첫 타는 {name}',
  tutCarryPlain: '넣기·뽑기 — 넣은 채 첫 타가 세다',
  tutMore: 'Q 물약 · Shift 달리기 · E 상호작용 · M 지도 · Esc 뒤로·일시정지',
  tutClose: 'Enter·Esc·클릭 닫기',
  /** 튜토리얼 단계 카드 진행 (TUTORIAL_STEP index+1 / total) */
  tutStep: '{n}/{total}',
  /** 일시정지 일기장 항목 — '싸우는 법' 패널 다시 보기 (53라운드 Q50) */
  pauseHowTo: '싸우는 법',
  /** 적 등장 경고 */
  warnTitle: '주의',
  warnLine: '적이 다가온다',
  /** 키 이름 */
  keyLeftClick: '좌클릭',
  keyRightClick: '우클릭',
  keySpace: 'Space',
} as const;
export type R53TextKey = keyof typeof R53_TEXT;

export function r53Text(key: R53TextKey): string {
  return uiText('hud', key, R53_TEXT[key]);
}

/**
 * 56라운드 문구 (임시값, 도영 님 검수 대상): 무기 고유 자원·그로기 HUD (계약 §13).
 * 고유 자원 라벨은 시스템이 주는 `gauge.label` 을 그대로 쓴다 (비면 아래 기본 이름). 텍스트 팩 `hud.<키>` 가 있으면 그 문구.
 */
export const R56_TEXT = {
  /** 그로기 남은 시간 — {s} = 1.2 */
  groggyLeft: '그로기 {s}초',
  /** 숨 정밀 조준 중 */
  breathFocus: '집중',
  /** gauge.label 이 비었을 때 */
  gaugeKenki: '검기',
  gaugeGrudge: '울분',
  gaugeBrand: '낙인',
  gaugeBreath: '숨',
} as const;
export type R56TextKey = keyof typeof R56_TEXT;

export function r56Text(key: R56TextKey): string {
  return uiText('hud', key, R56_TEXT[key]);
}
