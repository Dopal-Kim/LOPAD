/**
 * 이벤트 → 효과음 표 (음향↔시스템 계약 초안 `assets/audio/manifest.json` 의 trigger 제안을
 * 시스템 EventBus 이벤트 이름으로 확정한 것. 결정 로그 I·K).
 * 순수 데이터 — 재생은 systems/audio.ts 가 이 표를 구독해서 처리한다.
 * `sfx` 가 함수이면 페이로드로 id 를 정한다(null 이면 재생 없음). 매니페스트에 없는 id 는 조용히 무시된다.
 */
import {
  Events,
  type BossAttackPayload,
  type BossTelegraphPayload,
  type EnemyAttackPayload,
  type EnemyDamagedPayload,
  type EnemyTelegraphPayload,
  type MenuEventPayload,
  type PlayerAttackPayload,
  type PlayerSecondaryPayload,
  type TrialClearedPayload,
} from '../core/EventBus';
import { gameState } from '../core/GameState';

export interface AudioTrigger<P = unknown> {
  event: string;
  /** 설명 (매핑 요약용) */
  note: string;
  /** 재생할 효과음 id (고정 또는 페이로드로 결정) */
  sfx?: string | ((p: P) => string | null);
  /** 조건. 없으면 항상 */
  when?: (p: P) => boolean;
  /** 재생 지연 ms (애니 프레임에 맞출 때) */
  delayMs?: (p: P) => number;
  /** 루프 효과음 시작 (가드 유지) */
  loop?: string;
  /** 정지할 효과음·루프 id */
  stop?: string[];
}

function t<P>(def: AudioTrigger<P>): AudioTrigger {
  return def as AudioTrigger;
}

export const SFX = {
  swing: (weaponId: string) => `sfx/swing_${weaponId}`,
  bowShot: 'sfx/bow_shot',
  bowAimed: 'sfx/bow_aimed',
  bowDraw: 'sfx/bow_draw',
  guardHold: 'sfx/guard_hold',
  guardPush: 'sfx/guard_push',
  shadowstep: 'sfx/shadowstep',
  dash: 'sfx/dash',
  parry: 'sfx/parry',
  hitEnemy: 'sfx/hit_enemy',
  hitEnemyCrit: 'sfx/hit_enemy_crit',
  enemyHurt: 'sfx/enemy_hurt',
  enemyDeath: 'sfx/enemy_death',
  hitPlayer: 'sfx/hit_player',
  playerDeath: 'sfx/player_death',
  enemyTelegraph: (id: string) => `sfx/${id}_telegraph`,
  enemyDash: (id: string) => `sfx/${id}_dash`,
  enemyShot: (id: string) => `sfx/${id}_shot`,
  bossStart: 'sfx/boss_start',
  bossTelegraph: 'sfx/boss_telegraph',
  bossFan: 'sfx/boss_fan',
  bossPhase: 'sfx/boss_phase',
  bossDie: 'sfx/boss_die',
  doorClose: 'sfx/door_close',
  doorOpen: 'sfx/door_open',
  trialClear: 'sfx/trial_clear',
  bossUnlock: 'sfx/boss_unlock',
  exitOpen: 'sfx/exit_open',
  levelEnter: 'sfx/level_enter',
  save: 'sfx/save',
  pickupGold: 'sfx/pickup_gold',
  pickupPotion: 'sfx/pickup_potion',
  potionUse: 'sfx/potion_use',
  shopBuy: 'sfx/shop_buy',
  fateDecided: 'sfx/fate_decided',
  evolve: 'sfx/evolve',
  reinforce: 'sfx/reinforce',
  menuMove: 'sfx/menu_move',
  menuSelect: 'sfx/menu_select',
  menuCancel: 'sfx/menu_cancel',
} as const;

