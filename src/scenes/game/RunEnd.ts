/**
 * 62 루프 2 시스템 C (P16 §2·§3 · 점검 P1-6·P1-7) 생의 끝 흐름 (씬 쪽):
 * - 층 끝: 마지막 층(runEnd.floorEnd.lastFloor) 군주 처치 → '군주의 유품' 한 번(3택) → (게이지 눈금이면) 개성 발현 최대 growthMenus 장 →
 *   delayMs 뒤 '층 끝' 결산(`FLOOR_END` → RUN_ENDED cleared + floorEnd·summary). 출구를 놓지 않는다 — 다음 층 진입 차단.
 * - 죽음: 0.6초 0.25배 슬로모(물리·트윈·애니) → 먹 번짐(`InkSmear`, 시스템 그림) → 결산(RUN_ENDED + summary).
 * - 출구 방향 (`UiExitHint`) · 결산 만들기(처치자 초상 · 지나온 곳 · 빌드 아이콘 · 다음 기억).
 * 씬이 끝나면 스스로 정리한다(트윈 배율 되돌림).
 */
import Phaser from 'phaser';
import { GAME, TILE } from '../../core/Constants';
import { gameState } from '../../core/GameState';
import { RUN_END } from '../../data/runEnd';
import { NARRATIVE } from '../../data/narrative';
import {
  UI_EVENTS,
  __system,
  type UiDeathFx,
  type UiExitHint,
  type UiFloorEnd,
  type UiKiller,
  type UiRunSummary,
} from '../../contract/ui';
import type { Mob } from '../../objects/Mob';
import { InkSmear } from '../../systems/fx/inkSmear';
import { worldToLogicalScreen } from '../../systems/display';
import { runLogRecorder } from '../../systems/runlog/runLogRecorder';
import { buildIcons, floorEndOf, killerOf, runSummaryOf, statsOf } from '../../systems/runEnd/summary';
import { ownedRelics } from '../../systems/relics';
import { iconLoaded, traitIconKey } from '../../systems/growth/traitArt';
import { keepsakeIconKey, nextUnlock } from '../../systems/memory/memory';
import { META_CONFIG, metaStore } from '../../systems/meta';
import { invalidateMetaSummary } from '../../contract/metaSummary';
import { spriteLibrary } from '../../systems/sprites/sprites';
import { frameAt } from '../../systems/sprites/sheetFrames';
import { floorText } from '../../systems/story';
import type { Game } from '../Game';
import { BOSS_PORTRAIT, loadRunEndArt, portraitKey } from './RunEndArt';

type FloorPhase = 'idle' | 'relic' | 'growth' | 'wait' | 'done';

export class RunEnd {
  private phase: FloorPhase = 'idle';
  private growthLeft = 0;
  private growthSeen = false;
  private waitUntil = 0;
  private ink: InkSmear | null = null;
  private slowSaved: { world: number; tweens: number } | null = null;
  /** 디버그 */
  readonly log: string[] = [];

  constructor(private readonly g: Game) {
    loadRunEndArt(g);
    g.events.once(Phaser.Scenes.Events.SHUTDOWN, () => this.destroy());
  }

  /** 이 층 군주를 쓰러뜨리면 결산으로 끝나는가 (시험장·수련장 제외) */
  get finalFloor(): boolean {
    return !this.g.lab && gameState.floorReached >= RUN_END.floorEnd.lastFloor;
  }

  /** GrowthFlow: 결산 흐름이 개성 발현을 막는 중 (군주의 유품 뒤 최대 장 수를 넘었다·결산 기다림) */
  holdsGrowth(): boolean {
    return this.phase === 'wait' || this.phase === 'done' || (this.phase === 'growth' && this.growthLeft <= 0);
  }

  get floorPhase(): FloorPhase {
    return this.phase;
  }

  // --- 층 끝 (P1-6) ---

  /** 군주 처치 연출 뒤 (Progression.beginStageReward): 군주의 유품 → 개성 발현 → 결산 */
  beginFloorEnd(): void {
    const g = this.g;
    if (this.phase !== 'idle') return;
    this.phase = 'relic';
    this.log.push('floorEnd:relic');
    const down = RUN_END.floorEnd.bossDown[gameState.stageId];
    if (down) g.ui.story('notice', down);
    // 60라운드 (h) 파훼 n ≥ 4: 군주의 유품 희귀 이상 보장
    g.buildMenus.openPassiveMenu('boss', { rarities: g.bundle?.breaks.bossRarities() }, () => this.afterRelic());
  }

  private afterRelic(): void {
    this.phase = 'growth';
    this.growthLeft = RUN_END.floorEnd.growthMenus;
    this.growthSeen = false;
    this.log.push('floorEnd:growth');
  }

