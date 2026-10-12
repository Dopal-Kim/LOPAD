/**
 * 62 계약 UI §20 시작 의식 대체 화면 (시스템): UI 의식 씬(`UI_SCENES.RITUAL`)이 아직 없을 때 Setup 위에 뜨는 최소 화면.
 * UI 와 **같은 계약만** 쓴다 — 상태는 `getUiSnapshot().ritual` + `RITUAL` 이벤트, 입력은 `uiCommands.ritual.*` (UI 구현의 참고본).
 * 데모에서 고정폭 글꼴·브라우저 기본 입력칸이 보이지 않게: 글꼴 Galmuri11(로드 전 sans-serif), 이름은 숨긴 입력칸(한글 조합용)의 값을
 * 종이 위 글자로 비춘다. 3획은 시스템 획 연출(`StrokeFx` 등 그림 위 빛 획)로 보여 주고 점 목록을 `ritual.stroke` 로 보낸다.
 * 정식 화면(일기장 종이 키트·붓글씨·먹 획·무기 카드)은 UI 파트 몫.
 */
import Phaser from 'phaser';
import { RITUAL, SCENES } from '../../core/Constants';
import { UI_EVENTS, uiBus, uiCommands, type UiRitual, type UiRitualPoint } from '../../contract/ui';
import { ensureFont, fontFamilyOr } from '../../systems/fonts';
import { EventBus, Events } from '../../core/EventBus';
import { StrokeFx } from '../../systems/strokeFx/strokeFx';
import { toLogical } from '../../systems/display';
import { oncePerKeyEvent } from '../../systems/keyEvents';

const V = RITUAL.VIEW;
const DEPTH_TOP = 1000;

export class RitualView extends Phaser.Scene {
  private state: UiRitual | null = null;
  private paper!: Phaser.GameObjects.Graphics;
  private head!: Phaser.GameObjects.Text;
  private body!: Phaser.GameObjects.Text;
  private nameLine!: Phaser.GameObjects.Text;
  private corner!: Phaser.GameObjects.Text;
  private hint!: Phaser.GameObjects.Text;
  private look?: Phaser.GameObjects.Image;
  private field?: HTMLInputElement;
  private fx?: StrokeFx;
  private current: UiRitualPoint[] | null = null;
  private readonly onRitual = (r: UiRitual) => this.apply(r);
  /** 메뉴(영혼 강화)가 열린 동안은 이름 칸을 치운다 — 숫자 키가 이름에 들어가지 않게 · 적던 글자는 남긴다 */
  private menuOpen = false;
  private typed: string | null = null;
  private readonly onMenuOpen = () => {
    this.menuOpen = true;
    if (this.field) this.typed = this.field.value;
    this.dropField();
  };
  private readonly onMenuClose = () => {
    this.menuOpen = false;
    const st = this.state;
    if (st && (st.phase === 'name' || st.phase === 'rewrite')) this.time.delayedCall(60, () => this.ensureField());
  };
  private readonly onKey = oncePerKeyEvent<KeyboardEvent>((e) => this.key(e));

  constructor() {
    super(SCENES.RITUAL_VIEW);
  }

  create(): void {
    this.state = null;
    this.current = null;
    this.paper = this.add.graphics().setDepth(DEPTH_TOP);
    const text = (size: number, color: string) =>
      this.add
        .text(0, 0, '', { fontFamily: this.family(), fontSize: `${size}px`, color, align: 'center', lineSpacing: 6 })
        .setOrigin(0.5, 0)
        .setDepth(DEPTH_TOP + 1);
    this.head = text(V.TITLE_PX, V.INK);
    this.body = text(V.BODY_PX, V.INK_SOFT);
    this.nameLine = text(V.TITLE_PX, V.INK);
    this.corner = text(V.BODY_PX, V.LIGHT).setOrigin(1, 0).setAlign('right');
    this.hint = text(V.BODY_PX, V.LIGHT);
    // 글꼴이 늦게 오면 다시 그린다
    void ensureFont(V.FONT_FAMILY, V.BODY_PX).then((ok) => {
      if (!ok || !this.sys.isActive()) return;
      for (const t of [this.head, this.body, this.nameLine, this.corner, this.hint]) t.setFontFamily(this.family());
    });
    uiBus.on(UI_EVENTS.RITUAL, this.onRitual);
    // 시스템 메뉴 브로커 사건 (UI 렌더러가 없어 임시 텍스트 메뉴일 때도 온다)
    EventBus.on(Events.MENU_OPENED, this.onMenuOpen);
    EventBus.on(Events.MENU_CLOSED, this.onMenuClose);
    this.input.keyboard?.on('keydown', this.onKey);
    this.input.on('pointerdown', this.onDown, this);
    this.input.on('pointermove', this.onMove, this);
    this.input.on('pointerup', this.onUp, this);
    this.events.once('shutdown', () => {
      uiBus.off(UI_EVENTS.RITUAL, this.onRitual);
      EventBus.off(Events.MENU_OPENED, this.onMenuOpen);
      EventBus.off(Events.MENU_CLOSED, this.onMenuClose);
      this.input.keyboard?.off('keydown', this.onKey);
      this.input.off('pointerdown', this.onDown, this);
      this.input.off('pointermove', this.onMove, this);
      this.input.off('pointerup', this.onUp, this);
      this.dropField();
      this.fx?.destroy();
      this.fx = undefined;
    });
    this.apply(uiCommands.getUiSnapshot().ritual ?? null);
  }

