import Phaser from 'phaser';
import { UI_EVENTS, UI_SCREEN, uiBus, type UiMemoryBook, type UiMemoryEntry } from '../contract/ui';
import type { ChoiceGate } from './choiceGate';
import { armBar, keyTime, leftButton, pointerTime } from './choiceArm';
import { GlowText } from './glow';
import { diamond, traitIconBox, weaponFrameColor } from './growthArt';
import { ICON, accentHex, book, icon, rule } from './kit';
import { playUiSound } from './uiSound';
import { takeKey } from './keyGate';
import {
  focusAt,
  focusIndex,
  memoryAction,
  memoryActionHint,
  memoryDir,
  memoryGlyph,
  memoryLevel,
  memoryRows,
  memoryState,
  moveFocus,
  nextLine,
  recallTarget,
  type MemoryFocus,
  type MemoryRow,
  type RecallMark,
} from './memoryView';
import { fill } from './fmt';
import { l2eText } from './textLoop2E';
import { GRAY, SEPIA, hexToNum } from './theme';
import { MEMORY_UI as M } from './themeLoop2E';
import type { VoiceWeaponId } from './themeStory';

/**
 * 62 루프 2 UI E (계약 C P1-8): 일기장 '기억' 장 — 두 쪽 펼침.
 *  왼쪽 장: '기억' · 머리 문장 · 지닌 영혼 · 다음 기억 한 줄 · 괘선 · 고름 자리 기억(그림 64 · 이름 · 한 문장 · 수치 · 흐린 한 줄 ·
 *          단계 · 상태 · [Enter] 동작) · 떠올림 알림
 *  오른쪽 장: 다섯 칸(소품 · 손이 기억한 모양 · 떠올릴 개성 · 장터에 놓일 것 · 몸의 기억) — 칸마다 그림 32(없으면 이름 한 자) ·
 *            떠올림 ✓ · 지닌 소품 테 · 떠올릴 수 있으면 점 · 몸의 기억은 단계 마름모. 아래 조작 안내.
 * 조작: 방향키·WASD 고르기, Enter·Space 떠올린다 / 지니고 태어난다 / 내려놓는다, 0·Esc 덮기(Esc 는 `handleEsc` 일 때만 —
 * 메뉴 씬은 Esc 를 따로 받는다). 클릭은 같은 칸 위에서 눌렀다 뗀 것만, 무장 게이트(`gate`)를 지난 것만 (UI D 공통 규칙).
 * 쓰는 곳: 메뉴 'meta'(의식 덧쓰기 F2 — MenuScene) · 타이틀 · 결과 화면(덧그림).
 */
export interface MemoryBookOpts {
  stageIndex: number;
  /** 무장 게이트 (없으면 바로 받는다) */
  gate?: ChoiceGate;
  depth?: number;
  /** 다시 그릴 때 지킬 고름 자리 (평평한 번호) */
  keepFocus?: number;
  /** 지금 기억 장 */
  book(): UiMemoryBook | null;
  /** 떠올린다 — true 반영됨 · false 거절 · undefined 메뉴가 다시 그려 준다(메뉴 'meta') */
  recall(id: string): boolean | undefined;
  setKeepsake(id: string | null): boolean;
  close(): void;
  /** Esc 를 이 화면이 받는가 */
  handleEsc: boolean;
  /** MEMORY_CHANGED 로 다시 그린다 (타이틀·결과 — 메뉴 'meta' 는 시스템이 메뉴를 다시 연다) */
  live: boolean;
  /** 뒤를 어둡게 덮는다 */
  backdrop?: boolean;
}

/** 방금 떠올린 기억 (메뉴가 다시 그려도 연출을 이어서) */
let recallMark: RecallMark | null = null;

interface Cell {
  entry: UiMemoryEntry;
  row: number;
  col: number;
  x: number;
  y: number;
  box: Phaser.GameObjects.Container;
  frame: Phaser.GameObjects.Graphics;
}

