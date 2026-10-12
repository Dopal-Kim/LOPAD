/**
 * 62 루프 2 시스템 D 순수 규칙 테스트: 사연 아이콘 줄 · 웨이브 진입 방향 · 로딩 팁 · 이어하기 자동 저장 형식 · 세트피스·그을음 자리 ·
 * 노점 카드 대응 · 사연 말 걸기 데이터 (스토리 63 팩 합침)
 */
import { describe, expect, it } from 'vitest';
import { iconRow } from '../bundle2/eventIcons';
import { farFace, inSide, waveSideFor } from '../waveSides';
import { pickTip, tipAllowed } from '../loadingTips';
import { readSuspend } from '../save';
import { BUNDLE2, eventDef } from '../../data/bundle2';
import { LOADING_TIPS } from '../../data/loading';
import { ROUTE } from '../route';
import { cardIdOf, goodsArtOf, stallPositions } from './stallRules';
import { planHeroSetpiece, planSoot } from '../../world/heroSetpiece';
import { TileId, type FloorLayout } from '../mapgen';

describe('62 D P1-12 사연 아이콘 줄 (대가·보상)', () => {
  it('E3 독주를 건넨다: 대가 독주 −1 · 보상 숨김(?)', () => {
    const def = eventDef('conscript')!;
    const o = def.options!.find((x) => x.key === 'give')!;
    const r = iconRow(o.effects, def.talk!.options.give, {}, undefined, '?');
    expect(r.costs).toEqual([{ kind: 'potion', amount: 1, label: '독주 −1' }]);
    expect(r.rewards).toHaveLength(1);
    expect(r.rewards[0].hidden).toBe(true);
    expect(r.rewards[0].label).toBe('?');
  });

  it('E3 주머니를 턴다: 대가 다음 싸움 무리 +1 · 보상 전표 +30', () => {
    const def = eventDef('conscript')!;
    const o = def.options!.find((x) => x.key === 'rob')!;
    const r = iconRow(o.effects, def.talk!.options.rob, {}, undefined, '?');
    expect(r.costs.map((c) => [c.kind, c.label])).toEqual([['enemies', '다음 싸움 무리 +1']]);
    expect(r.rewards.map((c) => [c.kind, c.label])).toEqual([['gold', '전표 +30']]);
  });

  it('1층 사연 5종 모두 말 걸기 문장 · 선택지마다 결과 컷 한 줄 · NPC 사연은 시트', () => {
    for (const id of ['conscript', 'diary', 'tasting', 'offering', 'droppedLedger']) {
      const d = eventDef(id)!;
      expect(d.talk, id).toBeTruthy();
      for (const o of d.options ?? []) expect(d.talk!.options[o.key]?.cut, `${id}.${o.key}`).toBeTruthy();
    }
    expect(eventDef('conscript')!.talk!.npc?.sheet).toBe('npc_conscript');
    expect(eventDef('tasting')!.talk!.npc?.sheet).toBe('npc_brewer');
    expect(BUNDLE2.events.ui?.unknown).toBe('?');
  });

  it('E4 다듬는다 = 다시 뽑기 +1 (감각 대신, 63 팩 제안)', () => {
    const o = eventDef('diary')!.options!.find((x) => x.key === 'refine')!;
    expect(o.effects).toEqual([{ kind: 'reroll', value: 1 }]);
    const r = iconRow(o.effects, eventDef('diary')!.talk!.options.refine, {});
    expect(r.rewards[0].label).toBe('다시 뽑기 +1');
  });
});

