import { describe, expect, it } from 'vitest';
import { PLAYER_DATA, WEAPONS } from '../data';
import type { BowDrawDef, BrandGaugeDef, HeatResourceDef, StaminaResourceDef } from '../data/types';
import { WeaponResource } from './weaponResource';
import { BrandBook, BreathGauge, GrudgeGauge, KenkiGauge, isBackHit, makeGauge } from './weaponGauge';
import { drawFrame, drawState, releaseShot, strainShakeRad } from './bowDraw';
import { issenHit, lineTier, predictTravel, shadowAt } from './issenPath';
import { MOVES, availableMoves, pickMove } from './moves';
import { isPerfectGuard, resolveDefense } from './defense';
import {
  animRowNames,
  directionRow,
  facing8Of,
  frameAt,
  fxHoldFrame,
  hasDiagonalRows,
  parseAnimKey,
  rowDirFor,
  strokeDoneFrame,
  type SheetJson,
} from './spriteDefs';

const STAMINA: StaminaResourceDef = {
  kind: 'stamina',
  label: '기력',
  max: 100,
  regenPerSec: 50,
  regenDelayMs: 500,
  lowRatio: 0.3,
  recoverRatio: 0.35,
  exhaustedMoveMult: 0.5,
  cost: { hits: [20, 20, 30], dash: 10, dashAttack: 25, slam: 40 },
  groggyMs: 1500,
};

describe('56라운드 Q7·Q19 그로기 (기력 groggyMs)', () => {
  it('기력 0 → 1.5초 그로기, 그동안 회복·공격 없음, 지나야만 풀리고 recoverRatio 만큼', () => {
    const r = new WeaponResource(STAMINA);
    r.spend(100, 0);
    expect(r.isGroggy).toBe(true);
    expect(r.canAttack()).toBe(false);
    expect(r.moveMult).toBe(0.5);
    r.tick(1000, 1000);
    expect(r.value).toBe(0);
    expect(r.isGroggy).toBe(true);
    expect(r.groggyLeftMs(1000)).toBe(500);
    // 그로기 중 소모는 늘리지 않는다
    r.spend(10, 1100);
    r.tick(1500, 500);
    expect(r.isGroggy).toBe(false);
    expect(r.canAttack()).toBe(true);
    expect(r.value).toBe(35);
    // 풀린 뒤엔 바로 회복
    r.tick(1600, 100);
    expect(r.value).toBeCloseTo(40);
  });

  it('groggyMs 가 없는 기력은 49라운드 규칙 그대로 (공격은 가능)', () => {
    const r = new WeaponResource({ ...STAMINA, groggyMs: undefined });
    r.spend(100, 0);
    expect(r.isExhausted).toBe(true);
    expect(r.isGroggy).toBe(false);
    expect(r.canAttack()).toBe(true);
  });

  it('칼·대검 데이터에 그로기 1.5초, 단검·활에는 기력이 없다', () => {
    for (const id of ['katana', 'greatsword']) {
      const res = WEAPONS[id].resource;
      expect(res?.kind).toBe('stamina');
      expect(res?.kind === 'stamina' && res.groggyMs).toBe(1500);
    }
    expect(WEAPONS.dagger.resource?.kind).toBe('heat');
    expect(WEAPONS.bow.resource?.kind).toBe('ammo');
  });
});

