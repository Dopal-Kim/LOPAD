import { describe, expect, it } from 'vitest';
import { DEFAULT_TITLE_SPEC, TITLE_UI } from './themeTitle';
import {
  breathPhase,
  defaultIndex,
  diveOrigin,
  diveZoom,
  emberAlpha,
  emberFlicker,
  crowFlightY,
  hotkeyIndex,
  introState,
  isWakeKey,
  logoDoneMs,
  logoProgress,
  layerOffset,
  lerpStep,
  menuFrameSize,
  metaAutoEnter,
  metaMemo,
  parallaxInput,
  parseAlphaMax,
  parseDrift,
  parseRange,
  pickWeighted,
  readTitleSpec,
  reducedMotion,
  splitNote,
  stepIndex,
  titleItems,
  voiceAlpha,
  voiceLevel,
  type TitleLabels,
} from './titleView';

const LABELS: TitleLabels = {
  continue: '이어 쓴다',
  newRun: '다시 태어난다',
  newRunDeleteSave: '다시 태어난다 (일기장을 찢는다)',
  training: '수련장',
  lab: '무기 시험장',
  settings: '설정',
  quit: '끝내기',
};

describe('아트 문구 숫자 읽기', () => {
  it('초당 범위', () => {
    expect(parseRange('초당 6~9', [0, 0])).toEqual([6, 9]);
    expect(parseRange('초당 1', [0, 0])).toEqual([1, 1]);
    expect(parseRange('목소리가 켜진 무기에서만 초당 2~3', [0, 0])).toEqual([2, 3]);
    expect(parseRange(undefined, [4, 5])).toEqual([4, 5]);
  });
  it('흔들림·최대 알파', () => {
    expect(parseDrift('사인 흔들림 진폭 6~14px, 주기 1.6~2.6s', { amp: [0, 0], ms: [0, 0] })).toEqual({
      amp: [6, 14],
      ms: [1600, 2600],
    });
    expect(parseAlphaMax('최대 0.5', 1)).toBe(0.5);
    expect(parseAlphaMax('0 → 1 (0.3s)', 1)).toBe(1);
  });
});

describe('readTitleSpec', () => {
  it('JSON 이 없으면 기본값', () => {
    expect(readTitleSpec(null, null, null, null)).toEqual(DEFAULT_TITLE_SPEC);
  });
  it('아트 JSON 값을 읽는다', () => {
    const spec = readTitleSpec(
      {
        layers: [
          { key: 'title_bg_far', parallax: 0.2 },
          { key: 'title_fx_glow_hero', x: 10, y: 20 },
        ],
        parallax: {
          maxOffsetPx: { x: 30, y: 12 },
          offset: '레이어 오프셋 = … lerp 0.05/frame',
          edgeCover: '레이어를 scale 1.04 로 깔면',
          input: '포인터 + 느린 표류(사인, 주기 20s, 진폭 0.3)',
        },
        voices: [
          {
            weapon: 'bow',
            x: 1,
            y: 2,
            emberOrigin: [3, 4],
            pulse: { periodMs: 8000, offsetMs: 100, onMs: 900, alpha: [0.2, 0.9] },
          },
        ],
        logo: { x: 50, lettersBox: [0, 0, 10, 280], subtitleBox: [0, 300, 10, 380], emberDots: { katana: [1, 2] } },
        menu: { area: { x: 100, y: 600, w: 420, h: 360 } },
      },
      {
        rows: ['amber_s', 'amber_m', 'amber_l', 'katana', 'greatsword', 'dagger', 'bow'],
        emitters: [
          { name: 'city', rows: ['amber_s'], area: { x: 1, y: 2, w: 3, h: 4 }, rate: '초당 1', alpha: '최대 0.5' },
          { name: 'voices', rows: ['katana', 'bow'], origins: 'title.json voices[].emberOrigin', rate: '초당 2~3' },
        ],
      },
      { instances: [{ name: 'f', y: 10, alpha: 0.5, speedPxPerSec: 3 }] },
      { slice: { left: 40 }, contentInset: { left: 30, top: 33 } },
    );
    expect(spec.layers.far).toBe(0.2);
    expect(spec.glow).toMatchObject({ x: 10, y: 20 });
    expect(spec.parallax).toEqual({ maxX: 30, maxY: 12, lerp: 0.05, cover: 1.04, driftMs: 20000, driftAmp: 0.3 });
    expect(spec.voices).toEqual([
      { weapon: 'bow', x: 1, y: 2, ember: [3, 4], periodMs: 8000, offsetMs: 100, onMs: 900, alpha: [0.2, 0.9] },
    ]);
    expect(spec.logo.x).toBe(50);
    expect(spec.logo.splitY).toBe(290);
    expect(spec.logo.dots.katana).toEqual([1, 2]);
    expect(spec.logo.dots.bow).toEqual(DEFAULT_TITLE_SPEC.logo.dots.bow);
    expect(spec.menu).toMatchObject({ x: 100, y: 600, w: 420, h: 360, slice: 40, insetX: 30, insetY: 33 });
    expect(spec.fog).toEqual([{ name: 'f', y: 10, scaleY: 1, alpha: 0.5, speed: 3 }]);
    expect(spec.emitters[0]).toMatchObject({ name: 'city', rows: [0], rate: [1, 1], alphaMax: 0.5, layer: 'city' });
    expect(spec.emitters[1]).toMatchObject({ name: 'voices', rows: [3, 6], voice: true, area: null, layer: 'near' });
  });
});

