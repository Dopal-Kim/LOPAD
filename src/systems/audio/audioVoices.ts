/**
 * 61라운드 계약 sound §9: 효과음 목소리 묶음 — 동시 재생 상한(우선순위·그룹·UI) · 덕킹 봉투 · 효과음 버스 배율(설정 §15).
 * 규칙 계산은 audioMix(순수), 이 파일은 재생 중인 소리 목록과 음량 적용만 한다. 루프 효과음은 여기 넣지 않는다(빼앗지 않음).
 */
import type Phaser from 'phaser';
import type { AudioMixing } from './audioDefs';
import { dbToGain } from './audioDefs';
import {
  allocateVoice,
  duckDbAt,
  duckFinished,
  ducksFor,
  hitStackDb,
  parseDucking,
  startDuck,
  voiceLimitsOf,
  type ActiveDuck,
  type DuckRule,
  type VoiceLimits,
} from './audioMix';

type Snd = Phaser.Sound.BaseSound & { setVolume(value: number): unknown };

export interface Voice {
  snd: Snd;
  id: string;
  group: string;
  priority: number;
  ui: boolean;
  at: number;
  /** 버스·덕킹 전 음량 */
  base: number;
}

export class VoiceBank {
  private voices: Voice[] = [];
  private ducks: ActiveDuck[] = [];
  private rules: DuckRule[] = [];
  private limits: VoiceLimits = voiceLimitsOf({} as AudioMixing);
  private sfxMult = 1;
  private bgmDuck = 1;
  /** P19 타격음 층 최근 시작 (몰림 감쇠·같은 id 간격) */
  private hitStarts: { group: string; at: number }[] = [];

  constructor(private readonly kill: (snd: Snd) => void) {}

  configure(mix: AudioMixing): void {
    this.limits = voiceLimitsOf(mix);
    this.rules = parseDucking(mix.ducking);
  }

  /** 설정 §15 효과음 버스 배율 — 재생 중인 소리에도 바로 */
  setSfxMult(m: number, now: number): void {
    this.sfxMult = m;
    this.applyVolumes(now);
  }

  /**
   * P19 타격음 층(sound §14): 층 소리가 아니면 0, 같은 id 가 간격 안이면 null(버림), 아니면 몰림 감쇠 dB. 통과하면 시작으로 적는다
   */
  hitStack(group: string, now: number): number | null {
    const layer = this.limits.hitLayer;
    if (!layer?.ids.has(group)) return 0;
    const keepMs = Math.max(layer.windowMs, layer.minGapMs);
    this.hitStarts = this.hitStarts.filter((s) => now - s.at < keepMs);
    const db = hitStackDb(this.hitStarts, group, now, layer);
    if (db !== null) this.hitStarts.push({ group, at: now });
    return db;
  }

  /** 새 소리 자리: 끊을 것은 끊고 true, 자리가 없으면 false */
  admit(v: { group: string; priority: number; ui: boolean }): boolean {
    this.prune();
    const r = allocateVoice(this.voices, v, this.limits);
    if (!r.ok) return false;
    const gone = new Set(r.steal.map((i) => this.voices[i]));
    for (const g of gone) this.kill(g.snd);
    this.voices = this.voices.filter((x) => !gone.has(x));
    return true;
  }

  /** 지금 이 우선순위 소리에 곱할 음량 (버스 × 덕킹) */
  gainFor(priority: number, now: number, self?: Snd): number {
    return this.sfxMult * dbToGain(duckDbAt(this.ducks, now, { bus: 'sfx', priority }, self));
  }

  add(v: Voice, durationMs: number, now: number): void {
    this.voices.push(v);
    for (const r of ducksFor(this.rules, v)) this.ducks.push(startDuck(r, now, durationMs, v.snd));
  }

  /** 매 프레임: 덕킹 봉투 적용 · 끝난 덕킹 제거. 반환 = BGM 덕킹 게인 */
  update(now: number): number {
    if (this.ducks.length > 0) {
      this.applyVolumes(now);
      this.ducks = this.ducks.filter((d) => !duckFinished(d, now));
    }
    this.bgmDuck = dbToGain(duckDbAt(this.ducks, now, { bus: 'bgm' }));
    return this.bgmDuck;
  }

  get bgmGain(): number {
    return this.bgmDuck;
  }

  /** 같은 id 의 재생 중인 소리 끊기 */
  stopId(id: string): void {
    const keep: Voice[] = [];
    for (const v of this.voices) {
      if (v.id === id) this.kill(v.snd);
      else keep.push(v);
    }
    this.voices = keep;
  }

  get playing(): number {
    return this.voices.filter((v) => v.snd.isPlaying).length;
  }

  get activeDucks(): number {
    return this.ducks.length;
  }

  private applyVolumes(now: number): void {
    for (const v of this.voices)
      if (!v.snd.pendingRemove) v.snd.setVolume(v.base * this.gainFor(v.priority, now, v.snd));
  }

  private prune(): void {
    this.voices = this.voices.filter((v) => v.snd.isPlaying && !v.snd.pendingRemove);
  }
}
