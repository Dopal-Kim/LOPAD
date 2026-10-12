import Phaser from 'phaser';
import { GlowText, RING } from './glow';
import { takeKey } from './keyGate';
import { playUiSound } from './uiSound';
import { NinePanel } from './kit';
import { FLOOR1_RAMP, SEPIA, hexToNum } from './theme';
import { ART_TO_LOGIC, TITLE_EMBERS, TITLE_UI, titleKey, type TitleSpec } from './themeTitle';
import { clamp01, hotkeyIndex, menuFrameSize, stepIndex, type TitleItem } from './titleView';

/**
 * 62 타이틀 메뉴 (아트 §29): 왼쪽 아래 족자 9-slice 틀(`title_menu_frame`, 여백 48) 안 세로 목록.
 * 줄 = Container → Graphics(선택 할로 띠) → GlowText (phaser 스킬 버튼 패턴, Container 가 입력을 받는다).
 * 글자색: 기본 S5(1px S4) · 선택 #faeec0(할로 #d67a11 α0.5 + 그늘 S2) · 비활성 S4. 선택 줄 왼쪽에 작은 불씨(호박 m 프레임 루프).
 * 조작: ↑↓·W/S · Enter·스페이스 · 숫자 1~n(보이는 순서) · 마우스 올리기(고름)·누르기(실행).
 */
interface Row {
  c: Phaser.GameObjects.Container;
  band: Phaser.GameObjects.Graphics;
  text: GlowText;
  item: TitleItem;
  /** 줄 가운데 y (논리 px) */
  cy: number;
  baseX: number;
}

const L = ART_TO_LOGIC;
const AMBER = FLOOR1_RAMP[5];
/** 불씨 커서 배율 (논리) — 시트 24px 를 화면 2배로 (정수 배율) */
const CURSOR_SCALE = 1;

export class TitleMenu {
  private rows: Row[] = [];
  private frame: Phaser.GameObjects.GameObject & { setAlpha(a: number): unknown };
  private cursor?: Phaser.GameObjects.Image;
  private hint: GlowText;
  private idx: number;
  private inputOn = false;
  private locked = false;
  private noticeUntil = 0;
  private appear = 0;
  private rect: { x: number; y: number; w: number; h: number };

  constructor(
    private scene: Phaser.Scene,
    private spec: TitleSpec,
    private items: TitleItem[],
    startIdx: number,
    private onChoose: (item: TitleItem) => void,
  ) {
    const M = TITLE_UI.menu;
    const D = TITLE_UI.depth.menu;
    this.idx = startIdx;
    // 글자 먼저 만들어 폭을 잰다
    const texts = items.map((it) =>
      new GlowText(scene, 0, 0, it.label, it.enabled ? 'title_item' : 'title_disabled', { font: 'title' }).setDepth(
        D + 1,
      ),
    );
    const maxW = Math.max(0, ...texts.map((t) => t.displayWidth)) / L;
    const size = menuFrameSize(spec.menu, items.length, maxW, {
      rowH: M.rowH,
      textX: M.textX,
      minPadY: M.minPadY,
      padExtra: M.padExtra,
      insetX: spec.menu.insetX,
    });
    // 틀 아래 끝을 아트 영역 아래 끝에 맞춘다 (줄이 늘면 위로 자람)
    const fx = spec.menu.x;
    const fy = spec.menu.y + spec.menu.h - size.h;
    this.rect = { x: fx * L, y: fy * L, w: size.w * L, h: size.h * L };
    const key = titleKey('title_menu_frame');
    if (scene.textures.exists(key)) {
      const s = spec.menu.slice;
      this.frame = new NinePanel(scene, fx * L, fy * L, key, { l: s, r: s, t: s, b: s }, size.w, size.h)
        .setScale(L)
        .setDepth(D);
    } else {
      // 그림이 없으면 코드 족자 (종이 S3 + 테 S1)
      const g = scene.add.graphics().setDepth(D);
      g.fillStyle(hexToNum(SEPIA[1]), 1).fillRect(this.rect.x, this.rect.y, this.rect.w, this.rect.h);
      g.fillStyle(hexToNum(SEPIA[3]), 0.93).fillRect(
        this.rect.x + 6,
        this.rect.y + 8,
        this.rect.w - 12,
        this.rect.h - 16,
      );
      this.frame = g;
    }
    const rowW = Math.round(size.w * L);
    const rowH = Math.round(M.rowH * L);
    items.forEach((item, i) => {
      const top = Math.round((fy + size.rowTop + i * M.rowH) * L);
      const c = scene.add.container(Math.round(fx * L), top).setDepth(D + 1);
      const band = scene.add.graphics();
      const text = texts[i];
      const baseX = Math.round(M.textX * L) - RING;
      text.setPosition(baseX, Math.round((rowH - text.displayHeight) / 2));
      c.add([band, text]);
      c.setSize(rowW, rowH);
      c.setInteractive(new Phaser.Geom.Rectangle(rowW / 2, rowH / 2, rowW, rowH), Phaser.Geom.Rectangle.Contains);
      if (c.input) c.input.cursor = item.enabled ? 'pointer' : 'default';
      c.on('pointerover', () => {
        if (this.inputOn && !this.locked && item.enabled && this.idx !== i) this.select(i);
      });
      c.on('pointerdown', (_p: Phaser.Input.Pointer, _x: number, _y: number, ev: Phaser.Types.Input.EventData) => {
        if (!this.inputOn || this.locked) return;
        ev?.stopPropagation?.();
        this.choose(i);
      });
      this.rows.push({ c, band, text, item, cy: top + rowH / 2, baseX });
    });
    if (scene.textures.exists(titleKey(TITLE_EMBERS))) {
      const [px, py] = spec.embers.pivot;
      this.cursor = scene.add
        .image(0, 0, titleKey(TITLE_EMBERS), spec.embers.perRow)
        .setOrigin(px / spec.embers.frameW, py / spec.embers.frameH)
        .setScale(CURSOR_SCALE)
        .setBlendMode(Phaser.BlendModes.ADD)
        .setDepth(D + 2);
    }
    this.hint = new GlowText(scene, 0, 0, '', 'title_scene').setDepth(D + 1);
    this.hint.setPosition(
      Math.round(this.rect.x + spec.menu.insetX * L * 0.5),
      Math.round(this.rect.y + this.rect.h + 4),
    );
    this.paint(true);
    this.setAppear(0);
  }

