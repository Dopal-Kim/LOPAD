import { describe, expect, it } from 'vitest';
import { WEAPONS } from '../../data';
import { BUILD, CURSES, curseDef, themeTagOf, validateBuild } from '../../data/build';
import { TRAITS, traitDef } from '../../data/growth';
import { TAG_IDS, type BuildData } from '../../data/buildTypes';
import { PassiveSet } from '../passives';
import { WeaponState } from '../weapon/weapons';
import { withAttackTag, currentAttackTag } from './attackTags';
import { computeBuildMods, param, ruleOf } from './buildMods';
import { BuildState, uiTags } from './BuildState';
import { CurseState, pickPactCurse, scaledBenefit } from './curses';
import { DashCharges } from './dashCharges';
import { DotBook, DrunkTimer, EvadeTracker, MarkBook } from './statusBooks';
import { isStrongAttack } from './strikeKinds';
import { emptyScores, nextThreshold, setStage, tagScores } from './tagScore';

const weaponAt = (id: string, path: string[], traits: string[] = []) => {
  const w = new WeaponState(id, WEAPONS[id]);
  w.restore({ path, traits });
  return w;
};

describe('57라운드 빌드 축 데이터', () => {
  it('10태그 · 세트 2/4/6 × 10 · 개성 56 (61 G) · 저주 7', () => {
    expect(BUILD.tags.map((t) => t.id)).toEqual([...TAG_IDS]);
    for (const t of TAG_IDS) expect(BUILD.sets[t].map((s) => s.threshold)).toEqual([2, 4, 6]);
    expect(TRAITS).toHaveLength(56);
    expect(CURSES.items.map((c) => c.id)).toEqual([
      'drunkOath',
      'credit',
      'brokenCup',
      'burningTongue',
      'bareOath',
      'cursedChest',
      'bruise',
    ]);
    expect(themeTagOf(1)).toBe('drunk');
    expect(themeTagOf(2)).toBeNull();
  });

  it('검증: 세트 임계가 어긋나면 거부', () => {
    const bad = JSON.parse(JSON.stringify(BUILD)) as BuildData;
    bad.sets.vital[1].threshold = 3 as never;
    expect(() => validateBuild(bad)).toThrow(/threshold/);
    const bad2 = JSON.parse(JSON.stringify(BUILD)) as BuildData;
    bad2.sets.vital[0].effect = { kind: 'stat', stats: { nope: 1 } as never };
    expect(() => validateBuild(bad2)).toThrow(/알 수 없음/);
  });
});

describe('태그 점수 (57 Q25)', () => {
  it('패시브 종류당 1 + Lv3 +1 · 갈래 노드 1 · 더하는 점수(개성 카드·저주)', () => {
    const S = BUILD.scoring;
    const s = tagScores(
      {
        passives: [
          { tags: ['vital'], level: 3, maxLevel: 3 },
          { tags: ['weight', 'endure'], level: 1, maxLevel: 3 },
        ],
        branchNodes: [{ tags: ['weight', 'vital'] }, { tags: ['weight', 'vital'] }],
        extra: [{ scar: 1 }, { weight: 3 }],
      },
      S,
    );
    expect(s.vital).toBe(2 + 2);
    expect(s.weight).toBe(1 + 2 + 3);
    expect(s.endure).toBe(1);
    expect(s.scar).toBe(1);
    expect(setStage(4, S.thresholds)).toBe(4);
    expect(setStage(1, S.thresholds)).toBe(0);
    expect(setStage(9, S.thresholds)).toBe(6);
    expect(nextThreshold(3, S.thresholds)).toBe(4);
    expect(nextThreshold(6, S.thresholds)).toBeNull();
    expect(emptyScores().drunk).toBe(0);
  });
});

