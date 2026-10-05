import { describe, expect, it } from 'vitest';
import {
  KEY_GLYPH,
  currentVerbItems,
  snapshotVerbItems,
  glyphWidth,
  parseKey,
  rowOffsets,
  verbItems,
} from './keyGuideView';

describe('keyGuideView', () => {
  it('마우스 이름 여러 꼴을 읽는다 (홀드 포함)', () => {
    for (const k of ['lmb', 'LMB', '좌클릭', 'mouse:left', 'left'])
      expect(parseKey(k)).toEqual({ kind: 'mouse', button: 'left', hold: false });
    for (const k of ['rmb', '우클릭', 'mouse-right'])
      expect(parseKey(k)).toEqual({ kind: 'mouse', button: 'right', hold: false });
    for (const k of ['lmbHold', 'lmb_hold', 'hold:lmb', '좌 홀드', '좌클릭 길게'])
      expect(parseKey(k)).toEqual({ kind: 'mouse', button: 'left', hold: true });
  });

  it('키캡: 한 글자는 대문자, 이름 있는 키는 정한 글, Space 는 넓게', () => {
    expect(parseKey('q')).toEqual({ kind: 'key', label: 'Q', wide: false });
    expect(parseKey('space')).toEqual({ kind: 'key', label: 'Space', wide: true });
    expect(parseKey(' ')).toEqual({ kind: 'key', label: 'Space', wide: true });
    expect(parseKey('스페이스')).toEqual({ kind: 'key', label: 'Space', wide: true });
    expect(parseKey('Escape')).toEqual({ kind: 'key', label: 'Esc', wide: false });
    expect(parseKey('ArrowUp')).toEqual({ kind: 'key', label: '↑', wide: false });
  });

  it('폭: 마우스 고정, 키캡은 글 + 여백(최소 16, 넓은 키 34)', () => {
    expect(glyphWidth(parseKey('lmb'), 0)).toBe(KEY_GLYPH.mouseW);
    expect(glyphWidth(parseKey('Q'), 10)).toBe(18);
    expect(glyphWidth(parseKey('Q'), 4)).toBe(16);
    expect(glyphWidth(parseKey('space'), 20)).toBe(34);
    expect(glyphWidth(parseKey('space'), 40)).toBe(48);
  });

  it('한 줄 배치', () => {
    expect(rowOffsets([10, 20, 5], 4)).toEqual({ xs: [0, 14, 38], w: 43 });
    expect(rowOffsets([], 4)).toEqual({ xs: [], w: 0 });
  });

  it('동사 목록 → 안내 줄 (빈 이름은 뺀다, 못 쓰면 흐림)', () => {
    expect(
      verbItems([
        { input: 'lmb', name: '연격' },
        { input: 'rmb', name: ' ' },
        { input: 'lmbHold', name: '검기 해방', disabled: true },
      ]),
    ).toEqual([
      { keys: ['lmb'], label: '연격', dim: false },
      { keys: ['lmbHold'], label: '검기 해방', dim: true },
    ]);
    expect(verbItems(null)).toEqual([]);
  });

  it('지금 스냅샷으로 만든 안내: 좌·우·Space (+F)', () => {
    const t = (k: string) => ({ verbAttack: '공격', verbDash: '대쉬', verbCarry: '넣기·뽑기' })[k] ?? k;
    expect(
      currentVerbItems({ weapon: { secondaryName: '가드·패링' }, carry: { key: 'F' } }, t).map((i) => i.label),
    ).toEqual(['공격', '가드·패링', '대쉬', '넣기·뽑기']);
    expect(currentVerbItems({ weapon: { secondaryName: '' }, carry: null }, t)[1].label).toBe('보조 동작');
  });

  it('시스템 4동사가 있으면 그것으로 (키 글 그대로 해석)', () => {
    const t = (k: string) => k;
    const items = snapshotVerbItems(
      {
        weapon: { secondaryName: '가드·패링' },
        carry: null,
        weaponVerbs: {
          weapon: 'katana',
          verbs: [
            { slot: 'attack', key: '좌클릭', name: '3연격', hint: '', branch: null },
            { slot: 'signature', key: '우클릭', name: '가드 · 패링', hint: '', branch: null },
            { slot: 'dash', key: 'Space', name: '대쉬 · 일섬', hint: '', branch: null },
            { slot: 'hold', key: '좌클릭 길게', name: '발도', hint: '', branch: null },
          ],
        },
      },
      t,
    );
    expect(items.map((i) => i.label)).toEqual(['3연격', '가드 · 패링', '대쉬 · 일섬', '발도']);
    expect(parseKey(items[3].keys[0])).toEqual({ kind: 'mouse', button: 'left', hold: true });
    expect(snapshotVerbItems({ weapon: { secondaryName: 'x' }, weaponVerbs: null }, t)).toHaveLength(3);
  });
});