describe('56라운드 Q18 과열 식는 동안 (낙인 연동)', () => {
  const HEAT: HeatResourceDef = {
    kind: 'heat',
    label: '열기',
    max: 100,
    gainPerHit: [50],
    decayPerSec: 0,
    decayDelayMs: 1000,
    stages: [30, 60, 90],
    speedMults: [1, 1.1, 1.2, 1.3],
    overheatHoldMs: 0,
    cooldownMs: 1000,
  };
  it('100% 즉시 과열 → 식는 동안 공격 가능·느려짐', () => {
    const r = new WeaponResource(HEAT, { speedMult: 0.7, moveMult: 0.85 });
    r.heatUp(0, 0);
    r.heatUp(0, 10);
    r.tick(20, 10);
    expect(r.overheated).toBe(true);
    expect(r.canAttack()).toBe(true);
    expect(r.speedMult).toBe(0.7);
    expect(r.moveMult).toBe(0.85);
    r.tick(1100, 1080);
    expect(r.overheated).toBe(false);
    expect(r.moveMult).toBe(1);
  });
  it('냉각 규칙이 없으면 49라운드처럼 공격 불가', () => {
    const r = new WeaponResource(HEAT);
    r.heatUp(0, 0);
    r.heatUp(0, 10);
    r.tick(20, 10);
    expect(r.canAttack()).toBe(false);
  });
});

describe('56라운드 고유 자원', () => {
  it('검기 3단: 타격으로 조금씩, 패링 1단 즉시, 일섬이 전부 소모 (3단 = 분신)', () => {
    const k = new KenkiGauge({
      kind: 'kenki',
      label: '검기',
      stages: 3,
      perStage: 100,
      gainPerHit: 40,
      parryGainStages: 1,
      issenDamagePerStage: 0.25,
      cloneAtStages: 3,
    });
    expect(k.gainHit()).toBeNull();
    expect(k.gainHit()).toBeNull();
    expect(k.gainHit()).toBe(1); // 120
    expect(k.gainParry()).toBe(2);
    expect(k.value).toBe(200);
    expect(k.gainParry()).toBe(3);
    expect(k.gainParry()).toBeNull();
    const c = k.consume();
    expect(c).toEqual({ stages: 3, damageMult: 1.75, clone: true });
    expect(k.stage).toBe(0);
    k.gainParry();
    expect(k.consume().clone).toBe(false);
  });

  it('울분: 가드로 막은 피해 누적(퍼펙트 2배·그로기 3배), 차지가 전부 소모', () => {
    const g = new GrudgeGauge({
      kind: 'grudge',
      label: '울분',
      max: 100,
      blockGainMult: 2,
      perfectMult: 2,
      groggyMult: 3,
      slamDamageBonus: 1,
      slamRangeBonus: 0.3,
    });
    g.addBlocked(5, 'normal');
    expect(g.value).toBe(10);
    g.addBlocked(5, 'perfect');
    expect(g.value).toBe(30);
    expect(g.addBlocked(20, 'groggy')).toBe(true);
    expect(g.full).toBe(true);
    const c = g.consume();
    expect(c.damageMult).toBe(2);
    expect(c.rangeMult).toBeCloseTo(1.3);
    expect(g.value).toBe(0);
  });

  it('숨: 완벽 놓기마다 +1, 가득이면 집중 시작(숨 소모)', () => {
    const b = new BreathGauge({
      kind: 'breath',
      label: '숨',
      max: 3,
      perfectGain: 1,
      focusMs: 1000,
      focusTimeScale: 0.4,
      focusPerfectWindowMult: 4,
    });
    expect(b.startFocus(0)).toBe(false);
    b.addPerfect();
    b.addPerfect();
    expect(b.addPerfect()).toBe(true);
    expect(b.startFocus(100)).toBe(true);
    expect(b.value).toBe(0);
    expect(b.focusing(1099)).toBe(true);
    expect(b.focusing(1100)).toBe(false);
  });

  it('낙인: 같은 적마다 쌓임(등 뒤 2, 최대 5), 과열 단계면 더 빨리, 폭발로 떼어 냄', () => {
    const def: BrandGaugeDef = {
      kind: 'brand',
      label: '낙인',
      max: 5,
      perHit: 1,
      backGain: 2,
      backAngleDeg: 70,
      heatGainPerStage: 0.5,
      burstDamagePerMark: 0.6,
      overheatBurstRadiusTiles: 4,
      coolingSpeedMult: 0.7,
      coolingMoveMult: 0.85,
      lifeMs: 1000,
    };
    const book = new BrandBook<string>(def);
    expect(book.add('a', 0, { back: false, heatStage: 0 })).toEqual({ before: 0, after: 1 });
    expect(book.add('a', 0, { back: true, heatStage: 0 }).after).toBe(3);
    // 과열 1단: 1.5 → 1 + 소수 0.5 이월, 다음에 2
    expect(book.add('b', 0, { back: false, heatStage: 1 }).after).toBe(1);
    expect(book.add('b', 0, { back: false, heatStage: 1 }).after).toBe(3);
    book.add('a', 0, { back: true, heatStage: 3 });
    expect(book.marks('a')).toBe(5);
    expect(book.take('a')).toBe(5);
    expect(book.marks('a')).toBe(0);
    book.add('c', 0, { back: false, heatStage: 0 });
    expect(book.takeWhere((k) => k === 'c')).toEqual([['c', 1]]);
    book.expire(2000);
    expect(book.list()).toEqual([]);
  });

  it('등 뒤 판정 = 적이 보는 방향과 공격 방향이 같은 쪽', () => {
    expect(isBackHit({ x: 1, y: 0 }, { x: 1, y: 0.2 }, 70)).toBe(true);
    expect(isBackHit({ x: 1, y: 0 }, { x: -1, y: 0 }, 70)).toBe(false);
    expect(isBackHit({ x: 0, y: 0 }, { x: 1, y: 0 }, 70)).toBe(false);
  });

  it('무기 데이터 → 자원 (칼 검기·대검 울분·활 숨, 단검 낙인은 장부)', () => {
    expect(makeGauge(WEAPONS.katana.gauge)).toBeInstanceOf(KenkiGauge);
    expect(makeGauge(WEAPONS.greatsword.gauge)).toBeInstanceOf(GrudgeGauge);
    expect(makeGauge(WEAPONS.bow.gauge)).toBeInstanceOf(BreathGauge);
    expect(WEAPONS.dagger.gauge?.kind).toBe('brand');
    expect(makeGauge(WEAPONS.dagger.gauge)).toBeNull();
  });
});

