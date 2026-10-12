import Phaser from 'phaser';
import { GlowText, type GlowOptions } from './glow';
import { fill } from './fmt';
import { growthText, r53Text, r60Text, routeText, structText } from './text';
import type { TextStyleName } from './theme';

/**
 * 62 루프 2 UI D (렉): 런 시작(HUD 가 뜬 뒤 글꼴이 다 읽힌 때) 선택 메뉴에 늘 나오는 글을 미리 구워 둔다 (glyphCache.ts 풀에 남는다).
 * 글꼴 높이 측정(두 글꼴)도 여기서 끝난다 — 메뉴가 처음 열리는 순간에는 이미 구운 텍스처를 빌리기만 한다.
 * 한 프레임에 `PER_FRAME` 개씩 나눠 굽는다 (런 시작 화면이 멈칫하지 않게). 게임 하나에 한 번.
 */
const PER_FRAME = 4;
/** HUD 가 그려진 뒤 굽기 시작까지 (ms) — 탄생·전환 연출이 시작하는 프레임을 피한다 */
const START_DELAY_MS = 600;

const warmed = new WeakSet<Phaser.Game>();

type Item = [string, TextStyleName, GlowOptions?];

function items(): Item[] {
  const keys = ['1', '2', '3', '4', '0'].map((k): Item => [`[${k}]`, 'page_body']);
  return [
    ...keys,
    [growthText('headTrait'), 'ink_body'],
    [growthText('headAwaken1'), 'ink_body'],
    [growthText('headAwaken2'), 'ink_body'],
    [growthText('headTemper'), 'ink_body'],
    [growthText('guideNext'), 'page_faint'],
    [growthText('pathsHead'), 'page_faint'],
    [fill(r60Text('choiceHint'), { keys: '1·2·3' }), 'page_faint'],
    [fill(r60Text('choiceHint'), { keys: '1·2' }), 'page_faint'],
    [structText('menuClose'), 'page_body'],
    [r53Text('escStay'), 'ink_faint'],
    [routeText('mapTitle'), 'page_title', { font: 'title' }],
    [routeText('choosePrompt'), 'page_selected'],
  ];
}

/** HUD 씬 create 에서 부른다 */
export function warmUi(scene: Phaser.Scene): void {
  if (warmed.has(scene.game)) return;
  warmed.add(scene.game);
  const list = items().filter(([t]) => typeof t === 'string' && t.length > 0);
  let i = 0;
  const step = (): void => {
    if (!scene.sys.isActive()) {
      // HUD 가 꺼졌으면 다음 HUD 에서 다시
      warmed.delete(scene.game);
      return;
    }
    for (let n = 0; n < PER_FRAME && i < list.length; n++, i++) {
      const [text, style, opts] = list[i];
      new GlowText(scene, -1000, -1000, text, style, opts).setVisible(false).destroy();
    }
    if (i < list.length) scene.time.delayedCall(0, step);
  };
  scene.time.delayedCall(START_DELAY_MS, step);
}
