import Phaser from 'phaser';
import type { UiNodeGrade, UiNodeRewardKind } from '../contract/ui';
import { gradeStamp } from './buildView';
import { rewardGlyph, riskGlyph } from './bundleView';
import { GlowText } from './glow';
import { KIT, STAIN, accentHex } from './kit';
import { diamondRing } from './routeGlyph';
import { r60Text } from './text';
import { LAYOUT, SEPIA, hexToNum } from './theme';
import { MARKS } from './themeBuild';

/**
 * 60라운드 계약 §14.5 노드 표지 (노드 지도 위). 아이콘 7+2종·도장 3종이 오기 전의 **임시 표시** — 한 글자 + 기본 도형.
 * 색은 세피아·층 강조 램프만. 모두 (x, y) = 노드 아이콘 가운데 기준으로 놓는다.
 */

/** 작은 표 (Container → Graphics → 글자): 세피아 S1 바탕 + 테두리(보통 S4, 저주 = 층 강조 20) + 한 글자 */
function tag(
  scene: Phaser.Scene,
  x: number,
  y: number,
  ch: string,
  accent: boolean,
  si: number,
): Phaser.GameObjects.Container {
  const s = MARKS.badge;
  const g = scene.add.graphics();
  g.fillStyle(hexToNum(SEPIA[1]), 1).fillRect(0, 0, s, s);
  g.lineStyle(1, accent ? hexToNum(accentHex(scene, si, 20)) : hexToNum(SEPIA[4]), 1).strokeRect(
    0.5,
    0.5,
    s - 1,
    s - 1,
  );
  const t = new GlowText(scene, 0, 0, ch, accent ? 'ink_accent' : 'page_body', { stageIndex: si });
  t.setPosition(Math.round(s / 2 - t.displayWidth / 2), Math.round(s / 2 - t.displayHeight / 2));
  return scene.add.container(Math.round(x), Math.round(y), [g, t]);
}

/** 보상 미리보기 (아이콘 오른쪽 아래) */
export function rewardBadge(
  scene: Phaser.Scene,
  x: number,
  y: number,
  kind: UiNodeRewardKind,
  si: number,
): Phaser.GameObjects.Container {
  return tag(scene, x + MARKS.rewardDx, y + MARKS.rewardDy, rewardGlyph(kind), kind === 'curse', si);
}

/** 위험 노드 표 (아이콘 왼쪽 위, 층 강조) — 붉은 테두리는 RouteMap 이 노드 고리로 그린다 */
export function riskBadge(
  scene: Phaser.Scene,
  x: number,
  y: number,
  kind: 'elite' | 'curse',
  si: number,
): Phaser.GameObjects.Container {
  return tag(scene, x + MARKS.riskDx, y + MARKS.riskDy, riskGlyph(kind), true, si);
}

/** 위험 노드 테두리: 노드 고리 바깥 마름모 1px (층 강조 슬롯 MARKS.riskSlot) */
export function riskRing(g: Phaser.GameObjects.Graphics, scene: Phaser.Scene, r: number, si: number): void {
  diamondRing(g, r + MARKS.riskRingGap, 1, hexToNum(accentHex(scene, si, MARKS.riskSlot)), 1);
}

/** 성과 도장 (完·良) — 아이콘 오른쪽 위에 바랜 잉크 (도장 알파 0.85, 확대·회전 없음) */
export function gradeMark(scene: Phaser.Scene, x: number, y: number, grade: UiNodeGrade, si: number): GlowText {
  const t = new GlowText(scene, 0, 0, gradeStamp(grade, r60Text), 'page_body', { stageIndex: si });
  t.setPosition(Math.round(x + MARKS.gradeDx), Math.round(y + MARKS.gradeDy)).setAlpha(LAYOUT.stampAlpha);
  return t;
}

/**
 * 숨은 노드 얼룩 (§14.5 `hidden: 'smudge'`): 키트 얼룩 데칼(`MARKS.smudgeStain` — 어두운 지도 그림 위에서도 보이게
 * 발광 잉크 얼룩 `stain_blot`)을 땅 점에. 위치 표시(`located`)면
 * 얼룩 둘레에 흐린 마름모 점선 고리 + '?'. 반환 = 만든 객체들(얼룩 이미지가 첫째).
 */
export function smudgeMark(
  scene: Phaser.Scene,
  x: number,
  y: number,
  located: boolean,
  si: number,
): Phaser.GameObjects.GameObject[] {
  const img = scene.add
    .image(Math.round(x - 16), Math.round(y - 16), KIT.stains, STAIN.indexOf(MARKS.smudgeStain))
    .setOrigin(0, 0);
  const objs: Phaser.GameObjects.GameObject[] = [img];
  if (located) {
    const g = scene.add.graphics();
    const c = hexToNum(accentHex(scene, si, 20));
    const r = MARKS.locatedR;
    g.fillStyle(c, 1);
    // 점선 마름모 (2칸 건너 1칸)
    for (let i = -r; i <= r; i += 3) {
      const w = r - Math.abs(i);
      g.fillRect(Math.round(x - w), Math.round(y + i), 1, 1);
      g.fillRect(Math.round(x + w), Math.round(y + i), 1, 1);
    }
    const q = new GlowText(scene, 0, 0, '?', 'ink_accent', { stageIndex: si });
    q.setPosition(Math.round(x - q.displayWidth / 2), Math.round(y - q.displayHeight / 2));
    objs.push(g, q);
  }
  return objs;
}
