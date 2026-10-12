import Phaser from 'phaser';
import { RITUAL, SCENES } from '../core/Constants';
import { PERSONALITY, WEAPONS } from '../data';
import { RITUAL_DATA } from '../data/ritual';
import { fill } from '../systems/story';
import { chooseWeapon, strokeFeatures, type Stroke } from '../systems/personality';
import { encodeScar, type ScarData } from '../systems/setup/scar';
import { BACK } from '../systems/strokeFx/strokeFxBack';
import { gameState } from '../core/GameState';
import { autoStrokePoints, type AutoPreset } from '../systems/setup/autoStrokes';
import { spriteLibrary } from '../systems/sprites/sprites';
import { enemySheetRequests, missingRequests } from '../systems/sprites/lazySheets';
import { queueRequests } from '../systems/sprites/sheetLoader';
import { META_CONFIG, metaStore } from '../systems/meta';
import { settings } from '../systems/settings';
import { TextMenu } from '../systems/TextMenu';
import { worldZoom } from '../systems/display';
import { setMenuSelect, setRitualHost } from '../contract/host';
import { EventBus, Events } from '../core/EventBus';
import { audio } from '../systems/audio/audio';
import {
  UI_EVENTS,
  __system,
  uiCommands,
  type UiRitual,
  type UiRitualCommand,
  type UiRitualPoint,
  type UiRitualStrokeJudged,
  type UiMenuId,
} from '../contract/ui';
import { UI_SCENES } from '../ui';
import { trainingText } from '../data/training';
import { recordOffered } from '../systems/training/record';
import { trainingDoorName } from '../systems/transition/doorNames';
import { NARRATIVE_STORY, voiceLine } from '../data/narrative';
import {
  isFirstLife,
  koreanCount,
  readDiary,
  recordBirth,
  updateDiary,
  type DiaryRecord,
} from '../systems/narrative/diary';
import {
  cleanName,
  gradeHits,
  leaningWeapon,
  legendOf,
  metaCorner,
  rememberedWeapon,
  whyOf,
} from '../systems/ritual/ritual';
import { firstSteps } from '../systems/ritual/firstSteps';
import { MemoryPicks } from './setup/MemoryPicks';
import { canUnlockAny } from '../systems/memory/memory';
import { RUN_END } from '../data/runEnd';
import { loadRunEndArt } from './game/RunEndArt';
import { BirthTrialRunner } from './setup/BirthTrialRunner';
import { trialPropRequests } from './setup/trialProps';
import { doorFor, loadDoorIndex, loadPaint, paintLoaded } from './game/PaintArt';
import { loadBaseLook } from './game/growth/GrowthArt';

/**
 * 시작 의식 (62 루프 1 — 계약 UI §20 · P0-1·P0-2·P0-3·P1-9): **흐름·판정만** 시스템, 그리기는 UI 의식 씬(`UI_SCENES.RITUAL`, 없으면
 * 시스템 대체 화면 `RitualView` — 같은 계약만 쓴다). 상태 = `UiSnapshot.ritual`(+ `RITUAL` 이벤트), 명령 = `uiCommands.ritual.*`.
 * - 첫 생: ('수련장부터 / 바로 벽 밖으로' 한 번) → 이름 → 3획 → 회피 시험(탄생 전장 타일 위 실제 사수, `BirthTrialRunner`) → 운명 공개.
 *   영혼 강화 메뉴는 첫 생에 열지 않는다(P0-3).
 * - 두 번째 생부터: 이름 덧쓰기 한 화면(rewrite) → 운명 공개(손이 기억한 무기 = 지난 생 무기). `ritual.redraw` 면 3획만 다시(회피 시험 없음).
 *   영혼 강화는 이 화면 귀퉁이(`ritual.openMeta` → MENU 'meta').
 * 무기는 **3획만으로** 정한다(49라운드 2절, `personality.chooseWeapon`). 회피 시험은 첫 개성 발현 카드 수만(62 루프 2 C — S·A 4 / B·C 3). 그은 획은 상흔으로 런 상태에.
 * 화면에 획 판정 수치를 내보내지 않는다 — 운명 공개는 '왜' 한 줄(무기 목소리 말투, `data/narrative.json ritual.why`).
 */