describe('56라운드 Q9 활 당김·놓기', () => {
  const D: BowDrawDef = WEAPONS.bow.draw!;
  it('가득 전 = 약한 1발 · 가득 직후 0.15초 = 완벽 · 그 뒤 = 가득 · 오래 쥐면 흔들림·위력 감소', () => {
    expect(releaseShot(D, 300).power).toBe('weak');
    expect(releaseShot(D, 300).replacesAimed).toBe(true);
    expect(releaseShot(D, D.fullMs + 10)).toMatchObject({ power: 'perfect', refund: true, pierce: true });
    expect(releaseShot(D, D.fullMs + D.perfectWindowMs + 1).power).toBe('full');
    const late = releaseShot(D, D.fullMs + D.strainAfterMs + D.strainRampMs);
    expect(late.power).toBe('strained');
    expect(late.damageMult).toBeCloseTo(D.strainMinMult);
    // 숨 집중: 창이 넓고 흔들림이 없다
    expect(releaseShot(D, D.fullMs + 400, { focus: true, windowMult: 4 }).power).toBe('perfect');
    expect(drawState(D, D.fullMs + D.strainAfterMs + 500, true).phase).toBe('hold');
  });
  it('자동 발사 없음: 계속 쥐어도 상태만 바뀐다', () => {
    expect(drawState(D, 10_000).phase).toBe('strain');
  });
  it('몸 열: 진행 f0~5 → 유지 f6~9 반복 → 흔들림 f10~13 반복', () => {
    const sheet = {
      progressFrames: [0, 1, 2, 3, 4, 5],
      holdLoop: [6, 9] as [number, number],
      strainLoop: [10, 13] as [number, number],
      frameDurationsMs: [90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 70, 70, 70, 70],
    };
    expect(drawFrame(drawState(D, 0), sheet)).toBe(0);
    expect(drawFrame(drawState(D, D.fullMs * 0.5), sheet)).toBe(2);
    expect(drawFrame(drawState(D, D.fullMs), sheet)).toBe(6);
    expect(drawFrame(drawState(D, D.fullMs + 100), sheet)).toBe(7);
    const s = drawState(D, D.fullMs + D.strainAfterMs + 10);
    expect(drawFrame(s, sheet)).toBeGreaterThanOrEqual(10);
    expect(strainShakeRad(D, 0, 123)).toBe(0);
    expect(Math.abs(strainShakeRad(D, 1, 123))).toBeLessThanOrEqual((D.strainShakeDeg * Math.PI) / 180);
  });
});

