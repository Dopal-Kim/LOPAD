import Phaser from 'phaser';
import { UI_SCREEN, type UiSnapshot, type UiStoryLine } from '../contract/ui';
import { debugExpose } from './debug';
import { GlowText } from './glow';
import { KEYCAP, KeyCap } from './keycap';
import { NinePanel, inkPanel } from './kit';
import { fill, r53Text } from './text';
import {
  incomingWarns,
  isTutorialNode,
  sameStepText,
  stepFromEvent,
  stepFromNotice,
  tutorialKey,
  tutorialRows,
  type StepCard,
} from './tutorialView';

/** 튜토리얼 안내 패널·경고 배치 (53라운드, 임시값 — 도영 님 검수 대상) */
const TUT = {
  depth: 60,
  padX: 20,
  padY: 14,
  rowH: 22,
  keyGap: 3,
  /** 키 칸 폭 (줄마다 글 시작을 맞춘다) */
  keyColW: 92,
  minW: 360,
  /** 저절로 닫히기까지 (ms) */
  holdMs: 12000,
  fadeMs: 250,
  /** 경고: 화면 가운데에서 위로. 머무는 시간은 이것과 소환까지 남은 시간(delayMs) 중 긴 쪽 */
  warnDy: -110,
  warnHoldMs: 1800,
  warnBlinks: 3,
  /** 단계 카드: 위쪽 가운데 y, 머무는 시간(다음 공지가 오면 바뀐다) */
  stepTop: 52,
  stepHoldMs: 20000,
  stepPadX: 16,
  stepPadY: 8,
  /** 단계 카드 진행('2/5') 앞 간격 */
  stepProgressGap: 12,
  warnBlinkMs: 160,
} as const;

/** 한 번 띄운 튜토리얼 (런 시드 + 노드 id). HUD 씬이 다시 만들어져도 같은 런에서는 다시 띄우지 않는다 */
const shownTutorials = new Set<string>();

/**
 * 53라운드 튜토리얼 안내 (51라운드 §3, UI 몫).
 * - 안내 패널: 튜토리얼 노드(여정)에 들어와 배너·지역 카드가 끝난 뒤 화면 가운데 큰 잉크 패널 —
 *   제목 + 키 아이콘(KeyCap) 줄(이동·공격·우클릭·대쉬·F) + 기타 키 한 줄 + 닫기 안내. Enter·Esc·클릭 또는 12초 뒤 닫힌다.
 *   게임은 멈추지 않는다.
 * - 단계 카드: `TUTORIAL_STEP {index, total, text, keys}` (53라운드 계약) 을 위쪽 가운데 큰 카드로 — 키는 2배 키 아이콘,
 *   문장은 2배 글, 오른쪽 끝에 진행 '2/5'. 다음 단계가 올 때까지(최대 20초) 머물고, 노드를 옮기면 거둔다.
 *   이 이벤트를 아직 한 번도 받지 않았으면 예전처럼 튜토리얼 노드의 시스템 공지(STORY notice, 예 '…걸어가 보자. (WASD)',
 *   끝 괄호 = 키)를 카드로 쓴다. 이벤트를 받은 뒤로는 공지는 보통 자막이고, 지금 카드와 같은 문구의 공지만 삼킨다(겹침 방지).
 * - 경고: `ENEMY_INCOMING` 의 delayMs > 0 (53라운드 Q49·Q60 — 튜토리얼에서만 지연이 온다) 이면 적이 나오기 전에
 *   '주의 / 적이 다가온다' 를 가운데 위에 깜빡여 띄우고 안내 패널은 닫는다. 떠 있는 동안 같은 방의 예고가 또 와도 다시 띄우지 않는다.
 */
export class TutorialGuide {
  private panel?: Phaser.GameObjects.Container;
  private panelTimer?: Phaser.Time.TimerEvent;
  private warn?: Phaser.GameObjects.Container;
  private step?: Phaser.GameObjects.Container;
  private stepTimer?: Phaser.Time.TimerEvent;
  /** 지금 카드: 문구·출처·띄운 곳(시험장 여부 + 노드 id) */
  private stepText = '';
  private stepSource: 'event' | 'notice' = 'notice';
  private stepWhere = '';
  /** TUTORIAL_STEP 을 한 번이라도 받았는가 (받았으면 공지 대체 경로를 쓰지 않는다) */
  private stepEvents = false;
  private warnRoom: string | null = null;
  private alive = true;

  constructor(private scene: Phaser.Scene) {
    scene.input.on('pointerdown', this.onPointer);
  }