const NAME_MAX = 12;

type Phase = 'choice' | 'name' | 'rewrite' | 'meta' | 'strokes' | 'seal' | 'trial' | 'fate';

export class Setup extends Phaser.Scene {
  private phase: Phase = 'choice';
  private strokes: Stroke[] = [];
  private keys: Record<string, Phaser.Input.Keyboard.Key>;
  private menu: TextMenu;
  private diary: DiaryRecord = readDiary({ runs: 0, clears: 0 });
  private firstLife = true;
  private playerName = '';
  /** 덧쓰기 결과 한 줄 (두 번째 생) */
  private smudgeResult = '';
  /** 두 번째 생: 3획을 다시 긋는 중 (회피 시험 없음) */
  private redrawing = false;
  private weaponId?: string;
  private weaponSource: 'strokes' | 'remembered' = 'strokes';
  private scar?: ScarData;
  private runner?: BirthTrialRunner;
  /** 회피 시험 맞은 수 (끝났을 때) · 건너뜀 */
  private trialHits: number | null = null;
  private trialSkipped = false;
  private lookKey?: string;
  private startData?: {
    mode: 'new';
    weapon: string;
    playerName: string;
    traitCards: number;
    keepsake: string | null;
    aspect: string | null;
  };
  /** 62 루프 2 C (P1-8): 기억 장 · 운명 공개 뒤 모양·소품 고르기 */
  private picks!: MemoryPicks;
  /** 회피 시험 등급이 정한 첫 개성 발현 카드 수 (0 = 기본) */
  private trialCards = 0;
  private fateTimer?: Phaser.Time.TimerEvent;
  /** 대쉬 입력 걸쇠 (짧은 탭을 놓치지 않게 — keydown 에서 세우고 다음 프레임에 쓴다) */
  private dashQueued = false;
  /** Setup 위에 띄운 의식 화면 씬 키 (UI 또는 시스템 대체) */
  private overlayKey: string = SCENES.RITUAL_VIEW;
  /** 회피 시험 Esc: 씬을 다시 열어 3획부터 */
  private resumeAt: { playerName: string; redrawing: boolean } | null = null;

  constructor() {
    super(SCENES.SETUP);
  }

  init(data?: { back?: 'strokes'; playerName?: string; redrawing?: boolean }): void {
    this.resumeAt =
      data?.back === 'strokes' ? { playerName: data.playerName ?? '', redrawing: Boolean(data.redrawing) } : null;
  }

  preload(): void {
    // 회피 시험 사수 그림 (지난 런이 보스방에서 끝났으면 내려 가 있다)
    // + 62 art §30 탄생 전장 소품
    queueRequests(
      this,
      missingRequests(this, [...enemySheetRequests(), ...trialPropRequests(RITUAL_DATA.trial.props)]),
      () => {},
    );
    loadDoorIndex(this);
  }

  create(): void {
    audio.setState('title');
    this.strokes = [];
    this.playerName = '';
    this.smudgeResult = '';
    this.redrawing = false;
    this.weaponId = undefined;
    this.weaponSource = 'strokes';
    this.scar = undefined;
    this.runner = undefined;
    this.trialHits = null;
    this.trialSkipped = false;
    this.lookKey = undefined;
    this.startData = undefined;
    this.fateTimer = undefined;
    this.diary = readDiary(metaStore.read());
    this.firstLife =
      isFirstLife(this.diary) ||
      (typeof location !== 'undefined' && new URLSearchParams(location.search).get('ritual') === 'full');
    // 새 런은 1층: 이전 런이 바꿔 둔 층 변형을 원본으로 (시트·예고 색)
    spriteLibrary.activate(this, 1);
    const kb = this.input.keyboard!;
    // 62 D (P1-16): 회피 시험 이동·대쉬도 설정 키
    const bound = settings.current().keys;
    this.keys = {
      up: kb.addKey(bound.up),
      down: kb.addKey(bound.down),
      left: kb.addKey(bound.left),
      right: kb.addKey(bound.right),
      dash: kb.addKey(bound.dash),
    };
    this.dashQueued = false;
    this.keys.dash.on(Phaser.Input.Keyboard.Events.DOWN, this.queueDash, this);
    this.input.mouse?.disableContextMenu();
    this.menu = new TextMenu(this);
    this.picks = new MemoryPicks(this.menu, () => this.changed());
    this.trialCards = 0;
    // 62 루프 2 C: 기억 장 그림 (소품 · 모양·개성 대체 그림)
    loadRunEndArt(this, { memoryTraits: true });
    setMenuSelect((id, key) => this.menu.select(key, id));
    setRitualHost({ command: (c) => this.command(c), state: () => this.ritual() });
    this.events.once('shutdown', () => this.shutdown());
    this.exposeDebug();
    this.launchOverlay();

    const resume = this.resumeAt;
    this.resumeAt = null;
    if (resume) {
      this.playerName = resume.playerName;
      this.redrawing = resume.redrawing;
      this.beginStrokes();
    } else if (this.firstLife && !this.diary.training.offered) this.openTrainingChoice();
    else this.beginName();
  }

