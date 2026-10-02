import Phaser from 'phaser';
import { COLORS, DEPTH, GAME, KEYS, PLACEHOLDER_UI, PROTOTYPE, SCENES } from '../core/Constants';
import { PERSONALITY, STORY, WEAPONS } from '../data';
import { fill } from '../systems/story';
import { chooseWeapon, strokeFeatures, type Stroke, type StrokeFeatures } from '../systems/personality';
import {
  ARENA_SHAPES,
  DODGE_TRIAL,
  emptySample,
  gradeTrial,
  type ArenaShape,
  type DodgeSample,
  type TrialGrade,
  type TrialResult,
} from '../systems/dodgeTrial';
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

type Phase = 'meta' | 'name' | 'strokes' | 'burst' | 'trial' | 'fate';

/**
 * 개성 선택 (기획 1장): "가장 강한 것"을 3획으로 그린다(48라운드 Q8: 화면이 찢기며 빛이 새는 연출 `StrokeFx`,
 * 49라운드 1절: 부스러기 + 3획 뒤 흔들림 → 획에서 빛이 터짐). **무기는 3획만으로** 정한다(49라운드 2절).
 * 이어서 15초 회피 시험(`DodgeTrialRunner`, 무작위 경기장이 가장자리부터 갉아먹힘)의 버틴 시간·피격으로
 * 등급 → 시작 감각 +0~3 (`senseBonus`, Game 씬 시작 데이터로 넘긴다).
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
/** 디버그 회피 시험 강제 집계 프리셋: 등급 지정(S·A·B·C) + 떨어짐(fell, 12초에 1회 피격 → B) */
type TrialPreset = TrialGrade | 'fell';
const TRIAL_FULL = { survivedMs: DODGE_TRIAL.DURATION_MS, frames: 900, movingFrames: 600 };
const TRIAL_PRESETS: Record<TrialPreset, Partial<DodgeSample>> = {
  S: { ...TRIAL_FULL, hits: 0 },
  A: { ...TRIAL_FULL, hits: 3 },
  B: { ...TRIAL_FULL, hits: 7 },
  C: { survivedMs: 6000, frames: 360, movingFrames: 200, hits: 3, falls: 1 },
  fell: { survivedMs: 12000, frames: 720, movingFrames: 500, hits: 1, falls: 1 },
};

