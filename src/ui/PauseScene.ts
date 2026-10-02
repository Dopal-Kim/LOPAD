import Phaser from 'phaser';
import { UI_EVENTS, uiBus, uiCommands } from '../contract/ui';
import { withDebug } from './debug';
import { GlowText } from './glow';
import { ICON, book, fontsReady, icon, preloadKit, rule, setupKit } from './kit';
import { UI_SCENE_KEYS } from './keys';
import { hasRoute } from './routeView';
import { controlsLine, uiText } from './text';
import { SelectList } from './widgets';

const PAGE_W = 440;
const PAGE_H = 264;
const PAD = 24;

/**
 * 일시정지 = 일기장 한 페이지 (31라운드 채택 문구): 제목 '일기장', 이름·층·시련·세이브, 능력치, 무기, 패시브, 조작법,
 * '더 쓴다 (Esc)' / '일기장을 덮는다' → 확인 '적지 않은 것은 남지 않는다. 그래도 덮는다 — 예' / '더 쓴다'
 */
export class PauseScene extends Phaser.Scene {
  private list?: SelectList;
  private confirm = false;
  private alive = false;
  private onResumed = () => this.scene.stop();

  constructor() {
    super(UI_SCENE_KEYS.PAUSE);
  }

  preload(): void {
    preloadKit(this);
  }

  create(): void {
    this.confirm = false;
    this.alive = true;
    setupKit(this);
    // keydown 이벤트로 (HudScene 참조). Key 객체를 만들지 않는다
    this.input.keyboard?.on('keydown-ESC', this.onEsc);
    uiBus.on(UI_EVENTS.RESUMED, this.onResumed);
    this.events.once('shutdown', () => {
      this.alive = false;
      this.input.keyboard?.off('keydown-ESC', this.onEsc);
      uiBus.off(UI_EVENTS.RESUMED, this.onResumed);
      this.list?.destroy();
    });
    fontsReady().then(() => {
      if (this.alive) this.build();
    });
  }

  private onEsc = (): void => {
    uiCommands.resume();
  };

  private build(): void {
    const s = withDebug(uiCommands.getUiSnapshot());
    const stageIndex = Math.max(0, s.stageIndex);
    const W = this.scale.width;
    const H = this.scale.height;
    const bk = book(this, Math.round(W / 2), Math.round(H / 2), PAGE_W, PAGE_H, 1, 'pause');
    const pg = bk.pages[0];
    const innerW = PAGE_W - PAD * 2;
    let y = pg.y + 14;
    const title = new GlowText(this, 0, 0, uiText('pause', 'title', '일기장'), 'page_title', {
      font: 'title',
      stageIndex,
    });
    title.placeCenter(pg.x + PAGE_W / 2, y);
    y += title.displayHeight + 6;
    rule(this, pg.x + PAD, y, innerW);
    y += 4 + 10;
    const evo = s.weapon.evolutionName ? ` · ${s.weapon.evolutionName}` : '';
    const lines = [
      // 48라운드: 노드 지도 층이면 시련 수 대신 지금 노드 이름
      `${s.playerName || '―'}   ${s.floorTitle || s.stageName}   ${
        hasRoute(s.route)
          ? (s.route.nodes.find((n) => n.id === s.route?.currentId)?.name ?? '')
          : `시련 ${s.trialsCleared}/${s.trialsTotal}`
      }`,
      `공격 ${s.stats.attack}   방어 ${s.stats.defense}   치명타 ${s.stats.crit}%   감각 ${s.stats.sense}`,
      `무기: ${s.weapon.name}${evo}   (개성 ${s.weapon.personality}/${s.weapon.threshold})`,
      `패시브: ${s.passives.length ? s.passives.map((p) => `${p.name}${p.level > 1 ? ` Lv${p.level}` : ''}`).join(', ') : '―'}`,
    ];
    for (const t of lines) {
      const g = new GlowText(this, pg.x + PAD, y, t, 'page_body', { wrap: innerW, stageIndex });
      y += g.displayHeight + 2;
    }
    // 세이브 남음 (닫힌 일기장 아이콘) + 시드 (흐림)
    icon(this, pg.x + PAD, y - 1, ICON.save);
    new GlowText(this, pg.x + PAD + 20, y, `세이브 남음 ${s.savesLeft}`, 'page_body', { stageIndex });
    new GlowText(this, 0, y, `시드 ${s.seed}`, 'page_faint').placeRight(pg.x + PAGE_W - PAD, y);
    y += 16 + 6;
    rule(this, pg.x + PAD, y, innerW);
    y += 4 + 10;
    this.list = new SelectList(this, pg.x + PAD, y, (key) => this.choose(key), { stageIndex, detailWrap: innerW - 40 });
    this.setList();
    y += 18 * 2 + 10;
    new GlowText(this, pg.x + PAD, y, controlsLine(s.weapon.secondaryName, hasRoute(s.route)), 'page_faint', { wrap: innerW });
  }

  private setList(): void {
    this.list?.setLines(
      this.confirm
        ? [
            {
              key: '1',
              label: uiText('pause', 'confirmQuit', '적지 않은 것은 남지 않는다. 그래도 덮는다 — 예'),
              enabled: true,
            },
            { key: '2', label: uiText('pause', 'cancelQuit', '더 쓴다'), enabled: true },
          ]
        : [
            { key: '1', label: `${uiText('pause', 'cancelQuit', '더 쓴다')} (Esc)`, enabled: true },
            { key: '2', label: uiText('pause', 'toTitle', '일기장을 덮는다'), enabled: true },
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
