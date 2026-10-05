import Phaser from 'phaser';
import { UI_EVENTS, UI_SCREEN, uiBus, uiCommands } from '../contract/ui';
import { debugExpose, setMutedCmd, withDebug } from './debug';
import { GlowText } from './glow';
import { keyTaken, takeKey } from './keyGate';
import { ICON, book, fontsReady, icon, preloadKit, rule, setupKit } from './kit';
import { UI_SCENE_KEYS } from './keys';
import { hasRoute } from './routeView';
import { controlsLine, r49Text, r53Text, uiText } from './text';
import { GRAY, LAYOUT, ROUTE, hexToNum } from './theme';
import { buildPage } from './PauseBuild';
import { buildHowToPanel } from './TutorialHud';
import { SelectList } from './widgets';

const PAGE_W = 440;
/** 53라운드 Q50: '싸우는 법' 항목 한 줄만큼 높였다 */
const PAGE_H = 282 + LAYOUT.row;
const PAD = 24;
/** 60라운드: 두 쪽 펼침 쪽 높이 상한 (화면 540 - 책 틀 32 - 여백) */
const MAX_PAGE_H = UI_SCREEN.HEIGHT - 32 - 16;
/** '싸우는 법' 패널 깊이 (일기장 위) */
const HOWTO_DEPTH = 50;

/** 일기장 항목 key (53라운드 Q50: 3 = 싸우는 법, 덮기·나가기는 4) */
const PAUSE_KEY = { resume: '1', sound: '2', howTo: '3', leave: '4' } as const;

/**
 * 일시정지 = 일기장 한 페이지 (31라운드 채택 문구): 제목 '일기장', 이름·층·시련·세이브, 능력치, 무기, 패시브, 조작법,
 * '더 쓴다 (Esc)' / '소리 끄기·켜기' / '일기장을 덮는다' → 확인 '적지 않은 것은 남지 않는다. 그래도 덮는다 — 예' / '더 쓴다'
 * 49라운드(계약 §11.3·§11.4): 소리 항목 → `setMuted`, 상태는 `snapshot.muted`. 무기 시험장(`lab`)이면 제목 '무기 시험장',
 * '계속한다 (Esc)' / 소리 / '시험장을 나간다'(확인 없이 toTitle).
 * 60라운드(계약 §14): 두 쪽 펼침 — 오른쪽 쪽 '빌드'(PauseBuild.ts: 태그·세트·이중 개성·저주·패시브 Lv/최대·태그·소모품).
 *   패시브 줄은 왼쪽 쪽에서 오른쪽으로 옮겼다.
 * 53라운드 Q50: '싸우는 법' 항목 — 튜토리얼 안내 패널을 화면 가운데에 다시 띄운다(일기장 위). Esc·Enter·클릭으로 닫으면
 * 일기장으로 돌아온다 (Esc 한 단계 뒤로).
 */
