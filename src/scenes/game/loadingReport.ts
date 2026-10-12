/**
 * 62 루프 2 시스템 D (P2-6 · 계약 UI §22): 씬 로더 진행률 → `ui:loading` (부팅 Preloader · 노드 Game preload · 수련장).
 * 노드·보스면 들어갈 지역(키아트) · 단서 팁 한 줄(같은 생 안 중복 없음, 일기장 단서 조건). 끝나면 done true 로 한 번.
 */
import Phaser from 'phaser';
import { gameState } from '../../core/GameState';
import { UI_EVENTS, __system, type UiLoading } from '../../contract/ui';
import { LOADING_TIPS } from '../../data/loading';
import { pickTip } from '../../systems/loadingTips';
import { diaryNow } from '../../systems/narrative/diary';
import { regionIdOf } from '../../systems/route';

/** 이 생에 보인 팁 (시드가 바뀌면 = 새 생이면 비움) */
let used: { seed: string; texts: string[] } = { seed: '', texts: [] };

function nextTip(): UiLoading['tip'] {
  if (used.seed !== gameState.seed) used = { seed: gameState.seed, texts: [] };
  let clues: readonly string[];
  try {
    clues = diaryNow().clues;
  } catch {
    clues = [];
  }
  const r = pickTip(LOADING_TIPS, clues, used.texts, Math.random());
  used.texts = r.used;
  return r.tip ? { kind: r.tip.kind, text: r.tip.text } : undefined;
}

/** 들어갈 노드 지역 (노드 지도 런만) */
function nodeRegion(): string | undefined {
  const route = gameState.route;
  const n = route?.current;
  return route && n ? (regionIdOf(route.graph.stageId, n.col) ?? undefined) : undefined;
}

export function reportLoading(scene: Phaser.Scene, phase: UiLoading['phase']): void {
  const region = phase === 'node' || phase === 'boss' ? nodeRegion() : undefined;
  const tip = phase === 'prefetch' ? undefined : nextTip();
  const emit = (progress: number, done: boolean) =>
    __system.emit(UI_EVENTS.LOADING, {
      phase,
      progress: Math.max(0, Math.min(1, progress)),
      done,
      ...(region ? { region } : {}),
      ...(tip ? { tip } : {}),
    } satisfies UiLoading);
  emit(0, false);
  const onProgress = (v: number) => emit(v, false);
  scene.load.on(Phaser.Loader.Events.PROGRESS, onProgress);
  scene.load.once(Phaser.Loader.Events.COMPLETE, () => {
    scene.load.off(Phaser.Loader.Events.PROGRESS, onProgress);
    emit(1, true);
  });
}