export class MemoryBookView {
  private root!: Phaser.GameObjects.Container;
  private panel?: Phaser.GameObjects.Container;
  private rows: MemoryRow[] = [];
  private cells: Cell[] = [];
  private focus: MemoryFocus = { r: 0, c: 0 };
  private data: UiMemoryBook | null = null;
  private keepsake: string | null = null;
  private alive = true;
  private version = 0;
  private pressIdx = -1;
  private stopArm?: () => void;
  private panelArea = { x: 0, y: 0, w: 0, bottom: 0 };
  private notice?: GlowText;

  constructor(
    private scene: Phaser.Scene,
    private o: MemoryBookOpts,
  ) {
    this.data = o.book();
    this.keepsake = this.data?.keepsake ?? null;
    this.rows = this.data ? memoryRows(this.data) : [];
    this.focus = focusAt(this.rows, o.keepFocus ?? 0);
    this.build();
    scene.input.keyboard?.on('keydown', this.onKey);
    scene.input.on(Phaser.Input.Events.POINTER_UP, this.onUpAnywhere);
    if (o.live) uiBus.on(UI_EVENTS.MEMORY_CHANGED, this.onChanged);
  }

  /** 지금 고름 자리 (평평한 번호 — 메뉴가 다시 그릴 때 지킨다) */
  focusIndex(): number {
    return focusIndex(this.rows, this.focus);
  }

  destroy(): void {
    if (!this.alive) return;
    this.alive = false;
    this.scene.input.keyboard?.off('keydown', this.onKey);
    this.scene.input?.off(Phaser.Input.Events.POINTER_UP, this.onUpAnywhere);
    uiBus.off(UI_EVENTS.MEMORY_CHANGED, this.onChanged);
    this.stopArm?.();
    this.scene.tweens.killTweensOf(this.root.list);
    this.root.destroy();
  }

  // ---------------------------------------------------------------------------------------------
  // 입력

  private gateKey(e: KeyboardEvent): boolean {
    return !this.o.gate || this.o.gate.keyOk(e.code, keyTime(e), e.repeat);
  }

  private onKey = (e: KeyboardEvent): void => {
    if (!this.alive || e.repeat) return;
    const dir = memoryDir(e.key);
    if (dir) {
      if (!takeKey(e)) return;
      this.setFocus(moveFocus(this.rows, this.focus, dir), true);
      return;
    }
    if (e.key === 'Enter' || e.key === ' ') {
      if (takeKey(e) && this.gateKey(e)) this.act();
      return;
    }
    if (e.key === '0' || (e.key === 'Escape' && this.o.handleEsc)) {
      if (takeKey(e) && this.gateKey(e)) {
        playUiSound(this.scene, 'back');
        this.o.close();
      }
    }
  };

  private onUpAnywhere = (): void => {
    this.pressIdx = -1;
    this.o.gate?.pointerUp();
  };

  private press(i: number, p?: Phaser.Input.Pointer): void {
    if (!leftButton(p)) return;
    this.pressIdx = !this.o.gate || this.o.gate.pressOk(pointerTime(p)) ? i : -1;
  }

  private release(i: number, p?: Phaser.Input.Pointer): void {
    if (!leftButton(p)) return;
    const ok = this.o.gate ? this.o.gate.releaseOk() : true;
    const same = this.pressIdx === i;
    this.pressIdx = -1;
    if (ok && same) this.act();
  }

  private onChanged = (b: UiMemoryBook): void => {
    if (!this.alive) return;
    this.rebuild(b ?? this.o.book());
  };

