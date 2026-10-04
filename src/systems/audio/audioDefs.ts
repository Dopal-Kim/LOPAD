/**
 * 오디오 매니페스트 정의와 순수 규칙 (음향↔시스템 계약 초안 `assets/audio/manifest.json`, 결정 로그 I).
 * Phaser 의존 없음 — 로드·재생은 systems/audio.ts, 이벤트 → 효과음 표는 systems/audioMap.ts.
 */
import { ASSETS, AUDIO } from '../core/Constants';

export type AudioKind = 'sfx' | 'bgm';

export interface AudioEntry {
  id: string;
  kind: AudioKind;
  category: string;
  /** 저장소 루트 기준 경로 (`assets/audio/sfx/x.wav`) */
  file: string;
  durationMs: number;
  loop: boolean;
  /** 버스 기준 상대 음량 dB */
  gainDb: number;
  /** 음향 파트의 트리거 제안 (코드는 audioMap 을 쓴다) */
  trigger?: { event: string; when: string[] };
  floors?: number[];
}

export interface AudioMixing {
  masterDb: number;
  sfxBusDb: number;
  bgmBusDb: number;
  bgmCrossfadeMs: number;
  bgmBossDuckDb: number;
}

export interface AudioManifest {
  version: number;
  mixing?: Partial<AudioMixing>;
  bgmByFloor?: Record<string, string>;
  bgmByState?: Record<string, string>;
  entries: AudioEntry[];
}

/** 매니페스트가 비어 있거나 깨졌을 때의 빈 값 */
export const EMPTY_AUDIO_MANIFEST: AudioManifest = { version: 0, entries: [] };

export function isAudioManifest(v: unknown): v is AudioManifest {
  return Boolean(v && typeof v === 'object' && Array.isArray((v as AudioManifest).entries));
}

export function mixingOf(m: AudioManifest): AudioMixing {
  return { ...AUDIO.DEFAULT_MIXING, ...(m.mixing ?? {}) };
}

/** dB → 선형 게인 */
export function dbToGain(db: number): number {
  return Math.pow(10, db / 20);
}

/** `assets/audio/sfx/x.wav` → 매니페스트·URL 공통 상대 경로 `audio/sfx/x.wav` */
export function audioFileRel(entry: Pick<AudioEntry, 'file'>): string {
  const f = entry.file.replace(/\\/g, '/');
  return f.startsWith(ASSETS.AUDIO_FILE_PREFIX) ? f.slice(ASSETS.AUDIO_FILE_PREFIX.length) : f;
}

/** 음향 매니페스트 자체의 상대 경로 (`audio/manifest.json`) */
export function audioManifestRel(): string {
  return `${ASSETS.AUDIO_DIR}/${ASSETS.AUDIO_MANIFEST}`;
}

/** 효과음 음량 = master + sfx 버스 + entry gain */
export function sfxGain(mix: AudioMixing, entry: Pick<AudioEntry, 'gainDb'>): number {
  return dbToGain(mix.masterDb + mix.sfxBusDb + entry.gainDb);
}

/**
 * BGM 음량 = master + bgm 버스 + entry gain (+ 보스전 덕킹 + 일시정지 덕킹).
 * 보스전 덕킹은 상태 BGM(boss/emperor)에 적용된다.
 */
export function bgmGain(
  mix: AudioMixing,
  entry: Pick<AudioEntry, 'gainDb'>,
  opts: { bossDuck?: boolean; pauseDuck?: boolean } = {},
): number {
  let db = mix.masterDb + mix.bgmBusDb + entry.gainDb;
  if (opts.bossDuck) db += mix.bgmBossDuckDb;
  if (opts.pauseDuck) db += AUDIO.PAUSE_DUCK_DB;
  return dbToGain(db);
}

/** 현재 BGM 결정: 상태(title/boss/emperor…)가 있으면 상태 곡, 없으면 층 곡. 없으면 null */
export function resolveBgm(m: AudioManifest, floor: number | null, state: string | null): string | null {
  if (state) {
    const id = m.bgmByState?.[state];
    if (id) return id;
  }
  if (floor !== null) {
    const id = m.bgmByFloor?.[String(floor)];
    if (id) return id;
  }
  return null;
}

/** 보스 id 에 해당하는 상태 곡이 매니페스트에 있으면 그 상태(예: emperor), 아니면 'boss' */
export function bossBgmState(m: AudioManifest, bossId: string): string {
  return m.bgmByState?.[bossId] ? bossId : 'boss';
}

/** 상태 BGM 중 보스전 덕킹 대상인지 (title 제외) */
export function isBossState(state: string | null): boolean {
  return state !== null && state !== 'title';
}

/** swing·hit 류: 재생마다 ±PITCH_VARIANCE 랜덤 피치 */
export function hasPitchVariance(id: string): boolean {
  return AUDIO.PITCH_VARIANCE_PREFIXES.some((p) => id.startsWith(p));
}

/** 랜덤 재생 속도 (1 ± variance). rand 는 0..1 */
export function pitchRate(rand: number, variance = AUDIO.PITCH_VARIANCE): number {
  return 1 + (rand * 2 - 1) * variance;
}

/** 같은 효과음의 짧은 중복 요청을 1회로 묶는다 */
export class SfxDedupe {
  private readonly last = new Map<string, number>();

  constructor(private readonly windowMs: number = AUDIO.DEDUPE_MS) {}

  /** 재생해도 되면 true (그리고 시각을 기록) */
  allow(id: string, now: number): boolean {
    const prev = this.last.get(id);
    if (prev !== undefined && now - prev < this.windowMs) return false;
    this.last.set(id, now);
    return true;
  }

  clear(): void {
    this.last.clear();
  }
}

/** 매니페스트 entry 를 id 로 색인 */
export function indexEntries(m: AudioManifest): Map<string, AudioEntry> {
  const out = new Map<string, AudioEntry>();
  for (const e of m.entries) if (e && typeof e.id === 'string') out.set(e.id, e);
  return out;
}