describe('62 D P2-10 웨이브 진입 방향', () => {
  it('첫 웨이브 = 주인공 반대 면 · 마지막 = 사방 · 같은 쪽이 이어지지 않는다', () => {
    const c = { x: 0, y: 0 };
    expect(farFace({ x: -100, y: 0 }, c, 200, 100)).toBe('east');
    expect(farFace({ x: 0, y: 80 }, c, 200, 100)).toBe('north');
    for (let seed = 0; seed < 50; seed++) {
      const total = 6;
      const sides = Array.from({ length: total }, (_, i) => waveSideFor(i, total, seed * 7919, 'east'));
      expect(sides[0]).toBe('east');
      expect(sides[total - 1]).toBe('around');
      for (let i = 1; i < total - 1; i++) expect(sides[i]).not.toBe(sides[i - 1]);
    }
  });

  it('쪽 판정: 북은 가운데 위 · flank 는 주인공 좌우 멀리', () => {
    const c = { x: 0, y: 0 };
    const pl = { x: 0, y: 0 };
    expect(inSide('north', { x: 0, y: -60 }, c, 200, 100, pl)).toBe(true);
    expect(inSide('north', { x: 0, y: 60 }, c, 200, 100, pl)).toBe(false);
    expect(inSide('flank', { x: 150, y: 10 }, c, 200, 100, pl)).toBe(true);
    expect(inSide('flank', { x: 20, y: 10 }, c, 200, 100, pl)).toBe(false);
    expect(inSide('around', { x: 1, y: 1 }, c, 1, 1, pl)).toBe(true);
  });
});

describe('62 D P2-6 로딩 팁', () => {
  it('63 팩 18줄 · 숫자 없음 · 단서 조건 줄은 일기장에 단서가 있어야', () => {
    expect(LOADING_TIPS.length).toBe(18);
    const gated = LOADING_TIPS.filter((t) => t.requires);
    expect(gated.length).toBeGreaterThan(0);
    for (const t of gated) expect(tipAllowed(t, [])).toBe(false);
    expect(tipAllowed({ kind: 'lore', text: 'x', requires: 'clue.birthMask' }, ['birthMask'])).toBe(true);
  });

  it('같은 생 안 중복 없음 · 다 쓰면 처음부터', () => {
    let used: string[] = [];
    const seen = new Set<string>();
    const ok = LOADING_TIPS.filter((t) => tipAllowed(t, []));
    for (let i = 0; i < ok.length; i++) {
      const r = pickTip(LOADING_TIPS, [], used, (i * 0.37) % 1);
      expect(seen.has(r.tip!.text)).toBe(false);
      seen.add(r.tip!.text);
      used = r.used;
    }
    const again = pickTip(LOADING_TIPS, [], used, 0.5);
    expect(again.used).toHaveLength(1);
  });
});

describe('62 D P2-5 이어하기 자동 저장 형식', () => {
  it('맞는 형식만 받는다 · 깨지면 null (층 처음으로)', () => {
    const ok = readSuspend({
      floor: 1,
      currentId: 'n3',
      path: ['n0', 'n3'],
      cleared: ['n0'],
      nodeCleared: true,
      extras: {},
      shops: [],
      structures: null,
      birthPending: false,
      nodeKind: 'battle',
    });
    expect(ok?.currentId).toBe('n3');
    expect(ok?.nodeCleared).toBe(true);
    expect(ok?.nodeKind).toBe('battle');
    expect(readSuspend({ floor: 1, path: 'x' })).toBeNull();
    expect(readSuspend(null)).toBeNull();
    expect(readSuspend({ floor: 1, currentId: 3, path: [], cleared: [] })).toBeNull();
  });
});

describe('62 D 데이터 합침 (스토리 63 팩)', () => {
  it('노드 이름 바뀜 · 노드 고유 한 줄', () => {
    const f = ROUTE.floors.stage1;
    expect(f.names.boss).toEqual(['만취의 연회장']);
    expect(f.names.event).toEqual(['인적 끊긴 뒤뜰']);
    for (const list of Object.values(f.names)) for (const n of list ?? []) expect(f.nodeLines?.[n], n).toBeTruthy();
    expect(ROUTE.regions!.hall.name).toBe('연회장');
  });

  it('상인 대사 · 노점 문구 · 물건 카드', () => {
    expect(BUNDLE2.shop.talk?.merchant.speaker).toBe('종군 상인');
    expect(BUNDLE2.shop.cards?.items.heal?.name).toBe('뜨끈한 국밥 한 그릇');
    expect(BUNDLE2.shop.labels.reroll).toBe('다시 진열');
  });

  it('1층 단1·단3 웨이브 6 (P2-14)', () => {
    const cols = ROUTE.floors.stage1.columns!;
    expect(cols[0].waves?.length).toBe(6);
    expect(cols[2].waves?.length).toBe(6);
  });
});

