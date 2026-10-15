import Phaser from 'phaser';
import { UI_SCREEN, type UiSnapshot } from '../contract/ui';
import { debugExpose, debugTune } from './debug';
import { P19_EVENTS, R61_EVENTS } from './eventsR61';
import { GlowText } from './glow';
import { inkPanel } from './kit';
import {
  cameraOf,
  comboText,
  offscreenMarks,
  offscreenOf,
  popOf,
  popScreen,
  type OffscreenMark,
  type PopKind,
} from './p19View';
import { r62Text, storyText } from './text';
import { GRAY, LAYOUT, hexToNum } from './theme';
import { COMBO, INTRO_CORNER as IC, OFFSCREEN, POP } from './themeP19';
import { TimedCard } from './timedCard';

type On = <T>(event: string, handler: (p: T) => void) => void;

export interface HudP19Deps {
  stageIndex: () => number;
  /** 처음 보는 적 카드 위 끝 (왼쪽 위 띠 아래) */
  introTop: () => number;
  snapshot: () => UiSnapshot;
}

/**
 * P19 1-U 자유 전투 UI (decisions P19 ④G · contracts/free-combat §1·§2·§4) — HudScene 이 커지지 않게 한 곳에.
 *  - 화면 밖 적 표식: `snapshot.offscreen` 마다 가장자리 화살촉(예고 색 — 경고 호박·위험 적·원거리 청백, 위협 없음 무채). 가까우면 크고 진하다.
 *  - 반응 팝: 벽꽝·볼링·낙하·연쇄 폭발 — 월드 위 그림 문자 + 큰 숫자, 0.7초. 동시에 POP.max 개까지.
 *  - 연속 처치(COMBO_STREAK): 오른쪽 가장자리 작은 '연속 ×n' (보상 없음).
 *  - 처음 보는 적 소개: 위 가운데 띠 대신 왼쪽 위 작은 카드 (가운데 글 띠 ≤ 1 — ④G).
 */
export class HudP19 {
  private marks: Phaser.GameObjects.Graphics;
  private pops: TimedCard[] = [];
  private combo: Phaser.GameObjects.Container;
  private comboTag: GlowText;
  private comboNum: GlowText;
  private comboTimer?: Phaser.Time.TimerEvent;
  private intro?: { card: TimedCard; names: { name: string; desc: string | null }[] };
  private hidden = false;

  constructor(
    private scene: Phaser.Scene,
    private deps: HudP19Deps,
  ) {
    this.marks = scene.add.graphics().setDepth(OFFSCREEN.depth);
    const si = deps.stageIndex();
    this.comboTag = new GlowText(scene, 0, 0, r62Text('comboTag'), 'ink_faint', { stageIndex: si });
    this.comboNum = new GlowText(scene, 0, 0, '', 'ink_body', { scale: 2, stageIndex: si });
    this.combo = scene.add.container(0, 0, [this.comboTag, this.comboNum]).setDepth(COMBO.depth).setVisible(false);
  }

  subscribe(on: On): void {
    const pop = (kind: PopKind) => (p: unknown) => this.pop(kind, p);
    on(P19_EVENTS.ENEMY_WALL_SLAM, pop('wall'));
    on(P19_EVENTS.ENEMY_BOWLED, pop('bowl'));
    on(P19_EVENTS.ENEMY_FELL, pop('fell'));
    on(P19_EVENTS.HAZARD_EXPLODED, pop('blast'));
    on(P19_EVENTS.COMBO_STREAK, (p: unknown) => this.streak(p));
    on(R61_EVENTS.ENEMY_INTRO, (p: unknown) => this.enemyIntro(p));
  }

  /** 매 STATE (hidden = 메뉴·지도·탄생·사망·문 걷기가 덮음) */
  render(s: UiSnapshot, hidden: boolean): void {
    this.hidden = hidden;
    const g = this.marks.clear();
    const list = hidden ? [] : offscreenMarks(offscreenOf(s), UI_SCREEN.WIDTH, UI_SCREEN.HEIGHT);
    for (const m of list) drawMark(g, m);
    if (hidden) this.combo.setVisible(false);
    debugExpose(
      'offscreen',
      list.map((m) => `${m.threat ?? '-'}@${m.x},${m.y}/${m.size}`),
    );
  }

  /** 방을 떠남·사망·런 끝: 떠 있는 팝·연속 표·적 카드를 거둔다 */
  clear(): void {
    for (const c of this.pops) c.cancel();
    this.pops = [];
    this.comboTimer?.remove();
    this.combo.setVisible(false);
    this.intro?.card.cancel();
    this.intro = undefined;
  }

