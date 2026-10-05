import { describe, expect, it } from 'vitest';
import { stateLight } from './structureLight';

describe('61라운드 구조물 상태별 광원 (art §24 lightByState)', () => {
  const light = { radius: 160, color: '#e8b858' };
  it('객체 = 그 광원 · 문자열 = 기본 light · null·없는 상태 = 꺼짐 · 표 없음 = undefined', () => {
    const cask = { lightByState: { ready: { radius: 120 } } };
    expect(stateLight(cask, 'ready')).toEqual({ radius: 120 });
    expect(stateLight(cask, 'idle')).toBeNull();
    const sign = { light, lightByState: { active: '켜짐', idle: null } };
    expect(stateLight(sign, 'active')).toBe(light);
    expect(stateLight(sign, 'idle')).toBeNull();
    expect(stateLight({ light }, 'idle')).toBeUndefined();
  });
});
