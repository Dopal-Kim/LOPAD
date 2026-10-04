/**
 * 48·55라운드 근접 연격 데이터 형식 (data/weapons.json `combo`). 55라운드 계약 art-assets §17 새 연격 규격:
 * 타마다 판정 모양(`hitShape`)·내딛기(`step`)·막타(`heavy`)·후속 판정(`followUps` — 칼 잔상 베기·차지 충격파 링),
 * 연격 순환(`loop` — 대검 H1→V→H2→V…), 관성(`momentum`), 홀드 차지(`charge`), 그림 이름 표(`art`).
 * 각도 표기: 조준 방향 = 0°, 화면 기준 시계 방향 + (오른쪽 조준이면 + = 아래). 왼쪽 조준은 좌우 반전(그림과 같은 규칙).
 * R = 현재 판정 반경(`radiusPx` × 갈래·강화 배율 × 타·대쉬 크기 배율), 배율·비율은 R 기준.
 */

/** 판정 모양 (§17): arc = 내반경 있는 호(비대칭 대각 포함) · wedge = 좁은 쐐기(+끝점 충격원) · rect = 찌르기 · ring = 충격파 고리 */
export type HitShapeSpec = ArcShapeSpec | WedgeShapeSpec | RectShapeSpec | RingShapeSpec;

export interface ArcShapeSpec {
  kind: 'arc';
  /** 휘두름 시작각 → 끝각 (도, 조준 기준). 시계 방향 휘두름이면 from < to */
  fromDeg: number;
  toDeg: number;
  /** 내반경 / 반경 (0 = 부채꼴, 0.3 = 몸 가까이는 비는 초승달) */
  innerRatio?: number;
  /** 반경 = R × radiusMult (없으면 1) */
  radiusMult?: number;
}

export interface WedgeShapeSpec {
  kind: 'wedge';
  /** 쐐기 폭 (도, 조준 방향 가운데) */
  widthDeg: number;
  /** 길이 = R × lengthMult */
  lengthMult: number;
  /** 쐐기 가운데 방향 (도, 없으면 0) */
  angleDeg?: number;
  /** 끝점 충격원: 반지름 = R × radiusRatio, 중심 = 쐐기 끝(없으면) 또는 R × atMult */
  impactCircle?: { radiusRatio: number; atMult?: number };
}

export interface RectShapeSpec {
  kind: 'rect';
  /** 길이 = R × lengthMult, 폭 = R × widthMult */
  lengthMult: number;
  widthMult: number;
  angleDeg?: number;
  /** 몸에서 떨어진 시작 거리 = R × fromMult */
  fromMult?: number;
}

export interface RingShapeSpec {
  kind: 'ring';
  /** 바깥 반지름 = R × radiusMult, 안 반지름 = 바깥 × innerRatio */
  radiusMult: number;
  innerRatio?: number;
  /** 중심 = 원점에서 조준 방향 R × atMult (없으면 원점) */
  atMult?: number;
}

/** Q21 내딛기: 방향키를 누를 때만 조준 방향으로 px 를 ms 동안 (판정 프레임 시작에 끝나도록) */
export interface ComboStepDef {
  px: number;
  ms: number;
}

/**
 * 한 타 뒤에 따로 붙는 판정 (§17 칼 3타 잔상 베기 — 150ms 뒤 같은 호 50% · 대검 차지 3단 충격파 링).
 * 지연은 씬 시계(히트스톱 동안 멈춤)
 */
export interface ComboFollowUpDef {
  /** 디버그·이펙트 구분 이름 (echo · ring) */
  id: string;
  delayMs: number;
  /** 본 타 피해 배율에 곱한다 */
  damageMult: number;
  /** 판정 모양 (없으면 본 타와 같은 모양) */
  hitShape?: HitShapeSpec;
  /** 원점: origin = 그때 몸 중심(기본) · impact = 본 타 쐐기의 끝점 충격원 중심 */
  at?: 'origin' | 'impact';
  /** 판정 유지 ms (없으면 본 타) */
  activeMs?: number;
  /** 그림 이름 표(`combo.art`) 키 — 전용 이펙트 (없으면 플레이스홀더) */
  art?: string;
}

