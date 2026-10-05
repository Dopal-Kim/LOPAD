/**
 * 61라운드 플레이 점검 P0: 씬 종료(shutdown) 때는 Phaser DisplayList 가 Game.cleanup 보다 먼저 자식 스프라이트를 파괴한다
 * (파괴된 Sprite 는 `anims`·`scene` 이 undefined). 그 뒤 빌드 쪽 루프 fx(저주·취기 표시)를 `fx.stop` 으로 정리하면
 * `anims.chain()` 에서 TypeError → 씬이 다시 시작되지 않아 검은 화면이 됐다. 풀 반납 전에 파괴 여부를 본다. Phaser 의존 없음.
 */
export interface ReleasableSprite {
  scene?: unknown;
  anims?: { chain(): unknown; stop(): unknown } | null;
  off(event: string): unknown;
  setActive(v: boolean): ReleasableSprite;
  setVisible(v: boolean): ReleasableSprite;
  setAlpha(v: number): ReleasableSprite;
  setRotation(v: number): ReleasableSprite;
  setScale(v: number): ReleasableSprite;
  setFlipY(v: boolean): ReleasableSprite;
  clearTint(): ReleasableSprite;
}

/** 파괴된(또는 씬에서 떨어진) 스프라이트 */
export function isDestroyedSprite(s: Pick<ReleasableSprite, 'scene' | 'anims'>): boolean {
  return !s.scene || !s.anims;
}

/** 애니 체인을 비우고 멈춘 뒤 비활성으로 되돌린다. 이미 파괴됐으면 아무것도 하지 않고 false */
export function resetPooledSprite(s: ReleasableSprite, completeEvent: string): boolean {
  if (isDestroyedSprite(s)) return false;
  s.off(completeEvent);
  s.anims!.chain();
  s.anims!.stop();
  s.setActive(false).setVisible(false).setAlpha(1).setRotation(0).setScale(1).setFlipY(false).clearTint();
  return true;
}
