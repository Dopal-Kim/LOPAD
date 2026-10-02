import Phaser from 'phaser';
import { COLORS, DEPTH, GAME, KEYS, PLACEHOLDER_UI, PROTOTYPE, SCENES } from '../core/Constants';
import { PERSONALITY, STORY, WEAPONS } from '../data';
import { fill } from '../systems/story';
import type { Affinity } from '../data/types';
import { chooseWeapon, strokeFeatures, type Stroke } from '../systems/personality';
import { DODGE_TRIAL, emptySample, evaluateDodge, type DodgeEvaluation, type DodgeSample } from '../systems/dodgeTrial';
import { DodgeTrialRunner } from '../systems/dodgeTrialRunner';
import { StrokeFx } from '../systems/strokeFx';
import { STROKE_FX } from '../systems/strokeFxMath';
import { spriteLibrary } from '../systems/sprites';
import { META_CONFIG, buyUpgrade, metaStore, upgradeCost } from '../systems/meta';
import { TextMenu } from '../systems/TextMenu';
import { setMenuSelect } from '../contract/host';
import { EventBus, Events } from '../core/EventBus';
import { audio } from '../systems/audio';
import { UI_EVENTS, __system } from '../contract/ui';

type Phase = 'meta' | 'name' | 'strokes' | 'trial' | 'fate';

/**
 * 개성 선택 (기획 1장): "가장 강한 것"을 3획으로 그리고(48라운드 Q8: 화면이 찢기며 빛이 새는 연출 `StrokeFx`),
 * 15초 회피 시험(48라운드 Q7, 14라운드 5초 리듬 대체 `DodgeTrialRunner`) 결과를 합쳐
 * 성향 벡터 + 무기별 가산으로 '운명' 무기를 정한다.
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

/** 디버그 자동 획 (?debug=1, 헤드리스 검증용): 정규화 좌표 경로 3개 · 점 간격 ms · 획 사이 쉼 */
type AutoPreset = 'fast' | 'slow' | 'round';
const AUTO_STROKES: Record<AutoPreset, [number, number][][]> = {
  fast: [0.2, 0.42, 0.64].map((y0) =>
    Array.from({ length: 9 }, (_, i) => [0.18 + i * 0.07, y0 + (i % 2 === 0 ? 0 : 0.08)] as [number, number]),
  ),
  slow: [0.25, 0.45, 0.65].map((y0) =>
    Array.from({ length: 14 }, (_, i) => [0.15 + i * 0.05, y0 + i * 0.004] as [number, number]),
  ),
  round: [0.3, 0.5, 0.7].map((cx) =>
    Array.from({ length: 16 }, (_, i) => {
      const a = Math.PI * (1 + i / 10);
      return [cx + 0.12 * Math.cos(a), 0.4 + 0.2 * Math.sin(a)] as [number, number];
    }),
  ),
};
const AUTO_STEP_MS: Record<AutoPreset, number> = { fast: 16, slow: 90, round: 40 };
const AUTO_GAP_MS = 250;
/** 디버그 회피 시험 강제 집계 프리셋 (평가 검증용) */
type TrialPreset = 'far' | 'close' | 'dash' | 'tank' | 'fell' | 'clean';
const TRIAL_FULL = { survivedMs: DODGE_TRIAL.DURATION_MS, frames: 900 };
const TRIAL_PRESETS: Record<TrialPreset, Partial<DodgeSample>> = {
  far: { ...TRIAL_FULL, movingFrames: 540, dashes: 2, hits: 1, passes: { close: 1, mid: 3, far: 10 } },
  close: { ...TRIAL_FULL, movingFrames: 450, dashes: 3, dashDodges: 1, hits: 1, passes: { close: 8, mid: 4, far: 1 } },
  dash: { ...TRIAL_FULL, movingFrames: 750, dashes: 8, dashDodges: 4, hits: 2, passes: { close: 9, mid: 3, far: 0 } },
  tank: { ...TRIAL_FULL, movingFrames: 300, dashes: 1, hits: 7, passes: { close: 4, mid: 4, far: 2 } },
  fell: { survivedMs: 7000, frames: 420, movingFrames: 140, dashes: 1, hits: 3, falls: 1 },
  clean: { ...TRIAL_FULL, movingFrames: 700, dashes: 3, passes: { close: 0, mid: 2, far: 12 } },
};

export class Setup extends Phaser.Scene {
  private phase: Phase = 'strokes';
  private strokes: Stroke[] = [];
  private current: Stroke | null = null;
  private label: Phaser.GameObjects.Text;
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
  /** 획 찢기 연출 (strokes 단계에서만) */
  private strokeFx?: StrokeFx;
  /** 회피 시험 (trial 단계) · 화면 고정 글자용 카메라 (메인 카메라는 경기장 2배 확대) */
  private runner?: DodgeTrialRunner;
  private uiCam?: Phaser.Cameras.Scene2D.Camera;
  private trialSample?: DodgeSample;
  private trialEval?: DodgeEvaluation;
  private weaponId?: string;

