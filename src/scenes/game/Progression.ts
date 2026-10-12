/**
 * 런 진행: 처치 → 각성 게이지 적립(61 G — 눈금 메뉴는 growth/GrowthFlow) · 층 보상(62 루프 2 C: 군주의 유품 — 마지막 층이면
 * `RunEnd` 층 끝 결산) · 엔딩(23라운드 2지선다) · 사망(→ `RunEnd` 슬로모·먹 번짐) · 결과 화면 · 런 시작 모드(새 런 / 다음 층 /
 * 이어하기 / 다음 노드) · 세이브. 62 루프 2 C (P1-5): 1층에서 감각·능력치 포인트를 지웠다 — 옛 포인트는 각성 게이지로 흡수.
 */
import { PROTOTYPE, SCENES, SPRITES } from '../../core/Constants';
import { EventBus, Events, type RunEndedPayload, type RunStartedPayload } from '../../core/EventBus';
import { gameState, type EndingChoice } from '../../core/GameState';
import { ECONOMY, STORY } from '../../data';
import { GROWTH } from '../../data/growth';
import { UI_EVENTS, __system, type UiFloorEnd, type UiResult, type UiRunSummary } from '../../contract/ui';
import type { Mob } from '../../objects/Mob';
import { markUnderstood, metaStore, recordRun } from '../../systems/meta';
import { RUN_END } from '../../data/runEnd';
import { memoryDef } from '../../data/memory';
import { keepsakeEffect } from '../../systems/memory/memory';
import { invalidateMetaSummary } from '../../contract/metaSummary';
import type { KillKind } from '../../systems/senses';
import { deathLine, fill, floorText } from '../../systems/story';
import { NARRATIVE, NARRATIVE_STORY } from '../../data/narrative';
import { recordLifeEnd, updateDiary } from '../../systems/narrative/diary';
import { UI_SCENES } from '../../ui';
import type { TileWorld } from '../../world/TileWorld';
import type { Game } from '../Game';
import { continueSave } from './runWeapon';
import { restoreSuspend } from './RunExit';
import { urlParams, type GameInitData } from './shared';

export class Progression {
  /** 디버그: 마지막 결과 화면 페이로드 */
  debugLastResult: unknown = null;

  constructor(private readonly g: Game) {}

  // --- 런 시작 ---

  /** 런 시작 모드 결정: 새 런 / 다음 층 / 세이브 이어하기 / 같은 층 다음 노드(48라운드). 층 시작이면 true */
  prepareRun(init: GameInitData, _senseBonus: number): boolean {
    const g = this.g;
    if (init.mode === 'node') {
      // 같은 층의 다음 노드: 층 상태 유지, 층 시작 이벤트 없음
      if (gameState.route) return false;
      gameState.gotoStage(gameState.stageIndex);
    } else if (init.mode === 'next') {
      gameState.nextStage();
      this.saveIfAllowed();
    } else if (init.mode === 'floor') {
      gameState.gotoStage(init.floor ?? 0);
    } else if (init.mode === 'new') {
      gameState.startRun(pickSeed(), init.weapon, init.playerName ?? '');
      // 62 루프 2 C (P1-5·P1-8): 회피 시험 등급 → 첫 개성 발현 카드 수 · 기억의 소품 · 손이 기억한 모양 (감각 삭제)
      this.applyMemory(init);
      g.saveSlot.clear();
      this.emitRunStarted(false);
    } else {
      const save = continueSave(g.saveSlot);
      if (save) {
        gameState.applySave(save);
        // 62 D (P2-5): 나갈 때 자동 저장이면 그 노드로 (마친 노드면 출구가 열린 채로 — RouteFlow resume)
        if (save.suspend && restoreSuspend(save.suspend)) init.resume = save.suspend.nodeCleared;
      } else {
        gameState.startRun(pickSeed());
        g.saveSlot.clear();
      }
      this.emitRunStarted(Boolean(save));
    }
    EventBus.emit(Events.STAGE_STARTED, { stageIndex: gameState.stageIndex, stageId: gameState.stageId });
    return true;
  }

  /** 61라운드 P9 런 로그 시작 (새 런 · 이어하기) */
  private emitRunStarted(continued: boolean): void {
    EventBus.emit(Events.RUN_STARTED, {
      seed: gameState.seed,
      weapon: gameState.weapon.id,
      stageIndex: gameState.stageIndex,
      continued,
    } satisfies RunStartedPayload);
  }

