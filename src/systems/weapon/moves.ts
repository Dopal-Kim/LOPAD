/**
 * 56라운드 공격 수단 표 (Q21~Q24 키아트 · Q40~Q43 입력·조건). Phaser 의존 없음.
 * 무기마다 '기본기'와 '갈래(1단 노드에서 열림)' 수단을 한 곳에 적고, 입력 쪽(MeleeDriver·SecondaryDriver)은
 * `pickMove(weapon, trigger, ctx)` 로 지금 조건에 맞는 **구현된** 수단만 받는다. 아직 그림이 없는 수단은 `live: false` —
 * 아트 시트가 오면 live 로 바꾸고 실행기를 붙인다. 56라운드 2단계: 기본기 9종 live (실행기 `player/BasicMoves`·`katanaMoves`·
 * `greatswordMoves`·`daggerMoves`·`bowRain`, 수치 data `moves`). 갈래 수단(회전 베기·가드 불가 내려베기·부채꼴 투척·분신 교차 베기·
 * 속사 연사·관통 화살)은 그림 대기. 57라운드: 갈래 수단 5종은 기존 시트·플레이스홀더로 동작 (입력 `player/BranchMoves`,
 * 판정 `scenes/game/build/BranchStrikes`) — 관통 화살은 56 Q9 '가득 이상 관통'과 겹쳐 대기(인터뷰).
 */

/** 입력 계기 (Q40~Q43 결정 문구 그대로) */
export type MoveTrigger =
  /** 연격 n번째 타 (칼 3타 찌르기) */
  | 'comboFinisher'
  /** 차지를 떼서 (대검 휘둘러 내리찍기 + 균열) */
  | 'chargeRelease'
  /** 패링 성공 직후 창 안 좌클릭 (칼 간파 반격) */
  | 'afterParry'
  /** F 로 넣은 채 좌클릭을 눌렀다 뗌 (칼 대치 일격) */
  | 'sheathedHoldRelease'
  /** 대쉬 공격 자리 (대검 어깨 태클 · 58라운드 칼 일섬) */
  | 'dashAttack'
  /** 가드 중 좌클릭 (대검 버티기 올려베기) */
  | 'guardAttack'
  /** 차지 중 스페이스 (대검 공중제비 도약 찍기) */
  | 'chargeDash'
  /** 퍼펙트 가드 직후 우클릭을 뗌 (대검 막다가 떼면 돌진) */
  | 'perfectGuardRelease'
  /** 그림자 걸음 직후 좌클릭 (단검 등 뒤 치명 찌르기) */
  | 'afterShadowStep'
  /** 좌클릭 홀드 (단검 고속 난타 · 활 속사 연사) */
  | 'attackHold'
  /** 우클릭으로 당긴 채 좌클릭 (활 화살비) */
  | 'drawAttack'
  /** 기본 공격을 대신 (갈래가 바꾸는 모양 — 회전 베기·부채꼴 투척 등) */
  | 'branchAttack'
  /** 낙인 기폭 (단검 그림자 분신 교차 베기) */
  | 'brandBurst'
  /** 완벽 놓기 화살 (활 관통 화살) */
  | 'perfectRelease';

export interface MoveDef {
  id: string;
  weapon: string;
  name: string;
  /** basic = 기본기 · branch = 갈래(branch 노드가 경로에 있을 때) */
  slot: 'basic' | 'branch';
  branch?: string;
  trigger: MoveTrigger;
  /** 입력 창 등 임시값 (결정 문구의 선택지 설명값) */
  windowMs?: number;
  /** 구현됨 (그림·실행기가 있음) */
  live: boolean;
}