  private shutdown(): void {
    this.keys.dash.off(Phaser.Input.Keyboard.Events.DOWN, this.queueDash, this);
    this.menu.close();
    setMenuSelect(null);
    setRitualHost(null);
    this.runner?.destroy();
    this.runner = undefined;
    if (this.scene.isActive(this.overlayKey) || this.scene.isPaused(this.overlayKey)) this.scene.stop(this.overlayKey);
    __system.emit(UI_EVENTS.RITUAL, { phase: null, lives: this.diary.lives } satisfies UiRitual);
    delete (window as unknown as { __lopadSetup?: unknown }).__lopadSetup;
  }

  /** UI 의식 씬이 있으면 그것을, 없으면 시스템 대체 화면을 Setup 위에 띄운다 (계약 §20 — 같은 스냅샷·명령) */
  private launchOverlay(): void {
    const uiKey = (UI_SCENES as Readonly<Record<string, string | undefined>>).RITUAL;
    const forceSys =
      typeof location !== 'undefined' && new URLSearchParams(location.search).get('ritualview') === 'sys';
    const useUi = !forceSys && Boolean(uiKey && __system.rendererRegistered() && this.scene.manager.keys[uiKey]);
    this.overlayKey = useUi ? uiKey! : SCENES.RITUAL_VIEW;
    if (!this.scene.isActive(this.overlayKey)) this.scene.launch(this.overlayKey);
    this.scene.bringToTop(this.overlayKey);
  }

  // ─── 흐름 ───

  /** 상태가 바뀜 → UI 에 알린다 */
  private changed(): void {
    __system.emit(UI_EVENTS.RITUAL, this.ritual());
  }

  /**
   * 61 단계 6 (P14 §1 · 계약 UI §19): 첫 생 시작 — '수련장부터 / 바로 벽 밖으로' (메뉴 'trainingChoice', 한 번만 묻는다).
   * 62 P1-20: 카드 그림 = 입구 그림(`doorKey`, 받으면 같은 메뉴를 다시 그린다)
   */
  private openTrainingChoice(): void {
    this.phase = 'choice';
    const runDoor = doorFor(this, 'waste', 'birth');
    const doors = [trainingDoorName(false), runDoor].filter((n): n is string => Boolean(n));
    const open = () => {
      if (this.phase !== 'choice' || !this.scene.isActive()) return;
      const lines = [
        {
          key: '1',
          label: trainingText('choice.training'),
          detail: trainingText('choice.trainingHint'),
          enabled: true,
          doorKey: paintLoaded(this, trainingDoorName(false)),
        },
        {
          key: '2',
          label: trainingText('choice.run'),
          detail: trainingText('choice.runHint'),
          enabled: true,
          doorKey: runDoor ? paintLoaded(this, runDoor) : undefined,
        },
      ];
      this.menu.open('trainingChoice', trainingText('choice.prompt'), lines, (key) => {
        this.diary = updateDiary((d) => ({ ...d, training: recordOffered(d.training) }));
        this.menu.close();
        if (key === '1' && uiCommands.startTraining() === 'ok') return;
        this.beginName();
      });
    };
    open();
    loadPaint(this, doors, open);
    this.changed();
  }

  /** 첫 생 = 이름 칸 · 두 번째 생부터 = 이름 덧쓰기 한 화면 */
  private beginName(): void {
    this.menu.close();
    this.phase = this.firstLife ? 'name' : 'rewrite';
    this.changed();
  }