describe('56라운드 Q2 일섬 기하', () => {
  it('벽 예측 · t1~t4 · 판정 직사각형 · 분신 위치', () => {
    const open = () => true;
    expect(predictTravel(0, 0, { x: 1, y: 0 }, 64, open)).toBe(64);
    expect(predictTravel(0, 0, { x: 1, y: 0 }, 64, (x) => x < 40)).toBe(38);
    expect(lineTier(64, 16, 4)).toBe(3);
    expect(lineTier(40, 16, 4)).toBe(1);
    expect(lineTier(5, 16, 4)).toBe(0);
    const geom = { backPx: 6, extraPx: 16, widthPx: 18 };
    expect(issenHit({ x: 0, y: 0 }, { x: 1, y: 0 }, 64, geom, { x: 70, y: 0, r: 4 })).toBe(true);
    expect(issenHit({ x: 0, y: 0 }, { x: 1, y: 0 }, 64, geom, { x: 100, y: 0, r: 4 })).toBe(false);
    expect(issenHit({ x: 0, y: 0 }, { x: 1, y: 0 }, 64, geom, { x: 30, y: 20, r: 4 })).toBe(false);
    expect(shadowAt({ x: 0, y: 0 }, { x: 64, y: 0 }, 75, 150)).toEqual({ x: 32, y: 0 });
  });
  it('칼 3타 = 일섬, 반경 38, 템포 약 1.5초 (아트 시간)', () => {
    const c = WEAPONS.katana.combo!;
    expect(c.radiusPx).toBe(38);
    expect(c.hits.map((h) => [h.durationMs, h.hitAtMs])).toEqual([
      [470, 150],
      [440, 120],
      [740, 250],
    ]);
    expect(c.hits[2].move).toBe('issen');
    const total = c.hits[0].cancelFromMs + c.hits[1].cancelFromMs + c.hits[2].durationMs;
    expect(total).toBeGreaterThan(1400);
    expect(total).toBeLessThan(1700);
  });
});

describe('56라운드 Q40~Q43 공격 수단 표', () => {
  it('구현된 수단만 고른다 · 갈래 수단은 그 갈래가 경로에 있을 때만 열린다', () => {
    expect(pickMove('katana', 'comboFinisher', [])?.id).toBe('issen');
    expect(pickMove('katana', 'afterParry', [])).toBeNull();
    expect(availableMoves('katana', []).some((m) => m.id === 'spin')).toBe(false);
    expect(availableMoves('katana', ['iai']).some((m) => m.id === 'spin')).toBe(true);
    expect(pickMove('greatsword', 'chargeRelease', ['crush'], () => false)).toBeNull();
    expect(new Set(MOVES.map((m) => m.id)).size).toBe(MOVES.length);
  });
});

describe('56라운드 Q7 퍼펙트 가드', () => {
  it('가드 직후 0.15초 = 피해 0, 그 뒤 = 감소, 패링 = 튕겨냄', () => {
    expect(PLAYER_DATA.perfectGuard?.windowMs).toBe(150);
    expect(isPerfectGuard(1000, 1150, 150)).toBe(true);
    expect(isPerfectGuard(1000, 1151, 150)).toBe(false);
    const base = { guardStartedAt: 1000, perfectWindowMs: 150, guardReduction: 0.7, damage: 20, groggy: false };
    expect(resolveDefense({ ...base, action: 'guard', now: 1100 })).toEqual({ kind: 'perfect', blocked: 20 });
    expect(resolveDefense({ ...base, action: 'guard', now: 1300 })).toEqual({
      kind: 'guarded',
      amount: 6,
      blocked: 14,
      groggy: false,
    });
    expect(resolveDefense({ ...base, action: 'parry', now: 1300 }).kind).toBe('parried');
    expect(resolveDefense({ ...base, action: 'other', now: 1300 })).toEqual({ kind: 'hit', amount: 20 });
  });
});

