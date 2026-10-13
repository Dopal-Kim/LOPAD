/**
 * 62라운드 타이틀 화면 — 순수 계산 (Phaser·DOM 없음, 테스트한다).
 * 아트 JSON 읽기(§29) · 호흡·목소리 빛 위상 · 패럴랙스 · 불티 수명 알파 · 등장 단계 · 메뉴 항목·이동.
 */
import {
  DEFAULT_TITLE_SPEC,
  EMBER_ROWS,
  TITLE_UI,
  TITLE_WEAPONS,
  type EmitterSpec,
  type FogSpec,
  type TitleSpec,
  type VoiceSpec,
} from './themeTitle';

type Obj = Record<string, unknown>;
const obj = (v: unknown): Obj | null => (v && typeof v === 'object' && !Array.isArray(v) ? (v as Obj) : null);
const num = (v: unknown, d: number): number => (typeof v === 'number' && Number.isFinite(v) ? v : d);
const pair = (v: unknown, d: [number, number]): [number, number] =>
  Array.isArray(v) && v.length >= 2 && v.every((x) => typeof x === 'number' && Number.isFinite(x))
    ? [v[0] as number, v[1] as number]
    : d;

export const clamp01 = (v: number): number => (v < 0 ? 0 : v > 1 ? 1 : v);
const mod = (a: number, n: number): number => ((a % n) + n) % n;

// ---------------------------------------------------------------------------------------------
// 아트 문구 숫자 읽기 ("초당 6~9", "최대 0.5", "사인 흔들림 진폭 6~14px, 주기 1.6~2.6s")

/** "초당 6~9" → [6, 9], "초당 1" → [1, 1]. 못 읽으면 d */
export function parseRange(text: unknown, d: [number, number]): [number, number] {
  if (typeof text !== 'string') return d;
  const m = /(\d+(?:\.\d+)?)\s*(?:~\s*(\d+(?:\.\d+)?))?/.exec(text.replace(/^[^\d]*/, ''));
  if (!m) return d;
  const a = Number(m[1]);
  const b = m[2] !== undefined ? Number(m[2]) : a;
  return Number.isFinite(a) && Number.isFinite(b) ? [Math.min(a, b), Math.max(a, b)] : d;
}

/** "사인 흔들림 진폭 6~14px, 주기 1.6~2.6s" → 진폭 [6,14], 주기 ms [1600,2600] */
export function parseDrift(
  text: unknown,
  d: { amp: [number, number]; ms: [number, number] },
): { amp: [number, number]; ms: [number, number] } {
  if (typeof text !== 'string') return d;
  const amp = /진폭\s*([\d.]+)\s*~\s*([\d.]+)/.exec(text);
  const per = /주기\s*([\d.]+)\s*~\s*([\d.]+)\s*s/.exec(text);
  return {
    amp: amp ? [Number(amp[1]), Number(amp[2])] : d.amp,
    ms: per ? [Number(per[1]) * 1000, Number(per[2]) * 1000] : d.ms,
  };
}

/** "최대 0.5" → 0.5 */
export function parseAlphaMax(text: unknown, d: number): number {
  if (typeof text !== 'string') return d;
  const m = /최대\s*([\d.]+)/.exec(text);
  return m ? clamp01(Number(m[1])) : d;
}

// ---------------------------------------------------------------------------------------------
// 아트 JSON → TitleSpec (없는 값은 기본)

