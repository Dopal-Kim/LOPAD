/**
 * 무기 공격 수단 표 (56라운드 Q21~Q24 · Q40~Q43 → 61라운드 P1 '4동사'). Phaser 의존 없음.
 * 모든 무기의 기본 동사는 넷: 좌 = 연격 · 우 = 시그니처 · 스페이스 = 대쉬(+대쉬 직후 좌 = 대쉬 공격) · 좌 홀드 = 고유 자원 기술.
 * 이 표는 그 동사 칸에 걸린 '전용 동작'과 계기(trigger)를 적는다. 1단 갈래 동작(slot branch)은 경로에 그 갈래가 있을 때만 열리고,
 * **같은 계기의 기본 동작을 대신한다**(예: 칼 선풍 = 좌 홀드가 발도 대신 회전 베기) — 그래서 갈래가 '새 동작 하나'로 체감된다.
 * 입력 쪽(`player/BasicMoves`·`BranchMoves`·`MeleeDriver`·`SecondaryDriver`)은 `pickMove(weapon, trigger, path)` 로 지금 열린 동작만 받는다.
 * 61라운드에 지운 계기: 넣은 채 홀드(F — 칼 발도는 좌 홀드로) · 가드 중 좌(버티기 → 중압 갈래의 가드 뗌) · 차지 중 스페이스(도약 →
 * 파쇄 갈래의 대쉬 공격) · 퍼펙트 가드 뗌 돌진(삭제) · 당긴 채 좌(화살비 → 좌 홀드). `live` 표시는 모두 구현돼 지웠다.
 */

/** 4동사 칸 (데이터 `weapons.<무기>.verbs` 와 같은 이름) */
export type VerbSlot = 'attack' | 'signature' | 'dash' | 'hold';

/** 입력 계기 */
export type MoveTrigger =
  /** 연격 n번째 타 (칼 3타 찌르기) */
  | 'comboFinisher'
  /** 좌클릭 홀드 (칼 발도·선풍·투구가르기 · 대검 차지 · 단검 난타 · 활 화살비·속사) */
  | 'attackHold'
  /** 대쉬 직후 좌클릭 (칼 일섬 · 대검 태클·도약 찍기 · 단검 부채꼴 투척) */
  | 'dashAttack'
  /** 패링 성공 직후 창 안 좌클릭 (칼 간파 반격 — 시그니처의 자연 후속) */
  | 'afterParry'
  /** 그림자 걸음 직후 좌클릭 (단검 등 뒤 치명 — 시그니처의 자연 후속) */
  | 'afterShadowStep'
  /** 가드로 막은 직후 우클릭을 뗌 (대검 버티기 올려베기 — 중압) */
  | 'guardRelease'
  /** 낙인 기폭 (단검 그림자 분신 교차 베기 — 쌍격) */
  | 'brandBurst'
  /** 완벽 놓기 화살 (활 관통 화살 — 저격) */
  | 'perfectRelease';

export interface MoveDef {
  id: string;
  weapon: string;
  name: string;
  /** basic = 기본기 · branch = 1단 갈래(branch 노드가 경로에 있을 때 — 같은 계기의 기본 동작을 대신) */
  slot: 'basic' | 'branch';
  branch?: string;
  /** 이 동작이 걸린 동사 칸 */
  verb: VerbSlot;
  trigger: MoveTrigger;
  /** 입력 창 등 임시값 (결정 문구의 선택지 설명값) */
  windowMs?: number;
}