  destroy(): void {
    this.clear();
    this.marks.destroy();
    this.combo.destroy();
  }

  // ---- 반응 팝

  private pop(kind: PopKind, p: unknown): void {
    if (this.hidden) return;
    const s = this.deps.snapshot();
    const v = popOf(kind, p, s.settings?.damageNumbers !== false);
    const at = v && popScreen(p, cameraOf(s), UI_SCREEN.WIDTH, UI_SCREEN.HEIGHT);
    debugExpose('reactPop', { kind, num: v?.num ?? null, at });
    if (!v || !at) return;
    const sc = this.scene;
    const g = sc.add.graphics();
    const parts: Phaser.GameObjects.GameObject[] = [g];
    let w = POP.glyph;
    if (v.num) {
      const t = new GlowText(sc, 0, 0, v.num, 'ink_body', { scale: 2, stageIndex: this.deps.stageIndex() });
      t.setPosition(POP.glyph + POP.gap, Math.round(POP.glyph / 2 - t.displayHeight / 2));
      w += POP.gap + t.displayWidth;
      parts.push(t);
    }
    drawGlyph(g, kind, 0, 0, POP.glyph);
    const x = Math.round(Math.max(4, Math.min(UI_SCREEN.WIDTH - w - 4, at.x - w / 2)));
    const y = Math.round(Math.max(4, at.y - POP.lift - POP.glyph));
    // 떠오름은 안쪽 상자로 (바깥 상자의 y 는 TimedCard 가 쓴다)
    const inner = sc.add.container(0, 0, parts);
    const box = sc.add.container(x, y, [inner]).setDepth(POP.depth);
    // 헤드리스 캡처용: uidebug 의 tune.popSlow 배 느리게
    const k = debugTune('popSlow', 1);
    const tm = { inMs: POP.inMs * k, holdMs: POP.holdMs * k, outMs: POP.outMs * k };
    const card = new TimedCard(sc, box, tm, () => (this.pops = this.pops.filter((c) => c !== card)));
    sc.tweens.add({ targets: inner, y: -POP.rise, duration: tm.inMs + tm.holdMs + tm.outMs, ease: 'Quad.easeOut' });
    this.pops.push(card);
    while (this.pops.length > POP.max) this.pops.shift()!.cancel();
  }

  // ---- 연속 처치

  private streak(p: unknown): void {
    const o = (p ?? {}) as { count?: unknown; windowMs?: unknown };
    const text = this.hidden ? null : comboText(o.count, COMBO.min);
    debugExpose('combo', text);
    if (!text) return;
    this.comboNum.setText(text);
    const right = UI_SCREEN.WIDTH - COMBO.right;
    const y = Math.round(UI_SCREEN.HEIGHT * COMBO.yRatio);
    this.comboNum.placeRight(right, y);
    this.comboTag.placeRight(right, y - this.comboTag.displayHeight);
    const sc = this.scene;
    sc.tweens.killTweensOf([this.combo, this.comboNum]);
    this.combo.setVisible(true).setAlpha(1);
    sc.tweens.add({ targets: this.comboNum, y: y - COMBO.bump, duration: 70, yoyo: true });
    const hold = typeof o.windowMs === 'number' && o.windowMs > 0 ? o.windowMs : COMBO.holdMs;
    this.comboTimer?.remove();
    this.comboTimer = sc.time.delayedCall(hold, () =>
      sc.tweens.add({
        targets: this.combo,
        alpha: 0,
        duration: COMBO.outMs,
        onComplete: () => this.combo.setVisible(false),
      }),
    );
  }

  // ---- 처음 보는 적 (왼쪽 위 작은 카드 — 같은 때 여럿이면 한 장에 잇는다)

  private enemyIntro(p: unknown): void {
    const o = (p ?? {}) as { name?: unknown; desc?: unknown };
    const name = typeof o.name === 'string' ? o.name.trim() : '';
    if (!name) return;
    const desc = typeof o.desc === 'string' && o.desc.trim() ? o.desc.trim() : null;
    const prev = this.intro?.names.filter((n) => n.name !== name) ?? [];
    this.intro?.card.cancel();
    const names = [...prev, { name, desc }].slice(-IC.queueMax);
    const box = this.buildIntro(names);
    const card = new TimedCard(this.scene, box, { ...IC, drop: 3 }, () => {
      if (this.intro?.card === card) this.intro = undefined;
    });
    this.intro = { card, names };
    debugExpose('enemyIntro', { name, desc, names: names.map((n) => n.name), at: 'corner' });
  }

