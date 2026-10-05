/**
 * 오디오 시스템 (음향↔시스템 계약 초안 `assets/audio/manifest.json`, 결정 로그 I·K).
 * - Preloader 가 매니페스트·소리(57라운드: OGG → M4A 순 `files`)를 로드한 뒤 `register()` 로 넘긴다 (루프는 loopEnd 로 자름).
 * - 효과음은 EventBus 이벤트를 `audioMap.ts` 표로 매핑해 재생한다 (게임 코드는 소리를 직접 호출하지 않는다).
 * - BGM 은 층(`bgmByFloor`)·상태(`bgmByState`: title / boss / emperor)로 정하고 크로스페이드한다.
 * - 버스: SFX 0 dB, BGM -8 dB, 보스전 BGM -3 dB, entry.gainDb 가산. 같은 효과음 20ms 중복 1회, swing·hit 류 ±4% 피치.
 * - 음소거는 `setMute()` (localStorage `lopad.mute`) — 49라운드 계약 §11.3: Esc 메뉴 설정 → uiCommands.setMuted.
 * - 61라운드 계약 §15 음량: `setVolumes({master, bgm, sfx})` — master = 사운드 매니저 전체 음량, bgm·sfx = 버스 배율(0~1).
 *   즉시 반영(BGM 은 페이드 없이 목표 음량으로, 돌고 있는 루프 효과음도). 저장은 systems/settings(메타 세이브).
 *   M 키 토글은 없앴다 (M = UI 지도). 디버그 요약은 `summary()`.
 * - 61라운드 계약 sound §9: 층 장면 BGM(`bgmByFloorState` — 여정·전투·보스 국면, 국면은 재생 위치 유지 교차 페이드), 층 전용 곡 지연 로드
 *   (`audioLazy`), 효과음 변주·속도 흔들기·동시 재생 상한·덕킹(`audioVoices`/`audioMix`), 마스터 리미터.
 * 게임 수명 동안 하나(main.ts 에서 attach). 씬 재시작과 무관하게 BGM 이 이어진다.
 */
import Phaser from 'phaser';
import { AUDIO } from '../../core/Constants';
import { EventBus, Events, type RunEndedPayload } from '../../core/EventBus';
import { browserStorage } from '../save';
import {
  EMPTY_AUDIO_MANIFEST,
  bgmGain,
  bossBgmState,
  indexEntries,
  isBossState,
  loopEndFrames,
  mixingOf,
  sfxGain,
  SfxDedupe,
  type AudioEntry,
  type AudioManifest,
  type AudioMixing,
} from './audioDefs';
import { AUDIO_TRIGGERS, type AudioTrigger } from './audioMap';
import {
  dedupeMsOf,
  floorSceneOfNode,
  floorStateBgmIds,
  groupOf,
  jitterApplies,
  jitterRate,
  pickVariant,
  rateJitterOf,
  resolveBgmFor,
  type FloorScene,
} from './audioMix';
import { VoiceBank } from './audioVoices';
import { LazyAudio } from './audioLazy';
import type { BossPhasePayload, NodeEnteredPayload } from '../../core/EventBus';

/** 실제 구현체(WebAudio / HTML5 / NoAudio)는 모두 setVolume 을 가진다 */
type Snd = Phaser.Sound.BaseSound & { setVolume(value: number): unknown };
type Fade = { from: number; to: number; startAt: number; ms: number };
type BgmTrack = { id: string; sound: Snd; volume: number; fade: Fade | null; dying: boolean };

export interface AudioSummary {
  manager: string;
  locked: boolean;
  contextState: string | null;
  entries: number;
  loaded: number;
  missing: string[];
  bgm: string | null;
  bgmVolume: number;
  bgmFading: number;
  floor: number | null;
  state: string | null;
  /** 61라운드: 보스 처치 뒤 정적 중 */
  outroSilence: boolean;
  paused: boolean;
  loops: string[];
  /** 루프 끝(loopEndSample)에 맞춰 버퍼를 자른 소리 */
  loopTrimmed: string[];
  voices: number;
  recent: { id: string; at: number; rate: number; delayMs: number }[];
  mute: boolean;
  /** 61라운드 §15 음량 배율 */
  volumes: { master: number; bgm: number; sfx: number };
  /** 61라운드 §9: 층 장면 · 보스 국면 · 지연 로드 중 · 덕킹 수 · BGM 덕킹 게인 */
  scene: string;
  bossPhase: number;
  lazyLoading: string[];
  ducks: number;
  bgmDuck: number;
  limiter: boolean;
}

