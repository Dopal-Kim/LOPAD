import Phaser from 'phaser';
import { UI_SCREEN, uiCommands, type UiRitual } from '../contract/ui';
import { debugExpose } from './debug';
import { GlowText } from './glow';
import { ICON, KIT, book, fontFamily, icon } from './kit';
import { BrushName, InkText, darkBackdrop, hintRow, inkBleed, ritualButton, ritualMeta, ritualTex } from './ritualArt';
import { clampName, newCharIndexes } from './ritualView';
import { swatch } from './StructureHud';
import { fill } from './fmt';
import { ritualText } from './textRitual';
import { RITUAL_UI as R } from './themeRitual';
import { SEPIA, hexToNum } from './theme';
import type { RitualPage } from './RitualScene';

/** art §30 diary_first_page.json 에서 쓰는 값 */
interface PageMeta {
  size?: { w: number; h: number };
  placement?: { x: number; y: number };
  nameField: { x: number; y: number; w: number; h: number };
  nameBaselineY?: number;
  nameLabel?: { x: number; y: number; w: number; h: number };
  bodyArea?: { x: number; y: number; w: number; h: number };
  bodyLines?: number[];
}

/** 이름 글씨 (붓 스탬프 BrushName 또는 글꼴 InkText) */
interface NameInk {
  setText(v: string, animate: boolean): void;
  readonly textW: number;
  prefixW(n: number): number;
}

function inkTextName(t: InkText): NameInk {
  return {
    setText: (v) => void t.setText(v),
    get textW() {
      return t.textW;
    },
    prefixW: (n) => t.prefixW(n),
  };
}

/**
 * 62 루프 1 P0-2 이름 장 (계약 §20 phase 'name' · 'rewrite') — 일기장 첫 장 '이름 칸'에 붓글씨로 써진다.
 * 브라우저 기본 입력칸은 보이지 않는다: 숨은 `<input>` 이 글(한글 조합 포함)을 받고, 화면에는 먹 글씨(InkText)와 붓끝 커서를 그린다.
 * 숨은 칸은 이름 칸 위에 투명하게 겹쳐 두어 IME 후보 창이 칸 옆에 뜬다. 새 글자마다 먹이 번진다.
 *  - name: 일기장 줄(`lines`) · '이름' 칸 · [Enter] 적는다 → `ritual.submitName`
 *  - rewrite(두 번째 생부터): 지난 이름이 번진 채 칸에 남고 새 이름을 그 위에 덧쓴다. [Enter] 덧쓴다 → submitName,
 *    [redraw.key](지금 Tab) 획을 다시 긋는다 → `ritual.redraw`, [meta.key](지금 F2) 영혼 강화 귀퉁이 → `ritual.openMeta`
 *    (키는 스냅샷 값 — 글자 키가 오면 이름을 고치기 시작하기 전에만 단축키)
 */
export class RitualNamePage implements RitualPage {
  private root: Phaser.GameObjects.Container;
  private el?: HTMLInputElement;
  private ink!: NameInk;
  private placeholder!: GlowText;
  private caret!: Phaser.GameObjects.Graphics;
  private field = { x: 0, y: 0, w: 0, h: 0 };
  private value = '';
  private composing = false;
  /** rewrite: 이름을 고치기 시작했다 (그 뒤의 R 은 글자) */
  private editing = false;
  private sent = false;
  private maxLen = 8;
  private phase: 'name' | 'rewrite';
  private blocked = false;

  constructor(
    private scene: Phaser.Scene,
    r: UiRitual,
  ) {
    this.phase = r.phase === 'rewrite' ? 'rewrite' : 'name';
    this.keys = { redraw: r.redraw?.key, meta: r.meta?.key };
    this.root = scene.add.container(0, 0).setDepth(R.depth);
    this.build(r);
    this.mountInput(r);
  }

  update(r: UiRitual): void {
    // 같은 단계 안에서 바뀌는 것은 영혼 귀퉁이뿐 (메뉴에서 샀을 때)
    this.keys = { redraw: r.redraw?.key, meta: r.meta?.key };
    if (this.phase === 'rewrite') this.drawMeta(r);
  }

  /** 다른 화면(영혼 강화 메뉴)이 떠 있으면 입력을 놓는다 */
  setBlocked(b: boolean): void {
    if (b === this.blocked) return;
    this.blocked = b;
    if (b) this.el?.blur();
    else this.focus();
  }

