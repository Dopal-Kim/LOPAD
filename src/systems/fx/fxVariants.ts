/**
 * 53라운드 무기 이펙트 v3 (계약 art §10·§13, 결정 round-53 Q5·Q61~Q64) — 갈래 시트 고르기 · 2단 갈래/가열 변주. Phaser 의존 없음.
 *
 * - 1단 갈래 근접 시트 `fx/<무기>_combo<n>_<갈래>`: 갈래가 있고 파일이 있으면 기본 `fx/<무기>_combo<n>` 대신 (메모·판정 동일)
 * - 2단 갈래: 시트 없이 1단(또는 활 갈래) 시트 JSON `secondaryVariants[<2단 id>]` — `colorSwap`(정확 교체, 동시 적용) +
 *   `flashOverride`·`shakeOverride`·`trailOverride`·`holdLastFrameMs` + `overlay`(기존 시트 겹침)
 * - 단검 가열: 갈래 시트 JSON `heatVariants.colorSwap[<k>]` + `playbackRateHint[<k>]` (기본 시트는 별도 heat 시트)
 * 필드가 없거나 형식이 틀리면 조용히 무시한다 (원본 그대로).
 */
import { COMBO_HITS, type FxFlashSpec, type FxShakeSpec, type FxTrailSpec } from '../sprites/spriteDefs';
import { comboFxId, type FxWeaponShape } from './fxIds';

/** 정확 색 교체 한 쌍 ('#rrggbb') */
export interface ColorSwap {
  from: string;
  to: string;
}

/** 겹침 시트 (`fx/<이름>`) — loop 면 투사체·이펙트를 따라가고, onHit/onlyOnCrit 은 적중 연출 쪽(기존 치명·출혈)이 맡는다 */
export interface VariantOverlay {
  sheet: string;
  loop?: boolean;
  onHit?: boolean;
  onlyOnCrit?: boolean;
  minLevel?: number;
  atFrame?: number;
}

/** 한 번 재생에 적용할 변주 (해석 결과) */
export interface FxVariant {
  /** 동시 적용 색 교체 (2단 → 가열 순서로 합성) */
  swaps: ColorSwap[];
  flash?: FxFlashSpec;
  shake?: FxShakeSpec;
  trail?: FxTrailSpec;
  /** 마지막 프레임 유지 ms */
  holdLastMs?: number;
  /** 따라가는 루프 겹침 시트 id (`fx/` 뗀 이름) */
  followOverlays: string[];
  /** 가열 재생 배속 힌트 (없으면 null) */
  playbackRate: number | null;
}

/** 1단 갈래 근접 연격 이펙트 `<무기>_combo<n>_<갈래>` */
export function branchComboFxId(weaponId: string, n: number, branch: string): string {
  return `${comboFxId(weaponId, n)}_${branch}`;
}

/** 근접 무기 1단 갈래 연격 이펙트 전부 (Preloader 로드 목록 — 없는 파일은 매니페스트가 거른다) */
export function meleeBranchFxSheetIds(weapons: Record<string, FxWeaponShape>): string[] {
  const out: string[] = [];
  for (const [id, w] of Object.entries(weapons)) {
    if (w.kind !== 'melee') continue;
    for (const b of w.personality.branches)
      for (let n = 1; n <= COMBO_HITS; n++) out.push(branchComboFxId(id, n, b.id));
  }
  return out;
}

const HEX = /^#[0-9a-fA-F]{6}$/;

function asSwaps(v: unknown): ColorSwap[] {
  if (!Array.isArray(v)) return [];
  const out: ColorSwap[] = [];
  for (const e of v) {
    const c = e as Partial<ColorSwap> | null;
    if (c && typeof c.from === 'string' && typeof c.to === 'string' && HEX.test(c.from) && HEX.test(c.to))
      out.push({ from: c.from.toLowerCase(), to: c.to.toLowerCase() });
  }
  return out;
}

function asObj(v: unknown): Record<string, unknown> | null {
  return v && typeof v === 'object' && !Array.isArray(v) ? (v as Record<string, unknown>) : null;
}

function asOverlays(v: Record<string, unknown>): VariantOverlay[] {
  const list = Array.isArray(v.overlays) ? v.overlays : v.overlay ? [v.overlay] : [];
  const out: VariantOverlay[] = [];
  for (const o of list) {
    const r = asObj(o);
    if (r && typeof r.sheet === 'string') out.push(r as unknown as VariantOverlay);
  }
  return out;
}

/**
 * 두 동시 교체 표를 순서대로 합성한 하나의 동시 교체 표 (먼저 `a`, 그 결과에 `b`). 같은 색으로 가는 쌍은 뺀다
 */
export function composeSwaps(a: readonly ColorSwap[], b: readonly ColorSwap[]): ColorSwap[] {
  const first = new Map(a.map((s) => [s.from, s.to]));
  const second = new Map(b.map((s) => [s.from, s.to]));
  const out = new Map<string, string>();
  for (const [from, mid] of first) out.set(from, second.get(mid) ?? mid);
  for (const [from, to] of second) if (!first.has(from)) out.set(from, to);
  return [...out].filter(([f, t]) => f !== t).map(([from, to]) => ({ from, to }));
}