export class AudioSystem {
  private game: Phaser.Game | null = null;
  private manifest: AudioManifest = EMPTY_AUDIO_MANIFEST;
  private entries = new Map<string, AudioEntry>();
  private mix: AudioMixing = mixingOf(EMPTY_AUDIO_MANIFEST);
  private readonly loaded = new Set<string>();
  /** 루프 끝에 맞춰 자른 버퍼 (디버그) */
  private readonly trimmed = new Set<string>();
  private readonly missing = new Set<string>();
  private dedupe = new SfxDedupe();
  /** 61라운드 §9 목소리 상한·덕킹 */
  private readonly bank = new VoiceBank((snd) => this.kill(snd));
  /** 변주 그룹별 직전 재생 id */
  private readonly lastVariant = new Map<string, string>();
  private floorScene: FloorScene = 'combat';
  private bossPhase = 1;
  private readonly lazy = new LazyAudio();
  private limiter: DynamicsCompressorNode | null = null;
  private readonly loops = new Map<string, Snd>();
  /** 56라운드: 루프별 재생 속도 (디버그·검증) */
  private readonly loopRates = new Map<string, number>();
  /** 페이드 중인 루프 — to 0 = 페이드 아웃 뒤 정지, 그 밖 = 페이드 인 (55라운드 차지 루프) */
  private fading: { snd: Snd; from: number; to: number; at: number; ms: number }[] = [];
  /** 55라운드 Q14 ②: 지연 효과음 예약기 (게임 씬 시계 — 히트스톱 동안 멈춤). 없으면 WebAudio 지연 */
  private delayScheduler: ((ms: number, fire: () => void) => unknown) | null = null;
  private bgm: BgmTrack | null = null;
  private dying: BgmTrack[] = [];
  private floor: number | null = null;
  private state: string | null = null;
  /** 61라운드: 보스 처치 뒤 정적 (처치 연출·보상 메뉴 동안 — EXIT_OPENED·노드·층 진입에 풀림) */
  private outroSilence = false;
  private paused = false;
  private recent: AudioSummary['recent'] = [];
  private muted = false;
  /** 61라운드 §15: 음량 배율 (master = 매니저 전체, bgm·sfx = 버스) */
  private vol = { master: 1, bgm: 1, sfx: 1 };
  /** 루프 효과음의 버스 배율 전 음량 (음량 변경 때 다시 곱한다) */
  private readonly loopBase = new Map<string, number>();
  private readonly storage = browserStorage();
  private onGesture?: () => void;
  private readonly triggerHandlers: { event: string; fn: (p: unknown) => void }[] = [];

  /** 게임 생성 직후 1회. EventBus 구독·음소거 복원·크로스페이드 스텝 등록 */
  attach(game: Phaser.Game): void {
    if (this.game) return;
    this.game = game;
    this.muted = this.storage?.getItem(AUDIO.MUTE_STORAGE_KEY) === '1';
    this.applyMute();
    this.applyMasterVolume();
    game.events.on(Phaser.Core.Events.STEP, this.step, this);
    for (const tr of AUDIO_TRIGGERS) {
      const fn = (p: unknown) => this.onTrigger(tr, p);
      this.triggerHandlers.push({ event: tr.event, fn });
      EventBus.on(tr.event, fn);
    }
    EventBus.on(Events.STAGE_STARTED, this.onStageStarted, this);
    EventBus.on(Events.BOSS_STARTED, this.onBossStarted, this);
    EventBus.on(Events.BOSS_PHASE, this.onBossPhase, this);
    EventBus.on(Events.NODE_ENTERED, this.onNodeEntered, this);
    EventBus.on(Events.BOSS_DIED, this.onBossDied, this);
    EventBus.on(Events.EXIT_OPENED, this.endOutroSilence, this);
    EventBus.on(Events.PLAYER_DIED, this.onRunEnding, this);
    EventBus.on(Events.ENDING_CHOSEN, this.onRunEnding, this);
    EventBus.on(Events.RUN_ENDED, this.onRunEnded, this);
    if (typeof document !== 'undefined') {
      // 첫 사용자 입력에서 컨텍스트 재개 (Phaser 의 unlock 과 겹쳐도 무해)
      this.onGesture = () => this.resumeContext();
      document.addEventListener('pointerdown', this.onGesture, { passive: true });
      document.addEventListener('keydown', this.onGesture);
    }
    if (typeof location !== 'undefined' && new URLSearchParams(location.search).has('debug')) {
      (window as unknown as { __lopadAudio: () => AudioSummary }).__lopadAudio = () => this.summary();
    }
  }