  /** 명령 (계약 §20 uiCommands.ritual.*) — 단계가 맞지 않으면 false */
  private command(c: UiRitualCommand): boolean {
    switch (c.kind) {
      case 'submitName':
        return this.submitName(c.name, false);
      case 'redraw':
        return this.submitName(c.name, true);
      case 'stroke':
        return this.stroke(c.points);
      case 'next':
        return this.next();
      case 'skip':
        return this.skipTrial();
      case 'back':
        return this.back();
      case 'openMeta':
        return this.openMeta();
    }
  }

  private submitName(raw: string, redraw: boolean): boolean {
    if (this.phase === 'name' && !redraw) {
      this.playerName = cleanName(raw, NAME_MAX);
      this.beginStrokes();
      return true;
    }
    if (this.phase !== 'rewrite') return false;
    this.playerName = cleanName(raw, NAME_MAX);
    const N = NARRATIVE_STORY.nameSmudge;
    this.smudgeResult = this.playerName === this.diary.lastName.trim() ? N.resultSame : N.resultChanged;
    const remembered = redraw ? null : rememberedWeapon(this.diary, WEAPONS);
    if (remembered) {
      this.weaponId = remembered;
      this.weaponSource = 'remembered';
      this.scar = undefined;
      this.decideFate();
      return true;
    }
    // 덧쓰고 획을 다시 긋는다 (지난 생 기록이 없으면 획으로)
    this.redrawing = true;
    this.beginStrokes();
    return true;
  }

  private beginStrokes(): void {
    this.menu.close();
    this.phase = 'strokes';
    this.strokes = [];
    this.changed();
  }

  /** 한 획 판정 (UI 가 모은 점 — 논리 px). 3획째면 무기를 정하고 낙관 시간 뒤 회피 시험(첫 생) 또는 운명 */
  private stroke(points: readonly UiRitualPoint[]): boolean {
    if (this.phase !== 'strokes') return false;
    const s: Stroke = points
      .filter((p) => Number.isFinite(p.x) && Number.isFinite(p.y) && Number.isFinite(p.t))
      .map((p) => ({ x: p.x, y: p.y, t: p.t }));
    if (s.length < PERSONALITY.strokes.minPoints) return false;
    this.strokes.push(s);
    const index = this.strokes.length - 1;
    const judged: UiRitualStrokeJudged = { index, weaponHint: leaningWeapon(this.strokes, WEAPONS, PERSONALITY) };
    __system.emit(UI_EVENTS.RITUAL_STROKE_JUDGED, judged);
    if (this.strokes.length >= PERSONALITY.strokes.count) this.seal();
    else this.changed();
    return true;
  }

  /** 3획 끝: 무기는 지금 3획만으로 (49라운드 2절) → 낙관 연출 시간 → 다음 단계 */
  private seal(): void {
    this.phase = 'seal';
    const f = strokeFeatures(this.strokes, PERSONALITY);
    this.weaponId = chooseWeapon(f, WEAPONS, PERSONALITY).id;
    this.weaponSource = 'strokes';
    this.scar = encodeScar(this.strokes, BACK.SCAR_RECT);
    this.preloadLook();
    this.changed();
    this.time.delayedCall(RITUAL.SEAL_MS, () => {
      if (this.phase !== 'seal') return;
      if (this.firstLife && !this.redrawing) this.beginTrial();
      else this.decideFate();
    });
  }

  private preloadLook(): void {
    const id = this.weaponId;
    if (!id) return;
    loadBaseLook(this, id, (key) => {
      if (this.weaponId !== id) return;
      this.lookKey = key;
      if (this.phase === 'fate') this.changed();
    });
  }

  /** 회피 시험 (첫 생): 탄생 전장을 세우고 카메라를 맞춘다 */
  private beginTrial(): void {
    if (this.runner || !this.scene.isActive()) return;
    this.phase = 'trial';
    const T = RITUAL_DATA.trial;
    this.runner = new BirthTrialRunner(
      this,
      T,
      () => this.changed(),
      (hits) => this.onTrialDone(hits),
    );
    const c = this.runner.center;
    this.cameras.main.setOrigin(0.5).setZoom(worldZoom(T.zoom)).centerOn(c.x, c.y);
    this.runner.start(this.time.now);
    this.changed();
  }

