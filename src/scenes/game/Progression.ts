/**
 * 런 진행: 처치 → 각성 게이지 적립(61 G — 눈금 메뉴는 growth/GrowthFlow) · 스테이지 보상(감각 → 능력치 포인트 → 패시브) ·
 * 엔딩(23라운드 2지선다) · 사망 · 결과 화면 · 런 시작 모드(새 런 / 다음 층 / 이어하기 / 다음 노드) · 세이브.
 */
import { PROTOTYPE, SCENES, SPRITES } from '../../core/Constants';
import { EventBus, Events, type RunEndedPayload, type RunStartedPayload } from '../../core/EventBus';
import { gameState, type EndingChoice } from '../../core/GameState';
import { ECONOMY, STORY } from '../../data';
import { GROWTH } from '../../data/growth';
import type { StatKey } from '../../data/types';
import { UI_EVENTS, __system } from '../../contract/ui';
import type { Mob } from '../../objects/Mob';
import { applyStatReward, findReward } from '../../systems/economy';
import { markUnderstood, metaStore, recordRun } from '../../systems/meta';
import type { KillKind } from '../../systems/senses';
import { deathLine, fill, floorText } from '../../systems/story';
import { NARRATIVE, NARRATIVE_STORY } from '../../data/narrative';
import { recordLifeEnd, updateDiary } from '../../systems/narrative/diary';
import { UI_SCENES } from '../../ui';
import type { TileWorld } from '../../world/TileWorld';
import type { Game } from '../Game';
import { continueSave } from './runWeapon';
import { urlParams, type GameInitData } from './shared';

export class Progression {
  /** 디버그: 마지막 결과 화면 페이로드 */
  debugLastResult: unknown = null;

  constructor(private readonly g: Game) {}

  // --- 런 시작 ---

  /** 런 시작 모드 결정: 새 런 / 다음 층 / 세이브 이어하기 / 같은 층 다음 노드(48라운드). 층 시작이면 true */
  prepareRun(init: GameInitData, senseBonus: number): boolean {
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
      // 49라운드 Q2: 회피 시험 등급 보상 — 시작 감각 +0~3 (Setup 이 senseBonus 로 넘긴다)
      gameState.senses.sense += senseBonus;
      g.saveSlot.clear();
      this.emitRunStarted(false);
    } else {
      const save = continueSave(g.saveSlot);
      if (save) {
        gameState.applySave(save);
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
    if (gameState.senses.recordKill(kind)) {
      EventBus.emit(Events.SENSE_GAINED, { kind, sense: gameState.senses.sense });
    }
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
    gameState.pointsPending += gameState.senses.gainedThisStage;
    gameState.rewardPending = true;
    const finish = () => {
      gameState.rewardPending = false;
      gameState.route?.markCleared();
      g.world.placeExit(room);
      g.world.placeShop(room);
      gameState.exitOpen = true;
      EventBus.emit(Events.EXIT_OPENED, { stageIndex: gameState.stageIndex });
    };
    const passiveStep = () => this.openPassiveChooser(finish);
    if (gameState.pointsPending > 0) this.openStatChooser(passiveStep);
    else passiveStep();
  }

  /** 능력치 포인트를 모두 쓸 때까지 선택 메뉴를 보여준다 (임시 텍스트) */
  openStatChooser(onDone: () => void): void {
    const menu = this.g.menu;
    const lines = ECONOMY.statRewards.map((r, i) => ({ key: String(i + 1), label: r.name, enabled: true }));
    const show = () => {
      menu.open('reward', fill(STORY.ui.hud.rewardTitle, { n: gameState.pointsPending }), lines, (key) => {
        const reward = ECONOMY.statRewards[Number(key) - 1];
        this.applyReward(reward.id);
        if (gameState.pointsPending > 0) show();
        else {
          menu.close();
          onDone();
        }
      });
    };
    show();
  }

  /** 보스 보상 패시브 3지선다 — 57라운드: BuildMenus (이중 개성 확정 칸 · 태그 · 1층 테마 가중) */
  private openPassiveChooser(onDone: () => void): void {
    // 60라운드 (h) 파훼 n ≥ 4: 보스 패시브 희귀 이상 보장
    this.g.buildMenus.openPassiveMenu('boss', { rarities: this.g.bundle?.breaks.bossRarities() }, onDone);
  }

  private applyReward(id: StatKey): void {
    const reward = findReward(ECONOMY, id);
    gameState.bonus = applyStatReward(gameState.bonus, reward);
    if (reward.maxHp) {
      gameState.maxHp += reward.maxHp;
      gameState.hp += reward.maxHp;
    }
    gameState.pointsPending -= 1;
    EventBus.emit(Events.STAT_REWARD, { id, bonus: gameState.bonus, pointsLeft: gameState.pointsPending });
  }

  // --- 런 종료 ---

  /** 런 종료 정산: 영혼 지급·도감 기록 (사망·클리어 공통, 1회) */
  private settleRun(cleared: boolean): void {
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
  }

  onPlayerDied(): void {
    const g = this.g;
    g.saveSlot.clear(); // 영구 사망 (기획 3장)
    this.settleRun(false);
    g.player.body.setVelocity(0, 0);
    for (const m of g.mobs.getChildren() as Mob[]) m.body.setVelocity(0, 0);
    // 사망 애니가 있으면 끝 프레임을 보여준 뒤 결과 화면으로
    const delay = g.player.deathAnimMs > 0 ? g.player.deathAnimMs + SPRITES.DEATH_EXTRA_MS : 0;
    g.motion.stopAimFx(false);
    g.screenFx.death(delay);
    if (delay > 0) g.time.delayedCall(delay, () => this.endRunScene(false));
    else this.endRunScene(false);
  }

  /** 결과 화면: UI 렌더러가 있으면 UI 결과 씬, 아니면 시스템 임시 화면 */
  private endRunScene(cleared: boolean): void {
    const g = this.g;
    const result = {
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
    };
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