  /** Preloader: 매니페스트와 실제로 캐시에 들어온 키 */
  register(manifest: AudioManifest, loadedKeys: Iterable<string>): void {
    this.manifest = manifest;
    this.entries = indexEntries(manifest);
    this.mix = mixingOf(manifest);
    this.loaded.clear();
    this.trimmed.clear();
    for (const k of loadedKeys) if (this.entries.has(k)) this.loaded.add(k);
    for (const k of this.loaded) this.applyLoopEnd(this.entries.get(k)!);
    this.dedupe = new SfxDedupe(dedupeMsOf(this.mix));
    this.bank.configure(this.mix);
    this.installLimiter();
    this.refreshBgm();
  }

  /**
   * 61라운드 §9: 층 전용 BGM 지연 로드 후보 (Preloader 가 부팅 때 읽지 않은 항목 → 형식별 URL 후보). WebAudio 일 때만 —
   * 그 밖이면 Preloader 가 부팅 때 읽는다
   */
  registerLazy(urls: ReadonlyMap<string, readonly string[]>): void {
    this.lazy.register(urls);
  }

  /** 층 장면 곡을 미리 (boss = 국면 곡까지) */
  private prefetchFloor(floor: number, withBoss: boolean): void {
    const sm = this.game?.sound;
    if (!(sm instanceof Phaser.Sound.WebAudioSoundManager)) return;
    const fs = this.manifest.bgmByFloorState?.[String(floor)];
    const ids = withBoss
      ? floorStateBgmIds(this.manifest, floor)
      : [fs?.journey, fs?.combat].filter((x): x is string => typeof x === 'string');
    for (const id of ids) {
      if (this.loaded.has(id)) continue;
      void this.lazy.load(id, sm, this.game!).then((ok) => {
        if (!ok) {
          this.missing.add(id);
          return;
        }
        this.loaded.add(id);
        this.missing.delete(id);
        const e = this.entries.get(id);
        if (e) this.applyLoopEnd(e);
        this.refreshBgm();
      });
    }
  }

  /** §9 masterLimiter: 마스터 음량 노드 뒤에 압축기 하나 (WebAudio 만, 한 번) */
  private installLimiter(): void {
    const L = this.mix.masterLimiter;
    const sm = this.game?.sound;
    if (!L || !(sm instanceof Phaser.Sound.WebAudioSoundManager)) return;
    const ctx = sm.context;
    if (!this.limiter) {
      const node = sm as unknown as { masterVolumeNode?: AudioNode };
      if (!node.masterVolumeNode || typeof ctx.createDynamicsCompressor !== 'function') return;
      this.limiter = ctx.createDynamicsCompressor();
      node.masterVolumeNode.disconnect();
      node.masterVolumeNode.connect(this.limiter);
      this.limiter.connect(ctx.destination);
    }
    const c = this.limiter;
    c.threshold.value = L.thresholdDb;
    c.knee.value = L.kneeDb;
    c.ratio.value = L.ratio;
    c.attack.value = L.attackMs / 1000;
    c.release.value = L.releaseMs / 1000;
  }