  /** 틀 사각형 (논리 px) */
  bounds(): { x: number; y: number; w: number; h: number } {
    return { ...this.rect };
  }

  /** 디버그·헤드리스: 줄 가운데 (논리 px) */
  rowCenters(): { id: string; x: number; y: number; enabled: boolean }[] {
    return this.rows.map((r) => ({
      id: r.item.id,
      x: Math.round(r.c.x + r.baseX + r.text.displayWidth / 2),
      y: Math.round(r.cy),
      enabled: r.item.enabled,
    }));
  }

  selected(): TitleItem {
    return this.items[this.idx];
  }

  setInput(on: boolean): void {
    this.inputOn = on;
  }

  /** 고른 결과가 타이틀에 남을 때(설정·수련장 거부) 다시 입력을 받는다 */
  unlock(): void {
    this.locked = false;
    this.paint(false);
  }

  /** 등장 0~1: 틀이 먼저, 줄이 하나씩 (아래에서 6px 떠오름) */
  setAppear(p: number): void {
    this.appear = p;
    const lift = (1 - p) * 6;
    this.frame.setAlpha(p);
    if ('y' in this.frame) (this.frame as unknown as { y: number }).y = Math.round(this.rect.y + lift);
    const n = this.rows.length;
    this.rows.forEach((r, i) => {
      const a = clamp01(p * 1.5 - (i / Math.max(1, n)) * 0.5);
      r.c.setAlpha(a);
      r.c.y = Math.round(r.cy - (TITLE_UI.menu.rowH * L) / 2 + (1 - a) * 6);
    });
    this.cursor?.setAlpha(clamp01(p * 2 - 1));
    this.hint.setAlpha(clamp01(p * 2 - 1));
  }

  /** 키 하나 처리. 동작했으면 true */
  handleKey(e: KeyboardEvent): boolean {
    if (!this.inputOn || this.locked) return false;
    const k = e.key;
    if (k === 'ArrowUp' || k === 'w' || k === 'W') {
      if (!takeKey(e)) return false;
      this.select(stepIndex(this.items, this.idx, -1));
      return true;
    }
    if (k === 'ArrowDown' || k === 's' || k === 'S') {
      if (!takeKey(e)) return false;
      this.select(stepIndex(this.items, this.idx, 1));
      return true;
    }
    if (k === 'Enter' || k === ' ') {
      if (e.repeat || !takeKey(e)) return false;
      this.choose(this.idx);
      return true;
    }
    const h = hotkeyIndex(this.items, k);
    if (h >= 0) {
      if (e.repeat || !takeKey(e)) return false;
      this.choose(h);
      return true;
    }
    return false;
  }

  /** 틀 아래 한 줄 (수련장 거부 사유 등) — 잠깐 머문 뒤 고른 줄 안내로 돌아간다 */
  notice(text: string): void {
    this.noticeUntil = this.scene.time.now + TITLE_UI.noticeMs;
    this.hint.setGlowStyle('title_notice').setText(text);
  }

