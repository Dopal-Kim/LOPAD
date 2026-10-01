import Phaser from 'phaser';
import { uiCommands } from '../contract/ui';
import { UI_SCENE_KEYS } from './keys';
import { THEME } from './theme';
import { SelectList, label, panel } from './widgets';

/** 타이틀: 이어하기 / 새 런 / 조작법 */
export class TitleScene extends Phaser.Scene {
  private list?: SelectList;

  constructor() {
    super(UI_SCENE_KEYS.TITLE);
  }

  create(): void {
    uiCommands.registerRenderer();
    const W = this.scale.width;
    const H = this.scale.height;
    this.cameras.main.setBackgroundColor('#0b0b10');
    label(this, W / 2, H * 0.22, 'LOPAD', THEME.fontTitle).setOrigin(0.5);
    label(this, W / 2, H * 0.22 + 30, '로파드식 메가봉크 순수 도파민 사기치기', THEME.font, THEME.textDim).setOrigin(
      0.5,
    );

    const hasSave = uiCommands.hasSave();
    panel(this, W / 2 - 110, H * 0.45 - 10, 220, 70);
    this.list = new SelectList(this, W / 2 - 100, H * 0.45, (key) => {
      if (key === '1') {
        if (hasSave) uiCommands.continueRun();
        else uiCommands.startNewRun();
      } else if (key === '2' && hasSave) uiCommands.startNewRun();
    });
    this.list.setLines(
      hasSave
        ? [
            { key: '1', label: '이어하기', enabled: true },
            { key: '2', label: '새 런 (세이브 삭제)', enabled: true },
          ]
        : [
            { key: '1', label: '새 런', enabled: true },
            { key: '2', label: '이어하기 (세이브 없음)', enabled: false },
          ],
    );
    label(
      this,
      W / 2,
      H * 0.8,
      'WASD 이동 · 좌클릭 공격 · 우클릭 보조 동작 · 스페이스 대쉬 · Q 물약 · Esc 일시정지',
      THEME.font,
      THEME.textDim,
    ).setOrigin(0.5);
    this.events.once('shutdown', () => this.list?.destroy());
  }
}