  get panelOpen(): boolean {
    return Boolean(this.panel);
  }

  /**
   * 매 스냅샷. `idle` = 다른 화면(메뉴·지도·일시정지)·배너·탄생 연출이 없어 패널을 띄워도 되는가.
   */
  update(s: UiSnapshot, idle: boolean, stageIndex: number): void {
    if (!this.alive) return;
    if (this.step && this.stepLeft(s)) this.clearStep();
    const key = tutorialKey(s);
    if (!key || shownTutorials.has(key) || !idle || s.inCombat || this.panel) return;
    shownTutorials.add(key);
    this.showPanel(s, stageIndex);
  }

  /** Esc·Enter: 패널이 떠 있으면 닫고 true (Esc 한 단계 뒤로) */
  dismiss(): boolean {
    if (!this.panel) return false;
    this.closePanel();
    return true;
  }

  /**
   * STORY 공지: 단계 카드가 받았으면 true (HUD 는 작은 자막을 그리지 않는다).
   * TUTORIAL_STEP 을 받기 전: 튜토리얼 노드의 공지를 카드로. 받은 뒤: 지금 카드와 같은 문구의 공지만 삼킨다.
   */
  takeNotice(l: UiStoryLine, s: UiSnapshot, stageIndex: number): boolean {
    if (!this.alive || l.kind !== 'notice') return false;
    if (this.stepEvents) return Boolean(this.step) && sameStepText(l.text, this.stepText);
    if (!isTutorialNode(s)) return false;
    this.showStep(stepFromNotice(l.text), 'notice', s, stageIndex);
    return true;
  }

  /** TUTORIAL_STEP: 단계 카드를 띄우고 그 문구를 돌려준다 (HUD 가 같은 문구의 자막을 거두게). 잘못된 페이로드면 null */
  takeStep(p: unknown, s: UiSnapshot, stageIndex: number): string | null {
    if (!this.alive) return null;
    const card = stepFromEvent(p);
    if (!card) return null;
    this.stepEvents = true;
    this.showStep(card, 'event', s, stageIndex);
    return card.text;
  }

  /** ENEMY_INCOMING: 소환까지 시간이 있으면(delayMs > 0) '주의' 경고 */
  enemyIncoming(p: unknown, stageIndex: number): void {
    if (!this.alive || !incomingWarns(p)) return;
    // 한 무리를 여러 번에 나눠 예고해도 떠 있는 경고를 다시 시작하지 않는다
    if (this.warn && this.warnRoom === p.roomId) return;
    this.warnRoom = p.roomId;
    this.showWarning(stageIndex, p.delayMs);
  }

  /** 런이 끝나면 단계 카드·경고를 거둔다 */
  reset(): void {
    this.clearStep();
    this.warn?.destroy();
    this.warn = undefined;
    this.warnRoom = null;
  }

  destroy(): void {
    this.alive = false;
    this.scene.input?.off('pointerdown', this.onPointer);
    this.closePanel(true);
    this.stepTimer?.remove();
    this.step?.destroy();
    this.step = undefined;
    this.warn?.destroy();
    this.warn = undefined;
  }

  private onPointer = (): void => {
    if (this.panel) this.closePanel();
  };

  private showPanel(s: UiSnapshot, stageIndex: number): void {
    const p = buildHowToPanel(this.scene, s, stageIndex);
    const box = p.box.setDepth(TUT.depth).setAlpha(0);
    this.panel = box;
    this.scene.tweens.add({ targets: box, alpha: 1, duration: TUT.fadeMs });
    this.panelTimer = this.scene.time.delayedCall(TUT.holdMs, () => this.closePanel());
    debugExpose('tutorial', { open: true, rows: p.rows, x: p.x, y: p.y, w: p.w, h: p.h });
  }

  private closePanel(now = false): void {
    const p = this.panel;
    if (!p) return;
    this.panel = undefined;
    this.panelTimer?.remove();
    this.panelTimer = undefined;
    debugExpose('tutorial', { open: false });
    if (now || !this.alive) {
      p.destroy();
      return;
    }
    this.scene.tweens.add({ targets: p, alpha: 0, duration: TUT.fadeMs, onComplete: () => p.destroy() });
  }