  /**
   * 57라운드 Q38 루프 이음매: 디코딩 버퍼가 `loopEndSample / sampleRate` 보다 길면(M4A 끝 패딩) 그 길이로 자른 버퍼로 바꾼다
   * — Phaser WebAudio 루프는 버퍼 끝에서 다음 회차를 잇기 때문에 이것이 곧 loopEnd 다. WebAudio 가 아니면 그대로
   */
  private applyLoopEnd(entry: AudioEntry): void {
    const sm = this.game?.sound;
    if (!(sm instanceof Phaser.Sound.WebAudioSoundManager)) return;
    const buf = this.game!.cache.audio.get(entry.id) as unknown;
    if (typeof AudioBuffer === 'undefined' || !(buf instanceof AudioBuffer)) return;
    const frames = loopEndFrames(entry, buf);
    if (frames === null) return;
    const cut = sm.context.createBuffer(buf.numberOfChannels, frames, buf.sampleRate);
    for (let c = 0; c < buf.numberOfChannels; c++) cut.copyToChannel(buf.getChannelData(c).subarray(0, frames), c);
    this.game!.cache.audio.add(entry.id, cut);
    this.trimmed.add(entry.id);
  }

  get isMuted(): boolean {
    return this.muted;
  }

  toggleMute(): boolean {
    this.setMute(!this.muted);
    return this.muted;
  }

  setMute(on: boolean): void {
    this.muted = on;
    this.storage?.setItem(AUDIO.MUTE_STORAGE_KEY, on ? '1' : '0');
    this.applyMute();
  }

  /** 61라운드 §15 음량 (0~1). 게임 시작 전에 불러도 되고(attach 때 적용), 바뀌면 바로 반영 */
  setVolumes(v: { master: number; bgm: number; sfx: number }): void {
    const c = (x: number) => (Number.isFinite(x) ? Math.min(1, Math.max(0, x)) : 1);
    this.vol = { master: c(v.master), bgm: c(v.bgm), sfx: c(v.sfx) };
    this.applyMasterVolume();
    this.bank.setSfxMult(this.vol.sfx, this.now());
    for (const [id, snd] of this.loops) {
      if (this.fading.some((f) => f.snd === snd)) continue;
      snd.setVolume((this.loopBase.get(id) ?? 1) * this.vol.sfx);
    }
    // BGM: 페이드 중이 아니면 새 목표로 바로 (슬라이더를 끄는 동안 늦지 않게)
    const t = this.bgm;
    if (t && !t.dying) {
      const target = this.targetVolume(t.id);
      if (t.fade) t.fade.to = target;
      else {
        t.volume = target;
        t.sound.setVolume(target * this.bank.bgmGain);
      }
    }
  }

  get volumes(): { master: number; bgm: number; sfx: number } {
    return { ...this.vol };
  }

  // --- 효과음 ---

  /** 게임 씬이 지연 효과음을 자기 시계로 예약하게 한다 (씬 종료 때 null) */
  setDelayScheduler(fn: ((ms: number, fire: () => void) => unknown) | null): void {
    this.delayScheduler = fn;
  }

  /** 효과음 1회. 매니페스트에 없거나 로드되지 않았으면 무시(missing 기록) */
  playSfx(id: string, opts: { delayMs?: number; rate?: number } = {}): boolean {
    const sched = this.delayScheduler;
    if (sched && (opts.delayMs ?? 0) > 0) {
      sched(opts.delayMs!, () => this.playSfx(id, { rate: opts.rate }));
      return true;
    }
    const sm = this.game?.sound;
    const req = this.entries.get(id);
    if (!sm || !req) {
      this.missing.add(id);
      return false;
    }
    // 61라운드 §9 변주: 원본 트리거 → variants 중 로드된 것, 직전과 다른 것
    const group = groupOf(req);
    const loadedVariants = (req.variants ?? []).filter((v) => this.loaded.has(v));
    const pick =
      loadedVariants.length > 0 ? (pickVariant(loadedVariants, this.lastVariant.get(group), Math.random()) ?? id) : id;
    const entry = this.entries.get(pick) ?? req;
    if (!this.loaded.has(pick)) {
      this.missing.add(pick);
      return false;
    }
    const now = this.now();
    if (!this.dedupe.allow(group, now)) return false;
    const priority = entry.priority ?? req.priority ?? (entry.category === 'ui' ? 0 : 2);
    const ui = priority === 0 || entry.category === 'ui';
    if (!this.bank.admit({ group, priority, ui })) return false;
    const jitter = jitterApplies({ ...entry, priority }) ? jitterRate(Math.random(), rateJitterOf(this.mix)) : 1;
    const rate = jitter * (opts.rate ?? 1);
    const delayMs = Math.max(0, opts.delayMs ?? 0);
    const base = sfxGain(this.mix, entry);
    const snd = sm.add(pick, {
      volume: base * this.bank.gainFor(priority, now),
      rate,
      loop: false,
      delay: delayMs / 1000,
    }) as Snd;
    snd.once(Phaser.Sound.Events.COMPLETE, () => this.kill(snd));
    snd.play();
    this.lastVariant.set(group, pick);
    this.bank.add({ snd, id: pick, group, priority, ui, at: now, base }, entry.durationMs + delayMs, now);
    this.recent.push({ id: pick, at: Math.round(now), rate: Number(rate.toFixed(3)), delayMs });
    if (this.recent.length > AUDIO.RECENT_SFX) this.recent.shift();
    return true;
  }