describe('움직임', () => {
  it('호흡은 0 에서 시작해 반 주기에 1', () => {
    expect(breathPhase(0, 4200)).toBeCloseTo(0);
    expect(breathPhase(2100, 4200)).toBeCloseTo(1);
    expect(breathPhase(4200, 4200)).toBeCloseTo(0);
  });
  it('목소리 9.6초 순환 — 차례로 켜진다', () => {
    const [k, g] = DEFAULT_TITLE_SPEC.voices;
    expect(voiceLevel(850, k)).toBeCloseTo(1);
    expect(voiceLevel(850, g)).toBe(0);
    expect(voiceLevel(2400 + 850, g)).toBeCloseTo(1);
    expect(voiceLevel(9600 + 850, k)).toBeCloseTo(1);
    expect(voiceAlpha(0, [0.25, 1])).toBe(0.25);
    expect(voiceAlpha(1, [0.25, 1])).toBe(1);
  });
  it('패럴랙스: 모션 줄이기면 0, 그 밖은 -1..1', () => {
    const p = DEFAULT_TITLE_SPEC.parallax;
    expect(parallaxInput({ x: 1, y: 1 }, 0, p, true)).toEqual({ x: 0, y: 0 });
    const v = parallaxInput({ x: 1, y: -1 }, 6000, p, false);
    expect(v.x).toBeLessThanOrEqual(1);
    expect(v.y).toBeGreaterThanOrEqual(-1);
    expect(layerOffset(1, 1, 28)).toBe(-28);
    expect(layerOffset(-1, 0.15, 28)).toBe(4);
  });
  it('lerp 는 프레임 길이에 무관', () => {
    const one = lerpStep(lerpStep(0, 1, 0.035, 1000 / 60), 1, 0.035, 1000 / 60);
    expect(lerpStep(0, 1, 0.035, 2000 / 60)).toBeCloseTo(one, 6);
  });
  it('불티 알파·가중치', () => {
    expect(emberAlpha(0, 5000)).toBe(0);
    expect(emberAlpha(150, 5000)).toBeCloseTo(0.5);
    expect(emberAlpha(2500, 5000, 0.5)).toBe(0.5);
    expect(emberAlpha(4400, 5000)).toBeCloseTo(0.5);
    expect(pickWeighted([5, 3, 1], 0)).toBe(0);
    expect(pickWeighted([5, 3, 1], 0.6)).toBe(1);
    expect(pickWeighted([5, 3, 1], 0.99)).toBe(2);
  });
});

