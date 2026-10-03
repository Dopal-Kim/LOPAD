/**
 * 오디오 시스템 (음향↔시스템 계약 초안 `assets/audio/manifest.json`, 결정 로그 I·K).
 * - Preloader 가 매니페스트·WAV 를 로드한 뒤 `register()` 로 넘긴다.
 * - 효과음은 EventBus 이벤트를 `audioMap.ts` 표로 매핑해 재생한다 (게임 코드는 소리를 직접 호출하지 않는다).
 * - BGM 은 층(`bgmByFloor`)·상태(`bgmByState`: title / boss / emperor)로 정하고 크로스페이드한다.
 * - 버스: SFX 0 dB, BGM -8 dB, 보스전 BGM -3 dB, entry.gainDb 가산. 같은 효과음 20ms 중복 1회, swing·hit 류 ±4% 피치.
 * - 음소거는 `setMute()` (localStorage `lopad.mute`) — 49라운드 계약 §11.3: Esc 메뉴 설정 → uiCommands.setMuted.
 *   M 키 토글은 없앴다 (M = UI 지도). 디버그 요약은 `summary()`.
 * 게임 수명 동안 하나(main.ts 에서 attach). 씬 재시작과 무관하게 BGM 이 이어진다.
 */
import Phaser from 'phaser';
import { AUDIO } from '../core/Constants';
import { EventBus, Events, type RunEndedPayload } from '../core/EventBus';
import { browserStorage } from './save';
import {
  EMPTY_AUDIO_MANIFEST,
  bgmGain,
  bossBgmState,
  hasPitchVariance,
  indexEntries,
  isBossState,
  mixingOf,
  pitchRate,
  resolveBgm,
  sfxGain,
  SfxDedupe,
  type AudioEntry,
  type AudioManifest,
  type AudioMixing,
} from './audioDefs';
import { AUDIO_TRIGGERS, type AudioTrigger } from './audioMap';

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
  paused: boolean;
  loops: string[];
  voices: number;
  recent: { id: string; at: number; rate: number; delayMs: number }[];
  mute: boolean;
}

export class AudioSystem {
  private game: Phaser.Game | null = null;
  private manifest: AudioManifest = EMPTY_AUDIO_MANIFEST;
  private entries = new Map<string, AudioEntry>();
  private mix: AudioMixing = mixingOf(EMPTY_AUDIO_MANIFEST);
  private readonly loaded = new Set<string>();
  private readonly missing = new Set<string>();
  private readonly dedupe = new SfxDedupe();
  private voices: Snd[] = [];
  private readonly loops = new Map<string, Snd>();
  /** 페이드 아웃 중인 루프 */
  private fading: { snd: Snd; from: number; at: number; ms: number }[] = [];
  private bgm: BgmTrack | null = null;
  private dying: BgmTrack[] = [];
  private floor: number | null = null;
  private state: string | null = null;
  private paused = false;
  private recent: AudioSummary['recent'] = [];
  private muted = false;
  private readonly storage = browserStorage();
  private onGesture?: () => void;
  private readonly triggerHandlers: { event: string; fn: (p: unknown) => void }[] = [];

  /** 게임 생성 직후 1회. EventBus 구독·음소거 복원·크로스페이드 스텝 등록 */
  attach(game: Phaser.Game): void {
    if (this.game) return;
    this.game = game;
    this.muted = this.storage?.getItem(AUDIO.MUTE_STORAGE_KEY) === '1';
    this.applyMute();
    game.events.on(Phaser.Core.Events.STEP, this.step, this);
    for (const tr of AUDIO_TRIGGERS) {
      const fn = (p: unknown) => this.onTrigger(tr, p);
      this.triggerHandlers.push({ event: tr.event, fn });
      EventBus.on(tr.event, fn);
    }
    EventBus.on(Events.STAGE_STARTED, this.onStageStarted, this);
    EventBus.on(Events.BOSS_STARTED, this.onBossStarted, this);
    EventBus.on(Events.BOSS_DIED, this.onBossDied, this);
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
    for (const k of loadedKeys) if (this.entries.has(k)) this.loaded.add(k);
    this.refreshBgm();
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

  // --- 효과음 ---

  /** 효과음 1회. 매니페스트에 없거나 로드되지 않았으면 무시(missing 기록) */
  playSfx(id: string, opts: { delayMs?: number; rate?: number } = {}): boolean {
    const sm = this.game?.sound;
    const entry = this.entries.get(id);
    if (!sm || !entry) {
      this.missing.add(id);
      return false;
    }
    if (!this.loaded.has(id)) {
      this.missing.add(id);
      return false;
    }
    const now = this.now();
    if (!this.dedupe.allow(id, now)) return false;
    const rate = (hasPitchVariance(id) ? pitchRate(Math.random()) : 1) * (opts.rate ?? 1);
    const delayMs = Math.max(0, opts.delayMs ?? 0);
    this.pruneVoices();
    while (this.voices.length >= AUDIO.MAX_SFX_VOICES) {
      const oldest = this.voices.shift();
      this.kill(oldest);
    }
    const snd = sm.add(id, { volume: sfxGain(this.mix, entry), rate, loop: false, delay: delayMs / 1000 }) as Snd;
    snd.once(Phaser.Sound.Events.COMPLETE, () => this.kill(snd));
    snd.play();
    this.voices.push(snd);
    this.recent.push({ id, at: Math.round(now), rate: Number(rate.toFixed(3)), delayMs });
    if (this.recent.length > AUDIO.RECENT_SFX) this.recent.shift();
    return true;
  }

  /** 루프 효과음 시작 (가드 유지). 이미 돌고 있으면 유지 */
  startLoop(id: string): void {
    const sm = this.game?.sound;
    const entry = this.entries.get(id);
    if (!sm || !entry || !this.loaded.has(id) || this.loops.has(id)) {
      if (!entry || !this.loaded.has(id)) this.missing.add(id);
      return;
    }
    const snd = sm.add(id, { volume: sfxGain(this.mix, entry), loop: true }) as Snd;
    snd.play();
    this.loops.set(id, snd);
  }

  /** 루프 정지. fadeMs 가 있으면 그동안 볼륨을 줄인 뒤 (54라운드 보스 루프) */
  stopLoop(id: string, fadeMs = 0): void {
    const snd = this.loops.get(id);
    if (!snd) return;
    this.loops.delete(id);
    if (fadeMs > 0 && snd.isPlaying)
      this.fading.push({ snd, from: (snd as unknown as { volume: number }).volume ?? 1, at: this.now(), ms: fadeMs });
    else this.kill(snd);
  }

  /** 해당 id 의 재생 중인 효과음(일회성·루프) 전부 정지 */
  stopSfx(id: string): void {
    this.stopLoop(id);
    const keep: Snd[] = [];
    for (const v of this.voices) {
      if (v.key === id) this.kill(v);
      else keep.push(v);
    }
    this.voices = keep;
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
      voices: this.voices.filter((v) => v.isPlaying).length,
      recent: [...this.recent],
      mute: this.muted,
    };
  }