  private onTrialDone(hits: number): void {
    if (this.trialHits !== null) return;
    this.trialHits = hits;
    this.changed();
    this.time.delayedCall(RITUAL.TRIAL_RESULT_MS, () => this.decideFate());
  }

  private skipTrial(): boolean {
    if (this.phase !== 'trial' || this.trialHits !== null) return false;
    this.trialSkipped = true;
    this.decideFate();
    return true;
  }

  private next(): boolean {
    if (this.phase === 'trial' && this.runner) return this.runner.skipCard(this.time.now);
    // 62 루프 2 C: 모양·소품을 고르는 동안은 넘기지 않는다 (startData 는 고른 뒤에 생긴다)
    if (this.phase === 'fate' && this.startData && !this.picks.picking) {
      this.fateTimer?.remove();
      this.startGame();
      return true;
    }
    return false;
  }

  /** Esc — 한 단계 앞으로: 3획 → 이름(덧쓰기) · 회피 시험 → 씬을 다시 열어 3획부터 */
  private back(): boolean {
    if (this.phase === 'strokes') {
      this.strokes = [];
      this.redrawing = false;
      this.beginName();
      return true;
    }
    if (this.phase === 'trial' && this.trialHits === null) {
      this.scene.restart({ back: 'strokes', playerName: this.playerName, redrawing: this.redrawing });
      return true;
    }
    return false;
  }

  /** 두 번째 생부터: 일기장 '기억' 장 (P0-3 — 첫 생에는 열지 않는다 · 62 루프 2 C MemoryPicks). 닫기 '0' → 덧쓰기 화면 */
  private openMeta(): boolean {
    if (this.phase !== 'rewrite' && this.phase !== 'meta') return false;
    this.phase = 'meta';
    this.picks.openBook(() => {
      this.phase = 'rewrite';
      this.changed();
    });
    this.changed();
    return true;
  }

  /** 운명 공개 → (모양·소품 고르기) → 잠시 뒤(또는 ritual.next) Game (62 루프 2 C: 첫 개성 카드 수·소품·모양을 시작 데이터로) */
  private decideFate(): void {
    if (this.phase === 'fate' || !this.scene.isActive()) return;
    if (!this.weaponId) {
      const f = strokeFeatures(this.strokes, PERSONALITY);
      this.weaponId = chooseWeapon(f, WEAPONS, PERSONALITY).id;
    }
    this.phase = 'fate';
    this.runner?.forceEnd();
    const id = this.weaponId;
    // 62 루프 2 C (P1-5): 회피 시험 등급 → 첫 개성 발현 카드 수 (감각 삭제 — S·A 4장 / B·C 3장)
    const T = RUN_END.trial;
    this.trialCards =
      this.trialHits !== null && !this.trialSkipped
        ? T.firstTraitCards[gradeHits(this.trialHits, RITUAL_DATA.trial).grade]
        : this.firstLife && !this.redrawing
          ? T.skipped
          : 0;
    // 62 P0-1: UI 에 획 특징 수치를 보내지 않는다 (무기 이름·id 만)
    __system.emit(UI_EVENTS.FATE_DECIDED, { weaponName: WEAPONS[id].name, weapon: id });
    EventBus.emit(Events.FATE_DECIDED, { weapon: id });
    // 61라운드 P7·P8: 일기장에 이 생을 적는다 (다시 태어난 수·이름)
    const livesBefore = this.diary.lives;
    updateDiary((d) => recordBirth(d, this.playerName));
    firstSteps.begin(livesBefore);
    if (!this.lookKey) this.preloadLook();
    this.changed();
    // 62 루프 2 C (P1-8): 운명 공개 뒤 손이 기억한 모양 → 지닐 소품 (고르는 동안 운명 시계는 멈춘다)
    this.picks.begin(id, () => {
      if (this.phase !== 'fate' || !this.scene.isActive()) return;
      this.startData = {
        mode: 'new',
        weapon: id,
        playerName: this.playerName,
        traitCards: this.trialCards,
        keepsake: this.picks.keepsake,
        aspect: this.picks.aspect,
      };
      this.changed();
      this.fateTimer = this.time.delayedCall(RITUAL.FATE_MS, () => this.startGame());
    });
  }

