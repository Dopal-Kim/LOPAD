import { describe, expect, it } from 'vitest';
import { kenkiFxId, kenkiFxIds } from '../fx/fxIds';
import { headTopDot, nextCrack, rimFits } from './bossArtRules';

describe('61 E 아트 2 보스 그림 연결 (순수 규칙)', () => {
  it('기둥 균열: 충돌마다 한 단(crack1→2→3), 61 P13: 3단 다음 충돌에서 무너짐(단 4), 그 뒤는 없음', () => {
    expect(nextCrack(0, 3)).toEqual({ stage: 1, state: 'crack1', collapse: false });
    expect(nextCrack(2, 3)).toEqual({ stage: 3, state: 'crack3', collapse: false });
    expect(nextCrack(3, 3)).toEqual({ stage: 4, state: 'collapse', collapse: true });
    expect(nextCrack(4, 3)).toBeNull();
  });

  it('파훼 고리 머리 꼭대기: 동작·방향·열 → 없으면 idle 같은 방향 0 열 → 없으면 null', () => {
    const t = { idle: { down: [[10, 20]] }, fall: { down: [null, [30, 40]] } };
    expect(headTopDot(t, 'fall', 'down', 1)).toEqual([30, 40]);
    expect(headTopDot(t, 'fall', 'down', 0)).toEqual([10, 20]);
    expect(headTopDot(t, 'slam', 'down', 3)).toEqual([10, 20]);
    expect(headTopDot(t, 'slam', 'up', 0)).toBeNull();
    expect(headTopDot(null, 'idle', 'down', 0)).toBeNull();
  });

  it('림 시트는 지금 VRAM + 추정치가 예산 안일 때만', () => {
    expect(rimFits(450, 42, 500)).toBe(true);
    expect(rimFits(470, 42, 500)).toBe(false);
  });

  it('칼 발도 검기 단 그림: 소모한 단 1~3 (그 이상은 3), 0 이면 없음 · 검기 무기만 목록', () => {
    expect(kenkiFxId('katana_iai', 0)).toBeNull();
    expect(kenkiFxId('katana_iai', 2)).toBe('katana_iai_ki2');
    expect(kenkiFxId('katana_iai', 5)).toBe('katana_iai_ki3');
    expect(kenkiFxIds('katana', { gauge: { kind: 'kenki' } })).toEqual([
      'katana_iai_ki1',
      'katana_iai_ki2',
      'katana_iai_ki3',
    ]);
    expect(kenkiFxIds('dagger', { gauge: { kind: 'brand' } })).toEqual([]);
  });
});
