/**
 * 61라운드 단계 2 노드 지도 늦은 그림 버그 — 표시 순서 끼우기 (순수 계산).
 *
 * 원인: 늦게 읽힌 지도 그림을 `scene.children.moveAbove(img, anchor)` 로 바탕 바로 위에 끼웠는데, Phaser `MoveAbove` 는
 * '이미 위에 있으면 옮기지 않는다'. 새로 만든 그림은 표시 목록 맨 끝(= 가장 위)이라 그대로 남아 노드·길·글을 덮었다.
 * 그래서 늘 '빼고 → 기준 바로 위/아래에 넣는다'. 같은 depth 안에서는 Phaser 깊이 정렬이 안정 정렬이라 이 순서가 유지된다.
 */
export function insertNextTo<T>(list: T[], item: T, anchor: T, where: 'above' | 'below'): boolean {
  if (item === anchor) return false;
  const from = list.indexOf(item);
  if (from < 0 || list.indexOf(anchor) < 0) return false;
  list.splice(from, 1);
  const at = list.indexOf(anchor);
  list.splice(where === 'above' ? at + 1 : at, 0, item);
  return true;
}