  /** 루프 효과음 시작 (가드 유지). 이미 돌고 있으면 유지. fadeInMs 가 있으면 0 에서 그동안 올린다 (55라운드 차지 루프) */
  startLoop(id: string, fadeInMs = 0): void {
    const sm = this.game?.sound;
    const entry = this.entries.get(id);
    if (!sm || !entry || !this.loaded.has(id) || this.loops.has(id)) {
      if (!entry || !this.loaded.has(id)) this.missing.add(id);
      return;
    }
    const base = sfxGain(this.mix, entry);
    const volume = base * this.vol.sfx;
    const snd = sm.add(id, { volume: fadeInMs > 0 ? 0 : volume, loop: true }) as Snd;
    snd.play();
    this.loops.set(id, snd);
    this.loopBase.set(id, base);
    if (fadeInMs > 0) this.fading.push({ snd, from: 0, to: volume, at: this.now(), ms: fadeInMs });
  }

  /** 56라운드: 돌고 있는 루프의 재생 속도(음높이) — 차지 유지음 단계 1.0/1.03/1.06. 루프가 없으면 무시 */
  setLoopRate(id: string, rate: number): void {
    const snd = this.loops.get(id) as (Snd & { setRate?: (r: number) => unknown }) | undefined;
    if (snd && typeof snd.setRate === 'function' && rate > 0) snd.setRate(rate);
    this.loopRates.set(id, rate);
  }

  /** 디버그: 마지막으로 정한 루프 속도 */
  loopRateOf(id: string): number {
    return this.loopRates.get(id) ?? 1;
  }

  /** 루프 정지. fadeMs 가 있으면 그동안 볼륨을 줄인 뒤 (54라운드 보스 루프) */
  stopLoop(id: string, fadeMs = 0): void {
    const snd = this.loops.get(id);
    if (!snd) return;
    this.loops.delete(id);
    this.loopBase.delete(id);
    // 페이드 인 중이면 그 항목을 버리고 지금 볼륨에서 내린다
    this.fading = this.fading.filter((f) => f.snd !== snd);
    if (fadeMs > 0 && snd.isPlaying)
      this.fading.push({
        snd,
        from: (snd as unknown as { volume: number }).volume ?? 1,
        to: 0,
        at: this.now(),
        ms: fadeMs,
      });
    else this.kill(snd);
  }

  /** 해당 id 의 재생 중인 효과음(일회성·루프) 전부 정지 */
  stopSfx(id: string): void {
    this.stopLoop(id);
    this.bank.stopId(id);
    // 변주로 재생된 것도 (원본 id 로 멈추면 그 그룹 전부)
    for (const v of this.entries.get(id)?.variants ?? []) if (v !== id) this.bank.stopId(v);
  }

  stopAllLoops(): void {
    for (const id of [...this.loops.keys()]) this.stopLoop(id);
  }

  // --- BGM ---

  /** 층 진입: 상태 BGM 해제 후 층 곡 */
  setFloor(floor: number): void {
    this.floor = floor;
    this.state = null;
    this.refreshBgm();
  }

