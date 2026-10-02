import Phaser from 'phaser';
import { COLORS, DEPTH, GAME, KEYS, PLACEHOLDER_UI, PROTOTYPE, RHYTHM_DOT, SCENES, TILE } from '../core/Constants';
import { PERSONALITY, PLAYER_DATA, STORY, WEAPONS } from '../data';
import { fill } from '../systems/story';
import type { Affinity } from '../data/types';
import { chooseWeapon, rhythmFeatures, strokeFeatures, type RhythmSample, type Stroke } from '../systems/personality';
import { META_CONFIG, buyUpgrade, metaStore, upgradeCost } from '../systems/meta';
import { TextMenu } from '../systems/TextMenu';
import { setMenuSelect } from '../contract/host';
import { EventBus, Events } from '../core/EventBus';
import { audio } from '../systems/audio';
import { UI_EVENTS, __system } from '../contract/ui';

type Phase = 'meta' | 'name' | 'strokes' | 'rhythm' | 'fate';

/**
 * 개성 선택 (기획 1장): "가장 강한 것"을 3획으로 그리고, 5초간 자유롭게 입력한 리듬을 합쳐
 * 성향 벡터를 만들고 가장 가까운 무기를 '운명'으로 정한다.
 * 화면·연출은 시스템 파트 플레이스홀더이며 UI·아트 파트 산출물로 교체 대상.
 */
const NAME_MAX = 12;

/**
 * 획 예시 (30라운드): "이런 방식으로 그린다"만 보여준다. 어떤 획이 어떤 무기로 이어지는지는 표시하지 않는다.
 * 각 예시는 정규화 좌표(0~1)의 점 목록이며, durationMs 동안 천천히 그려지는 것을 반복한다.
 */
interface StrokeExample {
  caption: string;
  points: [number, number][];
  durationMs: number;
}
const STROKE_EXAMPLES: StrokeExample[] = [
  {
    caption: '길게, 곧게',
    points: [
      [0.05, 0.55],
      [0.95, 0.45],
    ],
    durationMs: 1400,
  },
  {
    caption: '짧게, 빠르게',
    points: [
      [0.3, 0.3],
      [0.45, 0.7],
      [0.55, 0.3],
      [0.7, 0.7],
    ],
    durationMs: 450,
  },
  {
    caption: '크게, 둥글게',
    points: Array.from({ length: 13 }, (_, i) => {
      const a = Math.PI * (1 + i / 12);
      return [0.5 + 0.42 * Math.cos(a), 0.55 + 0.4 * Math.sin(a) * -1] as [number, number];
    }),
    durationMs: 2000,
  },
  {
    caption: '한 번에 내려긋기',
    points: [
      [0.5, 0.1],
      [0.5, 0.9],
    ],
    durationMs: 700,
  },
];
const EXAMPLE_PANEL = PLACEHOLDER_UI.EXAMPLE_PANEL;

export class Setup extends Phaser.Scene {
  private phase: Phase = 'strokes';
  private strokes: Stroke[] = [];
  private current: Stroke | null = null;
  private gfx: Phaser.GameObjects.Graphics;
  private label: Phaser.GameObjects.Text;
  private rhythm: RhythmSample = { frames: 0, movingFrames: 0, attacks: 0, dashes: 0 };
  private rhythmEndAt = 0;
  private keys: Record<string, Phaser.Input.Keyboard.Key>;
  private features?: Affinity;
  private menu: TextMenu;
  private onEnter?: (e: KeyboardEvent) => void;
  /** 일기장 이름 입력 (26라운드): DOM input, 최대 12자 */
  private nameInput?: Phaser.GameObjects.DOMElement;
  /** 획 예시 패널 (strokes 단계에서만) */
  private exampleGfx?: Phaser.GameObjects.Graphics;
  private exampleTexts: Phaser.GameObjects.Text[] = [];
  private playerName = '';
  /** 리듬 단계 하얀 점 (31라운드 1): WASD 이동·스페이스 대쉬·클릭 번쩍. 집계 로직과는 무관한 표시용 */
  private dot?: Phaser.GameObjects.Arc;
  private dotFacing = new Phaser.Math.Vector2(1, 0);
  private dotLastDashAt = -Infinity;
  private dotClicks = 0;

  constructor() {
    super(SCENES.SETUP);
  }