  /** 스테이지 전환 세이브: 런당 최대 maxSaves 회 */
  private saveIfAllowed(): void {
    if (gameState.savesLeft <= 0) return;
    gameState.savesLeft -= 1;
    this.g.saveSlot.write(gameState.toSave());
    EventBus.emit(Events.STAGE_SAVED, { stageIndex: gameState.stageIndex, savesLeft: gameState.savesLeft });
    this.g.ui.story('notice', fill(STORY.notices.saved, { savesLeft: gameState.savesLeft }));
  }

  // --- 처치 · 개성 ---

  onKill(mob: Mob, kind: KillKind): void {
    const g = this.g;
    gameState.kills += 1;
    // 47라운드: 판돈 종·룰렛 '배수 판' 배율
    const km = g.structures.killMods();
    // 60라운드 엘리트: 처치 개성·전표 ×rewardMult
    const em = g.bundle?.rewardMult(mob) ?? 1;
    // 57라운드: 외상 저주 처치 전표 0
    g.economy.dropLoot(mob, km.goldMult * g.build.killGoldMult() * em);
    // 각성 게이지: 일반 처치 = 적 값 × growth.gain.normalKillMult (보스 그대로) · 공명 ×2 · 연쇄 6 살기 ×2
    const normal = mob.isBoss ? 1 : GROWTH.gain.normalKillMult;
    this.gainGrowth(
      Math.round(
        mob.personalityValue *
          normal *
          (1 + gameState.passives.total('personalityMult')) *
          km.personalityMult *
          g.build.combat.personalityMult() *
          em,
      ),
    );
    // 57라운드 빌드 축: 처치 사건 (연쇄·표식·상흔·취기·저주 궤짝·갈래)
    g.build.combat.onKill(mob, kind);
    const lifesteal = gameState.passives.total('healOnKill');
    if (lifesteal > 0) g.player.heal(lifesteal);
    // 62 루프 2 C (P1-5): 1층에서 감각을 지웠다 — 처치 방식 기록(SENSE_GAINED)을 더 내지 않는다
    // 60라운드 2차 묶음: 엘리트 드롭·접두어 사망 규칙·보스 결정타 (방 상태 머신보다 먼저 — 보스 부하 정리 전)
    g.bundle?.onKill(mob);
    g.director.onMobDied(mob);
  }

  /** 각성 게이지 적립 (61 G — 눈금 메뉴는 GrowthFlow 가 연다) */
  gainGrowth(amount: number): void {
    this.g.growth.gain(amount);
  }

  // --- 엔딩 (23라운드): 황제 처치 직후 2지선다, 선택 전까지 정지 ---

  beginEnding(): void {
    const g = this.g;
    g.setFrozen(true);
    g.player.body.setVelocity(0, 0);
    g.motion.stopLoops();
    const E = STORY.endings;
    const lines = [
      { key: '1', label: E.choice[0], enabled: true, detail: E.destroy },
      { key: '2', label: E.choice[1], enabled: true, detail: E.understand },
    ];
    g.menu.open('ending', E.title, lines, (key) => this.chooseEnding(key === '2' ? 'understand' : 'destroy'));
  }

  /** 선택: 세이브 삭제·정산(공통) → '이해한다' 는 도감에 기록 → 자막 → 결과 화면 */
  private chooseEnding(choice: EndingChoice): void {
    const g = this.g;
    if (gameState.ending) return;
    gameState.ending = choice;
    g.menu.close();
    EventBus.emit(Events.ENDING_CHOSEN, { choice });
    g.saveSlot.clear();
    this.settleRun(true);
    if (choice === 'understand') metaStore.write(markUnderstood(metaStore.read()));
    g.ui.story('death', STORY.endings[choice]);
    g.time.delayedCall(PROTOTYPE.CLEAR_DELAY_MS, () => this.endRunScene(true));
  }

  // --- 시련 · 스테이지 보상(감각 → 능력치 포인트) → 출구·상점 ---

  onTrialCleared(p: { roomId: string }): void {
    this.g.clearedRooms.add(p.roomId);
    this.g.economy.addGold(ECONOMY.gold.trialBonus);
    this.g.ui.story('notice', gameState.bossUnlocked ? STORY.notices.bossUnlocked : STORY.notices.trialClear);
  }

