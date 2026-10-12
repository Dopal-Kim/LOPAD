import { describe, expect, it, beforeEach } from 'vitest';
import { PERSONALITY, WEAPONS } from '../../data';
import { RITUAL_DATA, validateRitual, type RitualData } from '../../data/ritual';
import { META_CONFIG } from '../meta';
import {
  cleanName,
  fanAngles,
  gradeHits,
  leaningWeapon,
  legendOf,
  metaCorner,
  rememberedWeapon,
  shooterFor,
  spotAt,
  whyOf,
} from './ritual';
import { firstSteps } from './firstSteps';
import { autoStrokePoints } from '../setup/autoStrokes';
import { emptyDiary } from '../narrative/diary';

describe('62 시작 의식 규칙 (계약 §20)', () => {
  it('획 ↔ 무기 규칙 줄이 무기마다 있고 숫자가 없다', () => {
    const legend = legendOf(RITUAL_DATA, WEAPONS);
    expect(legend.map((l) => l.weapon)).toEqual(Object.keys(WEAPONS));
    for (const l of legend) {
      expect(l.line).not.toMatch(/[0-9]/);
      expect(l.weaponName).toBe(WEAPONS[l.weapon].name);
    }
  });

  it('왜 이 무기인지: 획·기억 두 갈래, 숫자 금지 (P0-1)', () => {
    for (const id of Object.keys(WEAPONS)) {
      expect(whyOf(RITUAL_DATA, id, 'strokes')).toBeTruthy();
      expect(whyOf(RITUAL_DATA, id, 'remembered')).toBeTruthy();
      expect(whyOf(RITUAL_DATA, id, 'strokes')).not.toMatch(/[0-9]/);
    }
    expect(whyOf(RITUAL_DATA, 'nope', 'strokes')).toBe('');
  });

  it('검증: 의식 문구에 숫자가 있으면 부팅 예외', () => {
    const bad = JSON.parse(JSON.stringify(RITUAL_DATA)) as RitualData;
    bad.why.katana.strokes = '획 길이 0.15';
    expect(() => validateRitual(bad, Object.keys(WEAPONS))).toThrow(/숫자/);
  });

  it('손이 기억한 무기 = 지난 생 무기 (없거나 모르는 무기면 null)', () => {
    const d = emptyDiary();
    expect(rememberedWeapon(d, WEAPONS)).toBeNull();
    const life = { name: 'a', weapon: 'dagger', floor: 1, kills: 3, cleared: false, bosses: [] };
    expect(rememberedWeapon({ pastLives: [{ ...life, weapon: 'bow' }, life] }, WEAPONS)).toBe('dagger');
    expect(rememberedWeapon({ pastLives: [{ ...life, weapon: 'spear' }] }, WEAPONS)).toBeNull();
  });

  it('획이 기우는 무기: 획이 없으면 없음, 자동 획이면 무기 id', () => {
    expect(leaningWeapon([], WEAPONS, PERSONALITY)).toBeUndefined();
    const strokes = autoStrokePoints('fast');
    expect(Object.keys(WEAPONS)).toContain(leaningWeapon(strokes, WEAPONS, PERSONALITY));
  });

  it('영혼 강화 귀퉁이: 살 수 있는 강화가 있을 때만 canBuy (P0-3)', () => {
    expect(metaCorner({ souls: 0, upgrades: {} }, META_CONFIG)).toEqual({ souls: 0, canBuy: false });
    expect(metaCorner({ souls: 1e6, upgrades: {} }, META_CONFIG).canBuy).toBe(true);
  });

  it('회피 시험 등급: 맞은 수 합계 → 등급·보너스', () => {
    const T = RITUAL_DATA.trial;
    expect(gradeHits(0, T)).toEqual({ grade: 'S', bonus: T.bonus.S });
    expect(gradeHits(T.grade.A, T).grade).toBe('A');
    expect(gradeHits(T.grade.B, T).grade).toBe('B');
    expect(gradeHits(T.grade.B + 1, T)).toEqual({ grade: 'C', bonus: T.bonus.C });
  });

  it('부채꼴·사수 차례·자리', () => {
    expect(fanAngles(1, 1, 60)).toEqual([1]);
    const f = fanAngles(0, 5, 90);
    expect(f).toHaveLength(5);
    expect(f[0]).toBeCloseTo(-Math.PI / 4);
    expect(f[4]).toBeCloseTo(Math.PI / 4);
    expect(f[2]).toBeCloseTo(0);
    expect([0, 1, 2, 3].map((v) => shooterFor(v, 2))).toEqual([0, 1, 0, 1]);
    expect(spotAt([0, 0], { x: 10, y: 20, w: 100, h: 40 })).toEqual({ x: 60, y: 40 });
    expect(spotAt([1, -1], { x: 0, y: 0, w: 100, h: 40 })).toEqual({ x: 100, y: 0 });
  });

  it('과제마다 사수 자리가 모자라지 않다', () => {
    for (const t of RITUAL_DATA.trial.tasks) expect(t.shooters).toBeLessThanOrEqual(RITUAL_DATA.trial.spots.length);
  });

  it('이름 다듬기: 공백 제거 · 글자 수 제한', () => {
    expect(cleanName('  도영  ', 12)).toBe('도영');
    expect(cleanName('가나다라마바사아자차카타파', 12)).toHaveLength(12);
  });
});

describe('62 P1-10 첫 생 키 막대', () => {
  beforeEach(() => firstSteps.reset());

  it('첫 생 · 앞 노드 단만', () => {
    firstSteps.begin(0);
    expect(firstSteps.keyBar(0, 3)).toBe(true);
    expect(firstSteps.keyBar(2, 3)).toBe(true);
    expect(firstSteps.keyBar(3, 3)).toBe(false);
    expect(firstSteps.keyBar(null, 3)).toBe(false);
  });

  it('두 번째 생부터 없음', () => {
    firstSteps.begin(1);
    expect(firstSteps.firstLife()).toBe(false);
    expect(firstSteps.keyBar(0, 3)).toBe(false);
  });
});