export function readTitleSpec(title: unknown, embers: unknown, fog: unknown, frame: unknown): TitleSpec {
  const D = DEFAULT_TITLE_SPEC;
  const t = obj(title);
  const spec: TitleSpec = structuredCloneSpec(D);
  if (t) {
    const layers = Array.isArray(t.layers) ? (t.layers as unknown[]).map(obj) : [];
    for (const l of layers) {
      if (!l || typeof l.key !== 'string') continue;
      if (l.key === 'title_bg_far') spec.layers.far = num(l.parallax, D.layers.far);
      if (l.key === 'title_bg_mid') spec.layers.mid = num(l.parallax, D.layers.mid);
      if (l.key === 'title_bg_near') spec.layers.near = num(l.parallax, D.layers.near);
    }
    const p = obj(t.parallax);
    if (p) {
      const max = obj(p.maxOffsetPx);
      spec.parallax.maxX = num(max?.x, D.parallax.maxX);
      spec.parallax.maxY = num(max?.y, D.parallax.maxY);
      const lerp = typeof p.offset === 'string' ? /lerp\s*([\d.]+)/.exec(p.offset) : null;
      if (lerp) spec.parallax.lerp = clamp01(Number(lerp[1])) || D.parallax.lerp;
      const cover = typeof p.edgeCover === 'string' ? /scale\s*([\d.]+)/.exec(p.edgeCover) : null;
      if (cover) spec.parallax.cover = Math.max(1, Number(cover[1]) || D.parallax.cover);
      if (typeof p.input === 'string') {
        const per = /주기\s*([\d.]+)\s*s/.exec(p.input);
        const amp = /진폭\s*([\d.]+)/.exec(p.input);
        if (per) spec.parallax.driftMs = Number(per[1]) * 1000;
        if (amp) spec.parallax.driftAmp = Number(amp[1]);
      }
    }
    const h = obj(t.hero);
    if (h) {
      const b = obj(h.breath);
      spec.hero = {
        x: num(h.x, D.hero.x),
        y: num(h.y, D.hero.y),
        w: num(h.w, D.hero.w),
        h: num(h.h, D.hero.h),
        feetY: num(h.feetY, D.hero.feetY),
        breathMs: num(b?.periodMs, D.hero.breathMs),
        scaleY: pair(b?.scaleY, D.hero.scaleY),
      };
    }
    const glow = layers.find((l) => l?.key === 'title_fx_glow_hero');
    if (glow) spec.glow = { ...spec.glow, x: num(glow.x, D.glow.x), y: num(glow.y, D.glow.y) };
    if (Array.isArray(t.voices)) {
      const vs: VoiceSpec[] = [];
      for (const raw of t.voices as unknown[]) {
        const v = obj(raw);
        const w = TITLE_WEAPONS.find((x) => x === v?.weapon);
        if (!v || !w) continue;
        const d = D.voices.find((x) => x.weapon === w) ?? D.voices[0];
        const pulse = obj(v.pulse);
        vs.push({
          weapon: w,
          x: num(v.x, d.x),
          y: num(v.y, d.y),
          ember: pair(v.emberOrigin, d.ember),
          periodMs: Math.max(1, num(pulse?.periodMs, d.periodMs)),
          offsetMs: num(pulse?.offsetMs, d.offsetMs),
          onMs: Math.max(1, num(pulse?.onMs, d.onMs)),
          alpha: pair(pulse?.alpha, d.alpha),
        });
      }
      if (vs.length) spec.voices = vs;
    }
    const lg = obj(t.logo);
    if (lg) {
      const size = pair(lg.size, [D.logo.w, D.logo.h]);
      const letters = Array.isArray(lg.lettersBox) ? (lg.lettersBox as number[]) : null;
      const sub = Array.isArray(lg.subtitleBox) ? (lg.subtitleBox as number[]) : null;
      let splitY = D.logo.splitY;
      if (letters && sub && typeof letters[3] === 'number' && typeof sub[1] === 'number')
        splitY = Math.round((letters[3] + sub[1]) / 2);
      const dots = obj(lg.emberDots);
      const out = { ...D.logo.dots };
      for (const w of TITLE_WEAPONS) out[w] = pair(dots?.[w], D.logo.dots[w]);
      spec.logo = { x: num(lg.x, D.logo.x), y: num(lg.y, D.logo.y), w: size[0], h: size[1], splitY, dots: out };
    }
    // art §30: 성문 자리 · 로고 쓰기 마스크
    const gate = obj(t.gate);
    if (gate) {
      const layer = typeof gate.layer === 'string' ? gate.layer.replace(/^title_bg_/, '') : D.gate.layer;
      spec.gate = {
        x: num(gate.x, D.gate.x),
        y: num(gate.y, D.gate.y),
        layer: layer === 'mid' || layer === 'near' ? layer : 'far',
      };
    }
    const lr = obj(t.logoReveal);
    if (lr) {
      const tl = obj(lr.timeline);
      const emb = Array.isArray(tl?.embers) ? (tl!.embers as unknown[]) : null;
      spec.logoReveal = {
        ms: Math.max(1, num(lr.durationMs, D.logoReveal!.ms)),
        softBand: clamp01(num(lr.softBand, D.logoReveal!.softBand)),
        embersAt: clamp01(num(emb?.[0], D.logoReveal!.embersAt)),
      };
    }
    const m = obj(obj(t.menu)?.area);
    if (m)
      spec.menu = {
        ...spec.menu,
        x: num(m.x, D.menu.x),
        y: num(m.y, D.menu.y),
        w: num(m.w, D.menu.w),
        h: num(m.h, D.menu.h),
      };
  }
  const fr = obj(frame);
  if (fr) {
    const s = obj(fr.slice);
    const inset = obj(fr.contentInset);
    spec.menu.slice = num(s?.left, D.menu.slice);
    spec.menu.insetX = num(inset?.left, D.menu.insetX);
    spec.menu.insetY = num(inset?.top, D.menu.insetY);
  }
  const f = obj(fog);
  if (f && Array.isArray(f.instances)) {
    const out: FogSpec[] = [];
    (f.instances as unknown[]).forEach((raw, i) => {
      const o = obj(raw);
      const d = D.fog[Math.min(i, D.fog.length - 1)];
      if (!o) return;
      out.push({
        name: typeof o.name === 'string' ? o.name : d.name,
        y: num(o.y, d.y),
        scaleY: num(o.scaleY, 1),
        alpha: clamp01(num(o.alpha, d.alpha)),
        speed: num(o.speedPxPerSec, d.speed),
      });
    });
    if (out.length) spec.fog = out;
  }
  const e = obj(embers);
  if (e) {
    const rowNames = Array.isArray(e.rows) ? (e.rows as unknown[]).filter((r) => typeof r === 'string') : EMBER_ROWS;
    const piv = obj(e.pivot);
    spec.embers = {
      frameW: num(e.frameWidth, D.embers.frameW),
      frameH: num(e.frameHeight, D.embers.frameH),
      perRow: num(e.framesPerRow, D.embers.perRow),
      pivot: [num(piv?.x, D.embers.pivot[0]), num(piv?.y, D.embers.pivot[1])],
      fps: Math.max(1, num(e.fps, D.embers.fps)),
      rowNames: rowNames as string[],
    };
    if (Array.isArray(e.emitters)) {
      const out: EmitterSpec[] = [];
      for (const raw of e.emitters as unknown[]) {
        const o = obj(raw);
        if (!o || typeof o.name !== 'string') continue;
        const d = D.emitters.find((x) => x.name === o.name) ?? D.emitters[0];
        const rows = Array.isArray(o.rows)
          ? (o.rows as unknown[]).map((r) => (rowNames as string[]).indexOf(String(r))).filter((r) => r >= 0)
          : d.rows;
        if (!rows.length) continue;
        const wts =
          Array.isArray(o.weights) && o.weights.length === rows.length
            ? (o.weights as unknown[]).map((w) => Math.max(0, num(w, 1)))
            : rows.map(() => 1);
        const area = obj(o.area);
        const vel = obj(o.velocity);
        const drift = parseDrift(o.drift, { amp: d.driftAmp, ms: d.driftMs });
        const voice = o.name === 'voices' || typeof o.origins === 'string';
        out.push({
          name: o.name,
          rows,
          weights: wts,
          area: area
            ? { x: num(area.x, 0), y: num(area.y, 0), w: num(area.w, 0), h: num(area.h, 0) }
            : voice
              ? null
              : d.area,
          voice,
          rate: parseRange(o.rate, d.rate),
          life: pair(o.lifespanMs, d.life),
          vx: pair(vel?.x, d.vx),
          vy: pair(vel?.y, d.vy),
          driftAmp: drift.amp,
          driftMs: drift.ms,
          alphaMax: parseAlphaMax(o.alpha, d.alphaMax),
          layer: o.name === 'city' || (typeof o.depth === 'string' && o.depth.includes('far')) ? 'city' : 'near',
        });
      }
      if (out.length) spec.emitters = out;
    }
  }
  return spec;
}

