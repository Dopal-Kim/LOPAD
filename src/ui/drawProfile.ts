import type Phaser from 'phaser';
import { debugExpose, uiDebugEnabled } from './debug';
import { rasterStats } from './glowRaster';
import { glyphStats } from './glyphCache';

/** 한 번 그린 기록 (헤드리스 측정용) */
export interface DrawRecord {
  name: string;
  /** 그리는 데 쓴 JS 시간 (ms) */
  ms: number;
  /** 그다음 프레임 그리기(prerender → postrender, GPU 업로드 포함) 시간 (ms) */
  renderMs?: number;
  /** 발광 글자: 새로 구운 수 · 풀에서 빌린 수 · 글꼴 측정 횟수 */
  glyphs: number;
  reused: number;
  measures: number;
  /** 같은 이름이 몇 번째로 그려졌나 (1 = 처음) */
  nth: number;
}

const log: DrawRecord[] = [];
const counts = new Map<string, number>();

/**
 * 62 루프 2 UI D: 메뉴·지도를 여는 순간의 비용을 잰다 (`uidebug=1` 일 때만 — 아니면 fn 만 부른다).
 * 기록은 `window.__lopadUi.view.drawLog` (최근 40개).
 */
export function profileDraw<T>(scene: Phaser.Scene, name: string, fn: () => T): T {
  if (!uiDebugEnabled()) return fn();
  const d0 = glyphStats.misses;
  const h0 = glyphStats.hits;
  const m0 = rasterStats.measures;
  const t0 = performance.now();
  const out = fn();
  const nth = (counts.get(name) ?? 0) + 1;
  counts.set(name, nth);
  const rec: DrawRecord = {
    name,
    ms: Math.round((performance.now() - t0) * 10) / 10,
    glyphs: glyphStats.misses - d0,
    reused: glyphStats.hits - h0,
    measures: rasterStats.measures - m0,
    nth,
  };
  log.push(rec);
  if (log.length > 40) log.shift();
  debugExpose('drawLog', log);
  const ev = scene.game.events;
  let r0 = 0;
  ev.once('prerender', () => (r0 = performance.now()));
  ev.once('postrender', () => {
    if (r0) rec.renderMs = Math.round((performance.now() - r0) * 10) / 10;
  });
  return out;
}
