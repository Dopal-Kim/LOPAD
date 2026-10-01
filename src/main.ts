import Phaser from 'phaser';
import { gameConfig } from './config';
import { GAME } from './core/Constants';
import { installContractHost } from './contract/host';
import { audio } from './systems/audio';

/** 창 크기에 맞는 가장 큰 정수 배율로 캔버스를 키운다 (픽셀이 고르게 유지됨). */
function integerZoom(): number {
  const z = Math.floor(Math.min(window.innerWidth / GAME.WIDTH, window.innerHeight / GAME.HEIGHT));
  return Math.max(GAME.MIN_ZOOM, z);
}

document.addEventListener('DOMContentLoaded', () => {
  const game = new Phaser.Game(gameConfig);
  installContractHost(game);
  audio.attach(game);
  const apply = () => game.scale.setZoom(integerZoom());
  game.events.once(Phaser.Core.Events.READY, apply);
  window.addEventListener('resize', apply);
});