function structuredCloneSpec(s: TitleSpec): TitleSpec {
  return JSON.parse(JSON.stringify(s)) as TitleSpec;
}

// ---------------------------------------------------------------------------------------------
// 움직임

/** 호흡 위상 0(내쉼)~1(들이쉼). 0 에서 시작해 반 주기에 1 */
export function breathPhase(tMs: number, periodMs: number): number {
  return (1 - Math.cos((2 * Math.PI * mod(tMs, periodMs)) / periodMs)) / 2;
}

/** 목소리 빛 세기 0~1 (켜진 동안 사인 종 모양, 꺼진 동안 0) */
export function voiceLevel(tMs: number, v: Pick<VoiceSpec, 'periodMs' | 'offsetMs' | 'onMs'>): number {
  const local = mod(tMs - v.offsetMs, v.periodMs);
  return local < v.onMs ? Math.sin((Math.PI * local) / v.onMs) : 0;
}

/** 세기 → 알파 (꺼진 동안도 최소값 유지) */
export function voiceAlpha(level: number, alpha: [number, number]): number {
  return alpha[0] + (alpha[1] - alpha[0]) * clamp01(level);
}

/** 이 세기 이상이면 그 무기에서 불티가 난다 */
export const VOICE_EMIT_LEVEL = 0.3;