describe('62 D P1-13 노점', () => {
  it('줄 → 카드 id (고정 칸 id · 진열 id · 궤짝 · C 품목 이름 규칙)', () => {
    const fixed = ['heal', 'potion'];
    expect(cardIdOf({ key: '1', group: 'fixed' }, fixed)).toBe('heal');
    expect(cardIdOf({ key: '2' }, fixed)).toBe('potion');
    expect(cardIdOf({ key: 'chest', group: 'chest' }, fixed)).toBe('chest');
    expect(cardIdOf({ key: 'g:inkBottle', group: 'display' }, fixed)).toBe('inkBottle');
    expect(cardIdOf({ key: 'd3', group: 'display' }, fixed, 'fireBottle')).toBe('fireBottle');
    expect(cardIdOf({ key: '1', group: 'fixed' }, ['traitReroll'])).toBe('inkBottle');
    expect(cardIdOf({ key: '1', group: 'fixed' }, ['temperOnce'])).toBe('bellows');
    expect(goodsArtOf('x', true)).toEqual({ sheet: 'shop_goods', row: 'relic_bundle' });
    expect(goodsArtOf('potion', false)?.sheet).toBe('potion');
    expect(goodsArtOf('heal', false)).toEqual({ sheet: 'shop_goods', row: 'heal' });
    expect(goodsArtOf('unknownThing', false)).toBeNull();
  });

  it('노점 자리: 상점 칸 아래 줄 · 한 줄 넘치면 두 줄 · 겹치지 않음', () => {
    const p = stallPositions({ x: 10, y: 10 }, 7);
    expect(p).toHaveLength(7);
    const keys = new Set(p.map((q) => `${q.x},${q.y}`));
    expect(keys.size).toBe(7);
    expect(new Set(p.map((q) => q.y)).size).toBe(2);
  });
});

describe('62 D P2-10 세트피스 · 그을음', () => {
  const open = (w: number, h: number): FloorLayout => {
    const tiles = Array.from({ length: h }, (_, y) =>
      Array.from({ length: w }, (_, x) =>
        x === 0 || y === 0 || x === w - 1 || y === h - 1 ? TileId.Wall : TileId.Floor,
      ),
    );
    return {
      seed: 1,
      gridW: 1,
      gridH: 1,
      rooms: [],
      hallways: [],
      connections: [],
      tiles,
      widthTiles: w,
      heightTiles: h,
      cellRoom: new Map(),
      arena: { spawn: { x: 4, y: 12 }, exit: { x: 34, y: 12 }, center: { x: 19, y: 12 } } as FloorLayout['arena'],
    };
  };
  it('전투장 바닥 위 · 시작/출구에서 떨어져 · 둘레 비움 · 결정적', () => {
    const L = open(38, 24);
    const a = planHeroSetpiece(L, 'outer', 's1', new Set());
    const b = planHeroSetpiece(L, 'outer', 's1', new Set());
    expect(a).not.toBeNull();
    expect(a).toEqual(b);
    for (let y = a!.ty - 1; y <= a!.ty + a!.h; y++)
      for (let x = a!.tx - 1; x <= a!.tx + a!.w; x++) expect(L.tiles[y][x]).toBe(TileId.Floor);
    expect(planHeroSetpiece(L, null, 's1', new Set())).toBeNull();
    const soot = planSoot(L, 'waste', 's1', new Set());
    expect(soot.length).toBeGreaterThanOrEqual(3);
    for (const d of soot) expect(L.tiles[d.y][d.x]).toBe(TileId.Floor);
  });
});
