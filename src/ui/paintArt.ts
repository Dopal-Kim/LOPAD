import type Phaser from 'phaser';

/**
 * 61 단계 6 (아트 §28) 붓 그림 에셋 키. 시스템이 `paint/...` 키로 읽어 두면 그것을 쓰고, 아직 없으면 UI 가 같은 파일을
 * `ui:paint/...` 키로 따로 읽는다 (같은 키를 두 곳에서 읽으면 Phaser 가 'key already in use' 오류를 낸다).
 */
export const PAINT_URL = 'assets-game/sprites/paint/';

/** UI 가 따로 읽을 때의 키 */
export const uiCopy = (key: string): string => `ui:${key}`;

/** 쓸 텍스처 키 (시스템 키 → UI 사본 → 없음) */
export function artTex(scene: Phaser.Scene, key: string | null | undefined): string | null {
  if (!key) return null;
  if (scene.textures.exists(key)) return key;
  const c = uiCopy(key);
  return scene.textures.exists(c) ? c : null;
}

/** 같은 키의 메타 JSON (시스템 키 → UI 사본 → `<키>.json`) */
export function artJson(scene: Phaser.Scene, key: string): unknown {
  for (const k of [key, uiCopy(key), `${key}.json`]) if (scene.cache.json.exists(k)) return scene.cache.json.get(k);
  return null;
}

/** `paint/<이름>` → 파일 주소 (확장자 없이) */
export function paintUrl(key: string): string {
  return `${PAINT_URL}${key.replace(/^ui:/, '').replace(/^paint\//, '')}`;
}
