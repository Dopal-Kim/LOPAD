import { describe, expect, it } from 'vitest';
import { ComboTracker, arcHit, comboShape, shapeHit, thrustHit } from './combo';
import type { ComboDef } from '../data/types';
import { WEAPONS } from '../data';

const def: ComboDef = {
  shape: 'arc',
  arcDeg: 120,
  bufferMs: 200,
  resetMs: 300,
  finisherRecoverMs: 100,
  hits: [
    { damageMult: 1, sizeMult: 1, durationMs: 300, cancelFromMs: 200, activeMs: 80 },
    { damageMult: 0.6, sizeMult: 1, durationMs: 150, cancelFromMs: 100, activeMs: 60 },
    { damageMult: 0.8, sizeMult: 1, durationMs: 200, cancelFromMs: 200, activeMs: 60 },
  ],
};

describe('48라운드 3연격 상태 머신', () => {
  it('1 → 2 → 3 → (마지막 타 뒤 회복) → 1', () => {
    const c = new ComboTracker(def);
    c.press(0);
    expect(c.poll(0, true)).toBe(0);
    // 다음 타 허용 창 전에 누르면 버퍼에 남는다
    c.press(150);
    expect(c.poll(150, true)).toBeNull();
    expect(c.poll(200, true)).toBe(1);
    c.press(300);
    expect(c.poll(300, true)).toBe(2);
    // 마지막 타: durationMs + finisherRecoverMs 뒤에야 새 연격
    c.press(400);
    expect(c.poll(400, true)).toBeNull();
    c.press(600);
    expect(c.poll(600, true)).toBe(0);
  });

  it('입력 버퍼는 bufferMs 만 유효', () => {
    const c = new ComboTracker(def);
    c.press(0);
    c.poll(0, true);
    c.press(0); // 너무 일찍
    expect(c.poll(250, true)).toBeNull(); // 250 - 0 > 200
  });

  it('리셋 시간이 지나면 1타로, 행동 불가면 기다린다, reset 은 연격을 끊는다', () => {
    const c = new ComboTracker(def);
    c.press(0);
    c.poll(0, true);
    c.press(1000); // 300 + 300 을 넘김
    expect(c.poll(1000, true)).toBe(0);
    c.press(1250);
    expect(c.poll(1250, false)).toBeNull();
    expect(c.poll(1300, true)).toBe(1);
    c.reset();
    c.press(1400);
    expect(c.poll(1400, true)).toBe(0);
  });

  it('시트 cancelFromFrame 로 다음 타 허용 시각을 바꾼다 (이 타 길이 안으로 자름)', () => {
    const c = new ComboTracker(def);
    c.press(0);
    c.poll(0, true);
    c.overrideCancel(120);
    c.press(130);
    expect(c.poll(130, true)).toBe(1);
  });
});

