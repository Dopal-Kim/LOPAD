/**
 * 이벤트 → 효과음 표 (음향↔시스템 계약 초안 `assets/audio/manifest.json` 의 trigger 제안을
 * 시스템 EventBus 이벤트 이름으로 확정한 것. 결정 로그 I·K).
 * 순수 데이터 — 재생은 systems/audio/audio.ts 가 이 표를 구독해서 처리한다.
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
  type BossBreakPayload,
  type BossLoopKind,
  type BossLoopPayload,
  type BossPhasePayload,
  type BossTelegraphPayload,
  type EnemyAttackPayload,
  type EnemyDamagedPayload,
  type EnemyTelegraphPayload,
  type MenuEventPayload,
  type PlayerAttackPayload,
  type PlayerChargePayload,
  type PlayerDamagedPayload,
  type PlayerFollowUpPayload,
  type PlayerSecondaryPayload,
  type PlayerSkillPayload,
  type GuardReleasedPayload,
  type TrialClearedPayload,
  type WeaponGaugePayload,
  type WeaponResourcePayload,
} from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { BUNDLE2 } from '../../data/bundle2';
import { t, type AudioTrigger } from './audioTrigger';
import { MOVE_AUDIO_TRIGGERS } from './audioMoves';
import { BUILD_AUDIO_TRIGGERS, BUILD_SFX, hasBranch, isRapidVolley, katanaThrustSfx } from './audioBuild';
export type { AudioTrigger } from './audioTrigger';

/** 61 단계 2·3 음향: 전용 소리가 있는 적 (공용 enemy_hurt·enemy_death·<id>_telegraph 대신) */
export const ENEMY_OWN_SFX: Record<string, { hurt?: string; death?: string; telegraph?: string }> = {
  peddler: { hurt: 'sfx/peddler_hurt', death: 'sfx/peddler_death', telegraph: 'sfx/peddler_wick' },
  porter: { hurt: 'sfx/porter_hurt', death: 'sfx/porter_death', telegraph: 'sfx/porter_windup' },
};
/** 61 단계 2: ENEMY_ATTACK phase → 효과음 (행상 착탄은 화염 술병 소모품과 같은 bottle_burst) */
export const ENEMY_PHASE_SFX: Record<string, string> = {
  throw: 'sfx/peddler_throw',
  burst: 'sfx/bottle_burst',
  push: 'sfx/porter_push',
  return: 'sfx/barrel_return',
  break: 'sfx/porter_barrel_break',
  spill: 'sfx/porter_liquor_spill',
};
const ENEMY_ROLL_LOOP = 'sfx/porter_barrel_roll';
const ENEMY_ROLL_LOOP_FADE_MS = 80;

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
  /** 61라운드 계약 sound §9 */
  guardBlock: 'sfx/guard_block',
  /** 61 단계 2·3: 대검 일반 가드 막음 (guard_block 대신) */
  guardBlockHeavy: 'sfx/guard_block_heavy',
  comboFinish: 'sfx/combo_finish',
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
    // 61라운드 단계 2·3 음향 (계약 sound §9 — 대체 관계: entrance↔boss_start · die↔boss_die · phase_drink/blackout↔boss_phase ·
    // dash_telegraph↔boss_telegraph · break_reel↔fall(파훼 인정 시). cup_shatter 는 보관 — 연결 끊음)
    entrance: 'sfx/boss1_entrance',
    phaseBlackout: 'sfx/boss1_phase_blackout',
    die: 'sfx/boss1_die',
    dashTelegraph: 'sfx/boss1_dash_telegraph',
    dash: 'sfx/boss1_dash',
    slamTelegraph: 'sfx/boss1_slam_telegraph',
    slam: 'sfx/boss1_slam',
    breakCup: 'sfx/boss1_break_cup',
    breakPillar: 'sfx/boss1_break_pillar',
    breakBarrel: 'sfx/boss1_break_barrel',
    breakReel: 'sfx/boss1_break_reel',
    barrelReturn: 'sfx/barrel_return',
    // 61 단계 4 음향: 아트 2 보스 동작 (BOSS_ACTION) — 포효는 entrance 와 함께, 균열은 파훼 알림 위에 겹쳐
    introRoar: 'sfx/boss1_intro_roar',
    cupStruck: 'sfx/boss1_cup_struck',
    pillarCrack1: 'sfx/boss1_pillar_crack1',
    pillarCrack2: 'sfx/boss1_pillar_crack2',
    pillarCrack3: 'sfx/boss1_pillar_crack3',
    flameSnuff: 'sfx/boss1_flame_snuff',
  },
} as const;

