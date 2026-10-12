import { describe, expect, it } from 'vitest';
import type { UiMenu, UiShopOffer } from '../contract/ui';
import {
  edgeArrow,
  eventIconArt,
  eventIconText,
  eventPage,
  greetText,
  isEventPageMenu,
  listFocusMove,
  portraitFit,
  readIcons,
  shopCardPos,
  shopCardView,
  signLines,
  stripPrice,
  waveEdges,
} from './eventView';

/** 시스템 D 헤드리스 실측 (s62d run1 — 양조장 시음회) 그대로 */
const tasting: UiMenu = {
  id: 'event',
  title: '양조장 시음회',
  footer:
    '양조장 사람들이 새 술을 맛볼 사람을 찾는다. 값은 받지 않는다. 다른 걸 받는다.\n뒤에 쌓인 술통마다 행선지 도장이 찍혀 있다.',
  lines: [
    {
      key: 'one',
      label: '한 잔',
      enabled: true,
      detail: '내준다 최대 체력 −10  /  얻는다 유품 2택',
      costs: [{ kind: 'maxHp', label: '최대 체력 −10', amount: 10 }],
      rewards: [{ kind: 'passive', label: '유품 2택', amount: 2 }],
    },
    {
      key: 'two',
      label: '두 잔',
      enabled: true,
      costs: [{ kind: 'maxHp', label: '최대 체력 −20', amount: 20 }],
      rewards: [{ kind: 'passive', label: '희귀 이상 유품 2택', amount: 2 }],
    },
    { key: '0', label: '사양한다', enabled: true },
  ],
  cancelKey: '0',
  event: {
    id: 'tasting',
    name: '양조장 시음회',
    speaker: '양조장 일꾼',
    portrait: { key: 'sheet_npc_brewer_st', frame: '0' },
    greet: '새 술이야. 한 잔도 공짜, 두 잔도 공짜. 값은 딴 데서 받아.',
    intro: [
      '양조장 사람들이 새 술을 맛볼 사람을 찾는다. 값은 받지 않는다. 다른 걸 받는다.',
      '뒤에 쌓인 술통마다 행선지 도장이 찍혀 있다.',
    ],
    heads: { costHead: '내준다', gainHead: '얻는다', unknown: '?', pick: '하나를 고른다' },
  },
};

