/**
 * 56라운드 무기 피드백 데이터 형식 (data/weapons.json — 결정 2026-10-04-round-56 Q1~Q39). 모든 수치는 임시값(보고서 표).
 * - 무기별 고유 자원 `gauge`: 칼 검기(劍氣) 3단 · 대검 울분(鬱憤) · 단검 낙인(烙印) · 활 숨(呼吸) (Q13~Q20)
 * - 칼 3타 일섬 `issen` (Q2·Q3·Q28·Q29) · 대검 개성 발현 후 차지 = 꽂아내리기 `plunge` (Q10)
 * - 활 우클릭 당김·놓기 `draw` (Q9·Q20) — 계약 art §18(56라운드) 시트 메모와 함께 쓴다
 */

/** 칼 검기 3단: 타격으로 조금씩 · 패링 성공 시 1단 즉시 · 일섬이 전부 소모해 강화, 3단이면 그림자 분신 */
export interface KenkiGaugeDef {
  kind: 'kenki';
  label: string;
  /** 단 수 (3) · 한 단의 양 */
  stages: number;
  perStage: number;
  /** 근접 적중 1회(한 휘두름에 여러 적이어도 1회)당 */
  gainPerHit: number;
  /** 패링 성공 시 즉시 채우는 단 수 */
  parryGainStages: number;
  /** 일섬이 소모한 단마다 피해 배율 + (1 + 단 × 값) */
  issenDamagePerStage: number;
  /** 이 단 이상을 소모하면 그림자 분신 (Q28: 3단만) */
  cloneAtStages: number;
}

/** 대검 울분: 가드로 막은 피해가 쌓임(퍼펙트 2배, 그로기 중 가드가 가장 많이) · 차지 내려찍기·꽂아내리기가 전부 소모 */
export interface GrudgeGaugeDef {
  kind: 'grudge';
  label: string;
  max: number;
  /** 가드로 막은(줄어든) 피해 × 값 만큼 쌓인다 */
  blockGainMult: number;
  /** 퍼펙트 가드 배율 (원래 피해 전부를 막은 것으로 보고 × 값) */
  perfectMult: number;
  /** 그로기 중 가드 배율 */
  groggyMult: number;
  /** 가득일 때 차지 피해 배율 + 값 (비율만큼) · 판정 길이 배율 + 값 */
  slamDamageBonus: number;
  slamRangeBonus: number;
}

/** 단검 낙인: 같은 적 타격마다 표식(등 뒤 2) · 그림자 걸음으로 그 적 뒤 → 전부 폭발 · 과열 연동 (Q16·Q18) */
export interface BrandGaugeDef {
  kind: 'brand';
  label: string;
  /** 적 하나당 최대 표식 */
  max: number;
  perHit: number;
  /** 등 뒤에서 맞히면 */
  backGain: number;
  /** 등 뒤 판정: 적이 바라보는 방향과 공격 방향 사이 각이 이 값(도) 이하 */
  backAngleDeg: number;
  /** 과열 단계마다 표식 획득 배율 + 값 (과열이 차면 낙인이 더 빨리) */
  heatGainPerStage: number;
  /** 폭발 피해 = 공격력 × 표식 수 × 값 */
  burstDamagePerMark: number;
  /** 과열 100%: 이 반경(칸) 안의 낙인 일괄 폭발 */
  overheatBurstRadiusTiles: number;
  /** 식는 동안(과열 냉각) 공격 속도·이동 배율 — 공격은 막지 않는다 (Q18 '잠깐 느려짐') */
  coolingSpeedMult: number;
  coolingMoveMult: number;
  /** 마지막 표식 뒤 이 시간이 지나면 그 적의 표식이 사라진다 */
  lifeMs: number;
  /** 56라운드 Q59: 그림자 걸음 착지 뒤 이 시간 동안은 방향과 무관하게 등 뒤로 인정 (없으면 0) */
  backAfterShadowStepMs?: number;
}

/** 활 숨: 완벽 놓기마다 회복 · 가득 차면 다음 당김이 짧은 감속 정밀 조준 (Q17) */
export interface BreathGaugeDef {
  kind: 'breath';
  label: string;
  max: number;
  perfectGain: number;
  /** 집중(감속 정밀 조준) 시간 · 그동안 물리 배속(0.4 = 40% 속도) · 완벽 놓기 창 배율 */
  focusMs: number;
  focusTimeScale: number;
  focusPerfectWindowMult: number;
}

