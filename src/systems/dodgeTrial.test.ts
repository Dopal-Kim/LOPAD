import { describe, expect, it } from 'vitest';
import {
  ARENA_SHAPES,
  DODGE_TRIAL,
  TASK_IDS,
  emptyTaskResult,
  gradeTrial,
  presetResults,
  taskScore,
  type TaskResult,
} from './dodgeTrial';
import {
  buildArena,
  cellIndexAt,
  erodeTimeForRank,
  erodedFraction,
  isFloorAt,
  pickShape,
  pillarAt,
  placePillars,
} from './dodgeTrialArena';
import {
  angleDiff,
  cueEndMs,
  cueFireMs,
  lineTelegraphMs,
  pickWallAngle,
  ringBeadAngles,
  ringHits,
  ringRadius,
  steer,
  taskCues,
  taskDurationMs,
  wallFrame,
} from './dodgeTrialTasks';

/** 결정적 의사 난수 (mulberry32) */
const seeded = (seed: number) => () => {
  seed |= 0;
  seed = (seed + 0x6d2b79f5) | 0;
  let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};

const all = (over: Partial<TaskResult>[] = []): TaskResult[] =>
  TASK_IDS.map((id, i) => ({ ...emptyTaskResult(id), ...(over[i] ?? {}) }));

describe('dodgeTrial 51라운드: 과제 5개 · 등급', () => {
  it('과제 순서: 예고선 → 고리 → 유도탄 → 벽 → 종합', () => {
    expect(TASK_IDS).toEqual(['lines', 'ring', 'homing', 'wall', 'mix']);
  });
  it('과제 점수: 피격마다 감점, 떨어지면 0', () => {
    expect(taskScore(emptyTaskResult('lines'))).toBe(100);
    expect(taskScore({ ...emptyTaskResult('ring'), hits: 1 })).toBe(100 - DODGE_TRIAL.GRADE.HIT_PENALTY);
    expect(taskScore({ ...emptyTaskResult('ring'), hits: 9 })).toBe(0);
    expect(taskScore({ ...emptyTaskResult('wall'), fell: true })).toBe(DODGE_TRIAL.GRADE.FELL_SCORE);
  });
  it('전부 무피격 = S(+3), 피격·떨어짐이 늘수록 내려간다', () => {
    expect(gradeTrial(all())).toMatchObject({ grade: 'S', bonus: 3, score: 100, fell: false });
    expect(gradeTrial(all([{ hits: 1 }])).grade).toBe('S');
    expect(gradeTrial(all([{ hits: 1 }, { hits: 1 }, { hits: 1 }]))).toMatchObject({ grade: 'A', bonus: 2 });
    expect(gradeTrial(all([{ fell: true }, { hits: 1 }, { hits: 1 }, {}, { hits: 1 }]))).toMatchObject({
      grade: 'B',
      bonus: 1,
    });
    expect(gradeTrial(all([{ fell: true }, { fell: true }, { hits: 3 }]))).toMatchObject({ grade: 'C', bonus: 0 });
  });
  it('떨어짐은 그 과제만 0점 — 나머지 과제는 그대로 센다', () => {
    const r = gradeTrial(all([{}, {}, { fell: true }]));
    expect(r.fell).toBe(true);
    expect(r.tasks.map((t) => t.score)).toEqual([100, 100, 0, 100, 100]);
    expect(r.grade).toBe('A');
  });
  it('결과가 모자라면(중간 종료) 빠진 과제는 0점', () => {
    expect(gradeTrial([]).grade).toBe('C');
    expect(gradeTrial([]).tasks).toHaveLength(5);
  });
  it('강제 등급 프리셋은 그 등급이 된다, 보상 0~3', () => {
    for (const g of ['S', 'A', 'B', 'C'] as const) expect(gradeTrial(presetResults(g)).grade).toBe(g);
    expect(gradeTrial(presetResults('fell')).fell).toBe(true);
    const T = DODGE_TRIAL.GRADE.TIERS;
    for (let i = 1; i < T.length; i++) expect(T[i].minScore).toBeLessThan(T[i - 1].minScore);
    expect(T.map((t) => t.bonus)).toEqual([3, 2, 1, 0]);
  });
});

