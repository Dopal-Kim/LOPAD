import { STORY } from '../data';

/** 텍스트 치환: "{name}" 형태의 키를 값으로 바꾼다 */
export function fill(template: string, vars: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (m, k: string) => (k in vars ? String(vars[k]) : m));
}

export function floorText(stageId: string) {
  return STORY.floors[stageId];
}

export function evolutionLine(evolutionName: string): string {
  return STORY.evolution.byName[evolutionName] ?? fill(STORY.evolution.generic, { evolution: evolutionName });
}

export function deathLine(name: string, floor: number, kills: number): string {
  return fill(STORY.death, { name: name || '―', floor, kills });
}
