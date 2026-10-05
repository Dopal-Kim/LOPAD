/**
 * 60라운드 효과음 연결 — 57·58라운드 빌드 37종 + 60라운드 2차 묶음·갈래·패시브 67종 (계약 sound-assets §6, 음향 manifest trigger 제안을
 * 시스템 EventBus 이름·실제 id 로 확정한 것). 순수 데이터 — 재생은 audio.ts 가 AUDIO_TRIGGERS(audioMap) 로 구독한다.
 * 음향 임시 id ↔ 시스템 id 차이는 `SOUND_ID_ALIASES` (음향이 manifest 를 시스템 id 로 맞춘다).
 * 보관 3종(gs_plunge·gs_crack·katana_echo — 60 Q6)은 연결하지 않는다 (`ARCHIVED_SFX`).
 */
import {
  Events,
  type BossBreakPayload,
  type BranchEffectPayload,
  type ChallengeEventPayload,
  type ConsumablePayload,
  type CurseGainedPayload,
  type ElitePrefixPayload,
  type EndureTriggeredPayload,
  type MarkChangedPayload,
  type NodeGradedPayload,
  type PassiveProcPayload,
  type PerfectSuccessPayload,
  type PlayerAttackPayload,
  type PlayerBranchMovePayload,
  type PlayerSkillPayload,
  type SetEffectPayload,
  type StatusBurstPayload,
  type StatusChangedPayload,
  type TagSetChangedPayload,
  type WeaponEvolvedPayload,
} from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { currentAttackTag } from '../build/attackTags';
import { t, type AudioTrigger } from './audioTrigger';

const s = (name: string): string => `sfx/${name}`;

/** 보관 (60라운드 Q6 — 파일·manifest 항목은 남기되 연결하지 않음) */
export const ARCHIVED_SFX: readonly string[] = [s('gs_plunge'), s('gs_crack'), s('katana_echo')];