/** 48라운드 Q2: 근접 연격 한 타 (임시값, data/weapons.json `combo.hits`) */
export interface ComboHitDef {
  /** 이 타의 피해 배율 (무기·진화 배율에 곱한다) */
  damageMult: number;
  /** 이 타의 판정 크기 배율 */
  sizeMult: number;
  /** 몸·무기 애니 길이 ms (공격 애니를 이 시간에 맞춘다) */
  durationMs: number;
  /** 다음 타를 시작할 수 있는 시각 (이 타 시작부터 ms). 마지막 타(순환 아님)는 durationMs 와 같게 */
  cancelFromMs: number;
  /** 판정이 살아 있는 시간 ms */
  activeMs: number;
  /**
   * 51라운드 Q3 템포: 판정 프레임(몸 시트 hitFrames[0], 없으면 impactFrame) 시작 ms. 있으면 예비 동작(앞 구간)과
   * 휘두름·여운(뒤 구간)을 따로 늘여 판정이 이 시각에 오게 한다. 없으면 시트 전체를 durationMs 에 균일 맞춤
   */
  hitAtMs?: number;
  /** 55라운드 §17: 그림 이름 표(`combo.art`) 키. 없으면 `combo<n>` (n = 타 번호) */
  art?: string;
  /** 55라운드 §17: 이 타의 판정 모양. 없으면 연격 공통 모양(`combo.shape` + 아트 메모 — 단검 찌르기 등 기존 규칙) */
  hitShape?: HitShapeSpec;
  /** 55라운드 Q21: 내딛기 (방향키를 누를 때만) */
  step?: ComboStepDef;
  /**
   * 55라운드 막타(heavy 적중 스파크·히트스톱 ×HEAVY_MULT·흔들림·충격파 갈래). 없으면 순환이 아닌 연격의 마지막 타.
   * 기력이 바닥나면 막타는 1타로 바뀐다
   */
  heavy?: boolean;
  /** 55라운드 §17: 뒤따르는 판정 (칼 잔상 베기) */
  followUps?: ComboFollowUpDef[];
  /** 56라운드: 일반 휘두름 대신 전용 동작 (칼 3타 일섬 — 무기 데이터 `issen`). 공격 수단 표(`systems/weapon/moves`)의 id */
  move?: string;
}

/** 근접 판정 모양: arc = 몸 중심 부채꼴, thrust = 앞으로 뻗는 직사각형(찌르기) — 타별 `hitShape` 가 없을 때 */
export type ComboShape = 'arc' | 'thrust';

/**
 * 55라운드 §17 그림 이름 표 (데이터 한 곳에서 시트 이름을 매핑): 키 → 후보 동작 이름(앞이 우선, 로드된 첫 시트).
 * 몸 `player_<무기>_<이름>` · 무기 `<무기>_<이름>`(몸을 따라감) · 휘두름 이펙트 `fx/<무기>_<이름>`.
 * 아트 명세가 오면 새 이름을 앞에 넣기만 하면 된다. 뒤쪽(기존 시트) 후보는 그림 메모(판정 모양·다음 타 허용 프레임)를 쓰지 않는다
 */
export interface ComboArtEntry {
  /** 몸(+무기 오버레이) 후보 */
  body?: string[];
  /** 휘두름 이펙트 후보 (빈 배열 = 휘두름 이펙트 없음) */
  fx?: string[];
  /** 끝점 충격원 위치의 바닥 충격 이펙트 후보 (내려찍기) */
  impactFx?: string[];
  /** 차지 단계에 닿을 때 몸에 붙여 재생할 번쩍임 이펙트 후보 (없으면 틴트 번쩍임만) */
  flashFx?: string[];
  /** 몸 시트에 holdFrame 이 없을 때 차지 유지 열 */
  holdColumn?: number;
  /** 56라운드 Q5: 판정 순간 땅 균열 (fx 후보 · 행 s·m·l · 관성 최대일 때 행) */
  crackFx?: string[];
  crackRow?: string;
  crackRowAtMax?: string;
}

/** 55라운드 Q23 대검 관성: 이어지는 타마다 공속 +perHit (최대 max), idleResetMs 무입력·피격 시 초기화 */
export interface ComboMomentumDef {
  perHit: number;
  max: number;
  idleResetMs: number;
  /** 최대일 때 내려찍기(쐐기) 끝점 충격원 반지름 배율 */
  maxImpactMult: number;
}

