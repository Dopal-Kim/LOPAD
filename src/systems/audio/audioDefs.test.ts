import { describe, expect, it, vi } from 'vitest';
import { EventEmitter } from 'node:events';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import {
  SfxDedupe,
  audioFileRel,
  audioManifestRel,
  bgmGain,
  bossBgmState,
  dbToGain,
  hasPitchVariance,
  indexEntries,
  isAudioManifest,
  isBossState,
  mixingOf,
  pitchRate,
  resolveBgm,
  sfxGain,
  type AudioManifest,
} from './audioDefs';
import {
  AUDIO_TRIGGERS,
  CHARGE_SFX,
  FOLLOW_UP_SFX,
  SFX,
  WEAPON_SFX,
  bossActionSfx,
  bossLoopSfx,
  chargeSfxIds,
  weaponSfxIds,
  staticSfxIds,
} from './audioMap';
import { Events, type BossActionKind } from '../../core/EventBus';
import { MOVE_SFX, moveSfxIds, pickFlurryVariant } from './audioMoves';

// audioMap → EventBus 가 Phaser 를 import 하므로(window 필요) 이벤트 이미터만 node 것으로 대체한다
vi.mock('phaser', () => ({ default: { Events: { EventEmitter } } }));

/** 음향 파트 계약 초안 (읽기 전용 참조) */
const manifest = JSON.parse(
  readFileSync(resolve(__dirname, '../../../assets/audio/manifest.json'), 'utf8'),
) as AudioManifest;

const small: AudioManifest = {
  version: 1,
  mixing: { bgmBusDb: -8, bgmBossDuckDb: -3 },
  bgmByFloor: { '1': 'bgm/low', '2': 'bgm/low', '3': 'bgm/mid' },
  bgmByState: { title: 'bgm/title', boss: 'bgm/boss', emperor: 'bgm/emperor' },
  entries: [
    {
      id: 'bgm/low',
      kind: 'bgm',
      category: 'bgm',
      file: 'assets/audio/bgm/low.wav',
      durationMs: 1,
      loop: true,
      gainDb: -0.5,
    },
    {
      id: 'bgm/boss',
      kind: 'bgm',
      category: 'bgm',
      file: 'assets/audio/bgm/boss.wav',
      durationMs: 1,
      loop: true,
      gainDb: 1.5,
    },
    {
      id: 'sfx/a',
      kind: 'sfx',
      category: 'combat',
      file: 'assets/audio/sfx/a.wav',
      durationMs: 1,
      loop: false,
      gainDb: -2,
    },
  ],
};