/** 표 (순서 = 같은 계기에서 우선) */
export const MOVES: readonly MoveDef[] = [
  // 칼 (Q40: 기본기 2 + 갈래 2, 기본 포함 일섬·분신)
  // 58라운드 Q1: 3연격 3타 = 찌르기(검기 소모 강화), 일섬은 대쉬 공격으로만
  { id: 'thrust', weapon: 'katana', name: '찌르기', slot: 'basic', trigger: 'comboFinisher', live: true },
  { id: 'issen', weapon: 'katana', name: '일섬', slot: 'basic', trigger: 'dashAttack', live: true },
  {
    id: 'counter',
    weapon: 'katana',
    name: '간파 반격',
    slot: 'basic',
    trigger: 'afterParry',
    windowMs: 400,
    live: true,
  },
  { id: 'iai_draw', weapon: 'katana', name: '대치 일격', slot: 'basic', trigger: 'sheathedHoldRelease', live: true },
  {
    id: 'spin',
    weapon: 'katana',
    name: '회전 베기',
    slot: 'branch',
    branch: 'iai',
    trigger: 'branchAttack',
    live: true,
  },
  {
    id: 'unblockable',
    weapon: 'katana',
    name: '가드 불가 내려베기',
    slot: 'branch',
    branch: 'batto',
    trigger: 'branchAttack',
    live: true,
  },
  // 대검 (Q41: 모두 기본기, 기본 포함 모아 내려찍기·땅 꽂기 충격파)
  // 58라운드 Q3: 차지 = 휘둘러 내리찍기 + 균열이 커서까지 (어느 갈래든 — 56라운드 꽂아내리기 대체)
  {
    id: 'charge_swing',
    weapon: 'greatsword',
    name: '휘둘러 내리찍기',
    slot: 'basic',
    trigger: 'chargeRelease',
    live: true,
  },
  { id: 'tackle', weapon: 'greatsword', name: '어깨 태클', slot: 'basic', trigger: 'dashAttack', live: true },
  {
    id: 'brace_upswing',
    weapon: 'greatsword',
    name: '버티기 올려베기',
    slot: 'basic',
    trigger: 'guardAttack',
    live: true,
  },
  {
    id: 'leap_slam',
    weapon: 'greatsword',
    name: '공중제비 도약 찍기',
    slot: 'basic',
    trigger: 'chargeDash',
    live: true,
  },
  {
    id: 'guard_rush',
    weapon: 'greatsword',
    name: '막다가 떼면 돌진',
    slot: 'basic',
    trigger: 'perfectGuardRelease',
    live: true,
  },
  // 단검 (Q42: 기본기 2 + 갈래 2, 기본 포함 그림자 걸음·낙인 기폭)
  {
    id: 'backstab',
    weapon: 'dagger',
    name: '등 뒤 치명 찌르기',
    slot: 'basic',
    trigger: 'afterShadowStep',
    live: true,
  },
  { id: 'flurry', weapon: 'dagger', name: '고속 난타', slot: 'basic', trigger: 'attackHold', live: true },
  {
    id: 'fan_throw',
    weapon: 'dagger',
    name: '부채꼴 투척',
    slot: 'branch',
    branch: 'gale',
    trigger: 'dashAttack',
    live: true,
  },
  {
    id: 'clone_cross',
    weapon: 'dagger',
    name: '그림자 분신 교차 베기',
    slot: 'branch',
    branch: 'twin',
    trigger: 'brandBurst',
    live: true,
  },
  // 활 (Q43: 화살비만 기본기, 나머지 갈래)
  { id: 'arrow_rain', weapon: 'bow', name: '화살비', slot: 'basic', trigger: 'drawAttack', live: true },
  {
    id: 'rapid_volley',
    weapon: 'bow',
    name: '속사 연사',
    slot: 'branch',
    branch: 'rapid',
    trigger: 'attackHold',
    live: true,
  },
  {
    id: 'pierce_arrow',
    weapon: 'bow',
    name: '관통 화살',
    slot: 'branch',
    branch: 'snipe',
    trigger: 'perfectRelease',
    live: false,
  },
];

/** 이 무기·갈래 경로에서 열린 수단 (구현 여부와 무관 — 디버그·도감용) */
export function availableMoves(weapon: string, path: readonly string[]): MoveDef[] {
  return MOVES.filter(
    (m) => m.weapon === weapon && (m.slot === 'basic' || (m.branch !== undefined && path.includes(m.branch))),
  );
}

/**
 * 계기에 맞는 구현된 수단 (없으면 null). `require` 는 수단별 추가 조건 — 호출 쪽이 판단
 */
export function pickMove(
  weapon: string,
  trigger: MoveTrigger,
  path: readonly string[],
  require: (m: MoveDef) => boolean = () => true,
): MoveDef | null {
  for (const m of availableMoves(weapon, path)) if (m.trigger === trigger && m.live && require(m)) return m;
  return null;
}
