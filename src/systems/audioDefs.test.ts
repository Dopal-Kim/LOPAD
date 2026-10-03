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
import { AUDIO_TRIGGERS, SFX, staticSfxIds } from './audioMap';

// audioMap → EventBus 가 Phaser 를 import 하므로(window 필요) 이벤트 이미터만 node 것으로 대체한다
vi.mock('phaser', () => ({ default: { Events: { EventEmitter } } }));

/** 음향 파트 계약 초안 (읽기 전용 참조) */
const manifest = JSON.parse(
  readFileSync(resolve(__dirname, '../../assets/audio/manifest.json'), 'utf8'),
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
    ]);
    const unused = manifest.entries.filter((e) => e.kind === 'sfx' && !used.has(e.id)).map((e) => e.id);
    expect(unused).toEqual([]);
    expect(AUDIO_TRIGGERS.length).toBeGreaterThan(30);
  });
});