export const BUILD_SFX = {
  setTier: (n: number) => s(`set_tier${n}`),
  dualTrait: s('dual_trait'),
  curseTake: s('curse_take'),
  curseEnd: s('curse_end'),
  bloodPact: s('blood_pact'),
  perfectEvade: s('perfect_evade'),
  awaken: (weapon: string) => s(`awaken_${weapon}`),
  markStack: s('mark_stack'),
  boilBurst: s('boil_burst'),
  stillness: s('stillness'),
  drunkIgnite: s('drunk_ignite'),
  drunkSway: s('drunk_sway'),
  endure: s('endure_trigger'),
  // 칼
  katanaSpinReady: s('katana_spin_ready'),
  katanaSpin: s('katana_spin'),
  katanaGuardbreakHold: s('katana_guardbreak_hold'),
  katanaGuardbreak: s('katana_guardbreak'),
  katanaThrust: s('katana_thrust'),
  katanaThrustKi: (n: number) => s(`katana_thrust_ki${n}`),
  katanaWhirlLoop: s('katana_whirl_loop'),
  katanaWhirlReflect: s('katana_whirl_reflect'),
  katanaMoonTrail: s('katana_moon_trail'),
  katanaCleaveCrack: s('katana_cleave_crack'),
  katanaExecute: s('katana_execute'),
  katanaMirrorParry: s('katana_mirror_parry'),
  // 대검
  gsCrackLine: (n: number) => s(`gs_crack_line_lv${n}`),
  gsQuakeRing: s('gs_quake_ring'),
  gsShatterSnuff: s('gs_shatter_snuff'),
  gsQuakeFork: s('gs_quake_fork'),
  gsEchoCounter: s('gs_echo_counter'),
  gsCongestLoop: s('gs_congest_loop'),
  gsCongestBurst: s('gs_congest_burst'),
  // 단검
  daggerFanThrow: s('dagger_fan_throw'),
  daggerFlyknifeThrow: s('dagger_flyknife_throw'),
  daggerCrossClone: s('dagger_cross_clone'),
  daggerFrenzyIn: s('dagger_frenzy_in'),
  daggerFrenzyOut: s('dagger_frenzy_out'),
  daggerBleed: s('dagger_bleed'),
  daggerBrandHop: s('dagger_brand_hop'),
  daggerKnifeStick: s('dagger_knife_stick'),
  daggerKnifeStep: s('dagger_knife_step'),
  daggerHotwindLoop: s('dagger_hotwind_loop'),
  daggerHotwindBurst: s('dagger_hotwind_burst'),
  // 활
  bowRapid: (n: number) => s(`bow_rapid${n}`),
  bowPierce: s('bow_pierce'),
  bowArrowSplit: s('bow_arrow_split'),
  bowArrowRecall: s('bow_arrow_recall'),
  bowDeadeyeLock: s('bow_deadeye_lock'),
  bowDeadeyeHold: s('bow_deadeye_hold'),
  bowLink: (n: number) => s(`bow_link${n}`),
  bowLinkBreak: s('bow_link_break'),
  bowSkypierce: s('bow_skypierce'),
  // 2차 묶음
  eliteAppear: s('elite_appear'),
  eliteArmorBreak: s('elite_armor_break'),
  eliteEnrage: s('elite_enrage'),
  eliteDrink: s('elite_drink'),
  eliteLeaderDown: s('elite_leader_down'),
  eliteDie: s('elite_die'),
  shrineActivate: s('shrine_activate'),
  shrineClear: s('shrine_clear'),
  shrineFail: s('shrine_fail'),
  gradePerfect: s('grade_perfect'),
  gradeGood: s('grade_good'),
  shopReroll: s('shop_reroll'),
  mapInfoBuy: s('map_info_buy'),
  bottleThrow: s('bottle_throw'),
  bottleBurst: s('bottle_burst'),
  strongDrink: s('strong_drink'),
  coldWater: s('cold_water'),
  eventEnter: s('event_enter'),
  eventChoice: s('event_choice'),
  hiddenNodeFound: s('hidden_node_found'),
  breakCount: s('break_count'),
  breakFinisher: s('break_finisher'),
  stillIgnite: s('still_ignite'),
  fireWeaponLoop: s('fire_weapon_loop'),
  fireWeaponEnd: s('fire_weapon_end'),
  /** 단 수: 세트 3단(2·4·6) · 찌르기 검기 3 · 속사 3 · 연결 3 · 균열 줄 3 */
  tiers: 3,
  /** 루프 끝 페이드 ms (음향 권장 80~150) */
  loopFadeMs: 100,
  /** 가드 불가 내려베기 소리 = 판정 앞 ms (음향 §6) */
  guardbreakLeadMs: 100,
  /** 회전 베기 2회전 재생 속도 */
  spinSecondRate: 1.06,
} as const;

/** 패시브 id → 효과음 (harshBreath 는 술불 위면 fire_breath) */
export const PASSIVE_SFX: Readonly<Record<string, string>> = {
  brokenShard: s('passive_glass_shard'),
  burningSleeve: s('passive_ember_sleeve'),
  bloodScent: s('passive_blood_scent'),
  domino: s('passive_domino'),
  brokenMirror: s('passive_mirror_clone'),
  emberHeart: s('passive_ember_heart'),
  spilledDrink: s('passive_spilled_drink'),
  harshBreath: s('passive_liquor_spray'),
  drunkFist: s('passive_drunk_fist'),
};
const HARSH_BREATH_FIRE = s('passive_fire_breath');

/** 갈래 효과 `<노드 id>:<효과>` → 효과음 (단 수가 있는 연결은 따로) */
export const BRANCH_EFFECT_SFX: Readonly<Record<string, string>> = {
  'zangetsu:trail': BUILD_SFX.katanaMoonTrail,
  'cleave:execute': BUILD_SFX.katanaExecute,
  'meikyo:parry': BUILD_SFX.katanaMirrorParry,
  /** 60 Q40: 중압 1~3단 원형 진동 (stack = 단). 거인 4단은 이벤트 없음 — charge_slam_lv4 하나만 */
  'weight:ring': BUILD_SFX.gsQuakeRing,
  'quake:fork': BUILD_SFX.gsQuakeFork,
  'resonance:counter': BUILD_SFX.gsEchoCounter,
  'clot:burst': BUILD_SFX.gsCongestBurst,
  'dance:clone_in': BUILD_SFX.daggerFrenzyIn,
  'dance:clone_out': BUILD_SFX.daggerFrenzyOut,
  'bleed:bleed': BUILD_SFX.daggerBleed,
  'twinBrand:transfer': BUILD_SFX.daggerBrandHop,
  'flyknife:stick': BUILD_SFX.daggerKnifeStick,
  'flyknife:step': BUILD_SFX.daggerKnifeStep,
  'volley:split': BUILD_SFX.bowArrowSplit,
  'quiver:recall': BUILD_SFX.bowArrowRecall,
  'deadeye:lock': BUILD_SFX.bowDeadeyeLock,
  'skypierce:link_break': BUILD_SFX.bowLinkBreak,
  'skypierce:line': BUILD_SFX.bowSkypierce,
};