describe('등장', () => {
  it('P21 느린 등장: 5초 안에 메뉴까지 (키·클릭이면 바로)', () => {
    const I = TITLE_UI.intro;
    expect(I.menuAt + I.menuMs).toBeLessThanOrEqual(5000);
    expect(I.blackMs + I.revealMs).toBeLessThanOrEqual(5000);
    expect(I.dotsAt + 3 * I.dotGapMs + I.dotMs).toBeLessThanOrEqual(5000);
    const s0 = introState(0, false);
    expect(s0).toMatchObject({ reveal: 0, logo: 0, menu: 0, done: false });
    const end = introState(I.endMs, false);
    expect(end).toMatchObject({ reveal: 1, logo: 1, sub: 1, menu: 1, done: true });
    expect(end.dots).toEqual([1, 1, 1, 1]);
  });
  it('불씨는 칼→대검→단검→활 순서로', () => {
    const s = introState(TITLE_UI.intro.dotsAt + TITLE_UI.intro.dotGapMs + 10, false);
    expect(s.dots[0]).toBeGreaterThan(s.dots[1]);
    expect(s.dots[2]).toBe(0);
  });
  it('모션 줄이기는 짧은 페이드', () => {
    expect(introState(TITLE_UI.intro.blackMs + TITLE_UI.intro.fadeMs, true).reveal).toBe(1);
    expect(introState(TITLE_UI.intro.blackMs + TITLE_UI.intro.fadeMs, false).reveal).toBeLessThan(1);
  });
});

describe('로고 쓰기 진행 (62 루프 3 UI H · P0-N1)', () => {
  const MS = 2600;
  it('메뉴가 열리는 시각에 멈추지 않고 끝까지 간다', () => {
    const atMenu = logoProgress(TITLE_UI.intro.menuAt, { complete: false, revealMs: MS });
    expect(atMenu.revealP).toBeLessThan(1);
    const done = logoProgress(logoDoneMs(MS), { complete: false, revealMs: MS });
    expect(done.revealP).toBe(1);
    expect(done.sub).toBe(1);
    expect(done.dots).toEqual([1, 1, 1, 1]);
  });
  it('넘김·돌아옴(complete)은 처음부터 완성', () => {
    const p = logoProgress(0, { complete: true, revealMs: MS });
    expect(p).toEqual({ revealP: 1, logo: 1, sub: 1, dots: [1, 1, 1, 1] });
  });
  it('넘김 키가 미는 시각은 쓰기 끝(logoAt+쓰기) 이후', () => {
    expect(logoDoneMs(MS)).toBeGreaterThanOrEqual(TITLE_UI.intro.logoAt + MS);
    expect(logoDoneMs()).toBe(TITLE_UI.intro.endMs);
  });
});

