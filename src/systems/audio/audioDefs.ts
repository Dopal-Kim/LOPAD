/**
 * 오디오 매니페스트 정의와 순수 규칙 (음향↔시스템 계약 초안 `assets/audio/manifest.json`, 결정 로그 I).
 * Phaser 의존 없음 — 로드·재생은 systems/audio/audio.ts, 이벤트 → 효과음 표는 systems/audio/audioMap.ts.
 */
import { ASSETS, AUDIO } from '../../core/Constants';

export type AudioKind = 'sfx' | 'bgm';

export interface AudioEntry {
  id: string;
  kind: AudioKind;
  category: string;
  /** 저장소 루트 기준 1순위 경로 (57라운드: `assets/audio/sfx/x.ogg`) */
  file: string;
  /** 57라운드 Q38 (계약 sound-assets): 같은 소리의 형식별 경로, 선호 순서(ogg → m4a) — 재생 가능한 첫 항목을 쓴다 */
  files?: string[];
  /** 원본 표본 수·표본율 (루프 이음매 계산) */
  samples?: number;
  sampleRate?: number;
  /** 루프 구간 [loopStartSample, loopEndSample) — 디코딩 버퍼가 끝 패딩으로 더 길면 loopEnd 로 자른다 */
  loopStartSample?: number;
  loopEndSample?: number;
  durationMs: number;
  loop: boolean;
  /** 버스 기준 상대 음량 dB */
  gainDb: number;
  /** 음향 파트의 트리거 제안 (코드는 audioMap 을 쓴다) */
  trigger?: { event: string; when: string[] } | null;
  floors?: number[];
  /** 61라운드 계약 sound §9: 효과음 우선순위 0(UI)~4(보스 예고) */
  priority?: number;
  /** §9: 원본 항목의 변주 목록(원본 포함) · 변주 항목의 원본 id */
  variants?: string[];
  variantOf?: string;
  /** §9: BGM 쓰임 (층·상태·국면) */
  use?: { floor?: number; state?: string; phase?: number };
  channels?: number;
}

export interface AudioMixing {
  masterDb: number;
  sfxBusDb: number;
  bgmBusDb: number;
  bgmCrossfadeMs: number;
  bgmBossDuckDb: number;
  /** 61라운드 §9 (없으면 audioMix 기본값) */
  dedupeMs?: number;
  voices?: AudioVoiceLimits;
  ducking?: AudioDuckRule[];
  variation?: { rateJitter?: number };
  masterLimiter?: { thresholdDb: number; kneeDb: number; ratio: number; attackMs: number; releaseMs: number };
  bgmPhaseCrossfadeMs?: number;
  bgmPhaseSyncPosition?: boolean;
}

/** §9 동시 재생 상한 (그룹 = 원본 id — 변주 포함) */
export interface AudioVoiceLimits {
  maxSfx?: number;
  maxUi?: number;
  perGroupMax?: number;
  perGroupOverrides?: Record<string, number>;
  /** 61 단계 5 (sound §11): 개성 발동 특색 층 전체 동시 상한 — ids + 접두어 `sfx/trait_`(trait_manifest 제외) */
  layerMax?: { ids?: string[]; max?: number };
}

/** §9 덕킹 규칙 (매니페스트 문장형 when/target 을 audioMix.parseDucking 이 해석) */
export interface AudioDuckRule {
  when: string;
  target: string;
  db: number;
  attackMs?: number;
  releaseMs?: number;
  hold?: string;
}

/** §9 층별 상태 곡: 여정 · 전투 · 보스(국면별) */
export interface FloorStateBgm {
  journey?: string;
  combat?: string;
  boss?: string;
  bossPhases?: string[];
}

export interface AudioManifest {
  version: number;
  mixing?: Partial<AudioMixing>;
  bgmByFloor?: Record<string, string>;
  bgmByState?: Record<string, string>;
  /** 61라운드 §9 */
  bgmByFloorState?: Record<string, FloorStateBgm>;
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

/**
 * 57라운드 Q38: 로드 후보 경로 (`files` 선호 순서, 없으면 `file` 하나) — 매니페스트·URL 공통 상대 경로.
 * Phaser `load.audio(id, urls)` 가 브라우저가 재생할 수 있는 첫 형식을 고른다
 */
export function audioFileRels(entry: Pick<AudioEntry, 'file' | 'files'>): string[] {
  const list = Array.isArray(entry.files) && entry.files.length > 0 ? entry.files : [entry.file];
  return [...new Set(list.filter((f) => typeof f === 'string' && f !== '').map((file) => audioFileRel({ file })))];
}

/**
 * 루프 끝(디코딩 버퍼의 표본 수 단위). 루프 항목이고 `loopEndSample`·`sampleRate` 가 있을 때만 — 디코더(AAC 등)가 끝 패딩을 남겨
 * 버퍼가 이보다 길면 이 길이로 잘라 이음매를 맞춘다. 버퍼 표본율이 원본과 다르면(컨텍스트 재표본화) 비례 환산. 자를 필요 없으면 null
 */
export function loopEndFrames(
  entry: Pick<AudioEntry, 'loop' | 'loopEndSample' | 'sampleRate'>,
  buffer: { length: number; sampleRate: number },
): number | null {
  const end = entry.loopEndSample;
  const rate = entry.sampleRate;
  if (!entry.loop || typeof end !== 'number' || !(end > 0) || typeof rate !== 'number' || !(rate > 0)) return null;
  const frames = Math.round((end / rate) * buffer.sampleRate);
  return frames > 0 && buffer.length > frames ? frames : null;
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
