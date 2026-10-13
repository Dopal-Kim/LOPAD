/**
 * 62 루프 3 시스템 I (P0-N2·P1-N3): 매 프레임 E 대상 하나를 고른다 — 구조물·상인·노점·소품 가운데 가장 가까운 곳만
 * 화면 프롬프트(스냅샷 interactable·shopOffer)에 보이고 E 를 받는다. 규칙은 `systems/interactFocus.pickFocus`.
 * 입력을 읽기 전에(구조물·소품·상점 update 보다 먼저) 부른다.
 */
import { pickFocus, type FocusCandidate, type FocusSource } from '../../systems/interactFocus';
import type { Game } from '../Game';

function cand(source: FocusSource, dist: number | null | undefined): FocusCandidate | null {
  return dist === null || dist === undefined ? null : { source, dist };
}

export class InteractFocus {
  current: FocusSource | null = null;

  constructor(private readonly g: Game) {}

  update(): FocusSource | null {
    const g = this.g;
    const src = pickFocus([
      cand('structure', g.structures?.focusDist()),
      cand('keeper', g.economy?.keeperFocusDist()),
      cand('stall', g.economy?.stallFocusDist()),
      cand('prop', g.bundle?.focusDist()),
    ]);
    this.current = src;
    g.structures?.setFocused(src === 'structure');
    g.economy?.setFocus(src);
    g.bundle?.setFocused(src === 'prop');
    return src;
  }
}