describe('eventView — 사연 메뉴 (계약 D P1-12)', () => {
  it('말하는 이·초상·첫 마디(말이면 「」)·설명, 아이콘 줄이 있으면 detail 을 숨긴다', () => {
    const p = eventPage(tasting);
    expect(isEventPageMenu(tasting)).toBe(true);
    expect(p.title).toBe('양조장 시음회');
    expect(p.speaker).toBe('양조장 일꾼');
    expect(p.portrait?.key).toBe('sheet_npc_brewer_st');
    expect(greetText(p)).toBe('「새 술이야. 한 잔도 공짜, 두 잔도 공짜. 값은 딴 데서 받아.」');
    expect(p.intro).toHaveLength(2);
    expect(p.extra).toEqual([]);
    expect(p.hasIcons).toBe(true);
    expect(p.rows.map((r) => r.hotkey)).toEqual(['1', '2', '0']);
    expect(p.rows[0].note).toBe('');
    expect(p.rows[0].costs[0].kind).toBe('maxHp');
    expect(p.hint).toContain('1·2·0');
    expect(p.hint).toContain('Esc 사양한다');
  });

  it('못 고르는 줄은 까닭(detail)을 흐리게, 숨은 보상은 ? 그림만', () => {
    const m: UiMenu = {
      ...tasting,
      lines: [
        {
          key: 'give',
          label: '독주를 건넨다',
          enabled: false,
          detail: '건넬 독주가 없다',
          costs: [{ kind: 'potion', label: '독주 −1', amount: 1 }],
          rewards: [{ kind: 'gold', label: '?', hidden: true }],
        },
        { key: '0', label: '지나간다', enabled: true },
      ],
      event: { ...tasting.event!, speaker: undefined, greet: '바람에 쪽이 넘어간다.' },
    };
    const p = eventPage(m);
    expect(p.rows[0].note).toBe('건넬 독주가 없다');
    expect(p.greetKind).toBe('narration');
    expect(greetText(p)).toBe('바람에 쪽이 넘어간다.');
    expect(p.speaker).toBe('');
    const hidden = p.rows[0].rewards[0];
    expect(eventIconArt(hidden)).toEqual({ sheet: 'event', frame: 'unknown' });
    expect(eventIconText(hidden)).toBe('');
  });

  it('footer 에만 있는 줄(다음 각성 미리보기)은 설명 아래 덧붙인다', () => {
    const p = eventPage({ ...tasting, footer: `${tasting.footer}\n칼날 · 칼등` });
    expect(p.extra).toEqual(['칼날 · 칼등']);
  });

  it('상인과 말하기 (event 없음): 제목 = 상인, 첫 마디 = footer, 값은 대가 칸 전표 아이콘으로 · 라벨 끝 값은 뗀다', () => {
    const m: UiMenu = {
      id: 'shopTalk',
      title: '종군 상인',
      footer: '어디서 왔든 상관없네. 전표만 있으면 손님이지.',
      speaker: '종군 상인',
      cancelKey: '0',
      lines: [
        {
          key: 'reroll',
          label: '다시 진열한다 · 전표 15',
          enabled: true,
          group: 'reroll',
          price: { kind: 'gold', amount: 15, label: '15전표', affordable: true },
        },
        { key: 'credit', label: '외상을 단다', enabled: true, detail: '처치 전표 0' },
        { key: '0', label: '그만 본다', enabled: true },
      ],
    };
    const p = eventPage(m);
    expect(isEventPageMenu(m)).toBe(true);
    expect(p.title).toBe('종군 상인');
    expect(p.speaker).toBe('');
    expect(p.greet).toBe('어디서 왔든 상관없네. 전표만 있으면 손님이지.');
    expect(p.rows[0].label).toBe('다시 진열한다');
    expect(p.rows[0].costs).toEqual([{ kind: 'gold', amount: 15, label: '15전표' }]);
    expect(p.rows[1].note).toBe('처치 전표 0');
    expect(p.rows.map((r) => r.hotkey)).toEqual(['1', '2', '0']);
  });

  it('event 머리가 없는 옛 사연 메뉴는 이 틀을 쓰지 않는다', () => {
    expect(isEventPageMenu({ id: 'event' })).toBe(false);
    expect(isEventPageMenu({ id: 'passive' })).toBe(false);
  });

  it('stripPrice: 값 숫자가 든 끝 마디만 뗀다', () => {
    expect(stripPrice('다시 진열한다 · 전표 15', 15)).toBe('다시 진열한다');
    expect(stripPrice('다시 진열한다 · 전표 150', 15)).toBe('다시 진열한다 · 전표 150');
    expect(stripPrice('외상을 단다', 15)).toBe('외상을 단다');
  });

  it('아이콘: 키트(전표·독주·체력) · UI F 시트 · 모르는 종류와 감각은 ?', () => {
    expect(eventIconArt({ kind: 'gold' })).toEqual({ sheet: 'kit', frame: 'icon_gold' });
    expect(eventIconArt({ kind: 'curse' })).toEqual({ sheet: 'event', frame: 'curse' });
    expect(eventIconArt({ kind: 'sense' })).toEqual({ sheet: 'event', frame: 'unknown' });
    expect(readIcons([{ kind: 'gold', label: 'a' }, null, 3, { label: 'x' }])).toHaveLength(1);
    expect(readIcons(undefined)).toEqual([]);
  });

  it('세로 표 이동: ↑↓ 돌아가고 ←→ 는 그대로', () => {
    expect(listFocusMove(0, 3, 'ArrowDown')).toBe(1);
    expect(listFocusMove(2, 3, 'ArrowDown')).toBe(0);
    expect(listFocusMove(0, 3, 'ArrowUp')).toBe(2);
    expect(listFocusMove(1, 3, 'ArrowLeft')).toBe(1);
    expect(listFocusMove(1, 3, 's')).toBe(2);
  });
});