  constructor() {
    super(SCENES.SETUP);
  }

  create(): void {
    audio.setState('title');
    this.phase = 'meta';
    this.strokes = [];
    this.current = null;
    this.playerName = '';
    this.strokeFx = undefined;
    this.runner = undefined;
    this.uiCam = undefined;
    this.trialSample = undefined;
    this.trialEval = undefined;
    this.features = undefined;
    this.weaponId = undefined;
    // 새 런은 1층: 이전 런이 바꿔 둔 층 변형을 원본으로 (시트·예고 색)
    spriteLibrary.activate(this, 1);
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
      this.strokeFx?.destroy();
      this.strokeFx = undefined;
      this.runner?.destroy();
      this.runner = undefined;
      this.events.off(Phaser.Scenes.Events.ADDED_TO_SCENE, this.hideFromUiCam, this);
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
    this.strokeFx = new StrokeFx(this);
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
      this.strokeFx?.update(time);
      return;
    }
    this.strokeFx?.update(time); // 마지막 획 섬광·사라짐
    if (this.phase !== 'trial' || !this.runner) return;
    const mx = (this.keys.right.isDown ? 1 : 0) - (this.keys.left.isDown ? 1 : 0);
    const my = (this.keys.down.isDown ? 1 : 0) - (this.keys.up.isDown ? 1 : 0);
    const dash = Phaser.Input.Keyboard.JustDown(this.keys.dash);
    this.runner.update(time, delta, { mx, my, dash });
    if (this.runner.phase === 'intro') this.label.setText(DODGE_TRIAL.TEXT.INTRO);
    else if (this.runner.phase === 'run')
      this.label.setText(
        fill(DODGE_TRIAL.TEXT.RUN, {
          sec: (this.runner.timeLeftMs / 1000).toFixed(1),
          hits: this.runner.sample.hits,
        }),
      );
  }

  private onPointerDown(p: Phaser.Input.Pointer): void {
    if (this.phase !== 'strokes') return;
    this.current = [{ x: p.x, y: p.y, t: p.downTime }];
    this.strokeFx?.begin(p.x, p.y, p.downTime);
  }

  private onPointerMove(p: Phaser.Input.Pointer): void {
    if (this.phase !== 'strokes' || !this.current || !p.isDown) return;
    const last = this.current[this.current.length - 1];
    if (Math.hypot(p.x - last.x, p.y - last.y) < 2) return;
    this.current.push({ x: p.x, y: p.y, t: p.moveTime });
    this.strokeFx?.move(p.x, p.y, p.moveTime);
  }

  private onPointerUp(p: Phaser.Input.Pointer): void {
    if (this.phase !== 'strokes' || !this.current) return;
    this.current.push({ x: p.x, y: p.y, t: p.upTime });
    this.strokeFx?.end(p.x, p.y, p.upTime);
    if (this.current.length >= PERSONALITY.strokes.minPoints) this.strokes.push(this.current);
    this.current = null;
    this.updateLabel();
    if (this.strokes.length >= PERSONALITY.strokes.count) {
      this.hideExamples();
      this.phase = 'trial';
      // 마지막 획의 섬광·식는 자국을 잠깐 보여 주고 사라진 뒤 회피 시험
      this.time.delayedCall(STROKE_FX.HOLD_AFTER_LAST_MS, () => {
        const fx = this.strokeFx;
        if (!fx) return this.beginTrial();
        fx.fadeOut(() => {
          if (this.strokeFx === fx) this.strokeFx = undefined;
          this.beginTrial();
        });
      });
    }
  }

  private updateLabel(): void {
    if (this.phase === 'strokes') {
      this.label.setText(
        `${STORY.diary.beforeFate}  (${this.strokes.length}/${PERSONALITY.strokes.count})\n마우스를 누른 채 긋고 떼면 한 획`,
      );
    }
  }

  /**
   * 회피 시험 시작: 메인 카메라 = 경기장 중심 2배 확대(게임 카메라와 같은 배율), 글자는 확대 없는 UI 카메라에만.
   * 이후 씬에 추가되는 오브젝트(투사체·예고·이펙트)는 UI 카메라에서 숨긴다.
   */
  private beginTrial(): void {
    if (this.runner || !this.scene.isActive()) return;
    this.phase = 'trial';
    const main = this.cameras.main;
    this.uiCam = this.cameras.add(0, 0, GAME.WIDTH, GAME.HEIGHT).setName('setup-ui');
    this.uiCam.ignore(this.children.list.filter((c) => c !== this.label));
    main.ignore(this.label);
    this.events.on(Phaser.Scenes.Events.ADDED_TO_SCENE, this.hideFromUiCam, this);
    main.setZoom(DODGE_TRIAL.ZOOM);
    main.centerOn(GAME.WIDTH / 2, GAME.HEIGHT / 2 - DODGE_TRIAL.ARENA.OFFSET_Y_PX);
    this.runner = new DodgeTrialRunner(this, (s) => this.onTrialDone(s));
    this.runner.start(this.time.now);
    this.label.setText(DODGE_TRIAL.TEXT.INTRO);
  }

  private hideFromUiCam(go: Phaser.GameObjects.GameObject): void {
    if (go !== this.label) this.uiCam?.ignore(go);
  }

  /** 시험 끝: 결과 한 줄(자리표시) → 잠시 뒤 운명 */
  private onTrialDone(sample: DodgeSample): void {
    if (this.trialEval) return;
    this.trialSample = { ...sample, passes: { ...sample.passes } };
    this.trialEval = evaluateDodge(this.trialSample, PERSONALITY.rhythm.dashSaturation);
    this.label.setText(DODGE_TRIAL.TEXT.RESULT[this.trialEval.kind]);
    this.time.delayedCall(DODGE_TRIAL.RESULT_MS, () => this.decideFate());
  }

  /** 검증 훅 (?debug=1): 단계·획 연출·회피 시험 상태 + 자동 입력. 게임 로직이 아니다 */
  private exposeDebug(): void {
    if (typeof location === 'undefined' || !new URLSearchParams(location.search).has('debug')) return;
    const api = Object.assign(
      () => ({
        phase: this.phase,
        strokes: this.strokes.length,
        strokeFx: this.strokeFx?.summary() ?? null,
        trial: this.runner?.snapshot() ?? null,
        camera: { zoom: this.cameras.main.zoom, uiCam: Boolean(this.uiCam) },
        evaluation: this.trialEval ?? null,
        features: this.features ?? null,
        weapon: this.weaponId ?? null,
      }),
      {
        /** 메타·이름 단계를 건너뛰고 획 단계로 */
        skipToStrokes: (name = 'debug') => {
          if (this.phase === 'meta') this.beginName();
          if (this.phase === 'name') this.finishName(name);
          return this.phase;
        },
        /** 3획 자동 입력 (같은 포인터 처리 경로, 프레임 간격으로 그린다). preset: fast · slow · round */
        autoStrokes: (preset: AutoPreset = 'fast') => this.autoStrokes(preset),
        /** 회피 시험 즉시 종료 + 강제 집계: 프리셋 이름 또는 DodgeSample 일부 */
        skipTrial: (arg: TrialPreset | Partial<DodgeSample> = 'far') => {
          if (this.phase !== 'trial') return false;
          if (!this.runner) this.beginTrial();
          const over = typeof arg === 'string' ? TRIAL_PRESETS[arg] : arg;
          this.runner!.forceEnd(over);
          return true;
        },
      },
    );
    (window as unknown as { __lopadSetup: unknown }).__lopadSetup = api;
  }

  private autoStrokes(preset: AutoPreset): boolean {
    if (this.phase !== 'strokes') return false;
    const paths = AUTO_STROKES[preset];
    const stepMs = AUTO_STEP_MS[preset];
    let delay = 0;
    for (const path of paths) {
      const pts = path.map(([x, y]) => ({ x: x * GAME.WIDTH, y: y * GAME.HEIGHT }));
      pts.forEach((pt, i) => {
        this.time.delayedCall(delay + i * stepMs, () => {
          const t = this.time.now;
          const p = { x: pt.x, y: pt.y, downTime: t, moveTime: t, upTime: t, isDown: true } as Phaser.Input.Pointer;
          if (i === 0) this.onPointerDown(p);
          else if (i === pts.length - 1) this.onPointerUp(p);
          else this.onPointerMove(p);
        });
      });
      delay += pts.length * stepMs + AUTO_GAP_MS;
    }
    return true;
  }

  private decideFate(): void {
    if (this.phase === 'fate') return;
    this.phase = 'fate';
    this.runner?.dim();
    const ev = this.trialEval ?? evaluateDodge(emptySample(), PERSONALITY.rhythm.dashSaturation);
    const f: Affinity = { ...strokeFeatures(this.strokes, PERSONALITY), ...ev.keys };
    this.features = f;
    const { id } = chooseWeapon(f, WEAPONS, PERSONALITY, ev.bias);
    this.weaponId = id;
    const w = WEAPONS[id];
    __system.emit(UI_EVENTS.FATE_DECIDED, { weaponName: w.name, features: f });
    EventBus.emit(Events.FATE_DECIDED, { weapon: id });
    const a = ev.axes;
    this.label.setText(
      `${this.playerName || '―'}\n\n${fill(STORY.diary.fate, { weapon: w.name })}\n\n(획 길이 ${f.strokeLength.toFixed(2)} 속도 ${f.strokeSpeed.toFixed(2)} 직선 ${f.straightness.toFixed(2)} · 회피 멀리 ${a.far.toFixed(2)} 직전 ${a.close.toFixed(2)} 대쉬 ${a.dashDodge.toFixed(2)} 버팀 ${a.endure.toFixed(2)} 무피격 ${a.clean.toFixed(2)}${ev.rare.flag ? ' · 희귀' : ''})`,
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