  /** Enter: 떠올린다 / 지니고 태어난다 / 내려놓는다 (할 것이 없으면 흔들림) */
  private act(): void {
    const cell = this.cellAt(this.focus);
    if (!cell) return;
    const e = cell.entry;
    const a = memoryAction(e, this.keepsake);
    if (a !== 'none') playUiSound(this.scene, 'select');
    if (a === 'recall') {
      recallMark = { id: e.id, at: performance.now() };
      const v = this.version;
      const ok = this.o.recall(e.id);
      if (ok === false) {
        recallMark = null;
        this.shake(cell);
      } else if (ok === true && this.alive && this.version === v) this.rebuild(this.o.book());
      return;
    }
    if (a === 'equip' || a === 'unequip') {
      const id = a === 'equip' ? e.id : null;
      const v = this.version;
      if (!this.o.setKeepsake(id)) return this.shake(cell);
      this.keepsake = id;
      if (this.alive && this.version === v) this.rebuild(this.o.book());
      return;
    }
    this.shake(cell);
  }

  private shake(cell: Cell): void {
    this.scene.tweens.killTweensOf(cell.box);
    cell.box.setX(cell.x);
    this.scene.tweens.add({
      targets: cell.box,
      x: { from: cell.x - 2, to: cell.x + 2 },
      duration: 50,
      yoyo: true,
      repeat: 1,
      onComplete: () => cell.box.setX(cell.x),
    });
  }

  // ---------------------------------------------------------------------------------------------
  // 그리기

  private rebuild(b: UiMemoryBook | null): void {
    const keep = this.focusIndex();
    this.version++;
    this.stopArm?.();
    this.stopArm = undefined;
    this.scene.tweens.killTweensOf(this.root.list);
    this.root.destroy();
    this.panel = undefined;
    this.notice = undefined;
    this.cells = [];
    this.data = b;
    this.keepsake = b?.keepsake ?? this.keepsake;
    this.rows = b ? memoryRows(b) : [];
    this.focus = focusAt(this.rows, keep);
    this.build();
  }

  private build(): void {
    const sc = this.scene;
    const W = UI_SCREEN.WIDTH;
    const H = UI_SCREEN.HEIGHT;
    const si = this.o.stageIndex;
    const before = new Set(sc.children.list);
    if (this.o.backdrop) sc.add.rectangle(0, 0, W, H, hexToNum(GRAY[0]), M.backdrop).setOrigin(0, 0).setInteractive();
    const bk = book(sc, Math.round(W / 2), Math.round(H / 2), M.pageW, M.pageH, 2, 'memory');
    const L = bk.pages[0];
    const R = bk.pages[1];
    const innerW = M.pageW - M.pad * 2;
    const b = this.data;
    // ---- 왼쪽 장: 제목 · 머리 문장 · 영혼 · 다음 기억
    let y = L.y + 14;
    const title = new GlowText(sc, 0, 0, b?.title || l2eText('bookTitle'), 'page_title', { scale: 2, stageIndex: si });
    title.placeCenter(L.x + M.pageW / 2, y);
    y += title.displayHeight + 6;
    for (const line of b?.intro ?? []) {
      const t = new GlowText(sc, L.x + M.pad, y, line, 'page_body', { wrap: innerW, stageIndex: si });
      y += t.displayHeight + 2;
    }
    y += 6;
    icon(sc, L.x + M.pad, y, ICON.souls);
    const souls = new GlowText(sc, L.x + M.pad + 22, y, b?.soulsText ?? '', 'page_title', { stageIndex: si });
    y += Math.max(18, souls.displayHeight) + 2;
    new GlowText(sc, L.x + M.pad, y, nextLine(b?.next ?? null), 'page_faint', { wrap: innerW });
    y += 18;
    rule(sc, L.x + M.pad, y, innerW);
    const ruleY = y;
    y += 4 + 10;
    this.panelArea = { x: L.x + M.pad, y, w: innerW, bottom: L.y + M.pageH - M.pad - 18 };
    // ---- 오른쪽 장: 다섯 칸
    let ry = R.y + 16;
    this.rows.forEach((row, r) => {
      new GlowText(sc, R.x + M.pad, ry, row.name, 'page_faint', { stageIndex: si });
      ry += M.headH;
      row.entries.forEach((e, c) => {
        this.cells.push(this.cell(e, r, c, R.x + M.pad + c * (M.cell + M.cellGap), ry));
      });
      ry += M.cell + (row.kind === 'stat' ? 8 : 0) + M.rowGap;
    });
    const hint = new GlowText(sc, 0, 0, l2eText('bookHint'), 'page_faint');
    hint.placeCenter(R.x + M.pageW / 2, R.y + M.pageH - M.pad - hint.displayHeight + 4);
    const made = sc.children.list.filter((x) => !before.has(x));
    this.root = sc.add.container(0, 0, made).setDepth(this.o.depth ?? 0);
    this.paintCells();
    this.drawPanel();
    // 무장 진행 (UI D 공통 — 괘선 위로 차오르는 선)
    const g = this.o.gate;
    if (g && !g.armed(performance.now()))
      this.stopArm = armBar(
        sc,
        g,
        L.x + M.pad,
        ruleY + 1,
        innerW,
        hexToNum(accentHex(sc, si, 20)),
        (this.o.depth ?? 0) + 1,
      );
    // 방금 떠올린 칸 연출
    const target = recallTarget(recallMark, this.rows, performance.now(), M.recallWindowMs);
    if (target) {
      recallMark = null;
      const cell = this.cells.find((x) => x.entry.id === target);
      if (cell) this.recallFx(cell);
    }
  }

