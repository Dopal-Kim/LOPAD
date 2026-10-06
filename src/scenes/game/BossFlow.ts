/**
 * 61라운드 점검 #5·#6 보스 등장·처치 연출 + 보스 대사 (data/bosses.json `show`·`lines` — 1층 '만취').
 *
 * 등장 (BOSS_STARTED — 보스방 진입, 보스 생성 직후): 보스를 잠재우고(패턴·접촉·피해 없음) 주인공 입력을 잠근 채
 *   카메라가 보스로 → `BOSS_INTRO`(무기 한마디 bossBefore 자리) → 층 등장 자막(floors.<층>.bossIntro) → 등장 대사(lines.intro)
 *   → 카메라 복귀 → 전투(`BOSS_FIGHT`, 보스 깨움).
 * 국면·파훼 대사: 2국면 진입 = lines.phase2 · 3국면 등불 끄기(어둠 시작) = lines.phase3 · 파훼 종류별 첫 1회 = lines.break.<종류>.
 * 처치 (BOSS_DIED): 히트스톱 · 섬광 · 흔들림 → 슬로모(물리·트윈·죽음 그림) → 쓰러짐 대사(lines.defeat) → `BOSS_FALLEN`
 *   (무기 한마디 bossKill 자리) → 보상 메뉴 (방 상태 머신의 층 보상을 `after` 로 미뤄 두었다가 이때 연다).
 * `show` 가 없는 보스·`?nobossintro`·시험장은 연출 없이 기존처럼 바로 전투·보상.
 * 61 E (아트 2): 등장 동작 재생은 `BossIntroArt`(걸어 들어옴·건배·포효), 결정타·쓰러짐 파편·방 불 끄기는 `BossFinale`.
 */
import { BOSS_FX } from '../../core/Constants';
import {
  EventBus,
  Events,
  type BossBreakPayload,
  type BossFallenPayload,
  type BossIntroPayload,
  type BossPhasePayload,
  type BossScreenPayload,
  type BossSpeechPayload,
} from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { BOSSES, STORY } from '../../data';
import type { BossLines } from '../../data/bossShowTypes';
import type { BossDef } from '../../data/types';
import type { Boss } from '../../objects/Boss';
import type { EntityVisual } from '../../objects/EntityVisual';
import type { Mob } from '../../objects/Mob';
import {
  StepClock,
  bossLinesOf,
  defeatSteps,
  introSteps,
  speechText,
  type DefeatStep,
  type IntroStep,
} from '../../systems/boss/bossShow';
import { floorText } from '../../systems/story';
import type { Game } from '../Game';
import { BossFinale } from './BossFinale';
import { BossIntroArt } from './BossIntroArt';
import { urlParams } from './shared';

type Mode = 'idle' | 'intro' | 'fight' | 'defeat' | 'done';

/** 연출 동안 매 프레임 주인공 무적을 이만큼 앞으로 (ms) */
const INVULN_PAD_MS = 200;

export class BossFlow {
  private mode: Mode = 'idle';
  private id = '';
  private def: BossDef | null = null;
  /** 대사 (data/story.json `linesKey`) */
  private lines: BossLines | undefined;
  private boss: Boss | null = null;
  private visual: EntityVisual | null = null;
  /**
   * 연출 경과 ms — 프레임 delta 누적 (실시간이 아니라 애니·트윈과 같은 박자: 프레임이 떨어져도 대사·쓰러짐 그림이 어긋나지 않는다)
   */
  private elapsed = 0;
  private intro: StepClock<IntroStep> | null = null;
  private defeat: StepClock<DefeatStep> | null = null;
  /** 보스가 쓰러진 자리 (카메라 초점) */
  private fallAt = { x: 0, y: 0 };
  private finisher = false;
  /** 연출이 끝나면 열 보상 (방 상태 머신 onStageCleared) */
  private pending: (() => void) | null = null;
  /** 이 노드에서 한 대사 키 (디버그) — 파훼·국면 '그 런 첫 1회'는 gameState.narrative.once */
  private readonly said = new Set<string>();
  /** 슬로모 전 값 (끝나면 되돌린다) */
  private slow: { world: number; tweens: number } | null = null;
  /** 디버그 */
  readonly log: { t: number; e: string }[] = [];
  /** 61 E 등장 동작 (등장 시트가 있을 때) · 결정타·쓰러짐·불 끄기 */
  private introArt: BossIntroArt | null = null;
  private readonly finale: BossFinale;

  private readonly subs: [string, (p: never) => void][] = [
    [Events.BOSS_STARTED, (p: { boss: string }) => this.onStarted(p)],
    [Events.BOSS_DIED, (p: { id: string }) => this.onDied(p)],
    [Events.BOSS_PHASE, (p: BossPhasePayload) => this.onPhase(p)],
    [Events.BOSS_BREAK, (p: BossBreakPayload) => this.onBreak(p)],
    [Events.BOSS_SCREEN, (p: BossScreenPayload) => this.onScreen(p)],
  ];

  constructor(private readonly g: Game) {
    this.finale = new BossFinale(g);
    for (const [e, fn] of this.subs) EventBus.on(e, fn, this);
  }