  create(): void {
    audio.setState('title');
    this.phase = 'meta';
    this.strokes = [];
    this.current = null;
    this.playerName = '';
    this.rhythm = { frames: 0, movingFrames: 0, attacks: 0, dashes: 0 };
    this.gfx = this.add.graphics().setDepth(DEPTH.ATTACK);
    this.label = this.add
      .text(GAME.WIDTH / 2, PLACEHOLDER_UI.LABEL_Y, '', {
        font: PLACEHOLDER_UI.FONT_BODY,
        color: COLORS.GAMEOVER_TEXT,
        align: 'center',
      })
      .setOrigin(0.5, 0)
      .setDepth(DEPTH.DEBUG);
    const kb = this.input.keyboard!;
    this.keys = {
      up: kb.addKey(KEYS.UP),
      down: kb.addKey(KEYS.DOWN),
      left: kb.addKey(KEYS.LEFT),
      right: kb.addKey(KEYS.RIGHT),
      dash: kb.addKey(KEYS.DASH),
    };
    this.input.mouse?.disableContextMenu();

    this.input.on('pointerdown', this.onPointerDown, this);
    this.input.on('pointermove', this.onPointerMove, this);
    this.input.on('pointerup', this.onPointerUp, this);
    this.events.once('shutdown', () => {
      this.input.off('pointerdown', this.onPointerDown, this);
      this.input.off('pointermove', this.onPointerMove, this);
      this.input.off('pointerup', this.onPointerUp, this);
      this.nameInput?.destroy();
      this.nameInput = undefined;
      this.input.keyboard?.enableGlobalCapture();
      this.hideExamples();
      this.dot?.destroy();
      this.dot = undefined;
      delete (window as unknown as { __lopadSetup?: unknown }).__lopadSetup;
    });
    this.exposeDebug();
    this.menu = new TextMenu(this);
    setMenuSelect((id, key) => {
      if (id === 'meta' && key === 'enter') this.beginName();
      else this.menu.select(key, id);
    });
    this.events.once('shutdown', () => setMenuSelect(null));
    this.openMetaMenu();
  }

  /** 런 시작 전: 영혼으로 영구 강화 구매, 도감 요약. Enter 로 개성 선택 시작 (임시 텍스트) */
  private openMetaMenu(): void {
    const meta = metaStore.read();
    const lines = META_CONFIG.upgrades.map((u, i) => {
      const lv = meta.upgrades[u.id] ?? 0;
      const maxed = lv >= u.maxLevel;
      const cost = maxed ? 0 : upgradeCost(u, lv);
      return {
        key: String(i + 1),
        label: `${u.name}  Lv ${lv}/${u.maxLevel}${maxed ? '  MAX' : `  ${cost} 영혼`}`,
        enabled: !maxed && meta.souls >= cost,
      };
    });
    const codex = Object.entries(WEAPONS)
      .map(([id, w]) => {
        const c = meta.codex[id];
        return c ? `${w.name} ★${c.maxStage} 처치 ${c.kills} 최고 ${c.bestFloor}층` : `${w.name} -`;
      })
      .join('  ·  ');
    this.menu.open(
      'meta',
      `영혼 ${meta.souls}   (런 ${meta.runs}회, 클리어 ${meta.clears}회, 최고 ${meta.bestFloor}층)`,
      lines,
      (key) => {
        const u = META_CONFIG.upgrades[Number(key) - 1];
        const next = buyUpgrade(metaStore.read(), u.id);
        if (next) {
          metaStore.write(next);
          this.openMetaMenu();
        }
      },
      `도감: ${codex}\n\n[Enter] 일기장을 펼친다`,
    );
    if (!this.onEnter) {
      this.onEnter = (e: KeyboardEvent) => {
        if (e.key === 'Enter' && this.phase === 'meta') this.beginName();
      };
      this.input.keyboard?.on('keydown', this.onEnter);
      this.events.once('shutdown', () => {
        if (this.onEnter) this.input.keyboard?.off('keydown', this.onEnter);
        this.onEnter = undefined;
        this.menu.close();
      });
    }
  }