/** 표 (같은 계기에서는 갈래가 기본을 대신하고, 같은 슬롯끼리는 앞이 우선) */
export const MOVES: readonly MoveDef[] = [
  // 칼: 좌 3연격(3타 찌르기) · 우 가드·패링(→ 간파 반격) · 대쉬 일섬 · 좌 홀드 발도(검기 소모)
  { id: 'thrust', weapon: 'katana', name: '찌르기', slot: 'basic', verb: 'attack', trigger: 'comboFinisher' },
  { id: 'issen', weapon: 'katana', name: '일섬', slot: 'basic', verb: 'dash', trigger: 'dashAttack' },
  {
    id: 'counter',
    weapon: 'katana',
    name: '간파 반격',
    slot: 'basic',
    verb: 'signature',
    trigger: 'afterParry',
    windowMs: 400,
  },
  { id: 'iai_draw', weapon: 'katana', name: '발도', slot: 'basic', verb: 'hold', trigger: 'attackHold' },
  {
    id: 'spin',
    weapon: 'katana',
    name: '회전 베기',
    slot: 'branch',
    branch: 'iai',
    verb: 'hold',
    trigger: 'attackHold',
  },
  {
    id: 'unblockable',
    weapon: 'katana',
    name: '투구가르기',
    slot: 'branch',
    branch: 'batto',
    verb: 'hold',
    trigger: 'attackHold',
  },
  // 대검: 좌 4타 순환 · 우 가드·퍼펙트 가드 · 대쉬 태클 · 좌 홀드 차지 내려찍기(울분 소모)
  {
    id: 'charge_swing',
    weapon: 'greatsword',
    name: '휘둘러 내리찍기',
    slot: 'basic',
    verb: 'hold',
    trigger: 'attackHold',
  },
  { id: 'tackle', weapon: 'greatsword', name: '어깨 태클', slot: 'basic', verb: 'dash', trigger: 'dashAttack' },
  {
    id: 'leap_slam',
    weapon: 'greatsword',
    name: '공중제비 도약 찍기',
    slot: 'branch',
    branch: 'crush',
    verb: 'dash',
    trigger: 'dashAttack',
  },
  {
    id: 'brace_upswing',
    weapon: 'greatsword',
    name: '버티기 올려베기',
    slot: 'branch',
    branch: 'weight',
    verb: 'signature',
    trigger: 'guardRelease',
  },
  // 단검: 좌 3찌르기 · 우 그림자 걸음(→ 등 뒤 치명) · 대쉬 찌르기 · 좌 홀드 고속 난타
  {
    id: 'backstab',
    weapon: 'dagger',
    name: '등 뒤 치명 찌르기',
    slot: 'basic',
    verb: 'signature',
    trigger: 'afterShadowStep',
  },
  { id: 'flurry', weapon: 'dagger', name: '고속 난타', slot: 'basic', verb: 'hold', trigger: 'attackHold' },
  {
    id: 'fan_throw',
    weapon: 'dagger',
    name: '부채꼴 투척',
    slot: 'branch',
    branch: 'gale',
    verb: 'dash',
    trigger: 'dashAttack',
  },
  {
    id: 'clone_cross',
    weapon: 'dagger',
    name: '그림자 분신 교차 베기',
    slot: 'branch',
    branch: 'twin',
    verb: 'signature',
    trigger: 'brandBurst',
  },
  // 활: 좌 짧게 쏘기 · 우 당겨 쏘기·완벽 놓기 · 대쉬 사격 · 좌 홀드 화살비(탄창 3)
  { id: 'arrow_rain', weapon: 'bow', name: '화살비', slot: 'basic', verb: 'hold', trigger: 'attackHold' },
  {
    id: 'rapid_volley',
    weapon: 'bow',
    name: '속사 연사',
    slot: 'branch',
    branch: 'rapid',
    verb: 'hold',
    trigger: 'attackHold',
  },
  {
    id: 'pierce_arrow',
    weapon: 'bow',
    name: '관통 화살',
    slot: 'branch',
    branch: 'snipe',
    verb: 'signature',
    trigger: 'perfectRelease',
  },
];

/**
 * 이 무기·갈래 경로에서 열린 동작. 갈래 동작이 열린 계기는 그 계기의 기본 동작을 뺀다 (갈래가 동사를 바꾼다)
 */
export function availableMoves(weapon: string, path: readonly string[]): MoveDef[] {
  const open = MOVES.filter(
    (m) => m.weapon === weapon && (m.slot === 'basic' || (m.branch !== undefined && path.includes(m.branch))),
  );
  const replaced = new Set(open.filter((m) => m.slot === 'branch').map((m) => m.trigger));
  return open.filter((m) => m.slot === 'branch' || !replaced.has(m.trigger));
}

/**
 * 계기에 맞는 열린 동작 (없으면 null). `require` 는 동작별 추가 조건 — 호출 쪽이 판단
 */
export function pickMove(
  weapon: string,
  trigger: MoveTrigger,
  path: readonly string[],
  require: (m: MoveDef) => boolean = () => true,
): MoveDef | null {
  for (const m of availableMoves(weapon, path)) if (m.trigger === trigger && require(m)) return m;
  return null;
}