  private showStep(card: StepCard, source: 'event' | 'notice', s: UiSnapshot, stageIndex: number): void {
    const sc = this.scene;
    this.stepTimer?.remove();
    this.step?.destroy();
    const caps = card.keys.map((k) => new KeyCap(sc, 0, 0, k).setScale(2));
    const t = new GlowText(sc, 0, 0, card.text, 'ink_body', { scale: 2, stageIndex });
    const prog = card.progress
      ? new GlowText(
          sc,
          0,
          0,
          fill(r53Text('tutStep'), { n: card.progress.n, total: card.progress.total }),
          'ink_faint',
          {
            stageIndex,
          },
        )
      : null;
    const capsW = caps.reduce((w, c) => w + c.width * 2 + TUT.keyGap * 2, 0);
    const progW = prog ? TUT.stepProgressGap + prog.displayWidth : 0;
    const innerH = Math.max(t.displayHeight, caps.length ? KEYCAP.h * 2 : 0);
    const w = TUT.stepPadX * 2 + capsW + (caps.length ? 8 : 0) + t.displayWidth + progW;
    const h = TUT.stepPadY * 2 + innerH;
    const bg = inkPanel(sc, 0, 0, w, h);
    let x = TUT.stepPadX;
    for (const c of caps) {
      c.setPosition(x, Math.round(h / 2 - KEYCAP.h));
      x += c.width * 2 + TUT.keyGap * 2;
    }
    if (caps.length) x += 8;
    t.setPosition(x, Math.round(h / 2 - t.displayHeight / 2));
    prog?.setPosition(x + t.displayWidth + TUT.stepProgressGap, Math.round(h / 2 - prog.displayHeight / 2));
    const objs: Phaser.GameObjects.GameObject[] = [bg, ...caps, t];
    if (prog) objs.push(prog);
    const box = sc.add
      .container(Math.round(UI_SCREEN.WIDTH / 2 - w / 2), TUT.stepTop, objs)
      .setDepth(TUT.depth)
      .setAlpha(0);
    this.step = box;
    this.stepText = card.text;
    this.stepSource = source;
    this.stepWhere = stepWhere(s);
    sc.tweens.add({ targets: box, alpha: 1, duration: TUT.fadeMs });
    this.stepTimer = sc.time.delayedCall(TUT.stepHoldMs, () => {
      if (this.step !== box) return;
      this.step = undefined;
      sc.tweens.add({ targets: box, alpha: 0, duration: TUT.fadeMs, onComplete: () => box.destroy() });
    });
    debugExpose('tutorialStep', { text: card.text, keys: card.keys, progress: card.progress, source, w, h });
  }

  /** 카드를 거둘 때인가: 노드(또는 시험장 여부)가 바뀌었거나, 공지에서 온 카드인데 튜토리얼 노드를 떠났다 */
  private stepLeft(s: UiSnapshot): boolean {
    return stepWhere(s) !== this.stepWhere || (this.stepSource === 'notice' && !isTutorialNode(s));
  }

  /** 단계 카드를 거둔다 */
  private clearStep(): void {
    this.stepTimer?.remove();
    this.stepTimer = undefined;
    this.step?.destroy();
    this.step = undefined;
    this.stepText = '';
    debugExpose('tutorialStep', null);
  }

  /** '주의' 경고: 큰 강조 글 + 한 줄, 깜빡이며 나타났다 사라진다. 안내 패널은 닫는다 */
  private showWarning(stageIndex: number, delayMs: number): void {
    const sc = this.scene;
    this.closePanel();
    this.warn?.destroy();
    const title = new GlowText(sc, 0, 0, r53Text('warnTitle'), 'ink_accent', { scale: 2, stageIndex });
    const line = new GlowText(sc, 0, 0, r53Text('warnLine'), 'ink_body', { stageIndex });
    const w = Math.max(title.displayWidth, line.displayWidth) + 32;
    const h = title.displayHeight + 4 + line.displayHeight + 16;
    const bg = inkPanel(sc, 0, 0, w, h);
    title.placeCenter(w / 2, 8);
    line.placeCenter(w / 2, 8 + title.displayHeight + 4);
    const x0 = Math.round(UI_SCREEN.WIDTH / 2 - w / 2);
    const y0 = Math.round(UI_SCREEN.HEIGHT / 2 + TUT.warnDy - h / 2);
    const box = sc.add.container(x0, y0, [bg, title, line]).setDepth(TUT.depth + 1);
    this.warn = box;
    debugExpose('warning', { at: sc.time.now, delayMs });
    // 깜빡임(계단 알파 1 ↔ 0.55, 키트 허용 알파) 뒤 머물렀다 사라진다
    sc.time.addEvent({
      delay: TUT.warnBlinkMs,
      repeat: TUT.warnBlinks * 2 - 1,
      callback: () => title.setAlpha(title.alpha < 1 ? 1 : 0.55),
    });
    sc.time.delayedCall(Math.max(TUT.warnHoldMs, delayMs), () => {
      if (this.warn !== box) return;
      sc.tweens.add({
        targets: box,
        alpha: 0,
        duration: TUT.fadeMs,
        onComplete: () => {
          box.destroy();
          if (this.warn === box) {
            this.warn = undefined;
            this.warnRoom = null;
          }
        },
      });
    });
  }
}