  update(time: number): void {
    this.fx?.update(time);
    if (this.field) this.showName();
  }

  private family(): string {
    return `${fontFamilyOr(V.FONT_FAMILY, V.FONT_FALLBACK)}, ${V.FONT_FALLBACK}`;
  }

  // ─── 상태 → 화면 ───

  private apply(r: UiRitual | null): void {
    const prev = this.state?.phase ?? null;
    this.state = r;
    const phase = r?.phase ?? null;
    if (phase !== prev) {
      this.dropField();
      this.typed = null;
      // 다음 틱에 만든다 — 앞 화면의 키(카드 '2' 등)가 새 입력칸에 들어가지 않게
      if (phase === 'name' || phase === 'rewrite') this.time.delayedCall(60, () => this.ensureField());
      if (phase === 'strokes' && !this.fx) this.fx = new StrokeFx(this);
      if (phase !== 'strokes' && this.fx) {
        const fx = this.fx;
        this.fx = undefined;
        fx.destroy();
      }
    }
    if (phase === 'strokes' && r?.strokes && r.strokes.done >= r.strokes.total && this.fx) this.fx.sear();
    this.draw();
  }

  private draw(): void {
    const r = this.state;
    this.paper.clear();
    this.look?.destroy();
    this.look = undefined;
    for (const t of [this.head, this.body, this.nameLine, this.corner, this.hint])
      t.setText('').setVisible(true).setWordWrapWidth(null);
    if (!r || !r.phase) return;
    const midX = 480;
    this.hint.setText(r.hint ?? '').setPosition(midX, V.HINT_Y - 6);
    switch (r.phase) {
      case 'name':
      case 'rewrite': {
        this.page(V.PAGE_H);
        const top = 270 - V.PAGE_H / 2 + 22;
        this.body
          .setText((r.lines ?? []).join('\n'))
          .setWordWrapWidth(V.PAGE_W - 40)
          .setPosition(midX, top);
        this.nameLine.setPosition(midX, top + this.body.height + 26);
        this.showName();
        this.paper.lineStyle(1, V.PAPER_EDGE, 1).lineBetween(380, this.nameLine.y + 30, 580, this.nameLine.y + 30);
        if (r.phase === 'rewrite' && r.meta) {
          const m = r.meta;
          this.corner.setText(`[${m.key}] ${m.label}${m.canBuy ? ' ✦' : ''}\n${m.souls}`).setPosition(948, 12);
        }
        return;
      }
      case 'strokes': {
        const s = r.strokes;
        const legend = (s?.legend ?? []).map((l) => `${l.line} — ${l.weaponName}`).join('    ');
        this.band(8, 64);
        this.head
          .setColor(V.LIGHT)
          .setFontSize(V.BODY_PX)
          .setText((r.lines ?? []).join('\n'))
          .setPosition(midX, 14);
        this.body
          .setColor(V.DIM)
          .setText(`${'●'.repeat(s?.done ?? 0)}${'○'.repeat(Math.max(0, (s?.total ?? 3) - (s?.done ?? 0)))}\n${legend}`)
          .setPosition(midX, 14 + this.head.height + 6);
        return;
      }
      case 'trial': {
        const t = r.trial;
        const lines = (t?.tasks ?? []).map((k) => {
          const mark = k.done ? (k.clean ? '●' : '◐') : k.id === t?.current ? '▸' : '○';
          return `${k.label}  ${mark}`;
        });
        this.corner.setText(lines.join('\n')).setPosition(V.TASK_X, V.TASK_Y);
        this.band(0, 0);
        return;
      }
      case 'fate': {
        const f = r.fate;
        if (!f) return;
        this.page(V.PAGE_H + 40);
        const top = 270 - (V.PAGE_H + 40) / 2 + 18;
        this.body
          .setColor(V.INK_SOFT)
          .setFontSize(V.BODY_PX)
          .setText((r.lines ?? []).join('\n'))
          .setPosition(midX, top);
        let y = top + this.body.height + 8;
        this.head.setColor(V.INK).setFontSize(V.TITLE_PX).setText(f.weaponName).setPosition(midX, y);
        y += this.head.height + 8;
        if (f.lookKey && this.textures.exists(f.lookKey)) {
          const img = this.add
            .image(midX, y, f.lookKey)
            .setOrigin(0.5, 0)
            .setDepth(DEPTH_TOP + 1);
          const k = Math.min(1, 120 / img.height, (V.PAGE_W - 60) / img.width);
          img.setScale(k);
          this.look = img;
          y += img.displayHeight + 8;
        }
        const words = [f.line ? `“${f.line}”` : '', f.why, f.gift ?? ''].filter(Boolean).join('\n\n');
        this.nameLine
          .setFontSize(V.BODY_PX)
          .setColor(V.INK)
          .setWordWrapWidth(V.PAGE_W - 40)
          .setText(words)
          .setPosition(midX, y);
        return;
      }
    }
  }

