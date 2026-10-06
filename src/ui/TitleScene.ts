import Phaser from 'phaser';
import { UI_SCREEN, uiCommands } from '../contract/ui';
import { GlowText } from './glow';
import { keyTaken, takeKey } from './keyGate';
import { DARK_BG, KIT, fontsReady, preloadKit, setupKit } from './kit';
import { UI_SCENE_KEYS } from './keys';
import { SettingsPanel } from './SettingsPanel';
import { controlsLine, r49Text, r61Text, trainingText, uiText } from './text';
import { ensureTransitionScene } from './TransitionScene';
import { SelectList } from './widgets';

/**
 * 타이틀: 펼친 일기장 장식 + 부제 + 이어 쓴다 / 다시 태어난다 / 무기 시험장(49라운드 §11.4) / 설정(61라운드 §15) + 조작법
 * (어두운 바탕, 잉크 글자). 설정은 일기장 한 쪽(SettingsPanel)으로 — Esc·'덮는다' 로 타이틀 목록에 돌아온다.
 */
export class TitleScene extends Phaser.Scene {
  private list?: SelectList;
  private alive = false;
  private settings?: SettingsPanel;
  private notice?: GlowText;

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
    this.settings = undefined;
    // 61 단계 6 (§19): 타이틀 → 수련장도 그림 속 입구로 들어간다
    ensureTransitionScene(this);
    this.input.keyboard?.on('keydown-ESC', this.onEsc);
    this.events.once('shutdown', () => {
      this.alive = false;
      this.input.keyboard?.off('keydown-ESC', this.onEsc);
      this.settings?.destroy();
      this.settings = undefined;
      this.list?.destroy();
    });
    fontsReady().then(() => {
      if (this.alive) this.build();
    });
  }

  /** Esc: 설정 쪽이 떠 있으면 덮는다 (그 밖에는 타이틀에서 할 일이 없다) */
  private onEsc = (e?: KeyboardEvent): void => {
    if (e?.repeat || !this.settings || keyTaken(e)) return;
    takeKey(e);
    this.settings.close();
  };

  private openSettings(): void {
    if (this.settings) return;
    this.list?.setEnabled(false);
    this.settings = new SettingsPanel(this, {
      stageIndex: 0,
      onClose: () => {
        this.settings = undefined;
        this.list?.setEnabled(true);
      },
    });
  }

  /** 61 단계 6 (§19): 수련장 — 받아들여지지 않으면 목록 아래 한 줄 */
  private startTraining(): void {
    const r = uiCommands.startTraining();
    if (r === 'ok') return;
    const why = r === 'combat' ? 'denyCombat' : r === 'boss' ? 'denyBoss' : 'denyBusy';
    this.notice?.setText(trainingText(why)).placeCenter(UI_SCREEN.WIDTH / 2, this.notice.y);
  }

  private build(): void {
    const W = UI_SCREEN.WIDTH;
    const H = UI_SCREEN.HEIGHT;
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
        else if (key === '3') this.startTraining();
        else if (key === '4') uiCommands.startWeaponLab();
        else if (key === '5') this.openSettings();
      },
      { surface: 'ink' },
    );
    this.list.setLines(
      hasSave
        ? [
            { key: '1', label: uiText('title', 'continue', '이어 쓴다'), enabled: true },
            { key: '2', label: uiText('title', 'newRunDeleteSave', '다시 태어난다 (일기장을 찢는다)'), enabled: true },
            { key: '3', label: trainingText('titleItem'), enabled: true },
            { key: '4', label: r49Text('titleLab'), enabled: true },
            { key: '5', label: r61Text('settingsItem'), enabled: true },
          ]
        : [
            { key: '1', label: uiText('title', 'newRun', '다시 태어난다'), enabled: true },
            { key: '2', label: uiText('title', 'continueNoSave', '이어 쓴다 (적힌 것이 없다)'), enabled: false },
            { key: '3', label: trainingText('titleItem'), enabled: true },
            { key: '4', label: r49Text('titleLab'), enabled: true },
            { key: '5', label: r61Text('settingsItem'), enabled: true },
          ],
    );
    // 목록을 가운데에 (항목 폭 기준)
    const w = this.list.maxWidth();
    this.list.setPosition(Math.round(cx - w / 2), 320);
    this.notice = new GlowText(this, 0, 320 + this.list.height() + 6, '', 'ink_faint');
    // 타이틀에선 무기가 정해지기 전이므로 {secondary} 는 '보조 동작' 으로 치환된다
    const controls = new GlowText(
      this,
      0,
      0,
      controlsLine(uiCommands.getUiSnapshot().weapon.secondaryName),
      'ink_faint',
      {
        wrap: W - 48,
        align: 'center',
      },
    );
    controls.placeCenter(cx, H - 48);
  }
}