  private startGame(): void {
    const data = this.startData;
    if (!data || !this.scene.isActive()) return;
    gameState.queueScar(this.scar ?? null); // 다음 startRun(새 런)이 가져간다
    this.scene.start(SCENES.GAME, data);
  }

  update(time: number, delta: number): void {
    if (this.phase !== 'trial' || !this.runner) return;
    const mx = (this.keys.right.isDown ? 1 : 0) - (this.keys.left.isDown ? 1 : 0);
    const my = (this.keys.down.isDown ? 1 : 0) - (this.keys.up.isDown ? 1 : 0);
    const dash = this.dashQueued;
    this.dashQueued = false;
    this.runner.update(time, delta, { mx, my, dash });
  }

  private queueDash(): void {
    if (this.phase === 'trial') this.dashQueued = true;
  }

  // ─── 계약 상태 (§20 UiRitual) ───

  /** 두 번째 생 첫 장 문장 (번진 이름 · 처음 돌아왔을 때 한 번 · 세 번째 생부터 겹 수 · 덧쓰기 안내) */
  private smudgeLines(): string[] {
    const N = NARRATIVE_STORY.nameSmudge;
    const lines: string[] = [];
    if (this.diary.lives === 1) lines.push(N.returnFirst);
    lines.push(N.diaryOpen);
    if (this.diary.deaths >= 2) lines.push(fill(N.layers, { lives: koreanCount(this.diary.deaths) }));
    lines.push(N.prompt);
    return lines;
  }

  private ritual(): UiRitual {
    const R = RITUAL_DATA;
    const base: UiRitual = { phase: null, lives: this.diary.lives };
    switch (this.phase) {
      case 'choice':
        return base;
      case 'name':
        return {
          ...base,
          phase: 'name',
          lines: [R.lines.name],
          name: { value: this.playerName, maxLen: NAME_MAX },
          hint: R.hints.name,
        };
      case 'rewrite':
      case 'meta': {
        const meta = metaStore.read();
        // 62 루프 2 C: 귀퉁이 '기억' — 지금 떠올릴 수 있는 것이 있나 (몸의 기억 포함)
        const corner = { ...metaCorner(meta, META_CONFIG), canBuy: canUnlockAny(meta, META_CONFIG) };
        return {
          ...base,
          phase: 'rewrite',
          lines: this.smudgeLines(),
          name: { value: this.playerName || this.diary.lastName, lastName: this.diary.lastName, maxLen: NAME_MAX },
          redraw: { ...R.redraw },
          meta: { ...corner, label: R.meta.label, key: R.meta.key },
          hint: fill(R.hints.rewrite, { redrawKey: R.redraw.key }),
        };
      }
      case 'strokes':
      case 'seal':
        return {
          ...base,
          phase: 'strokes',
          lines: [...(this.smudgeResult ? [this.smudgeResult] : []), R.lines.strokes],
          strokes: {
            done: this.strokes.length,
            total: 3,
            lastWeapon: this.phase === 'seal' ? this.weaponId : undefined,
            legend: legendOf(R, WEAPONS),
          },
          hint: R.hints.strokes,
        };
      case 'trial': {
        const st = this.runner?.status();
        return {
          ...base,
          phase: 'trial',
          lines: [st?.state === 'clear' || st?.state === 'done' ? R.lines.trialEnd : R.lines.trialIntro],
          trial: {
            tasks: R.trial.tasks.map((t, i) => {
              const r = st?.tasks[i];
              return {
                id: t.id,
                label: t.label,
                done: Boolean(r?.done),
                ...(t.verb ? { verb: t.verb } : {}),
                ...(r?.done ? { clean: r.hits === 0 } : {}),
              };
            }),
            skippable: true,
            current: st ? R.trial.tasks[Math.min(st.index, R.trial.tasks.length - 1)].id : undefined,
            state: st?.state ?? 'card',
          },
          hint: `${R.hints.trial} · ${R.hints.trialSkip}`,
        };
      }
      case 'fate': {
        const id = this.weaponId!;
        const gift =
          this.trialHits !== null && !this.trialSkipped
            ? R.gift[gradeHits(this.trialHits, R.trial).grade]
            : this.firstLife && !this.redrawing
              ? R.gift.skipped
              : undefined;
        return {
          ...base,
          phase: 'fate',
          lines: [this.playerName || '―'],
          fate: {
            weapon: id,
            weaponName: WEAPONS[id].name,
            line: voiceLine(id, 'pickup'),
            ...(this.lookKey ? { lookKey: this.lookKey } : {}),
            why: whyOf(R, id, this.weaponSource),
            ...(gift ? { gift } : {}),
            ...(this.weaponSource === 'remembered' ? { remembered: true } : {}),
          },
          // 62 루프 2 C: 회피 시험 결과 = 첫 개성 발현 카드 수 · 운명 공개 뒤 모양·소품 고르기
          ...(this.trialCards > 0 ? { giftNote: fill(RUN_END.trial.giftNote, { n: this.trialCards }) } : {}),
          memory: this.picks.state(),
          hint: R.hints.fate,
        };
      }
    }
  }

