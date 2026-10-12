/**
 * `?debug=1` 62 루프 2 C 검증 훅 (`__lopadRunEnd.*`) — 층 끝 결산·죽음 연출·결산·출구 방향 (게임 로직 아님).
 */
import type Phaser from 'phaser';
import { gameState } from '../../../core/GameState';
import { ownedRelics } from '../../../systems/relics';
import type { Game } from '../../Game';

export function runEndDebug(g: Game) {
  return {
    /** 지금 흐름 · 사건 기록 · 먹 번짐 진행 · 이번 생 기억 */
    state: () => ({
      phase: g.runEnd.floorPhase,
      finalFloor: g.runEnd.finalFloor,
      log: [...g.runEnd.log],
      ink: g.runEnd.inkProgress,
      memory: gameState.memory.toSave(),
      relics: ownedRelics(gameState.passives, gameState.weapon.id).map((r) => `${r.id}:${r.level}`),
      gameOver: gameState.gameOver,
      active: g.scene.isActive(),
      paused: g.scene.isPaused(),
      now: Math.round(g.time.now),
      timePaused: g.time.paused,
      timeScale: g.time.timeScale,
      fps: Math.round(g.game.loop.actualFps),
      timers: ((g.time as unknown as { _active?: Phaser.Time.TimerEvent[] })._active ?? []).map(
        (e) => `${Math.round(e.elapsed)}/${e.delay}${e.paused ? 'p' : ''}x${e.timeScale}`,
      ),
      scenes: g.scene.manager
        .getScenes(false)
        .filter((s) => s.sys.isActive() || s.sys.isPaused())
        .map((s) => `${s.sys.settings.key}${s.sys.isPaused() ? '(p)' : ''}`),
      lastResult: g.progress.debugLastResult !== null,
      cleared: gameState.cleared,
    }),
    exitHint: () => g.runEnd.exitHint(),
    result: () => g.progress.debugLastResult,
    floorEnd: () => g.runEnd.floorEnd(),
    summary: (cause: 'death' | 'floorEnd' = 'death') => g.runEnd.summary(cause),
    /** 주인공을 바로 쓰러뜨린다 (기존 사망 흐름) */
    killPlayer: () => {
      gameState.hp = 1;
      g.player.grantInvulnerable(0);
      return g.player.takeHit(9999, g.time.now + 100000);
    },
  };
}
