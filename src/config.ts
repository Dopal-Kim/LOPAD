import Phaser from 'phaser';
import { GAME } from './core/Constants';
import { Boot } from './scenes/Boot';
import { Game } from './scenes/Game';
import { GameOver } from './scenes/GameOver';
import { Preloader } from './scenes/Preloader';
import { Setup } from './scenes/Setup';
import { uiScenes } from './ui';

/** 내부 해상도 960×540 고정(32라운드), 정수 배율 확대는 main.ts 에서 처리. */
export const gameConfig: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,
  parent: 'game-container',
  width: GAME.WIDTH,
  height: GAME.HEIGHT,
  backgroundColor: GAME.BACKGROUND_COLOR,
  pixelArt: true,
  roundPixels: true,
  dom: { createContainer: true },
  scale: {
    mode: Phaser.Scale.NONE,
    autoCenter: Phaser.Scale.CENTER_BOTH,
  },
  physics: {
    default: 'arcade',
    arcade: { gravity: { x: 0, y: 0 }, debug: false },
  },
  scene: [Boot, Preloader, Setup, Game, GameOver, ...uiScenes],
};