  tick(now: number): void {
    const on = !this.sent && Math.floor(now / R.page.caretBlinkMs) % 2 === 0;
    this.caret.setVisible(on && !this.blocked);
  }

  /** 장면 단위 키 (숨은 칸이 받지 못한 경우 — 칸이 포커스를 잃었을 때) */
  key(e: KeyboardEvent): boolean {
    if (this.blocked || this.sent) return false;
    if (e.key === 'Enter') {
      this.submit();
      return true;
    }
    if (this.phase === 'rewrite' && this.keys.redraw && e.key.toLowerCase() === this.keys.redraw.toLowerCase()) {
      this.redraw();
      return true;
    }
    if (this.phase === 'rewrite' && this.keys.meta && e.key.toLowerCase() === this.keys.meta.toLowerCase()) {
      this.openMeta();
      return true;
    }
    return false;
  }

  destroy(): void {
    this.unmountInput();
    this.scene.tweens.killTweensOf(this.root.list);
    this.root.destroy();
  }

  // ---- 그림

  private build(r: UiRitual): void {
    const sc = this.scene;
    const P = R.page;
    const W = UI_SCREEN.WIDTH;
    this.root.add(darkBackdrop(sc, R.dimAlpha));
    const before = new Set(sc.children.list);
    const art = ritualTex(sc, 'page');
    const meta = art ? ritualMeta<PageMeta>(sc, 'page') : null;
    let pageBottom: number;
    if (art && meta?.nameField) {
      // art §30 일기장 첫 장 (1배) — json 자리(placement·nameField·nameBaselineY·nameLabel·bodyArea·bodyLines)대로
      const px = meta.placement?.x ?? Math.round(W / 2 - (meta.size?.w ?? 360) / 2);
      const py = meta.placement?.y ?? 44;
      sc.add.image(px, py, art).setOrigin(0, 0);
      pageBottom = py + (meta.size?.h ?? 420);
      const nf = meta.nameField;
      this.field = { x: px + nf.x, y: py + nf.y, w: nf.w, h: nf.h };
      const nl = meta.nameLabel ?? { x: 36, y: 160, w: 70, h: 28 };
      const label = new GlowText(sc, 0, 0, ritualText('nameLabel'), 'page_body');
      label.setPosition(px + nl.x, py + nl.y + Math.round((nl.h - label.displayHeight) / 2));
      this.bodyLines(r.lines ?? [], px, py, meta);
      // 밑줄: 빛나는 먹 S5 (nameField.y + h − 6)
      sc.add.rectangle(this.field.x, this.field.y + nf.h - 6, nf.w, 1, hexToNum(SEPIA[5]), 0.7).setOrigin(0, 0);
      const base = (meta.nameBaselineY ?? nf.y + nf.h - 9) - nf.y;
      if (this.phase === 'rewrite' && r.name?.lastName) this.smudged(r.name.lastName, base);
      this.placeholder = new GlowText(
        sc,
        this.field.x + 6,
        this.field.y + base - 14,
        ritualText('namePlaceholder'),
        'page_faint',
      );
      this.ink = sc.textures.exists(R.art.brush)
        ? new BrushName(sc, this.field.x, this.field.y, nf.w, nf.h, base)
        : inkTextName(new InkText(sc, this.field.x + 4, this.field.y + base - 26, '', P.inkScale));
    } else {
      // 그림이 없을 때: 키트 책 한 장
      const py = book(sc, W / 2, P.cy, P.w, P.h, 1, `ritual:${this.phase}`).pages[0].y;
      pageBottom = py + P.h;
      let y = py + P.pad;
      for (const line of r.lines ?? []) {
        const t = new GlowText(sc, 0, 0, line, 'page_body', { wrap: P.w - P.pad * 2, align: 'center' });
        t.placeCenter(W / 2, y);
        y += t.displayHeight + 4;
      }
      const fx = Math.round(W / 2 - P.fieldW / 2);
      const fy = Math.max(py + P.fieldTop, y + 18);
      const label = new GlowText(sc, 0, 0, ritualText('nameLabel'), 'page_title');
      label.setPosition(fx - label.displayWidth - 12, fy + 14);
      sc.add.tileSprite(fx, fy + 34, P.fieldW, 4, KIT.rule).setOrigin(0, 0);
      this.field = { x: fx, y: fy, w: P.fieldW, h: 30 };
      if (this.phase === 'rewrite' && r.name?.lastName) this.smudged(r.name.lastName, 26);
      this.placeholder = new GlowText(sc, fx + 6, fy + 10, ritualText('namePlaceholder'), 'page_faint');
      this.ink = inkTextName(new InkText(sc, fx + 4, fy, '', P.inkScale));
    }
    this.caret = sc.add.graphics();
    const made = sc.children.list.filter((o) => !before.has(o));
    this.root.add(made);
    // 아래 안내 (책 아래 잉크 위) — 단추로 그린 키(획 다시 긋기·영혼 강화)는 줄에서 뺀다
    const omit = this.phase === 'rewrite' ? [r.redraw?.key, r.meta?.key].filter((k): k is string => Boolean(k)) : [];
    this.root.add(hintRow(sc, r.hint, W / 2, UI_SCREEN.HEIGHT - R.hintBottom, 'ink', omit));
    if (this.phase === 'rewrite') this.buildRewriteButtons(r, pageBottom);
    this.drawMeta(r);
    this.setValue(clampName(r.name?.value ?? '', r.name?.maxLen ?? this.maxLen), false);
  }

