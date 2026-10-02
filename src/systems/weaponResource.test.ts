import { describe, expect, it } from 'vitest';
import { WEAPONS } from '../data';
import type { AmmoResourceDef, HeatResourceDef, StaminaResourceDef } from '../data/types';
import { WeaponResource } from './weaponResource';

const STAMINA: StaminaResourceDef = {
  kind: 'stamina',
  label: '기력',
  max: 100,
  regenPerSec: 50,
  regenDelayMs: 500,
  lowRatio: 0.3,
  recoverRatio: 0.4,
  exhaustedMoveMult: 0.5,
  cost: { hits: [20, 20, 30], dash: 10, dashAttack: 25, slam: 40 },
};

const AMMO: AmmoResourceDef = { kind: 'ammo', label: '화살', max: 3, reloadMs: 1000, lowCount: 1 };

const HEAT: HeatResourceDef = {
  kind: 'heat',
  label: '열기',
  max: 100,
  gainPerHit: [40, 40, 40],
  decayPerSec: 100,
  decayDelayMs: 300,
  stages: [30, 60, 90],
  speedMults: [1, 1.1, 1.2, 1.3],
  overheatHoldMs: 500,
  cooldownMs: 1000,
};

describe('기력 (stamina)', () => {
  it('소모 → 지연 뒤 회복', () => {
    const r = new WeaponResource(STAMINA);
    r.spend(30, 0);
    expect(r.value).toBe(70);
    r.tick(400, 400); // 지연 안
    expect(r.value).toBe(70);
    r.tick(600, 200); // 지연 지남: 50/s × 0.2s
    expect(r.value).toBeCloseTo(80);
    expect(r.toUi(600).state).toBe('ok');
  });

  it('바닥나면 exhausted: 감속·강한 타 불가, recoverRatio 까지 차면 풀린다', () => {
    const r = new WeaponResource(STAMINA);
    r.spend(120, 0);
    expect(r.value).toBe(0);
    expect(r.isExhausted).toBe(true);
    expect(r.canStrong).toBe(false);
    expect(r.moveMult).toBe(0.5);
    expect(r.toUi(0).state).toBe('exhausted');
    // 30 까지 회복 (recover 40 미만) → 여전히 exhausted
    r.tick(1100, 600);
    expect(r.value).toBeCloseTo(30);
    expect(r.isExhausted).toBe(true);
    r.tick(1300, 200);
    expect(r.value).toBeCloseTo(40);
    expect(r.isExhausted).toBe(false);
    expect(r.canStrong).toBe(true);
    expect(r.toUi(1300).state).toBe('ok');
  });

  it('low 표시는 lowRatio 미만', () => {
    const r = new WeaponResource(STAMINA);
    r.spend(75, 0);
    expect(r.toUi(0).state).toBe('low');
  });

  it('기력 무기는 항상 공격 가능 (일반 타)', () => {
    const r = new WeaponResource(STAMINA);
    r.spend(200, 0);
    expect(r.canAttack()).toBe(true);
  });
});

describe('화살 탄창 (ammo)', () => {
  it('비면 자동 장전, 장전 중 발사 불가, 끝나면 가득', () => {
    const r = new WeaponResource(AMMO);
    expect(r.canFire()).toBe(true);
    expect(r.fire(0)).toBe(false);
    expect(r.fire(10)).toBe(false);
    expect(r.toUi(10).state).toBe('low');
    expect(r.fire(20)).toBe(true); // 마지막 발 → 장전 시작
    expect(r.reloading).toBe(true);
    expect(r.canFire()).toBe(false);
    const ui = r.toUi(520);
    expect(ui.state).toBe('reloading');
    expect(ui.progress).toBeCloseTo(0.5);
    r.tick(1020, 16);
    expect(r.reloading).toBe(false);
    expect(r.value).toBe(3);
  });

  it('수동 장전은 탄창이 덜 찼을 때만', () => {
    const r = new WeaponResource(AMMO);
    expect(r.startReload(0)).toBe(false);
    r.fire(0);
    expect(r.startReload(5)).toBe(true);
    expect(r.startReload(6)).toBe(false); // 이미 장전 중
  });
});

