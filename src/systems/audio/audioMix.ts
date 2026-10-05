/**
 * 61라운드 계약 sound §9 믹싱 규칙 (순수 — Phaser 의존 없음, audio.ts 가 쓴다).
 * - BGM: `bgmByFloorState`(층 여정·전투·보스 국면) 고르기
 * - 효과음: 변주(직전과 다른 것) · 재생 속도 흔들기 · 동시 재생 상한(우선순위 낮고 오래된 것부터 끊기, 루프 제외) · 덕킹 봉투
 */
import { AUDIO } from '../../core/Constants';
import type { AudioDuckRule, AudioEntry, AudioManifest, AudioMixing } from './audioDefs';
import { resolveBgm } from './audioDefs';

/** 층 안의 장면: 여정(벽 밖·탄생지·버려진 길·국경 초소·휴식) · 전투(잔 거리 — 전투·상점·이벤트) */
export type FloorScene = 'journey' | 'combat';

/** 노드 종류 → 장면 (route.json kinds — 여정 3종 + 휴식은 journey) */
export function floorSceneOfNode(kind: string): FloorScene {
  return kind === 'birth' || kind === 'road' || kind === 'post' || kind === 'rest' ? 'journey' : 'combat';
}

/**
 * 61라운드 BGM 고르기: 보스 상태이고 층에 국면 곡이 있으면 국면 곡(1부터) → 상태 곡(title·boss·emperor) → 층 장면 곡 → 층 곡(bgmByFloor).
 * 층 장면 곡이 없으면 기존 resolveBgm 과 같다
 */
export function resolveBgmFor(
  m: AudioManifest,
  floor: number | null,
  state: string | null,
  scene: FloorScene,
  bossPhase: number,
): string | null {
  const fs = floor !== null ? m.bgmByFloorState?.[String(floor)] : undefined;
  if (fs && state !== null && state !== 'title') {
    const phases = fs.bossPhases ?? [];
    const id = phases.length > 0 ? phases[Math.min(phases.length, Math.max(1, bossPhase)) - 1] : fs.boss;
    if (id) return id;
  }
  if (state) return resolveBgm(m, floor, state);
  if (fs) {
    const id = scene === 'journey' ? (fs.journey ?? fs.combat) : fs.combat;
    if (id) return id;
  }
  return resolveBgm(m, floor, null);
}

/** 층 장면 곡 전부 (지연 로드 대상) */
export function floorStateBgmIds(m: AudioManifest, floor: number): string[] {
  const fs = m.bgmByFloorState?.[String(floor)];
  if (!fs) return [];
  return [...new Set([fs.journey, fs.combat, fs.boss, ...(fs.bossPhases ?? [])].filter((x): x is string => !!x))];
}

/** 부팅 때 읽지 않는 BGM (`use.floor` 가 있는 층 전용 곡 — 그 층에 들어갈 때 지연 로드) */
export function isLazyBgm(e: Pick<AudioEntry, 'kind' | 'use'>): boolean {
  return e.kind === 'bgm' && typeof e.use?.floor === 'number';
}

// --- 효과음 ---

/** 변주 그룹 = 원본 id */
export function groupOf(e: Pick<AudioEntry, 'id' | 'variantOf'>): string {
  return e.variantOf ?? e.id;
}

/** 원본의 변주 후보 중 직전과 다른 것 (rand 0..1). 후보가 하나면 그것 */
export function pickVariant(candidates: readonly string[], last: string | undefined, rand: number): string | null {
  if (candidates.length === 0) return null;
  const pool = candidates.length > 1 && last !== undefined ? candidates.filter((c) => c !== last) : candidates;
  const list = pool.length > 0 ? pool : candidates;
  return list[Math.min(list.length - 1, Math.floor(rand * list.length))];
}

/** 재생 속도 흔들기 대상: 우선순위 1~3 의 짧은 효과음 (루프·UI·BGM 제외) */
export function jitterApplies(e: Pick<AudioEntry, 'kind' | 'loop' | 'priority'>): boolean {
  const p = e.priority ?? 2;
  return e.kind === 'sfx' && !e.loop && p >= 1 && p <= 3;
}

export function jitterRate(rand: number, jitter: number): number {
  return 1 + (rand * 2 - 1) * jitter;
}

export function rateJitterOf(mix: AudioMixing): number {
  return mix.variation?.rateJitter ?? AUDIO.PITCH_VARIANCE;
}

export function dedupeMsOf(mix: AudioMixing): number {
  return mix.dedupeMs ?? AUDIO.DEDUPE_MS;
}

export interface VoiceInfo {
  group: string;
  priority: number;
  ui: boolean;
  /** 시작 시각 (오래된 것 먼저 끊기) */
  at: number;
}

export interface VoiceLimits {
  maxSfx: number;
  maxUi: number;
  perGroupMax: number;
  perGroupOverrides: Record<string, number>;
}

export function voiceLimitsOf(mix: AudioMixing): VoiceLimits {
  const v = mix.voices ?? {};
  return {
    maxSfx: v.maxSfx ?? AUDIO.MAX_SFX_VOICES,
    maxUi: v.maxUi ?? 2,
    perGroupMax: v.perGroupMax ?? 3,
    perGroupOverrides: v.perGroupOverrides ?? {},
  };
}

/**
 * 새 소리를 넣을 수 있는가 + 끊을 목소리(active 의 인덱스). 루프는 active 에 넣지 않는다(빼앗지 않음).
 * 1) 같은 그룹 상한 → 그 그룹의 가장 오래된 것 2) UI 는 UI 상한만 3) 전체 상한 → 우선순위가 새 소리 이하인 것 중 가장 낮고 오래된 것,
 * 그런 것이 없으면 새 소리를 버린다
 */