  /** 일기장 첫 장: 이름을 적는다. 비우면 '―' 로 기록된다 (26라운드) */
  private beginName(): void {
    if (this.phase !== 'meta') return; // 메뉴 선택과 keydown 이 둘 다 Enter 를 전달하므로 한 번만
    this.menu.close();
    this.phase = 'name';
    this.label.setText(`${STORY.diary.first}\n\n이름을 적고 Enter`);
    const kb = this.input.keyboard!;
    kb.disableGlobalCapture();
    this.nameInput = this.add
      .dom(
        GAME.WIDTH / 2,
        GAME.HEIGHT / 2,
        'input',
        `width:${PLACEHOLDER_UI.NAME_INPUT_WIDTH}px;font:${PLACEHOLDER_UI.FONT_BODY};background:#101018;color:#e8e8f0;border:1px solid #777;padding:4px;text-align:center;outline:none`,
      )
      .setDepth(DEPTH.DEBUG);
    const node = this.nameInput.node as HTMLInputElement;
    node.maxLength = NAME_MAX;
    node.placeholder = '이름';
    node.id = 'lopad-name';
    node.addEventListener('keydown', (e) => {
      e.stopPropagation();
      if (e.key === 'Enter') this.finishName(node.value);
    });
    node.focus();
  }

  private finishName(raw: string): void {
    if (this.phase !== 'name') return;
    this.playerName = raw.trim().slice(0, NAME_MAX);
    this.nameInput?.destroy();
    this.nameInput = undefined;
    this.input.keyboard?.enableGlobalCapture();
    this.beginStrokes();
  }

  private beginStrokes(): void {
    this.menu.close();
    this.phase = 'strokes';
    this.updateLabel();
    this.showExamples();
  }

  /** 예시 패널: 제목 + 예시별 캡션. 선은 update() 에서 시간에 따라 다시 그린다 */
  private showExamples(): void {
    this.exampleGfx = this.add.graphics().setDepth(DEPTH.ATTACK);
    const { y, h, gap } = EXAMPLE_PANEL;
    const n = STROKE_EXAMPLES.length;
    const cellW = (GAME.WIDTH - gap * (n + 1)) / n;
    const style = { font: PLACEHOLDER_UI.FONT_CAPTION, color: '#8a8aa0', align: 'center' as const };
    this.exampleTexts.push(
      this.add
        .text(GAME.WIDTH / 2, y - 12, '예시 — 이런 식으로 그어도 된다 (길게·짧게, 곧게·둥글게, 빠르게·느리게)', style)
        .setOrigin(0.5, 0)
        .setDepth(DEPTH.DEBUG),
    );
    STROKE_EXAMPLES.forEach((ex, i) => {
      const cx = gap + cellW * i + cellW / 2;
      this.exampleTexts.push(
        this.add
          .text(cx, y + h + 2, ex.caption, style)
          .setOrigin(0.5, 0)
          .setDepth(DEPTH.DEBUG),
      );
    });
  }

  private hideExamples(): void {
    this.exampleGfx?.destroy();
    this.exampleGfx = undefined;
    this.exampleTexts.forEach((t) => t.destroy());
    this.exampleTexts = [];
  }

  /** 예시 획을 각자 duration 동안 진행률만큼 그린다 (끝나면 잠시 멈췄다가 반복) */
  private drawExamples(time: number): void {
    const g = this.exampleGfx;
    if (!g) return;
    g.clear();
    const { y, h, gap, pauseMs } = EXAMPLE_PANEL;
    const n = STROKE_EXAMPLES.length;
    const cellW = (GAME.WIDTH - gap * (n + 1)) / n;
    STROKE_EXAMPLES.forEach((ex, i) => {
      const x0 = gap + cellW * i;
      g.lineStyle(1, 0x3a3a50, 1);
      g.strokeRect(x0, y, cellW, h);
      const cycle = ex.durationMs + pauseMs;
      const progress = Math.min(1, (time % cycle) / ex.durationMs);
      const pts = ex.points.map(([px, py]) => ({ x: x0 + px * cellW, y: y + py * h }));
      // 전체 경로 길이의 progress 만큼만 그린다
      let total = 0;
      const seg: number[] = [];
      for (let k = 1; k < pts.length; k++) {
        const d = Phaser.Math.Distance.BetweenPoints(pts[k - 1], pts[k]);
        seg.push(d);
        total += d;
      }
      let remain = total * progress;
      g.lineStyle(2, COLORS.STROKE, 0.55);
      for (let k = 1; k < pts.length && remain > 0; k++) {
        const d = seg[k - 1];
        const t = Math.min(1, remain / d);
        const ex2 = pts[k - 1].x + (pts[k].x - pts[k - 1].x) * t;
        const ey2 = pts[k - 1].y + (pts[k].y - pts[k - 1].y) * t;
        g.lineBetween(pts[k - 1].x, pts[k - 1].y, ex2, ey2);
        if (t >= 1) remain -= d;
        else {
          // 펜 끝 표시
          g.fillStyle(COLORS.STROKE, 0.9);
          g.fillCircle(ex2, ey2, 2);
          remain = 0;
        }
      }
    });
  }