  /** 매 프레임 (정지 중에도 — Game.update 가 growth.maybeOpen 옆에서 부른다) */
  update(time: number): void {
    const g = this.g;
    if (this.phase === 'growth') {
      if (g.menu.isOpen) {
        if (g.menu.menu?.id === 'evolve' && !this.growthSeen) {
          this.growthSeen = true;
          this.growthLeft -= 1;
        }
        return;
      }
      this.growthSeen = false;
      // 다음 프레임에 GrowthFlow 가 열 눈금이 남았고 아직 장 수가 남았으면 기다린다
      if (this.growthLeft > 0 && g.growth.pending()) return;
      if (g.build?.awaken.playing) return;
      this.phase = 'wait';
      this.waitUntil = time + RUN_END.floorEnd.delayMs;
      g.ui.story('notice', RUN_END.floorEnd.summary.closing);
      this.log.push('floorEnd:wait');
      return;
    }
    if (this.phase === 'wait' && time >= this.waitUntil && !g.menu.isOpen && !g.build?.awaken.playing) {
      this.phase = 'done';
      this.finishFloor();
    }
  }

  private finishFloor(): void {
    const g = this.g;
    g.player.body.setVelocity(0, 0);
    g.motion.stopLoops();
    g.saveSlot.clear();
    g.progress.settleRun(true);
    const floorEnd = this.floorEnd();
    const summary = this.summary('floorEnd');
    gameState.cleared = true;
    this.log.push('floorEnd:done');
    __system.emit(UI_EVENTS.FLOOR_END, floorEnd);
    g.progress.endRunScene(true, { floorEnd, summary });
  }

  /** 층 끝 결산 (`UiFloorEnd`) */
  floorEnd(): UiFloorEnd {
    const log = runLogRecorder.peek();
    return floorEndOf({
      floor: gameState.floorReached,
      stageId: gameState.stageId,
      floorTitle: floorText(gameState.stageId)?.title ?? gameState.stage.name,
      stats: statsOf(log, gameState.kills),
      build: this.buildIcons(),
      clues: { found: gameState.narrative.cluesRead.size, total: NARRATIVE.props.length },
      soulsGained: gameState.lastSoulGain,
    });
  }

  // --- 죽음 (P1-7) ---

  /** 사망 (Progression.onPlayerDied — 정산 뒤): 슬로모 → 먹 번짐 → onDone(결산). animMs = 쓰러짐 그림 남은 길이 */
  beginDeath(animMs: number, onDone: () => void): void {
    const g = this.g;
    const D = RUN_END.death;
    const totalMs = Math.max(animMs, D.slowMs + D.inkMs + D.holdMs);
    // 히트스톱 중에 죽으면 씬 시계가 멈춘 채라 예약 호출이 오지 않는다 — 먼저 푼다
    g.clearHitStop();
    // Game.update 는 사망 뒤 멈춘다 — HUD 가 마지막 상태(체력 0)를 받게 한 번 더 낸다
    g.ui.emitState();
    this.setSlow(D.slowScale);
    __system.emit(UI_EVENTS.DEATH_STARTED, {
      slowMs: D.slowMs,
      slowScale: D.slowScale,
      inkMs: D.inkMs,
      totalMs,
    } satisfies UiDeathFx);
    this.log.push('death:slow');
    g.time.delayedCall(D.slowMs, () => {
      if (!g.scene.isActive()) return;
      this.setSlow(1);
      const at = worldToLogicalScreen(g.cameras.main, g.player.x, g.player.y);
      this.ink ??= new InkSmear(g);
      this.ink.play(at, D.inkMs, () => g.rng.next());
      this.log.push('death:ink');
    });
    g.time.delayedCall(totalMs, () => {
      if (g.scene.isActive()) onDone();
    });
  }

  /** 슬로모: 물리(Arcade timeScale 은 클수록 느림)·씬 트윈·주인공·적 애니. scale 1 = 되돌림 */
  private setSlow(scale: number): void {
    const g = this.g;
    const world = g.physics.world;
    const anims = this.slowTargets();
    if (scale < 1) {
      if (this.slowSaved) return;
      this.slowSaved = { world: world?.timeScale ?? 1, tweens: g.tweens.timeScale };
      if (world) world.timeScale = this.slowSaved.world / scale;
      g.tweens.timeScale = this.slowSaved.tweens * scale;
      for (const o of anims) o.anims.timeScale = scale;
      return;
    }
    const s = this.slowSaved;
    if (!s) return;
    this.slowSaved = null;
    if (world) world.timeScale = s.world;
    if (g.tweens) g.tweens.timeScale = s.tweens;
    for (const o of anims) o.anims.timeScale = 1;
  }

