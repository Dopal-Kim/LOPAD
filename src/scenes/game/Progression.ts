/**
 * 런 진행: 처치 → 개성 적립 → 3지선다(변환 A/B · 강화) · 스테이지 보상(감각 → 능력치 포인트 → 패시브) ·
 * 엔딩(23라운드 2지선다) · 사망 · 결과 화면 · 런 시작 모드(새 런 / 다음 층 / 이어하기 / 다음 노드) · 세이브.
 */
import { COLORS, DEPTH, GAME, PLACEHOLDER_UI, PROTOTYPE, SCENES, SPRITES } from '../../core/Constants';
import { screenFixed } from '../../systems/display';
import {
  EventBus,
  Events,
  type RunEndedPayload,
  type WeaponEvolvedPayload,
  type WeaponReinforcedPayload,
} from '../../core/EventBus';
import { gameState, type EndingChoice } from '../../core/GameState';
import { ECONOMY, STORY, WEAPON_RULES } from '../../data';
import type { StatKey, WeaponEvolution } from '../../data/types';
import { UI_EVENTS, __system } from '../../contract/ui';
import type { Mob } from '../../objects/Mob';
import { applyStatReward, findReward } from '../../systems/economy';
import { markUnderstood, metaStore, recordRun } from '../../systems/meta';
import { PASSIVES } from '../../systems/passives';
import type { KillKind } from '../../systems/senses';
import { deathLine, evolutionLine, fill, floorText } from '../../systems/story';
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
    } else {
      const save = continueSave(g.saveSlot);
      if (save) {
        gameState.applySave(save);
      } else {
        gameState.startRun(pickSeed());
        g.saveSlot.clear();
      }
    }
    EventBus.emit(Events.STAGE_STARTED, { stageIndex: gameState.stageIndex, stageId: gameState.stageId });
    return true;
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
    g.economy.dropLoot(mob, km.goldMult);
    this.gainPersonality(
      Math.round(mob.personalityValue * (1 + gameState.passives.total('personalityMult')) * km.personalityMult),
    );
    const lifesteal = gameState.passives.total('healOnKill');
    if (lifesteal > 0) g.player.heal(lifesteal);
    if (gameState.senses.recordKill(kind)) {
      EventBus.emit(Events.SENSE_GAINED, { kind, sense: gameState.senses.sense });
    }
    g.director.onMobDied(mob);
  }

  /** 개성 수치 적립. 임계에 닿으면 선택 대기 → update 에서 메뉴를 연다 */
  gainPersonality(amount: number): void {
    const weapon = gameState.weapon;
    const reached = weapon.gainPersonality(amount);
    EventBus.emit(Events.PERSONALITY_GAINED, { value: weapon.personality, threshold: weapon.threshold });
    if (reached) EventBus.emit(Events.WEAPON_CHOICE_PENDING, { weapon: weapon.id, stage: weapon.stage });
  }

  /** 개성 임계 도달 → 다른 메뉴(보스 보상 등)가 닫힌 뒤 3지선다 (게임 정지) */
  maybeOpenEvolveMenu(): void {
    if (gameState.weapon.choicePending && !this.g.menu.isOpen && !this.g.frozen) this.openEvolveMenu();
  }

  private openEvolveMenu(): void {
    const g = this.g;
    const w = gameState.weapon;
    const options = w.options;
    if (!w.canEvolve) {
      w.choicePending = false;
      return;
    }
    g.setFrozen(true);
    const lines = [0, 1].map((i) => {
      const o = options[i] as WeaponEvolution | undefined;
      return {
        key: String(i + 1),
        label: o ? o.name : '변환 (완료)',
        enabled: Boolean(o),
        detail: o?.description,
      };
    });
    const cur = w.evolution ? w.evolution.name : w.def.name;
    const bonusPct = Math.round(WEAPON_RULES.reinforceBonus * 100);
    lines.push({
      key: '3',
      label: `${fill(STORY.ui.evolveMenu.reinforceItem, { n: w.reinforce + 1 })} — ${cur}`,
      enabled: w.canReinforce,
      detail: `피해·범위 +${bonusPct}% · 강화 ${w.reinforce}/${WEAPON_RULES.reinforceMax}`,
    });
    g.menu.open(
      'evolve',
      fill(STORY.ui.evolveMenu.title, { weapon: w.def.name, threshold: w.threshold }),
      lines,
      (key) => {
        if (key === '3') this.applyReinforce();
        else {
          const pick = options[Number(key) - 1];
          if (pick) this.applyEvolution(pick.id);
        }
      },
      STORY.ui.evolveMenu.footer,
    );
  }

  applyEvolution(id: string): void {
    const g = this.g;
    const weapon = gameState.weapon;
    const node = weapon.choose(id);
    if (!node) return;
    g.menu.close();
    g.setFrozen(false);
    g.screenFx.evolve();
    const payload: WeaponEvolvedPayload = { weapon: weapon.id, stage: weapon.stage, name: weapon.displayName };
    EventBus.emit(Events.WEAPON_EVOLVED, payload);
    if (!__system.rendererRegistered()) this.showEvolutionBanner(weapon.displayName);
    g.ui.story('evolution', evolutionLine(node.name));
  }

  private applyReinforce(): void {
    const g = this.g;
    const weapon = gameState.weapon;
    if (!weapon.reinforceNow()) return;
    g.menu.close();
    g.setFrozen(false);
    const payload: WeaponReinforcedPayload = {
      weapon: weapon.id,
      reinforce: weapon.reinforce,
      name: weapon.displayName,
    };
    EventBus.emit(Events.WEAPON_REINFORCED, payload);
    __system.emit(UI_EVENTS.WEAPON_EVOLVED, { name: weapon.displayName });
    if (!__system.rendererRegistered()) this.showEvolutionBanner(weapon.displayName);
    g.ui.story(
      'evolution',
      STORY.reinforce[weapon.reinforce - 1] ??
        fill(STORY.reinforceBanner, { evolution: weapon.displayName, n: weapon.reinforce }),
    );
  }

  /** 개성 변화 알림 (시스템 파트 임시 텍스트. 정식 연출·UI는 UI 파트) */
  private showEvolutionBanner(name: string): void {
    const g = this.g;
    const at = screenFixed(g.cameras.main, GAME.WIDTH / 2, GAME.HEIGHT / 2 - 40);
    const t = g.add
      .text(at.x, at.y, `개성 변화: ${name}`, {
        font: PLACEHOLDER_UI.FONT_BODY,
        color: COLORS.GAMEOVER_TEXT,
      })
      .setOrigin(0.5)
      .setScale(at.scale)
      .setScrollFactor(0)
      .setDepth(DEPTH.DEBUG);
    g.tweens.add({ targets: t, alpha: 0, delay: PROTOTYPE.BANNER_MS, duration: 400, onComplete: () => t.destroy() });
  }

  // --- 엔딩 (23라운드): 황제 처치 직후 2지선다, 선택 전까지 정지 ---

  beginEnding(): void {
    const g = this.g;
    g.setFrozen(true);
    g.player.body.setVelocity(0, 0);
    g.motion.stopGale();
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

  /** 보스 보상 패시브 3지선다 (임시 텍스트) */
  private openPassiveChooser(onDone: () => void): void {
    const g = this.g;
    const choices = gameState.passives.rollChoices(g.rng, ECONOMY.rarity, PASSIVES.choices);
    if (choices.length === 0) {
      onDone();
      return;
    }
    const lines = choices.map((p, i) => {
      const lv = gameState.passives.level(p.id);
      return {
        key: String(i + 1),
        label: `[${p.rarity}] ${p.name}${lv > 0 ? ` (Lv${lv} → ${lv + 1})` : ''} — ${p.description}`,
        enabled: true,
      };
    });
    g.menu.open('passive', STORY.ui.hud.passiveTitle, lines, (key) => {
      const pick = choices[Number(key) - 1];
      gameState.passives.add(pick.id);
      EventBus.emit(Events.PASSIVE_GAINED, { id: pick.id, level: gameState.passives.level(pick.id) });
      g.menu.close();
      onDone();
    });
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
