import Phaser from 'phaser';
import type { UiSnapshot } from '../contract/ui';
import { diaryLines, type DiaryLine } from './buildView';
import { GlowText } from './glow';
import { rule } from './kit';
import { r60Text } from './text';
import type { TextStyleName } from './theme';

const STYLE: Record<DiaryLine['style'], TextStyleName> = { head: 'page_faint', body: 'page_body', faint: 'page_faint' };
/** 제목 아래 괘선까지 + 괘선 아래 여백 */
const RULE_GAP = 6;
const AFTER_RULE = 4 + 10;

/**
 * 57·60라운드 일기장 오른쪽 쪽 '빌드' (계약 §14.1~14.3·§14.8): 태그·세트(점수·단계·다음 임계·세트 효과) / 이중 개성 /
 * 저주(남은 기간·이득·저주) / 패시브(Lv/최대·태그) / 소모품. 글을 먼저 만들어 높이를 재고(넘치면 효과·설명 줄을 접고,
 * 그래도 넘치면 끝을 '…'), 책을 깐 뒤 `place` 로 놓는다. 글은 depth 1 (책보다 위).
 */
export function buildPage(
  scene: Phaser.Scene,
  w: number,
  s: UiSnapshot,
  stageIndex: number,
  maxH: number,
): { h: number; place(x: number, y: number): void } {
  const title = new GlowText(scene, 0, 0, r60Text('buildTitle'), 'page_title', { font: 'title', stageIndex }).setDepth(
    1,
  );
  const top = title.displayHeight + RULE_GAP + AFTER_RULE;
  const make = (lines: DiaryLine[]): GlowText[] =>
    lines.map((l) => new GlowText(scene, 0, 0, l.text, STYLE[l.style], { wrap: w, stageIndex }).setDepth(1));
  const height = (ts: GlowText[], lines: DiaryLine[]): number =>
    ts.reduce((h, t, i) => h + lines[i].gap + t.displayHeight + 2, 0);
  // 넘치면 한 단계씩 접는다 (꺼진 효과·설명 → 효과·저주 줄)
  let lines = diaryLines(s, 0, r60Text);
  let texts = make(lines);
  for (const level of [1, 2] as const) {
    if (top + height(texts, lines) <= maxH) break;
    for (const t of texts) t.destroy();
    lines = diaryLines(s, level, r60Text);
    texts = make(lines);
  }
  // 그래도 넘치면 들어가는 데까지 + '…'
  let used = top;
  let keep = texts.length;
  for (let i = 0; i < texts.length; i++) {
    const add = lines[i].gap + texts[i].displayHeight + 2;
    if (used + add > maxH - 16) {
      keep = i;
      break;
    }
    used += add;
  }
  if (keep < texts.length) {
    for (const t of texts.slice(keep)) t.destroy();
    texts = texts.slice(0, keep);
    texts.push(new GlowText(scene, 0, 0, '…', 'page_faint').setDepth(1));
    lines = [...lines.slice(0, keep), { text: '…', style: 'faint', gap: 0 }];
    used += 16;
  }
  return {
    h: used,
    place(x: number, y: number): void {
      title.placeCenter(x + w / 2, y);
      let yy = y + title.displayHeight + RULE_GAP;
      rule(scene, x, yy, w).setDepth(1);
      yy += AFTER_RULE;
      texts.forEach((t, i) => {
        yy += lines[i].gap;
        t.setPosition(x, yy);
        yy += t.displayHeight + 2;
      });
    },
  };
}
