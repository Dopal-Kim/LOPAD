/**
 * 56라운드 무기 피드백 데이터 형식 (data/weapons.json — 결정 2026-10-04-round-56 Q1~Q39). 모든 수치는 임시값(보고서 표).
 * - 무기별 고유 자원 `gauge`: 칼 검기(劍氣) 3단 · 대검 울분(鬱憤) · 단검 낙인(烙印) · 활 숨(呼吸) (Q13~Q20)
 * - 칼 일섬 `issen` (Q2·Q3·Q28·Q29 — 58 Q1 대쉬 일섬) · (대검 꽂아내리기 `plunge` 는 58 Q11 로 삭제)
 * - 활 우클릭 당김·놓기 `draw` (Q9·Q20) — 계약 art §18(56라운드) 시트 메모와 함께 쓴다
 */

/** 칼 검기 3단: 타격으로 조금씩 · 패링 성공 시 1단 즉시 · 61라운드: 좌 홀드 발도가 전부 소모해 강화, critAtStages 이상이면 확정 치명 */
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
  /** 발도가 소모한 단마다 피해 배율 + (1 + 단 × 값) */
  damagePerStage: number;
  /** 이 단 이상을 소모하면 확정 치명 (옛 F 넣기 '발도 치명'을 흡수) */
  critAtStages: number;
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

/** 단검 낙인: 같은 적 타격마다 표식(등 뒤 2) · 그림자 걸음으로 그 적 뒤 → 전부 폭발 · 가속 단계가 획득을 늘린다 (61라운드: 과열 폭발·식힘 삭제) */
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
  /** 가속 단계마다 표식 획득 배율 + 값 (빨리 찌를수록 낙인이 더 빨리) */
  tempoGainPerStage: number;
  /** 폭발 피해 = 공격력 × 표식 수 × 값 */
  burstDamagePerMark: number;
  /** 마지막 표식 뒤 이 시간이 지나면 그 적의 표식이 사라진다 */
  lifeMs: number;
  /** 56라운드 Q59: 그림자 걸음 착지 뒤 이 시간 동안은 방향과 무관하게 등 뒤로 인정 (없으면 0) */
  backAfterShadowStepMs?: number;
}

/** 활 숨: 완벽 놓기마다 회복 · 가득 차면 다음 당김이 짧은 감속 정밀 조준 (Q17) — 61라운드: 저격 갈래에서만 */
export interface BreathGaugeDef {
  kind: 'breath';
  label: string;
  /** 이 1단 갈래가 경로에 있을 때만 켠다 (없으면 늘) */
  branch?: string;
  max: number;
  perfectGain: number;
  /** 집중(감속 정밀 조준) 시간 · 그동안 물리 배속(0.4 = 40% 속도) · 완벽 놓기 창 배율 */
  focusMs: number;
  focusTimeScale: number;
  focusPerfectWindowMult: number;
}

export type WeaponGaugeDef = KenkiGaugeDef | GrudgeGaugeDef | BrandGaugeDef | BreathGaugeDef;

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
  /** 일섬 선 시트 (fx id, t1~t4 순서) · 분신 없는 선 접미 (61라운드: 일섬은 검기를 쓰지 않아 늘 분신 없는 선) */
  lineSheets: string[];
  soloSuffix: string;
  /** 분신 없는 선 끝 폭발(연출만) — 선 시트 시각 */
  burstAtLineMs: number;
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