  update(time: number, delta: number): void {
    if (this.phase === 'strokes') {
      this.drawExamples(time);
      return;
    }
    if (this.phase !== 'rhythm') return;
    this.rhythm.frames += 1;
    const mx = (this.keys.right.isDown ? 1 : 0) - (this.keys.left.isDown ? 1 : 0);
    const my = (this.keys.down.isDown ? 1 : 0) - (this.keys.up.isDown ? 1 : 0);
    if (mx !== 0 || my !== 0) this.rhythm.movingFrames += 1;
    const dashed = Phaser.Input.Keyboard.JustDown(this.keys.dash);
    if (dashed) this.rhythm.dashes += 1;
    this.moveDot(mx, my, dashed, delta);
    const left = Math.max(0, this.rhythmEndAt - time);
    this.label.setText(
      `이제 5초 동안 자신답게 움직여 보세요 (WASD · 클릭 · 스페이스)\n남은 시간 ${(left / 1000).toFixed(1)}초`,
    );
    if (left <= 0) this.decideFate();
  }

  private onPointerDown(p: Phaser.Input.Pointer): void {
    if (this.phase === 'strokes') {
      this.current = [{ x: p.x, y: p.y, t: p.downTime }];
    } else if (this.phase === 'rhythm') {
      this.rhythm.attacks += 1;
      this.flashDotRing();
    }
  }

  /** 리듬 단계 시작: 화면 중앙에 하얀 점 */
  private showDot(): void {
    this.dot?.destroy();
    this.dot = this.add
      .circle(GAME.WIDTH / 2, GAME.HEIGHT / 2, RHYTHM_DOT.RADIUS, RHYTHM_DOT.COLOR)
      .setDepth(DEPTH.ATTACK);
    this.dotFacing.set(1, 0);
    this.dotClicks = 0;
  }

  /** WASD 로 플레이어 이동 속도만큼 움직이고, 스페이스면 대쉬 거리만큼 순간 이동 + 잔상 */
  private moveDot(mx: number, my: number, dashed: boolean, delta: number): void {
    const dot = this.dot;
    if (!dot) return;
    const dir = new Phaser.Math.Vector2(mx, my);
    if (dir.lengthSq() > 0) {
      dir.normalize();
      this.dotFacing.copy(dir);
    }
    const speed = PLAYER_DATA.stats.speedTiles * TILE;
    let x = dot.x + dir.x * speed * (delta / 1000);
    let y = dot.y + dir.y * speed * (delta / 1000);
    if (dashed) {
      const d = dir.lengthSq() > 0 ? dir : this.dotFacing;
      const dist = PLAYER_DATA.dash.distanceTiles * TILE;
      for (let i = 1; i <= RHYTHM_DOT.TRAIL_COUNT; i++) {
        const t = i / (RHYTHM_DOT.TRAIL_COUNT + 1);
        const ghost = this.add
          .circle(x + d.x * dist * t, y + d.y * dist * t, RHYTHM_DOT.RADIUS, RHYTHM_DOT.COLOR, RHYTHM_DOT.TRAIL_ALPHA)
          .setDepth(DEPTH.ATTACK);
        this.tweens.add({ targets: ghost, alpha: 0, duration: RHYTHM_DOT.TRAIL_MS, onComplete: () => ghost.destroy() });
      }
      x += d.x * dist;
      y += d.y * dist;
      this.dotLastDashAt = this.time.now;
    }
    const m = RHYTHM_DOT.MARGIN;
    dot.setPosition(Phaser.Math.Clamp(x, m, GAME.WIDTH - m), Phaser.Math.Clamp(y, m, GAME.HEIGHT - m));
  }