export type WeaponGaugeDef = KenkiGaugeDef | GrudgeGaugeDef | BrandGaugeDef | BreathGaugeDef;
export type WeaponGaugeKind = WeaponGaugeDef['kind'];

/** 칼 3타 일섬 (몸 시트 player_katana_issen 메모가 기준 — 여기는 시스템 값). 길이는 월드 px */
export interface IssenDef {
  /** 돌진 시작·끝 (몸 시트 시각) · 거리 · 한 칸 */
  dashStartMs: number;
  dashEndMs: number;
  distancePx: number;
  tilePx: number;
  /** 판정 구간 (몸 시트 시각) */
  hitFromMs: number;
  hitToMs: number;
  /** 판정 직사각형: 출발 원점 뒤 backPx 부터 이동한 거리 + extraPx 까지, 폭 widthPx */
  hitBackPx: number;
  hitExtraPx: number;
  hitWidthPx: number;
  /** 일섬 선 시트 (fx id, t1~t4 순서) · 분신 없는 선 접미 */
  lineSheets: string[];
  soloSuffix: string;
  /** 분신 없는 선 끝 폭발(연출만) — 선 시트 시각 */
  burstAtLineMs: number;
  /** 그림자 분신 (검기 3단 소모 시에만, Q28): 몸 기준 출발 · 이동 시간 · 피해 시각(도착 때 선 전체 1회, Q29) · 피해 배율 */
  shadow: { sheet: string; startAtMs: number; travelMs: number; hitAtMs: number; damageScale: number };
}

/** 대검 꽂아내리기 (개성 발현 후 차지, Q10): 휘두르지 않고 칼을 땅에 꽂아 마우스 방향 충격파 + 균열 */
export interface PlungeDef {
  /** 그림 이름 표(`combo.art`) 키 — 몸 greatsword_charge_plunge */
  art: string;
  durationMs: number;
  hitAtMs: number;
  /** 꽂힌 자리 작은 충격원: 반지름 = R × 값 · 피해 배율 */
  plantRadiusRatio: number;
  plantDamageMult: number;
  /** 충격파 (fx greatsword_plunge_wave, 마우스 방향 직사각형): 차지 단계별 길이 = R × 값 · 반폭 월드 px · 피해 배율 · 앞머리 진행 ms(시트 없을 때) */
  wave: {
    sheet: string;
    lengthMultByStage: number[];
    halfWidthPx: number;
    damageMult: number;
    travelMs: number;
  };
  /** 균열 행 (greatsword_ground_crack s·m·l) */
  crackRow: string;
}

/** 활 우클릭 당김·놓기 (Q9·Q20): 누르면 당김, 떼면 발사, 자동 발사 없음 */
export interface BowDrawDef {
  /** 가득까지 ms (secondary.chargeMs 와 같게 — 진행 프레임 f0~5) */
  fullMs: number;
  /** 가득 직후 완벽 놓기 창 */
  perfectWindowMs: number;
  /** 일찍 놓은 약한 화살 피해 배율 (조준 사격 배율 대신) · 관통 없음 */
  weakDamageMult: number;
  /** 완벽 놓기 피해 배율 (조준 사격 배율에 곱한다) */
  perfectDamageMult: number;
  /** 가득 뒤 이만큼 더 쥐면 흔들림 (strainLoop) — 위력 감소·조준선 흔들림 */
  strainAfterMs: number;
  /** 흔들림이 최대가 되는 시간 · 그때 위력 배율 · 조준 흔들림 최대 각(도) */
  strainRampMs: number;
  strainMinMult: number;
  strainShakeDeg: number;
  /** 약한 화살 시트 (없으면 기본 화살을 어둡게) · 어둡게 틴트 */
  weakArrowSheet: string;
  weakArrowTint: number;
  /** 놓기 동작 길이 (player_bow_release, 시트가 없으면) */
  releaseMs: number;
  /** 56라운드 Q58: 이보다 짧게 누른 탭은 취소 (화살·탄창 소모 없음, 없으면 0) */
  tapCancelMs?: number;
}