  /** 일기장 본문 줄: bodyArea 폭으로 줄바꿈해 괘선(bodyLines = 글자 바닥선)마다 한 줄 */
  private bodyLines(lines: string[], px: number, py: number, meta: PageMeta): void {
    const sc = this.scene;
    const area = meta.bodyArea ?? { x: 40, y: 222, w: 270, h: 128 };
    const rules = meta.bodyLines ?? [236, 262, 288, 314, 340];
    const probe = sc.add.text(0, 0, '', {
      fontFamily: fontFamily('body'),
      fontSize: '11px',
      wordWrap: { width: area.w - 4, useAdvancedWrap: true },
    });
    const wrapped = lines.flatMap((l) => probe.getWrappedText(l));
    probe.destroy();
    wrapped.slice(0, rules.length).forEach((l, i) => {
      const t = new GlowText(sc, 0, 0, l, 'page_body');
      t.setPosition(px + area.x, py + rules[i] - t.displayHeight + 3);
    });
  }

  /** 번진 지난 이름: 흐린 글씨(page_faint 2배) + 가로 먹 획(마른 붓 dry_d4_r0 — 없으면 얼룩 줄). base = 칸 안 바닥선 */
  private smudged(name: string, base: number): void {
    const sc = this.scene;
    const t = new GlowText(sc, this.field.x + 4, 0, name, 'page_faint', { scale: 2, font: 'title' });
    // 새 이름과 같은 바닥선 (붓 글씨 28px 의 바닥에 맞춤)
    t.setY(this.field.y + base - t.displayHeight + 10);
    const w = t.displayWidth;
    const mid = Math.round(t.y + t.displayHeight / 2);
    if (sc.textures.exists(R.art.brush)) {
      for (let k = 0; k < w; k += 3)
        sc.add
          .image(this.field.x + 4 + k, mid + (Math.floor(k / 14) % 2), R.art.brush, 'dry_d4_r0')
          .setTint(R.stamp.ink)
          .setAlpha(0.85);
      return;
    }
    const g = sc.add.graphics();
    g.fillStyle(hexToNum(R.ink), 0.6);
    for (let k = 0; k < w; k += 4) g.fillRect(this.field.x + 4 + k, mid + (Math.floor(k / 12) % 2), 4, 2);
  }

  /** 덧쓰기 장: 책 아래 '획을 다시 긋는다' 단추 (키캡 = 시스템 key) */
  private buildRewriteButtons(r: UiRitual, pageBottom: number): void {
    if (!r.redraw) return;
    const b = ritualButton(this.scene, 0, 0, r.redraw.key, r.redraw.label, () => this.redraw());
    b.box.setPosition(Math.round(UI_SCREEN.WIDTH / 2 - b.w / 2), pageBottom + 22);
    this.root.add(b.box);
  }

  private metaBox?: Phaser.GameObjects.Container;
  private metaSig = '';

