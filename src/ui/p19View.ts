/**
 * P19 1-U 자유 전투 UI — 순수 계산 (Phaser 없음). 화면 밖 적 표식 자리, 반응 팝 내용·자리, 카메라 값 읽기.
 * 계약 free-combat §1·§4 의 새 필드(`UiSnapshot.camera`·`offscreen`)는 시스템 S1~S3 가 넣는 중이라 스냅샷에서 느슨하게 읽는다.
 */
import { CAMERA_FALLBACK_ZOOM, OFFSCREEN as O, TELL } from './themeP19';

export type Threat = 'warn' | 'danger' | 'ranged' | null;

export interface OffscreenEnemy {
  id: string;
  /** 라디안, 화면 좌표(y 아래) — 화면 가운데(주인공)에서 적 쪽 (UiExitHint.angle 과 같은 규칙으로 가정) */
  angle: number;
  distTiles: number;
  threat: Threat;
}

export interface CameraInfo {
  zoom: number;
  combat: boolean;
  /** (요청 중) 보이는 월드 사각형 px — 월드 좌표 이벤트를 화면에 놓는 데 */
  view?: { x: number; y: number; w: number; h: number } | null;
}

const num = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v);

/** 스냅샷의 `camera` (없거나 잘못되면 null) */
export function cameraOf(s: unknown): CameraInfo | null {
  const c = (s as { camera?: unknown } | null)?.camera as Partial<CameraInfo> | null | undefined;
  if (!c || !num(c.zoom) || c.zoom <= 0) return null;
  const v = c.view;
  const view = v && num(v.x) && num(v.y) && num(v.w) && num(v.h) && v.w > 0 && v.h > 0 ? v : null;
  return { zoom: c.zoom, combat: Boolean(c.combat), view };
}

/** 논리 배율 (월드 px 1 = 화면 px n). 카메라 값이 없으면 옛 배율 2 */
export function cameraZoom(s: unknown): number {
  return cameraOf(s)?.zoom ?? CAMERA_FALLBACK_ZOOM;
}

/** 스냅샷의 `offscreen` (잘못된 줄은 버린다) */
export function offscreenOf(s: unknown): OffscreenEnemy[] {
  const list = (s as { offscreen?: unknown } | null)?.offscreen;
  if (!Array.isArray(list)) return [];
  const out: OffscreenEnemy[] = [];
  for (const e of list as Partial<OffscreenEnemy>[]) {
    if (!e || !num(e.angle)) continue;
    const t = e.threat;
    out.push({
      id: String(e.id ?? out.length),
      angle: e.angle,
      distTiles: num(e.distTiles) ? e.distTiles : O.farTiles,
      threat: t === 'warn' || t === 'danger' || t === 'ranged' ? t : null,
    });
  }
  return out;
}

/** 화면 가운데에서 angle 쪽으로 뻗은 선이 안쪽 사각형(가장자리 inset·위 top·아래 bottom)에 닿는 점 */
export function edgePoint(
  angle: number,
  W: number,
  H: number,
  inset: number,
  top: number,
  bottom: number,
): { x: number; y: number } {
  const cx = W / 2;
  const cy = H / 2;
  const dx = Math.cos(angle);
  const dy = Math.sin(angle);
  let k = Number.POSITIVE_INFINITY;
  if (dx > 1e-6) k = Math.min(k, (W - inset - cx) / dx);
  if (dx < -1e-6) k = Math.min(k, (inset - cx) / dx);
  if (dy > 1e-6) k = Math.min(k, (H - bottom - cy) / dy);
  if (dy < -1e-6) k = Math.min(k, (top - cy) / dy);
  return { x: Math.round(cx + dx * k), y: Math.round(cy + dy * k) };
}

export interface OffscreenMark {
  id: string;
  x: number;
  y: number;
  angle: number;
  size: number;
  alpha: number;
  /** 예고 색 (위협 없음 = null → 무채) */
  color: string | null;
  threat: Threat;
}

/** 화면 밖 적마다 하나씩 (100% 표식). 가까울수록 크고 진하다. 위협이 있는 것이 위에 그려지게 뒤로 보낸다 */
export function offscreenMarks(list: readonly OffscreenEnemy[], W: number, H: number): OffscreenMark[] {
  const rank = (t: Threat): number => (t === 'danger' ? 3 : t === 'warn' ? 2 : t === 'ranged' ? 1 : 0);
  return list
    .map((e) => {
      const f = Math.max(0, Math.min(1, (e.distTiles - O.nearTiles) / (O.farTiles - O.nearTiles)));
      const p = edgePoint(e.angle, W, H, O.inset, O.top, O.bottom);
      return {
        id: e.id,
        x: p.x,
        y: p.y,
        angle: e.angle,
        size: Math.round(O.sizeMax - (O.sizeMax - O.sizeMin) * f),
        alpha: Math.round((1 - (1 - O.farAlpha) * f) * 100) / 100,
        color: e.threat ? TELL[e.threat] : null,
        threat: e.threat,
      };
    })
    .sort((a, b) => rank(a.threat) - rank(b.threat));
}

// ---- 반응 팝 (벽꽝·볼링·낙하·연쇄 폭발)

export type PopKind = 'wall' | 'bowl' | 'fell' | 'blast';

export interface PopView {
  kind: PopKind;
  /** 큰 숫자 ('' = 그림 문자만) */
  num: string;
}

/** 이벤트 페이로드 → 팝 (연쇄 폭발은 연쇄(chain ≥ 1)만 — 첫 폭발은 팝 없음). numbers = 설정 '피해 숫자' */
export function popOf(kind: PopKind, p: unknown, numbers: boolean): PopView | null {
  if (!p || typeof p !== 'object') return null;
  const o = p as Record<string, unknown>;
  const n = (v: unknown): string => (numbers && num(v) && v >= 1 ? String(Math.round(v)) : '');
  switch (kind) {
    case 'wall':
      return { kind, num: n(o.bonusDamage) };
    case 'bowl':
      return { kind, num: n(o.damage) };
    case 'fell':
      return { kind, num: '' };
    case 'blast':
      return num(o.chain) && o.chain >= 1 ? { kind, num: `×${Math.round(o.chain) + 1}` } : null;
  }
}

/**
 * 팝 자리 (논리 px). 페이로드 `screen` 이 있으면 그것, 없으면 `camera.view` 로 월드 x,y 를 바꾼다. 둘 다 없으면 null(팝 없음).
 * shortcut: 계약 §1 페이로드는 월드 좌표뿐이고 §4 camera 에 보이는 사각형이 없다 — 시스템이 `screen` 또는 `camera.view` 를 주면 그때부터 보인다.
 */
export function popScreen(p: unknown, cam: CameraInfo | null, W: number, H: number): { x: number; y: number } | null {
  const o = (p ?? {}) as { x?: unknown; y?: unknown; screen?: { x?: unknown; y?: unknown } | null };
  if (o.screen && num(o.screen.x) && num(o.screen.y)) return { x: Math.round(o.screen.x), y: Math.round(o.screen.y) };
  const v = cam?.view;
  if (!v || !num(o.x) || !num(o.y)) return null;
  return { x: Math.round(((o.x - v.x) / v.w) * W), y: Math.round(((o.y - v.y) / v.h) * H) };
}

/** 연속 처치 표 (count < min 이면 null) */
export function comboText(count: unknown, min: number): string | null {
  return num(count) && count >= min ? `×${Math.round(count)}` : null;
}