  /** 오른쪽 장 칸 하나 (버튼 규약: Container → Graphics → 그림·글) */
  private cell(e: UiMemoryEntry, r: number, c: number, x: number, y: number): Cell {
    const sc = this.scene;
    const s = M.cell;
    const g = sc.add.graphics();
    const lit = e.unlocked || (e.level?.n ?? 0) > 0;
    g.fillStyle(hexToNum(lit ? GRAY[1] : SEPIA[1]), 1).fillRect(0, 0, s, s);
    const parts: Phaser.GameObjects.GameObject[] = [g];
    const pad = Math.round((s - M.icon) / 2);
    const key = e.iconKey;
    const img = key && sc.textures.exists(key) ? sc.add.image(pad, pad, key).setOrigin(0, 0) : null;
    if (img) {
      img.setScale(M.icon / Math.max(1, img.width, img.height));
      img.setAlpha(lit ? 1 : e.affordable ? 0.85 : 0.38);
      parts.push(img);
    } else {
      const t = new GlowText(sc, 0, 0, memoryGlyph(e), lit ? 'page_selected' : 'page_faint', { scale: 2 });
      t.setPosition(Math.round(s / 2 - t.displayWidth / 2), Math.round(s / 2 - t.displayHeight / 2));
      parts.push(t);
    }
    const marks = sc.add.graphics();
    parts.push(marks);
    // 떠올림 ✓ (몸의 기억은 단계 마름모)
    if (e.kind === 'stat' && e.level) {
      const pr = 2;
      const step = pr * 2 + 3;
      const x0 = Math.round(s / 2 - ((e.level.max - 1) * step) / 2);
      const on = hexToNum(accentHex(sc, this.o.stageIndex, M.recalledSlot));
      for (let k = 0; k < e.level.max; k++)
        diamond(marks, x0 + k * step, s + 5, pr, k < e.level.n ? on : hexToNum(SEPIA[4]), k < e.level.n);
    } else if (e.unlocked) {
      marks.fillStyle(hexToNum(accentHex(sc, this.o.stageIndex, M.recalledSlot)), 1).fillRect(s - 9, s - 9, 7, 7);
      marks.lineStyle(1, hexToNum(GRAY[0]), 1);
      marks.beginPath();
      marks.moveTo(s - 8, s - 6);
      marks.lineTo(s - 6, s - 4);
      marks.lineTo(s - 3, s - 8);
      marks.strokePath();
    }
    // 떠올릴 수 있으면 오른쪽 위 점
    if (e.affordable && !e.unlocked)
      marks.fillStyle(hexToNum(accentHex(sc, this.o.stageIndex, M.readySlot)), 1).fillRect(s - 6, 2, 4, 4);
    const frame = sc.add.graphics();
    parts.push(frame);
    const box = sc.add.container(x, y, parts).setSize(s, s);
    box.setInteractive(new Phaser.Geom.Rectangle(s / 2, s / 2, s, s), Phaser.Geom.Rectangle.Contains);
    if (box.input) box.input.cursor = 'pointer';
    const index = this.cells.length;
    box.on('pointerover', () => this.setFocus({ r, c }, true));
    box.on('pointerdown', (p: Phaser.Input.Pointer) => this.press(index, p));
    box.on('pointerup', (p: Phaser.Input.Pointer) => this.release(index, p));
    return { entry: e, row: r, col: c, x, y, box, frame };
  }