/** 55라운드 Q22 대검 홀드 차지 (좌클릭 홀드) — 떼면 차지 내려찍기 */
export interface ComboChargeStageDef {
  /** 누르기 시작(또는 행동 가능해진 때)부터 이 단계까지 ms */
  atMs: number;
  /** 쐐기 길이 배율 (hitShape.lengthMult 를 대신) */
  lengthMult: number;
  /** 피해 배율 (hit.damageMult 에 곱한다) */
  damageMult: number;
  /** 이 단계에 붙는 후속 판정 (3단 충격파 링) */
  followUps?: ComboFollowUpDef[];
  /** 이 단계 차지 내려찍기의 그림 키 (없으면 charge.hit.art) — 단계별 시트·번쩍임(flashFx) */
  art?: string;
  /** 끝점 충격원 반지름 배율 (바닥 충격 그림 배율과 같게 — 아트 제안 1.0/1.15/1.3) */
  impactMult?: number;
}

export interface ComboChargeDef {
  /** 이 시간 넘게 누르고 있으면 차지(짧게 누르면 일반 연격) — 임시값 */
  holdMs: number;
  /** 차지 중 이동 배율 */
  moveMult: number;
  stages: ComboChargeStageDef[];
  /** 차지 내려찍기 한 타 (모양 = wedge, 길이는 단계 배율) */
  hit: ComboHitDef;
  /** 차지 유지 자세 그림 키 (`combo.art`) */
  holdArt?: string;
  /** 58라운드 Q3: 휘둘러 내리찍은 자리에서 커서까지 이어지는 균열 (없으면 내려찍기만) */
  crackLine?: ComboCrackLineDef;
}

/**
 * 58라운드 Q3 대검 차지 균열 (꽂아내리기 대체): 찍은 자리 → 조준 방향으로 칸 수 = min(단계 최대, 커서까지 반올림(최소 1), 벽까지 내림).
 * 앞머리가 지나간 칸만 판정 (적마다 1회)
 */
export interface ComboCrackLineDef {
  /** 그림 이름 표 키 — fx = 칸 수별 균열 선(1칸부터 순서) · crackFx(그림이 없을 때 칸마다 놓는 균열) · crackRow */
  art: string;
  /** 차지 단계(1..) → 최대 칸 수 */
  tilesByStage: number[];
  tilePx: number;
  /** 판정 반폭 (월드 px, 갈래·강화 배율을 곱한다) · 피해 배율(차지 피해에 곱한다) */
  halfWidthPx: number;
  damageMult: number;
  /** 앞머리 속도 (fx 메모 frontPxByFrame 이 없을 때 한 칸당 ms) */
  msPerTile: number;
  /** 대체 그림: 칸마다 놓는 균열 배율 */
  tileCrackScale: number;
}

/** 48라운드 Q2: 무기별 연격 상태 머신 파라미터 (임시값) */
export interface ComboDef {
  shape: ComboShape;
  /** arc: 부채꼴 각도(도) · 반경 px (없으면 hitbox.reach + hitbox.width / 2). 진화·강화 배율을 곱한다 */
  arcDeg?: number;
  radiusPx?: number;
  /** thrust: 기본 길이·폭 px (진화·강화 배율을 곱한다) */
  thrust?: { lengthPx: number; widthPx: number };
  /** 다음 타 허용 전에 누른 입력을 기억하는 시간 ms */
  bufferMs: number;
  /** 한 타가 끝나고(durationMs) 이 시간 안에 다음 타가 없으면 1타로 돌아간다 */
  resetMs: number;
  /** 마지막 타가 끝난 뒤 새 연격까지 추가 대기 ms (순환 연격은 쓰지 않음) */
  finisherRecoverMs: number;
  hits: ComboHitDef[];
  /** 55라운드 Q18 대검 관성 순환: 마지막 타 다음은 다시 1타 (끊김 없이 교대) */
  loop?: boolean;
  /** 55라운드 §17 그림 이름 표 */
  art?: Record<string, ComboArtEntry>;
  momentum?: ComboMomentumDef;
  charge?: ComboChargeDef;
  /**
   * 55라운드 §17 왼쪽 조준 변환: mirror = 좌우 반전(48라운드 그림 규칙, 기본) · rotate = 180° 회전(새 시트 `dirTransform: rotate`).
   * 타별 hitShape 판정·칼끝 리본 폴백에 적용 (확인 전 임시)
   */
  leftTransform?: 'mirror' | 'rotate';
}