describe('메뉴', () => {
  it('세이브가 없으면 이어 하기를 숨기고 4개 이하', () => {
    const it0 = titleItems({ hasSave: false, desktop: false, dev: false, labels: LABELS });
    expect(it0.map((i) => i.id)).toEqual(['newRun', 'training', 'settings']);
    expect(it0[0]).toMatchObject({ label: '다시 태어난다', hint: '' });
    const it1 = titleItems({ hasSave: true, desktop: false, dev: false, labels: LABELS });
    expect(it1.map((i) => i.id)).toEqual(['continue', 'newRun', 'training', 'settings']);
    expect(it1[1]).toMatchObject({ label: '다시 태어난다', hint: '일기장을 찢는다' });
  });
  it('시험장은 개발용, 끝내기는 데스크톱만', () => {
    const ids = titleItems({ hasSave: true, desktop: true, dev: true, labels: LABELS }).map((i) => i.id);
    expect(ids).toEqual(['continue', 'newRun', 'training', 'lab', 'settings', 'quit']);
  });
  it('괄호 덧말 나누기', () => {
    expect(splitNote('이어 쓴다 (적힌 것이 없다)')).toEqual({ main: '이어 쓴다', note: '적힌 것이 없다' });
    expect(splitNote('수련장')).toEqual({ main: '수련장', note: '' });
  });
  it('이동·숫자 키', () => {
    const items = titleItems({ hasSave: true, desktop: false, dev: false, labels: LABELS });
    items[2].enabled = false;
    expect(defaultIndex(items)).toBe(0);
    expect(stepIndex(items, 1, 1)).toBe(3);
    expect(stepIndex(items, 0, -1)).toBe(3);
    expect(hotkeyIndex(items, '2')).toBe(1);
    expect(hotkeyIndex(items, '5')).toBe(-1);
    expect(hotkeyIndex(items, 'a')).toBe(-1);
  });
  it('틀 크기: 폭은 영역 이상, 높이는 줄 수에 맞춤', () => {
    const m = { rowH: 48, textX: 64, minPadY: 39, insetX: 36, padExtra: 24 };
    expect(menuFrameSize({ w: 400, h: 350 }, 4, 200, m)).toEqual({ w: 400, h: 4 * 48 + 126, rowTop: 63 });
    expect(menuFrameSize({ w: 400, h: 350 }, 3, 200, m).h).toBe(3 * 48 + 126);
    expect(menuFrameSize({ w: 400, h: 350 }, 4, 400, m).w).toBe(64 + 400 + 36 + 12);
  });
  it('모션 줄이기', () => {
    expect(reducedMotion({ shake: 0 }, false)).toBe(true);
    expect(reducedMotion({ shake: 0.5 }, false)).toBe(false);
    expect(reducedMotion(null, true)).toBe(true);
  });
  it('아무 키', () => {
    expect(isWakeKey('a')).toBe(true);
    expect(isWakeKey('Enter')).toBe(true);
    expect(isWakeKey('Shift')).toBe(false);
  });
});

describe('파고들기·메모', () => {
  it('가까운 층일수록 빨리 커지고 끝에서 초점이 가운데로', () => {
    expect(diveZoom(0, 1, 3)).toBe(1);
    expect(diveZoom(1, 1, 3)).toBeCloseTo(3);
    expect(diveZoom(0.5, 1, 3)).toBeGreaterThan(diveZoom(0.5, 0.15, 3));
    const f = { x: 451, y: 342 };
    const c = { x: 480, y: 270 };
    // z=1, pull=0 → 그대로
    expect(diveOrigin(c, f, 1, c, 0)).toEqual(c);
    // pull=1 → 초점이 화면 가운데에 온다: 초점 자리(f)에 있던 점이 가운데로
    const o = diveOrigin(c, f, 2, c, 1);
    expect(o.x + 2 * (f.x - c.x)).toBeCloseTo(c.x);
  });
  it('첫 생에는 메모 없음', () => {
    expect(metaMemo(null)).toBe('');
    expect(metaMemo({ lives: 0, souls: 10, bestFloor: 1 })).toBe('');
    expect(metaMemo({ lives: 3, souls: 120, bestFloor: 1 })).toBe('지난 생 3 · 영혼 120 · 가장 깊이 1층');
  });
});

describe('영혼 메뉴 건너뛰기', () => {
  it('고를 것이 없으면 바로 생으로', () => {
    expect(
      metaAutoEnter({
        id: 'meta',
        lines: [
          { key: 'm:a', enabled: false },
          { key: 'enter', enabled: true },
        ],
      }),
    ).toBe(true);
    expect(metaAutoEnter({ id: 'meta', lines: [] })).toBe(true);
    expect(metaAutoEnter({ id: 'meta', lines: [{ key: 'm:a', enabled: true }] })).toBe(false);
    expect(metaAutoEnter({ id: 'reward', lines: [] })).toBe(false);
  });
});

