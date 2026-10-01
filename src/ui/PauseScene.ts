import Phaser from 'phaser';
import { UI_EVENTS, uiBus, uiCommands } from '../contract/ui';
import { UI_SCENE_KEYS } from './keys';
import { THEME } from './theme';
import { SelectList, label, panel } from './widgets';

/** 일시정지: 능력치·패시브·감각·조작법, 재개 / 타이틀로 */
export class PauseScene extends Phaser.Scene {
  private list?: SelectList;
  private confirm = false;
  private escKey?: Phaser.Input.Keyboard.Key;
  private onResumed = () => this.scene.stop();

  constructor() {
    super(UI_SCENE_KEYS.PAUSE);
  }

  create(): void {
    const s = uiCommands.getUiSnapshot();
    const W = this.scale.width;
    const H = this.scale.height;
    this.confirm = false;
    panel(this, 60, 40, W - 120, H - 80);
    label(this, W / 2, 50, '일시정지', THEME.fontHeading).setOrigin(0.5, 0);
    const lines = [
      `${s.playerName || '―'}   ${s.floorTitle || s.stageName}   시련 ${s.trialsCleared}/${s.trialsTotal}   세이브 남음 ${s.savesLeft}   시드 ${s.seed}`,
      `공격 ${s.stats.attack}  방어 ${s.stats.defense}  치명타 ${s.stats.crit}%  감각 ${s.stats.sense}`,
      `무기: ${s.weapon.name}${s.weapon.evolutionName ? ` · ${s.weapon.evolutionName}` : ''}  (개성 ${s.weapon.personality}/${s.weapon.threshold})`,
      `패시브: ${s.passives.length ? s.passives.map((p) => `${p.name}${p.level > 1 ? ` Lv${p.level}` : ''}`).join(', ') : '-'}`,
      '',
      'WASD 이동 · 좌클릭 공격 · 우클릭 ' + s.weapon.secondaryName + ' · 스페이스 대쉬 · Q 물약',
    ];
    lines.forEach((t, i) => label(this, 80, 80 + i * 14, t, THEME.font, i === 5 ? THEME.textDim : THEME.text));
    this.list = new SelectList(this, 80, H - 90, (key) => this.choose(key));
    this.setList();
    this.escKey = this.input.keyboard?.addKey('ESC');
    uiBus.on(UI_EVENTS.RESUMED, this.onResumed);
    this.events.once('shutdown', () => {
      uiBus.off(UI_EVENTS.RESUMED, this.onResumed);
      this.list?.destroy();
    });
  }

  update(): void {
    if (this.escKey && Phaser.Input.Keyboard.JustDown(this.escKey)) uiCommands.resume();
  }

  private setList(): void {
    this.list?.setLines(
      this.confirm
        ? [
            { key: '1', label: '정말 타이틀로? 저장되지 않은 진행은 사라집니다 — 예', enabled: true },
            { key: '2', label: '아니오', enabled: true },
          ]
        : [
            { key: '1', label: '계속하기 (Esc)', enabled: true },
            { key: '2', label: '타이틀로', enabled: true },
          ],
    );
  }

  private choose(key: string): void {
    if (!this.confirm) {
      if (key === '1') uiCommands.resume();
      else {
        this.confirm = true;
        this.setList();
      }
    } else if (key === '1') uiCommands.toTitle();
    else {
      this.confirm = false;
      this.setList();
    }
  }
}
