import Phaser from 'phaser';
import { SCENES } from '../core/Constants';

/** 1단계 프로토타입은 로드할 에셋이 없다. 아트·음향 산출물이 계약으로 들어오면 여기서 로드. */
export class Preloader extends Phaser.Scene {
  constructor() {
    super(SCENES.PRELOADER);
  }

  create(): void {
    this.scene.start(SCENES.GAME);
  }
}
