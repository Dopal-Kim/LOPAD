import Phaser from 'phaser';
import { uiCommands } from '../contract/ui';
import { UI_SCENE_KEYS } from './keys';
import { THEME } from './theme';
import { controlsLine, uiText } from './text';
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
    label(
      this,
      W / 2,
      H * 0.22 + 30,
      uiText('title', 'subtitle', '로파드식 메가봉크 순수 도파민 사기치기'),
      THEME.font,
      THEME.textDim,
    ).setOrigin(0.5);

    const hasSave = uiCommands.hasSave();
    this.list = new SelectList(this, 0, H * 0.45, (key) => {
      if (key === '1') {
        if (hasSave) uiCommands.continueRun();
        else uiCommands.startNewRun();
      } else if (key === '2' && hasSave) uiCommands.startNewRun();
    });
    this.list.setLines(
      hasSave
        ? [
            { key: '1', label: uiText('title', 'continue', '이어하기'), enabled: true },
            { key: '2', label: uiText('title', 'newRunDeleteSave', '새 런 (세이브 삭제)'), enabled: true },
          ]
        : [
            { key: '1', label: uiText('title', 'newRun', '새 런'), enabled: true },
            { key: '2', label: uiText('title', 'continueNoSave', '이어하기 (세이브 없음)'), enabled: false },
          ],
    );
    // 패널은 항목 폭에 맞춘다 (세계관 문구가 길어도 잘리지 않게). 항목은 패널 위에 (depth 1)
    const w = Math.max(220, this.list.maxWidth() + 20);
    panel(this, W / 2 - w / 2, H * 0.45 - 10, w, 70).setDepth(0);
    this.list.setPosition(W / 2 - w / 2 + 10, H * 0.45).setDepth(1);
    // 타이틀에선 무기가 정해지기 전이므로 {secondary} 는 '보조 동작' 으로 치환된다
    label(
      this,
      W / 2,
      H * 0.8,
      controlsLine(uiCommands.getUiSnapshot().weapon.secondaryName),
      THEME.font,
      THEME.textDim,
    ).setOrigin(0.5);
    this.events.once('shutdown', () => this.list?.destroy());
  }
}
