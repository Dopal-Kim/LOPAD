import { describe, expect, it, vi } from 'vitest';
import { EventEmitter } from 'node:events';

vi.mock('phaser', () => ({ default: { Events: { EventEmitter } } }));

import { AUDIO_TRIGGERS } from './audioMap';
import { Events } from '../../core/EventBus';
import { markDeathVariant } from '../gore/goreHooks';
import { bodyFallSfx, goreGainOf, goreLayerGain, heartbeatRate, P21_SFX } from './audioP21';

function fire(event: string, payload: unknown) {
  return AUDIO_TRIGGERS.filter(
    (tr) => tr.event === event && tr.sfx !== undefined && (!tr.when || tr.when(payload as never)),
  ).map((tr) => ({
    sfx: typeof tr.sfx === 'function' ? tr.sfx(payload as never) : tr.sfx,
    delay: tr.delayMs ? tr.delayMs(payload as never) : 0,
  }));
}

describe('P21 효과음 연결 (sound §15)', () => {
  it('enemy:gore 결 → 살 층, amount ≥ 2 → blood_splat 110ms 늦게', () => {
    const p = { id: 'archer', x: 0, y: 0, dirX: 1, dirY: 0, weapon: 'katana', cut: 'slash', amount: 2 };
    expect(fire(Events.ENEMY_GORE, p)).toEqual([
      { sfx: 'sfx/flesh_slash', delay: 0 },
      { sfx: 'sfx/blood_splat', delay: 110 },
    ]);
    expect(fire(Events.ENEMY_GORE, { ...p, cut: 'pierce', amount: 1 })).toEqual([{ sfx: 'sfx/arrow_stick', delay: 0 }]);
    expect(goreLayerGain({ amount: 2, weapon: null })).toBeCloseTo(10 ** (-3 / 20));
  });

  it('사망 변형이 따라오면 enemy_death 대신 body_fall · 전용 사망음 적은 body_fall 생략', () => {
    markDeathVariant('archer');
    expect(fire(Events.ENEMY_DIED, { id: 'archer', elite: false }).map((f) => f.sfx)).toEqual([null]);
    expect(fire(Events.ENEMY_DIED, { id: 'charger', elite: false }).map((f) => f.sfx)).toEqual(['sfx/enemy_death']);
    const v = { id: 'archer', x: 0, y: 0, kind: 'archer', variant: 'collapse', dirX: 1, dirY: 0 } as const;
    expect(bodyFallSfx(v)).toBe(P21_SFX.bodyFall);
    expect(bodyFallSfx({ ...v, armored: true })).toBe(P21_SFX.bodyFallArmor);
    expect(bodyFallSfx({ ...v, id: 'peddler' })).toBeNull();
    expect(bodyFallSfx({ ...v, variant: 'drown' })).toBeNull();
    expect(fire(Events.ENEMY_DEATH_VARIANT, { ...v, variant: 'bisect' }).map((f) => f.sfx)).toEqual([
      P21_SFX.bodyFall,
      P21_SFX.dismember,
    ]);
  });

  it('처형 execute_hit 은 결정타(impactMs)에 · 심장 박동 속도 · 고어 설정 끄기·낮추기', () => {
    const ex = fire(Events.PLAYER_EXECUTE, { target: 'archer', x: 0, y: 0, weapon: 'dagger', ms: 450, impactMs: 248 });
    expect(ex).toEqual([
      { sfx: P21_SFX.executeHit, delay: 248 },
      { sfx: P21_SFX.fleshStab, delay: 248 },
    ]);
    expect(heartbeatRate(0.25)).toBe(1);
    expect(heartbeatRate(0.05)).toBeCloseTo(1.15);
    const levels = { '0': { mute: ['sfx/flesh_slash'] }, '1': { gainDb: { 'sfx/flesh_slash': -6 } } };
    expect(goreGainOf(levels, 'sfx/flesh_slash', 0)).toBe(0);
    expect(goreGainOf(levels, 'sfx/flesh_slash', 1)).toBeCloseTo(0.501, 2);
    expect(goreGainOf(levels, 'sfx/flesh_slash', 2)).toBe(1);
    expect(goreGainOf(levels, 'sfx/body_fall', 0)).toBe(1);
  });
});