/** 단계 카드를 띄운 곳 (시험장 여부 + 지금 노드 id) — 바뀌면 카드를 거둔다 */
function stepWhere(s: Pick<UiSnapshot, 'lab' | 'route'>): string {
  return `${s.lab ? 'lab' : ''}|${s.route?.currentId ?? ''}`;
}

/** '싸우는 법' 패널 한 장 (화면 가운데 Container). 튜토리얼 안내와 일시정지 일기장 '다시 보기'(53라운드 Q50)가 같이 쓴다 */
export interface HowToPanel {
  box: Phaser.GameObjects.Container;
  x: number;
  y: number;
  w: number;
  h: number;
  /** 디버그용 줄 요약 ('W+A+S+D 이동' …) */
  rows: string[];
}

/**
 * '싸우는 법' 패널을 화면 가운데에 만든다 (깊이·알파·닫기는 부르는 쪽이 정한다).
 * 제목 + 키 아이콘(KeyCap) 줄(이동·공격·우클릭·대쉬·F) + 기타 키 한 줄 + 닫기 안내. 줄은 스냅샷(무기 보조 동작·넣기/뽑기)으로 만든다.
 */
export function buildHowToPanel(sc: Phaser.Scene, s: UiSnapshot, stageIndex: number): HowToPanel {
  const rows = tutorialRows(s, (k, v) => (v ? fill(r53Text(k), v) : r53Text(k)));
  const objs: Phaser.GameObjects.GameObject[] = [];
  const title = new GlowText(sc, 0, 0, r53Text('tutTitle'), 'ink_body', { scale: 2, stageIndex });
  objs.push(title);
  // 줄: 키 아이콘들 + 글
  const rowObjs = rows.map((r) => {
    const caps = r.keys.map((k) => new KeyCap(sc, 0, 0, k));
    const text = new GlowText(sc, 0, 0, r.text, 'ink_body', { stageIndex });
    objs.push(...caps, text);
    return { caps, text };
  });
  const more = new GlowText(sc, 0, 0, r53Text('tutMore'), 'ink_faint', {
    wrap: UI_SCREEN.WIDTH - 200,
    align: 'center',
  });
  const close = new GlowText(sc, 0, 0, r53Text('tutClose'), 'ink_accent', { stageIndex });
  objs.push(more, close);
  const rowsW = Math.max(...rowObjs.map((r) => TUT.keyColW + r.text.displayWidth));
  const w = Math.max(TUT.minW, rowsW, more.displayWidth, title.displayWidth) + TUT.padX * 2;
  const h =
    TUT.padY +
    title.displayHeight +
    10 +
    rows.length * TUT.rowH +
    8 +
    more.displayHeight +
    6 +
    close.displayHeight +
    TUT.padY;
  const x0 = Math.round(UI_SCREEN.WIDTH / 2 - w / 2);
  const y0 = Math.round(UI_SCREEN.HEIGHT / 2 - h / 2);
  const bg: NinePanel = inkPanel(sc, 0, 0, w, h);
  let y = TUT.padY;
  title.placeCenter(w / 2, y);
  y += title.displayHeight + 10;
  // 키 칸을 가운데 묶음으로: 묶음 폭 = rowsW
  const left = Math.round(w / 2 - rowsW / 2);
  for (const r of rowObjs) {
    let kx = left;
    for (const c of r.caps) {
      c.setPosition(kx, y + 2);
      kx += c.width + TUT.keyGap;
    }
    r.text.setPosition(left + TUT.keyColW, y + 2 + Math.round((KEYCAP.h - r.text.displayHeight) / 2));
    y += TUT.rowH;
  }
  y += 8;
  more.placeCenter(w / 2, y);
  y += more.displayHeight + 6;
  close.placeCenter(w / 2, y);
  const box = sc.add.container(x0, y0, [bg, ...objs]);
  return { box, x: x0, y: y0, w, h, rows: rows.map((r) => `${r.keys.join('+')} ${r.text}`) };
}