export const AUDIO_TRIGGERS: readonly AudioTrigger[] = [
  // --- 주인공 공격·보조 동작 ---
  t<PlayerAttackPayload>({
    event: Events.PLAYER_ATTACKED,
    note: '공격: 근접은 무기별 swing(휘두름 2프레임 시작에 맞춤), 활은 bow_shot(3프레임 = 화살 생성), 조준 사격은 bow_aimed',
    sfx: (p) => {
      const w = gameState.weapon.def;
      if (w.kind === 'ranged') return p.kind === 'aimed' ? SFX.bowAimed : SFX.bowShot;
      return SFX.swing(gameState.weapon.id);
    },
    delayMs: (p) => (gameState.weapon.def.kind === 'ranged' ? p.releaseDelayMs : p.swingDelayMs),
  }),
  t<PlayerSecondaryPayload>({
    event: Events.PLAYER_SECONDARY,
    note: '조준 사격 차지 시작 → bow_draw',
    when: (p) => p.kind === 'aimedshot' && p.phase === 'start',
    sfx: SFX.bowDraw,
  }),
  t<PlayerSecondaryPayload>({
    event: Events.PLAYER_SECONDARY,
    note: '조준 사격 조기 해제 → bow_draw 정지',
    when: (p) => p.kind === 'aimedshot' && p.phase === 'cancel',
    stop: [SFX.bowDraw],
  }),
  t<PlayerSecondaryPayload>({
    event: Events.PLAYER_SECONDARY,
    note: '가드 시작 → guard_hold 루프',
    when: (p) => p.kind === 'guard' && p.phase === 'start',
    loop: SFX.guardHold,
  }),
  t({
    event: Events.PLAYER_GUARD_RELEASED,
    note: '가드 해제 → 루프 정지 + guard_push',
    stop: [SFX.guardHold],
    sfx: SFX.guardPush,
  }),
  t({ event: Events.PLAYER_SHADOW_STEP, note: '그림자 걸음', sfx: SFX.shadowstep }),
  t({ event: Events.PLAYER_DASHED, note: '대쉬', sfx: SFX.dash }),
  t({ event: Events.PLAYER_PARRIED, note: '패링 성공', sfx: SFX.parry }),

  // --- 타격·적 ---
  t<EnemyDamagedPayload>({
    event: Events.ENEMY_DAMAGED,
    note: '적 피격: 치명이면 hit_enemy_crit, 아니면 hit_enemy (출혈·잔월 틱은 제외)',
    when: (p) => !p.tick,
    sfx: (p) => (p.crit ? SFX.hitEnemyCrit : SFX.hitEnemy),
  }),
  t<EnemyDamagedPayload>({
    event: Events.ENEMY_DAMAGED,
    note: '적 피격 보조음 enemy_hurt (틱 포함, 피격음과 겹침)',
    sfx: SFX.enemyHurt,
  }),
  t({ event: Events.ENEMY_DIED, note: '일반 적 사망', sfx: SFX.enemyDeath }),
  t({ event: Events.PLAYER_DAMAGED, note: '주인공 피격', sfx: SFX.hitPlayer }),
  t({ event: Events.PLAYER_DIED, note: '주인공 사망', sfx: SFX.playerDeath }),
  t<EnemyTelegraphPayload>({
    event: Events.ENEMY_TELEGRAPH,
    note: '적 돌진 예고 → sfx/<적id>_telegraph (결사병 charger_telegraph)',
    sfx: (p) => SFX.enemyTelegraph(p.id),
  }),
  t<EnemyAttackPayload>({
    event: Events.ENEMY_ATTACK,
    note: '적 공격 실행 → dash 는 sfx/<적id>_dash(결사병), shot 은 sfx/<적id>_shot(사수, 총구 프레임에 맞춘 발사 시점). 접촉 공격은 없음',
    sfx: (p) => (p.kind === 'dash' ? SFX.enemyDash(p.id) : p.kind === 'shot' ? SFX.enemyShot(p.id) : null),
  }),

  // --- 보스 ---
  t({ event: Events.BOSS_STARTED, note: '보스 등장', sfx: SFX.bossStart }),
  t<BossTelegraphPayload>({
    event: Events.BOSS_TELEGRAPH,
    note: '보스 돌진 예고',
    when: (p) => p.attack === 'dash',
    sfx: SFX.bossTelegraph,
  }),
  t<BossAttackPayload>({
    event: Events.BOSS_ATTACK,
    note: '보스 부채꼴 투사체 (돌진 실행음은 자산 없음)',
    when: (p) => p.attack === 'fan',
    sfx: SFX.bossFan,
  }),
  t({ event: Events.BOSS_PHASE, note: '보스 국면 전환', sfx: SFX.bossPhase }),
  t({ event: Events.BOSS_DIED, note: '보스 사망', sfx: SFX.bossDie }),

  // --- 맵·월드 ---
  t({ event: Events.TRIAL_STARTED, note: '시련 방 문 잠김', sfx: SFX.doorClose }),
  t({ event: Events.TRIAL_CLEARED, note: '시련 클리어: 문 열림', sfx: SFX.doorOpen }),
  t<TrialClearedPayload>({
    event: Events.TRIAL_CLEARED,
    note: '시련 클리어 북 (마지막 시련은 boss_unlock 이 대신한다)',
    when: (p) => p.cleared < p.total,
    sfx: SFX.trialClear,
  }),
  t({ event: Events.BOSS_UNLOCKED, note: '본영 문 열림', sfx: SFX.bossUnlock }),
  t({ event: Events.EXIT_OPENED, note: '오르는 길(출구) 열림', sfx: SFX.exitOpen }),
  t({ event: Events.STAGE_STARTED, note: '층 진입', sfx: SFX.levelEnter }),
  t({ event: Events.STAGE_SAVED, note: '기록 저장', sfx: SFX.save }),

  // --- 획득·소모·상점 ---
  t<{ delta: number }>({
    event: Events.GOLD_CHANGED,
    note: '골드 증가 (드랍·시련·보스 보너스)',
    when: (p) => p.delta > 0,
    sfx: SFX.pickupGold,
  }),
  t<{ kind: string }>({
    event: Events.ITEM_PICKED,
    note: '물약 획득',
    when: (p) => p.kind === 'potion',
    sfx: SFX.pickupPotion,
  }),
  t({ event: Events.POTION_USED, note: '물약 사용 (휴식·상점 회복에는 없음)', sfx: SFX.potionUse }),
  t({ event: Events.SHOP_BOUGHT, note: '상점 구매', sfx: SFX.shopBuy }),

  // --- 연출·UI ---
  t({ event: Events.FATE_DECIDED, note: '운명(무기) 결정', sfx: SFX.fateDecided }),
  t({
    event: Events.ENDING_CHOSEN,
    note: '엔딩 선택 — 전용 자산이 없어 fate_decided(일기장 덮는 소리) 재사용 (임시)',
    sfx: SFX.fateDecided,
  }),
  t({ event: Events.WEAPON_EVOLVED, note: '개성 변화', sfx: SFX.evolve }),
  t({ event: Events.WEAPON_REINFORCED, note: '무기 강화', sfx: SFX.reinforce }),
  t<MenuEventPayload>({
    event: Events.MENU_OPENED,
    note: '메뉴 열림 → menu_move (같은 메뉴를 다시 그리는 reopen 은 제외)',
    when: (p) => !p.reopen,
    sfx: SFX.menuMove,
  }),
  t({ event: Events.MENU_SELECTED, note: '메뉴 선택', sfx: SFX.menuSelect }),
  t<MenuEventPayload>({
    event: Events.MENU_CLOSED,
    note: '선택 없이 닫힘(상점 이탈 등) → menu_cancel',
    when: (p) => !p.selected,
    sfx: SFX.menuCancel,
  }),
];

/** 표에 등장하는 고정 효과음 id (매니페스트 대조 테스트용) */
export function staticSfxIds(triggers: readonly AudioTrigger[] = AUDIO_TRIGGERS): string[] {
  const out = new Set<string>();
  for (const tr of triggers) {
    if (typeof tr.sfx === 'string') out.add(tr.sfx);
    if (tr.loop) out.add(tr.loop);
    for (const s of tr.stop ?? []) out.add(s);
  }
  return [...out].sort();
}