export function allocateVoice(
  active: readonly VoiceInfo[],
  incoming: Omit<VoiceInfo, 'at'>,
  lim: VoiceLimits,
): { ok: boolean; steal: number[] } {
  const steal = new Set<number>();
  const alive = () => active.map((v, i) => ({ v, i })).filter((x) => !steal.has(x.i));
  const oldest = (xs: { v: VoiceInfo; i: number }[]) => xs.sort((a, b) => a.v.at - b.v.at)[0];
  const groupMax = lim.perGroupOverrides[incoming.group] ?? lim.perGroupMax;
  const same = alive().filter((x) => x.v.group === incoming.group);
  if (same.length >= groupMax) {
    const o = oldest(same);
    if (o) steal.add(o.i);
  }
  if (incoming.ui) {
    const uis = alive().filter((x) => x.v.ui);
    if (uis.length >= lim.maxUi) {
      const o = oldest(uis);
      if (o) steal.add(o.i);
    }
    return { ok: true, steal: [...steal] };
  }
  const sfx = alive().filter((x) => !x.v.ui);
  if (sfx.length >= lim.maxSfx) {
    const cands = sfx.filter((x) => x.v.priority <= incoming.priority);
    if (cands.length === 0) return { ok: false, steal: [] };
    const minP = Math.min(...cands.map((x) => x.v.priority));
    const o = oldest(cands.filter((x) => x.v.priority === minP));
    steal.add(o.i);
  }
  return { ok: true, steal: [...steal] };
}

// --- 덕킹 ---

export type DuckTrigger = { kind: 'priority'; level: number } | { kind: 'group'; group: string };
export type DuckTarget = { bus: 'bgm' } | { bus: 'sfx'; maxPriority: number };

export interface DuckRule {
  trigger: DuckTrigger;
  target: DuckTarget;
  db: number;
  attackMs: number;
  releaseMs: number;
  /** null = 그 소리 길이 동안 */
  holdMs: number | null;
}

/** 매니페스트 문장형 규칙 해석 ('priority 4 재생 시작' · 'sfx/hit_player 그룹 재생' / 'bgm' · 'sfx priority ≤ 2' / '150 ms') */
export function parseDucking(rules: readonly AudioDuckRule[] | undefined): DuckRule[] {
  const out: DuckRule[] = [];
  for (const r of rules ?? []) {
    if (!r || typeof r.db !== 'number') continue;
    const pm = /priority\s*(\d+)/.exec(r.when);
    const gm = /(sfx\/[\w/]+)/.exec(r.when);
    const trigger: DuckTrigger | null = gm
      ? { kind: 'group', group: gm[1] }
      : pm
        ? { kind: 'priority', level: Number(pm[1]) }
        : null;
    const tm = /priority\s*[≤<]=?\s*(\d+)/.exec(r.target);
    const target: DuckTarget | null =
      r.target.trim() === 'bgm' ? { bus: 'bgm' } : tm ? { bus: 'sfx', maxPriority: Number(tm[1]) } : null;
    if (!trigger || !target) continue;
    const hm = /(\d+)\s*ms/.exec(r.hold ?? '');
    out.push({
      trigger,
      target,
      db: r.db,
      attackMs: r.attackMs ?? 0,
      releaseMs: r.releaseMs ?? 0,
      holdMs: hm ? Number(hm[1]) : null,
    });
  }
  return out;
}

/** 이 소리가 켜는 덕킹 규칙 */
export function ducksFor(rules: readonly DuckRule[], e: { group: string; priority: number }): DuckRule[] {
  return rules.filter((r) =>
    r.trigger.kind === 'group' ? r.trigger.group === e.group : e.priority >= r.trigger.level,
  );
}

export interface ActiveDuck {
  rule: DuckRule;
  start: number;
  holdEnd: number;
}

export function startDuck(rule: DuckRule, now: number, soundMs: number): ActiveDuck {
  return { rule, start: now, holdEnd: now + rule.attackMs + (rule.holdMs ?? soundMs) };
}

/** 봉투 0..1 (공격 → 유지 → 해제) */
export function duckEnvelope(d: ActiveDuck, now: number): number {
  const r = d.rule;
  if (now < d.start) return 0;
  if (r.attackMs > 0 && now < d.start + r.attackMs) return (now - d.start) / r.attackMs;
  if (now < d.holdEnd) return 1;
  if (r.releaseMs > 0 && now < d.holdEnd + r.releaseMs) return 1 - (now - d.holdEnd) / r.releaseMs;
  return 0;
}

export function duckFinished(d: ActiveDuck, now: number): boolean {
  return now >= d.holdEnd + d.rule.releaseMs;
}

/** 대상별 지금 감쇠 dB (가장 깊은 것 하나 — 합산하지 않음). sfx 는 그 우선순위에 닿는 규칙만 */
export function duckDbAt(
  active: readonly ActiveDuck[],
  now: number,
  target: { bus: 'bgm' } | { bus: 'sfx'; priority: number },
): number {
  let db = 0;
  for (const d of active) {
    const t = d.rule.target;
    if (t.bus !== target.bus) continue;
    if (t.bus === 'sfx' && target.bus === 'sfx' && target.priority > t.maxPriority) continue;
    db = Math.min(db, d.rule.db * duckEnvelope(d, now));
  }
  return db || 0;
}