  /** 61라운드 계약 §17: 이번 보스 등장 연출 길이 ms (0 = 연출 없음 — BOSS_STARTED 처리기에서 정해진다) */
  introMs = 0;

  /** 이번 처치가 결정타였는지 (BOSS_BREAK finisher) */
  get finished(): boolean {
    return this.finisher;
  }

  /** 지금 싸우는 보스 (없으면 null) */
  get current(): Boss | null {
    return this.boss?.active ? this.boss : null;
  }

  /** 등장·처치 연출 동안 주인공 입력 잠금 */
  get inputLocked(): boolean {
    return this.mode === 'intro' || this.mode === 'defeat';
  }

  /** 연출 중 (다른 메뉴 — 개성 3지선다 — 를 미룬다) */
  get busy(): boolean {
    return this.inputLocked;
  }

  /** 방 상태 머신의 보스 보상: 처치 연출 중이면 끝날 때까지 미룬다 */
  after(fn: () => void): void {
    if (this.mode === 'defeat') this.pending = fn;
    else fn();
  }

  private mark(e: string): void {
    this.log.push({ t: Math.round(this.elapsed), e });
  }

  // --- 등장 ---

  private onStarted(p: { boss: string }): void {
    const def = BOSSES[p.boss] ?? null;
    this.id = p.boss;
    this.def = def;
    this.lines = bossLinesOf(STORY, def?.linesKey);
    this.boss = this.findBoss();
    this.visual = this.boss?.visual ?? null;
    const show = def?.show;
    if (this.boss && show) this.boss.visual.corpseHoldMs = show.defeat.rewardAtMs + BOSS_FX.CORPSE_EXTRA_HOLD_MS;
    this.elapsed = 0;
    this.log.length = 0;
    this.finisher = false;
    this.introMs = 0;
    // 61 단계 6 수련장 '만취 그림자': 등장 연출·층 자막·대사 없이 바로 (그림자는 말하지 않는다 — 스토리 팩)
    if (this.g.training) {
      this.mode = 'fight';
      EventBus.emit(Events.BOSS_FIGHT, { id: this.id });
      return;
    }
    if (!def || !show || !this.boss || this.g.lab || urlParams().has('nobossintro')) {
      // 연출 없음: 기존처럼 층 등장 자막 + 등장 대사, 바로 전투
      this.mode = 'fight';
      this.g.ui.story('boss', floorText(gameState.stageId)?.bossIntro ?? '');
      this.speak('intro');
      EventBus.emit(Events.BOSS_FIGHT, { id: this.id });
      return;
    }
    this.mode = 'intro';
    this.introMs = show.intro.fightAtMs;
    this.boss.setDormant(true);
    this.g.player.body.setVelocity(0, 0);
    this.introArt = BossIntroArt.create(this.g, this.boss, show.intro);
    this.intro = new StepClock(introSteps(show.intro));
    EventBus.emit(Events.BOSS_INTRO, {
      id: this.id,
      floor: gameState.floorReached,
      durationMs: show.intro.fightAtMs,
      lineGapMs: show.intro.floorLineAtMs,
    } satisfies BossIntroPayload);
  }

  private runIntro(step: IntroStep, now: number): void {
    const I = this.def!.show!.intro;
    this.mark(step);
    switch (step) {
      case 'pan':
        if (this.boss?.active) {
          // 61 E: 걸어 들어오는 동안에도 멈출 자리(시작 자리)를 비춘다
          const at = this.introArt?.target ?? this.boss;
          this.g.cam.setFocus({ x: at.x, y: at.y - this.boss.body.height }, I.panMs);
        }
        break;
      case 'floorLine':
        this.g.ui.story('boss', floorText(gameState.stageId)?.bossIntro ?? '');
        break;
      case 'speech':
        this.speak('intro');
        break;
      case 'return':
        this.g.cam.setFocus(null, I.returnMs);
        break;
      case 'fight':
        this.mode = 'fight';
        this.introArt?.finish();
        this.introArt = null;
        this.boss?.wake(now);
        EventBus.emit(Events.BOSS_FIGHT, { id: this.id });
        break;
    }
  }

  // --- 대사 ---

  /** 보스 대사 한 줄 (계약 STORY kind 'speech' + speaker). once = 그 런 첫 1회 (gameState.narrative) */
  private speak(key: string, once = false): void {
    if (this.g.training) return;
    const L = this.lines;
    const text = speechText(L, key);
    if (!L || !text) return;
    if (once && !gameState.narrative.once(`${this.def?.linesKey ?? this.id}.${key}`)) return;
    this.said.add(key);
    this.g.ui.speech(L.speaker, text);
    EventBus.emit(Events.BOSS_SPEECH, { id: this.id, key, speaker: L.speaker, text } satisfies BossSpeechPayload);
  }

  private onPhase(p: BossPhasePayload): void {
    if (this.mode !== 'fight') return;
    if (p.phase === 2) this.speak('phase2', true);
  }