  /** 상태 BGM (title / boss / emperor …). null 이면 층 곡으로 복귀 */
  setState(state: string | null): void {
    this.state = state;
    this.refreshBgm();
  }

  /** 일시정지 덕킹 */
  setPaused(on: boolean): void {
    if (this.paused === on) return;
    this.paused = on;
    this.refreshBgm();
  }

  /** 런 종료: BGM 페이드아웃, 다음 층·타이틀이 정하기 전까지 무음 */
  fadeOutBgm(ms: number = AUDIO.RUN_END_FADE_MS): void {
    this.floor = null;
    this.state = null;
    this.retire(ms);
  }

  get currentBgm(): string | null {
    return this.bgm?.id ?? null;
  }

  summary(): AudioSummary {
    const sm = this.game?.sound;
    const ctx = sm && 'context' in sm ? (sm as Phaser.Sound.WebAudioSoundManager).context : null;
    const manager = !sm
      ? 'none'
      : ctx
        ? 'webaudio'
        : sm instanceof Phaser.Sound.HTML5AudioSoundManager
          ? 'html5'
          : 'noaudio';
    return {
      manager,
      locked: sm?.locked ?? false,
      contextState: ctx ? ctx.state : null,
      entries: this.entries.size,
      loaded: this.loaded.size,
      missing: [...this.missing].sort(),
      bgm: this.bgm?.id ?? null,
      bgmVolume: this.bgm ? Number(this.bgm.volume.toFixed(3)) : 0,
      bgmFading: this.dying.length + (this.bgm?.fade ? 1 : 0),
      floor: this.floor,
      state: this.state,
      paused: this.paused,
      loops: [...this.loops.keys()],
      loopTrimmed: [...this.trimmed],
      voices: this.bank.playing,
      recent: [...this.recent],
      mute: this.muted,
      volumes: { ...this.vol },
      scene: this.floorScene,
      bossPhase: this.bossPhase,
      outroSilence: this.outroSilence,
      lazyLoading: this.lazy.inFlight,
      ducks: this.bank.activeDucks,
      bgmDuck: Number(this.bank.bgmGain.toFixed(3)),
      limiter: this.limiter !== null,
    };
  }

  // --- 내부 ---

  private onTrigger(tr: AudioTrigger, payload: unknown): void {
    if (tr.when && !tr.when(payload)) return;
    const stops = [...(tr.stop ?? []), ...(tr.stopOf?.(payload) ?? [])];
    const fadeMs = typeof tr.stopFadeMs === 'function' ? tr.stopFadeMs(payload) : (tr.stopFadeMs ?? 0);
    for (const id of stops) {
      if (fadeMs > 0) this.stopLoop(id, fadeMs);
      this.stopSfx(id);
    }
    if (tr.loop) this.startLoop(tr.loop, tr.loopFadeInMs);
    const loopId = tr.loopOf?.(payload);
    if (loopId) {
      this.startLoop(loopId, tr.loopFadeInMs);
      this.loopRates.set(loopId, 1);
    }
    const lr = tr.loopRate?.(payload);
    if (lr) this.setLoopRate(lr.id, lr.rate);
    const id = this.pickLoaded(typeof tr.sfx === 'function' ? tr.sfx(payload) : tr.sfx);
    if (id) this.playSfx(id, { delayMs: tr.delayMs ? tr.delayMs(payload) : 0, rate: tr.rate ? tr.rate(payload) : 1 });
  }

  /** 55라운드: 효과음 후보 목록이면 로드된 첫 id (없으면 첫 후보 — playSfx 가 missing 으로 기록하고 무음) */
  private pickLoaded(ids: string | readonly string[] | null | undefined): string | null {
    if (ids === null || ids === undefined) return null;
    if (typeof ids === 'string') return ids;
    return ids.find((id) => this.loaded.has(id)) ?? ids[0] ?? null;
  }

  private onStageStarted(p: { stageIndex: number }): void {
    this.outroSilence = false;
    this.stopAllLoops();
    // 61라운드 §9: 층 시작 = 여정부터 (노드 진입이 곧 장면을 정한다)
    this.floorScene = 'journey';
    this.bossPhase = 1;
    this.prefetchFloor(p.stageIndex + 1, false);
    this.setFloor(p.stageIndex + 1);
  }

