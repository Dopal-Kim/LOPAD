import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { mixingOf, type AudioManifest } from './audioDefs';
import {
  allocateVoice,
  inTraitLayer,
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

  it('62라운드 P0-5: 수련장(training) 등 보스가 아닌 상태는 1층에서도 보스 국면 곡이 아니라 자기 상태 곡', () => {
    expect(resolveBgmFor(manifest, 1, 'training', 'journey', 1)).toBe('bgm/training');
    expect(resolveBgmFor(manifest, 1, 'training', 'combat', 3)).toBe('bgm/training');
    expect(resolveBgmFor(manifest, null, 'training', 'journey', 1)).toBe('bgm/training');
    expect(resolveBgmFor(manifest, 1, 'emperor', 'combat', 1)).toBe('bgm/f1_boss_p1');
  });

  it('지연 로드 대상 = 층 전용 곡(use.floor), 1층 6곡 (P19 전투 타악 층 포함)', () => {
    const lazy = manifest.entries
      .filter(isLazyBgm)
      .map((e) => e.id)
      .sort();
    expect(lazy).toEqual([...floorStateBgmIds(manifest, 1)].sort());
    expect(lazy).toHaveLength(6);
    expect(lazy).toContain('bgm/f1_jan_perc');
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

  it('실제 매니페스트 믹싱: 상한 12·UI 2 · 덕킹 15규칙(보스 예고 → 효과음 −6·BGM −3, 피격 → 효과음 −3 150ms)', () => {
    const mix = mixingOf(manifest);
    expect(voiceLimitsOf(mix)).toMatchObject({ maxSfx: 12, maxUi: 2, perGroupMax: 3 });
    const rules = parseDucking(mix.ducking);
    // 61라운드 단계 3: 파훼·결정타 → 효과음 우선순위 2 이하 −4dB 300ms (이름 목록 규칙)
    // 61 단계 6: 전환음 → 효과음 −8·BGM −4, 도장 → 효과음(1 이하) −4 (줍기류 대상 규칙은 그룹 대상이라 아직 해석 안 함)
    // 62 루프 2 (sound §13): 막타 슬로모 → 효과음 −5·BGM −4 280ms · 사망 슬로모 → 효과음 −10·BGM −12 · 층 끝 → BGM −6
    // P19 (sound §14): 벽꽝·볼링 → 효과음 −3 120ms · 큰 폭발 → 효과음 −4 200ms · BGM −3 300ms
    expect(rules).toHaveLength(15);
    for (const g of ['sfx/wall_slam_wall', 'sfx/wall_slam_prop', 'sfx/wall_slam_pillar', 'sfx/enemy_bowl'])
      expect(
        ducksFor(rules, { group: g, priority: 3 }).map((r) => [r.target.bus, r.db, r.holdMs]),
        g,
      ).toEqual([['sfx', -3, 120]]);
    for (const g of ['sfx/explode_large', 'sfx/bomber_blast'])
      expect(
        ducksFor(rules, { group: g, priority: 2 })
          .map((r) => [r.target.bus, r.db, r.holdMs])
          .sort(),
        g,
      ).toEqual([
        ['bgm', -3, 300],
        ['sfx', -4, 200],
      ]);
    const lk = ducksFor(rules, { group: 'sfx/last_kill_slow', priority: 3 });
    expect(lk.map((r) => [r.target.bus, r.db, r.holdMs]).sort()).toEqual([
      ['bgm', -4, 280],
      ['sfx', -5, 280],
    ]);
    const ds = ducksFor(rules, { group: 'sfx/death_slow', priority: 4 }).filter((r) => r.db <= -10);
    expect(ds.map((r) => [r.target.bus, r.db]).sort()).toEqual([
      ['bgm', -12],
      ['sfx', -10],
    ]);
    expect(ducksFor(rules, { group: 'sfx/floor_end_sting', priority: 3 }).map((r) => [r.target.bus, r.db])).toEqual([
      ['bgm', -6],
    ]);
    // 파훼 줄 첫 괄호 안에 기둥 무너짐 (62 루프 2 음향 고침)
    expect(ducksFor(rules, { group: 'sfx/boss1_pillar_collapse', priority: 3 }).map((r) => r.db)).toEqual([-4]);
    const tr = ducksFor(rules, { group: 'sfx/transition_enter', priority: 3 });
    expect(tr.map((r) => r.target.bus).sort()).toEqual(['bgm', 'sfx']);
    expect(ducksFor(rules, { group: 'sfx/training_stamp', priority: 3 }).map((r) => r.db)).toEqual([-4]);
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

describe('61 단계 5 sound §11 개성 발동 특색 층', () => {
  it('trait_ 층은 전체 동시 상한을 넘으면 그 층 가장 오래된 것을 끊고, trait_manifest 는 층이 아니다', () => {
    const lim = {
      maxSfx: 12,
      maxUi: 2,
      perGroupMax: 3,
      perGroupOverrides: {},
      traitLayer: { ids: new Set<string>(), max: 3 },
    };
    const v = (group: string, at: number) => ({ group, priority: 1, ui: false, at });
    const active = [v('sfx/trait_pull', 1), v('sfx/trait_slam', 2), v('sfx/trait_ignite', 3), v('sfx/hit_enemy', 0)];
    expect(allocateVoice(active, { group: 'sfx/trait_bind', priority: 1, ui: false }, lim)).toEqual({
      ok: true,
      steal: [0],
    });
    expect(inTraitLayer('sfx/trait_manifest', lim.traitLayer)).toBe(false);
    expect(inTraitLayer('sfx/trait_katana_k_edgeLift', lim.traitLayer)).toBe(true);
  });
});
