import { describe, expect, it, vi } from 'vitest';
import { EventEmitter } from 'node:events';

// audioMap → EventBus·contract 가 Phaser 를 import 하므로(window 필요) 이벤트 이미터만 node 것으로 대체한다
vi.mock('phaser', () => ({ default: { Events: { EventEmitter } } }));

import { AUDIO_TRIGGERS } from './audioMap';
import { Events } from '../../core/EventBus';
import { CombatLayerGate, P19_SFX, chainRate, igniteJustPlayed, p19Moments, streakSfx, swellRate } from './audioP19';
import { duckDbAt, hitStackDb, startDuck, type DuckRule } from './audioMix';

function fire(event: string, payload: unknown) {
  return AUDIO_TRIGGERS.filter((tr) => tr.event === event && (!tr.when || tr.when(payload as never))).map((tr) => ({
    sfx: typeof tr.sfx === 'function' ? tr.sfx(payload as never) : (tr.sfx ?? null),
    rate: tr.rate ? tr.rate(payload as never) : 1,
    loop: tr.loop ?? null,
    stop: tr.stop ?? [],
  }));
}
const sounds = (event: string, payload: unknown) =>
  fire(event, payload)
    .map((f) => f.sfx)
    .filter((x) => x !== null);

describe('P19 계약 sound §14 효과음 연결', () => {
  it('무기 타격: hit_<무기>(없으면 hit_enemy) · 환경 피해·틱은 타격음 없음 · 치명은 위에 겹침', () => {
    const base = { id: 'conscript', amount: 5, died: false, tick: false };
    expect(sounds(Events.ENEMY_DAMAGED, { ...base, crit: false, weapon: 'katana' })).toEqual([
      [P19_SFX.hit('katana'), 'sfx/hit_enemy'],
      'sfx/enemy_hurt',
    ]);
    expect(sounds(Events.ENEMY_DAMAGED, { ...base, crit: true, weapon: 'bow' })).toEqual([
      [P19_SFX.hit('bow'), 'sfx/hit_enemy'],
      P19_SFX.hitEnemyCrit,
      'sfx/enemy_hurt',
    ]);
    // 폭발·벽꽝 등 (weapon 없음): 몸 보조음만
    expect(sounds(Events.ENEMY_DAMAGED, { ...base, crit: false })).toEqual(['sfx/enemy_hurt']);
    expect(sounds(Events.ENEMY_DAMAGED, { ...base, crit: false, tick: true, weapon: 'dagger' })).toEqual([
      'sfx/enemy_hurt',
    ]);
  });

  it('반응: 움찔/버팀 깨짐 · 넉백 1단 무음 · 벽꽝 면 · 볼링 연쇄 1.06 · 착지 · 낙하 구역', () => {
    expect(sounds(Events.ENEMY_STAGGERED, { kind: 'flinch' })).toEqual([P19_SFX.flinch]);
    expect(sounds(Events.ENEMY_STAGGERED, { kind: 'stagger' })).toEqual([P19_SFX.staggerBreak]);
    expect(sounds(Events.ENEMY_KNOCKED, { tier: 1 })).toEqual([]);
    expect(sounds(Events.ENEMY_KNOCKED, { tier: 3 })).toEqual(['sfx/knock_wind3']);
    expect(sounds(Events.ENEMY_WALL_SLAM, { surface: 'pillar' })).toEqual(['sfx/wall_slam_pillar']);
    expect(fire(Events.ENEMY_BOWLED, { chain: 0 })[0].rate).toBe(1);
    expect(fire(Events.ENEMY_BOWLED, { chain: 1 })[0].rate).toBe(1.06);
    expect(sounds(Events.ENEMY_LANDED, { slam: true })).toEqual([P19_SFX.landSlam]);
    expect(sounds(Events.ENEMY_FELL, { zone: 'water' })).toEqual(['sfx/fall_water']);
  });

  it('폭발 크기 + 연쇄 겹침 (chain>3 속도 상한 1.26) · 자폭병 폭발과 같은 순간이면 크기 소리 쉼', () => {
    p19Moments.bomberBlastAt = -Infinity;
    expect(sounds(Events.HAZARD_EXPLODED, { kind: 'still', chain: 0 })).toEqual(['sfx/explode_large']);
    expect(sounds(Events.HAZARD_EXPLODED, { kind: 'cask', chain: 2 })).toEqual([
      'sfx/explode_mid',
      'sfx/explode_chain2',
    ]);
    expect(sounds(Events.HAZARD_EXPLODED, { kind: 'cask', chain: 7 })).toContain('sfx/explode_chain3');
    expect(chainRate(3)).toBe(1);
    expect(chainRate(4)).toBeCloseTo(2 ** (2 / 12));
    expect(chainRate(20)).toBe(1.26);
    expect(sounds(Events.ENEMY_ATTACK, { id: 'bomber', kind: 'explode', phase: 'blast' })).toEqual([
      P19_SFX.bomberBlast,
    ]);
    expect(sounds(Events.HAZARD_EXPLODED, { kind: 'cask', chain: 0 })).toEqual([]);
  });

  it('점화(반경 ≥ 3칸 0.9) 뒤 같은 순간 drunk_ignite 는 쉰다 · 연속 처치 2·4·6 이상 짝수', () => {
    p19Moments.hazardIgnitedAt = -Infinity;
    expect(sounds(Events.POOL_IGNITED, {})).toEqual(['sfx/drunk_ignite']);
    expect(fire(Events.HAZARD_IGNITED, { radiusTiles: 3.5 })[0]).toMatchObject({ sfx: P19_SFX.ignite, rate: 0.9 });
    expect(igniteJustPlayed()).toBe(true);
    expect(sounds(Events.POOL_IGNITED, {})).toEqual([]);
    expect([2, 3, 4, 5, 6, 7, 8].map(streakSfx)).toEqual([
      'sfx/streak_2',
      null,
      'sfx/streak_4',
      null,
      'sfx/streak_6',
      null,
      'sfx/streak_6',
    ]);
  });

  it('새 적: 고수 rally·beat · 처치 drummer_death(enemy_death 대신) · 자폭병 루프는 마지막 달리기가 끝날 때 멈춤', () => {
    expect(sounds(Events.ENEMY_ATTACK, { id: 'drummer', kind: 'drum', phase: 'rally' })).toEqual([
      P19_SFX.drummerRally,
    ]);
    expect(sounds(Events.ENEMY_ATTACK, { id: 'drummer', kind: 'drum', phase: 'beat' })).toEqual([P19_SFX.drummerBeat]);
    expect(sounds(Events.ENEMY_DIED, { id: 'drummer' })).toEqual([P19_SFX.drummerDeath]);
    expect(sounds(Events.ENEMY_DIED, { id: 'bomber' })).toEqual([]);
    p19Moments.bombersRunning = 0;
    const run = { id: 'bomber', kind: 'explode', phase: 'run' };
    const end = { id: 'bomber', kind: 'explode', phase: 'runEnd' };
    expect(fire(Events.ENEMY_ATTACK, run).map((f) => f.loop)).toContain(P19_SFX.bomberFuse);
    fire(Events.ENEMY_ATTACK, run);
    expect(fire(Events.ENEMY_ATTACK, end).some((f) => f.stop.includes(P19_SFX.bomberFuse))).toBe(false);
    expect(fire(Events.ENEMY_ATTACK, end).some((f) => f.stop.includes(P19_SFX.bomberFuse))).toBe(true);
    // 예고: bomber_swell, 속도 = clamp(1000/ms, 0.85, 1.2)
    expect(fire(Events.ENEMY_TELEGRAPH, { id: 'bomber', kind: 'fuse', ms: 800 })[0]).toMatchObject({
      sfx: P19_SFX.bomberSwell,
      rate: 1.2,
    });
    expect(swellRate(1000)).toBe(1);
    expect(swellRate(2000)).toBe(0.85);
  });

  it('타격음 층: 같은 id 30ms 안 버림 · 40ms 안 몰리면 둘째부터 −3dB (최저 −9)', () => {
    const layer = { ids: new Set(['a', 'b']), max: 4, windowMs: 40, stackDb: -3, minGapMs: 30 };
    expect(hitStackDb([], 'a', 0, layer)).toBe(0);
    expect(hitStackDb([{ group: 'a', at: 0 }], 'a', 20, layer)).toBeNull();
    expect(hitStackDb([{ group: 'a', at: 0 }], 'b', 20, layer)).toBe(-3);
    const many = [0, 1, 2, 3, 4].map((at) => ({ group: 'b', at }));
    expect(hitStackDb(many, 'a', 10, layer)).toBe(-9);
    expect(hitStackDb([{ group: 'a', at: 0 }], 'a', 50, layer)).toBe(0);
  });

  it('덕킹을 일으킨 소리 자신은 눌리지 않는다 (bomber_blast 우선순위 2)', () => {
    const rule: DuckRule = {
      trigger: { kind: 'groups', groups: ['sfx/bomber_blast'] },
      target: { bus: 'sfx', maxPriority: 2 },
      db: -4,
      attackMs: 0,
      releaseMs: 0,
      holdMs: 200,
    };
    const self = {};
    const d = [startDuck(rule, 0, 1000, self)];
    expect(duckDbAt(d, 10, { bus: 'sfx', priority: 2 })).toBe(-4);
    expect(duckDbAt(d, 10, { bus: 'sfx', priority: 2 }, self)).toBe(0);
  });

  it('전투 BGM 강도: 적 ≥ 6 켬 · ≤ 3 이 2초 이어지면 끔(켠 뒤 최소 6초) · 보스 방은 끔', () => {
    const g = new CombatLayerGate();
    g.set(5, false, 0);
    expect(g.isOn(0)).toBe(false);
    g.set(6, false, 100);
    expect(g.isOn(100)).toBe(true);
    g.set(2, false, 1000);
    expect(g.isOn(4000)).toBe(true); // 켠 뒤 6초 안
    expect(g.isOn(6000)).toBe(true); // 켠 뒤 5.9초
    expect(g.isOn(6200)).toBe(false); // 6.1초 · 낮은 상태 2초 넘음
    g.set(8, false, 7000);
    expect(g.isOn(7000)).toBe(true);
    g.set(8, true, 7100);
    expect(g.isOn(7100)).toBe(false);
  });
});
