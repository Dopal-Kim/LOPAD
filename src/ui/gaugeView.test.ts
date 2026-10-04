import { describe, expect, it } from 'vitest';
import {
  gaugeKey,
  gaugeView,
  groggySeconds,
  groggyShake,
  groggyView,
  maskEdges,
  partialPx,
  spreadCells,
} from './gaugeView';

describe('gaugeView (56라운드 무기 고유 자원, 계약 §13)', () => {
  it('값이 없거나 모르는 종류면 숨김', () => {
    expect(gaugeView(null)).toBeNull();
    expect(gaugeView(undefined)).toBeNull();
    expect(gaugeView({} as never)).toBeNull();
    expect(gaugeView({ kind: 'heat', label: '', value: 1, max: 1 } as never)).toBeNull();
  });
  it('검기: 단계 = 찬 칸, 다음 칸은 비율 나머지', () => {
    const v = gaugeView({ kind: 'kenki', label: '검기', value: 50, max: 100, stage: 1 });
    expect(v?.cells.map((c) => +c.toFixed(2))).toEqual([1, 0.5, 0]);
    expect(v?.stage).toBe(1);
    expect(v?.full).toBe(false);
  });
  it('검기: 비율이 단계와 어긋나면 단계를 믿는다', () => {
    expect(gaugeView({ kind: 'kenki', label: '', value: 10, max: 100, stage: 2 })?.cells).toEqual([1, 1, 0]);
    expect(gaugeView({ kind: 'kenki', label: '', value: 3, max: 3, stage: 3 })?.full).toBe(true);
    // 단계가 없으면 비율로 (0~3 정수 값도 그대로)
    expect(gaugeView({ kind: 'kenki', label: '', value: 2, max: 3 })?.cells).toEqual([1, 1, 0]);
  });
  it('울분: 이어진 3칸 + 색 구간 (1~33 / 34~66 / 67~100%)', () => {
    const v = gaugeView({ kind: 'grudge', label: '울분', value: 50, max: 100 });
    expect(v?.cells.map((c) => +c.toFixed(2))).toEqual([1, 0.5, 0]);
    expect(v?.stage).toBe(2);
    expect(gaugeView({ kind: 'grudge', label: '', value: 1, max: 100 })?.stage).toBe(1);
    expect(gaugeView({ kind: 'grudge', label: '', value: 0, max: 100 })?.stage).toBe(0);
    expect(gaugeView({ kind: 'grudge', label: '', value: 100, max: 100 })?.full).toBe(true);
    // 시스템이 준 단계 우선
    expect(gaugeView({ kind: 'grudge', label: '', value: 50, max: 100, stage: 3 })?.stage).toBe(3);
  });
  it('낙인: max 칸(기본 5), 정수 스택만', () => {
    expect(gaugeView({ kind: 'brand', label: '낙인', value: 2.7, max: 5 })?.cells).toEqual([1, 1, 0, 0, 0]);
    expect(gaugeView({ kind: 'brand', label: '', value: 5, max: 5 })?.full).toBe(true);
    expect(gaugeView({ kind: 'brand', label: '', value: 1, max: 0 })?.cells.length).toBe(5);
    expect(gaugeView({ kind: 'brand', label: '', value: 99, max: 99 })?.cells.length).toBe(8);
  });
  it('숨: 소수면 부분 칸, focusing 은 숨만', () => {
    const v = gaugeView({ kind: 'breath', label: '숨', value: 1.5, max: 3, focusing: true });
    expect(v?.cells).toEqual([1, 0.5, 0]);
    expect(v?.focusing).toBe(true);
    expect(gaugeView({ kind: 'kenki', label: '', value: 1, max: 3, focusing: true })?.focusing).toBe(false);
  });
  it('표시 키: 같은 표시면 같다', () => {
    const a = gaugeView({ kind: 'breath', label: '숨', value: 1, max: 3 });
    const b = gaugeView({ kind: 'breath', label: '숨', value: 1.001, max: 3 });
    expect(gaugeKey(a)).toBe(gaugeKey(b));
    expect(gaugeKey(null)).toBe('');
  });
  it('칸 채움·부분 px·테두리', () => {
    expect(spreadCells(1.25, 3)).toEqual([1, 0.25, 0]);
    expect(partialPx(8, 0)).toBe(0);
    expect(partialPx(8, 0.01)).toBe(1);
    expect(partialPx(8, 0.99)).toBe(7);
    expect(partialPx(8, 1)).toBe(8);
    const e = maskEdges(['.x.', 'xxx', '.x.']);
    expect(e[1][1]).toBe(false);
    expect(e[0][1]).toBe(true);
    expect(e[0][0]).toBe(false);
  });
});

describe('groggy (56라운드 그로기 1.5초, 계약 §13)', () => {
  it('비활성·없음이면 숨김', () => {
    expect(groggyView(null, 1500)).toBeNull();
    expect(groggyView({ active: false, leftMs: 900 }, 1500)).toBeNull();
  });
  it('남은 비율·초', () => {
    const v = groggyView({ active: true, leftMs: 750 }, 1500);
    expect(v?.ratio).toBe(0.5);
    expect(v?.seconds).toBe('0.8');
    // 전체가 leftMs 보다 작게 오면 leftMs 를 전체로
    expect(groggyView({ active: true, leftMs: 2000 }, 1500)?.ratio).toBe(1);
  });
  it('초 문구: 0.1 단위 올림', () => {
    expect(groggySeconds(1500)).toBe('1.5');
    expect(groggySeconds(1401)).toBe('1.5');
    expect(groggySeconds(1)).toBe('0.1');
    expect(groggySeconds(0)).toBe('0.0');
    expect(groggySeconds(Number.NaN)).toBe('0.0');
  });
  it('떨림 계단 0 → 1 → 0 → -1', () => {
    expect([0, 60, 120, 180, 240].map((t) => groggyShake(t, 60))).toEqual([0, 1, 0, -1, 0]);
  });
});