  beginStageReward(room: ReturnType<TileWorld['room']>): void {
    const g = this.g;
    g.economy.addGold(ECONOMY.gold.bossBonus);
    // 62 루프 2 C: 남은 옛 능력치 포인트(보스 파훼 등)는 각성 게이지로
    this.absorbPoints();
    gameState.rewardPending = true;
    // 62 루프 2 C (P1-6): 마지막 층이면 출구 없이 군주의 유품 → 결산 (다음 층 진입 차단)
    if (g.runEnd.finalFloor) {
      gameState.route?.markCleared();
      return g.runEnd.beginFloorEnd();
    }
    const finish = () => {
      gameState.rewardPending = false;
      gameState.route?.markCleared();
      // 62 루프 2 E: 노드 지도 층(보스 노드)은 외벽 문이 층 출구 — 바닥 발판(출구·상점)은 방+복도 층만
      if (!g.route.openFloorExit()) {
        g.world.placeExit(room);
        g.world.placeShop(room);
      }
      gameState.exitOpen = true;
      EventBus.emit(Events.EXIT_OPENED, { stageIndex: gameState.stageIndex });
    };
    this.openPassiveChooser(finish);
  }

  /**
   * 옛 '능력치 포인트' 자리 (보스 파훼 · 사연 · 구조물이 포인트를 줄 때 부른다 — 이름은 호환으로 둔다).
   * 62 루프 2 C (P1-5): 1층에서 능력치를 지웠다 — 쌓인 포인트를 모두 각성 게이지로 흡수하고 바로 onDone (메뉴 없음)
   */
  openStatChooser(onDone: () => void): void {
    this.absorbPoints();
    onDone();
  }

  /** 쌓인 옛 포인트 → 각성 게이지 (한 점 = runEnd.points.growthPerPoint) */
  private absorbPoints(): void {
    const n = gameState.pointsPending;
    if (n <= 0) return;
    gameState.pointsPending = 0;
    const amount = n * RUN_END.points.growthPerPoint;
    this.gainGrowth(amount);
    this.g.ui.story('notice', fill(RUN_END.points.breakNotice, { n: amount }));
  }

  /**
   * 새 런: 이번 생에 지닌 기억 (Setup 이 넘긴 소품·모양·첫 개성 카드 수). 소품 = 시작 전표(접힌 전표) · 첫 피격 무효 · 대쉬 충전 ·
   * 첫 개성 카드 + (먹 묻은 붓) · 모양 = 그 무기 시작 개성 한 장
   */
  private applyMemory(init: GameInitData): void {
    const keepsake = init.keepsake && memoryDef(init.keepsake)?.kind === 'keepsake' ? init.keepsake : null;
    const aspectDef = init.aspect ? memoryDef(init.aspect) : undefined;
    const aspect = aspectDef?.kind === 'aspect' && aspectDef.weapon === gameState.weapon.id ? aspectDef : null;
    gameState.memory.begin({
      keepsake,
      aspect: aspect?.id ?? null,
      trialCards: init.traitCards,
      baseCards: GROWTH.traitChoices,
      maxCards: RUN_END.trial.max,
    });
    const gold = keepsakeEffect(keepsake).startGold ?? 0;
    if (gold > 0) gameState.gold += gold;
    if (aspect?.trait) gameState.weapon.addTrait(aspect.trait);
  }

  /** 보스 보상 패시브 3지선다 — 57라운드: BuildMenus (이중 개성 확정 칸 · 태그 · 1층 테마 가중) */
  private openPassiveChooser(onDone: () => void): void {
    // 60라운드 (h) 파훼 n ≥ 4: 보스 패시브 희귀 이상 보장
    this.g.buildMenus.openPassiveMenu('boss', { rarities: this.g.bundle?.breaks.bossRarities() }, onDone);
  }

  // --- 런 종료 ---

