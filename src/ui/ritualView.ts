/**
 * 62 루프 1 P0-2 첫 생 의식 UI — 순수 계산 (Phaser 없음, 계약 §20).
 * 안내 줄 해석('[Enter] 적는다 · [R] …'), 이름 길이 자르기(한글 조합 중 글자 포함), 먹 붓 획 점 모으기.
 */
import type { UiRitual, UiRitualPhase, UiRitualPoint } from '../contract/ui';
import { RITUAL_UI as R } from './themeRitual';

/** 안내 한 마디: 키 그림 + 동작 */
export interface HintPart {
  keys: string[];
  label: string;
}

/**
 * '[Enter] 이름을 적는다 · [R] 획을 다시 긋는다' → [{keys:['Enter'], label:'이름을 적는다'}, …].
 * 대괄호 안이 키(여럿이면 '[W][A]' 처럼 이어 쓴다), 대괄호가 없으면 글만.
 */
export function parseHint(hint: string | null | undefined): HintPart[] {
  const raw = (hint ?? '').trim();
  if (!raw) return [];
  return raw
    .split(/\s+·\s+/)
    .map((seg) => {
      const keys: string[] = [];
      let rest = seg.trim();
      for (;;) {
        const m = /^\[([^\]]+)\]\s*/.exec(rest);
        if (!m) break;
        keys.push(m[1].trim());
        rest = rest.slice(m[0].length);
      }
      return { keys, label: rest.trim() };
    })
    .filter((p) => p.keys.length || p.label);
}

/** 이름 칸 값: 줄바꿈·앞 공백 제거, 최대 글자 수까지 */
export function clampName(value: string, maxLen: number): string {
  const flat = value.replace(/[\r\n\t]/g, ' ').replace(/^\s+/, '');
  const n = Math.max(1, Math.floor(maxLen));
  return Array.from(flat).slice(0, n).join('');
}

/**
 * 새로 적힌 글자 위치들 (먹 번짐 연출): 앞 값과 공통 앞부분 뒤로 바뀐 글자의 순번. 지워졌으면 [].
 * 한글 조합 중에는 마지막 글자가 계속 바뀌므로 그 글자도 '새 글자'로 친다.
 */
export function newCharIndexes(prev: string, next: string): number[] {
  const a = Array.from(prev);
  const b = Array.from(next);
  let i = 0;
  while (i < a.length && i < b.length && a[i] === b[i]) i++;
  const out: number[] = [];
  for (let k = i; k < b.length; k++) out.push(k);
  return out;
}

/**
 * 획 점 모으기: 앞 점에서 minDist 미만이면 버린다(같은 자리 연타 방지), 최대 maxPoints. 돌려주는 값 = 넣었는가.
 * 점은 논리 화면 좌표(계약 §20 `UiRitualPoint`).
 */
export function pushPoint(points: UiRitualPoint[], p: UiRitualPoint, minDist: number, maxPoints: number): boolean {
  if (points.length >= maxPoints) return false;
  const last = points[points.length - 1];
  if (last && Math.hypot(p.x - last.x, p.y - last.y) < minDist) return false;
  points.push({ x: Math.round(p.x * 10) / 10, y: Math.round(p.y * 10) / 10, t: Math.round(p.t) });
  return true;
}

/** 스냅샷에서 의식 상태 읽기 (없거나 모양이 틀리면 null) */
export function readRitual(v: unknown): UiRitual | null {
  if (!v || typeof v !== 'object') return null;
  const r = v as UiRitual;
  const phases: UiRitualPhase[] = ['name', 'strokes', 'trial', 'fate', 'rewrite', null];
  if (!phases.includes(r.phase ?? null)) return null;
  return r;
}

/** 그림을 새로 짜야 하는 바뀜인가 (단계가 바뀜) — 같은 단계면 부분 갱신 */
export function ritualRebuild(prev: UiRitual | null, next: UiRitual | null): boolean {
  return (prev?.phase ?? null) !== (next?.phase ?? null);
}

/** 3획 낙관 칸 상태: 찍힘 / 지금 / 아직 */
export function sealStates(done: number, total: number): ('done' | 'now' | 'todo')[] {
  const n = Math.max(1, Math.floor(total));
  const d = Math.max(0, Math.min(n, Math.floor(done)));
  return Array.from({ length: n }, (_, i) => (i < d ? 'done' : i === d ? 'now' : 'todo'));
}

/** 진행 방향 → 45° 칸 (0 오른쪽 · 2 아래 · 4 왼쪽 · 6 위) */
export function dirIndex(dx: number, dy: number): number {
  const a = Math.atan2(dy, dx);
  return (((Math.round(a / (Math.PI / 4)) % 8) + 8) % 8) as number;
}

/** 속도(논리 px/ms) → 몸통 스탬프 프레임 (art §30: 느림·누름 8~10 · 보통 5~6 · 빠름 = 마른 붓) */
export function bodyFrame(speed: number, dir: number): string {
  const S = R.stamp;
  if (!Number.isFinite(speed) || speed < S.slow * 0.5) return 'tip_d10';
  if (speed < S.slow) return 'tip_d8';
  if (speed < (S.slow + S.fast) / 2) return 'tip_d6';
  if (speed < S.fast) return 'tip_d5';
  return `dry_d6_r${dir}`;
}

/** 다각형 안 (짝홀 규칙) */
export function inPolygon(x: number, y: number, poly: readonly (readonly [number, number])[]): boolean {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i];
    const [xj, yj] = poly[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi + 1e-9) + xi) inside = !inside;
  }
  return inside;
}
