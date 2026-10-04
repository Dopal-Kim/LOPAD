import Phaser from 'phaser';
import { COLORS, DEPTH, GAME, KEYS, PLACEHOLDER_UI, PROTOTYPE, SCENES } from '../core/Constants';
import { PERSONALITY, STORY, WEAPONS } from '../data';
import { fill } from '../systems/story';
import { chooseWeapon, strokeFeatures, type Stroke, type StrokeFeatures } from '../systems/personality';
import {
  ARENA_SHAPES,
  DODGE_TRIAL,
  TASK_IDS,
  emptyTaskResult,
  gradeTrial,
  presetResults,
  type ArenaShape,
  type TaskId,
  type TaskResult,
  type TrialGrade,
  type TrialResult,
} from '../systems/dodgeTrial/dodgeTrial';
import { DodgeTrialRunner } from '../systems/dodgeTrial/dodgeTrialRunner';
import { StrokeFx } from '../systems/strokeFx/strokeFx';
import { BACK } from '../systems/strokeFx/strokeFxBack';
import { encodeScar, type ScarData } from '../systems/setup/scar';
import { gameState } from '../core/GameState';
import { STROKE_FX } from '../systems/strokeFx/strokeFxMath';
import { oncePerKeyEvent } from '../systems/keyEvents';
import { StrokeExamples } from '../systems/setup/strokeExamples';
import { scheduleAutoStrokes, type AutoPreset } from '../systems/setup/autoStrokes';
import { TrialHud } from '../systems/setup/trialHud';
import { spriteLibrary } from '../systems/sprites/sprites';
import { META_CONFIG, buyUpgrade, metaStore, upgradeCost } from '../systems/meta';
import { TextMenu } from '../systems/TextMenu';
import { CANVAS_H, CANVAS_W, makeLogicalCamera, toLogical, worldZoom } from '../systems/display';
import { setMenuSelect } from '../contract/host';
import { EventBus, Events } from '../core/EventBus';
import { audio } from '../systems/audio/audio';
import { UI_EVENTS, __system } from '../contract/ui';

type Phase = 'meta' | 'name' | 'strokes' | 'sear' | 'trial' | 'fate';

/**
 * 개성 선택 (기획 1장): "가장 강한 것"을 3획으로 그린다(48라운드 Q8 `StrokeFx`, 51라운드 1절: 가늘고 매끄러운 곡선 획,
 * 53라운드 Q3: 화면 가득 찬 주인공의 등에 긋고, 3획 뒤 상흔이 호박빛으로 타오르다 살에 스며든다).
 * 그은 획은 상흔으로 런 상태에 저장한다(53라운드 Q4 준비, `setup/scar.ts`).
 * **무기는 3획만으로** 정한다(49라운드 2절). 이어서 회피 시험(51라운드 2절: 짧은 과제 5개, `DodgeTrialRunner`)의
 * 과제별 피격·떨어짐으로 등급 → 시작 감각 +0~3 (`senseBonus`, Game 씬 시작 데이터로 넘긴다).
 * 화면·연출은 시스템 파트 플레이스홀더이며 UI·아트 파트 산출물로 교체 대상.
 */
const NAME_MAX = 12;