describe('48라운드 판정 모양', () => {
  it('부채꼴: 반경·각도 안만, 대상 반지름만큼 여유', () => {
    expect(arcHit(0, 0, 1, 0, 30, 120, { x: 25, y: 0, r: 4 })).toBe(true);
    expect(arcHit(0, 0, 1, 0, 30, 120, { x: 40, y: 0, r: 4 })).toBe(false);
    expect(arcHit(0, 0, 1, 0, 30, 120, { x: 0, y: 20, r: 2 })).toBe(false); // 90° 옆
    expect(arcHit(0, 0, 1, 0, 30, 200, { x: 0, y: 20, r: 2 })).toBe(true);
    expect(arcHit(0, 0, 1, 0, 30, 120, { x: -20, y: 0, r: 4 })).toBe(false); // 뒤
    expect(arcHit(0, 0, 1, 0, 30, 120, { x: 1, y: 1, r: 4 })).toBe(true); // 겹침
  });

  it('찌르기: 앞으로 뻗는 직사각형 (옆으로 넓지 않다)', () => {
    expect(thrustHit(0, 0, 1, 0, 30, 10, { x: 28, y: 0, r: 3 })).toBe(true);
    expect(thrustHit(0, 0, 1, 0, 30, 10, { x: 15, y: 12, r: 3 })).toBe(false);
    expect(thrustHit(0, 0, 0, 1, 30, 10, { x: 0, y: 20, r: 3 })).toBe(true);
    expect(thrustHit(0, 0, 1, 0, 30, 10, { x: -10, y: 0, r: 3 })).toBe(false);
  });

  it('범위 1.5배: 칼·대검은 부채꼴, 단검은 찌르기, 활은 연격 없음 (데이터)', () => {
    expect(WEAPONS.katana.combo?.shape).toBe('arc');
    expect(WEAPONS.greatsword.combo?.shape).toBe('arc');
    expect(WEAPONS.dagger.combo?.shape).toBe('thrust');
    expect(WEAPONS.bow.combo).toBeUndefined();
    for (const id of ['katana', 'greatsword', 'dagger']) expect(WEAPONS[id].combo!.hits).toHaveLength(3);
    // 1.5배 히트박스 (47라운드 칼 24×16 리치 14 → 36×24 리치 21)
    expect(WEAPONS.katana.hitbox).toMatchObject({ width: 36, height: 24, reach: 21 });
    expect(WEAPONS.bow.hitbox).toMatchObject({ width: 6, height: 6, reach: 12 });
    // 대검 3타가 가장 크다(피해), 칼 2타는 1타보다 빠르다
    const gs = WEAPONS.greatsword.combo!.hits;
    expect(gs[2].damageMult).toBeGreaterThan(gs[0].damageMult);
    const k = WEAPONS.katana.combo!.hits;
    expect(k[1].durationMs).toBeLessThan(k[0].durationMs);
  });

  it('모양: 아트 메모가 데이터보다 우선, 배율 적용, left 는 좌우 반전', () => {
    const k = WEAPONS.katana;
    const s1 = comboShape(k.combo!, k.hitbox, 1);
    expect(s1).toMatchObject({ kind: 'arc', radius: 33, arcDeg: 140 });
    const s2 = comboShape(k.combo!, k.hitbox, 1.5, { hitRadiusPx: 20, arcDeg: 90, arcFromDeg: 65, arcToDeg: -25 });
    expect(s2).toMatchObject({ kind: 'arc', radius: 30, arcDeg: 90, centerDeg: 20 });
    const d = WEAPONS.dagger;
    const t = comboShape(d.combo!, d.hitbox, 2, { thrust: { lengthPx: 24, widthPx: 8, angleDeg: -8, fromPx: 4 } });
    expect(t).toMatchObject({ kind: 'thrust', length: 48, width: 16, angleDeg: -8, fromPx: 8 });
    // 비대칭 호(중심 +20° = 아래쪽으로 치우침): right 면 아래가, left 면 반전돼 역시 아래가 맞는다 (left 는 180-θ)
    if (s2.kind !== 'arc') throw new Error('arc');
    const below = { x: 10, y: 25, r: 2 };
    expect(shapeHit(0, 0, 1, 0, s2, below, 'right')).toBe(true);
    expect(shapeHit(0, 0, -1, 0, s2, { x: -10, y: 25, r: 2 }, 'left')).toBe(true);
    expect(shapeHit(0, 0, -1, 0, s2, { x: -10, y: -25, r: 2 }, 'left')).toBe(false);
  });
});

describe('49라운드 연격 보강 (과열 속도 · 기력 바닥 마지막 타 불가)', () => {
  it('setSpeed 는 다음 타부터 길이·다음 타 허용을 줄인다', () => {
    const c = new ComboTracker(def);
    c.setSpeed(2);
    c.press(0);
    expect(c.poll(0, true)).toBe(0);
    expect(c.currentSpeed).toBe(2);
    expect(c.durationOf(0)).toBe(def.hits[0].durationMs / 2);
    expect(c.readyAt()).toBe(def.hits[0].cancelFromMs / 2);
  });

  it('allowFinisher=false 면 마지막 타 대신 1타', () => {
    const c = new ComboTracker(def);
    let t = 0;
    c.press(t);
    expect(c.poll(t, true)).toBe(0);
    t = c.readyAt();
    c.press(t);
    expect(c.poll(t, true)).toBe(1);
    t = c.readyAt();
    c.press(t);
    expect(c.poll(t, true, false)).toBe(0);
  });
});