describe('audio defs (계약 초안 assets/audio/manifest.json)', () => {
  it('dB → 게인', () => {
    expect(dbToGain(0)).toBeCloseTo(1);
    expect(dbToGain(-6)).toBeCloseTo(0.501, 2);
    expect(dbToGain(-20)).toBeCloseTo(0.1);
  });

  it('entry.file 의 assets/ 접두를 떼고 서빙 상대 경로로', () => {
    expect(audioFileRel({ file: 'assets/audio/sfx/swing_katana.wav' })).toBe('audio/sfx/swing_katana.wav');
    expect(audioFileRel({ file: 'audio/sfx/x.wav' })).toBe('audio/sfx/x.wav');
    expect(audioManifestRel()).toBe('audio/manifest.json');
  });

  it('버스 음량: SFX 0 dB + gainDb, BGM -8 dB (+ 보스 -3 dB, 일시정지 -6 dB)', () => {
    const mix = mixingOf(small);
    expect(mix.sfxBusDb).toBe(0);
    expect(sfxGain(mix, { gainDb: -2 })).toBeCloseTo(dbToGain(-2));
    expect(bgmGain(mix, { gainDb: 1.5 })).toBeCloseTo(dbToGain(-6.5));
    expect(bgmGain(mix, { gainDb: 1.5 }, { bossDuck: true })).toBeCloseTo(dbToGain(-9.5));
    expect(bgmGain(mix, { gainDb: 0 }, { pauseDuck: true })).toBeCloseTo(dbToGain(-14));
  });

  it('BGM 결정: 상태 > 층, 보스 id 가 상태 곡이면 그 상태(황제)', () => {
    expect(resolveBgm(small, 1, null)).toBe('bgm/low');
    expect(resolveBgm(small, 3, null)).toBe('bgm/mid');
    expect(resolveBgm(small, 1, 'boss')).toBe('bgm/boss');
    expect(resolveBgm(small, null, 'title')).toBe('bgm/title');
    expect(resolveBgm(small, 9, null)).toBeNull();
    expect(bossBgmState(small, 'stage2')).toBe('boss');
    expect(bossBgmState(small, 'emperor')).toBe('emperor');
    expect(isBossState('boss')).toBe(true);
    expect(isBossState('title')).toBe(false);
    expect(isBossState(null)).toBe(false);
  });

  it('20ms 중복 묶기와 ±4% 피치 변주 대상', () => {
    const d = new SfxDedupe(20);
    expect(d.allow('sfx/a', 100)).toBe(true);
    expect(d.allow('sfx/a', 110)).toBe(false);
    expect(d.allow('sfx/b', 110)).toBe(true);
    expect(d.allow('sfx/a', 120)).toBe(true);
    expect(hasPitchVariance('sfx/swing_katana')).toBe(true);
    expect(hasPitchVariance('sfx/hit_enemy_crit')).toBe(true);
    expect(hasPitchVariance('sfx/door_open')).toBe(false);
    expect(pitchRate(0)).toBeCloseTo(0.96);
    expect(pitchRate(1)).toBeCloseTo(1.04);
    expect(pitchRate(0.5)).toBeCloseTo(1);
  });

  it('실제 매니페스트: 형식·색인·층 1~8 BGM·상태 3종', () => {
    expect(isAudioManifest(manifest)).toBe(true);
    const idx = indexEntries(manifest);
    expect(idx.size).toBe(manifest.entries.length);
    for (let f = 1; f <= 8; f++) expect(idx.has(resolveBgm(manifest, f, null)!)).toBe(true);
    for (const st of ['title', 'boss', 'emperor']) expect(idx.has(resolveBgm(manifest, null, st)!)).toBe(true);
    expect(mixingOf(manifest)).toMatchObject({ sfxBusDb: 0, bgmBusDb: -8, bgmCrossfadeMs: 1200, bgmBossDuckDb: -3 });
  });

  it('트리거 표의 고정 id 와 무기별 swing·적별 돌진/발사 id 가 전부 매니페스트에 있다', () => {
    const idx = indexEntries(manifest);
    for (const id of staticSfxIds()) expect(idx.has(id), id).toBe(true);
    for (const w of ['katana', 'greatsword', 'dagger']) expect(idx.has(SFX.swing(w)), w).toBe(true);
    expect(idx.has(SFX.enemyTelegraph('charger'))).toBe(true);
    expect(idx.has(SFX.enemyDash('charger'))).toBe(true);
    expect(idx.has(SFX.enemyShot('archer'))).toBe(true);
    // 54라운드 1층 보스 '만취' 효과음 18종 (페이로드로 고르는 id)
    for (const id of Object.values(SFX.boss1)) expect(idx.has(id), id).toBe(true);
    // 매니페스트의 모든 효과음이 표 어딘가에서 쓰인다 (누락 자산 점검)
    const used = new Set([
      ...staticSfxIds(),
      SFX.swing('katana'),
      SFX.swing('greatsword'),
      SFX.swing('dagger'),
      SFX.enemyTelegraph('charger'),
      SFX.enemyDash('charger'),
      SFX.enemyShot('archer'),
      SFX.bowShot,
      SFX.bowAimed,
      SFX.hitEnemy,
      SFX.hitEnemyCrit,
      SFX.bossPhase,
      ...Object.values(SFX.boss1),
      // 55라운드 차지·잔상 (후보 목록 — 없어도 무음)
      ...chargeSfxIds(),
      // 56라운드 무기 피드백 · 2단계 새 기본기
      ...weaponSfxIds(),
      ...moveSfxIds(),
    ]);
    const unused = manifest.entries.filter((e) => e.kind === 'sfx' && !used.has(e.id)).map((e) => e.id);
    expect(unused).toEqual([]);
    expect(AUDIO_TRIGGERS.length).toBeGreaterThan(30);
  });

  it('54라운드 보스 18종이 전부 시스템 이벤트로 닿는다 (매니페스트 trigger 문자열과 무관 — audioMap 대응표)', () => {
    const actions: BossActionKind[] = [
      'drinkLift',
      'drinkFinish',
      'cupBreak',
      'reelTelegraph',
      'reelDash',
      'fall',
      'rise',
      'kick',
      'caskBounce',
      'caskBreak',
      'caskRedirect',
      'spill',
      'torchThrow',
      'ignite',
      'bossIgnite',
      'candleTopple',
      'candleRelight',
      'phaseDrink',
    ];
    const reached = new Set<string>();
    for (const a of actions) {
      const id = bossActionSfx(a);
      if (id) reached.add(id);
    }
    for (const l of ['gulp', 'roll', 'fire'] as const) reached.add(bossLoopSfx(l));
    // BOSS_ATTACK spin · BOSS_PHASE(1층) 은 트리거 표에서 직접
    reached.add(SFX.boss1.spinStart);
    reached.add(SFX.boss1.phaseDrink);
    expect([...reached].sort()).toEqual(Object.values(SFX.boss1).sort());
    expect(bossActionSfx('bossIgnite')).toBe(SFX.boss1.ignite);
  });
});

