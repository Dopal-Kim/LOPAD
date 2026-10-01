import Phaser from 'phaser';
import { COLORS, GAME, KEYS, SCENES } from '../core/Constants';
import { EventBus, Events } from '../core/EventBus';
import { gameState } from '../core/GameState';

/**
 * 결과 화면 플레이스홀더. 정식 결과 화면은 UI 파트 소유이며,
 * 이 씬은 1단계 "사망/재시작" 검증용 최소 구현이다.
 */
export class GameOver extends Phaser.Scene {
  private cleared = false;

  constructor() {
    super(SCENES.GAME_OVER);
  }

  init(data: { cleared?: boolean }): void {
    this.cleared = Boolean(data?.cleared);
  }

  create(): void {
    const title = this.cleared ? 'CLEAR' : 'DEAD';
    const sub = `kills ${gameState.kills}  trials ${gameState.trialsCleared}/${gameState.trialsTotal}  seed ${gameState.seed}   -   click or [${KEYS.RESTART}] to restart`;
    this.add
      .text(GAME.WIDTH / 2, GAME.HEIGHT / 2 - 12, title, { font: '24px monospace', color: COLORS.GAMEOVER_TEXT })
      .setOrigin(0.5);
    this.add
      .text(GAME.WIDTH / 2, GAME.HEIGHT / 2 + 16, sub, { font: '10px monospace', color: COLORS.GAMEOVER_TEXT })
      .setOrigin(0.5);

    const restart = () => {
      EventBus.emit(Events.GAME_RESTART);
      this.scene.start(SCENES.GAME);
    };
    this.input.once('pointerdown', restart);
    this.input.keyboard!.once(`keydown-${KEYS.RESTART}`, restart);
  }
}