  // ─── 디버그 ───

  /** 검증 훅 (?debug=1): 단계·의식 상태·회피 시험 + 자동 입력. 게임 로직이 아니다 */
  private exposeDebug(): void {
    if (typeof location === 'undefined' || !new URLSearchParams(location.search).has('debug')) return;
    const api = Object.assign(
      () => ({
        phase: this.phase,
        overlay: this.overlayKey,
        ritual: this.ritual(),
        strokes: this.strokes.length,
        trial: this.runner?.snapshot() ?? null,
        trialHits: this.trialHits,
        trialSkipped: this.trialSkipped,
        camera: { zoom: this.cameras.main.zoom },
        startData: this.startData ?? null,
        weapon: this.weaponId ?? null,
        weaponSource: this.weaponSource,
        scar: this.scar ?? null,
        firstLife: this.firstLife,
        diary: this.diary,
      }),
      {
        /** 계약 스냅샷 (UI 가 보는 것 — ritual · meta) */
        snapshot: () => uiCommands.getUiSnapshot(),
        /** 62 루프 2 C: 열린 메뉴 (기억 장·모양·소품 고르기) */
        menu: () => this.menu.menu,
        /** 계약 명령 그대로 (uiCommands.select) */
        select: (id: UiMenuId, key: string) => uiCommands.select(id, key),
        /** 계약 명령 그대로 (UI 와 같은 길) */
        command: (c: UiRitualCommand) => this.command(c),
        /** 이름 단계를 건너뛰고 획 단계로 (첫 생 이름 · 두 번째 생은 redraw) */
        skipToStrokes: (name = 'debug') => {
          if (this.phase === 'choice') this.beginName();
          if (this.phase === 'name') this.submitName(name, false);
          else if (this.phase === 'rewrite') this.submitName(name, true);
          return this.phase;
        },
        /** 3획 자동 입력 (계약 ritual.stroke 와 같은 길). preset: fast · slow · round */
        autoStrokes: (preset: AutoPreset = 'fast') => {
          if (this.phase !== 'strokes') return false;
          for (const s of autoStrokePoints(preset)) this.stroke(s);
          return true;
        },
        /** 회피 시험을 바로 끝낸다 — 과제마다 hitsEach 대 맞은 것으로 (기본 0 = S) */
        skipTrial: (hitsEach = 0) => {
          if (this.phase === 'seal') this.beginTrial();
          if (!this.runner || this.trialHits !== null) return false;
          this.runner.forceEnd(hitsEach);
          return true;
        },
        /** 지금 과제를 바로 끝낸다 (hits 를 주면 그 수로) */
        trialSkipTask: (hits?: number) => this.runner?.skipTask(this.time.now, hits) ?? false,
        /** 무적 (스크린샷용) */
        trialGod: (on = true) => {
          if (!this.runner) return false;
          this.runner.god = on;
          return true;
        },
        /** 운명 공개 시계 멈춤 (스크린샷용) */
        holdFate: () => {
          this.fateTimer?.remove();
          return this.phase === 'fate';
        },
      },
    );
    (window as unknown as { __lopadSetup: unknown }).__lopadSetup = api;
  }
}