/** 루프 갈래 효과 (시작 · 끝) */
const BRANCH_LOOPS: Readonly<Record<string, { start: string; end: string; id: string }>> = {
  clot: { start: 'hold', end: 'end|burst', id: BUILD_SFX.gsCongestLoop },
  heatwave: { start: 'trail_start', end: 'trail_end', id: BUILD_SFX.daggerHotwindLoop },
  deadeye: { start: 'hold_start', end: 'hold_end', id: BUILD_SFX.bowDeadeyeHold },
};

/**
 * 음향 임시 id(manifest trigger.when) ↔ 시스템 실제 id (보고용 — 음향이 manifest 를 고친다).
 * 키 = 음향 쪽, 값 = 시스템 쪽
 */
export const SOUND_ID_ALIASES: Readonly<Record<string, string>> = {
  'passive:brokenGlass': 'passive:brokenShard',
  'passive:strongBreath': 'passive:harshBreath',
  'prefix:drinker': 'prefix:guzzler',
  'prefix:leader': 'prefix:ringleader',
  'branch:moon': 'branch:zangetsu',
  'branch:mirror': 'branch:meikyo',
  'branch:echo': 'branch:resonance',
  'branch:congest': 'branch:clot',
  'branch:frenzy': 'branch:dance',
  'branch:hotwind': 'branch:heatwave',
  'branch:split': 'branch:volley',
  'branch:pressure': 'branch:giant',
  'branch:bleed(transfer)': 'branch:twinBrand',
  'ROOM_ENTERED{type:event}': 'EVENT_NODE_ENTERED',
  'BOSS_DIED{finisher:true}': 'BOSS_BREAK{kind:finisher}',
  'STRUCTURE_USED{kind:still}': 'STRUCTURE_FIRE{target:weapon|arrow}',
  KENKI_CHANGED: 'WEAPON_GAUGE{gauge:kenki,event:stage}',
  'GROGGY{branch:congest}': 'BRANCH_EFFECT{branch:clot,effect:hold|end|burst}',
  'OVERHEAT{branch:hotwind}':
    'BRANCH_EFFECT{branch:heatwave,effect:trail_start|trail_end} · PLAYER_SKILL{move:overheat}',
  'BREATH_FOCUS{branch:deadeye}': 'BRANCH_EFFECT{branch:deadeye,effect:lock|hold_start|hold_end}',
  'PLAYER_ATTACK{move:rapid}': 'PLAYER_ATTACKED (속사 연사 — attackTags rapidVolley, 1→2→3 순환)',
  'PLAYER_CHARGE{part:quake|fork}': 'BRANCH_EFFECT{branch:weight,effect:ring,stack:1~3} · {branch:quake,effect:fork}',
  'PERFECT_GUARD{branch:echo}': 'BRANCH_EFFECT{branch:resonance,effect:counter}',
  'PARRY_SUCCESS{branch:mirror}': 'BRANCH_EFFECT{branch:meikyo,effect:parry}',
  'PLAYER_SECONDARY{target:knife}': 'BRANCH_EFFECT{branch:flyknife,effect:step}',
  'BRAND_BURST{branch:bleed}': 'BRANCH_EFFECT{branch:bleed,effect:bleed}',
  'PLAYER_SKILL{move:guardbreak,phase:hold}': 'PLAYER_BRANCH_MOVE{move:unblockable,phase:hold}',
  // --- 60라운드 manifest(9e897ec, 시스템 이름으로 고친 뒤) 남은 불일치: 키 = manifest trigger 지금 값, 값 = 시스템 실제 ---
  'BRANCH_EFFECT{branch:heatwave,effect:trail}':
    'BRANCH_EFFECT{branch:heatwave,effect:trail_start} 루프 시작 · {effect:trail_end} 루프 끝',
  'BRANCH_EFFECT{branch:heatwave,effect:burst}':
    'PLAYER_SKILL{weapon:dagger,move:overheat,phase:burst} + 경로에 heatwave',
  'BRANCH_EFFECT{branch:deadeye,effect:hold}':
    'BRANCH_EFFECT{branch:deadeye,effect:hold_start} 루프 시작 · {effect:hold_end} 루프 끝',
  'BRANCH_EFFECT{branch:clot,effect:hold}':
    'BRANCH_EFFECT{branch:clot,effect:hold} 루프 시작 · {effect:end|burst} 루프 끝 (일치)',
  'PLAYER_CHARGE{branch:giant,part:quake}': '없음 (60 Q40 — 거인 4단은 charge_slam_lv4 하나만)',
  'PLAYER_CHARGE{branch:quake,part:fork}': 'BRANCH_EFFECT{branch:quake,effect:fork}',
  'PARRY_SUCCESS{weapon:katana,branch:meikyo}': 'BRANCH_EFFECT{branch:meikyo,effect:parry}',
  'PERFECT_GUARD{weapon:greatsword,branch:resonance}': 'BRANCH_EFFECT{branch:resonance,effect:counter}',
  'BRAND_BURST{branch:twinBrand}': 'BRANCH_EFFECT{branch:bleed,effect:bleed} (dagger_bleed)',
  'PLAYER_SECONDARY{kind:shadowstep,target:knife}': 'BRANCH_EFFECT{branch:flyknife,effect:step}',
  'PLAYER_ATTACK{move:rapid,branch:volley,phase:split}': 'BRANCH_EFFECT{branch:volley,effect:split}',
  'PLAYER_SKILL{weapon:dagger,move:fan_throw,branch:flyknife}':
    'PLAYER_SKILL{weapon:dagger,move:fan_throw} + 경로에 flyknife (페이로드에 branch 키 없음)',
  'WEAPON_GAUGE{stage:n,delta>0}':
    'WEAPON_GAUGE{weapon:katana,gauge:kenki,event:stage,stage:n} (오를 때만 — 내릴 때는 event:consume)',
  'UTBUN_CHANGED{full:true}': 'WEAPON_GAUGE{weapon:greatsword,gauge:grudge,event:full}',
  'BRAND_CHANGED{delta>0}': 'WEAPON_GAUGE{weapon:dagger,gauge:brand,event:apply,back?} (등 뒤 rate 1.1)',
  BRAND_BURST: 'PLAYER_SKILL{weapon:dagger,move:brand,phase:burst}',
  'OVERHEAT{full:true}': 'PLAYER_SKILL{weapon:dagger,move:overheat,phase:burst}',
  'BREATH_FOCUS{phase:start}': 'WEAPON_GAUGE{weapon:bow,gauge:breath,event:focusStart}',
  'GROGGY{phase:start}': 'WEAPON_RESOURCE{event:groggy}',
  // --- 60라운드 Q33~Q35 후속 확인 (dada3f8 기준 manifest): 아래는 시스템 실제 — 일치하는 것은 '(일치)' ---
  'BRANCH_EFFECT{branch:twinBrand,effect:transfer}':
    'BRANCH_EFFECT{branch:twinBrand,effect:transfer} (일치 — twinBrand = 이중 개성 id, 쌍격 분신 교차 뒤 낙인이 옮겨갈 때)',
  'PLAYER_SKILL{weapon:katana,move:guardbreak,phase:strike}':
    'PLAYER_SKILL{weapon:katana,move:guardbreak,phase:strike,impactDelayMs} (일치 — 뗀 순간 발행, 판정 100ms 앞에 재생)',
  'PLAYER_SKILL{weapon:katana,move:guardbreak,phase:cleave}':
    'PLAYER_SKILL{weapon:katana,move:guardbreak,phase:cleave,impactDelayMs} (일치 — 판정 순간 발행, impactDelayMs(40) 뒤 재생 = strike 재생 + 140ms)',
  'BRANCH_EFFECT{branch:zangetsu,effect:trail}':
    'BRANCH_EFFECT{branch:zangetsu,effect:trail} (일치 — 궤적 한 줄에 1회)',
  'BRANCH_EFFECT{branch:dance,effect:clone_in|clone_out}':
    'BRANCH_EFFECT{branch:dance,effect:clone_in} 새로 나타날 때만 · {effect:clone_out} 지속 끝 (일치)',
  'PLAYER_SKILL{weapon:katana,move:whirl,phase:hold|reflect}':
    'PLAYER_SKILL{weapon:katana,move:whirl,phase:hold} 루프 시작 · {phase:end} 루프 끝 · {phase:reflect} 탄마다 (일치)',
  'PLAYER_CHARGE{weapon:greatsword,phase:stage|release,stage:4}':
    'PLAYER_CHARGE{phase:stage,stage:4} · {phase:release,stage:4,impactDelayMs} (weapon 키 없음 — 차지는 대검만, 4단은 거인 런만)',
  'BRANCH_EFFECT{branch:giant,effect:ring}':
    'BRANCH_EFFECT{branch:weight,effect:ring,stack:1~3} (60 Q40 — 중압 1~3단 원형 진동 순간, gs_quake_ring) · 거인 4단은 이벤트 없음(charge_slam_lv4 하나만, gs_crack_line 도 없음)',
  'WEAPON_GAUGE{gauge:kenki,event:stage}':
    'WEAPON_GAUGE{weapon:katana,gauge:kenki,event:stage,stage:n} 오를 때만 · 일섬 소모 = {event:consume,stage:소모 단 수} · 갈래 수단(선풍·투구가르기)의 1단 소모는 이벤트 없음',
  'PLAYER_SKILL{weapon:dagger,move:brand|overheat,phase:burst}':
    'PLAYER_SKILL{weapon:dagger,…} (weapon 조건 없어도 됨 — 낙인·과열은 단검만 발행, payload 에는 늘 weapon:dagger)',
};

