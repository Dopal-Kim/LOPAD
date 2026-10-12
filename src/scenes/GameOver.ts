import Phaser from 'phaser';
import { COLORS, GAME, KEYS, RITUAL, SCENES } from '../core/Constants';
import { EventBus, Events } from '../core/EventBus';
import { gameState } from '../core/GameState';
import { STORY } from '../data';
import { metaStore } from '../systems/meta';
import { ensureFont, fontFamilyOr } from '../systems/fonts';

/**
 * 결과 화면 대체 (시스템): UI 결과 씬(`UI_SCENES.RESULT`)이 없을 때만 뜬다 — 정식 결산(사망 연출·일기장)은 UI 파트 몫(루프 2).
 * 62 P2-9: 시드를 보이지 않는다 · 고정폭 글꼴 대신 Galmuri11(로드 전 sans-serif) · 문구는 스토리 팩(`story.json ui.result`).
 */
export class GameOver extends Phaser.Scene {
  private cleared = false;

  constructor() {
    super(SCENES.GAME_OVER);
  }

  init(data: { cleared?: boolean }): void {
    this.cleared = Boolean(data?.cleared);
  }

  create(): void {
    const V = RITUAL.VIEW;
    const family = () => `${fontFamilyOr(V.FONT_FAMILY, V.FONT_FALLBACK)}, ${V.FONT_FALLBACK}`;
    const R = STORY.ui.result ?? {};
    const title = (this.cleared ? R.cleared : R.died) ?? '';
    const names = STORY.names;
    const souls = `${names.souls} +${gameState.lastSoulGain}  ·  ${metaStore.read().souls}`;
    const sub = `${gameState.stage.name}  ·  ${gameState.kills}  ·  ${gameState.weapon.displayName}`;
    const retry = `[${KEYS.RESTART}] ${R.retry ?? ''}`;
    const texts = [
      this.add.text(GAME.WIDTH / 2, GAME.HEIGHT / 2 - 40, title, { fontSize: `${V.TITLE_PX}px` }),
      this.add.text(GAME.WIDTH / 2, GAME.HEIGHT / 2, sub, { fontSize: `${V.BODY_PX}px` }),
      this.add.text(GAME.WIDTH / 2, GAME.HEIGHT / 2 + 22, souls, { fontSize: `${V.BODY_PX}px` }),
      this.add.text(GAME.WIDTH / 2, GAME.HEIGHT / 2 + 60, retry, { fontSize: `${V.BODY_PX}px` }),
    ];
    for (const t of texts) t.setOrigin(0.5).setColor(COLORS.GAMEOVER_TEXT).setFontFamily(family());
    void ensureFont(V.FONT_FAMILY, V.BODY_PX).then((ok) => {
      if (ok && this.sys.isActive()) for (const t of texts) t.setFontFamily(family());
    });

    const restart = () => {
      EventBus.emit(Events.GAME_RESTART);
      const forced = typeof location !== 'undefined' ? new URLSearchParams(location.search).get('weapon') : null;
      if (forced) this.scene.start(SCENES.GAME, { mode: 'new', weapon: forced });
      else this.scene.start(SCENES.SETUP);
    };
    this.input.once('pointerdown', restart);
    this.input.keyboard!.once(`keydown-${KEYS.RESTART}`, restart);
  }
}