  // --- 내부 ---

  private onTrigger(tr: AudioTrigger, payload: unknown): void {
    if (tr.when && !tr.when(payload)) return;
    const stops = [...(tr.stop ?? []), ...(tr.stopOf?.(payload) ?? [])];
    for (const id of stops) {
      if (tr.stopFadeMs) this.stopLoop(id, tr.stopFadeMs);
      this.stopSfx(id);
    }
    if (tr.loop) this.startLoop(tr.loop);
    const loopId = tr.loopOf?.(payload);
    if (loopId) this.startLoop(loopId);
    const id = typeof tr.sfx === 'function' ? tr.sfx(payload) : tr.sfx;
    if (id) this.playSfx(id, { delayMs: tr.delayMs ? tr.delayMs(payload) : 0, rate: tr.rate ? tr.rate(payload) : 1 });
  }

  private onStageStarted(p: { stageIndex: number }): void {
    this.stopAllLoops();
    this.setFloor(p.stageIndex + 1);
  }

  private onBossStarted(p: { boss: string }): void {
    this.setState(bossBgmState(this.manifest, p.boss));
  }

  private onBossDied(): void {
    if (isBossState(this.state)) this.setState(null);
  }

  private onRunEnding(): void {
    this.stopAllLoops();
    this.fadeOutBgm();
  }

  private onRunEnded(_p: RunEndedPayload): void {
    this.stopAllLoops();
    if (this.bgm) this.fadeOutBgm();
  }

  private refreshBgm(): void {
    const sm = this.game?.sound;
    if (!sm) return;
    const want = resolveBgm(this.manifest, this.floor, this.state);
    const target = want ? this.targetVolume(want) : 0;
    if (this.bgm && this.bgm.id === want) {
      if (Math.abs(this.bgm.volume - target) > 1e-4 || (this.bgm.fade && this.bgm.fade.to !== target)) {
        this.bgm.fade = { from: this.bgm.volume, to: target, startAt: this.now(), ms: this.mix.bgmCrossfadeMs };
      }
      return;
    }
    this.retire(this.mix.bgmCrossfadeMs);
    if (!want) return;
    const entry = this.entries.get(want);
    if (!entry || !this.loaded.has(want)) {
      this.missing.add(want);
      return;
    }
    const snd = sm.add(want, { loop: true, volume: 0 }) as Snd;
    snd.play();
    this.bgm = {
      id: want,
      sound: snd,
      volume: 0,
      fade: { from: 0, to: target, startAt: this.now(), ms: this.mix.bgmCrossfadeMs },
      dying: false,
    };
  }

  private targetVolume(id: string): number {
    const entry = this.entries.get(id);
    if (!entry) return 0;
    return bgmGain(this.mix, entry, { bossDuck: isBossState(this.state), pauseDuck: this.paused });
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
    if (this.fading.length > 0) {
      this.fading = this.fading.filter((f) => {
        const k = Math.min(1, (now - f.at) / f.ms);
        if (k >= 1 || f.snd.pendingRemove) {
          this.kill(f.snd);
          return false;
        }
        f.snd.setVolume(f.from * (1 - k));
        return true;
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
    t.sound.setVolume(t.volume);
    if (k >= 1) t.fade = null;
  }

  private pruneVoices(): void {
    this.voices = this.voices.filter((v) => v.isPlaying && !v.pendingRemove);
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
    EventBus.off(Events.BOSS_DIED, this.onBossDied, this);
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