/** 패럴랙스 입력 (-1..1): 포인터(화면 가운데 기준) + 느린 표류. 모션 줄이기면 0 */
export function parallaxInput(
  pointer: { x: number; y: number } | null,
  tMs: number,
  p: Pick<TitleSpec['parallax'], 'driftMs' | 'driftAmp'>,
  reduced: boolean,
): { x: number; y: number } {
  if (reduced) return { x: 0, y: 0 };
  const a = (2 * Math.PI * tMs) / Math.max(1, p.driftMs);
  const px = pointer ? pointer.x : 0;
  const py = pointer ? pointer.y : 0;
  return {
    x: Math.max(-1, Math.min(1, px + Math.sin(a) * p.driftAmp)),
    y: Math.max(-1, Math.min(1, py + Math.cos(a * 0.7) * p.driftAmp)),
  };
}

/** 프레임 길이에 무관한 lerp (기준 60fps 한 프레임에 `k`) */
export function lerpStep(cur: number, target: number, k: number, dtMs: number): number {
  const f = 1 - Math.pow(1 - clamp01(k), Math.max(0, dtMs) / (1000 / 60));
  return cur + (target - cur) * f;
}

/** 레이어 오프셋 (아트 px, 정수) — 포인터 반대쪽으로 */
export function layerOffset(input: number, factor: number, max: number): number {
  return -Math.round(factor * max * input);
}

/** 불티 알파: 0.3초 동안 0→1, 마지막 1.2초 동안 1→0, 최대 alphaMax */
export function emberAlpha(age: number, life: number, alphaMax = 1, inMs = 300, outMs = 1200): number {
  if (age <= 0 || age >= life) return 0;
  const a = Math.min(age / inMs, (life - age) / Math.min(outMs, life / 2), 1);
  return clamp01(a) * alphaMax;
}

