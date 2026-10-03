import Phaser from 'phaser';
import { GAME } from './core/Constants';
import { Boot } from './scenes/Boot';
import { Game } from './scenes/Game';
import { GameOver } from './scenes/GameOver';
import { Preloader } from './scenes/Preloader';
import { Setup } from './scenes/Setup';
import { WeaponLab } from './scenes/WeaponLab';
import { uiScenes } from './ui';
import { CANVAS_H, CANVAS_W } from './systems/display';

/**
 * 논리 해상도 960×540(32라운드), 52라운드 Q8: 실제 캔버스 1920×1080(× RENDER.RESOLUTION — 카메라가 그만큼 더 확대, systems/display.ts).
 * 창 표시 배율은 main.ts
 */
export const gameConfig: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,
  parent: 'game-container',
  width: CANVAS_W,
  height: CANVAS_H,
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
  scene: [Boot, Preloader, Setup, Game, WeaponLab, GameOver, ...uiScenes],
};
