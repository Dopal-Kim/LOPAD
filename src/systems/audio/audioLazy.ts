/**
 * 61라운드 계약 sound §9: 층 전용 BGM 지연 로드 (1층 곡 5개 OGG 약 9MB — 부팅을 막지 않게). WebAudio 전용:
 * fetch → decodeAudioData → 오디오 캐시. 형식은 URL 확장자와 기기 지원(Phaser device.audio)으로 고른다.
 */
import type Phaser from 'phaser';

const EXT_KEYS: Record<string, readonly string[]> = {
  ogg: ['ogg', 'opus'],
  m4a: ['m4a', 'aac', 'mp4'],
  mp3: ['mp3'],
  wav: ['wav'],
  webm: ['webm'],
};

/** 기기가 재생할 수 있는 첫 URL (확장자 기준). 지원 정보가 없으면 첫 URL */
export function pickPlayableUrl(
  urls: readonly string[],
  support: Readonly<Record<string, boolean>> | null,
): string | null {
  if (urls.length === 0) return null;
  if (!support) return urls[0];
  for (const u of urls) {
    const ext = /\.(\w+)(?:\?.*)?$/.exec(u)?.[1]?.toLowerCase() ?? '';
    const keys = EXT_KEYS[ext] ?? [ext];
    if (keys.some((k) => support[k])) return u;
  }
  return null;
}

export class LazyAudio {
  private urls = new Map<string, readonly string[]>();
  private readonly loading = new Map<string, Promise<boolean>>();

  register(urls: ReadonlyMap<string, readonly string[]>): void {
    this.urls = new Map(urls);
  }

  has(id: string): boolean {
    return this.urls.has(id);
  }

  isLoading(id: string): boolean {
    return this.loading.has(id);
  }

  get inFlight(): string[] {
    return [...this.loading.keys()];
  }

  /** 받아서 캐시에 넣는다. 이미 캐시에 있으면 true, 실패하면 false (한 번 실패하면 다시 시도 가능) */
  load(id: string, sm: Phaser.Sound.WebAudioSoundManager, game: Phaser.Game): Promise<boolean> {
    if (game.cache.audio.exists(id)) return Promise.resolve(true);
    const pending = this.loading.get(id);
    if (pending) return pending;
    const url = pickPlayableUrl(
      this.urls.get(id) ?? [],
      (game.device?.audio as unknown as Record<string, boolean> | undefined) ?? null,
    );
    if (!url || typeof fetch === 'undefined') return Promise.resolve(false);
    const p = fetch(url)
      .then((r) => (r.ok ? r.arrayBuffer() : Promise.reject(new Error(String(r.status)))))
      .then((ab) => sm.context.decodeAudioData(ab))
      .then((buf) => {
        game.cache.audio.add(id, buf);
        return true;
      })
      .catch(() => false)
      .finally(() => this.loading.delete(id));
    this.loading.set(id, p);
    return p;
  }
}
