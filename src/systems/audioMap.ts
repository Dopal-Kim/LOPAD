/**
 * 이벤트 → 효과음 표 (음향↔시스템 계약 초안 `assets/audio/manifest.json` 의 trigger 제안을
 * 시스템 EventBus 이벤트 이름으로 확정한 것. 결정 로그 I·K).
 * 순수 데이터 — 재생은 systems/audio.ts 가 이 표를 구독해서 처리한다.
 * `sfx` 가 함수이면 페이로드로 id 를 정한다(null 이면 재생 없음). 매니페스트에 없는 id 는 조용히 무시된다.
 */
import {
  Events,
  type ChallengeEventPayload,
  type StructureBellPayload,
  type StructureEventPayload,
  type StructureFirePayload,
  type BossActionKind,
  type BossActionPayload,
  type BossAttackPayload,
  type BossLoopKind,
  type BossLoopPayload,
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
  /** 54라운드: 페이로드로 정하는 루프·정지 (보스 루프) */
  loopOf?: (p: P) => string;
  stopOf?: (p: P) => string[];
  /** 54라운드: 정지 페이드 ms (루프 끝 80~150ms 권장 — 음향 파트) */
  stopFadeMs?: number;
  /** 54라운드: 재생 속도 (3연 취권 1·2·3타 1.0/1.06/1.12 — 음향 파트 권장) */
  rate?: (p: P) => number;
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
  // 54라운드 1층 보스 '만취' (음향 매니페스트 조건 boss:1)
  boss1: {
    drinkLift: 'sfx/boss1_drink_lift',
    drinkGulp: 'sfx/boss1_drink_gulp',
    drinkFinish: 'sfx/boss1_drink_finish',
    cupShatter: 'sfx/boss1_cup_shatter',
    spinStart: 'sfx/boss1_spin_start',
    reelTelegraph: 'sfx/boss1_reel_telegraph',
    reelDash: 'sfx/boss1_reel_dash',
    fall: 'sfx/boss1_fall',
    barrelKick: 'sfx/boss1_barrel_kick',
    barrelRoll: 'sfx/boss1_barrel_roll',
    barrelBounce: 'sfx/boss1_barrel_bounce',
    liquorSplash: 'sfx/boss1_liquor_splash',
    torchThrow: 'sfx/boss1_torch_throw',
    ignite: 'sfx/boss1_ignite',
    fireLoop: 'sfx/boss1_fire_loop',
    candleTopple: 'sfx/boss1_candle_topple',
    candleRelight: 'sfx/boss1_candle_relight',
    phaseDrink: 'sfx/boss1_phase_drink',
  },
} as const;

/** 54라운드: 3연 취권 n타(0부터) 재생 속도 (음향 권장 1.0 / 1.06 / 1.12) */
export const REEL_RATES = [1, 1.06, 1.12] as const;

/** 54라운드: 보스 패턴 국면 → 효과음 (null = 없음). 대응표는 parts/system/README.md 54라운드 절 */
export function bossActionSfx(action: BossActionKind): string | null {
  const B = SFX.boss1;
  switch (action) {
    case 'drinkLift':
      return B.drinkLift;
    case 'drinkFinish':
      return B.drinkFinish;
    case 'cupBreak':
      return B.cupShatter;
    case 'reelTelegraph':
      return B.reelTelegraph;
    case 'reelDash':
      return B.reelDash;
    case 'fall':
      return B.fall;
    case 'kick':
    case 'caskRedirect':
      return B.barrelKick;
    case 'caskBounce':
      return B.barrelBounce;
    case 'caskBreak':
    case 'spill':
      return B.liquorSplash;
    case 'torchThrow':
      return B.torchThrow;
    case 'ignite':
    case 'bossIgnite':
      return B.ignite;
    case 'candleTopple':
      return B.candleTopple;
    case 'candleRelight':
      return B.candleRelight;
    default:
      return null;
  }
}

/** 54라운드 루프 종류 → 루프 효과음 */
export function bossLoopSfx(loop: BossLoopKind): string {
  const B = SFX.boss1;
  return loop === 'gulp' ? B.drinkGulp : loop === 'roll' ? B.barrelRoll : B.fireLoop;
}

/** 루프 끝 페이드 ms (음향 권장 80~150) */
const BOSS_LOOP_FADE_MS = 120;

/**
 * 47라운드 구조물 사용음: 새 효과음 없이 기존 효과음에 임시 연결 (음향 파트 후속, 결정 round-47).
 * 패 탁자는 메뉴 선택음이, 투견 링은 도전 시작음이 대신한다
 */