describe('합산 (세트·패시브·저주)', () => {
  it('급소 2·4 = 치명 +8%p · 치명 피해 +0.5, 간파 2 규칙, 패시브 수치 합', () => {
    const p = new PassiveSet();
    p.add('whetstone');
    p.add('whetstone');
    p.add('whetstone'); // Lv3 → 급소 2점
    const st = new BuildState();
    const m = st.compute(p, weaponAt('katana', ['batto']));
    // 숫돌 Lv3 (1+1) + 투구가르기 (급소) = 3
    expect(m.scores.vital).toBe(3);
    expect(m.stages.vital).toBe(2);
    expect(m.stats.critChanceAdd).toBe(4 * 3 + 8);
    p.add('officerEpaulet');
    const m2 = st.compute(p, weaponAt('katana', ['batto']));
    expect(m2.stages.vital).toBe(4);
    expect(m2.stats.critDamageAdd).toBeCloseTo(0.5 + 0.15);
    expect(ruleOf(m2, 'markedCrit')).not.toBeNull();
    // 1단 노드 태그만으로는 세트가 없다
    expect(st.compute(new PassiveSet(), weaponAt('katana', ['iai'])).stages.chain).toBe(0);
  });

  it('저주 만취 서약: 공격 +30% · 받는 피해 +50% · 취기 +1점 · 취기 상시, 피의 계약은 이득 ×1.5', () => {
    const def = curseDef('drunkOath')!;
    const m = computeBuildMods({
      data: BUILD,
      passives: new PassiveSet(),
      nodes: [],
      traits: [],
      curse: new CurseState(def),
      permanentTags: {},
    });
    expect(m.stats.attackMult).toBeCloseTo(0.3);
    expect(m.stats.damageTakenMult).toBeCloseTo(0.5);
    expect(m.scores.drunk).toBe(1);
    expect(m.flags.drunkAlways).toBe(true);
    const pact = computeBuildMods({
      data: BUILD,
      passives: new PassiveSet(),
      nodes: [],
      traits: [],
      curse: new CurseState(def, true),
      permanentTags: {},
    });
    expect(pact.stats.attackMult).toBeCloseTo(0.45);
    expect(scaledBenefit(100, true, 1.5)).toBe(150);
  });

  it('외상 처치 전표 0 · 상점 +20%, 맨손 맹세 대쉬 불가', () => {
    const base = {
      data: BUILD,
      passives: new PassiveSet(),
      nodes: [],
      traits: [],
      permanentTags: {},
    };
    const credit = computeBuildMods({ ...base, curse: new CurseState(curseDef('credit')!) });
    expect(1 + credit.stats.killGoldMult).toBe(0);
    expect(credit.stats.shopPriceMult).toBeCloseTo(0.2);
    expect(computeBuildMods({ ...base, curse: new CurseState(curseDef('bareOath')!) }).flags.noDash).toBe(true);
  });

  it('패시브 규칙 레벨 인자 · 길 노드 규칙 · 개성 카드 규칙과 태그 점수 (61 G)', () => {
    const p = new PassiveSet();
    p.add('spilledDrink');
    p.add('spilledDrink');
    const st = new BuildState();
    const m = st.compute(p, weaponAt('greatsword', ['crush', 'quake']));
    expect(param(ruleOf(m, 'spillPool')!, 'chance')).toBeCloseTo(0.22);
    expect(ruleOf(m, 'quake')).not.toBeNull(); // 2단 노드 규칙
    // 옛 산붕 '4타 충격파'는 폐기 (P12)
    expect(ruleOf(m, 'mountainFall')).toBeNull();
    const t = st.compute(new PassiveSet(), weaponAt('katana', ['mangetsu'], ['k_iaiWave', 'k_moonRelay']));
    expect(ruleOf(t, 'moonClone')?.source).toBe('branch');
    expect(ruleOf(t, 'iaiWave')?.source).toBe('trait');
    expect(t.scores.weight).toBe(1); // 발도풍 = 중량 +1
    expect(t.scores.chain).toBe(1); // 달빛 잇기 = 연쇄 +1
    expect(traitDef('k_moonRelay')?.branch).toBe('mangetsu');
  });

  it('UI 태그 상태: 점수 > 0 만, 높은 순, 효과 3칸 active', () => {
    const p = new PassiveSet();
    p.add('lastCup');
    p.add('hipFlask');
    const m = new BuildState().compute(p, weaponAt('bow', ['rapid']));
    const ui = uiTags(m);
    expect(ui[0]).toMatchObject({ id: 'drunk', score: 2, stage: 2, next: 4 });
    expect(ui[0].effects.map((e) => e.active)).toEqual([true, false, false]);
    expect(ui.every((t) => t.score > 0)).toBe(true);
  });
});