  private cellAt(f: MemoryFocus): Cell | undefined {
    return this.cells.find((x) => x.row === f.r && x.col === f.c);
  }

  private setFocus(f: MemoryFocus, sound = false): void {
    if (f.r === this.focus.r && f.c === this.focus.c) return;
    this.focus = f;
    if (sound) playUiSound(this.scene, 'move');
    this.paintCells();
    this.drawPanel();
  }

  private paintCells(): void {
    const sc = this.scene;
    const si = this.o.stageIndex;
    const s = M.cell;
    for (const cell of this.cells) {
      const e = cell.entry;
      const sel = cell.row === this.focus.r && cell.col === this.focus.c;
      const equipped = e.kind === 'keepsake' && e.unlocked && this.keepsake === e.id;
      const f = cell.frame.clear();
      if (sel) f.lineStyle(2, hexToNum(accentHex(sc, si, M.focusSlot)), 1).strokeRect(-1, -1, s + 2, s + 2);
      else if (equipped)
        f.lineStyle(2, hexToNum(accentHex(sc, si, M.equippedSlot)), 1).strokeRect(-1, -1, s + 2, s + 2);
      else if (e.unlocked)
        f.lineStyle(1, hexToNum(accentHex(sc, si, M.recalledSlot)), 1).strokeRect(0.5, 0.5, s - 1, s - 1);
      else f.lineStyle(1, hexToNum(e.affordable ? SEPIA[5] : SEPIA[3]), 1).strokeRect(0.5, 0.5, s - 1, s - 1);
      // 지닌 소품: 안쪽 한 줄 더
      if (equipped && sel)
        f.lineStyle(1, hexToNum(accentHex(sc, si, M.equippedSlot)), 1).strokeRect(2.5, 2.5, s - 5, s - 5);
      cell.box.setY(sel ? cell.y - 2 : cell.y);
    }
  }