describe('dodgeTrial 51라운드: 박자 (읽으면 피할 수 있게)', () => {
  it('과제마다 4~6초 (마지막 위협 끝 기준)', () => {
    for (const id of TASK_IDS) {
      const d = taskDurationMs(id);
      expect(d, id).toBeGreaterThanOrEqual(4000);
      expect(d, id).toBeLessThanOrEqual(6000);
    }
  });
  it('모든 위협은 예고가 먼저 (예고 ≥ 0.5초), 같은 과제의 예고 시작은 0.7초 이상 간격', () => {
    for (const id of TASK_IDS) {
      const cues = taskCues(id);
      for (const c of cues) expect(cueFireMs(c, id) - c.at, `${id} ${c.kind}`).toBeGreaterThanOrEqual(500);
      for (let i = 1; i < cues.length; i++) expect(cues[i].at - cues[i - 1].at, id).toBeGreaterThanOrEqual(700);
    }
  });
  it('한꺼번에 살아 있는 위협 묶음은 많아야 3 (화면을 덮는 난사 없음)', () => {
    for (const id of TASK_IDS) {
      const cues = taskCues(id);
      for (const c of cues) {
        const t = c.at + 1;
        const live = cues.filter((d) => d.at <= t && cueEndMs(d, id) > t).length;
        expect(live, `${id} @${c.at}`).toBeLessThanOrEqual(3);
      }
    }
  });
  it('과제별 주제: ① 예고선만 ② 고리만 ③ 유도탄만 ④ 벽만 ⑤ 섞임', () => {
    const kinds = (id: (typeof TASK_IDS)[number]) => [...new Set(taskCues(id).map((c) => c.kind))].sort();
    expect(kinds('lines')).toEqual(['line']);
    expect(kinds('ring')).toEqual(['ring']);
    expect(kinds('homing')).toEqual(['homing']);
    expect(kinds('wall')).toEqual(['wall']);
    expect(kinds('mix').length).toBeGreaterThanOrEqual(3);
  });
  it('갉아먹힘은 ②·⑤ 에서만, 기둥은 ③ 에서만', () => {
    for (const id of TASK_IDS) {
      const def = DODGE_TRIAL.TASKS[id];
      expect(Boolean(def.erosion), id).toBe(id === 'ring' || id === 'mix');
      expect(def.pillars[1] > 0, id).toBe(id === 'homing');
    }
  });
  it('예고선 예고는 과제 안에서 짧아진다 (처음 → 끝)', () => {
    const [a, b] = DODGE_TRIAL.LINES.TELEGRAPH_MS;
    expect(lineTelegraphMs(0, 'lines')).toBe(a);
    const last = taskCues('lines').at(-1)!.at;
    expect(lineTelegraphMs(last, 'lines')).toBeCloseTo(b);
  });
});

describe('dodgeTrial 고리 · 유도 · 벽 기하', () => {
  it('고리: 예고 동안 R0, 이후 조여 0', () => {
    const W = DODGE_TRIAL.RING.WARN_MS;
    expect(ringRadius(0, 1000, 90)).toBe(90);
    expect(ringRadius(W + 500, 1000, 90)).toBeCloseTo(45);
    expect(ringRadius(W + 2000, 1000, 90)).toBe(0);
  });
  it('고리 판정: 띠 위 + 틈 밖 = 맞음, 틈 안 = 안전, 띠 밖 = 안전, 다 조여 든 중심 = 맞음', () => {
    const hitR = 5;
    // 틈 = 오른쪽(0 rad) 60°
    expect(ringHits(0, 0, 40, 0, 60, -40, 0, hitR, 2.5)).toBe(true);
    expect(ringHits(0, 0, 40, 0, 60, 40, 0, hitR, 2.5)).toBe(false);
    expect(ringHits(0, 0, 40, 0, 60, 0, 10, hitR, 2.5)).toBe(false);
    expect(ringHits(0, 0, 2, 0, 60, 0, 0, hitR, 2.5)).toBe(true);
    // 틈 가장자리에 몸이 걸치면 맞는다
    const edge = (29 * Math.PI) / 180;
    expect(ringHits(0, 0, 40, 0, 60, 40 * Math.cos(edge), 40 * Math.sin(edge), hitR, 2.5)).toBe(true);
  });
  it('고리 구슬: 틈 안에는 없다', () => {
    const beads = ringBeadAngles(90, 0, 60, 7);
    expect(beads.length).toBeGreaterThan(50);
    for (const a of beads) expect(Math.abs(angleDiff(a, 0))).toBeGreaterThan(Math.PI / 6);
  });
  it('유도탄 회전: 한계 안에서만 돈다', () => {
    expect(steer(0, Math.PI / 2, 0.1)).toBeCloseTo(0.1);
    expect(steer(0, -Math.PI / 2, 0.1)).toBeCloseTo(-0.1);
    expect(steer(0, 0.05, 0.1)).toBeCloseTo(0.05);
    expect(steer(3, -3, 1)).toBeCloseTo(3 + (Math.PI * 2 - 6));
  });
  it('벽: 경기장 상자를 다 덮고, 직전과 90° 이상 다른 방향', () => {
    const b = { minX: -100, maxX: 100, minY: -60, maxY: 60 };
    const f = wallFrame(b, 0, 12);
    expect(f.from).toBe(-112);
    expect(f.to).toBe(112);
    expect(f.half).toBe(72);
    const rnd = seeded(4);
    let prev: number | null = null;
    for (let k = 0; k < 30; k++) {
      const a = pickWallAngle(prev, rnd);
      if (prev !== null) expect(Math.abs(angleDiff(a, prev))).toBeGreaterThanOrEqual(Math.PI / 2 - 1e-6);
      prev = a;
    }
  });
  it('벽 탄 간격은 판정 지름보다 좁다 (걸어서 빠질 틈이 없다)', () => {
    const d = 2 * (DODGE_TRIAL.PLAYER.HIT_RADIUS_PX + DODGE_TRIAL.BULLET.RADIUS_PX);
    expect(DODGE_TRIAL.WALL.SPACING_PX).toBeLessThan(d);
  });
});

