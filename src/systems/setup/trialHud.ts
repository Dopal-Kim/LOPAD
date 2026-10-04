/**
 * 회피 시험 자리표시 화면 글자 (시스템 파트 플레이스홀더, UI 파트 산출물로 교체 대상):
 * 위쪽 진행 줄(Setup 의 라벨) + 가운데 카드(제목 카드 · 과제 결과 한 줄 · 전체 결과)와 그 뒤 어두운 판.
 * 글자는 확대 없는 UI 카메라에서만 보인다(Setup 이 `objects` 를 메인 카메라에서 뺀다).
 */
import Phaser from 'phaser';
import { COLORS, DEPTH, GAME, PLACEHOLDER_UI } from '../../core/Constants';
import type { TrialResult } from '../dodgeTrial/dodgeTrial';
import type { TrialStatus } from '../dodgeTrial/dodgeTrialRunner';
import { cardText, resultText, statusLine, taskLine } from './trialText';

/** 카드 판 알파 (제목 카드 · 과제 결과 · 전체 결과) · 판 여백 px */
const LOOK = { CARD_ALPHA: 0.62, CLEAR_ALPHA: 0.4, RESULT_ALPHA: 0.7, PAD: 18 };

export class TrialHud {
  private readonly panel: Phaser.GameObjects.Rectangle;
  private readonly card: Phaser.GameObjects.Text;
  private shown = '';

  constructor(
    scene: Phaser.Scene,
    private readonly label: Phaser.GameObjects.Text,
  ) {
    this.panel = scene.add
      .rectangle(GAME.WIDTH / 2, GAME.HEIGHT / 2, 10, 10, 0x000000, LOOK.CARD_ALPHA)
      .setDepth(DEPTH.DEBUG - 1)
      .setVisible(false);
    this.card = scene.add
      .text(GAME.WIDTH / 2, GAME.HEIGHT / 2, '', {
        font: PLACEHOLDER_UI.FONT_BODY,
        color: COLORS.GAMEOVER_TEXT,
        align: 'center',
        lineSpacing: 4,
      })
      .setOrigin(0.5)
      .setDepth(DEPTH.DEBUG)
      .setVisible(false);
  }

  /** UI 카메라 전용 */
  get objects(): Phaser.GameObjects.GameObject[] {
    return [this.panel, this.card];
  }

  /** 진행 상태 → 진행 줄·카드 */
  update(st: TrialStatus): void {
    this.label.setText(statusLine(st));
    if (st.phase === 'card') this.showCard(cardText(st), LOOK.CARD_ALPHA);
    else if (st.phase === 'clear' && st.results.length > 0)
      this.showCard(taskLine(st.results[st.results.length - 1]), LOOK.CLEAR_ALPHA);
    else this.hideCard();
  }

  showResult(r: TrialResult): void {
    this.label.setText('');
    this.showCard(resultText(r), LOOK.RESULT_ALPHA);
  }

  hideCard(): void {
    if (!this.card.visible) return;
    this.card.setVisible(false);
    this.panel.setVisible(false);
    this.shown = '';
  }

  destroy(): void {
    this.panel.destroy();
    this.card.destroy();
  }

  private showCard(text: string, alpha: number): void {
    if (this.shown === text && this.card.visible) return;
    this.shown = text;
    this.card.setText(text).setVisible(true);
    this.panel
      .setSize(this.card.width + LOOK.PAD * 2, this.card.height + LOOK.PAD * 2)
      .setFillStyle(0x000000, alpha)
      .setVisible(true);
  }
}