describe('P21 어두운 연출', () => {
  const F = TITLE_UI.dark.flicker;
  it('불씨 일렁임은 1 − amp … 1 사이, 잦아듦 구간에서는 더 낮다', () => {
    for (let t = 0; t < 12000; t += 37) {
      const k = emberFlicker(t, 2, F);
      expect(k).toBeGreaterThanOrEqual(0);
      expect(k).toBeLessThanOrEqual(1);
    }
    // seed 0 · 잦아듦 한가운데
    const dip = emberFlicker(F.dipMs / 2, 0, F);
    expect(dip).toBeLessThanOrEqual(F.dip + 1e-9);
  });
  it('까마귀 높이는 로고 글자 상자를 피한다', () => {
    const box: [number, number, number, number] = [242, 64, 1118, 304];
    expect(crowFlightY(0.5, [160, 520], null, 30, 48)).toBe(340);
    const y = crowFlightY(0, [160, 520], box, 30, 48)!;
    expect(y - 30 - 24).toBeGreaterThan(304);
    expect(crowFlightY(1, [160, 520], box, 30, 48)).toBe(520);
    expect(crowFlightY(0.5, [160, 300], box, 30, 48)).toBeNull();
  });
  it('title.json 날씨: 비 두 겹 · 까마귀 · 젖은 재', () => {
    const spec = readTitleSpec(
      {
        layers: [{ key: 'title_fx_rain#near', image: 'title_fx_rain.png', depth: 9.7, ref: 'rain' }],
        rain: {
          instances: [
            { name: 'rain_far', scale: 0.67, alpha: 0.35, speedPxPerSec: { x: 40, y: 520 } },
            { name: 'rain_near', alpha: 0.55, speedPxPerSec: { x: 90, y: 980 } },
          ],
        },
        crows: { frameWidth: 72, frameHeight: 48, flights: { path: 'y 160~520 사이, ±30px 사인 (주기 1.4s)' } },
        ash: {
          rows: ['ash_s', 'ash_l'],
          emitters: [
            {
              name: 'ash_fall',
              rows: ['ash_s', 'ash_l'],
              weights: [3, 1],
              area: { x: -100, y: -40, w: 2120, h: 20 },
              rate: '초당 4~6',
              alpha: '0 → 0.8 (0.6s) → 0 (마지막 1.5s)',
              scale: [0.67, 1],
            },
          ],
        },
      },
      null,
      null,
      null,
    );
    expect(spec.extras).toEqual([]);
    expect(spec.rain).toEqual([
      { layer: 'far', depth: 2.3, scale: 0.67, alpha: 0.35, vx: 40, vy: 520 },
      { layer: 'near', depth: 9.7, scale: 1, alpha: 0.55, vx: 90, vy: 980 },
    ]);
    expect(spec.crows).toMatchObject({ y: [160, 520], swayPx: 30, swayMs: 1400, pivot: [36, 24] });
    expect(spec.ash?.emitters[0]).toMatchObject({ rows: [0, 1], weights: [3, 1], rate: [4, 6], alphaMax: 0.8 });
    expect(spec.ash).toMatchObject({ inMs: 600, outMs: 1500, scale: [0.67, 1], depth: 9.3 });
  });
  it('title.json 새 층: 아는 파일은 빼고, 값이 빠지면 기본, 깊이 순', () => {
    const spec = readTitleSpec(
      {
        layers: [
          { key: 'title_bg_far', image: 'title_bg_far.png', depth: 0 },
          { key: 'title_fx_fog#far', image: 'title_fx_fog.png', depth: 1 },
          { key: 'mist', image: 'title_fx_mist.png', depth: 10.2, blendMode: 'add', speedPxPerSec: -30, alpha: 0.4 },
          { key: 'crows', image: 'title_crows.png', depth: 2.5, x: 300, y: 120, flicker: true },
          { key: 'bad', image: '../x.png', depth: 3 },
        ],
      },
      null,
      null,
      null,
    );
    expect(spec.extras.map((e) => e.image)).toEqual(['title_crows', 'title_fx_mist']);
    expect(spec.extras[0]).toMatchObject({ x: 300, y: 120, parallax: 1, blend: 'NORMAL', speed: 0, flicker: true });
    expect(spec.extras[1]).toMatchObject({ blend: 'ADD', speed: -30, alpha: 0.4 });
    expect(readTitleSpec(null, null, null, null).extras).toEqual([]);
  });
});
