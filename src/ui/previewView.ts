/**
 * 62 루프 3 UI G (도영 님 추가 지시 — 지도 선택 + 키아트 미리보기) 순수 계산 (Phaser 없음, 테스트한다).
 * 미리보기 카드 자리 고르기 · 카드 글 줄 · 그림 고르기 · 켄번스 자르기 · 수련장 지도 조각 자르기.
 */
import type { UiRouteNode } from '../contract/ui';
import { nodeLook } from './bundleView';
import { firstSentence, regionArtKey } from './regionView';
import { REWARD_NAME } from './textBuild';

export interface Box {
  x: number;
  y: number;
  w: number;
  h: number;
}

/** 카드가 피할 것 — weight 가 클수록 더 피한다 (가리킨 곳 자체는 아주 크게) */
export interface Obstacle {
  rect: Box;
  weight: number;
}

export type PreviewSide = 'left' | 'right' | 'above' | 'below';

export interface PreviewPlace {
  x: number;
  y: number;
  side: PreviewSide;
}

/** 두 사각형이 겹치는 넓이 */
export function overlapArea(a: Box, b: Box): number {
  const w = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
  const h = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
  return w > 0 && h > 0 ? w * h : 0;
}

const clampTo = (v: number, lo: number, hi: number): number => (hi < lo ? lo : Math.max(lo, Math.min(hi, v)));

/**
 * 미리보기 카드 자리: 가리킨 곳(anchor) 옆 — 오른쪽·왼쪽(기본) 또는 위·아래 — 중 지도 칸(area) 안에서 피할 것과 덜 겹치는 곳.
 * 같은 점수면 지도 칸 가운데에서 먼 쪽(빈자리가 넓은 쪽 — 가리킨 곳이 왼쪽이면 오른쪽)을, 그다음 가까운 자리를 고른다.
 * 위·아래는 옆자리가 모두 겹칠 때만 이기도록 조금 불리하게 친다. 정수 좌표.
 */
export function placePreview(
  anchor: { x: number; y: number },
  size: { w: number; h: number },
  area: Box,
  obstacles: readonly Obstacle[],
  gap: number,
): PreviewPlace {
  const { w, h } = size;
  const maxX = area.x + area.w - w;
  const maxY = area.y + area.h - h;
  const cands: PreviewPlace[] = [];
  // 가리킨 곳에 맞춘 세 자리 + 지도 칸 위·아래 끝 (이름표·다른 곳을 비켜 갈 여지)
  const ys = [anchor.y - h / 2, anchor.y - h + gap, anchor.y - gap, area.y, maxY];
  for (const side of ['right', 'left'] as const) {
    const x = side === 'right' ? anchor.x + gap : anchor.x - gap - w;
    for (const y of ys) cands.push({ x, y, side });
  }
  const xs = [anchor.x - w / 2, anchor.x - w + gap, anchor.x - gap, area.x, maxX];
  for (const side of ['above', 'below'] as const) {
    const y = side === 'above' ? anchor.y - gap - h : anchor.y + gap;
    for (const x of xs) cands.push({ x, y, side });
  }
  // 넓은 쪽: 가리킨 곳이 지도 칸 왼쪽 절반이면 오른쪽이 넓다
  const roomy: PreviewSide = anchor.x < area.x + area.w / 2 ? 'right' : 'left';
  let best: PreviewPlace | null = null;
  let bestScore = Infinity;
  for (const c of cands) {
    const x = Math.round(clampTo(c.x, area.x, maxX));
    const y = Math.round(clampTo(c.y, area.y, maxY));
    const rect = { x, y, w, h };
    let score = 0;
    for (const o of obstacles) score += overlapArea(rect, o.rect) * o.weight;
    if (c.side === 'above' || c.side === 'below') score += w * h * 0.02;
    if (c.side !== roomy) score += 1;
    const dx = x + w / 2 - anchor.x;
    const dy = y + h / 2 - anchor.y;
    score += Math.hypot(dx, dy) * 0.01;
    if (score < bestScore - 1e-9) {
      bestScore = score;
      best = { x, y, side: c.side };
    }
  }
  return best ?? { x: Math.round(area.x), y: Math.round(area.y), side: roomy };
}

/** 카드 글: 이름 · 종류 · 고유 한 줄 · 보상·위험 줄 · 위험 한 줄 (빈 글은 그리지 않는다) */
export interface PreviewText {
  name: string;
  kind: string;
  line: string;
  /** 보상·위험 표 한 줄 ('보상 전표 주머니 · 위험 정예 길') */
  marks: string;
  /** 위험 노드의 경고 한 줄 (`riskText`) */
  warn: string;
}

type Tx = (key: 'rewardHead' | 'riskHead' | 'riskElite' | 'riskCurse') => string;

const fillName = (t: string, name: string): string => t.replace('{name}', name);

/**
 * 노드 → 카드 글. 고유 한 줄 = 이벤트 내용 이름(지도 정보로 공개된 경우) 또는 설명 첫 문장. 숨은 노드(얼룩)는 이름·보상을 숨긴다.
 */