describe('저주 지속 (57 Q37)', () => {
  it('노드 수: 받은 노드 다음부터 n 노드, 전투 노드만 세는 저주, 처치 수 저주', () => {
    const c = new CurseState(curseDef('drunkOath')!);
    expect(c.onNodeEntered(true)).toBe(false); // 첫 영향 노드 (무장)
    expect(c.nodesLeft).toBe(2);
    expect(c.onNodeEntered(true)).toBe(false);
    expect(c.nodesLeft).toBe(1);
    expect(c.onNodeEntered(false)).toBe(true); // 2노드가 지나면 끝
    const bare = new CurseState(curseDef('bareOath')!);
    expect(bare.onNodeEntered(false)).toBe(false);
    expect(bare.armed).toBe(false); // 비전투 노드는 세지 않음
    bare.onNodeEntered(true);
    expect(bare.onNodeEntered(true)).toBe(true);
    const chest = new CurseState(curseDef('cursedChest')!);
    for (let i = 0; i < 11; i++) expect(chest.onKill()).toBe(false);
    expect(chest.onKill()).toBe(true);
    const pact = new CurseState(curseDef('credit')!, true, BUILD.pact.extraNodes);
    expect(pact.nodesLeft).toBe(4);
    const restored = CurseState.restore(curseDef('credit')!, pact.toSave());
    expect(restored.toSave()).toEqual(pact.toSave());
    expect(pickPactCurse(['a', 'b'], 0.99)).toBe('b');
  });

  it('BuildState 세이브 왕복 · 층당 1회', () => {
    const s = new BuildState();
    s.curse = new CurseState(curseDef('brokenCup')!);
    s.bossFloorCleared = 5;
    s.permanentTags = { scar: 1 };
    const t = new BuildState();
    t.restore(s.toSave());
    expect(t.toSave()).toEqual(s.toSave());
    expect(t.takeFloorOnce('lastStand')).toBe(true);
    expect(t.takeFloorOnce('lastStand')).toBe(false);
    t.onFloorStart();
    expect(t.takeFloorOnce('lastStand')).toBe(true);
    t.restore({
      curse: { id: 'nope', nodesLeft: 1, killsLeft: null, armed: false, pact: false, maxHpTaken: 0 },
    });
    expect(t.curse).toBeNull();
  });
});

