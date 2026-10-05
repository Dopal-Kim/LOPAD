/** `{name}` 꼴 치환자를 채운다. 값이 없는 치환자는 그대로 둔다 (Phaser·계약 없이 — 순수 계산 모듈이 쓴다) */
export function fill(template: string, vars: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (m, k: string) => (k in vars ? String(vars[k]) : m));
}