  /** 61라운드 §9: 노드 → 장면(여정·전투), 보스 노드면 국면 곡 미리 */
  private onNodeEntered(p: NodeEnteredPayload): void {
    this.outroSilence = false;
    this.floorScene = floorSceneOfNode(p.kind);
    if (p.kind === 'boss' && this.floor !== null) this.prefetchFloor(this.floor, true);
    this.refreshBgm();
  }

  private onBossStarted(p: { boss: string }): void {
    this.outroSilence = false;
    this.bossPhase = 1;
    this.setState(bossBgmState(this.manifest, p.boss));
  }

  /** 61라운드 §9: 국면 곡 — 지금 재생 위치에서 bgmPhaseCrossfadeMs 교차 페이드 */
  private onBossPhase(p: BossPhasePayload): void {
    if (!isBossState(this.state)) return;
    this.bossPhase = Math.max(1, p.phase);
    this.refreshBgm(true);
  }

  /** 61라운드: 보스 곡을 페이드아웃하고 보상 메뉴가 끝날 때까지 정적 (층 곡이 처치 연출 위로 바로 돌아오지 않게) */
  private onBossDied(): void {
    if (!isBossState(this.state)) return;
    this.state = null;
    this.outroSilence = true;
    this.retire(AUDIO.BOSS_DEFEAT_FADE_MS);
  }

  private endOutroSilence(): void {
    if (!this.outroSilence) return;
    this.outroSilence = false;
    this.refreshBgm();
  }

  private onRunEnding(): void {
    this.stopAllLoops();
    this.fadeOutBgm();
  }

  private onRunEnded(_p: RunEndedPayload): void {
    this.stopAllLoops();
    if (this.bgm) this.fadeOutBgm();
  }

  private refreshBgm(phaseChange = false): void {
    const sm = this.game?.sound;
    if (!sm) return;
    if (this.outroSilence) {
      if (this.bgm) this.retire(AUDIO.BOSS_DEFEAT_FADE_MS);
      return;
    }
    const want = resolveBgmFor(this.manifest, this.floor, this.state, this.floorScene, this.bossPhase);
    const target = want ? this.targetVolume(want) : 0;
    if (this.bgm && this.bgm.id === want) {
      if (Math.abs(this.bgm.volume - target) > 1e-4 || (this.bgm.fade && this.bgm.fade.to !== target)) {
        this.bgm.fade = { from: this.bgm.volume, to: target, startAt: this.now(), ms: this.mix.bgmCrossfadeMs };
      }
      return;
    }
    // 지연 로드 중인 곡이면 지금 곡을 유지하고 도착하면 다시 (prefetchFloor → refreshBgm)
    if (want && !this.loaded.has(want) && this.lazy.isLoading(want)) return;
    // 61라운드 §9: 국면 전환은 지금 재생 위치에서 짧게 교차
    const sync = phaseChange && this.mix.bgmPhaseSyncPosition !== false && this.bgm !== null;
    const ms = sync ? (this.mix.bgmPhaseCrossfadeMs ?? this.mix.bgmCrossfadeMs) : this.mix.bgmCrossfadeMs;
    const seekFrom = sync ? this.bgm!.sound : null;
    this.retire(ms);
    if (!want) return;
    const entry = this.entries.get(want);
    if (!entry || !this.loaded.has(want)) {
      this.missing.add(want);
      return;
    }
    const snd = sm.add(want, { loop: true, volume: 0 }) as Snd;
    const dur = entry.durationMs / 1000;
    const pos = seekFrom && dur > 0 ? (seekFrom as unknown as { seek: number }).seek % dur : 0;
    if (pos > 0) snd.play({ seek: pos });
    else snd.play();
    this.bgm = {
      id: want,
      sound: snd,
      volume: 0,
      fade: { from: 0, to: target, startAt: this.now(), ms },
      dying: false,
    };
  }

  private targetVolume(id: string): number {
    const entry = this.entries.get(id);
    if (!entry) return 0;
    return bgmGain(this.mix, entry, { bossDuck: isBossState(this.state), pauseDuck: this.paused }) * this.vol.bgm;
  }