/** 속사 연사 n번째 (1→2→3 순환) */
let rapidIndex = 0;
export function nextRapidVariant(): number {
  rapidIndex = (rapidIndex % BUILD_SFX.tiers) + 1;
  return rapidIndex;
}

/** 칼 3타 찌르기: 검기 단에 맞는 소리 (단 4·5 는 3), 없으면 기본 찌르기 */
export function katanaThrustSfx(kenkiStage: number | undefined): readonly string[] {
  const n = Math.min(BUILD_SFX.tiers, Math.max(0, Math.floor(kenkiStage ?? 0)));
  return n > 0 ? [BUILD_SFX.katanaThrustKi(n), BUILD_SFX.katanaThrust] : [BUILD_SFX.katanaThrust];
}

/** 속사 연사 공격인가 (PLAYER_ATTACKED 발행 중) */
export function isRapidVolley(): boolean {
  return currentAttackTag() === 'rapidVolley';
}

const skill =
  (move: PlayerSkillPayload['move'], phase?: PlayerSkillPayload['phase']) =>
  (p: PlayerSkillPayload): boolean =>
    p.move === move && (phase === undefined || p.phase === phase);
const effectIs = (branch: string, effects: string) => (p: BranchEffectPayload) =>
  p.branch === branch && effects.split('|').includes(p.effect);

