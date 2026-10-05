import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { mixingOf, type AudioManifest } from './audioDefs';
import {
  allocateVoice,
  duckDbAt,
  ducksFor,
  floorSceneOfNode,
  floorStateBgmIds,
  isLazyBgm,
  parseDucking,
  pickVariant,
  resolveBgmFor,
  startDuck,
  voiceLimitsOf,
} from './audioMix';
import { pickPlayableUrl } from './audioLazy';

const manifest = JSON.parse(
  readFileSync(resolve(__dirname, '../../../assets/audio/manifest.json'), 'utf8'),
) as AudioManifest;

describe('61라운드 계약 sound §9 믹싱', () => {
  it('BGM: 1층 여정 = f1_outside, 전투 = f1_jan, 보스 국면 1~3, 타이틀·2층은 그대로', () => {
    expect(floorSceneOfNode('birth')).toBe('journey');
    expect(floorSceneOfNode('road')).toBe('journey');
    expect(floorSceneOfNode('battle')).toBe('combat');
    expect(resolveBgmFor(manifest, 1, null, 'journey', 1)).toBe('bgm/f1_outside');
    expect(resolveBgmFor(manifest, 1, null, 'combat', 1)).toBe('bgm/f1_jan');
    expect(resolveBgmFor(manifest, 1, 'boss', 'combat', 1)).toBe('bgm/f1_boss_p1');
    expect(resolveBgmFor(manifest, 1, 'boss', 'combat', 3)).toBe('bgm/f1_boss_p3');
    expect(resolveBgmFor(manifest, 1, 'boss', 'combat', 9)).toBe('bgm/f1_boss_p3');
    expect(resolveBgmFor(manifest, 1, 'title', 'journey', 1)).toBe('bgm/title');
    expect(resolveBgmFor(manifest, 2, null, 'journey', 1)).toBe('bgm/floor_low');
    expect(resolveBgmFor(manifest, 2, 'boss', 'combat', 2)).toBe('bgm/boss');
  });

  it('지연 로드 대상 = 층 전용 곡(use.floor), 1층 5곡', () => {
    const lazy = manifest.entries
      .filter(isLazyBgm)
      .map((e) => e.id)
      .sort();
    expect(lazy).toEqual([...floorStateBgmIds(manifest, 1)].sort());
    expect(lazy).toHaveLength(5);
    expect(
      manifest.entries.find((e) => e.id === 'bgm/title') &&
        isLazyBgm(manifest.entries.find((e) => e.id === 'bgm/title')!),
    ).toBe(false);
  });

  it('변주: 직전과 다른 것, 하나뿐이면 그것', () => {
    const c = ['a', 'b', 'c'];
    for (let i = 0; i < 20; i++) expect(pickVariant(c, 'b', i / 20)).not.toBe('b');
    expect(pickVariant(['a'], 'a', 0.5)).toBe('a');
    expect(pickVariant([], undefined, 0)).toBeNull();
  });

  it('동시 재생: 같은 그룹 상한 → 그 그룹 가장 오래된 것, 전체 상한 → 우선순위 낮고 오래된 것, 모두 높으면 버림', () => {
    const lim = { maxSfx: 3, maxUi: 1, perGroupMax: 2, perGroupOverrides: { dash: 1 } };
    const v = (group: string, priority: number, at: number, ui = false) => ({ group, priority, at, ui });
    expect(allocateVoice([v('hit', 2, 0), v('hit', 2, 5)], { group: 'hit', priority: 2, ui: false }, lim)).toEqual({
      ok: true,
      steal: [0],
    });
    expect(allocateVoice([v('dash', 2, 0)], { group: 'dash', priority: 2, ui: false }, lim).steal).toEqual([0]);
    const full = [v('a', 1, 10), v('b', 1, 0), v('c', 3, 0)];
    expect(allocateVoice(full, { group: 'd', priority: 2, ui: false }, lim)).toEqual({ ok: true, steal: [1] });
    expect(
      allocateVoice([v('a', 4, 0), v('b', 4, 0), v('c', 4, 0)], { group: 'd', priority: 2, ui: false }, lim).ok,
    ).toBe(false);
    // UI 는 UI 상한만
    expect(allocateVoice([...full, v('ui', 0, 0, true)], { group: 'ui2', priority: 0, ui: true }, lim)).toEqual({
      ok: true,
      steal: [3],
    });
  });

  it('실제 매니페스트 믹싱: 상한 12·UI 2 · 덕킹 3규칙(보스 예고 → 효과음 −6·BGM −3, 피격 → 효과음 −3 150ms)', () => {
    const mix = mixingOf(manifest);
    expect(voiceLimitsOf(mix)).toMatchObject({ maxSfx: 12, maxUi: 2, perGroupMax: 3 });
    const rules = parseDucking(mix.ducking);
    // 61라운드 단계 3: 파훼·결정타 → 효과음 우선순위 2 이하 −4dB 300ms (이름 목록 규칙)
    expect(rules).toHaveLength(4);
    for (const g of ['sfx/boss1_break_cup', 'sfx/boss1_break_reel', 'sfx/break_finisher']) {
      const br = ducksFor(rules, { group: g, priority: 3 });
      expect(br, g).toHaveLength(1);
      expect(br[0]).toMatchObject({ db: -4, holdMs: 300, target: { bus: 'sfx', maxPriority: 2 } });
    }
    expect(ducksFor(rules, { group: 'sfx/break_count', priority: 3 })).toHaveLength(0);
    const boss = ducksFor(rules, { group: 'sfx/boss1_spin', priority: 4 });
    expect(boss.map((r) => r.target.bus).sort()).toEqual(['bgm', 'sfx']);
    const hurt = ducksFor(rules, { group: 'sfx/hit_player', priority: 3 });
    expect(hurt).toHaveLength(1);
    expect(hurt[0].holdMs).toBe(150);
    // 봉투: 공격 5ms 뒤 −3dB, 우선순위 3 효과음은 대상 아님
    const d = [startDuck(hurt[0], 0, 400)];
    expect(duckDbAt(d, 10, { bus: 'sfx', priority: 2 })).toBeCloseTo(-3);
    expect(duckDbAt(d, 10, { bus: 'sfx', priority: 3 })).toBe(0);
    expect(duckDbAt(d, 5 + 150 + 180 + 1, { bus: 'sfx', priority: 2 })).toBe(0);
  });

  it('지연 로드 형식: 기기가 재생할 수 있는 첫 URL', () => {
    const urls = ['a/x.ogg', 'a/x.m4a'];
    expect(pickPlayableUrl(urls, { ogg: true, m4a: true })).toBe('a/x.ogg');
    expect(pickPlayableUrl(urls, { ogg: false, m4a: true })).toBe('a/x.m4a');
    expect(pickPlayableUrl(urls, { ogg: false, m4a: false })).toBeNull();
  });
});
