import { describe, expect, it } from 'vitest';
import type { UiMenu } from '../contract/ui';
import { menuEscAction, resolveMenuEsc } from './escNav';
import { keyTaken, takeKey } from './keyGate';

/** 53라운드 계약 cancelKey 규칙: 상점·구조물·lab '0', labBranch '9', 필수 메뉴 없음 */
const LAB: Pick<UiMenu, 'id' | 'cancelKey'> = { id: 'lab', cancelKey: '0' };
const BRANCH: Pick<UiMenu, 'id' | 'cancelKey'> = { id: 'labBranch', cancelKey: '9' };
const SHOP: Pick<UiMenu, 'id' | 'cancelKey'> = { id: 'shop', cancelKey: '0' };
const esc = () => ({ key: 'Escape', repeat: false, timeStamp: 1 });

describe('menuEscAction (51라운드 §6 Esc 한 단계 뒤로)', () => {
  it('cancelKey 가 있으면 그 메뉴의 줄 (메뉴마다 다르다)', () => {
    expect(menuEscAction({ id: 'cards', cancelKey: '0' })).toEqual({ kind: 'select', key: '0' });
    expect(menuEscAction(SHOP)).toEqual({ kind: 'select', key: '0' });
    expect(menuEscAction(LAB)).toEqual({ kind: 'select', key: '0' });
    expect(menuEscAction(BRANCH)).toEqual({ kind: 'select', key: '9' });
  });
  it('메타 메뉴는 타이틀로', () => {
    expect(menuEscAction({ id: 'meta' })).toEqual({ kind: 'title' });
  });
  it('반드시 고르는 메뉴(cancelKey 없음)는 머문다', () => {
    for (const id of ['reward', 'passive', 'evolve', 'ending'] as const)
      expect(menuEscAction({ id })).toEqual({ kind: 'stay' });
  });
});

describe('resolveMenuEsc (53라운드 시험장 갈래 첫 Esc 버그)', () => {
  it('갈래 메뉴의 Esc 는 9 — 같은 이벤트가 다시 넘어와도 새로 열린 lab 의 0 을 보내지 않는다', () => {
    const e = esc();
    let open = BRANCH;
    expect(resolveMenuEsc(open, e, false)).toEqual({ kind: 'select', key: '9' });
    // 시스템이 갈래 → 무기 고르기(lab)로 되돌림
    open = LAB;
    // Phaser 가 같은 KeyboardEvent 를 다시 넘김 (프레임 밀림)
    expect(resolveMenuEsc(open, e, false)).toBeNull();
    // 새로 누른 Esc 는 lab 을 닫는다
    expect(resolveMenuEsc(open, esc(), false)).toEqual({ kind: 'select', key: '0' });
  });
  it('상점 ↔ 시험장 전환에서도 앞 메뉴의 Esc 가 뒤 메뉴로 새지 않는다', () => {
    const e = esc();
    expect(resolveMenuEsc(SHOP, e, false)).toEqual({ kind: 'select', key: '0' });
    expect(resolveMenuEsc(LAB, e, false)).toBeNull();
    expect(resolveMenuEsc(BRANCH, e, false)).toBeNull();
  });
  it('닫히는 중·메뉴 없음·자동 반복이면 아무것도 하지 않고 이벤트도 소비하지 않는다', () => {
    const e = esc();
    expect(resolveMenuEsc(BRANCH, e, true)).toBeNull();
    expect(resolveMenuEsc(undefined, e, false)).toBeNull();
    expect(resolveMenuEsc(BRANCH, { ...e, repeat: true }, false)).toBeNull();
    expect(keyTaken(e)).toBe(false);
  });
  it('필수 메뉴는 머무름 안내 (이벤트는 소비)', () => {
    const e = esc();
    expect(resolveMenuEsc({ id: 'reward' }, e, false)).toEqual({ kind: 'stay' });
    expect(keyTaken(e)).toBe(true);
  });
});

describe('takeKey (키 이벤트 한 번 = 동작 한 번)', () => {
  it('같은 이벤트 객체는 한 번만, 다른 이벤트는 각각', () => {
    const a = { key: '1' };
    const b = { key: '1' };
    expect(takeKey(a)).toBe(true);
    expect(takeKey(a)).toBe(false);
    expect(takeKey(b)).toBe(true);
  });
  it('이벤트가 없으면 (직접 호출) 항상 통과', () => {
    expect(takeKey(undefined)).toBe(true);
    expect(takeKey(undefined)).toBe(true);
  });
});