  /** 3국면 등불 끄기 확정 = 어둠 시작 */
  private onScreen(p: BossScreenPayload): void {
    if (this.mode === 'fight' && p.effect === 'dark' && p.on) this.speak('phase3', true);
  }

  private onBreak(p: BossBreakPayload): void {
    if (p.kind === 'finisher') {
      this.finisher = true;
      if (this.mode === 'defeat') this.finale.onFinisher();
      return;
    }
    if (this.mode === 'fight' && p.distinct) this.speak(`break.${p.kind}`, true);
  }

  // --- 처치 ---

  private onDied(p: { id: string }): void {
    const show = this.def?.show;
    if (!show || p.id !== this.id || this.mode === 'defeat' || this.mode === 'done') return;
    const b = this.boss;
    this.fallAt = b ? { x: b.x, y: b.y - b.body.height } : { x: this.g.player.x, y: this.g.player.y };
    this.mode = 'defeat';
    this.elapsed = 0;
    this.defeat = new StepClock(defeatSteps(show.defeat));
    this.g.player.body.setVelocity(0, 0);
    // 일격 순간은 지금 바로 (무기 히트스톱보다 먼저)
    this.step(this.g.time.now);
  }

  private runDefeat(step: DefeatStep, now: number): void {
    const D = this.def!.show!.defeat;
    const g = this.g;
    this.mark(step);
    switch (step) {
      case 'hit':
        this.finale.onDefeat(this.boss?.active ? this.boss : null, D.snuffAtMs);
        g.hitStop.request(now, D.hitstopMs, true);
        g.screenFx.flash(BOSS_FX.DEFEAT_FLASH, D.flashMs, D.flashAlpha);
        g.shake.add(now, D.shakePx, D.shakeMs);
        g.cam.setFocus(this.fallAt, D.panMs);
        break;
      case 'slowStart':
        this.setSlow(D.slowScale);
        break;
      case 'slowEnd':
        this.setSlow(1);
        break;
      case 'speech':
        this.speak('defeat');
        break;
      case 'fallen':
        EventBus.emit(Events.BOSS_FALLEN, {
          id: this.id,
          finisher: this.finisher,
          rewardInMs: Math.max(0, D.rewardAtMs - D.fallenAtMs),
        } satisfies BossFallenPayload);
        break;
      case 'reward': {
        this.setSlow(1);
        this.finale.onReward();
        this.mode = 'done';
        g.cam.setFocus(null, D.panMs);
        const fn = this.pending;
        this.pending = null;
        fn?.();
        break;
      }
    }
  }

  /** 슬로모: 물리(Arcade timeScale 은 클수록 느림)·씬 트윈·죽음 그림 애니. scale 1 = 되돌림 */
  private setSlow(scale: number): void {
    const g = this.g;
    const world = g.physics.world;
    const corpse = this.visual?.corpse ?? null;
    if (scale < 1) {
      if (this.slow) return;
      this.slow = { world: world?.timeScale ?? 1, tweens: g.tweens.timeScale };
      if (world) world.timeScale = this.slow.world / scale;
      g.tweens.timeScale = this.slow.tweens * scale;
      if (corpse?.active) corpse.anims.timeScale = scale;
      return;
    }
    const s = this.slow;
    if (!s) return;
    this.slow = null;
    if (world) world.timeScale = s.world;
    g.tweens.timeScale = s.tweens;
    if (corpse?.active) corpse.anims.timeScale = 1;
  }

  // --- 매 프레임 (히트스톱 중에도 — 시간표는 실시간) ---

  update(now: number, delta: number): void {
    if (this.mode !== 'intro' && this.mode !== 'defeat') return;
    this.elapsed += delta;
    // 연출 동안 주인공 무적 (남은 불 웅덩이·잔여 탄) — 매 프레임 조금씩 늘린다
    this.g.player.grantInvulnerable(now + INVULN_PAD_MS);
    this.step(now);
  }

  private step(now: number): void {
    const t = this.elapsed;
    if (this.mode === 'intro' && this.intro) {
      this.introArt?.update(t, now);
      for (const s of this.intro.due(t)) this.runIntro(s, now);
    } else if (this.mode === 'defeat' && this.defeat) {
      for (const s of this.defeat.due(t)) this.runDefeat(s, now);
      this.finale.update(t);
    }
  }

  private findBoss(): Boss | null {
    for (const m of this.g.mobs.getChildren() as Mob[]) if (m.active && m.isBoss) return m as Boss;
    return null;
  }

  summary(): Record<string, unknown> {
    return {
      mode: this.mode,
      id: this.id,
      elapsedMs: Math.round(this.elapsed),
      finisher: this.finisher,
      pendingReward: this.pending !== null,
      slow: this.slow !== null,
      said: [...this.said],
      log: [...this.log],
      introArt: this.introArt?.summary() ?? null,
      finale: this.finale.summary(),
    };
  }

  destroy(): void {
    for (const [e, fn] of this.subs) EventBus.off(e, fn, this);
    this.setSlow(1);
    this.finale.destroy();
    this.introArt = null;
    this.pending = null;
    this.boss = null;
    this.visual = null;
  }
}