/** 61 단계 4: 기둥 균열 단(1~3) → 소리 (범위 밖은 끝으로 자른다) */
const PILLAR_CRACK_SFX = [SFX.boss1.pillarCrack1, SFX.boss1.pillarCrack2, SFX.boss1.pillarCrack3] as const;

/**
 * 55라운드 Q32 대검 홀드 차지·칼 잔상 베기 효과음 (음향 커밋 — `sfx/<키>`). **키 이름이 바뀌면 여기만 고친다.**
 * 함수 결과가 목록이면 로드된 첫 후보를 재생하고, 아무것도 없으면 무음 (매니페스트에 없어도 동작).
 */
export const CHARGE_SFX = {
  /** 홀드 인식(holdMs) — 차지 시작 */
  start: 'sfx/charge_start',
  /** 단계 도달 n = 1..4 (60라운드 거인 4단) */
  stage: (n: number): readonly string[] => [`sfx/charge_stage${n}`],
  /** 차지 유지 루프 (시작 페이드 인 · 떼거나 취소 시 페이드 아웃) */
  loop: 'sfx/charge_loop',
  /** 차지 내려찍기 n단 — 0ms = 타격 순간이라 판정(impact) 프레임에 재생. 단계 파일이 없으면 공용 charge_slam */
  slam: (n: number): readonly string[] => [`sfx/charge_slam_lv${n}`, 'sfx/charge_slam'],
  loopFadeInMs: 150,
  /** 떼거나(release)·1단 전에 뗌·대쉬·가드 등 취소 */
  loopFadeOutMs: 120,
  /** 피격 취소 (음향 권장 60ms) */
  loopFadeOutHurtMs: 60,
  stages: 4,
  /** 56라운드: 차지 유지음 음높이 — 단계 1·2·3 (시작 = 1.0) · 60라운드 거인 4단 1.09 */
  loopRates: [1.0, 1.03, 1.06, 1.09],
} as const;

/**
 * 55라운드 §17 후속 판정 → 효과음 (키 `<무기>:<followUps[].id>`). 없는 항목은 무음 — 대검 3단 링은 charge_slam_lv3 에 포함.
 * 60라운드 Q6: 칼 잔상 베기 katana_echo 는 보관(연결하지 않음 — audioBuild ARCHIVED_SFX)
 */
export const FOLLOW_UP_SFX: Readonly<Record<string, readonly string[]>> = {};

/**
 * 56라운드 무기 피드백 효과음 (음향 매니페스트 sfx/<키> — 파일이 없는 키는 조용히 건너뛴다). **키 이름이 바뀌면 여기만 고친다.**
 */
export const WEAPON_SFX = {
  perfectGuard: 'sfx/perfect_guard',
  parryPerfect: 'sfx/parry_perfect',
  groggyStart: 'sfx/groggy_start',
  kenkiStage: (n: number) => `sfx/kenki_stage${n}`,
  utbunFull: 'sfx/utbun_full',
  brandApply: 'sfx/brand_apply',
  brandBurst: 'sfx/brand_burst',
  overheatBurst: 'sfx/overheat_burst',
  breathFocus: 'sfx/breath_focus',
  issenDash: 'sfx/issen_dash',
  issenBurst: 'sfx/issen_burst',
  shadowClone: 'sfx/shadow_clone',
  gsDrag: 'sfx/gs_drag',
  bowReleaseWeak: 'sfx/bow_release_weak',
  bowReleasePerfect: 'sfx/bow_release_perfect',
  /** Q44 가득 당김 '틱' — 음향 추가 제작 예정(파일이 없으면 건너뜀) */
  bowFullDraw: 'sfx/bow_full_draw',
  /** Q44 오래 쥔 흔들림 루프 (흔들림 시작 페이드 인 · 놓으면 페이드 아웃) */
  bowStrain: 'sfx/bow_strain',
  bowStrainFadeInMs: 180,
  bowStrainFadeOutMs: 60,
  /** 균열 = 꽂히는 순간 + 이만큼 (음향 권장 0~40ms) */
  crackDelayMs: 40,
  /** 낙인 등 뒤 2스택 재생 속도 (음향 권장) */
  brandBackRate: 1.1,
  /** 검기 단 수 (60라운드: 4·5 단 — 각성 등) */
  kenkiStages: 5,
} as const;