/** 디버그 강제 결과: 등급(S·A·B·C) · 'fell'(한 과제 떨어짐) · 과제 결과 일부 목록 */
type TrialForce = TrialGrade | 'fell' | Partial<TaskResult>[];

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
  private examples?: StrokeExamples;
  private playerName = '';
  /** 획 찢기 연출 (strokes 단계에서만) */
  private strokeFx?: StrokeFx;
  /** 회피 시험 (trial 단계) · 화면 고정 글자용 카메라 (메인 카메라는 경기장 2배 확대) */
  private runner?: DodgeTrialRunner;
  private hud?: TrialHud;
  private uiCam?: Phaser.Cameras.Scene2D.Camera;
  /** UI 카메라에만 보이는 글자 (라벨 + 시험 카드) */
  private uiOnly: Phaser.GameObjects.GameObject[] = [];
  private trialResult?: TrialResult;
  private weaponId?: string;
  /** 등에 그은 상흔 (Game 시작 직전에 런 상태로 넘긴다) */
  private scar?: ScarData;
  /** Game 씬 시작 데이터 (디버그 표시용) */
  private startData?: { mode: 'new'; weapon: string; playerName: string; senseBonus: number };
  /** 디버그: 다음 회피 시험 경기장 모양 고정 */
  private forcedShape?: ArenaShape;
  /**
   * 대쉬 입력 걸쇠: 키 DOWN 이벤트에서 세우고 다음 프레임에 쓴다. JustDown 은 한 프레임 안에 눌렀다 뗀 짧은 탭을
   * 놓친다(Phaser Key.onUp 이 _justDown 을 지움) — 회피 시험은 대쉬 박자가 핵심이라 탭을 잃지 않게.
   */
  private dashQueued = false;
  private readonly onEscKey = oncePerKeyEvent<KeyboardEvent>(() => this.onEsc());

  /** 53라운드 UI 요청 B4: 회피 시험에서 Esc → 3획부터 다시 (씬을 다시 열어 시험 카메라·경기장을 깨끗이) */
  private resumeAt: { back: 'strokes'; playerName: string } | null = null;

  constructor() {
    super(SCENES.SETUP);
  }

  init(data?: { back?: 'strokes'; playerName?: string }): void {
    this.resumeAt = data?.back === 'strokes' ? { back: 'strokes', playerName: data.playerName ?? '' } : null;
  }

  create(): void {
    audio.setState('title');
    this.phase = 'meta';
    this.strokes = [];
    this.current = null;
    this.playerName = '';
    this.strokeFx = undefined;
    this.runner = undefined;
    this.hud = undefined;
    this.uiCam = undefined;
    this.uiOnly = [];
    this.trialResult = undefined;
    this.forcedShape = undefined;
    this.startData = undefined;
    this.features = undefined;
    this.weaponId = undefined;
    this.scar = undefined;
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
    this.dashQueued = false;
    this.keys.dash.on(Phaser.Input.Keyboard.Events.DOWN, this.queueDash, this);
    this.input.mouse?.disableContextMenu();

    this.input.on('pointerdown', this.onPointerDown, this);
    this.input.on('pointermove', this.onPointerMove, this);
    this.input.on('pointerup', this.onPointerUp, this);
    this.events.once('shutdown', () => {
      this.input.off('pointerdown', this.onPointerDown, this);
      this.input.off('pointermove', this.onPointerMove, this);
      this.input.off('pointerup', this.onPointerUp, this);
      this.keys.dash.off(Phaser.Input.Keyboard.Events.DOWN, this.queueDash, this);
      this.nameInput?.destroy();
      this.nameInput = undefined;
      this.input.keyboard?.enableGlobalCapture();
      this.hideExamples();
      this.strokeFx?.destroy();
      this.strokeFx = undefined;
      this.runner?.destroy();
      this.runner = undefined;
      this.hud?.destroy();
      this.hud = undefined;
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
    // 53라운드 UI 요청 B4: Esc = 한 단계 앞으로 (회피 시험 → 3획 → 이름 → 메타 메뉴)
    // 53라운드: 같은 keydown 객체 재전달(Phaser 3.90 큐 재처리)로 두 단계 물러나지 않게 (keyEvents)
    kb.on('keydown-ESC', this.onEscKey);
    this.events.once('shutdown', () => this.input.keyboard?.off('keydown-ESC', this.onEscKey));
    const resume = this.resumeAt;
    this.resumeAt = null;
    if (resume) {
      this.playerName = resume.playerName;
      this.beginStrokes();
    } else this.openMetaMenu();
  }

  /** Esc: 한 단계 앞으로. 메타 메뉴·운명 단계는 그대로 */
  private onEsc(): void {
    switch (this.phase) {
      case 'name':
        return this.backToMeta();
      case 'strokes':
        return this.backToName();
      case 'sear':
      case 'trial':
        this.scene.restart({ back: 'strokes', playerName: this.playerName });
        return;
      default:
        return;
    }
  }

  /** 이름 → 메타 메뉴 */
  private backToMeta(): void {
    if (this.phase !== 'name') return;
    this.nameInput?.destroy();
    this.nameInput = undefined;
    this.input.keyboard?.enableGlobalCapture();
    this.label.setText('');
    this.phase = 'meta';
    this.openMetaMenu();
  }

  /** 3획 → 이름 (그은 획은 버린다, 적어 둔 이름은 입력란에 남긴다) */
  private backToName(): void {
    if (this.phase !== 'strokes') return;
    this.hideExamples();
    this.strokeFx?.destroy();
    this.strokeFx = undefined;
    this.strokes = [];
    this.current = null;
    this.phase = 'meta';
    this.beginName();
    const node = this.nameInput?.node as HTMLInputElement | undefined;
    if (node) node.value = this.playerName;
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
      this.onEnter = oncePerKeyEvent((e: KeyboardEvent) => {
        if (e.key === 'Enter' && this.phase === 'meta') this.beginName();
      });
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
      else if (e.key === 'Escape') this.backToMeta();
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

  private showExamples(): void {
    this.examples = new StrokeExamples(this);
    this.examples.show();
  }

  private hideExamples(): void {
    this.examples?.hide();
    this.examples = undefined;
  }

  update(time: number, delta: number): void {
    if (this.phase === 'strokes') {
      this.examples?.draw(time);
      this.strokeFx?.update(time);
      return;
    }
    this.strokeFx?.update(time); // 마지막 획 섬광 → 타오름·스며듦 → 어둠이 걷힘 (시험 시작 뒤에도 잠깐)
    if (this.phase !== 'trial' || !this.runner) return;
    const mx = (this.keys.right.isDown ? 1 : 0) - (this.keys.left.isDown ? 1 : 0);
    const my = (this.keys.down.isDown ? 1 : 0) - (this.keys.up.isDown ? 1 : 0);
    const dash = this.dashQueued;
    this.dashQueued = false;
    this.runner.update(time, delta, { mx, my, dash });
    if (!this.trialResult) this.hud?.update(this.runner.status());
  }

  private queueDash(): void {
    if (this.phase === 'trial') this.dashQueued = true;
  }

  /** 52라운드: 포인터는 실제 캔버스 px(1920×1080) → 획 판정·연출은 논리 px(960×540) */
  private onPointerDown(p: Phaser.Input.Pointer): void {
    if (this.phase !== 'strokes') return;
    const x = toLogical(p.x);
    const y = toLogical(p.y);
    this.current = [{ x, y, t: p.downTime }];
    this.strokeFx?.begin(x, y, p.downTime);
  }

  private onPointerMove(p: Phaser.Input.Pointer): void {
    if (this.phase !== 'strokes' || !this.current || !p.isDown) return;
    // 51라운드: 브라우저가 한 프레임에 묶은 중간 포인터 점도 연출에 넣는다 (빠른 곡선이 매끄럽게). 판정 점은 그대로
    const ev = p.event as PointerEvent | undefined;
    const merged = typeof ev?.getCoalescedEvents === 'function' ? ev.getCoalescedEvents() : [];
    for (let k = 0; k < merged.length - 1; k++)
      this.strokeFx?.move(
        toLogical(this.scale.transformX(merged[k].pageX)),
        toLogical(this.scale.transformY(merged[k].pageY)),
        merged[k].timeStamp,
      );
    const x = toLogical(p.x);
    const y = toLogical(p.y);
    const last = this.current[this.current.length - 1];
    if (Math.hypot(x - last.x, y - last.y) < 2) {
      this.strokeFx?.move(x, y, p.moveTime);
      return;
    }
    this.current.push({ x, y, t: p.moveTime });
    this.strokeFx?.move(x, y, p.moveTime);
  }

  private onPointerUp(p: Phaser.Input.Pointer): void {
    if (this.phase !== 'strokes' || !this.current) return;
    const x = toLogical(p.x);
    const y = toLogical(p.y);
    this.current.push({ x, y, t: p.upTime });
    this.strokeFx?.end(x, y, p.upTime);
    if (this.current.length >= PERSONALITY.strokes.minPoints) this.strokes.push(this.current);
    this.current = null;
    this.updateLabel();
    if (this.strokes.length >= PERSONALITY.strokes.count) this.beginSear();
  }

  /**
   * 3획 완료: 무기는 이 순간 3획만으로 정해 둔다(49라운드 1절). 마지막 획의 섬광을 잠깐 보여 준 뒤 (53라운드 Q3)
   * 획이 호박빛으로 타오름 → 살에 스며들어 균열 + 잔불 심 → 불티 → 검게 덮인 순간 회피 시험 시작 → 어둠이 걷힌다.
   */
  private beginSear(): void {
    if (this.phase !== 'strokes') return;
    this.hideExamples();
    this.phase = 'sear';
    this.decideWeapon();
    this.time.delayedCall(STROKE_FX.HOLD_AFTER_LAST_MS, () => {
      if (this.phase !== 'sear') return;
      this.label.setText('');
      const fx = this.strokeFx;
      if (!fx) return this.beginTrial();
      fx.sear(
        () => this.beginTrial(),
        () => {
          if (this.strokeFx === fx) this.strokeFx = undefined;
        },
      );
    });
  }

  /** 3획 특징 → 운명 무기 (회피 시험과 무관) + 상흔 저장 형식 (53라운드 Q4 준비) */
  private decideWeapon(): void {
    const f = strokeFeatures(this.strokes, PERSONALITY);
    this.features = f;
    this.weaponId = chooseWeapon(f, WEAPONS, PERSONALITY).id;
    this.scar = encodeScar(this.strokes, BACK.SCAR_RECT);
  }

  private updateLabel(): void {
    if (this.phase === 'strokes') {
      this.label.setText(
        `${STORY.diary.beforeFate}  (${this.strokes.length}/${PERSONALITY.strokes.count})\n마우스를 누른 채 긋고 떼면 한 획`,
      );
    }
  }

  /**
   * 회피 시험 시작: 메인 카메라 = 경기장 중심 2배 확대(게임 카메라와 같은 배율), 글자(라벨·카드)는 확대 없는 UI 카메라에만.
   * 이후 씬에 추가되는 오브젝트(투사체·예고·이펙트)는 UI 카메라에서 숨긴다.
   */
  private beginTrial(): void {
    if (this.runner || !this.scene.isActive() || (this.phase !== 'sear' && this.phase !== 'trial')) return;
    this.phase = 'trial';
    const main = this.cameras.main;
    this.hud = new TrialHud(this, this.label);
    this.uiOnly = [this.label, ...this.hud.objects];
    // 52라운드: UI 카메라 = 논리 카메라(캔버스 전체, 960×540 좌표), 시험 카메라 = 월드 카메라(원점 가운데·논리 배율 × RESOLUTION)
    this.uiCam = makeLogicalCamera(this.cameras.add(0, 0, CANVAS_W, CANVAS_H).setName('setup-ui'));
    this.uiCam.ignore(this.children.list.filter((c) => !this.uiOnly.includes(c)));
    main.ignore(this.uiOnly);
    this.events.on(Phaser.Scenes.Events.ADDED_TO_SCENE, this.hideFromUiCam, this);
    main.setOrigin(0.5).setZoom(worldZoom(DODGE_TRIAL.ZOOM));
    main.centerOn(GAME.WIDTH / 2, GAME.HEIGHT / 2 - DODGE_TRIAL.ARENA.OFFSET_Y_PX);
    this.startRunner();
  }

  private startRunner(): void {
    this.runner = new DodgeTrialRunner(this, (r) => this.onTrialDone(r), { shape: this.forcedShape });
    this.runner.start(this.time.now);
    this.hud?.update(this.runner.status());
  }

  private hideFromUiCam(go: Phaser.GameObjects.GameObject): void {
    if (!this.uiOnly.includes(go)) this.uiCam?.ignore(go);
  }

  /** 시험 끝: 과제별 결과 한 줄씩 + 등급·시작 감각 보상(자리표시 문구) → 잠시 뒤 운명 */
  private onTrialDone(results: TaskResult[]): void {
    if (this.trialResult) return;
    const r = gradeTrial(results);
    this.trialResult = r;
    this.hud?.showResult(r);
    this.time.delayedCall(DODGE_TRIAL.RESULT_MS, () => this.decideFate());
  }

  /** 디버그 강제 결과 → 과제 결과 목록 */
  private forcedResults(arg: TrialForce): TaskResult[] {
    if (typeof arg === 'string') return presetResults(arg);
    return TASK_IDS.map((id, i) => ({ ...emptyTaskResult(id), ...(arg[i] ?? {}), id }));
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
        scar: this.scar ?? null,
      }),
      {
        /** 메타·이름 단계를 건너뛰고 획 단계로 */
        skipToStrokes: (name = 'debug') => {
          if (this.phase === 'meta') this.beginName();
          if (this.phase === 'name') this.finishName(name);
          return this.phase;
        },
        /** 3획 자동 입력 (같은 포인터 처리 경로, 프레임 간격으로 그린다). preset: fast · slow · round */
        autoStrokes: (preset: AutoPreset = 'fast') => {
          if (this.phase !== 'strokes') return false;
          scheduleAutoStrokes(this, preset, {
            down: (p) => this.onPointerDown(p),
            move: (p) => this.onPointerMove(p),
            up: (p) => this.onPointerUp(p),
          });
          return true;
        },
        /**
         * 회피 시험 즉시 종료 + 강제 등급: 'S'|'A'|'B'|'C'(감각 +3/+2/+1/+0) · 'fell'(한 과제 떨어짐) 또는 과제 결과 일부 목록.
         * 타오름·스며듦 중이면 기다리지 않고 바로 시험을 열어 끝낸다. (`trialForceGrade` 와 같다)
         */
        skipTrial: (arg: TrialForce = 'S') => this.debugForce(arg),
        trialForceGrade: (arg: TrialForce = 'S') => this.debugForce(arg),
        /** 지금 과제를 바로 끝낸다 (결과 덮어쓰기: { hits, fell }) → 결과 한 줄 → 다음 과제 */
        trialSkipTask: (over: Partial<TaskResult> = {}) => this.ensureRunner()?.skipTask(over) ?? false,
        /** 특정 과제부터 (1~5 또는 'lines'|'ring'|'homing'|'wall'|'mix'). 앞 과제는 건너뜀(무피격으로 침) */
        trialStartTask: (n: number | TaskId = 1) => {
          const idx = typeof n === 'number' ? n - 1 : TASK_IDS.indexOf(n);
          return this.ensureRunner()?.startTask(idx) ?? false;
        },
        /** 경기장 모양 고정 ('circle'|'ellipse'|'polygon'|'islands', 없으면 과제별 무작위). 시험 중이면 첫 과제부터 다시 */
        trialShape: (shape?: ArenaShape) => {
          if (shape && !ARENA_SHAPES.includes(shape)) return false;
          this.forcedShape = shape;
          if (this.runner && !this.trialResult) {
            this.runner.destroy();
            this.startRunner();
          }
          return true;
        },
        /** 타오름·스며듦 시계를 ms 에 멈춤 (null = 풀기). 3획 전에 걸어 둘 수 있다 (스크린샷용) */
        holdSear: (ms: number | null = null) => {
          if (!this.strokeFx) return false;
          this.strokeFx.holdSear(ms);
          return true;
        },
        /** 카드·정비면 바로 과제 시작, 과제 중이면 과제 시계를 ms 앞당김 (갉아먹힘·예약) */
        trialWarp: (ms = 2000) => {
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

  /** 시험 단계가 아직 안 열렸으면(타오름·스며듦 중) 바로 연다 */
  private ensureRunner(): DodgeTrialRunner | undefined {
    if (this.phase !== 'trial' && this.phase !== 'sear') return undefined;
    if (!this.runner) this.beginTrial();
    return this.runner;
  }

  private debugForce(arg: TrialForce): boolean {
    const runner = this.ensureRunner();
    if (!runner || this.trialResult) return false;
    runner.forceEnd(this.forcedResults(arg));
    return true;
  }

  /** 운명 문구 + 시작 감각 보상 → Game (`senseBonus` 0~3 을 시작 데이터로, 49라운드 2절) */
  private decideFate(): void {
    if (this.phase === 'fate') return;
    this.phase = 'fate';
    this.runner?.dim();
    this.hud?.hideCard();
    if (!this.weaponId || !this.features) this.decideWeapon();
    const f = this.features!;
    const id = this.weaponId!;
    const r = this.trialResult ?? gradeTrial([]);
    const senseBonus = r.bonus;
    const w = WEAPONS[id];
    __system.emit(UI_EVENTS.FATE_DECIDED, { weaponName: w.name, features: f });
    EventBus.emit(Events.FATE_DECIDED, { weapon: id });
    this.label.setText(
      `${this.playerName || '―'}\n\n${fill(STORY.diary.fate, { weapon: w.name })}\n시작 감각 +${senseBonus}  (시험 등급 ${r.grade})\n\n(획 길이 ${f.strokeLength.toFixed(2)} 속도 ${f.strokeSpeed.toFixed(2)} 직선 ${f.straightness.toFixed(2)})`,
    );
    const data = { mode: 'new' as const, weapon: id, playerName: this.playerName, senseBonus };
    this.startData = data;
    this.time.delayedCall(PROTOTYPE.FATE_BANNER_MS, () => {
      gameState.queueScar(this.scar ?? null); // 다음 startRun(새 런)이 가져간다
      this.scene.start(SCENES.GAME, data);
    });
  }

  /** 디버그/테스트용 */
  get debugFeatures(): StrokeFeatures | undefined {
    return this.features;
  }
}