describe('55라운드 Q32 차지·잔상 효과음 매핑 (CHARGE_SFX · FOLLOW_UP_SFX)', () => {
  const fire = (event: string, payload: unknown) =>
    AUDIO_TRIGGERS.filter((tr) => tr.event === event && (!tr.when || tr.when(payload)));
  const sfxOf = (tr: (typeof AUDIO_TRIGGERS)[number], p: unknown) =>
    typeof tr.sfx === 'function' ? tr.sfx(p) : tr.sfx;

  it('고정 id 목록에 넣지 않는다 (매니페스트에 없어도 무음으로 동작)', () => {
    const fixed = new Set(staticSfxIds());
    for (const id of chargeSfxIds()) expect(fixed.has(id), id).toBe(false);
  });

  it('start → charge_start + 루프(페이드 인), stage n → charge_stage<n>', () => {
    const start = fire(Events.PLAYER_CHARGE, { phase: 'start', stage: 0 });
    expect(start).toHaveLength(1);
    expect(sfxOf(start[0], {})).toBe(CHARGE_SFX.start);
    expect(start[0].loopOf?.({})).toBe(CHARGE_SFX.loop);
    expect(start[0].loopFadeInMs).toBe(150);
    const st = fire(Events.PLAYER_CHARGE, { phase: 'stage', stage: 2 });
    expect(st.map((tr) => sfxOf(tr, { phase: 'stage', stage: 2 }))).toEqual([['sfx/charge_stage2']]);
  });

  it('release → 루프 120ms 페이드 + charge_slam_lv<n> 을 판정 프레임(impactDelayMs)에, cancel(hurt) → 60ms', () => {
    const rel = { phase: 'release', stage: 3, impactDelayMs: 120 };
    const trs = fire(Events.PLAYER_CHARGE, rel);
    const stop = trs.find((tr) => tr.stopOf)!;
    expect(stop.stopOf!(rel)).toEqual([CHARGE_SFX.loop]);
    expect(typeof stop.stopFadeMs === 'function' ? stop.stopFadeMs(rel) : stop.stopFadeMs).toBe(120);
    const slam = trs.find((tr) => tr.sfx)!;
    expect(sfxOf(slam, rel)).toEqual(['sfx/charge_slam_lv3', 'sfx/charge_slam']);
    expect(slam.delayMs!(rel)).toBe(120);
    const hurt = { phase: 'cancel', stage: 0, reason: 'hurt' };
    const c = fire(Events.PLAYER_CHARGE, hurt);
    expect(c).toHaveLength(1);
    expect(typeof c[0].stopFadeMs === 'function' ? c[0].stopFadeMs(hurt) : 0).toBe(60);
    // 1단 전에 뗀 일반 연격(tap)도 루프를 끈다 (swing_greatsword 는 PLAYER_ATTACKED 가 그대로)
    expect(fire(Events.PLAYER_CHARGE, { phase: 'cancel', stage: 0, reason: 'tap' })).toHaveLength(1);
  });

  it('차지 내려찍기 공격은 swing 대신 charge_slam (PLAYER_ATTACKED 의 swing 없음)', () => {
    const atk = AUDIO_TRIGGERS.find((tr) => tr.event === Events.PLAYER_ATTACKED)!;
    expect(sfxOf(atk, { kind: 'attack', charge: 2, swingDelayMs: 100 })).toBeNull();
  });

  it('후속 판정: 칼 잔상 베기 → katana_echo, 대검 링 → 없음', () => {
    const tr = fire(Events.PLAYER_FOLLOW_UP, { weapon: 'katana', id: 'echo' });
    expect(tr).toHaveLength(1);
    expect(sfxOf(tr[0], { weapon: 'katana', id: 'echo' })).toEqual(FOLLOW_UP_SFX['katana:echo']);
    expect(sfxOf(tr[0], { weapon: 'greatsword', id: 'ring' })).toBeNull();
  });
});

