import { describe, expect, it, vi } from 'vitest';
import { EventEmitter } from 'node:events';

// EventBus 가 Phaser 를 import 하므로(window 필요) 이벤트 이미터만 node 것으로 대체한다 (audioLoop2.test 와 같다)
vi.mock('phaser', () => ({ default: { Events: { EventEmitter } } }));

import { Events, type TransitionBeginPayload } from '../../core/EventBus';
import { FADE_FALLBACK, P14_SFX, TRAINING_AUDIO_TRIGGERS } from './audioTraining';

const tr = TRAINING_AUDIO_TRIGGERS.find((t) => t.event === Events.TRANSITION_BEGIN)!;
const p = (mode: TransitionBeginPayload['mode']): TransitionBeginPayload => ({ id: 1, mode, region: 'waste' });
const sfx = (mode: TransitionBeginPayload['mode']) => (typeof tr.sfx === 'function' ? tr.sfx(p(mode)) : tr.sfx);

describe('62 H 전환 소리 — fade', () => {
  it('fade = transition_fade, 없으면 transition_exit (작고 빠르게)', () => {
    expect(sfx('fade')).toEqual([P14_SFX.fade, P14_SFX.exit]);
    expect(tr.gain?.(p('fade'), P14_SFX.exit)).toBe(FADE_FALLBACK.GAIN);
    expect(tr.rate?.(p('fade'), P14_SFX.exit)).toBe(FADE_FALLBACK.RATE);
    expect(tr.gain?.(p('fade'), P14_SFX.fade)).toBe(1);
    expect(tr.rate?.(p('fade'), P14_SFX.fade)).toBe(1);
  });
  it('다른 mode 는 그대로 (exitRoom 의 exit 는 원래 크기·속도)', () => {
    expect(sfx('enterNode')).toEqual([P14_SFX.enter]);
    expect(sfx('floor')).toEqual([P14_SFX.floor, P14_SFX.enter]);
    expect(tr.gain?.(p('exitRoom'), P14_SFX.exit)).toBe(1);
    expect(tr.rate?.(p('exitRoom'), P14_SFX.exit)).toBe(1);
  });
});