export function previewText(n: UiRouteNode, kind: string, tx: Tx): PreviewText {
  const look = nodeLook(n);
  if (look.hidden === 'smudge') return { name: '', kind: '', line: '', marks: '', warn: '' };
  const marks: string[] = [];
  if (look.reward) marks.push(fillName(tx('rewardHead'), REWARD_NAME[look.reward] ?? look.reward));
  if (look.risk) marks.push(fillName(tx('riskHead'), tx(look.risk === 'elite' ? 'riskElite' : 'riskCurse')));
  return {
    name: n.name,
    kind,
    line: n.eventName ? n.eventName : firstSentence(n.desc),
    marks: marks.join(' · '),
    warn: look.risk && n.riskText ? n.riskText : '',
  };
}

/**
 * 시스템 H (`UiRouteNode.previewKey` · `UiMenuLine.previewKey`): 미리보기 그림 텍스처 키. 계약 필드가 아직 없는 빌드에서도 읽히게
 * 이름으로 읽는다. 없으면 null
 */
export function readPreviewKey(o: unknown): string | null {
  return readStr(o, 'previewKey');
}

/** 시스템 H `previewRegion`: 대체 키아트 지역 id (waste·gate·outer·brewery·hall·training …). 없으면 null */
export function readPreviewRegion(o: unknown): string | null {
  return readStr(o, 'previewRegion');
}

function readStr(o: unknown, name: string): string | null {
  if (!o || typeof o !== 'object') return null;
  const k = (o as Record<string, unknown>)[name];
  return typeof k === 'string' && k.length > 0 ? k : null;
}

/** 미리보기 그림 고르기 결과 */
export type PreviewArt = { kind: 'texture'; key: string } | { kind: 'keyart'; art: string } | { kind: 'paper' };

/** 지역 id(waste·outer·gate·hall·brewery, boss → hall) → 키아트 키. 그 밖(training 등)은 null */
export function regionIdArt(id: string | null | undefined): string | null {
  const r = (id ?? '').trim().toLowerCase();
  if (['waste', 'outer', 'gate', 'hall', 'brewery'].includes(r)) return r;
  return r === 'boss' ? 'hall' : null;
}

/**
 * 그림 고르기: ① 시스템 `previewKey` 텍스처가 이미 있으면 그것 ② 지역 키아트 — 시스템 `previewRegion` id, 없으면 지역 표시 이름 낱말
 * (UI 소유 그림 — 아직 안 읽혔으면 읽으며 기다림) ③ 종이. `pending` = previewKey 를 받았는데 텍스처가 아직 없음(시스템이 받는 중 —
 * 오면 바꿔 끼운다). 입구 그림(`paint/door_*`)을 이름 규칙으로 찾지 않는다(시스템이 고른 키만 쓴다).
 */
export function pickPreviewArt(
  src: { previewKey?: string | null; previewRegion?: string | null; region?: string | null },
  has: (key: string) => string | null,
): { art: PreviewArt; pending: string | null } {
  const key = src.previewKey || null;
  const tex = key ? has(key) : null;
  if (tex) return { art: { kind: 'texture', key: tex }, pending: null };
  const art = regionIdArt(src.previewRegion) ?? regionArtKey(src.region);
  return { art: art ? { kind: 'keyart', art } : { kind: 'paper' }, pending: key };
}

/**
 * 켄번스: 그림 텍스처(texW×texH)를 z 배 확대해 보이는 자르기 사각형. pan(-1~1) 은 남는 폭 안에서 치우침.
 */
export function kenBurnsCrop(texW: number, texH: number, z: number, panX = 0, panY = 0): Box {
  const k = Math.max(1, z);
  const w = texW / k;
  const h = texH / k;
  const px = Math.max(-1, Math.min(1, panX));
  const py = Math.max(-1, Math.min(1, panY));
  return { x: ((texW - w) / 2) * (1 + px), y: ((texH - h) / 2) * (1 + py), w, h };
}

/** 켄번스 배율 (경과 ms): 1 → zMax 를 periodMs 동안 부드럽게 갔다가 되돌아온다 */
export function kenBurnsZoom(elapsed: number, zMax: number, periodMs: number): number {
  const p = Math.max(1, periodMs);
  const t = ((elapsed % (p * 2)) + p * 2) % (p * 2);
  const u = t < p ? t / p : 2 - t / p;
  const e = 0.5 - Math.cos(Math.PI * u) / 2;
  return 1 + (zMax - 1) * e;
}

/** 교차 페이드 알파 (경과 ms, 길이 ms): 새 카드 0 → 1 */
export function fadeIn(elapsed: number, ms: number): number {
  return ms <= 0 ? 1 : Math.max(0, Math.min(1, elapsed / ms));
}

/**
 * 수련장 지도 그림에서 방 자리(u, v 0~1) 둘레를 16:9 로 자를 사각형 (그림 픽셀). frac = 그림 폭 대비 자르는 폭. 그림 밖으로 나가지 않게 민다
 */
export function spotCrop(u: number, v: number, imgW: number, imgH: number, frac: number, aspect = 16 / 9): Box {
  const w = Math.min(imgW, Math.max(1, Math.round(imgW * frac)));
  const h = Math.min(imgH, Math.max(1, Math.round(w / aspect)));
  const x = clampTo(Math.round(u * imgW - w / 2), 0, imgW - w);
  const y = clampTo(Math.round(v * imgH - h / 2), 0, imgH - h);
  return { x, y, w, h };
}