export const BUILD_AUDIO_TRIGGERS: readonly AudioTrigger[] = [
  // --- 57·58라운드 빌드 축 ---
  t<TagSetChangedPayload>({
    event: Events.TAG_SET_CHANGED,
    note: '세트 2·4·6 단 도달 → set_tier1~3',
    when: (p) => p.delta > 0 && p.stage % 2 === 0 && p.stage >= 2 && p.prev < p.stage,
    sfx: (p) => BUILD_SFX.setTier(Math.min(BUILD_SFX.tiers, p.stage / 2)),
  }),
  t({ event: Events.DUAL_TRAIT_GAINED, note: '이중 개성 획득', sfx: BUILD_SFX.dualTrait }),
  t<CurseGainedPayload>({
    event: Events.CURSE_GAINED,
    note: '저주 받음 (피의 계약 칸이면 blood_pact)',
    sfx: (p) => (p.source === 'bloodPact' ? BUILD_SFX.bloodPact : BUILD_SFX.curseTake),
  }),
  t({ event: Events.CURSE_ENDED, note: '저주 끝', sfx: BUILD_SFX.curseEnd }),
  t<PerfectSuccessPayload>({
    event: Events.PERFECT_SUCCESS,
    note: '완벽 회피 (패링·퍼펙트 가드·완벽 놓기는 기존 소리)',
    when: (p) => p.kind === 'perfectEvade',
    sfx: BUILD_SFX.perfectEvade,
  }),
  t<WeaponEvolvedPayload>({
    event: Events.WEAPON_EVOLVED,
    note: '최종 각성 → awaken_<무기> (없으면 evolve)',
    when: (p) => p.kind === 'awaken',
    sfx: (p) => [BUILD_SFX.awaken(p.weapon), 'sfx/evolve'],
  }),
  t<MarkChangedPayload>({
    event: Events.MARK_CHANGED,
    note: '표식 쌓임',
    when: (p) => p.delta > 0,
    sfx: BUILD_SFX.markStack,
  }),
  t<StatusBurstPayload>({
    event: Events.STATUS_BURST,
    note: '끓음 폭발',
    when: (p) => p.kind === 'boil',
    sfx: BUILD_SFX.boilBurst,
  }),
  t<SetEffectPayload>({
    event: Events.SET_EFFECT,
    note: '간파 6 정적',
    when: (p) => p.effect === 'stillness',
    sfx: BUILD_SFX.stillness,
  }),
  t({ event: Events.POOL_IGNITED, note: '술 웅덩이 점화 (취기 술불)', sfx: BUILD_SFX.drunkIgnite }),
  t({ event: Events.DRUNK_SWAY, note: '취보 휘청', sfx: BUILD_SFX.drunkSway }),
  t<EndureTriggeredPayload>({
    event: Events.ENDURE_TRIGGERED,
    note: '버팀 (위기·최후의 저항·마지막 잔)',
    sfx: BUILD_SFX.endure,
  }),

  // --- 칼 갈래 ---
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '회전 베기 홀드 완료 반짝임',
    when: skill('spin', 'ready'),
    sfx: BUILD_SFX.katanaSpinReady,
  }),
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '회전 베기 (2회전은 재생 속도 ×1.06)',
    when: skill('spin', 'release'),
    sfx: BUILD_SFX.katanaSpin,
    rate: (p) => (p.variant === 2 ? BUILD_SFX.spinSecondRate : 1),
  }),
  t<PlayerBranchMovePayload>({
    event: Events.PLAYER_BRANCH_MOVE,
    note: '가드 불가 내려베기 홀드 → katana_guardbreak_hold 루프',
    when: (p) => p.move === 'unblockable' && p.phase === 'hold',
    loop: BUILD_SFX.katanaGuardbreakHold,
  }),
  t<PlayerBranchMovePayload>({
    event: Events.PLAYER_BRANCH_MOVE,
    note: '가드 불가 내려베기 떼기·취소 → 홀드 루프 정지',
    when: (p) => p.move === 'unblockable' && (p.phase === 'release' || p.phase === 'cancel'),
    stop: [BUILD_SFX.katanaGuardbreakHold],
    stopFadeMs: BUILD_SFX.loopFadeMs,
  }),
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '가드 불가 내려베기 판정 (판정 100ms 앞)',
    when: skill('guardbreak', 'strike'),
    sfx: BUILD_SFX.katanaGuardbreak,
    delayMs: (p) => Math.max(0, (p.impactDelayMs ?? 0) - BUILD_SFX.guardbreakLeadMs),
  }),
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '일도양단 균열 (균열 fx 시작 = 판정 + impactDelayMs)',
    when: skill('guardbreak', 'cleave'),
    sfx: BUILD_SFX.katanaCleaveCrack,
    delayMs: (p) => Math.max(0, p.impactDelayMs ?? 0),
  }),
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '회오리 지속 회전 → 루프',
    when: skill('whirl', 'hold'),
    loop: BUILD_SFX.katanaWhirlLoop,
  }),
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '회오리 끝 → 루프 정지',
    when: skill('whirl', 'end'),
    stop: [BUILD_SFX.katanaWhirlLoop],
    stopFadeMs: BUILD_SFX.loopFadeMs,
  }),
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '회오리 탄 반사',
    when: skill('whirl', 'reflect'),
    sfx: BUILD_SFX.katanaWhirlReflect,
  }),

  // --- 대검 · 단검 · 활 수단 ---
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '분쇄 균열 소멸',
    when: skill('crack', 'snuff'),
    sfx: BUILD_SFX.gsShatterSnuff,
  }),
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '부채꼴 투척 (비도면 flyknife_throw)',
    when: skill('fan_throw'),
    sfx: () =>
      hasBranch('flyknife') ? [BUILD_SFX.daggerFlyknifeThrow, BUILD_SFX.daggerFanThrow] : BUILD_SFX.daggerFanThrow,
  }),
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '쌍격 분신 교차',
    when: skill('cross_clone'),
    sfx: BUILD_SFX.daggerCrossClone,
  }),
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '관통 화살 관통',
    when: skill('pierce', 'pass'),
    sfx: BUILD_SFX.bowPierce,
  }),
  t<PlayerAttackPayload>({
    event: Events.PLAYER_ATTACKED,
    note: '속사 연사 → bow_rapid1→2→3 (bow_shot 대신)',
    when: () => isRapidVolley(),
    sfx: () => [BUILD_SFX.bowRapid(nextRapidVariant()), 'sfx/bow_shot'],
    delayMs: (p) => p.releaseDelayMs,
  }),

  // --- 갈래 효과 순간 (BRANCH_EFFECT) ---
  t<BranchEffectPayload>({
    event: Events.BRANCH_EFFECT,
    note: '갈래 효과 → BRANCH_EFFECT_SFX · 천공 연결 스택 n → bow_link<n>',
    sfx: (p) =>
      p.branch === 'skypierce' && p.effect === 'link'
        ? BUILD_SFX.bowLink(Math.max(1, Math.min(BUILD_SFX.tiers, p.stack ?? 1)))
        : (BRANCH_EFFECT_SFX[`${p.branch}:${p.effect}`] ?? null),
  }),
  ...Object.entries(BRANCH_LOOPS).flatMap(([branch, L]) => [
    t<BranchEffectPayload>({
      event: Events.BRANCH_EFFECT,
      note: `${branch} 루프 시작`,
      when: effectIs(branch, L.start),
      loop: L.id,
    }),
    t<BranchEffectPayload>({
      event: Events.BRANCH_EFFECT,
      note: `${branch} 루프 끝`,
      when: effectIs(branch, L.end),
      stop: [L.id],
      stopFadeMs: BUILD_SFX.loopFadeMs,
    }),
  ]),

  // --- 패시브 ---
  t<PassiveProcPayload>({
    event: Events.PASSIVE_PROC,
    note: '패시브 발동 → PASSIVE_SFX (독한 숨 술불 위 = fire_breath)',
    sfx: (p) => (p.passive === 'harshBreath' && p.fire ? HARSH_BREATH_FIRE : (PASSIVE_SFX[p.passive] ?? null)),
  }),

  // --- 2차 묶음 ---
  t({ event: Events.ELITE_SPAWNED, note: '엘리트 등장', sfx: BUILD_SFX.eliteAppear }),
  t<ElitePrefixPayload>({
    event: Events.ELITE_PREFIX,
    note: '엘리트 접두어 사건',
    sfx: (p) =>
      p.prefix === 'barrelArmor' && p.phase === 'break'
        ? BUILD_SFX.eliteArmorBreak
        : p.prefix === 'enraged' && p.phase === 'trigger'
          ? BUILD_SFX.eliteEnrage
          : p.prefix === 'guzzler' && p.phase === 'drink'
            ? BUILD_SFX.eliteDrink
            : p.prefix === 'ringleader' && p.phase === 'death'
              ? BUILD_SFX.eliteLeaderDown
              : null,
  }),
  t<ChallengeEventPayload>({
    event: Events.CHALLENGE_STARTED,
    note: '도전 성소 깃발 세움',
    when: (p) => p.kind === 'warFlag',
    sfx: BUILD_SFX.shrineActivate,
  }),
  t<ChallengeEventPayload>({
    event: Events.CHALLENGE_CLEARED,
    note: '도전 성소 끝 (clear·flawless / fail·timeout)',
    when: (p) => p.kind === 'warFlag',
    sfx: (p) => (p.outcome === 'fail' || p.outcome === 'timeout' ? BUILD_SFX.shrineFail : BUILD_SFX.shrineClear),
  }),
  t<NodeGradedPayload>({
    event: Events.NODE_GRADED,
    note: '노드 성과 등급 완·양',
    sfx: (p) => (p.grade === 'perfect' ? BUILD_SFX.gradePerfect : p.grade === 'good' ? BUILD_SFX.gradeGood : null),
  }),
  t<ConsumablePayload>({
    event: Events.CONSUMABLE_USED,
    note: '소모품 사용',
    sfx: (p) =>
      p.id === 'fireBottle'
        ? BUILD_SFX.bottleThrow
        : p.id === 'strongDrink'
          ? BUILD_SFX.strongDrink
          : p.id === 'coldWater'
            ? BUILD_SFX.coldWater
            : null,
  }),
  t<ConsumablePayload>({
    event: Events.CONSUMABLE_IMPACT,
    note: '화염 술병 깨짐',
    when: (p) => p.id === 'fireBottle',
    sfx: BUILD_SFX.bottleBurst,
  }),
  t({ event: Events.EVENT_NODE_ENTERED, note: '이벤트 노드 진입', sfx: BUILD_SFX.eventEnter }),
  t({ event: Events.HIDDEN_NODE_FOUND, note: '숨은 길 열림', sfx: BUILD_SFX.hiddenNodeFound }),
  t<BossBreakPayload>({
    event: Events.BOSS_BREAK,
    note: '파훼 새 종류 → break_count · 결정타 → break_finisher',
    sfx: (p) => (p.kind === 'finisher' ? BUILD_SFX.breakFinisher : p.distinct ? BUILD_SFX.breakCount : null),
  }),
  t<StatusChangedPayload>({
    event: Events.STATUS_CHANGED,
    note: '불붙은 무기 켜짐 → 루프',
    when: (p) => p.id === 'fireWeapon' && p.phase === 'start',
    loop: BUILD_SFX.fireWeaponLoop,
  }),
  t<StatusChangedPayload>({
    event: Events.STATUS_CHANGED,
    note: '불붙은 무기 꺼짐 → 루프 정지 + fire_weapon_end',
    when: (p) => p.id === 'fireWeapon' && p.phase === 'end',
    stop: [BUILD_SFX.fireWeaponLoop],
    stopFadeMs: BUILD_SFX.loopFadeMs,
    sfx: BUILD_SFX.fireWeaponEnd,
  }),
];

/** 지금 무기 트리에 그 노드를 골랐나 */
export function hasBranch(id: string): boolean {
  return gameState.weapon?.path.includes(id) ?? false;
}

/** 이 표가 쓰는 효과음 전부 (매니페스트 대조) */
export function buildSfxIds(): string[] {
  const out = new Set<string>();
  for (const v of Object.values(BUILD_SFX)) if (typeof v === 'string') out.add(v);
  for (let n = 1; n <= BUILD_SFX.tiers; n++) {
    out.add(BUILD_SFX.setTier(n));
    out.add(BUILD_SFX.katanaThrustKi(n));
    out.add(BUILD_SFX.bowRapid(n));
    out.add(BUILD_SFX.bowLink(n));
    out.add(BUILD_SFX.gsCrackLine(n));
  }
  for (const w of ['katana', 'greatsword', 'dagger', 'bow']) out.add(BUILD_SFX.awaken(w));
  for (const v of Object.values(PASSIVE_SFX)) out.add(v);
  out.add(HARSH_BREATH_FIRE);
  return [...out].sort();
}
