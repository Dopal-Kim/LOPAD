/**
 * 전투 수식. 프로토타입 임시 규칙:
 *  - 방어력은 평면 차감: damage = max(1, attack - defense)  (Claude 임시 규칙, 확인 필요)
 *  - 치명타·개성·감각은 1단계에서 미적용
 */
export function applyDefense(attack: number, defense: number): number {
  return Math.max(1, attack - defense);
}
