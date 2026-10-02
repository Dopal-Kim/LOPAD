import { PLAYER_DATA, RUN, STAGES, WEAPONS } from '../data';
import type { StageDef } from '../data/types';
import type { SaveData } from '../systems/save';
import { SAVE_VERSION } from '../systems/save';
import { SenseTracker } from '../systems/senses';
import { WeaponState } from '../systems/weapons';
import { EMPTY_BONUS, type StatBonus } from '../systems/economy';
import { metaBonus, metaStore, type MetaBonus } from '../systems/meta';
import { PassiveSet } from '../systems/passives';
import type { RouteState } from '../systems/route';
import type { StructureFloorCarry } from '../systems/structures/StructureSystem';

export type EndingChoice = 'destroy' | 'understand';

/** 런 상태의 단일 출처. 런 시작은 startRun(), 층 전환은 nextStage(). */
class GameState {
  seed = '';
  /** 일기장에 적은 이름 (23라운드). 비어 있으면 '―' 로 표시 */
  playerName = '';
  stageIndex = 0;
  savesLeft = RUN.maxSaves;
  hp = PLAYER_DATA.stats.hp;
  maxHp = PLAYER_DATA.stats.hp;
  kills = 0;
  readonly senses = new SenseTracker();
  gold = 0;
  potions = 0;
  /** 아직 쓰지 않은 능력치 포인트 */
  pointsPending = 0;
  bonus: StatBonus = { ...EMPTY_BONUS };
  passives = new PassiveSet();
  /** 보상 선택 중 (출구는 끝난 뒤 열림) */
  rewardPending = false;
  /** 런 시작 시 적용된 영구 강화 */
  meta: MetaBonus = { maxHp: 0, attack: 0, defense: 0, dashCooldownMult: 1, potionCarry: 0 };
  /** 마지막 런 종료 시 얻은 영혼 (결과 화면용) */
  lastSoulGain = 0;
  /** 런 종료 정산이 끝났는지 (중복 정산 방지) */
  runSettled = false;
  weapon = new WeaponState(PLAYER_DATA.startWeapon, WEAPONS[PLAYER_DATA.startWeapon]);
  trialsCleared = 0;
  trialsTotal = 0;
  roomId = '';
  roomType = '';
  bossHp = 0;
  bossMaxHp = 0;
  bossPhase = 0;
  bossUnlocked = false;
  gameOver = false;
  cleared = false;
  /** 황제 처치 후 고른 엔딩 (23라운드: 없앤다 / 이해한다). 선택 전·일반 런은 null */
  ending: EndingChoice | null = null;
  /** 보스 처치 후 출구가 열린 상태 */
  exitOpen = false;
  /** 47라운드 구조물: 층 안에서만 유지되는 방어력 가감 (1-5 취기). 층 전환 시 0 */
  structureDefense = 0;
  /**
   * 47라운드 C3 묘 '기록한다'로 이번 런에 이미 메타에 적립한 영혼 (결과 화면 합산 표시용).
   * 적립은 즉시 메타에 쓰므로 세이브 형식은 그대로다 (Q13)
   */
  bonusSouls = 0;
  /** 48라운드 노드 지도 진행 상태 (노드 지도를 쓰지 않는 층이면 null). 층 전환 시 null */
  route: RouteState | null = null;
  /** 48라운드: 노드 사이에 들고 다니는 구조물 층 상태 (빚·취기·판돈 등). 층 전환 시 null */
  structureCarry: StructureFloorCarry | null = null;
  /** 48라운드 Q6: 새 런 첫 노드에서 탄생 연출을 아직 보지 않았다 */
  birthPending = false;

  get stageId(): string {
    return RUN.order[this.stageIndex];
  }

  get stage(): StageDef {
    return STAGES[this.stageId];
  }

  get isLastStage(): boolean {
    return this.stageIndex >= RUN.order.length - 1;
  }

  /** 이 층의 맵 시드 (런 시드 + 층 번호) */
  get floorSeed(): string {
    return `${this.seed}:${this.stageIndex}`;
  }