export class PauseScene extends Phaser.Scene {
  private list?: SelectList;
  private confirm = false;
  private alive = false;
  private muted = false;
  private lab = false;
  /** '싸우는 법' 패널 (떠 있으면 일기장 목록 입력을 막는다) */
  private howTo?: Phaser.GameObjects.Container;
  private howToBlock?: Phaser.GameObjects.Rectangle;
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
    this.howTo = undefined;
    this.howToBlock = undefined;
    setupKit(this);
    // keydown 이벤트로 (HudScene 참조). Key 객체를 만들지 않는다
    this.input.keyboard?.on('keydown-ESC', this.onEsc);
    this.input.keyboard?.on('keydown-ENTER', this.onEnter);
    uiBus.on(UI_EVENTS.RESUMED, this.onResumed);
    this.events.once('shutdown', () => {
      this.alive = false;
      this.howTo = undefined;
      this.howToBlock = undefined;
      this.input.keyboard?.off('keydown-ESC', this.onEsc);
      this.input.keyboard?.off('keydown-ENTER', this.onEnter);
      uiBus.off(UI_EVENTS.RESUMED, this.onResumed);
      this.list?.destroy();
    });
    fontsReady().then(() => {
      if (this.alive) this.build();
    });
  }

  /**
   * 51라운드 §6: Esc = 한 단계 뒤로. '싸우는 법' 패널이면 패널만, 덮기 확인 중이면 확인만 닫고, 아니면 게임으로.
   * 같은 Esc 이벤트가 다시 넘어오면 무시 (keyGate.ts — 닫힌 뒤 HUD 가 같은 Esc 로 일시정지를 또 열지 않게)
   */
  private onEsc = (e?: KeyboardEvent): void => {
    if (e?.repeat || !takeKey(e)) return;
    if (this.howTo) {
      this.closeHowTo();
      return;
    }
    if (this.confirm) {
      this.confirm = false;
      this.setList();
      return;
    }
    uiCommands.resume();
  };

  private build(): void {
    const s = withDebug(uiCommands.getUiSnapshot());
    const stageIndex = Math.max(0, s.stageIndex);
    this.muted = Boolean(s.muted);
    this.lab = Boolean(s.lab);
    const W = UI_SCREEN.WIDTH;
    const H = UI_SCREEN.HEIGHT;
    // 60라운드 §14: 오른쪽 쪽 '빌드'(태그·세트·이중 개성·저주·패시브·소모품) — 글을 먼저 재고 두 쪽 높이를 맞춘다
    const right = buildPage(this, PAGE_W - PAD * 2, s, stageIndex, MAX_PAGE_H - 14 - 14);
    const pageH = Math.min(MAX_PAGE_H, Math.max(PAGE_H, right.h + 14 + 14));
    const bk = book(this, Math.round(W / 2), Math.round(H / 2), PAGE_W, pageH, 2, 'pause');
    const pg = bk.pages[0];
    right.place(bk.pages[1].x + PAD, bk.pages[1].y + 14);
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
      // 패시브는 60라운드부터 오른쪽 '빌드' 쪽에 (Lv/최대·태그와 함께)
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

  /** Enter: '싸우는 법' 패널 닫기 (목록의 Enter 는 패널이 떠 있는 동안 막혀 있다) */
  private onEnter = (e?: KeyboardEvent): void => {
    if (!this.howTo || keyTaken(e)) return;
    takeKey(e);
    this.closeHowTo();
  };

  /** 53라운드 Q50: '싸우는 법' 패널 다시 보기 — 튜토리얼과 같은 패널을 화면 가운데, 일기장 위에 */
  private showHowTo(): void {
    if (this.howTo) return;
    const s = withDebug(uiCommands.getUiSnapshot());
    const p = buildHowToPanel(this, s, Math.max(0, s.stageIndex));
    // 일기장을 G00 α0.55(노드 지도 배경과 같은 허용 알파)로 덮어 반투명 잉크 패널 아래 글이 비치지 않게 하고, 패널 밖 클릭도 닫기.
    // 화면 전체를 덮어 아래 일기장 항목이 눌리지 않게 한다
    // (지금 처리 중인 클릭에는 새 판정 대상이 끼지 않으므로, 항목을 누른 그 클릭으로 바로 닫히지 않는다)
    const block = this.add
      .rectangle(0, 0, UI_SCREEN.WIDTH, UI_SCREEN.HEIGHT, hexToNum(GRAY[0]), ROUTE.dimAlpha)
      .setOrigin(0)
      .setDepth(HOWTO_DEPTH - 1)
      .setInteractive();
    block.on('pointerdown', () => this.closeHowTo());
    this.howTo = p.box.setDepth(HOWTO_DEPTH);
    this.howToBlock = block;
    this.list?.setEnabled(false);
    debugExpose('pauseHowTo', { open: true, rows: p.rows, x: p.x, y: p.y, w: p.w, h: p.h });
  }

  private closeHowTo(): void {
    this.howTo?.destroy();
    this.howToBlock?.destroy();
    this.howTo = undefined;
    this.howToBlock = undefined;
    this.list?.setEnabled(true);
    debugExpose('pauseHowTo', { open: false });
  }

  private soundLabel(): string {
    return this.muted ? r49Text('soundOn') : r49Text('soundOff');
  }

  private setList(): void {
    const keep = this.list?.cursorIndex() ?? 0;
    if (this.lab && !this.confirm) {
      this.list?.setLines([
        { key: PAUSE_KEY.resume, label: `${r49Text('labContinue')} (Esc)`, enabled: true },
        { key: PAUSE_KEY.sound, label: this.soundLabel(), enabled: true },
        { key: PAUSE_KEY.howTo, label: r53Text('pauseHowTo'), enabled: true },
        { key: PAUSE_KEY.leave, label: r49Text('labLeave'), enabled: true },
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
            { key: PAUSE_KEY.resume, label: `${uiText('pause', 'cancelQuit', '더 쓴다')} (Esc)`, enabled: true },
            { key: PAUSE_KEY.sound, label: this.soundLabel(), enabled: true },
            { key: PAUSE_KEY.howTo, label: r53Text('pauseHowTo'), enabled: true },
            { key: PAUSE_KEY.leave, label: uiText('pause', 'toTitle', '일기장을 덮는다'), enabled: true },
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
      if (key === PAUSE_KEY.resume) uiCommands.resume();
      else if (key === PAUSE_KEY.sound) this.toggleSound();
      else if (key === PAUSE_KEY.howTo) this.showHowTo();
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