describe('dodgeTrialArena 경기장 모양 · 갉아먹힘 · 기둥', () => {
  it('모양 뽑기: 목록 안에서', () => {
    const seen = new Set(Array.from({ length: 40 }, (_, i) => pickShape(i / 40, ARENA_SHAPES)));
    expect([...seen].sort()).toEqual([...ARENA_SHAPES].sort());
    expect(pickShape(0.99, ['circle'])).toBe('circle');
  });
  it('모든 과제·모양: 시작 자리(중심·발)는 바닥이고 끝까지 남는다, 격자 안', () => {
    for (const id of TASK_IDS) {
      const def = DODGE_TRIAL.TASKS[id];
      for (const shape of def.shapes)
        for (let seed = 1; seed <= 8; seed++) {
          const m = buildArena(shape, seeded(seed * 31 + shape.length), def.erosion);
          expect(m.cells).toBeGreaterThan(200);
          const foot = DODGE_TRIAL.PLAYER.FOOT_OFFSET_PX;
          expect(isFloorAt(m, 0, foot, 0)).toBe(true);
          expect(isFloorAt(m, 0, foot, 1e9)).toBe(true);
          expect(m.bounds.maxY).toBeLessThanOrEqual(DODGE_TRIAL.ARENA.HALF_H_PX + m.cell);
          expect(m.bounds.maxX).toBeLessThanOrEqual(DODGE_TRIAL.ARENA.HALF_W_PX + m.cell);
        }
    }
  });
  it('같은 시드 = 같은 경기장, 다른 시드 = 다른 경기장', () => {
    const a = buildArena('polygon', seeded(7));
    const b = buildArena('polygon', seeded(7));
    const c = buildArena('polygon', seeded(8));
    expect(Array.from(a.floor)).toEqual(Array.from(b.floor));
    expect(Array.from(a.floor)).not.toEqual(Array.from(c.floor));
  });
  it('갉아먹힘 없음(null) = 끝까지 그대로', () => {
    const m = buildArena('circle', seeded(3), null);
    expect(Array.from(m.order).every((i) => m.erodeAt[i] === Infinity)).toBe(true);
    expect(erodedFraction(5000, null)).toBe(0);
  });
  it('갉아먹힘(②): 가장자리부터, 시작 전 0 → 끝에 1 − endFloorFrac', () => {
    const E = DODGE_TRIAL.TASKS.ring.erosion!;
    const m = buildArena('circle', seeded(3), E);
    const n = m.order.length;
    const avg = (from: number, to: number) => {
      let s = 0;
      for (let k = from; k < to; k++) s += m.depth[m.order[k]];
      return s / (to - from);
    };
    expect(avg(0, Math.floor(n * 0.1))).toBeLessThan(avg(Math.floor(n * 0.6), Math.floor(n * 0.7)));
    for (let k = 1; k < n; k++) expect(m.erodeAt[m.order[k]]).toBeGreaterThanOrEqual(m.erodeAt[m.order[k - 1]]);
    expect(erodedFraction(0, E)).toBe(0);
    expect(erodedFraction(E.endMs, E)).toBeCloseTo(1 - E.endFloorFrac);
    const alive = (t: number) => Array.from(m.order).filter((i) => m.erodeAt[i] > t).length / m.cells;
    expect(alive(E.startMs - 1)).toBe(1);
    expect(alive(E.endMs)).toBeCloseTo(E.endFloorFrac, 1);
    expect(erodeTimeForRank(0.99, E)).toBe(Infinity);
  });
  it('기둥(③): 바닥 위, 시작 자리와 떨어져, 서로 겹치지 않게', () => {
    for (let seed = 1; seed <= 10; seed++) {
      const m = buildArena('circle', seeded(seed));
      const ps = placePillars(m, 4, seeded(seed + 100));
      expect(ps.length).toBeGreaterThanOrEqual(2);
      for (const p of ps) {
        expect(isFloorAt(m, p.x, p.y, 0)).toBe(true);
        expect(Math.hypot(p.x, p.y)).toBeGreaterThan(DODGE_TRIAL.ARENA.PILLAR.CLEAR_CENTER_PX);
        expect(pillarAt(m, p.x, p.y)).toBe(p);
      }
      for (let i = 0; i < ps.length; i++)
        for (let j = i + 1; j < ps.length; j++)
          expect(Math.hypot(ps[i].x - ps[j].x, ps[i].y - ps[j].y)).toBeGreaterThan(ps[i].r + ps[j].r);
      expect(pillarAt(m, 0, 0)).toBeNull();
    }
  });
  it('칸 좌표: 격자 밖은 -1', () => {
    const m = buildArena('circle', seeded(1));
    expect(cellIndexAt(m, 0, 0)).toBeGreaterThanOrEqual(0);
    expect(cellIndexAt(m, 9999, 0)).toBe(-1);
    expect(isFloorAt(m, 9999, 0, 0)).toBe(false);
  });
});
