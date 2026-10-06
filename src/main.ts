import Phaser from 'phaser';
import { gameConfig } from './config';
import { SCENES } from './core/Constants';
import { installContractHost } from './contract/host';
import { audio } from './systems/audio/audio';
import { settings } from './systems/settings';
import { runLogRecorder } from './systems/runlog/runLogRecorder';
import { installBootDebug } from './debug/boot';
import { displayZoom, installLogicalCameras } from './systems/display';

document.addEventListener('DOMContentLoaded', () => {
  const game = new Phaser.Game(gameConfig);
  // 52라운드: 캔버스 1920×1080, 화면 고정 씬(UI 포함)은 논리 960×540 카메라. 월드 카메라 씬은 스스로 배율을 정한다
  installLogicalCameras(game, [SCENES.GAME, SCENES.WEAPON_LAB, SCENES.TRAINING]);
  installContractHost(game);
  audio.attach(game);
  // 61라운드 §15: 저장된 설정(흔들림·섬광·기울기·피해 숫자·음량)을 부팅 때 적용 — UI 는 스냅샷 settings 로 받는다
  settings.load((v) => audio.setVolumes(v));
  // 61라운드 P9: 런 로그 (노드별 시간·처치·피격·메뉴·선택·사망 원인 → 메타 세이브 최근 N개)
  runLogRecorder.attach(game);
  // ?debug: 게임 씬 전(타이틀)에도 __lopad.runlog · __lopad.vram · __lopad.settings
  installBootDebug(game);
  // 창 크기에 맞는 배율 (논리 정수 배율 — 픽셀이 고르게 유지됨)
  const apply = () => game.scale.setZoom(displayZoom(window.innerWidth, window.innerHeight));
  game.events.once(Phaser.Core.Events.READY, apply);
  window.addEventListener('resize', apply);
});