  /** 영혼 강화 귀퉁이 (오른쪽 위, rewrite 만): [Tab] 영혼 강화 · 영혼 n — 살 수 있으면 강조 */
  private drawMeta(r: UiRitual): void {
    const m = this.phase === 'rewrite' ? r.meta : undefined;
    const sig = m ? `${m.key}|${m.label}|${m.souls}|${m.canBuy}` : '';
    if (sig === this.metaSig) return;
    this.metaSig = sig;
    this.metaBox?.destroy();
    this.metaBox = undefined;
    if (!m) return;
    const sc = this.scene;
    const b = ritualButton(sc, 0, 0, m.key, m.label, () => this.openMeta(), m.canBuy);
    const souls = icon(sc, 0, 4, ICON.souls);
    const n = new GlowText(
      sc,
      0,
      4,
      fill(ritualText('metaSouls'), { souls: m.souls }),
      m.canBuy ? 'ink_accent' : 'ink_faint',
    );
    const x = UI_SCREEN.WIDTH - 16 - b.w;
    b.box.setPosition(x, 14);
    souls.setPosition(x - 8 - n.displayWidth - 18, 18);
    n.setPosition(x - 8 - n.displayWidth, 18);
    const parts: Phaser.GameObjects.GameObject[] = [b.box, souls, n];
    if (m.canBuy) {
      const dot = sc.add.graphics();
      dot.fillStyle(swatch(sc, 0, { slot: 25 }), 1).fillRect(x + b.w - 5, 12, 4, 4);
      parts.push(dot);
    }
    this.metaBox = sc.add.container(0, 0, parts);
    this.root.add(this.metaBox);
  }

  // ---- 숨은 입력칸 (IME)

  private mountInput(r: UiRitual): void {
    if (typeof document === 'undefined') return;
    this.maxLen = Math.max(1, r.name?.maxLen ?? this.maxLen);
    const el = document.createElement('input');
    el.type = 'text';
    el.autocomplete = 'off';
    el.spellcheck = false;
    el.setAttribute('aria-label', ritualText('nameLabel'));
    el.maxLength = this.maxLen + 2;
    el.value = this.value;
    Object.assign(el.style, {
      position: 'fixed',
      opacity: '0',
      border: '0',
      padding: '0',
      margin: '0',
      outline: 'none',
      background: 'transparent',
      color: 'transparent',
      caretColor: 'transparent',
      fontSize: '16px',
      zIndex: '5',
    } satisfies Partial<CSSStyleDeclaration>);
    document.body.appendChild(el);
    this.el = el;
    this.placeInput();
    el.addEventListener('input', this.onInput);
    el.addEventListener('compositionstart', this.onCompStart);
    el.addEventListener('compositionend', this.onCompEnd);
    el.addEventListener('keydown', this.onKeyDown);
    el.addEventListener('blur', this.onBlur);
    this.scene.input.on('pointerdown', this.onPointer);
    this.scene.scale.on(Phaser.Scale.Events.RESIZE, this.placeInput);
    // 숨은 칸에 글을 치는 동안 게임 키 잡기(preventDefault)가 글자를 막지 않게
    this.scene.input.keyboard?.disableGlobalCapture();
    // 앞 장을 넘긴 키(첫 생 선택 '2' 등)가 같은 순간 칸에 글자로 들어가지 않게 한 박자 뒤에 포커스
    this.scene.time.delayedCall(R.page.focusDelayMs, () => this.focus());
  }

  private unmountInput(): void {
    const el = this.el;
    this.el = undefined;
    this.scene.input?.off('pointerdown', this.onPointer);
    this.scene.scale?.off(Phaser.Scale.Events.RESIZE, this.placeInput);
    this.scene.input?.keyboard?.enableGlobalCapture();
    if (!el) return;
    el.removeEventListener('input', this.onInput);
    el.removeEventListener('compositionstart', this.onCompStart);
    el.removeEventListener('compositionend', this.onCompEnd);
    el.removeEventListener('keydown', this.onKeyDown);
    el.removeEventListener('blur', this.onBlur);
    el.remove();
  }

  /** 숨은 칸을 화면의 이름 칸 위에 겹친다 (IME 후보 창 자리) */
  private placeInput = (): void => {
    const el = this.el;
    const canvas = this.scene.game.canvas;
    if (!el || !canvas) return;
    const rect = canvas.getBoundingClientRect();
    const k = rect.width / UI_SCREEN.WIDTH;
    el.style.left = `${Math.round(rect.left + this.field.x * k)}px`;
    el.style.top = `${Math.round(rect.top + this.field.y * k)}px`;
    el.style.width = `${Math.round(this.field.w * k)}px`;
    el.style.height = `${Math.round(this.field.h * k)}px`;
  };

