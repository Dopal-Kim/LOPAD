/**
 * 61라운드 P8 서사 런 상태 (GameState.narrative — 새 런마다 새로). Phaser 의존 없음.
 * 무기 한마디 장면 1회 · 이번 생에 읽은 단서 · 이번 생에 쓰러뜨린 보스(층 id) · 한 번만 하는 말(만취 파훼 대사 등 — 보스 담당이 `once`).
 * 층 전환 세이브에는 남기지 않는다 (1층 범위 — 이어하기는 층 처음부터라 한마디가 한 번 더 나올 수 있다).
 */
import type { VoiceScene } from '../../data/narrative';

export class NarrativeState {
  /** 이번 런에 나온 무기 한마디 장면 */
  readonly voiced = new Set<VoiceScene>();
  /** 이번 생에 읽은 단서 id */
  readonly cluesRead = new Set<string>();
  /** 이번 생에 쓰러뜨린 층 보스 (stage id) */
  readonly bossKilled = new Set<string>();
  private readonly onceKeys = new Set<string>();

  /** 이 장면 한마디를 아직 안 했으면 true (이번에 한 것으로 남긴다) */
  takeVoice(scene: VoiceScene): boolean {
    if (this.voiced.has(scene)) return false;
    this.voiced.add(scene);
    return true;
  }

  /** 아무 키 1회 (예 'boss1.break.cup') — 처음이면 true */
  once(key: string): boolean {
    if (this.onceKeys.has(key)) return false;
    this.onceKeys.add(key);
    return true;
  }

  debug(): Record<string, unknown> {
    return {
      voiced: [...this.voiced],
      cluesRead: [...this.cluesRead],
      bossKilled: [...this.bossKilled],
      once: [...this.onceKeys],
    };
  }
}