/** 56라운드 효과음 전부 (검기 단 포함) — 매니페스트 점검 */
export function weaponSfxIds(): string[] {
  const out: string[] = [];
  for (const v of Object.values(WEAPON_SFX)) if (typeof v === 'string') out.push(v);
  for (let n = 1; n <= WEAPON_SFX.kenkiStages; n++) out.push(WEAPON_SFX.kenkiStage(n));
  return out;
}

/** 표의 페이로드 결정 효과음 전부 (매니페스트 대조 테스트용 — 없어도 무음이라 고정 id 목록과 분리) */
export function chargeSfxIds(): string[] {
  const out = new Set<string>([CHARGE_SFX.start, CHARGE_SFX.loop]);
  for (let n = 1; n <= CHARGE_SFX.stages; n++) {
    for (const id of CHARGE_SFX.stage(n)) out.add(id);
    for (const id of CHARGE_SFX.slam(n)) out.add(id);
  }
  for (const ids of Object.values(FOLLOW_UP_SFX)) for (const id of ids) out.add(id);
  return [...out].sort();
}

/** 54라운드: 3연 취권 n타(0부터) 재생 속도 (음향 권장 1.0 / 1.06 / 1.12) */
export const REEL_RATES = [1, 1.06, 1.12] as const;

/**
 * 54라운드: 보스 패턴 국면 → 효과음 (null = 없음). 대응표는 parts/system/CHANGELOG.md 54라운드 절.
 * index = 페이로드 index (61 단계 4: pillarCrack 의 새 균열 단 1~3)
 */
export function bossActionSfx(action: BossActionKind, index?: number): string | null {
  const B = SFX.boss1;
  switch (action) {
    case 'drinkLift':
      return B.drinkLift;
    case 'drinkFinish':
      return B.drinkFinish;
    case 'cupBreak':
      // 61라운드: 잔 깨짐 소리는 파훼(BOSS_BREAK cup → boss1_break_cup)가 맡는다 (cup_shatter 보관)
      return null;
    case 'reelTelegraph':
      return B.reelTelegraph;
    case 'reelDash':
      return B.reelDash;
    case 'fall':
      // 61라운드: 넘어짐은 파훼(reel)로 인정 → BOSS_BREAK reel → boss1_break_reel 이 대신 (1층 파훼 종류에 reel 이 없으면 fall)
      return BUNDLE2.break.kinds.includes('reel') ? null : B.fall;
    case 'kick':
      return B.barrelKick;
    case 'caskRedirect':
      // 61라운드: 술통 되치기 = 파훼 cask → boss1_break_barrel 과 함께 되돌아가는 소리
      return B.barrelReturn;
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
    // 61 단계 4: 등장 포효 · 잔 맞음(안 깨짐 — 깨지는 타는 cupStruck 이 아니라 파훼 boss1_break_cup) · 기둥 균열 단 · 불 꺼짐(변주 _v2·_v3)
    case 'introRoar':
      return B.introRoar;
    case 'cupStruck':
      return B.cupStruck;
    case 'pillarCrack':
      return PILLAR_CRACK_SFX[Math.min(PILLAR_CRACK_SFX.length, Math.max(1, Math.round(index ?? 1))) - 1];
    case 'flameSnuff':
      return B.flameSnuff;
    default:
      return null;
  }
}

/** 61라운드: 1층 보스 id */
function isBoss1(id: string | undefined): boolean {
  return id === 'stage1';
}

/** 61라운드: 결정타(BOSS_BREAK finisher — BOSS_DIED 직후 같은 프레임)의 break_finisher 뒤에 boss1_die 를 겹친다 (ms) */
export const BOSS1_DIE_DELAY_MS = 120;