/** 가중치로 하나 고르기 (r 0~1) */
export function pickWeighted(weights: number[], r: number): number {
  const sum = weights.reduce((s, w) => s + Math.max(0, w), 0);
  if (sum <= 0) return 0;
  let acc = 0;
  const target = clamp01(r) * sum;
  for (let i = 0; i < weights.length; i++) {
    acc += Math.max(0, weights[i]);
    if (target < acc) return i;
  }
  return weights.length - 1;
}

// ---------------------------------------------------------------------------------------------
// 등장 (그림이 읽힌 뒤 경과 ms)

export interface IntroState {
  /** 덮개가 걷힌 정도 0(검음)~1(다 걷힘) */
  reveal: number;
  logo: number;
  sub: number;
  /** 무기 불씨 4개 점등 0~1 (칼→대검→단검→활) */
  dots: number[];
  /** 메뉴 나타남 0~1 */
  menu: number;
  done: boolean;
}

const easeOut = (t: number): number => Math.sin((clamp01(t) * Math.PI) / 2);

export function introState(tMs: number, reduced: boolean): IntroState {
  const I = TITLE_UI.intro;
  const span = reduced ? I.fadeMs : I.revealMs;
  return {
    reveal: clamp01((tMs - I.blackMs) / span),
    logo: easeOut((tMs - I.logoAt) / I.logoMs),
    sub: easeOut((tMs - I.subAt) / I.subMs),
    dots: TITLE_WEAPONS.map((_, i) => clamp01((tMs - I.dotsAt - i * I.dotGapMs) / I.dotMs)),
    menu: easeOut((tMs - I.menuAt) / I.menuMs),
    done: tMs >= I.endMs,
  };
}

/**
 * 62 루프 3 UI H (점검 P0-N1): 로고 쓰기(art §30)·부제·무기 불씨의 진행. 메뉴 단계와 무관하게 `introT` 로 끝까지 가고,
 * `complete`(키·클릭으로 넘김 · 같은 세션에서 돌아온 타이틀 · 모션 줄이기)면 처음부터 완성 상태.
 * `revealMs` 는 art §30 `logoReveal.ms`(없으면 쓰기 없이 바로 완성).
 */
export interface LogoProgress {
  /** 마스크 로고 쓰기 0~1 */
  revealP: number;
  logo: number;
  sub: number;
  dots: number[];
}

export function logoProgress(tMs: number, opts: { complete: boolean; revealMs?: number }): LogoProgress {
  if (opts.complete || !opts.revealMs) return { revealP: 1, logo: 1, sub: 1, dots: TITLE_WEAPONS.map(() => 1) };
  const it = introState(tMs, false);
  return {
    revealP: clamp01((tMs - TITLE_UI.intro.logoAt) / opts.revealMs),
    logo: it.logo,
    sub: it.sub,
    dots: it.dots,
  };
}

/** 로고·부제·불씨가 모두 다 그려지는 시각 (ms) — 넘김 키가 `introT` 를 여기까지 민다 */
export function logoDoneMs(revealMs?: number): number {
  const I = TITLE_UI.intro;
  const dots = I.dotsAt + (TITLE_WEAPONS.length - 1) * I.dotGapMs + I.dotMs;
  return Math.max(I.endMs, dots, revealMs ? I.logoAt + revealMs : 0);
}

// ---------------------------------------------------------------------------------------------
// 메뉴

export type TitleItemId = 'continue' | 'newRun' | 'training' | 'memory' | 'lab' | 'settings' | 'quit';

export interface TitleItem {
  id: TitleItemId;
  label: string;
  enabled: boolean;
  /** 고른 줄일 때 틀 아래에 보이는 한 줄 (없으면 빈 줄) */
  hint: string;
}

export interface TitleLabels {
  continue: string;
  newRun: string;
  newRunDeleteSave: string;
  training: string;
  /** 62 루프 2 UI E: 일기장 '기억' 장 (지난 생이 있을 때만) */
  memory?: string;
  memoryHint?: string;
  lab: string;
  settings: string;
  quit: string;
}

