/**
 * 61라운드 P5·P8 이벤트 문장 (Phaser 의존 없음): 스토리 팩 선택지 문구의 {…} 를 효과 값으로 채운다.
 * gold 전표 · trait 개성 · sense 감각 · hp 최대 체력 · discount 할인 % · curse 저주 이름
 */
import { curseDef } from '../../data/build';
import type { EventOption } from '../../data/bundle2Types';
import { fill } from '../story';

export function optionLabel(o: EventOption): string {
  const vars: Record<string, string | number> = {};
  for (const e of o.effects) {
    if (e.kind === 'gold') vars.gold = Math.abs(e.value);
    else if (e.kind === 'personality') vars.trait = e.value;
    else if (e.kind === 'sense') vars.sense = e.value;
    else if (e.kind === 'maxHp') vars.hp = Math.abs(e.value);
    else if (e.kind === 'shopDiscount') vars.discount = Math.round(e.value * 100);
    else if (e.kind === 'curse') vars.curse = `저주 '${curseDef(e.id)?.name ?? e.id}'`;
  }
  return fill(o.label, vars);
}