export function structureUseSfx(kind: string): string | null {
  switch (kind) {
    case 'chest':
    case 'ledger':
    case 'exchange':
    case 'pawn':
      return SFX.shopBuy;
    case 'grave':
      return SFX.save;
    case 'campfire':
    case 'counter':
      return SFX.potionUse;
    case 'agingBarrel':
      return SFX.pickupPotion;
    default:
      return null;
  }
}

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
  t({
    event: Events.BOSS_PHASE,
    note: '보스 국면 전환 (54라운드: 1층 보스는 들이켜기 boss1_phase_drink)',
    sfx: () => (gameState.stage?.boss === 'stage1' ? SFX.boss1.phaseDrink : SFX.bossPhase),
  }),
  // --- 54라운드 1층 보스 '만취' 새 패턴 ---
  t<BossAttackPayload>({
    event: Events.BOSS_ATTACK,
    note: '세상이 돈다 시작 → boss1_spin_start',
    when: (p) => p.attack === 'spin',
    sfx: SFX.boss1.spinStart,
  }),
  t<BossActionPayload>({
    event: Events.BOSS_ACTION,
    note: '잔 깨짐 → 들이켜기 루프 즉시 정지',
    when: (p) => p.action === 'cupBreak',
    stop: [SFX.boss1.drinkGulp],
  }),
  t<BossActionPayload>({
    event: Events.BOSS_ACTION,
    note: '보스 패턴 국면 → bossActionSfx (3연 취권 n타는 재생 속도 REEL_RATES)',
    sfx: (p) => bossActionSfx(p.action),
    rate: (p) =>
      p.action === 'reelTelegraph' || p.action === 'reelDash'
        ? REEL_RATES[Math.min(REEL_RATES.length - 1, p.index ?? 0)]
        : 1,
  }),
  t<BossLoopPayload>({
    event: Events.BOSS_LOOP,
    note: '보스 루프 켜기: 들이켜기·술통 구름·불 웅덩이(여러 개여도 하나)',
    when: (p) => p.on,
    loopOf: (p) => bossLoopSfx(p.loop),
  }),
  t<BossLoopPayload>({
    event: Events.BOSS_LOOP,
    note: '보스 루프 끄기 (페이드)',
    when: (p) => !p.on,
    stopOf: (p) => [bossLoopSfx(p.loop)],
    stopFadeMs: BOSS_LOOP_FADE_MS,
  }),
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

  // --- 47라운드 상호작용 구조물 (전부 기존 효과음 임시 연결) ---
  t<StructureEventPayload>({
    event: Events.STRUCTURE_BROKEN,
    note: '구조물 부서짐: 짐 hit_enemy · 술통 guard_push · 숨은 벽 door_open (임시)',
    sfx: (p) => (p.kind === 'cask' ? SFX.guardPush : p.kind === 'hiddenWall' ? SFX.doorOpen : SFX.hitEnemy),
  }),
  t<StructureEventPayload>({
    event: Events.STRUCTURE_HIT,
    note: '부서지지 않는 타격: 숨은 벽 금·술통 굴림 → hit_enemy (임시)',
    when: (p) => p.kind === 'hiddenWall' || p.kind === 'cask',
    sfx: SFX.hitEnemy,
  }),
  t<StructureEventPayload>({
    event: Events.STRUCTURE_USED,
    note: 'E형 구조물 사용 → structureUseSfx (상점·저장·물약 소리 재사용, 임시)',
    sfx: (p) => structureUseSfx(p.kind),
  }),
  t<StructureFirePayload>({
    event: Events.STRUCTURE_FIRE,
    note: '불붙음: 독주 웅덩이 boss_fan · 무기·화살 dash (임시)',
    sfx: (p) => (p.target === 'pool' ? SFX.bossFan : p.target === 'burn' ? null : SFX.dash),
  }),
  t<StructureBellPayload>({
    event: Events.STRUCTURE_BELL,
    note: '판돈 종: 첫 타격(경고) boss_telegraph · 확정 boss_phase (임시)',
    sfx: (p) => (p.confirmed ? SFX.bossPhase : SFX.bossTelegraph),
  }),
  t({ event: Events.STRUCTURE_ROULETTE, note: '룰렛 회전 → menu_move (임시)', sfx: SFX.menuMove }),
  t({ event: Events.CHALLENGE_STARTED, note: '투견 링·흉패 도전 시작 → door_close (임시)', sfx: SFX.doorClose }),
  t<ChallengeEventPayload>({
    event: Events.CHALLENGE_CLEARED,
    note: '도전 끝: 시간 초과 menu_cancel · 그 외 trial_clear (임시)',
    sfx: (p) => (p.outcome === 'timeout' ? SFX.menuCancel : SFX.trialClear),
  }),
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
