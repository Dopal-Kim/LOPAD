/**
 * P21 어두운 톤 · 잔혹 전투 UI — 순수 계산 (Phaser 없음, 테스트한다). contracts/dark-brutal §1·§2·§3.
 * 계약 코드(`src/contract/ui.ts`)에 새 필드·이벤트가 들어오는 중이라 페이로드·스냅샷은 느슨하게 읽는다(모양이 틀리면 버림).
 */
type Obj = Record<string, unknown>;
const num = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v);
const obj = (v: unknown): Obj | null => (v && typeof v === 'object' && !Array.isArray(v) ? (v as Obj) : null);
const mod = (a: number, n: number): number => ((a % n) + n) % n;

// ---- 첫 실행 잔혹 묘사 안내 (한 번)

export const GORE_NOTICE_KEY = 'lopad.goreNotice';
/** 저장소를 못 쓰는 환경: 이번 페이지에서만 기억 */
let seenThisPage = false;

type Store = Pick<Storage, 'getItem' | 'setItem'> | null | undefined;

export function goreNoticeSeen(store: Store): boolean {
  if (seenThisPage) return true;
  try {
    return store?.getItem(GORE_NOTICE_KEY) === '1';
  } catch {
    return false;
  }
}

export function markGoreNoticeSeen(store: Store): void {
  seenThisPage = true;
  try {
    store?.setItem(GORE_NOTICE_KEY, '1');
  } catch {
    // 사생활 보호 창 등 — 이번 페이지만
  }
}

/** 테스트용 */
export function resetGoreNoticePage(): void {
  seenThisPage = false;
}

/** 안내 카드·설정의 갈래 이동 (끝에서 멈춤). i = 갈래 번호(0 = 전체) */
export function stepGoreIndex(i: number, dir: -1 | 1, n = 3): number {
  return Math.max(0, Math.min(n - 1, i + dir));
}

// ---- 주인공 상흔 (§3)

export interface Wound {
  stage: 0 | 1 | 2 | 3;
  arrows: number;
}

/** `{stage, arrows}` 페이로드·스냅샷 조각 → 상흔 (틀리면 null) */
export function woundOf(v: unknown): Wound | null {
  const o = obj(v);
  if (!o || !num(o.stage)) return null;
  const stage = Math.max(0, Math.min(3, Math.round(o.stage))) as Wound['stage'];
  const arrows = num(o.arrows) ? Math.max(0, Math.min(5, Math.round(o.arrows))) : 0;
  return { stage, arrows };
}

/** 스냅샷 `player.wound` (계약 §2 — 아직 없으면 null) */
export function snapshotWound(s: unknown): Wound | null {
  return woundOf(obj(obj(s)?.player)?.wound);
}

/**
 * 체력 막대 위 균열 (막대 왼쪽 위 기준 px). 같은 `seed`·단계면 늘 같은 모양 — 매 프레임 다시 그려도 떨리지 않는다.
 * 균열 하나 = 위 끝에서 아래로 꺾이며 내려가는 점 3~4개. 단계가 오르면 앞 단계 균열을 그대로 두고 더한다.
 */
export function crackPaths(count: number, w: number, h: number, seed = 7): { x: number; y: number }[][] {
  let r = seed * 9301 + 49297;
  const rnd = (): number => {
    r = (r * 9301 + 49297) % 233280;
    return r / 233280;
  };
  const out: { x: number; y: number }[][] = [];
  for (let i = 0; i < count; i++) {
    // 고르게 퍼지게: 칸을 나눠 그 안에서
    const x0 = Math.round(((i * 0.618 + 0.13) % 1) * (w - 6)) + 3;
    const pts = [{ x: x0, y: 0 }];
    const steps = 2 + Math.floor(rnd() * 2);
    for (let k = 1; k <= steps; k++)
      pts.push({ x: pts[k - 1].x + Math.round((rnd() - 0.5) * 6), y: Math.round((h * k) / steps) });
    out.push(pts.map((p) => ({ x: Math.max(0, Math.min(w - 1, p.x)), y: Math.max(0, Math.min(h - 1, p.y)) })));
  }
  return out;
}

// ---- 저HP (§2 LOW_HP)

export function lowHpOf(v: unknown): boolean | null {
  const o = obj(v);
  return o && typeof o.on === 'boolean' ? o.on : null;
}

/**
 * 저HP 비네트 알파: 심장 박동 '쿵·쿵' (위상 0 과 beat2 에 가우스 봉우리). flash 끄면 고정 알파.
 */
export function lowHpAlpha(
  tMs: number,
  flash: boolean,
  v: {
    alphaMin: number;
    alphaMax: number;
    alphaFixed: number;
    hz: number;
    beat2: number;
    beatW: number;
    beat2Gain: number;
  },
): number {
  if (!flash) return v.alphaFixed;
  const ph = mod((tMs / 1000) * v.hz, 1);
  const g = (c: number): number => Math.exp(-(((ph - c) / v.beatW) ** 2)) + Math.exp(-(((ph - c - 1) / v.beatW) ** 2));
  const k = Math.min(1, g(0) + v.beat2Gain * g(v.beat2));
  return v.alphaMin + (v.alphaMax - v.alphaMin) * k;
}

// ---- 처형 가능 표식 (§2 — 자리는 스냅샷 `executable {uid, screen}`, 이벤트는 켜기·끄기)

/** 스냅샷의 처형 가능한 적 (지금 하나) → 표식 자리 (없으면 null) */
export function executableOf(s: unknown): { uid: number; x: number; y: number } | null {
  const e = obj(obj(s)?.executable);
  const sc = obj(e?.screen);
  return e && num(e.uid) && sc && num(sc.x) && num(sc.y) ? { uid: e.uid, x: sc.x, y: sc.y } : null;
}

/** `ui:enemy-executable` → 꺼진 개체 번호 (켜짐·모양 틀림이면 null) */
export function executableOffUid(v: unknown): number | null {
  const o = obj(v);
  return o && o.on === false && num(o.uid) ? o.uid : null;
}

/** `ui:player-execute` → 처형 동작 길이 (없으면 450ms — 계약 §4 무적 시간) */
export function executeMsOf(v: unknown): number {
  const ms = obj(v)?.ms;
  return num(ms) && ms > 0 ? ms : 450;
}

// ---- 연속 처치 단계 낱말 (66 reactPops.streak — 2 고인다 · 4 차오른다 · 7 넘친다)

export function streakKey(count: number): 'streak2' | 'streak4' | 'streak7' {
  return count >= 7 ? 'streak7' : count >= 4 ? 'streak4' : 'streak2';
}