/** 교체 목록 → 텍스처 키 접미용 짧은 태그 (순서 무관, 결정적) */
export function swapTag(swaps: readonly ColorSwap[]): string {
  return swaps
    .map((s) => `${s.from.slice(1)}${s.to.slice(1)}`)
    .sort()
    .join('');
}

/** 변주를 고르는 데 필요한 시트 JSON 최소 형태 (SheetJson 에 섞여 온다) */
export interface VariantSheetFields {
  secondaryVariants?: unknown;
  heatVariants?: unknown;
}

/**
 * 변주 묶음 하나(`secondaryVariants[<id>]` 또는 2단 시트 JSON `runtime`)를 해석한다. `withSwaps` 가 false 면 colorSwap 을 읽지 않는다
 * (2단 전용 시트는 색이 이미 그려져 있다 — 계약 §10 55라운드 Q16)
 */
function specVariant(sv: Record<string, unknown>, withSwaps: boolean): FxVariant {
  const v: FxVariant = { swaps: withSwaps ? asSwaps(sv.colorSwap) : [], followOverlays: [], playbackRate: null };
  const flash = asObj(sv.flashOverride);
  if (flash) v.flash = flash as FxFlashSpec;
  const shake = asObj(sv.shakeOverride);
  if (shake && typeof shake.px === 'number' && typeof shake.ms === 'number') v.shake = shake as unknown as FxShakeSpec;
  const trail = asObj(sv.trailOverride);
  if (trail) v.trail = trail as FxTrailSpec;
  if (typeof sv.holdLastFrameMs === 'number' && sv.holdLastFrameMs > 0) v.holdLastMs = sv.holdLastFrameMs;
  for (const o of asOverlays(sv))
    if (o.loop && !o.onHit && !o.onlyOnCrit)
      v.followOverlays.push(o.sheet.startsWith('fx/') ? o.sheet.slice(3) : o.sheet);
  return v;
}

/** 아무것도 바꾸지 않는 변주인지 */
export function isEmptyVariant(v: FxVariant): boolean {
  return (
    v.swaps.length === 0 &&
    !v.flash &&
    !v.shake &&
    !v.trail &&
    !v.holdLastMs &&
    v.followOverlays.length === 0 &&
    v.playbackRate === null
  );
}

/** 두 변주 합치기 (색 교체는 a → b 순서로 합성, 나머지는 a 우선). 둘 다 없으면 null */
export function mergeVariants(a: FxVariant | null, b: FxVariant | null): FxVariant | null {
  if (!a || isEmptyVariant(a)) return b && !isEmptyVariant(b) ? b : null;
  if (!b || isEmptyVariant(b)) return a;
  return {
    swaps: composeSwaps(a.swaps, b.swaps),
    flash: a.flash ?? b.flash,
    shake: a.shake ?? b.shake,
    trail: a.trail ?? b.trail,
    holdLastMs: a.holdLastMs ?? b.holdLastMs,
    followOverlays: [...new Set([...a.followOverlays, ...b.followOverlays])],
    playbackRate: a.playbackRate ?? b.playbackRate,
  };
}

/**
 * 재생 변주 해석: `secondary` = 2단 갈래 노드 id (경로의 두 번째), `heat` = 가열 단계(0 = 없음).
 * 아무 변주도 없으면 null. 55라운드: 2단 전용 시트가 있으면 이 함수 대신 `runtimeFxVariant`(fxTier 가 고른다) — 여기는 대체 경로
 */
export function resolveFxVariant(
  def: VariantSheetFields | null | undefined,
  opts: { secondary?: string | null; heat?: number },
): FxVariant | null {
  if (!def) return null;
  const sv = opts.secondary ? asObj(asObj(def.secondaryVariants)?.[opts.secondary]) : null;
  const hv = opts.heat && opts.heat > 0 ? asObj(def.heatVariants) : null;
  const heatSwaps = hv ? asSwaps(asObj(hv.colorSwap)?.[String(opts.heat)]) : [];
  const rateRaw = hv ? asObj(hv.playbackRateHint)?.[String(opts.heat)] : undefined;
  const playbackRate = typeof rateRaw === 'number' && rateRaw > 0 ? rateRaw : null;
  if (!sv && heatSwaps.length === 0 && playbackRate === null) return null;
  const base: FxVariant = sv ? specVariant(sv, true) : { swaps: [], followOverlays: [], playbackRate: null };
  return { ...base, swaps: composeSwaps(base.swaps, heatSwaps), playbackRate };
}

/**
 * 55라운드 Q16 (계약 §10): 2단 전용 시트의 `runtime`(overlay·flashOverride·holdLastFrameMs·shakeOverride·trailOverride) +
 * 그 시트의 `heatVariants`(단검 가열). colorSwap 은 그림에 이미 반영돼 있어 쓰지 않는다. 아무것도 없으면 null
 */
export function runtimeFxVariant(
  def: (VariantSheetFields & { runtime?: unknown }) | null | undefined,
  heat = 0,
): FxVariant | null {
  if (!def) return null;
  const rt = asObj(def.runtime);
  return mergeVariants(rt ? specVariant(rt, false) : null, resolveFxVariant(def, { heat }));
}