  /** 새 런. weaponId 는 개성 선택 결과 (없으면 기본 무기) */
  startRun(seed: string, weaponId: string = PLAYER_DATA.startWeapon, playerName = ''): void {
    const wid = WEAPONS[weaponId] ? weaponId : PLAYER_DATA.startWeapon;
    this.seed = seed;
    this.playerName = playerName;
    this.stageIndex = 0;
    this.savesLeft = RUN.maxSaves;
    this.meta = metaBonus(metaStore.read());
    this.hp = PLAYER_DATA.stats.hp + this.meta.maxHp;
    this.maxHp = PLAYER_DATA.stats.hp + this.meta.maxHp;
    this.lastSoulGain = 0;
    this.bonusSouls = 0;
    this.runSettled = false;
    this.ending = null;
    this.kills = 0;
    this.senses.reset();
    this.gold = 0;
    this.potions = 0;
    this.pointsPending = 0;
    this.bonus = { ...EMPTY_BONUS };
    this.passives = new PassiveSet();
    this.weapon = new WeaponState(wid, WEAPONS[wid]); // 사망 시 무기 초기화 (기획 3장)
    this.birthPending = true;
    this.resetStage();
  }

  /** 다음 층으로 (HP·무기·감각·처치 수 유지) */
  nextStage(): void {
    this.stageIndex += 1;
    this.senses.nextStage();
    this.resetStage();
  }

  /** 디버그·검증 전용 (47라운드): 지정 층으로 바로 (세이브 없음, 나머지는 nextStage 와 같음) */
  gotoStage(index: number): void {
    this.stageIndex = Math.max(0, Math.min(RUN.order.length - 1, Math.floor(index)));
    this.senses.nextStage();
    this.resetStage();
  }

  private resetStage(): void {
    this.trialsCleared = 0;
    this.trialsTotal = 0;
    this.roomId = '';
    this.roomType = '';
    this.bossHp = 0;
    this.bossMaxHp = 0;
    this.bossPhase = 0;
    this.bossUnlocked = false;
    this.gameOver = false;
    this.cleared = false;
    this.exitOpen = false;
    this.rewardPending = false;
    this.structureDefense = 0;
    this.route = null;
    this.structureCarry = null;
  }

  /** 기본 스탯 + 런 보너스 */
  get attack(): number {
    return PLAYER_DATA.stats.attack + this.bonus.attack + this.meta.attack;
  }

  get defense(): number {
    return (
      PLAYER_DATA.stats.defense +
      this.bonus.defense +
      this.meta.defense +
      this.passives.total('defense') +
      this.structureDefense
    );
  }

  /** 1부터 세는 도달 층 */
  get floorReached(): number {
    return this.stageIndex + 1;
  }

  get crit(): number {
    return PLAYER_DATA.stats.crit + this.bonus.crit + this.weapon.def.critBonus;
  }

  toSave(): SaveData {
    return {
      version: SAVE_VERSION,
      seed: this.seed,
      stageIndex: this.stageIndex,
      hp: this.hp,
      maxHp: this.maxHp,
      kills: this.kills,
      sense: this.senses.sense,
      savesLeft: this.savesLeft,
      weapon: { id: this.weapon.id, ...this.weapon.toProgress() },
      gold: this.gold,
      potions: this.potions,
      pointsPending: this.pointsPending,
      bonus: { ...this.bonus },
      passives: { ...this.passives.owned },
      playerName: this.playerName,
      savedAt: Date.now(),
    };
  }

  applySave(d: SaveData): void {
    this.startRun(d.seed);
    this.birthPending = false;
    this.stageIndex = Math.min(d.stageIndex, RUN.order.length - 1);
    this.hp = d.hp;
    this.maxHp = d.maxHp;
    this.kills = d.kills;
    this.senses.sense = d.sense;
    this.savesLeft = d.savesLeft;
    const weaponId = WEAPONS[d.weapon.id] ? d.weapon.id : PLAYER_DATA.startWeapon;
    this.weapon = new WeaponState(weaponId, WEAPONS[weaponId]);
    this.weapon.restore(d.weapon);
    this.gold = d.gold;
    this.potions = d.potions;
    this.pointsPending = d.pointsPending;
    this.bonus = { ...EMPTY_BONUS, ...d.bonus };
    this.passives.restore(d.passives ?? {});
    this.playerName = d.playerName ?? '';
  }
}

export const gameState = new GameState();
