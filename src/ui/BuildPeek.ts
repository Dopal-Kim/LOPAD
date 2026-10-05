import Phaser from 'phaser';
import type { UiSnapshot } from '../contract/ui';
import { personalityRatio } from './combatView';
import { GlowText } from './glow';
import { KeyGuide } from './keyGuide';
import { snapshotVerbItems } from './keyGuideView';
import { paperPage, rule } from './kit';
import { buildPage } from './PauseBuild';
import { swatch } from './StructureHud';
import { fill, r60Text, r61Text } from './text';
import { PEEK } from './themeR61';

/** 개성 진행 막대 (종이 위) */
const PERS_BAR = { w: 120, h: 4 } as const;

/**
 * 61라운드 P10 Tab 빌드 보기 — Tab 을 누르고 있는 동안 왼쪽 위에 종이 두 장(게임은 멈추지 않는다, 데드셀 Tab 처럼 훑어보기).
 * 전투 HUD 에서 접은 것을 여기서 본다.
 *  왼쪽 장: 무기 · 갈래 / 개성 n/m + 막대 / 조작 키캡 안내(2단) / 떼면 닫힌다
 *  오른쪽 장: 빌드(태그·세트·이중 개성·저주·패시브·소모품 — 일시정지 일기장 오른쪽 쪽과 같은 글 `buildPage`)
 * 두 장 모두 전투 묶음 위에서 끝난다(체력·자원은 계속 보인다). 노드 지도 층·무기 시험장에서만(그 밖의 층은 Tab = 워프 지도).
 */
export class BuildPeek {
  private box?: Phaser.GameObjects.Container;

  constructor(private scene: Phaser.Scene) {}

  get open(): boolean {
    return Boolean(this.box);
  }

  /** maxBottom = 종이 아래 끝 상한 (전투 묶음 위) */
  show(s: UiSnapshot, si: number, maxBottom: number): void {
    this.hide();
    const sc = this.scene;
    const innerL = PEEK.leftW - PEEK.pad * 2;
    const innerR = PEEK.rightW - PEEK.pad * 2;
    const xL = PEEK.x + PEEK.pad;
    const xR = PEEK.x + PEEK.leftW + PEEK.gap + PEEK.pad;
    const texts: Phaser.GameObjects.GameObject[] = [];
    // ---- 왼쪽 장: 무기 · 개성 · 조작
    let y = PEEK.y + PEEK.top;
    const evo = s.weapon.evolutionName ? ` · ${s.weapon.evolutionName}` : '';
    const name = new GlowText(
      sc,
      xL,
      y,
      fill(r61Text('peekWeapon'), { name: `${s.weapon.name}${evo}` }),
      'page_title',
      {
        stageIndex: si,
        wrap: innerL,
      },
    );
    texts.push(name);
    y += name.displayHeight + 2;
    const pers = new GlowText(
      sc,
      xL,
      y,
      fill(r61Text('peekPersonality'), { n: s.weapon.personality, max: s.weapon.threshold }),
      'page_body',
      { stageIndex: si },
    );
    const bar = sc.add.graphics();
    const bx = xL + pers.displayWidth + 6;
    const barW = Math.max(20, Math.min(PERS_BAR.w, xL + innerL - bx));
    const by = y + Math.round(pers.displayHeight / 2 - PERS_BAR.h / 2);
    const ratio = personalityRatio(s.weapon);
    bar.fillStyle(swatch(sc, si, { sepia: 1 }), 1).fillRect(bx, by, barW, PERS_BAR.h);
    bar.lineStyle(1, swatch(sc, si, { sepia: 3 }), 1).strokeRect(bx + 0.5, by + 0.5, barW - 1, PERS_BAR.h - 1);
    const fw = Math.round(barW * ratio);
    if (fw > 0) bar.fillStyle(swatch(sc, si, { slot: ratio >= 1 ? 25 : 22 }), 1).fillRect(bx, by, fw, PERS_BAR.h);
    texts.push(pers, bar);
    y += pers.displayHeight + 6;
    texts.push(rule(sc, xL, y, innerL));
    y += 4 + 6;
    const head = new GlowText(sc, xL, y, r61Text('peekKeys'), 'page_faint');
    texts.push(head);
    y += head.displayHeight + 2;
    // 조작 키캡 안내 — 시스템 4동사(weaponVerbs)가 있으면 그것, 없으면 지금 조작
    const guide = new KeyGuide(sc, xL + 2, y, 'column', { surface: 'page', stageIndex: si, cols: 2 }).setItems(
      snapshotVerbItems(s, (k) => r61Text(k)),
    );
    texts.push(guide);
    y += guide.boxH + 10;
    const foot = new GlowText(sc, xL, y, r61Text('peekFoot'), 'page_faint', { wrap: innerL });
    texts.push(foot);
    const leftH = y + foot.displayHeight + PEEK.top - PEEK.y;
    // ---- 오른쪽 장: 빌드 (일기장과 같은 글, 남은 높이에 맞춰 접는다)
    const title = new GlowText(sc, 0, 0, r60Text('buildTitle'), 'page_title', { stageIndex: si });
    title.placeCenter(xR + innerR / 2, PEEK.y + PEEK.top);
    let yr = title.y + title.displayHeight + 4;
    texts.push(title, rule(sc, xR, yr, innerR));
    yr += 4 + 6;
    const room = Math.max(60, maxBottom - yr - PEEK.top);
    const page = buildPage(sc, innerR, s, si, room, { title: false });
    page.place(xR, yr);
    texts.push(...page.objects());
    const rightH = yr + page.h + PEEK.top - PEEK.y;
    // 종이를 글 뒤에 깐다 (만든 것을 모아 그릇 하나로 — 놓는 순서: 종이 → 글)
    const before = new Set(sc.children.list);
    paperPage(sc, PEEK.x, PEEK.y, PEEK.leftW, leftH, 'peekL');
    paperPage(sc, PEEK.x + PEEK.leftW + PEEK.gap, PEEK.y, PEEK.rightW, Math.max(rightH, leftH), 'peekR');
    const paper = sc.children.list.filter((o) => !before.has(o));
    this.box = sc.add.container(0, 0, [...paper, ...texts]).setDepth(PEEK.depth);
  }

  hide(): void {
    this.box?.destroy();
    this.box = undefined;
  }

  destroy(): void {
    this.hide();
  }
}