  /** 런 종료 정산: 영혼 지급·도감 기록 (사망·클리어·층 끝 공통, 1회) */
  settleRun(cleared: boolean): void {
    if (gameState.runSettled) return;
    gameState.runSettled = true;
    const w = gameState.weapon;
    const { meta, gained } = recordRun(metaStore.read(), {
      weaponId: w.id,
      weaponStage: w.stage,
      evolutionNames: w.nodes.map((e) => e.name),
      floorReached: gameState.floorReached,
      kills: gameState.kills,
      cleared,
    });
    metaStore.write(meta);
    // 61라운드 P7·P8 일기장: 지난 생 기록 · 사망 수 (시험장 제외)
    if (!this.g.lab)
      updateDiary((d) =>
        recordLifeEnd(
          d,
          {
            name: gameState.playerName,
            weapon: w.id,
            floor: gameState.floorReached,
            kills: gameState.kills,
            cleared,
            bosses: [...gameState.narrative.bossKilled],
          },
          NARRATIVE.diary.pastLivesMax,
        ),
      );
    // 47라운드 C3 묘 '기록한다' 영혼은 이미 메타에 적립 — 결과 화면에 합산만
    gameState.lastSoulGain = gained + gameState.bonusSouls;
    invalidateMetaSummary();
  }

  onPlayerDied(): void {
    const g = this.g;
    g.saveSlot.clear(); // 영구 사망 (기획 3장)
    this.settleRun(false);
    g.player.body.setVelocity(0, 0);
    for (const m of g.mobs.getChildren() as Mob[]) m.body.setVelocity(0, 0);
    // 62 루프 2 C (P1-7): 슬로모 → 먹 번짐 → 결산 (쓰러짐 그림이 길면 끝 프레임까지)
    const animMs = g.player.deathAnimMs > 0 ? g.player.deathAnimMs + SPRITES.DEATH_EXTRA_MS : 0;
    g.motion.stopAimFx(false);
    g.screenFx.death(RUN_END.death.slowMs + RUN_END.death.inkMs);
    g.runEnd.beginDeath(animMs, () => this.endRunScene(false, { summary: g.runEnd.summary('death') }));
  }

  /**
   * 결과 화면: UI 렌더러가 있으면 UI 결과 씬, 아니면 시스템 임시 화면. extra = 62 루프 2 C 결산(summary)·층 끝(floorEnd)
   * (D '런 포기' 도 사망과 같은 결산 — summary 를 넘기면 그대로 싣는다)
   */
  endRunScene(cleared: boolean, extra: { summary?: UiRunSummary; floorEnd?: UiFloorEnd } = {}): void {
    const g = this.g;
    const result: UiResult = {
      cleared,
      stageName: floorText(gameState.stageId)?.title ?? gameState.stage.name,
      floorReached: gameState.floorReached,
      kills: gameState.kills,
      gold: gameState.gold,
      sense: gameState.senses.sense,
      weaponName: gameState.weapon.displayName,
      soulsGained: gameState.lastSoulGain,
      soulsTotal: metaStore.read().souls,
      seed: gameState.seed,
      playerName: gameState.playerName,
      line: cleared
        ? STORY.endings[gameState.ending ?? 'destroy']
        : deathLine(gameState.playerName, gameState.floorReached, gameState.kills),
      ending: cleared ? (gameState.ending ?? 'destroy') : undefined,
      // 61라운드 P7: 사망 문장 뒤 '이름이 번진다.' (UI 가 이름 번짐 연출과 함께)
      smudgeLine: cleared ? undefined : NARRATIVE_STORY.nameSmudge.onDeath,
      ...(extra.summary ? { summary: extra.summary } : {}),
      ...(extra.floorEnd ? { floorEnd: extra.floorEnd } : {}),
    };
    // 층 끝: 문장 = 층 끝 맺음 (엔딩 문장 아님)
    if (extra.floorEnd) {
      result.line = RUN_END.floorEnd.summary.closing;
      delete result.ending;
    }
    this.debugLastResult = result;
    EventBus.emit(Events.RUN_ENDED, { cleared } satisfies RunEndedPayload);
    __system.emit(UI_EVENTS.RUN_ENDED, result);
    if (__system.rendererRegistered() && g.scene.manager.keys[UI_SCENES.RESULT]) {
      if (g.scene.isActive(UI_SCENES.HUD)) g.scene.stop(UI_SCENES.HUD);
      g.scene.start(UI_SCENES.RESULT, result);
    } else {
      g.scene.start(SCENES.GAME_OVER, { cleared });
    }
  }
}

function pickSeed(): string {
  return urlParams().get('seed') || Date.now().toString(36);
}