  /** 왼쪽 장 아래: 고름 자리 기억 */
  private drawPanel(): void {
    this.panel?.destroy();
    const cell = this.cellAt(this.focus);
    if (!cell) return;
    const sc = this.scene;
    const si = this.o.stageIndex;
    const e = cell.entry;
    const A = this.panelArea;
    const objs: Phaser.GameObjects.GameObject[] = [];
    const size = M.focusIcon;
    const weapon = (
      e.weapon && ['katana', 'greatsword', 'dagger', 'bow'].includes(e.weapon) ? e.weapon : null
    ) as VoiceWeaponId | null;
    const frameColor = weapon ? weaponFrameColor(sc, weapon) : hexToNum(SEPIA[5]);
    const art = traitIconBox(sc, e.iconKey, A.x + 3, A.y + 3, size, frameColor, 2, hexToNum(GRAY[1]));
    if (art) objs.push(...art);
    else {
      const g = sc.add.graphics();
      g.fillStyle(hexToNum(GRAY[1]), 1).fillRect(A.x + 3, A.y + 3, size, size);
      g.lineStyle(2, frameColor, 1).strokeRect(A.x + 2, A.y + 2, size + 2, size + 2);
      const t = new GlowText(sc, 0, 0, memoryGlyph(e), 'ink_accent', { scale: 2, stageIndex: si });
      t.setPosition(
        Math.round(A.x + 3 + size / 2 - t.displayWidth / 2),
        Math.round(A.y + 3 + size / 2 - t.displayHeight / 2),
      );
      objs.push(g, t);
    }
    const tx = A.x + size + 14;
    const tw = A.w - size - 14;
    let ty = A.y;
    const chapter = this.rows[cell.row]?.name ?? '';
    const head = new GlowText(sc, tx, ty, [chapter, e.weaponName].filter(Boolean).join(' · '), 'page_faint', {
      wrap: tw,
    });
    ty += head.displayHeight + 2;
    const name = new GlowText(sc, tx, ty, e.name, 'page_title', { wrap: tw, stageIndex: si });
    ty += name.displayHeight + 2;
    const level = memoryLevel(e);
    objs.push(head, name);
    if (level) {
      const lv = new GlowText(sc, tx, ty, level, 'page_body', { stageIndex: si });
      objs.push(lv);
      ty += lv.displayHeight;
    }
    let y = Math.max(ty, A.y + size + 6) + 6;
    const add = (text: string | undefined, style: 'page_body' | 'page_faint' | 'page_selected'): void => {
      if (!text) return;
      const t = new GlowText(sc, A.x, y, text, style, { wrap: A.w, stageIndex: si });
      objs.push(t);
      y += t.displayHeight + 3;
    };
    add(e.line, 'page_body');
    add(e.detail, 'page_faint');
    add(e.flavor, 'page_faint');
    y += 4;
    const a = memoryAction(e, this.keepsake);
    add(memoryState(e, this.keepsake), a === 'recall' ? 'page_selected' : 'page_faint');
    add(memoryActionHint(a), 'page_body');
    this.panel = sc.add.container(0, 0, objs);
    this.root.add(this.panel);
  }

  /** 떠올리기 연출: 칸에서 먹 고리가 번지고 칸이 한 번 튀어 오르며, 왼쪽 장 아래에 '떠올렸다 — …' */
  private recallFx(cell: Cell): void {
    const sc = this.scene;
    const si = this.o.stageIndex;
    const cx = cell.x + M.cell / 2;
    const cy = cell.y + M.cell / 2;
    const ring = sc.add.graphics();
    this.root.add(ring);
    const v = { t: 0 };
    sc.tweens.add({
      targets: v,
      t: 1,
      duration: M.ringMs,
      ease: 'Cubic.easeOut',
      onUpdate: () => {
        const r = 6 + (M.ringR - 6) * v.t;
        ring.clear();
        ring.lineStyle(3 * (1 - v.t) + 1, hexToNum(accentHex(sc, si, M.recalledSlot)), 1 - v.t);
        ring.strokeCircle(cx, cy, r);
        ring.fillStyle(hexToNum(GRAY[0]), 0.35 * (1 - v.t)).fillCircle(cx, cy, r * 0.6);
      },
      onComplete: () => ring.destroy(),
    });
    // 칸 튀어 오름 (가운데 기준 — 컨테이너 원점이 왼쪽 위라 위치를 같이 옮긴다)
    const k = { s: M.popScale };
    sc.tweens.add({
      targets: k,
      s: 1,
      duration: M.popMs,
      ease: 'Back.easeOut',
      onUpdate: () => {
        cell.box.setScale(k.s);
        cell.box.setPosition(Math.round(cx - (M.cell * k.s) / 2), Math.round(cy - (M.cell * k.s) / 2) - 2);
      },
      onComplete: () => {
        cell.box.setScale(1);
        this.paintCells();
      },
    });
    const A = this.panelArea;
    this.notice?.destroy();
    const n = new GlowText(sc, A.x, A.bottom, fill(l2eText('recalled'), { name: cell.entry.name }), 'page_selected', {
      wrap: A.w,
      stageIndex: si,
    });
    n.setY(A.bottom - n.displayHeight + 14).setAlpha(0);
    this.root.add(n);
    this.notice = n;
    sc.tweens.chain({
      targets: n,
      tweens: [
        { alpha: 1, duration: 220 },
        { alpha: 0, delay: M.noticeMs, duration: 400 },
      ],
    });
  }
}