/** 61라운드 파훼 종류 → 1층 파훼 효과음 (finisher 는 null — audioBuild 의 break_finisher) */
export function breakSfx(kind: string): string | null {
  const B = SFX.boss1;
  switch (kind) {
    case 'cup':
      return B.breakCup;
    case 'pillar':
      return B.breakPillar;
    case 'cask':
    case 'barrel':
      return B.breakBarrel;
    case 'reel':
      return B.breakReel;
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
  // --- 56라운드 2단계 새 기본기 (audioMoves) ---
  ...MOVE_AUDIO_TRIGGERS,
  // --- 주인공 공격·보조 동작 ---
  t<PlayerAttackPayload>({
    event: Events.PLAYER_ATTACKED,
    note: '공격: 근접은 무기별 swing(휘두름 2프레임 시작에 맞춤), 활은 bow_shot(3프레임 = 화살 생성), 조준 사격은 bow_aimed. 차지 내려찍기는 charge_slam_lv<n> 이 대신 (PLAYER_CHARGE release)',
    sfx: (p) => {
      const w = gameState.weapon.def;
      // 56라운드 Q9: 약한 화살은 bow_release_weak 가 대신 (PLAYER_SECONDARY release)
      // 60라운드: 속사 연사는 bow_rapid1~3 (audioBuild) 이 대신
      if (w.kind === 'ranged')
        return p.kind === 'aimed'
          ? p.bowPower === 'weak'
            ? null
            : SFX.bowAimed
          : isRapidVolley()
            ? null
            : SFX.bowShot;
      // 56라운드 2단계 새 기본기는 전용 소리(PLAYER_SKILL — audioMoves)가 대신
      if (p.charge !== undefined || p.move) return null;
      // 60라운드: 칼 3타 찌르기 = katana_thrust(검기 단 _ki1~3)
      if (gameState.weapon.id === 'katana' && p.art === 'thrust') return katanaThrustSfx(p.kenkiStage);
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
    note: '조준 사격 취소·56라운드 놓기 → bow_draw 정지 · 흔들림 루프 페이드 아웃',
    when: (p) => p.kind === 'aimedshot' && (p.phase === 'cancel' || p.phase === 'release'),
    stop: [SFX.bowDraw, WEAPON_SFX.bowStrain],
    stopFadeMs: WEAPON_SFX.bowStrainFadeOutMs,
  }),
  t<PlayerSecondaryPayload>({
    event: Events.PLAYER_SECONDARY,
    note: '56라운드 Q20·Q44 너무 오래 쥠 → bow_strain 루프 (페이드 인)',
    when: (p) => p.kind === 'aimedshot' && p.phase === 'strain',
    loop: WEAPON_SFX.bowStrain,
    loopFadeInMs: WEAPON_SFX.bowStrainFadeInMs,
  }),
  t<PlayerSecondaryPayload>({
    event: Events.PLAYER_SECONDARY,
    note: '56라운드 Q44 가득 당김 → bow_full_draw (음향 추가 예정 — 없으면 무음)',
    when: (p) => p.kind === 'aimedshot' && p.phase === 'ready',
    sfx: () => WEAPON_SFX.bowFullDraw,
  }),
  t<PlayerSecondaryPayload>({
    event: Events.PLAYER_SECONDARY,
    note: '56라운드 Q9 놓기: 약한 화살 → bow_release_weak · 완벽 → bow_release_perfect (bow_aimed 위에 겹침)',
    when: (p) => p.kind === 'aimedshot' && p.phase === 'release',
    sfx: (p) =>
      p.power === 'weak' ? WEAPON_SFX.bowReleaseWeak : p.power === 'perfect' ? WEAPON_SFX.bowReleasePerfect : null,
  }),
  t<PlayerSecondaryPayload>({
    event: Events.PLAYER_SECONDARY,
    note: '가드 시작 → guard_hold 루프',
    when: (p) => p.kind === 'guard' && p.phase === 'start',
    loop: SFX.guardHold,
  }),
  t<GuardReleasedPayload>({
    event: Events.PLAYER_GUARD_RELEASED,
    note: '가드 해제 → 루프 정지 + guard_push (56라운드 2단계: 돌진·반격·올려베기로 끝나면 밀쳐내기 소리 없음)',
    stop: [SFX.guardHold],
    when: (p) => !p?.quiet,
    sfx: SFX.guardPush,
  }),
  t<GuardReleasedPayload>({
    event: Events.PLAYER_GUARD_RELEASED,
    note: '56라운드 2단계: 조용한 가드 해제 → 루프 정지만',
    when: (p) => Boolean(p?.quiet),
    stop: [SFX.guardHold],
  }),
  // --- 55라운드 Q32 대검 홀드 차지 · 칼 잔상 베기 (CHARGE_SFX · FOLLOW_UP_SFX) ---
  t<PlayerChargePayload>({
    event: Events.PLAYER_CHARGE,
    note: '차지 시작(홀드 인식) → charge_start + charge_loop 루프(페이드 인 150ms)',
    when: (p) => p.phase === 'start',
    sfx: () => CHARGE_SFX.start,
    loopOf: () => CHARGE_SFX.loop,
    loopFadeInMs: CHARGE_SFX.loopFadeInMs,
  }),
  t<PlayerChargePayload>({
    event: Events.PLAYER_CHARGE,
    note: '차지 단계 n → charge_stage<n> · 56라운드: 유지음 음높이 단계 1.0/1.03/1.06',
    when: (p) => p.phase === 'stage',
    sfx: (p) => CHARGE_SFX.stage(p.stage),
    loopRate: (p) => ({
      id: CHARGE_SFX.loop,
      rate: CHARGE_SFX.loopRates[Math.min(p.stage, CHARGE_SFX.loopRates.length) - 1] ?? 1,
    }),
  }),
  t<PlayerChargePayload>({
    event: Events.PLAYER_CHARGE,
    note: '떼거나 취소 → charge_loop 페이드 아웃 (피격 취소 60ms, 그 밖 120ms)',
    when: (p) => p.phase === 'release' || p.phase === 'cancel',
    stopOf: () => [CHARGE_SFX.loop],
    stopFadeMs: (p) => (p.reason === 'hurt' ? CHARGE_SFX.loopFadeOutHurtMs : CHARGE_SFX.loopFadeOutMs),
  }),
  t<PlayerChargePayload>({
    event: Events.PLAYER_CHARGE,
    note: '차지 내려찍기 → charge_slam_lv<n> (판정 프레임 = impactDelayMs 에, swing_greatsword 대신)',
    when: (p) => p.phase === 'release' && p.stage > 0,
    sfx: (p) => CHARGE_SFX.slam(p.stage),
    delayMs: (p) => p.impactDelayMs ?? 0,
  }),
  // --- 56라운드 무기 피드백 (WEAPON_SFX) ---
  t<PlayerChargePayload>({
    event: Events.PLAYER_CHARGE,
    note: '58라운드 Q3 휘둘러 내리찍은 자리에서 커서까지 균열 → 60라운드 gs_crack_line_lv<n> (내리찍기 + 40ms, 1~3단만 — 60 Q40 거인 4단은 charge_slam_lv4 하나만 · 중압(weight) 런은 균열 대신 원형 진동이라 무음 · gs_crack·gs_plunge 는 보관)',
    when: (p) => p.phase === 'release' && p.stage > 0 && p.stage <= BUILD_SFX.tiers && !hasBranch('weight'),
    sfx: (p) => BUILD_SFX.gsCrackLine(p.stage),
    delayMs: (p) => (p.impactDelayMs ?? 0) + WEAPON_SFX.crackDelayMs,
  }),
  t({ event: Events.PLAYER_PERFECT_GUARD, note: '56라운드 Q7 퍼펙트 가드', sfx: WEAPON_SFX.perfectGuard }),
  t({
    event: Events.PLAYER_PARRIED,
    note: '56라운드 칼 패링 강조 (기존 parry 위에 겹침, PARRY 문구·검기 1단)',
    when: () => gameState.weapon.id === 'katana',
    sfx: WEAPON_SFX.parryPerfect,
  }),
  t<WeaponResourcePayload>({
    event: Events.WEAPON_RESOURCE,
    note: '56라운드 Q7 그로기 시작 (칼·대검 기력 0)',
    when: (p) => p.event === 'groggy',
    sfx: WEAPON_SFX.groggyStart,
  }),
  t<WeaponGaugePayload>({
    event: Events.WEAPON_GAUGE,
    note: '56라운드 검기 단 도달 → kenki_stage<n> · 울분 가득 → utbun_full · 낙인 → brand_apply(등 뒤 rate 1.1) · 숨 집중 → breath_focus',
    sfx: (p) =>
      p.gauge === 'kenki' && p.event === 'stage' && (p.stage ?? 0) > 0
        ? WEAPON_SFX.kenkiStage(p.stage!)
        : p.gauge === 'grudge' && p.event === 'full'
          ? WEAPON_SFX.utbunFull
          : p.gauge === 'brand' && p.event === 'apply'
            ? WEAPON_SFX.brandApply
            : p.gauge === 'breath' && p.event === 'focusStart'
              ? WEAPON_SFX.breathFocus
              : null,
    rate: (p) => (p.gauge === 'brand' && p.back ? WEAPON_SFX.brandBackRate : 1),
  }),
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '56라운드 전용 동작: 일섬 돌진·분신·터짐 · 낙인 폭발 · 과열 일괄 폭발 · 대검 끌림',
    sfx: (p) =>
      p.move === 'issen'
        ? p.phase === 'dash'
          ? WEAPON_SFX.issenDash
          : p.phase === 'clone'
            ? WEAPON_SFX.shadowClone
            : p.phase === 'burst'
              ? WEAPON_SFX.issenBurst
              : null
        : p.move === 'brand'
          ? WEAPON_SFX.brandBurst
          : p.move === 'overheat'
            ? hasBranch('heatwave')
              ? [BUILD_SFX.daggerHotwindBurst, WEAPON_SFX.overheatBurst]
              : WEAPON_SFX.overheatBurst
            : p.move === 'drag'
              ? WEAPON_SFX.gsDrag
              : null,
  }),
  t<PlayerFollowUpPayload>({
    event: Events.PLAYER_FOLLOW_UP,
    note: '후속 판정 시각 → FOLLOW_UP_SFX (칼 잔상 베기 katana_echo)',
    sfx: (p) => FOLLOW_UP_SFX[`${p.weapon}:${p.id}`] ?? null,
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
    note: '적 피격 보조음 enemy_hurt (틱 포함, 피격음과 겹침) · 61 단계 2: 행상·짐꾼은 전용 <id>_hurt 로 대체',
    sfx: (p) => ENEMY_OWN_SFX[p.id]?.hurt ?? SFX.enemyHurt,
  }),
  t<{ id?: string; elite?: boolean }>({
    event: Events.ENEMY_DIED,
    note: '일반 적 사망 (60라운드 엘리트 = elite_die)',
    sfx: (p) => {
      const own = ENEMY_OWN_SFX[p?.id ?? '']?.death ?? SFX.enemyDeath;
      return p?.elite ? [BUILD_SFX.eliteDie, own] : own;
    },
  }),
  t<PlayerDamagedPayload>({
    event: Events.PLAYER_DAMAGED,
    note: '주인공 피격 · 61라운드 §9: 가드로 막은 피격(guarded)은 guard_block',
    sfx: (p) =>
      p?.guarded ? (gameState.weapon?.id === 'greatsword' ? SFX.guardBlockHeavy : SFX.guardBlock) : SFX.hitPlayer,
  }),
  t({ event: Events.PLAYER_COMBO_FINISH, note: '61라운드 §9: 연격 마지막 타 적중 (활 제외)', sfx: SFX.comboFinish }),
  t({ event: Events.PLAYER_DIED, note: '주인공 사망', sfx: SFX.playerDeath }),
  t<EnemyTelegraphPayload>({
    event: Events.ENEMY_TELEGRAPH,
    note: '적 돌진 예고 → sfx/<적id>_telegraph (결사병 charger_telegraph) · 61 단계 2: 행상 심지 peddler_wick · 짐꾼 porter_windup',
    sfx: (p) => ENEMY_OWN_SFX[p.id]?.telegraph ?? SFX.enemyTelegraph(p.id),
  }),
  t<EnemyAttackPayload>({
    event: Events.ENEMY_ATTACK,
    note: '적 공격 실행 → dash 는 sfx/<적id>_dash(결사병), shot 은 sfx/<적id>_shot(사수, 총구 프레임에 맞춘 발사 시점). 접촉 공격은 없음',
    when: (p) => !p.phase,
    sfx: (p) => (p.kind === 'dash' ? SFX.enemyDash(p.id) : p.kind === 'shot' ? SFX.enemyShot(p.id) : null),
  }),
  t<EnemyAttackPayload>({
    event: Events.ENEMY_ATTACK,
    note: '61 단계 2 행상·짐꾼 단계(phase): throw·burst(bottle_burst)·push·return·break·spill (ENEMY_PHASE_SFX)',
    when: (p) => Boolean(p.phase && p.phase !== 'rollEnd'),
    sfx: (p) => ENEMY_PHASE_SFX[p.phase ?? ''] ?? null,
  }),
  t<EnemyAttackPayload>({
    event: Events.ENEMY_ATTACK,
    note: '61 단계 2 짐꾼 술통 놓음 → porter_barrel_roll 루프 (되친 술통도 같은 루프)',
    when: (p) => p.phase === 'push',
    loop: ENEMY_ROLL_LOOP,
  }),
  t<EnemyAttackPayload>({
    event: Events.ENEMY_ATTACK,
    note: '61 단계 2 굴러가는 술통이 다 깨짐 → 굴림 루프 80ms 페이드',
    when: (p) => p.phase === 'rollEnd',
    stop: [ENEMY_ROLL_LOOP],
    stopFadeMs: ENEMY_ROLL_LOOP_FADE_MS,
  }),

  // --- 보스 ---
  t<{ boss: string }>({
    event: Events.BOSS_STARTED,
    note: '보스 등장 (61라운드: 1층 = boss1_entrance, 그 밖 boss_start)',
    sfx: (p) => (p.boss === 'stage1' ? SFX.boss1.entrance : SFX.bossStart),
  }),
  t<BossTelegraphPayload>({
    event: Events.BOSS_TELEGRAPH,
    note: '보스 돌진·내리찍기 예고 (61라운드: 1층 = boss1_dash_telegraph · boss1_slam_telegraph)',
    when: (p) => p.attack === 'dash' || (p.attack === 'slam' && isBoss1(p.id)),
    sfx: (p) =>
      isBoss1(p.id) ? (p.attack === 'dash' ? SFX.boss1.dashTelegraph : SFX.boss1.slamTelegraph) : SFX.bossTelegraph,
  }),
  t<BossAttackPayload>({
    event: Events.BOSS_ATTACK,
    note: '61라운드 1층 돌진·내리찍기 실행 → boss1_dash · boss1_slam',
    when: (p) => isBoss1(p.id) && (p.attack === 'dash' || p.attack === 'slam'),
    sfx: (p) => (p.attack === 'dash' ? SFX.boss1.dash : SFX.boss1.slam),
  }),
  t<BossAttackPayload>({
    event: Events.BOSS_ATTACK,
    note: '보스 부채꼴 투사체 (돌진 실행음은 자산 없음)',
    when: (p) => p.attack === 'fan',
    sfx: SFX.bossFan,
  }),
  t<BossPhasePayload>({
    event: Events.BOSS_PHASE,
    note: '보스 국면 전환 (61라운드 1층: 2국면 boss1_phase_drink · 3국면 boss1_phase_blackout, 그 밖 boss_phase)',
    sfx: (p) =>
      gameState.stage?.boss === 'stage1'
        ? p.phase >= 3
          ? SFX.boss1.phaseBlackout
          : SFX.boss1.phaseDrink
        : SFX.bossPhase,
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
    sfx: (p) => bossActionSfx(p.action, p.index),
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
  t<{ id: string }>({
    event: Events.BOSS_DIED,
    note: '보스 사망 (61라운드 1층 = boss1_die — 결정타면 break_finisher 뒤에 겹치게 지연)',
    sfx: (p) => (isBoss1(p.id) ? SFX.boss1.die : SFX.bossDie),
    delayMs: (p) => (isBoss1(p.id) ? BOSS1_DIE_DELAY_MS : 0),
  }),
  t<BossBreakPayload>({
    event: Events.BOSS_BREAK,
    note: '61라운드 1층 파훼 종류별 → boss1_break_cup·pillar·barrel·reel (결정타·새 종류 수는 audioBuild)',
    sfx: (p) => breakSfx(p.kind),
  }),

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
  t<{ source?: string }>({
    event: Events.PLAYER_HEALED,
    note: '60라운드: 독주 회복만 potion_use (PLAYER_HEALED{source:potion} — 휴식·상점·이벤트 회복에는 없음)',
    when: (p) => p?.source === 'potion',
    sfx: SFX.potionUse,
  }),
  t<{ group?: string }>({
    event: Events.SHOP_BOUGHT,
    note: '상점 구매 (60라운드: 진열 바꾸기 shop_reroll · 지도 정보 map_info_buy)',
    sfx: (p) =>
      p?.group === 'reroll' ? BUILD_SFX.shopReroll : p?.group === 'mapInfo' ? BUILD_SFX.mapInfoBuy : SFX.shopBuy,
  }),

  // --- 연출·UI ---
  t({ event: Events.FATE_DECIDED, note: '운명(무기) 결정', sfx: SFX.fateDecided }),
  t({
    event: Events.ENDING_CHOSEN,
    note: '엔딩 선택 — 전용 자산이 없어 fate_decided(일기장 덮는 소리) 재사용 (임시)',
    sfx: SFX.fateDecided,
  }),
  // 61 G (sound §10): 1차·2차 각성 · 개성 발현 · 게이지 반짝 · 단련 — audioBuild GROWTH_AUDIO_TRIGGERS
  t({ event: Events.WEAPON_TEMPERED, note: '단련 (옛 강화 소리)', sfx: SFX.reinforce }),
  t<MenuEventPayload>({
    event: Events.MENU_OPENED,
    note: '메뉴 열림 → menu_move (같은 메뉴를 다시 그리는 reopen 은 제외)',
    when: (p) => !p.reopen,
    sfx: SFX.menuMove,
  }),
  t<MenuEventPayload>({
    event: Events.MENU_SELECTED,
    note: '메뉴 선택 (60라운드 이벤트 노드 메뉴 = event_choice)',
    sfx: (p) => (p?.id === 'event' ? [BUILD_SFX.eventChoice, SFX.menuSelect] : SFX.menuSelect),
  }),

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
    note: '불붙음: 독주 웅덩이 boss_fan(임시) · 무기·화살 = 60라운드 증류기 점화 still_ignite',
    sfx: (p) => (p.target === 'pool' ? SFX.bossFan : p.target === 'burn' ? null : [BUILD_SFX.stillIgnite, SFX.dash]),
  }),
  t<StructureBellPayload>({
    event: Events.STRUCTURE_BELL,
    note: '판돈 종: 첫 타격(경고) boss_telegraph · 확정 boss_phase (임시)',
    sfx: (p) => (p.confirmed ? SFX.bossPhase : SFX.bossTelegraph),
  }),
  t({ event: Events.STRUCTURE_ROULETTE, note: '룰렛 회전 → menu_move (임시)', sfx: SFX.menuMove }),
  t<ChallengeEventPayload>({
    event: Events.CHALLENGE_STARTED,
    note: '투견 링·흉패 도전 시작 → door_close (임시 — 성소 깃발은 audioBuild)',
    when: (p) => p.kind !== 'warFlag',
    sfx: SFX.doorClose,
  }),
  t<ChallengeEventPayload>({
    event: Events.CHALLENGE_CLEARED,
    note: '도전 끝: 시간 초과 menu_cancel · 그 외 trial_clear (임시 — 성소 깃발은 audioBuild)',
    when: (p) => p.kind !== 'warFlag',
    sfx: (p) => (p.outcome === 'timeout' ? SFX.menuCancel : SFX.trialClear),
  }),
  t<MenuEventPayload>({
    event: Events.MENU_CLOSED,
    note: '선택 없이 닫힘(상점 이탈 등) → menu_cancel',
    when: (p) => !p.selected,
    sfx: SFX.menuCancel,
  }),
  // --- 60라운드 빌드·갈래·패시브·2차 묶음 (audioBuild) ---
  ...BUILD_AUDIO_TRIGGERS,
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
