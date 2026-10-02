import Phaser from 'phaser';
import { UI_EVENTS, uiBus, uiCommands } from '../contract/ui';
import { setMutedCmd, withDebug } from './debug';
import { GlowText } from './glow';
import { ICON, book, fontsReady, icon, preloadKit, rule, setupKit } from './kit';
import { UI_SCENE_KEYS } from './keys';
import { hasRoute } from './routeView';
import { controlsLine, r49Text, uiText } from './text';
import { SelectList } from './widgets';

const PAGE_W = 440;
const PAGE_H = 282;
const PAD = 24;

/**
 * 일시정지 = 일기장 한 페이지 (31라운드 채택 문구): 제목 '일기장', 이름·층·시련·세이브, 능력치, 무기, 패시브, 조작법,
 * '더 쓴다 (Esc)' / '소리 끄기·켜기' / '일기장을 덮는다' → 확인 '적지 않은 것은 남지 않는다. 그래도 덮는다 — 예' / '더 쓴다'
 * 49라운드(계약 §11.3·§11.4): 소리 항목 → `setMuted`, 상태는 `snapshot.muted`. 무기 시험장(`lab`)이면 제목 '무기 시험장',
 * '계속한다 (Esc)' / 소리 / '시험장을 나간다'(확인 없이 toTitle).
 */
export class PauseScene extends Phaser.Scene {
  private list?: SelectList;
  private confirm = false;
  private alive = false;
  private muted = false;
  private lab = false;
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
    this.muted = Boolean(s.muted);
    this.lab = Boolean(s.lab);
    const W = this.scale.width;
    const H = this.scale.height;
    const bk = book(this, Math.round(W / 2), Math.round(H / 2), PAGE_W, PAGE_H, 1, 'pause');
    const pg = bk.pages[0];
    const innerW = PAGE_W - PAD * 2;
    let y = pg.y + 14;
    const titleText = this.lab ? r49Text('labPauseTitle') : uiText('pause', 'title', '일기장');
    const title = new GlowText(this, 0, 0, titleText, 'page_title', {
      font: 'title',
      stageIndex,
    });
    title.placeCenter(pg.x + PAGE_W / 2, y);
    y += title.displayHeight + 6;
    rule(this, pg.x + PAD, y, innerW);
    y += 4 + 10;
    const evo = s.weapon.evolutionName ? ` · ${s.weapon.evolutionName}` : '';
    const cur = hasRoute(s.route) ? s.route.nodes.find((n) => n.id === s.route?.currentId) : undefined;
    const lines = [
      // 48라운드: 노드 지도 층이면 시련 수 대신 지금 노드 이름 (49라운드: 지역 · 이름). 시험장이면 이 줄 없음
      this.lab
        ? ''
        : `${s.playerName || '―'}   ${s.floorTitle || s.stageName}   ${
            hasRoute(s.route)
              ? [cur?.region, cur?.name].filter(Boolean).join(' · ')
              : `시련 ${s.trialsCleared}/${s.trialsTotal}`
          }`,
      `공격 ${s.stats.attack}   방어 ${s.stats.defense}   치명타 ${s.stats.crit}%   감각 ${s.stats.sense}`,
      `무기: ${s.weapon.name}${evo}   (개성 ${s.weapon.personality}/${s.weapon.threshold})`,
      `패시브: ${s.passives.length ? s.passives.map((p) => `${p.name}${p.level > 1 ? ` Lv${p.level}` : ''}`).join(', ') : '―'}`,
    ];
    for (const t of lines) {
      if (!t) continue;
      const g = new GlowText(this, pg.x + PAD, y, t, 'page_body', { wrap: innerW, stageIndex });
      y += g.displayHeight + 2;
    }
    // 세이브 남음 (닫힌 일기장 아이콘) + 시드 (흐림). 시험장에서는 기록이 남지 않으므로 생략
    if (!this.lab) {
      icon(this, pg.x + PAD, y - 1, ICON.save);
      new GlowText(this, pg.x + PAD + 20, y, `세이브 남음 ${s.savesLeft}`, 'page_body', { stageIndex });
      new GlowText(this, 0, y, `시드 ${s.seed}`, 'page_faint').placeRight(pg.x + PAGE_W - PAD, y);
      y += 16;
    }
    y += 6;
    rule(this, pg.x + PAD, y, innerW);
    y += 4 + 10;
    this.list = new SelectList(this, pg.x + PAD, y, (key) => this.choose(key), { stageIndex, detailWrap: innerW - 40 });
    this.setList();
    y += this.list.height() + 10;
    // 시험장은 워프가 없으므로 'Tab 워프' 를 덧붙이지 않는다 (routeMode 와 같은 처리)
    new GlowText(
      this,
      pg.x + PAD,
      y,
      controlsLine(s.weapon.secondaryName, hasRoute(s.route) || this.lab),
      'page_faint',
      {
        wrap: innerW,
      },
    );
  }

  private soundLabel(): string {
    return this.muted ? r49Text('soundOn') : r49Text('soundOff');
  }

  private setList(): void {
    const keep = this.list?.cursorIndex() ?? 0;
    if (this.lab && !this.confirm) {
      this.list?.setLines([
        { key: '1', label: `${r49Text('labContinue')} (Esc)`, enabled: true },
        { key: '2', label: this.soundLabel(), enabled: true },
        { key: '3', label: r49Text('labLeave'), enabled: true },
      ]);
      this.list?.setCursorIndex(keep);
      return;
    }
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
            { key: '2', label: this.soundLabel(), enabled: true },
            { key: '3', label: uiText('pause', 'toTitle', '일기장을 덮는다'), enabled: true },
          ],
    );
    if (!this.confirm) this.list?.setCursorIndex(keep);
  }

  /** 소리 끄기·켜기 (계약 §11.3). 일시정지 중 스냅샷이 늦게 바뀔 수 있어 화면 상태는 여기서 뒤집는다 */
  private toggleSound(): void {
    this.muted = !this.muted;
    setMutedCmd(this.muted);
    this.setList();
  }

  private choose(key: string): void {
    if (!this.confirm) {
      if (key === '1') uiCommands.resume();
      else if (key === '2') this.toggleSound();
      else if (this.lab) uiCommands.toTitle();
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