export class Setup extends Phaser.Scene {
  private phase: Phase = 'strokes';
  private strokes: Stroke[] = [];
  private current: Stroke | null = null;
  private label: Phaser.GameObjects.Text;
  private keys: Record<string, Phaser.Input.Keyboard.Key>;
  private features?: StrokeFeatures;
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
  private trialResult?: TrialResult;
  private weaponId?: string;
  /** Game 씬 시작 데이터 (디버그 표시용) */
  private startData?: { mode: 'new'; weapon: string; playerName: string; senseBonus: number };
  /** 디버그: 다음 회피 시험 경기장 모양 고정 */
  private forcedShape?: ArenaShape;

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
    this.trialResult = undefined;
    this.forcedShape = undefined;
    this.startData = undefined;
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
    this.strokeFx?.update(time); // 마지막 획 섬광 → 빛 터짐 → 하얀 빛이 걷힘 (시험 시작 뒤에도 잠깐)
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
    if (this.strokes.length >= PERSONALITY.strokes.count) this.beginBurst();
  }

  /**
   * 3획 완료 (49라운드 1절): 무기는 이 순간 3획만으로 정해 둔다. 마지막 획의 섬광을 잠깐 보여 준 뒤
   * 화면이 살짝 흔들리고 획에서 빛이 터져 나와 하얗게 번쩍 → 가장 하얀 순간에 회피 시험 시작 → 빛이 걷힌다.
   */
  private beginBurst(): void {
    if (this.phase !== 'strokes') return;
    this.hideExamples();
    this.phase = 'burst';
    this.decideWeapon();
    this.time.delayedCall(STROKE_FX.HOLD_AFTER_LAST_MS, () => {
      if (this.phase !== 'burst') return;
      this.label.setText('');
      const fx = this.strokeFx;
      if (!fx) return this.beginTrial();
      fx.burst(
        () => this.beginTrial(),
        () => {
          if (this.strokeFx === fx) this.strokeFx = undefined;
        },
      );
    });
  }

  /** 3획 특징 → 운명 무기 (회피 시험과 무관) */
  private decideWeapon(): void {
    const f = strokeFeatures(this.strokes, PERSONALITY);
    this.features = f;
    this.weaponId = chooseWeapon(f, WEAPONS, PERSONALITY).id;
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
    if (this.runner || !this.scene.isActive() || (this.phase !== 'burst' && this.phase !== 'trial')) return;
    this.phase = 'trial';
    const main = this.cameras.main;
    this.uiCam = this.cameras.add(0, 0, GAME.WIDTH, GAME.HEIGHT).setName('setup-ui');
    this.uiCam.ignore(this.children.list.filter((c) => c !== this.label));
    main.ignore(this.label);
    this.events.on(Phaser.Scenes.Events.ADDED_TO_SCENE, this.hideFromUiCam, this);
    main.setZoom(DODGE_TRIAL.ZOOM);
    main.centerOn(GAME.WIDTH / 2, GAME.HEIGHT / 2 - DODGE_TRIAL.ARENA.OFFSET_Y_PX);
    this.startRunner();
  }

  private startRunner(): void {
    this.runner = new DodgeTrialRunner(this, (s) => this.onTrialDone(s), { shape: this.forcedShape });
    this.runner.start(this.time.now);
    this.label.setText(DODGE_TRIAL.TEXT.INTRO);
  }

  private hideFromUiCam(go: Phaser.GameObjects.GameObject): void {
    if (go !== this.label) this.uiCam?.ignore(go);
  }

  /** 시험 끝: 등급·시작 감각 보상(자리표시 문구) → 잠시 뒤 운명 */
  private onTrialDone(sample: DodgeSample): void {
    if (this.trialResult) return;
    this.trialSample = { ...sample, passes: { ...sample.passes } };
    const r = gradeTrial(this.trialSample);
    this.trialResult = r;
    const T = DODGE_TRIAL.TEXT;
    this.label.setText(
      fill(T.RESULT, {
        line: T.LINES[r.fell ? 'fell' : r.grade],
        grade: r.grade,
        bonus: r.bonus,
        sec: (sample.survivedMs / 1000).toFixed(1),
        hits: sample.hits,
      }),
    );
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
        result: this.trialResult ?? null,
        senseBonus: this.trialResult?.bonus ?? null,
        forcedShape: this.forcedShape ?? null,
        startData: this.startData ?? null,
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
        /**
         * 회피 시험 즉시 종료 + 강제 집계: 등급 'S'|'A'|'B'|'C'(감각 +3/+2/+1/+0) · 'fell' 또는 DodgeSample 일부.
         * 빛 터짐 중이면 기다리지 않고 바로 시험을 열어 끝낸다.
         */
        skipTrial: (arg: TrialPreset | Partial<DodgeSample> = 'S') => {
          if (this.phase !== 'trial' && this.phase !== 'burst') return false;
          if (!this.runner) this.beginTrial();
          if (!this.runner) return false;
          const over = typeof arg === 'string' ? TRIAL_PRESETS[arg] : arg;
          this.runner.forceEnd(over);
          return true;
        },
        /** 경기장 모양 고정 ('circle'|'ellipse'|'polygon'|'islands', 없으면 무작위로 되돌림). 시험 중이면 그 모양으로 다시 시작 */
        trialShape: (shape?: ArenaShape) => {
          if (shape && !ARENA_SHAPES.includes(shape)) return false;
          this.forcedShape = shape;
          if (this.phase === 'trial' && this.runner && !this.trialResult) {
            this.runner.destroy();
            this.startRunner();
          }
          return true;
        },
        /** 빛 터짐 시계를 ms 에 멈춤 (null = 풀기). 3획 전에 걸어 둘 수 있다 (스크린샷용) */
        holdBurst: (ms: number | null = null) => {
          if (!this.strokeFx) return false;
          this.strokeFx.holdBurst(ms);
          return true;
        },
        /** 회피 시험 시계를 ms 앞당김 (갉아먹힘 확인용, 안내 중이면 바로 시작) */
        trialWarp: (ms = 5000) => {
          if (!this.runner) return false;
          this.runner.warp(ms);
          return true;
        },
        /** 무적 (맞지 않고 떨어지지 않음, 스크린샷용) */
        trialGod: (on = true) => {
          if (!this.runner) return false;
          this.runner.god = on;
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

  /** 운명 문구 + 시작 감각 보상 → Game (`senseBonus` 0~3 을 시작 데이터로, 49라운드 2절) */
  private decideFate(): void {
    if (this.phase === 'fate') return;
    this.phase = 'fate';
    this.runner?.dim();
    if (!this.weaponId || !this.features) this.decideWeapon();
    const f = this.features!;
    const id = this.weaponId!;
    const r = this.trialResult ?? gradeTrial(emptySample());
    const senseBonus = r.bonus;
    const w = WEAPONS[id];
    __system.emit(UI_EVENTS.FATE_DECIDED, { weaponName: w.name, features: f });
    EventBus.emit(Events.FATE_DECIDED, { weapon: id });
    this.label.setText(
      `${this.playerName || '―'}\n\n${fill(STORY.diary.fate, { weapon: w.name })}\n시작 감각 +${senseBonus}  (시험 등급 ${r.grade})\n\n(획 길이 ${f.strokeLength.toFixed(2)} 속도 ${f.strokeSpeed.toFixed(2)} 직선 ${f.straightness.toFixed(2)})`,
    );
    const data = { mode: 'new' as const, weapon: id, playerName: this.playerName, senseBonus };
    this.startData = data;
    this.time.delayedCall(PROTOTYPE.FATE_BANNER_MS, () => this.scene.start(SCENES.GAME, data));
  }

  /** 디버그/테스트용 */
  get debugFeatures(): StrokeFeatures | undefined {
    return this.features;
  }
}