/** '다시 태어난다 (일기장을 찢는다)' → 이름 '다시 태어난다' · 덧말 '일기장을 찢는다' */
export function splitNote(label: string): { main: string; note: string } {
  const m = /^(.*?)\s*[(（]([^)）]+)[)）]\s*$/.exec(label);
  return m && m[1].trim() ? { main: m[1].trim(), note: m[2].trim() } : { main: label.trim(), note: '' };
}

/**
 * 타이틀 항목 (62 경쟁력 점검 T4·T5 — 4개 이하): 이어 하기(세이브가 없으면 **숨김**) · 새로 태어나기 · 수련장 · 설정,
 * 데스크톱 껍데기면 끝내기(웹에서는 숨김). 무기 시험장은 개발용이라 `dev`(주소 `#lab`·uidebug)일 때만 설정 앞에.
 * 이름에 붙은 괄호 덧말('다시 태어난다 (일기장을 찢는다)')은 고른 줄 안내로 옮긴다(틀 폭에 맞게).
 */
export function titleItems(o: {
  hasSave: boolean;
  desktop: boolean;
  dev: boolean;
  labels: TitleLabels;
  /** 62 루프 2 UI E: 기억 장을 열 수 있다 (계약 C `memory.book()` · 지난 생이 있다) */
  memory?: boolean;
}): TitleItem[] {
  const L = o.labels;
  const fresh = splitNote(o.hasSave ? L.newRunDeleteSave : L.newRun);
  const items: TitleItem[] = [];
  if (o.hasSave) {
    const cont = splitNote(L.continue);
    items.push({ id: 'continue', label: cont.main, enabled: true, hint: cont.note });
  }
  items.push({ id: 'newRun', label: fresh.main, enabled: true, hint: fresh.note });
  items.push({ id: 'training', label: L.training, enabled: true, hint: '' });
  if (o.memory && L.memory) items.push({ id: 'memory', label: L.memory, enabled: true, hint: L.memoryHint ?? '' });
  if (o.dev) items.push({ id: 'lab', label: L.lab, enabled: true, hint: '' });
  items.push({ id: 'settings', label: L.settings, enabled: true, hint: '' });
  if (o.desktop) items.push({ id: 'quit', label: L.quit, enabled: true, hint: '' });
  return items;
}

/** 처음 고른 줄: 세이브가 있으면 이어 하기, 없으면 새로 태어나기 */
export function defaultIndex(items: TitleItem[]): number {
  const i = items.findIndex((it) => it.enabled);
  return i < 0 ? 0 : i;
}

/** 다음 활성 줄 (끝에서 돌아감). 활성 줄이 없으면 그대로 */
export function stepIndex(items: TitleItem[], idx: number, dir: 1 | -1): number {
  const n = items.length;
  for (let k = 1; k <= n; k++) {
    const j = mod(idx + dir * k, n);
    if (items[j]?.enabled) return j;
  }
  return idx;
}

/** 숫자 키 '1'… → 줄 번호 (보이는 순서). 없으면 -1 */
export function hotkeyIndex(items: TitleItem[], key: string): number {
  const n = Number(key);
  return Number.isInteger(n) && n >= 1 && n <= items.length ? n - 1 : -1;
}

/**
 * 메뉴 틀 크기 (아트 px): 폭은 아트 영역보다 좁아지지 않고 글자가 넘치면 늘린다. 높이는 줄 수에 맞춘다(위아래 여백
 * `minPadY + padExtra`) — 4줄 이하로 줄어든 메뉴가 빈 족자로 보이지 않게(62 점검 T4). 영역 아래 끝 기준으로 놓는다.
 */
export function menuFrameSize(
  area: { w: number; h: number },
  rows: number,
  maxLabelW: number,
  m: { rowH: number; textX: number; minPadY: number; insetX: number; padExtra: number },
): { w: number; h: number; rowTop: number } {
  const needW = m.textX + maxLabelW + m.insetX + 12;
  const h = rows * m.rowH + (m.minPadY + m.padExtra) * 2;
  const w = Math.max(area.w, Math.ceil(needW));
  return { w, h, rowTop: Math.round((h - rows * m.rowH) / 2) };
}