describe('56라운드 Q6 8방향 행 · Q37 정지 프레임', () => {
  const four = { directions: ['down', 'up', 'left', 'right'] } as SheetJson;
  const eight = {
    directions: ['down', 'up', 'left', 'right', 'down-right', 'down-left', 'up-right', 'up-left'],
    frames: 6,
  } as SheetJson;
  it('조준각 8분할 (−22.5°~22.5° = right, 시계 방향)', () => {
    expect(facing8Of(1, 0, 'down')).toBe('right');
    expect(facing8Of(1, 1, 'down')).toBe('down-right');
    expect(facing8Of(0, 1, 'down')).toBe('down');
    expect(facing8Of(-1, 1, 'down')).toBe('down-left');
    expect(facing8Of(-1, -1, 'down')).toBe('up-left');
    expect(facing8Of(1, -1, 'down')).toBe('up-right');
    expect(facing8Of(1, 0.3, 'down')).toBe('right');
  });
  it('8행 시트만 대각 행, 4행 시트는 기존 4방향 그대로', () => {
    expect(hasDiagonalRows(eight)).toBe(true);
    expect(hasDiagonalRows(four)).toBe(false);
    expect(rowDirFor(eight, 1, 1, 'down')).toBe('down-right');
    expect(rowDirFor(four, 1, 1.2, 'down')).toBe('down');
    expect(directionRow(eight, 'up-left')).toBe(7);
    expect(directionRow(four, 'up-left')).toBe(2);
    expect(frameAt(eight, 'down-left', 2)).toBe(5 * 6 + 2);
    expect(directionRow({ directions: ['s', 'm', 'l'] }, 'l')).toBe(2);
    expect(animRowNames({ directions: ['any'] })).toEqual(['down', 'up', 'left', 'right']);
    expect(animRowNames(eight)).toHaveLength(8);
    expect(parseAnimKey('player_greatsword_cleave_down-right#k6-440-920', 'player')).toEqual({
      action: 'greatsword_cleave',
      dir: 'down-right',
    });
  });
  it('붓획 시트는 백열 다음 칸에서 멈춘다 (적중 스파크 holdFrame 은 그대로)', () => {
    const stroke = { frames: 6, impactFrame: 1, glowFrames: [1, 2], brushStroke: true } as SheetJson;
    expect(fxHoldFrame(stroke)).toBe(3);
    expect(strokeDoneFrame({ frames: 3, impactFrame: 1, glowFrames: [2] } as SheetJson)).toBe(2);
    expect(fxHoldFrame({ frames: 6, holdFrame: 1, brushStroke: true } as SheetJson)).toBe(1);
    expect(fxHoldFrame({ frames: 6, impactFrame: 2 } as SheetJson)).toBe(2);
    // Q51: frameRoles 로 계산 — 'draw(끝까지)' 다음 칸, 없으면 마지막 draw·impact 다음 칸
    const roles = ['pre', 'draw(머리 55%)', 'draw(끝까지 · 붓털 갈라짐)', 'decay', 'decay', 'decay'];
    expect(fxHoldFrame({ frames: 6, impactFrame: 1, brushStroke: true, frameRoles: roles } as SheetJson)).toBe(3);
    const cleave = ['pre', 'draw(내려옴)', 'impact(지면 붓획 · 판정)', 'decay', 'decay', 'decay'];
    expect(fxHoldFrame({ frames: 6, impactFrame: 2, brushStroke: true, frameRoles: cleave } as SheetJson)).toBe(3);
  });
});
