import Phaser from 'phaser';
import { uiCommands, type UiResult } from '../contract/ui';
import { UI_SCENE_KEYS } from './keys';
import { THEME } from './theme';
import { uiText } from './text';
import { SelectList, label, panel } from './widgets';

/** 런 결과: 사망 / 클리어 */
export class ResultScene extends Phaser.Scene {
  private list?: SelectList;

  constructor() {
    super(UI_SCENE_KEYS.RESULT);
  }

  create(r: UiResult): void {
    const W = this.scale.width;
    const H = this.scale.height;
    this.cameras.main.setBackgroundColor('#0b0b10');
    panel(this, W / 2 - 180, 50, 360, H - 100);
    label(
      this,
      W / 2,
      62,
      r.cleared ? '런 클리어' : '쓰러졌다',
      THEME.fontTitle,
      r.cleared ? '#fff0a0' : '#e05050',
    ).setOrigin(0.5, 0);
    // 클리어 시 고른 엔딩 부제 (23라운드 ending). '런 클리어' 자체는 보류 문구 유지 (round-29 자율 결정 B)
    const endingKey =
      r.ending === 'destroy' ? 'clearedDestroy' : r.ending === 'understand' ? 'clearedUnderstand' : null;
    const endingDefault = r.ending === 'destroy' ? '다음 전장으로' : '처음으로 내일을 적었다';
    if (r.cleared && endingKey) {
      label(this, W / 2, 94, uiText('result', endingKey, endingDefault), THEME.fontHeading, '#fff0a0').setOrigin(
        0.5,
        0,
      );
    }
    const linesTop = r.cleared && endingKey ? 120 : 112;
    const lines = [
      r.line,
      `${r.playerName || '―'}   ${r.stageName}  (도달 ${r.floorReached}층)`,
      `처치 ${r.kills}   골드 ${r.gold}   감각 ${r.sense}`,
      `무기 ${r.weaponName}`,
      `영혼 +${r.soulsGained}  (보유 ${r.soulsTotal})`,
      `시드 ${r.seed}`,
    ];
    lines.forEach((t, i) =>
      label(
        this,
        W / 2,
        linesTop + i * 16,
        t,
        THEME.font,
        i === 4 ? '#9ad0ff' : i === 0 ? THEME.textDim : THEME.text,
      ).setOrigin(0.5, 0),
    );
    this.list = new SelectList(this, W / 2 - 100, H - 110, (key) => {
      if (key === '1') uiCommands.startNewRun();
      else uiCommands.toTitle();
    });
    this.list.setLines([
      { key: '1', label: uiText('result', 'retry', '다시 (영혼 강화 → 개성 선택)'), enabled: true },
      // '타이틀로'·'런 클리어' 는 보류 (round-29 자율 결정 B): 기본 문구 유지
      { key: '2', label: '타이틀로', enabled: true },
    ]);
    this.events.once('shutdown', () => this.list?.destroy());
  }
}