describe('상태 장부', () => {
  it('표식: n 타마다 1, 최대·옮겨감·수명', () => {
    const b = new MarkBook<string>();
    expect(b.hit('a', 0, 3, 3)).toBeNull();
    b.hit('a', 0, 3, 3);
    expect(b.hit('a', 0, 3, 3)).toBe(1);
    for (let i = 0; i < 12; i++) b.hit('a', 0, 3, 3);
    expect(b.marks('a')).toBe(3);
    b.set('b', b.take('a'), 0);
    expect(b.marks('b')).toBe(3);
    b.expire(10_000, 8000);
    expect(b.list()).toEqual([]);
  });

  it('지속 피해: 틱 · 남은 피해 · 끓음용 take · 옮겨붙기 snapshot', () => {
    const d = new DotBook<string>();
    d.apply('m', 'bleed', 0, 3000, 500, 2);
    d.apply('m', 'burn', 0, 1000, 500, 3);
    expect(d.has('m', 'burn', 100)).toBe(true);
    expect(d.remaining('m', 0)).toBe(6 * 2 + 2 * 3);
    expect(d.tick(500).map(([, k, v]) => [k, v])).toEqual([
      ['bleed', 2],
      ['burn', 3],
    ]);
    expect(d.snapshot('m', 600).map((x) => x.kind)).toEqual(['bleed', 'burn']);
    expect(d.take('m', 600)).toBeGreaterThan(0);
    expect(d.any('m', 600)).toBe(false);
  });

  it('취기 상태: 새로 고침(합산 아님)·상한, 취보 1회·반격 창', () => {
    const t = new DrunkTimer();
    t.drink(0, 5000);
    t.drink(1000, 5000);
    expect(t.remainMs(1000)).toBe(5000);
    expect(t.tryStagger(1200, 600)).toBe(true);
    expect(t.tryStagger(1300, 600)).toBe(false);
    expect(t.takeCounter(1500)).toBe(true);
    expect(t.takeCounter(1500)).toBe(false);
    t.drink(7000, 5000); // 새 취기 상태 → 휘청 다시
    expect(t.tryStagger(7100, 600)).toBe(true);
    t.extend(7100, 99999, 10000);
    expect(t.remainMs(7100)).toBe(10000);
  });

  it('완벽 회피: 시작 뒤 0.15초 안, 무장 자리 반경 안, 1회', () => {
    const e = new EvadeTracker();
    expect(e.check(0, 150, 0, 0, 10)).toBe(false);
    e.arm(1000, 100, 100);
    expect(e.check(1200, 150, 100, 100, 10)).toBe(false); // 창 밖
    e.arm(2000, 100, 100);
    expect(e.check(2100, 150, 130, 100, 10)).toBe(false); // 자리 밖
    expect(e.check(2100, 150, 105, 100, 10)).toBe(true);
    expect(e.check(2110, 150, 105, 100, 10)).toBe(false); // 1회
    e.arm(3000, 0, 0);
    expect(e.consume(3150, 150)).toBe(true);
  });

  it('대쉬 충전 (돌파 6): 2회 쓰고 순서대로 돌아온다', () => {
    const d = new DashCharges();
    expect(d.ready(0, 2)).toBe(true);
    d.use(0, 600);
    expect(d.ready(10, 2)).toBe(true);
    d.use(10, 600);
    expect(d.ready(20, 2)).toBe(false);
    expect(d.ready(600, 2)).toBe(true);
    expect(d.left(1300, 2)).toBe(2);
    const one = new DashCharges();
    one.use(0, 600);
    expect(one.ready(599, 1)).toBe(false);
    expect(one.ready(600, 1)).toBe(true);
  });
});

describe('공통 사건 분류', () => {
  it('강공: 일섬·차지 균열·새 동작·가득 당긴 화살 (연격 막타는 아님)', () => {
    expect(isStrongAttack({ move: 'backstab' })).toBe(true);
    expect(
      isStrongAttack({ crackLine: { stage: 1, maxTiles: 3, cursorX: 0, cursorY: 0, halfWidthPx: 4, damageMult: 1 } }),
    ).toBe(true);
    expect(isStrongAttack({ buildMove: 'spin' })).toBe(true);
    expect(isStrongAttack({ bowPower: 'perfect' })).toBe(true);
    expect(isStrongAttack({ bowPower: 'weak' })).toBe(false);
    expect(isStrongAttack({})).toBe(false);
  });

  it('공격 표시: 발행 동안만', () => {
    expect(currentAttackTag()).toBeNull();
    expect(withAttackTag('rapidVolley', () => currentAttackTag())).toBe('rapidVolley');
    expect(currentAttackTag()).toBeNull();
  });
});
