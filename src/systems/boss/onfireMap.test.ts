import { describe, expect, it } from 'vitest';
import { forceOut, newBurnState, stepBurn } from './burnMath';
import { chooseOverlay, lyingOffset, mappedActions, type LyingMap } from './onfireMap';

/** 아트 ffafe90 boss1_onfire_down 매핑 (메인 세션 전달값) */
const DOWN: LyingMap & { standFor: Record<string, number[]> } = {
  useFor: { fall: [2, 3, 4, 5, 6, 7, 8, 9, 10, 11], death: [8, 9, 10, 11, 12, 13] },
  standFor: { fall: [0, 1, 12, 13, 14, 15, 16], death: [0, 1, 2, 3, 4, 5, 6, 7] },
  frameOffsets: {
    fall: { '2': [0, -43], '3': [0, -12], '4': [0, 4], '6': [0, 0] },
    death: { '8': [0, -36], '10': [0, -10] },
  },
};

describe('54라운드 Q23·Q28 누운 자세 불길 선택', () => {
  it('useFor 열 = 누운 불길(frameOffsets 도트), standFor·그 밖 = 서 있는 불길', () => {
    expect(chooseOverlay('fall', 2, DOWN)).toEqual({ sheet: 'lying', dx: 0, dy: -43 });
    expect(chooseOverlay('fall', 6, DOWN)).toEqual({ sheet: 'lying', dx: 0, dy: 0 });
    expect(chooseOverlay('fall', 7, DOWN)).toEqual({ sheet: 'lying', dx: 0, dy: 0 });
    expect(chooseOverlay('fall', 1, DOWN)).toEqual({ sheet: 'stand' });
    expect(chooseOverlay('fall', 12, DOWN)).toEqual({ sheet: 'stand' });
    expect(chooseOverlay('death', 7, DOWN)).toEqual({ sheet: 'stand' });
    expect(chooseOverlay('death', 8, DOWN)).toEqual({ sheet: 'lying', dx: 0, dy: -36 });
    expect(chooseOverlay('death', 13, DOWN)).toEqual({ sheet: 'lying', dx: 0, dy: 0 });
    expect(chooseOverlay('walk', 3, DOWN)).toEqual({ sheet: 'stand' });
    expect(chooseOverlay(null, 3, DOWN)).toEqual({ sheet: 'stand' });
  });

  it('누운 시트가 없으면 fall·death 동안 숨김 (54라운드 2차 동작)', () => {
    expect(chooseOverlay('fall', 1, null)).toEqual({ sheet: 'hide' });
    expect(chooseOverlay('death', 9, null)).toEqual({ sheet: 'hide' });
    expect(chooseOverlay('idle', 0, null)).toEqual({ sheet: 'stand' });
  });

  it('useFor 가 없는 누운 시트는 fall·death 전체를 누운 불길로', () => {
    expect(chooseOverlay('fall', 0, {})).toEqual({ sheet: 'lying', dx: 0, dy: 0 });
    expect(chooseOverlay('slam', 0, {})).toEqual({ sheet: 'stand' });
  });

  it('옮김 값 형식이 이상하면 0', () => {
    expect(lyingOffset({ frameOffsets: { fall: { '2': ['a' as unknown as number] } } }, 'fall', 2)).toEqual({
      dx: 0,
      dy: 0,
    });
  });

  it('판단할 동작 = 누운 동작 + 매핑 키', () => {
    expect(mappedActions(null).sort()).toEqual(['death', 'fall']);
    expect(mappedActions({ useFor: { kneel: [1] }, standFor: { fall: [0] } }).sort()).toEqual([
      'death',
      'fall',
      'kneel',
    ]);
  });

  it('죽음 마지막 프레임: 타는 중이면 out, 꺼지는 중·꺼짐이면 그대로', () => {
    const T = { igniteMs: 260, outMs: 420, lingerMs: 1000 };
    const s = newBurnState();
    expect(forceOut(s, 0)).toBe(false);
    stepBurn(s, true, 0, T);
    stepBurn(s, true, 300, T);
    expect(s.phase).toBe('loop');
    expect(forceOut(s, 500)).toBe(true);
    expect(s).toMatchObject({ phase: 'out', since: 500 });
    expect(forceOut(s, 600)).toBe(false);
    stepBurn(s, false, 920, T);
    expect(s.phase).toBe('off');
  });
});