describe('과열 (heat)', () => {
  it('연격마다 가열 → 단계·공격 속도 상승', () => {
    const r = new WeaponResource(HEAT);
    expect(r.stage).toBe(0);
    r.heatUp(0, 0);
    expect(r.stage).toBe(1);
    expect(r.speedMult).toBe(1.1);
    r.heatUp(1, 100);
    expect(r.stage).toBe(2);
    r.heatUp(2, 200);
    expect(r.value).toBe(100);
    expect(r.stage).toBe(3);
    expect(r.toUi(200).stage).toBe(3);
  });

  it('공격을 멈추면 식는다 (지연 뒤)', () => {
    const r = new WeaponResource(HEAT);
    r.heatUp(0, 0);
    r.tick(200, 200);
    expect(r.value).toBe(40);
    r.tick(500, 300);
    expect(r.value).toBeCloseTo(10);
  });

  it('최대 열을 유지하면 과열 → 냉각 동안 공격 불가, 끝나면 0', () => {
    const r = new WeaponResource(HEAT);
    r.heatUp(0, 0);
    r.heatUp(0, 0);
    r.heatUp(0, 0);
    let t = 0;
    while (!r.overheated && t < 1000) {
      t += 100;
      r.heatUp(0, t); // 계속 휘두름
      r.tick(t, 100);
    }
    expect(r.overheated).toBe(true);
    expect(t).toBeGreaterThanOrEqual(HEAT.overheatHoldMs);
    expect(r.canAttack()).toBe(false);
    expect(r.stage).toBe(0);
    const mid = r.toUi(t + 500);
    r.tick(t + 500, 500);
    expect(mid.state).toBe('overheat');
    expect(mid.progress).toBeCloseTo(0.5);
    expect(r.value).toBeCloseTo(50);
    r.tick(t + 1000, 500);
    expect(r.overheated).toBe(false);
    expect(r.value).toBe(0);
    expect(r.canAttack()).toBe(true);
  });

  it('최대에서 잠깐 떨어지면 유지 시간이 초기화된다', () => {
    const r = new WeaponResource(HEAT);
    r.heatUp(0, 0);
    r.heatUp(0, 0);
    r.heatUp(0, 0);
    r.tick(400, 400); // 지연 300 지남 → 식기 시작 (최대 유지 400 누적 후 떨어짐)
    r.tick(500, 100);
    expect(r.value).toBeLessThan(100);
    r.heatUp(0, 500);
    r.tick(900, 400);
    expect(r.overheated).toBe(false);
  });
});

describe('data/weapons.json 자원 (49라운드 임시값)', () => {
  it('칼·대검 기력, 활 탄창, 단검 과열', () => {
    expect(WEAPONS.katana.resource?.kind).toBe('stamina');
    expect(WEAPONS.greatsword.resource?.kind).toBe('stamina');
    expect(WEAPONS.bow.resource?.kind).toBe('ammo');
    expect(WEAPONS.dagger.resource?.kind).toBe('heat');
  });

  it('대검이 칼보다 크게 소모', () => {
    const k = WEAPONS.katana.resource as StaminaResourceDef;
    const g = WEAPONS.greatsword.resource as StaminaResourceDef;
    for (let i = 0; i < 3; i++) expect(g.cost.hits[i]).toBeGreaterThan(k.cost.hits[i]);
  });

  it('휴대: 칼 허리 · 대검 등 · 단검·활 손', () => {
    expect(WEAPONS.katana.carry?.mode).toBe('sheath');
    expect(WEAPONS.greatsword.carry?.mode).toBe('back');
    expect(WEAPONS.dagger.carry?.mode).toBe('hand');
    expect(WEAPONS.bow.carry?.mode).toBe('hand');
  });
});
