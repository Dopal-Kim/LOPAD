import { describe, expect, it } from 'vitest';
import { RELICS, relicDetailTemplate, relicLine } from '../data/relics';
import { PassiveSet } from './passives';
import { Rng } from './rng';
import {
  ownedRelics,
  relicDetailText,
  relicExclude,
  relicFallbackKey,
  relicValues,
  rollRelics,
  uiRelic,
} from './relics';
import { ECONOMY } from '../data';
import pack from '../../parts/story/text-pack-63-loop2.json';

const WEAPONS = ['katana', 'greatsword', 'dagger', 'bow'];

describe('62 루프 2 C 유품 (P1-5)', () => {
  it('1층 패시브 15종이 모두 유품이고 문장은 스토리 63 팩과 같다', () => {
    const set = new PassiveSet();
    const floor1 = set.defs.filter((p) => (p.floor ?? 1) <= 1).map((p) => p.id);
    expect(RELICS.items.map((r) => r.id).sort()).toEqual(floor1.sort());
    const P = (
      pack as unknown as { relics: { items: Record<string, { name: string; lines: Record<string, string> }> } }
    ).relics.items;
    for (const r of RELICS.items) {
      expect(r.name).toBe(P[r.id].name);
      expect(r.lines).toEqual(P[r.id].lines);
    }
  });

  it('카드 문장에는 숫자·×·% 가 없고, 수치 틀은 모든 자리표시가 채워진다', () => {
    const set = new PassiveSet();
    for (const r of RELICS.items)
      for (const w of WEAPONS) {
        const line = relicLine(r, w);
        if (!line) continue;
        expect(line).not.toMatch(/[0-9×%]/);
        const text = relicDetailText(relicDetailTemplate(r, w), relicValues(set.def(r.id)!, 1), w);
        expect(text, `${r.id}/${w}: ${text}`).not.toMatch(/[{}]/);
      }
  });

  it('수치 틀 채우기: % 는 ×100 (치명은 그대로) · 초는 ms ÷1000 · 음수는 절댓값', () => {
    expect(relicDetailText('공격력 +{attackMult}%', { attackMult: 0.15 }, 'katana')).toBe('공격력 +15%');
    expect(relicDetailText('치명 확률 +{critChanceAdd}%', { critChanceAdd: 4 }, 'bow')).toBe('치명 확률 +4%');
    expect(relicDetailText('틈 +{perfectWindowAddMs}초', { perfectWindowAddMs: 50 }, 'katana')).toBe('틈 +0.05초');
    expect(relicDetailText('대기 −{d}%', { d: -0.3 }, 'katana')).toBe('대기 −30%');
    expect(relicDetailText('({strongAttack})', {}, 'katana')).toBe('(발도·일섬)');
  });

  it('단계: 같은 유품을 또 고르면 단계 값이 오른다 (2단계 흡혈 = 체력 +4)', () => {
    const set = new PassiveSet();
    const card = uiRelic(set.def('lifesteal')!, 'katana', 2, set.maxLevel)!;
    expect(card.level).toBe(2);
    expect(card.levelText).toBe('2단계');
    expect(card.detail).toBe('처치마다 체력 +4');
  });

  it('들고 있는 무기 문장만 — 뽑기는 유품이 아닌 패시브·최대 단계를 뺀다', () => {
    const set = new PassiveSet();
    const ex = relicExclude('katana', set);
    expect(ex).toContain('ironskin'); // 2층 패시브 (유품 아님)
    expect(ex).not.toContain('lifesteal');
    set.setLevel('lifesteal', set.maxLevel);
    expect(relicExclude('katana', set)).toContain('lifesteal');
    const picks = rollRelics(new PassiveSet(), 'bow', new Rng(3), ECONOMY.rarity, 3, { floor: 1 });
    expect(picks).toHaveLength(3);
    for (const p of picks) expect(RELICS.items.some((r) => r.id === p.id)).toBe(true);
  });

  it('카드 그림: 유품 그림 → 없으면 같은 태그 개성 그림 → 없으면 생략', () => {
    const set = new PassiveSet();
    const d = set.def('domino')!;
    expect(uiRelic(d, 'katana', 1, 3, { loaded: (k) => k === 'ui_relics/domino' })!.iconKey).toBe('ui_relics/domino');
    const fb = relicFallbackKey({ tag: 'chain' }, 'katana')!;
    expect(fb).toMatch(/^ui_traits\/katana_/);
    expect(uiRelic(d, 'katana', 1, 3, { loaded: (k) => k === fb })!.iconKey).toBe(fb);
    expect(uiRelic(d, 'katana', 1, 3, { loaded: () => false })!.iconKey).toBeUndefined();
  });

  it('지닌 유품 목록 (얻은 순서 · 지금 단계)', () => {
    const set = new PassiveSet();
    set.add('sprint');
    set.add('lifesteal');
    set.add('lifesteal');
    const list = ownedRelics(set, 'dagger');
    expect(list.map((r) => [r.id, r.level])).toEqual([
      ['sprint', 1],
      ['lifesteal', 2],
    ]);
  });
});
