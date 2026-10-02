/**
 * 49라운드 순수 계산 (Phaser 없이 테스트한다). 계약 `ui-system-interface.md` §11.
 * - 무기 자원 게이지(기력 막대·화살 칸·열기 단계)의 칸 수·링 점·단계
 * - 무기 시험장 갈래 메뉴의 들여쓰기 추정
 * - 조작법 줄의 'M 음소거' → 'M 지도' 바꾸기
 */
import type { UiWeaponResource } from '../contract/ui';

/** 0..1 로 자른다 (NaN → 0) */
export function clamp01(v: number): number {
  return Number.isFinite(v) ? Math.max(0, Math.min(1, v)) : 0;
}

/** 자원 비율 (max 0 이하·빈 값 → 0) */
export function resourceRatio(r: Pick<UiWeaponResource, 'value' | 'max'>): number {
  return r.max > 0 ? clamp01(r.value / r.max) : 0;
}

/**
 * 화살 칸: 칸 수(max)와 찬 칸(value). `cap` 을 넘으면 칸 대신 막대로 그리라고 compact=true.
 * 값은 정수로 내림 (장전 중 소수가 와도 칸이 반쯤 차지 않게).
 */
export function ammoCells(
  value: number,
  max: number,
  cap: number,
): { filled: number; total: number; compact: boolean } {
  const total = Math.max(0, Math.floor(Number.isFinite(max) ? max : 0));
  const filled = Math.max(0, Math.min(total, Math.floor(Number.isFinite(value) ? value : 0)));
  return { filled, total, compact: total > cap };
}

/**
 * 진행 링의 픽셀 점: 반지름 r 원 위의 정수 점을 12시 방향부터 시계 방향으로 (겹침 없이).
 * 1px 링이 끊기지 않게 각도를 촘촘히 돌며 새 칸만 담는다.
 */
export function ringPoints(r: number): { x: number; y: number }[] {
  const pts: { x: number; y: number }[] = [];
  const seen = new Set<string>();
  const steps = Math.max(16, Math.round(2 * Math.PI * r * 4));
  for (let i = 0; i < steps; i++) {
    const a = (i / steps) * Math.PI * 2;
    const x = Math.round(Math.sin(a) * r);
    const y = Math.round(-Math.cos(a) * r);
    const k = `${x},${y}`;
    if (seen.has(k)) continue;
    seen.add(k);
    pts.push({ x, y });
  }
  return pts;
}

/** 진행도 p(0..1)만큼 켤 점 개수 */
export function ringLit(count: number, progress: number): number {
  return Math.round(count * clamp01(progress));
}

/** 열기 단계 0..maxStage. stage 가 오면 그것, 없으면 비율로 나눈다 (가득이면 최고 단계) */
export function heatStage(r: Pick<UiWeaponResource, 'value' | 'max' | 'stage'>, maxStage = 3): number {
  if (typeof r.stage === 'number' && Number.isFinite(r.stage))
    return Math.max(0, Math.min(maxStage, Math.floor(r.stage)));
  const ratio = resourceRatio(r);
  return Math.max(0, Math.min(maxStage, Math.floor(ratio * maxStage + 1e-9)));
}

/** 표시할 정수 (기력 등은 소수로 올 수 있다 — 바닥은 0, 그 외 올림해 '조금 남음' 이 0 으로 보이지 않게) */
export function shownValue(v: number): number {
  if (!Number.isFinite(v) || v <= 0) return 0;
  return Math.ceil(v - 1e-9);
}

// ---------------------------------------------------------------------------------------------
/** 갈래 트리 기호 (라벨 앞에 오면 떼고 깊이로 센다) */
const TREE_MARK = /^[\s\u3000]*([└├│─┗┣┃━ㄴ·\-–—>»]+)[\s\u3000]*/;

/**
 * 무기 시험장 메뉴 줄의 들여쓰기 깊이 (계약에 깊이 필드가 없어 라벨·key 모양으로 추정한다).
 * - 라벨 앞 공백 2칸(전각 1칸) = 1단계, 트리 기호(└ ├ ㄴ · - 등)가 있으면 +1 하고 기호를 뗀다.
 * - key 가 '1.2'·'a/b'·'a>b' 꼴이면 구분자 수만큼.
 * 둘 중 큰 값. 최대 4.
 */
export function menuIndent(line: { key: string; label: string }): { depth: number; label: string } {
  let label = line.label;
  const lead = /^[ \u3000]*/.exec(label)?.[0] ?? '';
  let depth = 0;
  for (const ch of lead) depth += ch === '\u3000' ? 2 : 1;
  depth = Math.floor(depth / 2);
  const m = TREE_MARK.exec(label);
  if (m) {
    depth += 1;
    label = label.slice(m[0].length);
  } else label = label.slice(lead.length);
  const keyDepth = (line.key.match(/[./>]/g) ?? []).length;
  return { depth: Math.min(4, Math.max(depth, keyDepth)), label };
}

// ---------------------------------------------------------------------------------------------
/**
 * 49라운드: M 은 음소거가 아니라 지도. 조작법 줄(텍스트 팩)에 'M 음소거' 류가 남아 있으면 지도 문구로 바꾼다.
 * 없으면 그대로.
 */
export function replaceMuteHint(line: string, mapText: string): string {
  return line.replace(/M\s*(음소거|소리\s*끄기|소리)/g, mapText);
}