  private buildIntro(names: { name: string; desc: string | null }[]): Phaser.GameObjects.Container {
    const sc = this.scene;
    const si = this.deps.stageIndex();
    const texts: GlowText[] = [new GlowText(sc, IC.padX, IC.padY, storyText('enemyIntroTag'), 'ink_faint')];
    let y = IC.padY + texts[0].displayHeight;
    for (const n of names) {
      const t = new GlowText(sc, IC.padX, y, n.name, 'ink_accent', { stageIndex: si });
      texts.push(t);
      y += t.displayHeight;
      if (n.desc) {
        const d = new GlowText(sc, IC.padX, y, n.desc, 'ink_faint');
        texts.push(d);
        y += d.displayHeight;
      }
    }
    const w = Math.max(...texts.map((t) => t.displayWidth)) + IC.padX * 2;
    const panel = inkPanel(sc, 0, 0, w, y + IC.padY);
    return sc.add
      .container(LAYOUT.edge, Math.round(this.deps.introTop() + IC.gap), [panel, ...texts])
      .setDepth(IC.depth);
  }
}

/** 화살촉 (끝 = 가장자리 점, 바깥을 가리킴) — 먹 테 + 예고 색 몸 */
function drawMark(g: Phaser.GameObjects.Graphics, m: OffscreenMark): void {
  const ux = Math.cos(m.angle);
  const uy = Math.sin(m.angle);
  const bx = m.x - ux * m.size;
  const by = m.y - uy * m.size;
  const px = -uy * (m.size * 0.7);
  const py = ux * (m.size * 0.7);
  g.fillStyle(hexToNum(GRAY[0]), 0.85 * m.alpha);
  g.fillTriangle(
    m.x + ux * 2,
    m.y + uy * 2,
    bx + px * 1.4 - ux,
    by + py * 1.4 - uy,
    bx - px * 1.4 - ux,
    by - py * 1.4 - uy,
  );
  g.fillStyle(hexToNum(m.color ?? GRAY[OFFSCREEN.idleGray]), m.alpha);
  g.fillTriangle(m.x, m.y, bx + px, by + py, bx - px, by - py);
}

/**
 * 반응 그림 문자 (s×s, 흰 몸 + 먹 테 — 예고 색 '흰 테 = 내가 일으킨 것').
 * 벽꽝 = 벽 기둥 + 부딪힌 금 · 볼링 = 겹친 두 몸 · 낙하 = 아래 화살 · 연쇄 폭발 = 여덟 갈래 불꽃.
 */
function drawGlyph(g: Phaser.GameObjects.Graphics, kind: PopKind, x: number, y: number, s: number): void {
  const h = Math.floor(s / 2);
  const shape = (dx: number, dy: number): void => {
    const X = x + dx;
    const Y = y + dy;
    switch (kind) {
      case 'wall':
        g.fillRect(X + s - 3, Y, 3, s);
        g.fillRect(X + s - 6, Y + 2, 2, 2)
          .fillRect(X + s - 8, Y + h - 1, 4, 2)
          .fillRect(X + s - 6, Y + s - 4, 2, 2);
        g.fillRect(X, Y + h - 1, 3, 2);
        break;
      case 'bowl':
        g.fillCircle(X + 4, Y + h, 4).fillCircle(X + s - 4, Y + h + 1, 4);
        break;
      case 'fell':
        g.fillRect(X + h - 1, Y, 3, h + 1);
        g.fillTriangle(X + 1, Y + h, X + s - 1, Y + h, X + h + 0.5, Y + s);
        break;
      case 'blast':
        g.fillRect(X + h - 1, Y, 2, s).fillRect(X, Y + h - 1, s, 2);
        for (const [a, b] of [
          [2, 2],
          [s - 4, 2],
          [2, s - 4],
          [s - 4, s - 4],
        ])
          g.fillRect(X + a, Y + b, 2, 2);
        g.fillRect(X + h - 2, Y + h - 2, 4, 4);
        break;
    }
  };
  g.fillStyle(hexToNum(GRAY[0]), 1);
  for (const [dx, dy] of [
    [-1, 0],
    [1, 0],
    [0, -1],
    [0, 1],
  ])
    shape(dx, dy);
  g.fillStyle(hexToNum(GRAY[15]), 1);
  shape(0, 0);
}