  /** 클릭: 점 주변에 작은 원이 번쩍 */
  private flashDotRing(): void {
    const dot = this.dot;
    if (!dot) return;
    this.dotClicks += 1;
    const ring = this.add
      .circle(dot.x, dot.y, RHYTHM_DOT.RING_FROM)
      .setStrokeStyle(RHYTHM_DOT.RING_WIDTH, RHYTHM_DOT.COLOR, 0.9)
      .setDepth(DEPTH.ATTACK);
    this.tweens.add({
      targets: ring,
      radius: RHYTHM_DOT.RING_TO,
      alpha: 0,
      duration: RHYTHM_DOT.RING_MS,
      onComplete: () => ring.destroy(),
    });
  }

  /** 검증 훅 (?debug=1): 단계·점 위치·리듬 집계. 게임 로직이 아니다 */
  private exposeDebug(): void {
    if (typeof location === 'undefined' || !new URLSearchParams(location.search).has('debug')) return;
    (window as unknown as { __lopadSetup: unknown }).__lopadSetup = () => ({
      phase: this.phase,
      dot: this.dot ? { x: this.dot.x, y: this.dot.y } : null,
      rhythm: { ...this.rhythm },
      strokes: this.strokes.length,
      lastDashAt: this.dotLastDashAt,
      clicks: this.dotClicks,
      rings: this.children.list.filter((c) => c instanceof Phaser.GameObjects.Arc && c.isStroked).length,
      features: this.features ?? null,
    });
  }

  private onPointerMove(p: Phaser.Input.Pointer): void {
    if (this.phase !== 'strokes' || !this.current || !p.isDown) return;
    const last = this.current[this.current.length - 1];
    if (Math.hypot(p.x - last.x, p.y - last.y) < 2) return;
    this.current.push({ x: p.x, y: p.y, t: p.moveTime });
    this.gfx.lineStyle(2, COLORS.STROKE, 1);
    this.gfx.lineBetween(last.x, last.y, p.x, p.y);
  }

  private onPointerUp(p: Phaser.Input.Pointer): void {
    if (this.phase !== 'strokes' || !this.current) return;
    this.current.push({ x: p.x, y: p.y, t: p.upTime });
    if (this.current.length >= PERSONALITY.strokes.minPoints) this.strokes.push(this.current);
    this.current = null;
    if (this.strokes.length >= PERSONALITY.strokes.count) {
      this.hideExamples();
      this.phase = 'rhythm';
      this.rhythmEndAt = this.time.now + PERSONALITY.rhythm.durationMs;
      this.showDot();
    }
    this.updateLabel();
  }

  private updateLabel(): void {
    if (this.phase === 'strokes') {
      this.label.setText(
        `${STORY.diary.beforeFate}  (${this.strokes.length}/${PERSONALITY.strokes.count})\n마우스를 누른 채 긋고 떼면 한 획`,
      );
    }
  }

  private decideFate(): void {
    this.phase = 'fate';
    this.dot?.destroy();
    this.dot = undefined;
    const f: Affinity = { ...strokeFeatures(this.strokes, PERSONALITY), ...rhythmFeatures(this.rhythm, PERSONALITY) };
    this.features = f;
    const { id } = chooseWeapon(f, WEAPONS, PERSONALITY);
    const w = WEAPONS[id];
    __system.emit(UI_EVENTS.FATE_DECIDED, { weaponName: w.name, features: f });
    EventBus.emit(Events.FATE_DECIDED, { weapon: id });
    this.label.setText(
      `${this.playerName || '―'}\n\n${fill(STORY.diary.fate, { weapon: w.name })}\n\n(획 길이 ${f.strokeLength.toFixed(2)} 속도 ${f.strokeSpeed.toFixed(2)} 직선 ${f.straightness.toFixed(2)} · 이동 ${f.keyMove.toFixed(2)} 공격 ${f.keyAttack.toFixed(2)} 대쉬 ${f.keyDash.toFixed(2)})`,
    );
    this.time.delayedCall(PROTOTYPE.FATE_BANNER_MS, () =>
      this.scene.start(SCENES.GAME, { mode: 'new', weapon: id, playerName: this.playerName }),
    );
  }

  /** 디버그/테스트용 */
  get debugFeatures(): Affinity | undefined {
    return this.features;
  }
}