/** 모션 줄이기: 설정 흔들림 0(기존 설정 기준) 또는 브라우저 '동작 줄이기' */
export function reducedMotion(settings: { shake?: number } | null | undefined, prefersReduced: boolean): boolean {
  return prefersReduced || (typeof settings?.shake === 'number' && settings.shake <= 0);
}

// ---------------------------------------------------------------------------------------------
// 첫 생으로 들어가기 (62 점검 T8: '그림 속 입구'와 같은 문법 — 키아트 안 성문으로 파고든다)

/** 파고들기 배율: 가까운 층일수록 빨리 커진다 (깊이감). p 0~1 */
export function diveZoom(p: number, factor: number, max: number): number {
  const e = clamp01(p) * clamp01(p) * (3 - 2 * clamp01(p));
  return 1 + (max - 1) * e * (0.55 + 0.45 * clamp01(factor));
}

/**
 * 초점 F(화면 px)를 중심으로 Z 배 확대하면서 F 를 화면 가운데 쪽으로 끌어온다(pull 0~1).
 * 컨테이너 원점 C(화면 px) → 새 원점. 자식은 배율만 Z 배.
 */
export function diveOrigin(
  c: { x: number; y: number },
  f: { x: number; y: number },
  z: number,
  center: { x: number; y: number },
  pull: number,
): { x: number; y: number } {
  const k = clamp01(pull);
  const fx = f.x + (center.x - f.x) * k;
  const fy = f.y + (center.y - f.y) * k;
  return { x: fx + z * (c.x - f.x), y: fy + z * (c.y - f.y) };
}

// ---------------------------------------------------------------------------------------------
// 귀퉁이 메타 메모 (62 점검 T7) — 계약에 값이 생기면 채운다 (지금은 시스템 값 없음 → 숨김)

export interface TitleMetaInfo {
  /** 지난 생 수 */
  lives: number;
  /** 모은 영혼 (메타 화폐) */
  souls: number;
  /** 가장 깊이 간 층 (0 = 없음) */
  bestFloor: number;
}

/** '지난 생 3 · 영혼 120 · 가장 깊이 1층'. 첫 생(지난 생 0)이면 빈 문자열(첫 화면은 깨끗하게) */
export function metaMemo(m: TitleMetaInfo | null, soulsName = '영혼'): string {
  if (!m || !(m.lives > 0)) return '';
  const parts = [`지난 생 ${Math.floor(m.lives)}`];
  if (m.souls > 0) parts.push(`${soulsName} ${Math.floor(m.souls)}`);
  if (m.bestFloor > 0) parts.push(`가장 깊이 ${Math.floor(m.bestFloor)}층`);
  return parts.join(' · ');
}

/** 숫자 키·스페이스·엔터 외에도 '아무 키' 로 치는가 (조합 보조 키만 누른 것은 빼고) */
export function isWakeKey(key: string): boolean {
  return !['Shift', 'Control', 'Alt', 'Meta', 'CapsLock', 'Tab', 'Fn'].includes(key);
}

/**
 * 62 점검 ⑦: 영혼(메타) 메뉴를 건너뛸까 — 시작 줄('enter')말고 고를 수 있는 줄이 하나도 없으면 true
 * (새 플레이어의 첫 화면이 '(불가)'만 가득한 메뉴로 보이지 않게 — MenuScene 이 그리지 않고 바로 'enter').
 */
export function metaAutoEnter(m: {
  id: string;
  lines: { key: string; enabled: boolean; memory?: unknown }[];
}): boolean {
  // 62 루프 2 UI E: 계약 C 기억 장('meta' 줄마다 `line.memory`)은 고를 것이 없어도 보여 준다 (지금 무엇이 흐릿한지 보는 장)
  if (m.id !== 'meta' || m.lines.some((l) => Boolean(l.memory))) return false;
  return m.lines.every((l) => !l.enabled || l.key === 'enter');
}
