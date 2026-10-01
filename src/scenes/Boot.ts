import Phaser from 'phaser';
import { SCENES } from '../core/Constants';

export class Boot extends Phaser.Scene {
  constructor() {
    super(SCENES.BOOT);
  }

  create(): void {
    this.scene.start(SCENES.PRELOADER);
  }
}