describe('eventView — 장터 노점 카드 (계약 D P1-13)', () => {
  const base: UiShopOffer = {
    stallId: 'stall:1',
    line: {
      key: '1',
      label: '뜨끈한 국밥 한 그릇',
      enabled: true,
      price: { kind: 'gold', amount: 30, label: '30전표', affordable: true },
      group: 'fixed',
      detail: '그 자리에서 먹으면 체력이 돌아온다',
    },
    icon: { key: 'sheet_potion_st', frame: '0' },
    buyKey: 'E',
    usable: true,
    reason: null,
    reasonText: '',
    screen: { x: 560, y: 279 },
  };

  it('물건: 이름·한 줄·값·[E] 산다·드랍 그림', () => {
    const v = shopCardView(base);
    expect(v.name).toBe('뜨끈한 국밥 한 그릇');
    expect(v.line).toBe('그 자리에서 먹으면 체력이 돌아온다');
    expect(v.price).toBe(30);
    expect(v.action).toBe('[E] 산다');
    expect(v.art).toEqual({ kind: 'item', key: 'sheet_potion_st', frame: '0' });
  });

  it('못 사면 까닭, 팔렸으면 팔렸다', () => {
    const poor = shopCardView({
      ...base,
      usable: false,
      reason: 'gold',
      reasonText: '전표가 모자란다',
      line: { ...base.line, price: { ...base.line.price!, affordable: false } },
    });
    expect(poor.action).toBe('전표가 모자란다');
    expect(poor.affordable).toBe(false);
    expect(poor.usable).toBe(false);
    const sold = shopCardView({ ...base, line: { ...base.line, soldOut: true } });
    expect(sold.action).toBe('팔렸다');
    expect(sold.sold).toBe(true);
  });

  it('유품 줄: 유품 카드 필드(이름·한 문장·단계·태그·희귀도·그림)', () => {
    const v = shopCardView(
      {
        ...base,
        line: {
          ...base.line,
          label: '맹공',
          relic: {
            id: 'ferocity',
            name: '맹공',
            line: '세 번째 타격이 더 깊이 든다',
            detail: '피해 +20%',
            tag: 'vital',
            rarity: 'rare',
            level: 1,
            maxLevel: 3,
            levelText: '1단계',
            iconKey: 'ui_relics/ferocity',
          },
        },
      },
      (t) => (t === 'vital' ? '급소' : t),
    );
    expect(v.name).toBe('맹공');
    expect(v.line).toBe('세 번째 타격이 더 깊이 든다');
    expect(v.meta).toBe('1단계 · 급소');
    expect(v.rarityRank).toBe(2);
    expect(v.art).toEqual({ kind: 'relic', key: 'ui_relics/ferocity' });
  });

  it('카드 자리: 위에 붙이고, 자리가 없으면 아래 · 화면 안으로', () => {
    expect(shopCardPos({ x: 480, y: 300 }, 168, 80, 960, 540, 6, 11)).toEqual({
      x: 396,
      y: 209,
      tailX: 480,
      below: false,
    });
    const top = shopCardPos({ x: 10, y: 40 }, 168, 80, 960, 540, 6, 11);
    expect(top.below).toBe(true);
    expect(top.x).toBe(6);
    expect(top.tailX).toBe(14);
  });
});

describe('eventView — 팻말 · 무리 방향', () => {
  it('팻말 두 줄', () => {
    expect(signLines({ title: '허수아비', value: '누적 120 · 8타' })).toEqual({
      title: '허수아비',
      value: '누적 120 · 8타',
      sig: '허수아비\u0001누적 120 · 8타',
    });
  });

  it('들어오는 쪽 → 가장자리', () => {
    expect(waveEdges('north')).toEqual(['north']);
    expect(waveEdges('flank')).toEqual(['west', 'east']);
    expect(waveEdges('around')).toHaveLength(4);
    expect(waveEdges(undefined)).toEqual([]);
    expect(waveEdges('sideways')).toEqual([]);
  });

  it('위쪽 화살촉은 알림 줄 위, 오른쪽은 가운데 높이 · 바깥을 가리킨다', () => {
    expect(edgeArrow('north', 960, 540, 14, 24, 10)).toEqual({ x: 480, y: 24, angle: -Math.PI / 2 });
    expect(edgeArrow('east', 960, 540, 14, 24, 10)).toEqual({ x: 946, y: 270, angle: 0 });
  });
});

describe('eventView — 초상 놓기 (잘린 아틀라스 프레임)', () => {
  it('칸보다 크면 머리를 위에 맞추고 발을 자른다 · 가로 가운데', () => {
    // 양조장 일꾼: 실제 160×192 안 (54,40) 에 51×114
    const r = portraitFit(
      { realW: 160, realH: 192, trimX: 54, trimY: 40, w: 51, h: 114 },
      { x: 100, y: 50, w: 70, h: 81 },
      1,
      5,
    );
    expect(r.y).toBe(50 + 5 - 40);
    expect(Math.abs(r.x + 54 + 51 / 2 - 135)).toBeLessThanOrEqual(1);
    expect(r.crop.y).toBe(35);
    expect(r.crop.h).toBe(81);
    expect(r.crop.x).toBeGreaterThanOrEqual(0);
    expect(r.crop.w).toBe(70);
  });

  it('칸에 다 들면 아래 맞춤 · 자를 것 없음', () => {
    const r = portraitFit(
      { realW: 96, realH: 144, trimX: 20, trimY: 20, w: 45, h: 111 },
      { x: 0, y: 0, w: 70, h: 81 },
      0.5,
      5,
    );
    expect(Math.abs(r.y + (20 + 111) * 0.5 - 76)).toBeLessThanOrEqual(1);
    expect(r.crop.h).toBeGreaterThan(0);
  });
});
