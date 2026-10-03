import Phaser from 'phaser';
import { gameConfig } from './config';
import { SCENES } from './core/Constants';
import { installContractHost } from './contract/host';
import { audio } from './systems/audio';
import { displayZoom, installLogicalCameras } from './systems/display';

document.addEventListener('DOMContentLoaded', () => {
  const game = new Phaser.Game(gameConfig);
  // 52라운드: 캔버스 1920×1080, 화면 고정 씬(UI 포함)은 논리 960×540 카메라. 월드 카메라 씬은 스스로 배율을 정한다
  installLogicalCameras(game, [SCENES.GAME, SCENES.WEAPON_LAB]);
  installContractHost(game);
  audio.attach(game);
  // 창 크기에 맞는 배율 (논리 정수 배율 — 픽셀이 고르게 유지됨)
  const apply = () => game.scale.setZoom(displayZoom(window.innerWidth, window.innerHeight));
  game.events.once(Phaser.Core.Events.READY, apply);
  window.addEventListener('resize', apply);
});