  /** 가운데 종이 한 장 */
  private page(h: number): void {
    const g = this.paper;
    const x = 480 - V.PAGE_W / 2;
    const y = 270 - h / 2;
    g.fillStyle(V.PAPER, V.PAPER_ALPHA).fillRect(x, y, V.PAGE_W, h);
    g.lineStyle(1, V.PAPER_EDGE, 1).strokeRect(x + 0.5, y + 0.5, V.PAGE_W - 1, h - 1);
    this.hint.setColor(V.LIGHT);
  }

  /** 화면 위 어두운 띠 (등 그림·전장 위 글자를 읽히게) + 아래 안내 띠 */
  private band(y: number, h: number): void {
    const g = this.paper;
    if (h > 0) g.fillStyle(0x000000, 0.45).fillRect(0, y, 960, h);
    g.fillStyle(0x000000, 0.45).fillRect(0, V.HINT_Y - 10, 960, 26);
  }

  // ─── 이름 (숨긴 입력칸 — 한글 조합) ───

  private ensureField(): void {
    const st = this.state;
    if (this.field || this.menuOpen || !st || (st.phase !== 'name' && st.phase !== 'rewrite')) return;
    this.makeField(st);
  }

  private makeField(r: UiRitual): void {
    this.dropField();
    if (typeof document === 'undefined') return;
    const el = document.createElement('input');
    el.type = 'text';
    el.maxLength = r.name?.maxLen ?? 12;
    el.value = this.typed ?? r.name?.value ?? '';
    el.setAttribute('aria-label', '이름');
    el.autocomplete = 'off';
    // 화면에는 보이지 않는다 (글자는 종이 위 Phaser 글자로 비춘다)
    el.style.cssText = 'position:fixed;left:-9999px;top:0;width:1px;height:1px;opacity:0;border:0;padding:0;';
    el.addEventListener('input', () => this.showName());
    el.addEventListener('keydown', (e) => {
      e.stopPropagation();
      const st = this.state;
      if (e.key === 'Enter' && !e.isComposing) uiCommands.ritual.submitName(el.value);
      else if (st?.phase === 'rewrite' && st.redraw && e.key === st.redraw.key) {
        e.preventDefault();
        uiCommands.ritual.redraw(el.value);
      } else if (st?.phase === 'rewrite' && st.meta && e.key === st.meta.key) {
        e.preventDefault();
        uiCommands.ritual.openMeta();
      }
    });
    el.addEventListener('blur', () => {
      if (this.field === el) setTimeout(() => this.field === el && el.focus(), 0);
    });
    document.body.appendChild(el);
    this.input.keyboard?.disableGlobalCapture();
    this.field = el;
    el.focus();
  }

  private dropField(): void {
    if (!this.field) return;
    const el = this.field;
    this.field = undefined;
    el.remove();
    this.input.keyboard?.enableGlobalCapture();
  }

  private showName(): void {
    const v = this.field?.value ?? this.state?.name?.value ?? '';
    const caret = Math.floor(this.time.now / 500) % 2 === 0 ? '|' : ' ';
    this.nameLine.setColor(V.INK).setFontSize(V.TITLE_PX).setText(`${v}${caret}`);
  }

  // ─── 키 (이름 칸 밖) ───

  private key(e: KeyboardEvent): void {
    const p = this.state?.phase;
    if (e.key === 'Escape') uiCommands.ritual.back();
    else if (e.key === 'Enter') {
      if (p === 'trial') uiCommands.ritual.skip();
      else if (p === 'fate') uiCommands.ritual.next();
    }
  }

  // ─── 3획 (논리 px 점 목록 → ritual.stroke) ───

  private onDown(p: Phaser.Input.Pointer): void {
    const ph = this.state?.phase;
    if (ph === 'fate') {
      uiCommands.ritual.next();
      return;
    }
    if (ph === 'trial') {
      uiCommands.ritual.next();
      return;
    }
    if (ph !== 'strokes') return;
    const x = toLogical(p.x);
    const y = toLogical(p.y);
    this.current = [{ x, y, t: p.downTime }];
    this.fx?.begin(x, y, p.downTime);
  }

  private onMove(p: Phaser.Input.Pointer): void {
    if (this.state?.phase !== 'strokes' || !this.current || !p.isDown) return;
    const x = toLogical(p.x);
    const y = toLogical(p.y);
    this.fx?.move(x, y, p.moveTime);
    const last = this.current[this.current.length - 1];
    if (Math.hypot(x - last.x, y - last.y) >= 2) this.current.push({ x, y, t: p.moveTime });
  }

  private onUp(p: Phaser.Input.Pointer): void {
    if (this.state?.phase !== 'strokes' || !this.current) return;
    const x = toLogical(p.x);
    const y = toLogical(p.y);
    this.current.push({ x, y, t: p.upTime });
    this.fx?.end(x, y, p.upTime);
    const pts = this.current;
    this.current = null;
    uiCommands.ritual.stroke(pts);
  }
}