  /** 현재 BGM 을 페이드아웃 목록으로 넘긴다 */
  private retire(ms: number): void {
    const cur = this.bgm;
    if (!cur) return;
    this.bgm = null;
    cur.dying = true;
    cur.fade = { from: cur.volume, to: 0, startAt: this.now(), ms };
    this.dying.push(cur);
  }

  private step(): void {
    const now = this.now();
    // 61라운드 §9 덕킹: 효과음 봉투 적용 · BGM 덕킹이 바뀌면 지금 곡에 바로
    const prevDuck = this.bank.bgmGain;
    const duck = this.bank.update(now);
    if (Math.abs(duck - prevDuck) > 1e-4 && this.bgm && !this.bgm.fade)
      this.bgm.sound.setVolume(this.bgm.volume * duck);
    if (this.fading.length > 0) {
      this.fading = this.fading.filter((f) => {
        const k = Math.min(1, (now - f.at) / f.ms);
        if (f.snd.pendingRemove || (k >= 1 && f.to <= 0)) {
          this.kill(f.snd);
          return false;
        }
        f.snd.setVolume(f.from + (f.to - f.from) * k);
        return k < 1;
      });
    }
    if (this.bgm?.fade) this.applyFade(this.bgm, now);
    if (this.dying.length > 0) {
      const keep: BgmTrack[] = [];
      for (const t of this.dying) {
        this.applyFade(t, now);
        if (t.fade) keep.push(t);
        else this.kill(t.sound);
      }
      this.dying = keep;
    }
  }

  private applyFade(t: BgmTrack, now: number): void {
    const f = t.fade;
    if (!f) return;
    const k = f.ms <= 0 ? 1 : Math.min(1, (now - f.startAt) / f.ms);
    t.volume = f.from + (f.to - f.from) * k;
    t.sound.setVolume(t.volume * (t.dying ? 1 : this.bank.bgmGain));
    if (k >= 1) t.fade = null;
  }

  private kill(snd: Snd | undefined): void {
    if (!snd || snd.pendingRemove) return;
    snd.removeAllListeners();
    if (snd.isPlaying) snd.stop();
    snd.destroy();
  }

  private applyMute(): void {
    const sm = this.game?.sound;
    if (sm) sm.mute = this.muted;
  }

  private applyMasterVolume(): void {
    const sm = this.game?.sound;
    if (sm) sm.volume = this.vol.master;
  }

  private resumeContext(): void {
    const sm = this.game?.sound;
    if (!sm || !('context' in sm)) return;
    const ctx = (sm as Phaser.Sound.WebAudioSoundManager).context;
    if (ctx && ctx.state === 'suspended') void ctx.resume();
  }

  private now(): number {
    return this.game ? this.game.getTime() : 0;
  }

  /** 테스트·재초기화용 */
  detach(): void {
    const game = this.game;
    if (!game) return;
    game.events.off(Phaser.Core.Events.STEP, this.step, this);
    for (const h of this.triggerHandlers) EventBus.off(h.event, h.fn);
    this.triggerHandlers.length = 0;
    EventBus.off(Events.STAGE_STARTED, this.onStageStarted, this);
    EventBus.off(Events.BOSS_STARTED, this.onBossStarted, this);
    EventBus.off(Events.BOSS_PHASE, this.onBossPhase, this);
    EventBus.off(Events.NODE_ENTERED, this.onNodeEntered, this);
    EventBus.off(Events.BOSS_DIED, this.onBossDied, this);
    EventBus.off(Events.EXIT_OPENED, this.endOutroSilence, this);
    EventBus.off(Events.PLAYER_DIED, this.onRunEnding, this);
    EventBus.off(Events.ENDING_CHOSEN, this.onRunEnding, this);
    EventBus.off(Events.RUN_ENDED, this.onRunEnded, this);
    if (typeof document !== 'undefined') {
      if (this.onGesture) {
        document.removeEventListener('pointerdown', this.onGesture);
        document.removeEventListener('keydown', this.onGesture);
      }
    }
    this.stopAllLoops();
    this.retire(0);
    this.step();
    this.game = null;
  }
}

export const audio = new AudioSystem();
