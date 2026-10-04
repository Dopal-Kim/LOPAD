/**
 * 56라운드 2단계 새 기본기 효과음 (음향 4-1-2절 · assets/audio/manifest.json trigger `PLAYER_SKILL` move·phase).
 * 키 이름이 바뀌면 `MOVE_SFX` 만 고친다. 매니페스트에 없는 id 는 조용히 건너뛴다.
 */
import { Events, type PlayerSkillPayload } from '../core/EventBus';
import { t, type AudioTrigger } from './audioTrigger';

export const MOVE_SFX = {
  katanaCounter: 'sfx/katana_counter',
  /** 대치 일격 유지 루프 (누르는 동안) · 발도 (뗀 순간) */
  katanaIaiHold: 'sfx/katana_iai_hold',
  katanaIaiRelease: 'sfx/katana_iai_release',
  gsTackle: 'sfx/gs_tackle',
  gsBraceUpswing: 'sfx/gs_brace_upswing',
  gsLeap: 'sfx/gs_leap',
  gsLeapSlam: 'sfx/gs_leap_slam',
  gsGuardRush: 'sfx/gs_guard_rush',
  daggerBackstab: 'sfx/dagger_backstab',
  /** 고속 난타 찌르기 변주 1~4 (찌를 때마다 직전과 다른 것) */
  daggerFlurry: (n: number) => `sfx/dagger_flurry${n}`,
  daggerFlurryVariants: 4,
  arrowRainLaunch: 'sfx/arrow_rain_launch',
  arrowRainImpact: 'sfx/arrow_rain_impact',
  /** 음향 권장값: 유지 루프 페이드 · 울분 소모 올려베기 재생 속도 · 난타 ±3% */
  iaiHoldFadeInMs: 120,
  iaiHoldFadeOutMs: 80,
  braceRageRate: 0.92,
  flurryRateJitter: 0.03,
} as const;

/** 차지 내려찍기 n단 (도약 찍기 착지에 겹침 — audioMap CHARGE_SFX.slam 과 같은 키) */
const chargeSlam = (n: number): readonly string[] => [`sfx/charge_slam_lv${n}`, 'sfx/charge_slam'];

/** 새 기본기 효과음 전부 (매니페스트 대조) */
export function moveSfxIds(): string[] {
  const out: string[] = [];
  for (const v of Object.values(MOVE_SFX)) if (typeof v === 'string') out.push(v);
  for (let n = 1; n <= MOVE_SFX.daggerFlurryVariants; n++) out.push(MOVE_SFX.daggerFlurry(n));
  return out;
}

/** 난타 변주: 1~n 중 직전과 다른 것 (rand = 0..1) */
export function pickFlurryVariant(prev: number, n: number, rand: number): number {
  if (n <= 1) return 1;
  const k = 1 + Math.floor(rand * (n - 1));
  return ((prev - 1 + k) % n) + 1;
}

let lastFlurry = 0;

const skill = (move: PlayerSkillPayload['move'], phase?: PlayerSkillPayload['phase']) => (p: PlayerSkillPayload) =>
  p.move === move && (phase === undefined || p.phase === phase);

export const MOVE_AUDIO_TRIGGERS: readonly AudioTrigger[] = [
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '2단계 칼 간파 반격 → katana_counter',
    when: skill('counter', 'start'),
    sfx: MOVE_SFX.katanaCounter,
  }),
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '2단계 칼 대치 일격 유지 → katana_iai_hold 루프',
    when: skill('iai', 'hold'),
    loop: MOVE_SFX.katanaIaiHold,
    loopFadeInMs: MOVE_SFX.iaiHoldFadeInMs,
  }),
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '2단계 칼 대치 일격 뗌·끊김 → 유지 루프 정지 (뗌이면 katana_iai_release)',
    when: (p) => p.move === 'iai' && (p.phase === 'release' || p.phase === 'cancel'),
    stop: [MOVE_SFX.katanaIaiHold],
    stopFadeMs: MOVE_SFX.iaiHoldFadeOutMs,
    sfx: (p) => (p.phase === 'release' ? MOVE_SFX.katanaIaiRelease : null),
  }),
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '2단계 대검 어깨 태클 → gs_tackle',
    when: skill('tackle', 'start'),
    sfx: MOVE_SFX.gsTackle,
  }),
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '2단계 대검 버티기 올려베기 → gs_brace_upswing (울분 소모 rate 0.92)',
    when: skill('brace_upswing', 'start'),
    sfx: MOVE_SFX.gsBraceUpswing,
    rate: (p) => (p.rage ? MOVE_SFX.braceRageRate : 1),
  }),
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '2단계 대검 도약 → gs_leap',
    when: skill('leap', 'takeoff'),
    sfx: MOVE_SFX.gsLeap,
  }),
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '2단계 대검 도약 착지 → gs_leap_slam',
    when: skill('leap', 'land'),
    sfx: MOVE_SFX.gsLeapSlam,
  }),
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '2단계 대검 도약 착지 · 차지 1단 이상 → charge_slam_lv<n> 겹침',
    when: (p) => p.move === 'leap' && p.phase === 'land' && (p.stage ?? 0) > 0,
    sfx: (p) => chargeSlam(p.stage ?? 1),
  }),
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '2단계 대검 막다가 떼면 돌진 → gs_guard_rush',
    when: skill('guard_rush', 'start'),
    sfx: MOVE_SFX.gsGuardRush,
  }),
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '2단계 단검 등 뒤 치명 찌르기 → dagger_backstab',
    when: skill('backstab', 'start'),
    sfx: MOVE_SFX.daggerBackstab,
  }),
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '2단계 단검 고속 난타 찌르기마다 → dagger_flurry1~4 (직전과 다른 것, ±3%)',
    when: skill('flurry', 'stab'),
    sfx: () => {
      lastFlurry = pickFlurryVariant(lastFlurry, MOVE_SFX.daggerFlurryVariants, Math.random());
      return MOVE_SFX.daggerFlurry(lastFlurry);
    },
    rate: () => 1 + (Math.random() * 2 - 1) * MOVE_SFX.flurryRateJitter,
  }),
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '2단계 활 화살비 발사 → arrow_rain_launch',
    when: skill('arrow_rain', 'launch'),
    sfx: MOVE_SFX.arrowRainLaunch,
  }),
  t<PlayerSkillPayload>({
    event: Events.PLAYER_SKILL,
    note: '2단계 활 화살비 낙하 → arrow_rain_impact (첫 꽂힘 0.1s 앞에서)',
    when: skill('arrow_rain', 'impact'),
    sfx: MOVE_SFX.arrowRainImpact,
  }),
];
