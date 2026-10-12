/**
 * 62 루프 2 시스템 G (UI E·F 요청): 상인 말하기 머리 · 외상 대가 아이콘 · 저주 문구 용어집 · 보이는 그림 윗변 · 주인공 화면 자리
 */
import { describe, expect, it } from 'vitest';
import curses from '../../../data/curses.json';
import pack from '../../../parts/story/text-pack-63-loop2.json';
import { creditLine, merchantScene } from '../../scenes/game/shopTalkUi';
import { firstOpaqueRow } from '../sprites/opaqueTop';
import { gameState } from '../../core/GameState';
import { buildSnapshot } from '../../contract/snapshot';

const banned = (pack as unknown as { glossary: { bannedWords: string[] } }).glossary.bannedWords;

describe('62 G 종군 상인 말하기 (shopTalk)', () => {
  it('머리 = 사연 메뉴 꼴 (말하는 이 · 초상 · 첫 마디, 설명 없음)', () => {
    const s = merchantScene('종군 상인', '어서 오게.', { key: 'npc_merchant_st', frame: '0' });
    expect(s).toMatchObject({
      id: 'merchant',
      name: '종군 상인',
      speaker: '종군 상인',
      greet: '어서 오게.',
      intro: [],
      portrait: { key: 'npc_merchant_st', frame: '0' },
    });
    expect(merchantScene('종군 상인', '', null).portrait).toBeUndefined();
  });

  it("'외상을 단다' = 저주 아이콘 한 칸 + 금지어 없는 대체 글", () => {
    const l = creditLine('credit', '외상을 단다');
    expect(l.key).toBe('credit');
    expect(l.costs).toEqual([{ kind: 'curse', label: '저주 외상' }]);
    expect(l.detail).toContain('장터');
    expect(banned.filter((w) => (l.detail ?? '').includes(w) || l.costs!.some((c) => c.label.includes(w)))).toEqual([]);
  });

  it('저주 이름·이득·대가 문구에 용어집 금지어가 없다 (UiCurse 로 그대로 나간다)', () => {
    const texts = curses.items.flatMap((c) => [c.name, c.benefit, c.penalty]);
    expect(texts.flatMap((t) => banned.filter((w) => t.includes(w)).map((w) => `${w} ← ${t}`))).toEqual([]);
  });
});

describe('62 G 보이는 그림 윗변 (노점 카드 자리)', () => {
  const rgba = (w: number, h: number, opaque: [number, number][]) => {
    const d = new Uint8ClampedArray(w * h * 4);
    for (const [x, y] of opaque) d[(y * w + x) * 4 + 3] = 255;
    return d;
  };
  it('처음 보이는 줄', () => {
    expect(firstOpaqueRow(rgba(4, 6, [[2, 3]]), 4, 6)).toBe(3);
    expect(firstOpaqueRow(rgba(4, 6, [[0, 0]]), 4, 6)).toBe(0);
    expect(firstOpaqueRow(rgba(4, 6, []), 4, 6)).toBe(6);
  });
  it('흐린 픽셀(알파 16 미만)은 보이지 않는 것으로', () => {
    const d = rgba(2, 3, [[1, 2]]);
    d[(0 * 2 + 0) * 4 + 3] = 8;
    expect(firstOpaqueRow(d, 2, 3)).toBe(2);
  });
});

describe('62 G 주인공 화면 자리 (UiSnapshot.hero)', () => {
  it('생략하면 null · 주면 복사본', () => {
    gameState.startRun('hero', 'katana');
    const base = {
      layout: null,
      visited: new Set<string>(),
      cleared: new Set<string>(),
      bossName: null,
      paused: false,
      menu: null,
      inCombat: false,
      sprinting: false,
      warp: { ready: false, blocked: 'busy' as const, targets: [], warping: false },
    };
    expect(buildSnapshot(base).hero).toBeNull();
    const hero = { head: { x: 480, y: 200 }, body: { x: 480, y: 236 }, feet: { x: 480, y: 272 }, visible: true };
    const s = buildSnapshot({ ...base, hero });
    expect(s.hero).toEqual(hero);
    s.hero!.head.y = 0;
    expect(hero.head.y).toBe(200);
  });
});