  private focus(): void {
    if (!this.el || this.sent || this.blocked) return;
    this.el.focus({ preventScroll: true });
  }

  private onPointer = (): void => {
    // 캔버스를 누르면 포커스가 캔버스로 가므로 다음 틀에 칸으로 되돌린다
    this.scene.time.delayedCall(0, () => this.focus());
  };

  private onBlur = (): void => {
    this.scene.time?.delayedCall(30, () => this.focus());
  };

  private onCompStart = (): void => {
    this.composing = true;
  };

  private onCompEnd = (): void => {
    this.composing = false;
    this.onInput();
  };

  private onInput = (): void => {
    const el = this.el;
    if (!el || this.sent) return;
    const v = clampName(el.value, this.maxLen);
    // 조합 중에 값을 바꾸면 IME 가 깨지므로 조합이 끝난 뒤에만 잘라 쓴다
    if (!this.composing && v !== el.value) el.value = v;
    if (v !== this.value) this.editing = true;
    this.setValue(v, true);
  };

  private onKeyDown = (e: KeyboardEvent): void => {
    // 칸에서 친 키는 게임(Phaser) 키 처리로 넘기지 않는다
    e.stopPropagation();
    if (this.sent || this.blocked) return;
    const composing = this.composing || e.isComposing || e.keyCode === 229;
    if (e.key === 'Enter' && !composing) {
      e.preventDefault();
      this.submit();
      return;
    }
    if (this.phase !== 'rewrite' || composing) return;
    // 키는 시스템이 정한 것(스냅샷 redraw.key · meta.key — 지금 Tab · F2). 글자 키면 이름을 고치기 전에만
    const printable = (k: string): boolean => k.length === 1;
    const hit = (k: string | undefined): boolean =>
      Boolean(k) && e.key.toLowerCase() === k!.toLowerCase() && (!printable(k!) || !this.editing);
    if (hit(this.keys.redraw)) {
      e.preventDefault();
      this.redraw();
    } else if (hit(this.keys.meta)) {
      e.preventDefault();
      this.openMeta();
    }
  };

  /** rewrite 단추 키 (시스템 값) */
  private keys: { redraw?: string; meta?: string } = {};

  private setValue(v: string, bleed: boolean): void {
    const prev = this.value;
    this.value = v;
    this.ink.setText(v, bleed);
    this.placeholder.setVisible(v.length === 0);
    const P = R.page;
    const cx = this.field.x + 4 + this.ink.textW + 2;
    // 붓끝 커서: 칸 바닥 쪽 먹 방울
    this.caret
      .clear()
      .fillStyle(hexToNum(R.ink), 1)
      .fillRect(cx, this.field.y + Math.round(this.field.h * 0.35), 2, Math.round(this.field.h * 0.45))
      .fillRect(cx - 1, this.field.y + Math.round(this.field.h * 0.8) - 2, 4, 3);
    if (bleed) {
      const idx = newCharIndexes(prev, v);
      const last = idx[idx.length - 1];
      if (last !== undefined) {
        const x = this.field.x + this.ink.prefixW(last + 1);
        inkBleed(this.scene, x, this.field.y + Math.round(this.field.h / 2), R.depth + 1);
      }
    }
    debugExpose('ritualName', { value: v, phase: this.phase, scale: P.inkScale });
  }

  private submit(): void {
    if (this.sent) return;
    const name = this.value.trim();
    if (uiCommands.ritual.submitName(name)) this.lock();
  }

  private redraw(): void {
    if (this.sent) return;
    if (uiCommands.ritual.redraw(this.value.trim())) this.lock();
  }

  private openMeta(): void {
    if (this.sent || this.blocked) return;
    uiCommands.ritual.openMeta();
  }

  /** 적었다: 칸을 닫고 글씨에 마지막 먹 번짐 */
  private lock(): void {
    this.sent = true;
    this.el?.blur();
    inkBleed(this.scene, this.field.x + 4 + this.ink.textW, this.field.y + Math.round(this.field.h * 0.6), R.depth + 1);
  }
}