  private select(i: number): void {
    if (i === this.idx) return;
    this.idx = i;
    // 62 루프 2: 커서 이동 소리 (음향 ui_move — 없으면 조용히)
    playUiSound(this.scene, 'move');
    this.paint(false);
  }

  private choose(i: number): void {
    const r = this.rows[i];
    if (!r) return;
    if (!r.item.enabled) {
      // 못 고르는 줄: 살짝 떨림 + 그 줄의 덧말
      this.scene.tweens.killTweensOf(r.text);
      r.text.x = r.baseX;
      this.scene.tweens.add({ targets: r.text, x: r.baseX + 2, duration: 40, yoyo: true, repeat: 2 });
      if (r.item.hint) this.notice(r.item.hint);
      return;
    }
    this.select(i);
    this.locked = true;
    playUiSound(this.scene, 'select');
    // 누른 느낌: 띠가 한 번 밝아지고 불씨가 부푼다
    r.band.setAlpha(1);
    this.scene.tweens.add({ targets: r.band, alpha: 0.55, duration: TITLE_UI.menu.chooseMs, yoyo: true });
    if (this.cursor)
      this.scene.tweens.add({
        targets: this.cursor,
        scale: CURSOR_SCALE * 1.5,
        duration: TITLE_UI.menu.chooseMs / 2,
        yoyo: true,
      });
    this.scene.time.delayedCall(TITLE_UI.menu.chooseMs, () => this.onChoose(r.item));
  }

  /** 선택 표시 다시 칠하기 */
  private paint(instant: boolean): void {
    const M = TITLE_UI.menu;
    const rowH = Math.round(M.rowH * L);
    this.rows.forEach((r, i) => {
      const sel = i === this.idx;
      r.text.setGlowStyle(!r.item.enabled ? 'title_disabled' : sel ? 'title_selected' : 'title_item');
      const tx = r.baseX + (sel && r.item.enabled ? TITLE_UI.selectNudge : 0);
      this.scene.tweens.killTweensOf(r.text);
      if (instant) r.text.x = tx;
      else this.scene.tweens.add({ targets: r.text, x: tx, duration: 90, ease: 'Sine.easeOut' });
      r.band.clear();
      if (sel && r.item.enabled) {
        // 할로 띠: 호박 α 계단이 오른쪽으로 옅어진다 (픽셀 단위 정수)
        const x0 = Math.round(M.bandInset * L);
        const w = Math.round(r.c.width - M.bandInset * L * 2);
        const h = Math.round(M.bandH * L);
        const y0 = Math.round((rowH - h) / 2);
        const steps = 8;
        const seg = Math.ceil(w / steps);
        for (let k = 0; k < steps; k++) {
          const a = 0.34 * (1 - k / steps);
          r.band.fillStyle(hexToNum(AMBER), a).fillRect(x0 + k * seg, y0 + 2, Math.min(seg, w - k * seg), h - 4);
          r.band.fillStyle(hexToNum(AMBER), a * 0.5).fillRect(x0 + k * seg, y0, Math.min(seg, w - k * seg), 2);
          r.band.fillStyle(hexToNum(AMBER), a * 0.5).fillRect(x0 + k * seg, y0 + h - 2, Math.min(seg, w - k * seg), 2);
        }
        r.band.setAlpha(0.55);
      }
    });
    const r = this.rows[this.idx];
    if (this.cursor && r) {
      const x = Math.round(this.rect.x + M.cursorX * L);
      this.scene.tweens.killTweensOf(this.cursor);
      this.cursor.setScale(CURSOR_SCALE);
      if (instant) this.cursor.setPosition(x, Math.round(r.cy));
      else this.scene.tweens.add({ targets: this.cursor, x, y: Math.round(r.cy), duration: 80, ease: 'Sine.easeOut' });
    }
    if (this.scene.time.now >= this.noticeUntil) this.hint.setGlowStyle('title_scene').setText(r?.item.hint ?? '');
  }

  /** 매 프레임: 불씨 커서 프레임 · 안내 줄 만료 */
  update(t: number): void {
    if (this.cursor) {
      const per = this.spec.embers.perRow;
      // 호박 m 행 (시트 행 1) 10fps 루프
      const row = Math.max(0, this.spec.embers.rowNames.indexOf('amber_m'));
      this.cursor.setFrame(row * per + (Math.floor(t / (1000 / this.spec.embers.fps)) % per));
    }
    if (this.noticeUntil && t >= this.noticeUntil) {
      this.noticeUntil = 0;
      this.hint.setGlowStyle('title_scene').setText(this.items[this.idx]?.hint ?? '');
      this.hint.setAlpha(clamp01(this.appear * 2 - 1));
    }
  }

  destroy(): void {
    for (const r of this.rows) r.c.destroy();
    this.rows = [];
    this.frame.destroy();
    this.cursor?.destroy();
    this.hint.destroy();
  }
}
