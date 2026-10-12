/**
 * 62 루프 2 F: 작은 정지 그림(유품·소품·초상·개성 카드·미리보기·사연 컷)을 **씬 사이에서 한 번만** 받는다.
 * 문제: 노드를 옮기면 Game 씬이 다시 시작되는데, Phaser 로더는 씬 종료 때 목록만 비우고(`reset`) 이미 받기 시작한 파일은
 * 끝까지 받아 텍스처에 넣는다(리스너는 지워짐). 새 씬이 같은 키를 다시 큐에 넣으면 둘 다 완료돼
 * 'Texture key already in use' 경고가 났다(장터 첫 진입 등 — 시스템 C RunEndArt · 61 G GrowthArt · 의식 Setup 이 같은 키).
 * 해결: 키별 마지막 파일을 기억해, 그 파일이 **실제로 받는 중**(LOADING·LOADED·PROCESSING)이면 다시 넣지 않고 텍스처가
 * 들어오는 순간(`addtexture-<key>`)을 기다린다. 아직 시작하지 않은 채 씬 종료로 버려진 파일(PENDING)·실패한 파일은 다시 받는다.
 */
import type Phaser from 'phaser';

/** Phaser.Loader 파일 상태 (loader/const.js) — 받는 중으로 보는 것 */
const LIVE_STATES: ReadonlySet<number> = new Set([
  11 /* FILE_LOADING */, 12 /* FILE_LOADED */, 14 /* FILE_PROCESSING */,
]);
/** Phaser Textures.Events.ADD_KEY ('addtexture-' + key) */
const ADD_KEY = 'addtexture-';

type FileLike = { key: string; type: string; state: number };
const lastFile = new Map<string, FileLike>();

/** 그 키의 파일이 지금 (어느 씬 로더에서든) 받는 중인가 */
export function imageLoading(key: string): boolean {
  const f = lastFile.get(key);
  return Boolean(f && LIVE_STATES.has(f.state));
}

/**
 * 그림 하나를 (없으면) 받도록 큐에 넣는다. 이미 있으면 바로 onLoaded, 다른 씬이 받는 중이면 들어오는 순간 onLoaded.
 * 반환 = 이 로더 큐에 새로 넣었는가 (true 면 호출한 쪽이 `load.start()` 를 챙긴다)
 */
export function queueImageOnce(scene: Phaser.Scene, key: string, url: string, onLoaded?: () => void): boolean {
  const tex = scene.textures;
  if (tex.exists(key)) {
    onLoaded?.();
    return false;
  }
  if (onLoaded) tex.once(`${ADD_KEY}${key}`, onLoaded);
  if (imageLoading(key)) return false;
  const load = scene.load;
  load.image(key, url);
  // 방금 넣은 파일 (같은 로더에 이미 있던 같은 키면 Phaser 가 무시 — 그때는 그 파일)
  let file: FileLike | undefined;
  load.list.each((f: FileLike) => {
    if (f.key === key && f.type === 'image') file = f;
    return !file;
  });
  if (file) lastFile.set(key, file);
  return true;
}
