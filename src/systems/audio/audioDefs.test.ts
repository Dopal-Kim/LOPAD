import { describe, expect, it, vi } from 'vitest';
import { EventEmitter } from 'node:events';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import {
  SfxDedupe,
  audioFileRel,
  audioFileRels,
  loopEndFrames,
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
  ENEMY_OWN_SFX,
  ENEMY_PHASE_SFX,
  FOLLOW_UP_SFX,
  SFX,
  WEAPON_SFX,
  bossActionSfx,
  bossLoopSfx,
  breakSfx,
  chargeSfxIds,
  weaponSfxIds,
  staticSfxIds,
} from './audioMap';
import { Events, type BossActionKind } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { MOVE_SFX, moveSfxIds, pickFlurryVariant } from './audioMoves';
import { P13_SFX } from './audioDrops';
import { ARCHIVED_SFX, BUILD_SFX, GROWTH_SFX, buildSfxIds } from './audioBuild';

/** 61라운드: 이벤트·페이로드에 걸리는 트리거들의 효과음 id (조건·페이로드 함수 풀이) */
function sfxFor(event: string, payload: unknown): string[] {
  const out: string[] = [];
  for (const tr of AUDIO_TRIGGERS) {
    if (tr.event !== event || (tr.when && !tr.when(payload as never))) continue;
    const v = typeof tr.sfx === 'function' ? tr.sfx(payload as never) : tr.sfx;
    for (const id of Array.isArray(v) ? v : v ? [v] : []) out.push(id);
  }
  return out;
}

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

  it('57라운드 Q38: files(ogg → m4a) 순서대로 후보, 없으면 file 하나 · 실제 매니페스트는 .wav 없음', () => {
    expect(
      audioFileRels({
        file: 'assets/audio/sfx/a.ogg',
        files: ['assets/audio/sfx/a.ogg', 'assets/audio/sfx/a.m4a'],
      }),
    ).toEqual(['audio/sfx/a.ogg', 'audio/sfx/a.m4a']);
    expect(audioFileRels({ file: 'assets/audio/sfx/a.ogg' })).toEqual(['audio/sfx/a.ogg']);
    expect(audioFileRels({ file: 'assets/audio/sfx/a.ogg', files: [] })).toEqual(['audio/sfx/a.ogg']);
    for (const e of manifest.entries) {
      const rels = audioFileRels(e);
      expect(rels.length, e.id).toBeGreaterThan(0);
      for (const r of rels) expect(r.endsWith('.wav'), r).toBe(false);
      if (e.files) expect(rels[0].endsWith('.ogg'), e.id).toBe(true);
    }
  });

  it('57라운드 Q38 루프 끝: 디코딩 버퍼가 loopEndSample/sampleRate 보다 길 때만 그 길이 (재표본화 비례)', () => {
    const e = { loop: true, loopEndSample: 26460, sampleRate: 44100 };
    expect(loopEndFrames(e, { length: 26460, sampleRate: 44100 })).toBeNull();
    expect(loopEndFrames(e, { length: 27484, sampleRate: 44100 })).toBe(26460);
    // 48kHz 컨텍스트: 0.6초 = 28800
    expect(loopEndFrames(e, { length: 30000, sampleRate: 48000 })).toBe(28800);
    expect(loopEndFrames({ ...e, loop: false }, { length: 30000, sampleRate: 44100 })).toBeNull();
    expect(loopEndFrames({ loop: true }, { length: 30000, sampleRate: 44100 })).toBeNull();
    // 실제 매니페스트의 루프 항목은 이음매 정보가 있다
    for (const m of manifest.entries.filter((x) => x.loop))
      if (m.files) expect(m.loopEndSample, m.id).toBeGreaterThan(0);
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
      // 60라운드 빌드 37 + 2차 묶음·갈래·패시브 67 · 페이로드로 고르게 된 기존 id
      ...buildSfxIds(),
      SFX.shopBuy,
      // 61 G: 1차·2차 각성 폴백 (WEAPON_AWAKEN 페이로드로 고른다)
      SFX.evolve,
      // 61 단계 4 P12: 각성·개성·게이지 (계약 sound §10)
      // 61 단계 5 P13: 기둥 무너짐·포물선 술병·드랍 (계약 sound §11)
      P13_SFX.pillarCollapse,
      P13_SFX.lobBottle,
      P13_SFX.voucherDrop,
      P13_SFX.voucherPickup,
      P13_SFX.itemPickup,
      GROWTH_SFX.awaken1,
      GROWTH_SFX.awaken2,
      GROWTH_SFX.traitManifest,
      GROWTH_SFX.growthTick,
      ...(['katana', 'greatsword', 'dagger', 'bow'] as const).map((w) => GROWTH_SFX.awakenTail(w)),
      SFX.menuSelect,
      SFX.enemyDeath,
      SFX.dash,
      // 61라운드 보스 단계 3: 1층 밖 보스의 등장·예고·사망(페이로드로 고름) · 칼 발도 검기 단별
      SFX.bossStart,
      SFX.bossTelegraph,
      SFX.bossDie,
      ...[1, 2, 3, 4, 5].map((n) => MOVE_SFX.katanaIaiKi(n)),
      // 61라운드 계약 sound §9: 피격·가드 막기 · 연격 마무리
      SFX.hitPlayer,
      SFX.guardBlock,
      SFX.comboFinish,
      // 61라운드 단계 2: 적 보조음(행상·짐꾼은 전용) · 행상·짐꾼 단계 · 대검 가드
      SFX.enemyHurt,
      SFX.guardBlockHeavy,
      ...Object.values(ENEMY_OWN_SFX).flatMap((o) => [o.hurt, o.death, o.telegraph].filter((x): x is string => !!x)),
      ...Object.values(ENEMY_PHASE_SFX),
    ]);
    // 60라운드 Q6 보관 3종은 연결하지 않는다
    for (const id of ARCHIVED_SFX) expect(used.has(id), id).toBe(false);
    const unused = manifest.entries
      // 61라운드 §9: 변주(variantOf)는 원본 트리거가 고른다 — 원본이 쓰이면 쓰인 것
      .filter(
        (e) =>
          e.kind === 'sfx' &&
          !used.has(e.id) &&
          !(e.variantOf && used.has(e.variantOf)) &&
          !ARCHIVED_SFX.includes(e.id),
      )
      .map((e) => e.id);
    expect(unused).toEqual([]);
    // 60라운드 새 id 는 전부 매니페스트에 있다
    for (const id of buildSfxIds()) expect(idx.has(id), id).toBe(true);
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
    // 61 단계 4: 아트 2 보스 동작 — 기둥 균열은 단(1~3)마다, 범위 밖 단은 끝으로 자른다
    for (const a of ['introRoar', 'cupStruck', 'flameSnuff'] as const) reached.add(bossActionSfx(a)!);
    for (const n of [1, 2, 3]) reached.add(bossActionSfx('pillarCrack', n)!);
    expect(bossActionSfx('pillarCrack', 0)).toBe(SFX.boss1.pillarCrack1);
    expect(bossActionSfx('pillarCrack', 7)).toBe(SFX.boss1.pillarCrack3);
    for (const l of ['gulp', 'roll', 'fire'] as const) reached.add(bossLoopSfx(l));
    // BOSS_ATTACK spin · BOSS_PHASE(1층) 은 트리거 표에서 직접
    reached.add(SFX.boss1.spinStart);
    reached.add(SFX.boss1.phaseDrink);
    // 61라운드 단계 3: 파훼 종류별 · 등장·3국면·사망 · 1국면 돌진/내리찍기 예고·실행 · 술통 되치기
    for (const k of ['cup', 'pillar', 'cask', 'reel']) reached.add(breakSfx(k)!);
    for (const [ev, p] of [
      [Events.BOSS_STARTED, { boss: 'stage1' }],
      [Events.BOSS_DIED, { id: 'stage1' }],
      [Events.BOSS_TELEGRAPH, { id: 'stage1', attack: 'dash' }],
      [Events.BOSS_TELEGRAPH, { id: 'stage1', attack: 'slam' }],
      [Events.BOSS_ATTACK, { id: 'stage1', attack: 'dash' }],
      [Events.BOSS_ATTACK, { id: 'stage1', attack: 'slam' }],
    ] as const)
      for (const id of sfxFor(ev, p)) reached.add(id);
    reached.add(SFX.boss1.phaseBlackout);
    // 넘어짐 boss1_fall 은 1층 파훼 종류에 reel 이 없을 때의 대신 소리 (지금은 boss1_break_reel)
    reached.add(SFX.boss1.fall);
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

  it('후속 판정: 60라운드 Q6 칼 잔상 베기 katana_echo 는 보관(무음), 대검 링 → 없음', () => {
    const tr = fire(Events.PLAYER_FOLLOW_UP, { weapon: 'katana', id: 'echo' });
    expect(tr).toHaveLength(1);
    expect(FOLLOW_UP_SFX['katana:echo']).toBeUndefined();
    expect(sfxOf(tr[0], { weapon: 'katana', id: 'echo' })).toBeNull();
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

  it('60라운드 차지 휘둘러 내리찍기 = charge_slam + 균열 gs_crack_line_lv<n>(40ms 뒤, 60 Q40 4단·중압 런 = charge_slam 만) — gs_crack·gs_plunge 보관', () => {
    const release = { phase: 'release', stage: 3, impactDelayMs: 180 };
    expect(ids(Events.PLAYER_CHARGE, release)).toEqual([CHARGE_SFX.slam(3), BUILD_SFX.gsCrackLine(3)]);
    const crack = fire(Events.PLAYER_CHARGE, release).find(
      (tr) => typeof tr.sfx === 'function' && tr.sfx(release) === BUILD_SFX.gsCrackLine(3),
    );
    expect(crack?.delayMs?.(release)).toBe(220);
    const four = { phase: 'release', stage: 4, impactDelayMs: 0 };
    expect(ids(Events.PLAYER_CHARGE, four)).toEqual([CHARGE_SFX.slam(4)]);
    // 60 Q40 보충: 중압(weight) 런은 균열이 안 보이므로 1~3단에서도 균열 소리 없음
    const path = gameState.weapon.path;
    gameState.weapon.path = ['weight'];
    try {
      expect(ids(Events.PLAYER_CHARGE, release)).toEqual([CHARGE_SFX.slam(3)]);
    } finally {
      gameState.weapon.path = path;
    }
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
