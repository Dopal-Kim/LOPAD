/**
 * 51·52라운드 (계약 art §10) 활 갈래 시트 고르기 · 저격 단계. Phaser 의존 없음.
 * 1단 갈래 시트: 화살 `fx/<무기>_arrow[_aimed]_<갈래>` · 발사 섬광 `fx/<무기>_muzzle_<갈래>` · 조준선 `fx/aim_line_<갈래>` ·
 * 저격 꼬리 = 화살 JSON `tailSheets`. 파일이 없으면 기본 시트로 대체(호출 쪽).
 * 근접 갈래 이펙트(`<무기>_combo<n>_<갈래>`)·2단 색 교체(secondaryVariants)·단검 heatVariants 는 53라운드 무기 이펙트 v3 와
 * 함께 연결 — `fxVariants`.
 */
import { arrowFxId, type FxWeaponShape } from './fxIds';

/**
 * 갈래 메모 필드 (SheetJson 에 섞여 온다): 저격 화살의 단계별 꼬리 시트 · 2단 갈래/가열 변주(형식 검사는 `fxVariants`)
 */
export interface BranchSheetFields {
  tailSheets?: string[];
  secondaryVariants?: unknown;
  heatVariants?: unknown;
}

/** 'fx/<이름>' → '<이름>' */
export function stripFxPrefix(ref: string): string {
  return ref.startsWith('fx/') ? ref.slice(3) : ref;
}

/** 활 1단 갈래 화살 `<무기>_arrow_<갈래>` / `<무기>_arrow_aimed_<갈래>` */
export function branchArrowFxId(weaponId: string, aimed: boolean, branch: string): string {
  return `${arrowFxId(weaponId, aimed)}_${branch}`;
}

/** 활 1단 갈래 발사 섬광 `<무기>_muzzle_<갈래>` (spawn arrow_spawn) */
export function muzzleFxId(weaponId: string, branch: string): string {
  return `${weaponId}_muzzle_${branch}`;
}

/** 조준선 `aim_line` / 갈래 조준선 `aim_line_<갈래>` */
export function aimLineFxId(branch?: string | null): string {
  return branch ? `aim_line_${branch}` : 'aim_line';
}

/** 저격 꼬리 후보 `<화살>_lv<k>` (로드 목록용 — 실제 고르기는 JSON tailSheets 우선) */
export function tailFxIds(arrowId: string, levels = 3): string[] {
  return Array.from({ length: levels }, (_, i) => `${arrowId}_lv${i + 1}`);
}

/** 활 1단 갈래가 정한 시트 목록 (로드용): 화살·조준 화살·발사 섬광·조준선·꼬리 */
export function branchSheetIds(weaponId: string, branch: string): string[] {
  const arrow = branchArrowFxId(weaponId, false, branch);
  return [
    arrow,
    branchArrowFxId(weaponId, true, branch),
    muzzleFxId(weaponId, branch),
    aimLineFxId(branch),
    ...tailFxIds(arrow),
  ];
}

/**
 * 52라운드 Q5 저격 단계: 비행 거리 / 최대 사거리 < 1/3 → 1, < 2/3 → 2, 그 이상 → 3 (경계는 데이터)
 */
export function snipeLevel(traveledPx: number, maxRangePx: number, bounds: readonly number[] = [1 / 3, 2 / 3]): number {
  if (!(maxRangePx > 0)) return 1;
  const r = traveledPx / maxRangePx;
  let lv = 1;
  for (const b of bounds) if (r >= b) lv += 1;
  return lv;
}

/**
 * 확정 치명이 시작되는 단계 (필중 `critFromLevel`). 53라운드 Q40: `critAimedOnly` 면 조준 사격만 — 일반 화살은 없음(undefined).
 * 거리 배율(levelMults)은 이와 무관하게 모든 화살
 */
export function snipeCritFromLevel(
  snipe: { critFromLevel?: number; critAimedOnly?: boolean } | null | undefined,
  aimed: boolean,
): number | undefined {
  if (!snipe || snipe.critFromLevel === undefined) return undefined;
  return aimed || !snipe.critAimedOnly ? snipe.critFromLevel : undefined;
}

/** 단계 배율 (배열 범위 밖이면 끝 값, 없으면 1) */
export function levelMult(mults: readonly number[] | undefined, level: number): number {
  if (!mults || mults.length === 0) return 1;
  return mults[Math.max(0, Math.min(mults.length - 1, level - 1))];
}

/**
 * 진행도 구동 조준선 (`aim_line_snipe`): 차지 중 frame = min(마지막 진행 프레임, floor(progress × n)), 완료 = stateFrames.complete.
 * progressFrames 가 없으면 상태 프레임(charging/complete)만
 */
export function aimLineFrame(
  def: { progressFrames?: number[]; stateFrames?: Record<string, number | number[]>; frames: number },
  progress: number,
): number {
  const done = progress >= 1;
  const sf = def.stateFrames ?? {};
  const pick = (v: number | number[] | undefined, fallback: number) =>
    typeof v === 'number' ? v : Array.isArray(v) && v.length > 0 ? v[0] : fallback;
  if (done) return clampFrame(pick(sf.complete, def.frames - 1), def.frames);
  const prog = def.progressFrames;
  if (!prog || prog.length === 0) return clampFrame(pick(sf.charging, 0), def.frames);
  const i = Math.min(prog.length - 1, Math.floor(Math.max(0, progress) * prog.length));
  return clampFrame(prog[i], def.frames);
}

function clampFrame(f: number, frames: number): number {
  return f >= 0 && f < frames ? f : 0;
}

/** 활 1단 갈래 시트 전부 (Preloader 로드 목록 — 무기 데이터에서 유도, 없는 파일은 매니페스트가 거른다) */
export function branchFxSheetIds(weapons: Record<string, FxWeaponShape>): string[] {
  const out = new Set<string>();
  for (const [id, w] of Object.entries(weapons))
    if (w.kind === 'ranged')
      for (const b of w.personality.branches) for (const s of branchSheetIds(id, b.id)) out.add(s);
  return [...out];
}