describe('56라운드 무기 피드백 효과음 (WEAPON_SFX)', () => {
  const fire = (event: string, payload: unknown) =>
    AUDIO_TRIGGERS.filter((tr) => tr.event === event && (!tr.when || tr.when(payload)));
  const ids = (event: string, payload: unknown) =>
    fire(event, payload)
      .map((tr) => (typeof tr.sfx === 'function' ? tr.sfx(payload) : tr.sfx))
      .filter(Boolean);

  it('차지 유지음 음높이 단계 1.0 / 1.03 / 1.06', () => {
    const rates = [1, 2, 3].map((n) =>
      fire(Events.PLAYER_CHARGE, { phase: 'stage', stage: n })
        .map((tr) => tr.loopRate?.({ phase: 'stage', stage: n }))
        .find(Boolean),
    );
    expect(rates).toEqual([
      { id: CHARGE_SFX.loop, rate: 1 },
      { id: CHARGE_SFX.loop, rate: 1.03 },
      { id: CHARGE_SFX.loop, rate: 1.06 },
    ]);
  });

  it('꽂아내리기 = gs_plunge + gs_crack(40ms 뒤), 기본 차지 = charge_slam', () => {
    const plunge = { phase: 'release', stage: 3, impactDelayMs: 280, mode: 'plunge' };
    expect(ids(Events.PLAYER_CHARGE, plunge)).toEqual([WEAPON_SFX.gsPlunge, WEAPON_SFX.gsCrack]);
    const crack = fire(Events.PLAYER_CHARGE, plunge).find((tr) => tr.sfx === WEAPON_SFX.gsCrack);
    expect(crack?.delayMs?.(plunge)).toBe(320);
    expect(ids(Events.PLAYER_CHARGE, { phase: 'release', stage: 3, impactDelayMs: 180 })).toEqual([CHARGE_SFX.slam(3)]);
  });

  it('퍼펙트 가드 · 그로기 · 검기 단 · 일섬 · 활 약한/완벽 놓기', () => {
    expect(ids(Events.PLAYER_PERFECT_GUARD, { x: 0, y: 0, attack: 5 })).toEqual([WEAPON_SFX.perfectGuard]);
    expect(ids(Events.WEAPON_RESOURCE, { weapon: 'katana', kind: 'stamina', event: 'groggy' })).toEqual([
      WEAPON_SFX.groggyStart,
    ]);
    expect(ids(Events.WEAPON_GAUGE, { weapon: 'katana', gauge: 'kenki', event: 'stage', stage: 2 })).toEqual([
      'sfx/kenki_stage2',
    ]);
    expect(ids(Events.WEAPON_GAUGE, { weapon: 'katana', gauge: 'kenki', event: 'consume', stage: 3 })).toEqual([]);
    expect(ids(Events.PLAYER_SKILL, { weapon: 'katana', move: 'issen', phase: 'dash' })).toEqual([
      WEAPON_SFX.issenDash,
    ]);
    expect(ids(Events.PLAYER_SECONDARY, { kind: 'aimedshot', phase: 'release', power: 'weak' })).toEqual([
      WEAPON_SFX.bowReleaseWeak,
    ]);
    expect(ids(Events.PLAYER_SECONDARY, { kind: 'aimedshot', phase: 'release', power: 'perfect' })).toEqual([
      WEAPON_SFX.bowReleasePerfect,
    ]);
  });

  it('2단계 새 기본기 목록과 56라운드 목록은 겹치지 않는다', () => {
    const a = new Set(weaponSfxIds());
    for (const id of moveSfxIds()) expect(a.has(id), id).toBe(false);
  });

  it('2단계 새 기본기: PLAYER_SKILL move·phase → 효과음 (난타 변주는 직전과 다름)', () => {
    const skill = (move: string, phase: string, more = {}) => ({ weapon: 'x', move, phase, ...more });
    expect(ids(Events.PLAYER_SKILL, skill('counter', 'start'))).toEqual([MOVE_SFX.katanaCounter]);
    expect(ids(Events.PLAYER_SKILL, skill('iai', 'release'))).toEqual([MOVE_SFX.katanaIaiRelease]);
    expect(ids(Events.PLAYER_SKILL, skill('leap', 'land', { stage: 0 }))).toEqual([MOVE_SFX.gsLeapSlam]);
    expect(ids(Events.PLAYER_SKILL, skill('leap', 'land', { stage: 2 }))).toEqual([
      MOVE_SFX.gsLeapSlam,
      ['sfx/charge_slam_lv2', 'sfx/charge_slam'],
    ]);
    expect(ids(Events.PLAYER_SKILL, skill('arrow_rain', 'impact'))).toEqual([MOVE_SFX.arrowRainImpact]);
    for (let prev = 1; prev <= 4; prev++)
      for (const r of [0, 0.4, 0.99]) {
        const n = pickFlurryVariant(prev, 4, r);
        expect(n).not.toBe(prev);
        expect(n >= 1 && n <= 4).toBe(true);
      }
  });

  it('2단계: 새 기본기 공격은 휘두름 소리 없음 · 조용한 가드 해제는 밀쳐내기 소리 없음', () => {
    const atk = { x: 0, y: 0, dirX: 1, dirY: 0, damageMult: 1, sizeMult: 1, kind: 'attack', forceCrit: false };
    expect(
      ids(Events.PLAYER_ATTACKED, { ...atk, primed: false, swingDelayMs: 0, releaseDelayMs: 0, move: 'counter' }),
    ).toEqual([]);
    expect(ids(Events.PLAYER_GUARD_RELEASED, { x: 0, y: 0, quiet: true })).toEqual([]);
  });
});