  /** 슬로모를 걸 개체 (씬이 끝나는 중이면 적 묶음이 이미 없을 수 있다) */
  private slowTargets(): { anims: Phaser.Animations.AnimationState }[] {
    const g = this.g;
    const mobs = g.mobs?.children ? (g.mobs.getChildren() as Mob[]) : [];
    return [g.player, ...mobs].filter((o) => o?.active && o.anims);
  }

  /** 디버그: 먹 번짐 진행 */
  get inkProgress(): number {
    return this.ink?.progress ?? 0;
  }

  // --- 결산 ---

  /** 처치자 (런 로그 사망 원인 + 초상) */
  killer(): UiKiller {
    const k = killerOf(runLogRecorder.peek()?.death?.cause);
    const g = this.g;
    const art = k.kind === 'boss' ? BOSS_PORTRAIT[k.id] : k.kind === 'enemy' ? k.id : null;
    if (art && iconLoaded(portraitKey(art))) return { ...k, portrait: { key: portraitKey(art), frame: 0 } };
    if (k.id) {
      const tex = spriteLibrary.textureKey(k.id, 'idle');
      const def = spriteLibrary.sheet(k.id, 'idle');
      if (tex && def && g.textures.exists(tex)) return { ...k, portrait: { key: tex, frame: frameAt(def, 'down', 0) } };
    }
    return k;
  }

  /** 빌드 아이콘 줄 (갈래·길·개성·유품·모양·소품) */
  buildIcons() {
    const w = gameState.weapon;
    return buildIcons({
      weapon: w.id,
      branchId: w.branchId,
      pathId: w.pathId,
      traits: w.traits,
      relics: ownedRelics(gameState.passives, w.id),
      keepsake: gameState.memory.keepsake,
      aspect: gameState.memory.aspect,
      traitIcon: (wid, id) => (iconLoaded(traitIconKey(wid, id)) ? traitIconKey(wid, id) : undefined),
      memoryIcon: (id) => (iconLoaded(keepsakeIconKey(id)) ? keepsakeIconKey(id) : undefined),
    });
  }

  /** 결산 (`UiRunSummary`) — 정산(settleRun) 뒤에 부른다 */
  summary(cause: UiRunSummary['cause']): UiRunSummary {
    const meta = metaStore.read();
    invalidateMetaSummary();
    const next = nextUnlock(meta, META_CONFIG);
    const seed = gameState.seed;
    let pick = 0;
    for (let i = 0; i < seed.length; i++) pick = (pick * 31 + seed.charCodeAt(i)) >>> 0;
    return runSummaryOf({
      cause,
      log: runLogRecorder.peek(),
      kills: gameState.kills,
      route: gameState.route?.toUi() ?? null,
      build: this.buildIcons(),
      killer: cause === 'death' ? this.killer() : null,
      floor: gameState.floorReached,
      stageId: gameState.stageId,
      pick,
      // 처음으로 떠올릴 수 있게 됐다 = 아직 아무것도 떠올리지 않았고 지금 가장 싼 것을 살 수 있다
      firstReady: !(meta.memory?.unlocked?.length ?? 0) && Boolean(next && next.left === 0),
      souls: { gained: gameState.lastSoulGain, total: meta.souls, next },
    });
  }

  // --- 출구 방향 (P1-6) ---

  /** 출구가 열렸고 노드를 고르는 중이 아니면 출구 방향 (`UiExitHint`) */
  exitHint(): UiExitHint | null {
    const g = this.g;
    if (!gameState.exitOpen || gameState.route?.choosing || g.transitioning || !g.player?.active) return null;
    // 62 루프 2 E: 출구 = 외벽 문 가운데 (문이 없으면 옛 출구 자리)
    const door = g.doors?.exitPoint() ?? null;
    const e = g.layout?.arena?.exit;
    if (!door && !e) return null;
    const wx = door ? door.x : (e!.x + 1) * TILE;
    const wy = door ? door.y : (e!.y + 1) * TILE;
    const cam = g.cameras.main;
    const p = worldToLogicalScreen(cam, wx, wy);
    const W = GAME.WIDTH;
    const H = GAME.HEIGHT;
    const onScreen = p.x >= 0 && p.x <= W && p.y >= 0 && p.y <= H;
    const floorExit = !g.routeMode || g.nodeKind === 'boss';
    return {
      x: Math.max(0, Math.min(W, p.x)),
      y: Math.max(0, Math.min(H, p.y)),
      angle: Math.atan2(p.y - H / 2, p.x - W / 2),
      onScreen,
      distTiles: Math.round((Math.hypot(wx - g.player.x, wy - g.player.y) / TILE) * 10) / 10,
      label: floorExit ? RUN_END.floorEnd.exitArrow : '',
      ...(door && g.doors.exit ? { side: g.doors.exit.side } : {}),
    };
  }

  destroy(): void {
    this.setSlow(1);
    this.ink = null;
  }
}
