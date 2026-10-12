/**
 * 61라운드 계약 §17 보스 UI 선택 필드: 스냅샷 `boss` 의 국면 이름·눈금 · 파훼 창 · 촛대(논리 960×540 화면 좌표) · 어둠,
 * 파훼·결정타 이벤트(`UI_EVENTS.BOSS_BREAK`) 페이로드. UiRelay 가 쓴다.
 */
import { BOSS_FX } from '../../core/Constants';
import { gameState } from '../../core/GameState';
import { BOSSES } from '../../data';
import type { UiBossBreak, UiBossSnapshot } from '../../contract/ui';
import { worldToLogicalScreen } from '../../systems/display';
import type { Game } from '../Game';

/** 시스템 파훼 이름 → 계약 이름 (취권 넘어짐 reel = stumble) */
const BREAK_KIND: Record<string, UiBossBreak['kind']> = {
  cup: 'cup',
  pillar: 'pillar',
  cask: 'cask',
  reel: 'stumble',
  finisher: 'finisher',
};

export function uiBossBreak(kind: string): UiBossBreak | null {
  const k = BREAK_KIND[kind];
  if (!k) return null;
  return { kind: k, label: BOSS_FX.BREAK_LABELS[k] };
}

/** 62 D (P1-14): 국면 공개 여부 — 지금 국면까지(1부터 센 phase) true */
export function phaseRevealed(count: number, phase: number): boolean[] {
  return Array.from({ length: count }, (_, i) => i < Math.max(1, phase));
}

/** 스냅샷 boss 선택 필드 (보스전이 아니면 null) */
export function bossSnapshotExtra(g: Game): Partial<UiBossSnapshot> | null {
  if (gameState.bossMaxHp <= 0) return null;
  const def = BOSSES[gameState.stage.boss];
  if (!def) return null;
  const phases = def.phases;
  const names = phases.map((p, i) => p.name ?? `${i + 1}`);
  // 62 D (P1-14): 앞으로 올 국면 이름은 그 국면이 될 때 공개 (하데스 — 등장 카드엔 '???', UI 가 그린다)
  const revealed = phaseRevealed(names.length, gameState.bossPhase);
  const out: Partial<UiBossSnapshot> = {
    phaseName: names[Math.max(0, Math.min(names.length - 1, gameState.bossPhase - 1))],
    phaseNames: names.map((n, i) => (revealed[i] ? n : '')),
    phaseRevealed: revealed,
    phaseMarks: phases.slice(1).map((p) => p.hpFraction),
  };
  const boss = g.bossFlow?.current ?? null;
  out.broken = boss ? boss.brokenWindow(g.time.now) : null;
  const arena = g.bossArena;
  if (arena) {
    const cam = g.cameras.main;
    out.dark = arena.dark;
    out.candles = arena.candles.list.map((c) => {
      const s = worldToLogicalScreen(cam, c.x, c.y);
      return { x: Math.round(s.x), y: Math.round(s.y), lit: c.state !== 'fallen' };
    });
  }
  return out;
}
