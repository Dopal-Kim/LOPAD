import Phaser from 'phaser';
import { uiCommands } from '../contract/ui';
import { GlowText } from './glow';
import { DARK_BG, KIT, fontsReady, preloadKit, setupKit } from './kit';
import { UI_SCENE_KEYS } from './keys';
import { controlsLine, uiText } from './text';
import { SelectList } from './widgets';

/** 타이틀: 펼친 일기장 장식 + 부제 + 이어 쓴다 / 다시 태어난다 + 조작법 (어두운 바탕, 잉크 글자) */
export class TitleScene extends Phaser.Scene {
  private list?: SelectList;
  private alive = false;

  constructor() {
    super(UI_SCENE_KEYS.TITLE);
  }

  preload(): void {
    preloadKit(this);
  }

  create(): void {
    uiCommands.registerRenderer();
    setupKit(this);
    this.cameras.main.setBackgroundColor(DARK_BG);
    this.alive = true;
    this.events.once('shutdown', () => {
      this.alive = false;
      this.list?.destroy();
    });
    fontsReady().then(() => {
      if (this.alive) this.build();
    });
  }

  private build(): void {
    const W = this.scale.width;
    const H = this.scale.height;
    const cx = W / 2;
    // 펼친 일기장 (160×96) 2배 정수 확대
    if (this.textures.exists(KIT.titleDiary)) this.add.image(cx, 128, KIT.titleDiary).setScale(2);
    const title = new GlowText(this, 0, 0, 'LOPAD', 'ink_body', { font: 'title', scale: 2 });
    title.placeCenter(cx, 236);
    const sub = new GlowText(this, 0, 0, uiText('title', 'subtitle', '다시 태어난다. 기록만 남는다.'), 'ink_faint');
    sub.placeCenter(cx, 272);

    const hasSave = uiCommands.hasSave();
    this.list = new SelectList(
      this,
      0,
      320,
      (key) => {
        if (key === '1') {
          if (hasSave) uiCommands.continueRun();
          else uiCommands.startNewRun();
        } else if (key === '2' && hasSave) uiCommands.startNewRun();
      },
      { surface: 'ink' },
    );
    this.list.setLines(
      hasSave
        ? [
            { key: '1', label: uiText('title', 'continue', '이어 쓴다'), enabled: true },
            { key: '2', label: uiText('title', 'newRunDeleteSave', '다시 태어난다 (일기장을 찢는다)'), enabled: true },
          ]
        : [
            { key: '1', label: uiText('title', 'newRun', '다시 태어난다'), enabled: true },
            { key: '2', label: uiText('title', 'continueNoSave', '이어 쓴다 (적힌 것이 없다)'), enabled: false },
          ],
    );
    // 목록을 가운데에 (항목 폭 기준)
    const w = this.list.maxWidth();
    this.list.setPosition(Math.round(cx - w / 2), 320);
    // 타이틀에선 무기가 정해지기 전이므로 {secondary} 는 '보조 동작' 으로 치환된다
    const controls = new GlowText(
      this,
      0,
      0,
      controlsLine(uiCommands.getUiSnapshot().weapon.secondaryName),
      'ink_faint',
      {
        wrap: W - 160,
        align: 'center',
      },
    );
    controls.placeCenter(cx, H - 48);
  }
}
