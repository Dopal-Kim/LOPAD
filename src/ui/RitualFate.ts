import Phaser from 'phaser';
import { UI_SCREEN, uiCommands, type UiRitual } from '../contract/ui';
import { debugExpose } from './debug';
import { GlowText } from './glow';
import { lookImage, lookText } from './growthArt';
import { verbKey } from './growthView';
import { bannerCard } from './HudAlerts';
import { keyGlyph } from './keyGuide';
import { NinePanel, ensureImage, inkPanel, weaponIconKey } from './kit';
import { darkBackdrop, hintRow, ritualMeta, ritualTex } from './ritualArt';
import { quoteVoice, voiceLook } from './storyView';
import { ritualText } from './textRitual';
import { GRAY, hexToNum } from './theme';
import { RITUAL_UI as R } from './themeRitual';
import { WEAPON_HUE, type WeaponHueId } from './themeWeapon';
import { drawCheck } from './TrainingHud';
import type { RitualPage } from './RitualScene';

/**
 * 62 루프 1 P0-2 운명 공개 장 (계약 §20 phase 'fate'): 어둠 위 액자 하나 — 위에 적은 이름(흐림), 액자 안 무기 미리보기 그림
 * (`fate.lookKey`, 없으면 무기 아이콘 4배·이름 글자), 무기 이름 2배(무기 색 테), 원한의 첫 한마디(무기 목소리 글씨), '왜' 한 줄,
 * 회피 시험 결과 한 줄(`gift`). 두 번째 생 '손이 기억한 무기' 표. [Enter] 벽 밖으로 → `ritual.next`. 수치는 없다.
 */
export class RitualFatePage implements RitualPage {
  private root: Phaser.GameObjects.Container;

  constructor(
    private scene: Phaser.Scene,
    r: UiRitual,
  ) {
    this.root = scene.add.container(0, 0).setDepth(R.depth);
    this.build(r);
  }

  update(): void {}

  key(e: KeyboardEvent): boolean {
    if (e.key === 'Enter' || e.key === ' ') {
      uiCommands.ritual.next();
      return true;
    }
    return false;
  }

  destroy(): void {
    this.scene.tweens.killTweensOf(this.root.list);
    this.root.destroy();
  }

  private build(r: UiRitual): void {
    const sc = this.scene;
    const F = R.fate;
    const W = UI_SCREEN.WIDTH;
    const f = r.fate;
    this.root.add(darkBackdrop(sc, 1));
    if (!f) return;
    const weapon = (f.weapon in WEAPON_HUE ? f.weapon : 'katana') as WeaponHueId;
    const hue = hexToNum(WEAPON_HUE[weapon].main);
    // 적은 이름 (위, 흐림) · 두 번째 생 '손이 기억한 무기'
    const who = (r.lines ?? [])[0];
    const top: Phaser.GameObjects.GameObject[] = [];
    if (who) {
      const t = new GlowText(sc, 0, 0, who, 'ink_faint');
      t.placeCenter(W / 2, 22);
      top.push(t);
    }
    if (f.remembered) {
      const tag = new GlowText(sc, 0, 0, ritualText('rememberedTag'), 'ink_accent');
      tag.placeCenter(W / 2, 46);
      top.push(tag);
    }
    this.root.add(top);
    // 액자 (art §30 fate_frame 9-slice — 안쪽은 투명이라 어두운 판을 먼저 깐다) · 없으면 잉크 패널 + 무기 색 테
    const frame = sc.add.container(0, 0);
    const size = F.size;
    const inner = F.inner;
    const plate = sc.add.graphics();
    plate
      .fillStyle(hexToNum(GRAY[1]), 1)
      .fillRect(F.x + inner - 2, F.y + inner - 2, size - inner * 2 + 4, size - inner * 2 + 4);
    frame.add(plate);
    const art = ritualTex(sc, 'frame');
    const meta = ritualMeta<{ slice?: { left: number; right: number; top: number; bottom: number } }>(sc, 'frame');
    const sl = meta?.slice;
    if (art) {
      const s9 = sl
        ? { l: sl.left, r: sl.right, t: sl.top, b: sl.bottom }
        : { l: F.slice, r: F.slice, t: F.slice, b: F.slice };
      frame.add(new NinePanel(sc, F.x, F.y, art, s9, size, size));
    } else {
      frame.add(inkPanel(sc, F.x, F.y, size, size));
      const g = sc.add.graphics();
      g.lineStyle(1, hue, 1).strokeRect(F.x + 5.5, F.y + 5.5, size - 11, size - 11);
      frame.add(g);
    }
    // 무기 미리보기 (계약 lookKey → UI 가 읽은 looks/<무기>_base → 무기 아이콘 4배 → 이름 글자)
    const lookKey = f.lookKey && sc.textures.exists(f.lookKey) ? f.lookKey : uiLookKey(sc, weapon);
    const lookBox = size - inner * 2;
    const look = lookImage(sc, lookKey, W / 2, F.y + inner, lookBox, lookBox);
    if (look) frame.add(look);
    else if (sc.textures.exists(weaponIconKey(weapon)))
      frame.add(sc.add.image(W / 2, F.y + size / 2, weaponIconKey(weapon)).setScale(4));
    else frame.add(lookText(sc, f.weaponName, W / 2, F.y + inner, lookBox));
    // 불씨 테 한 번 밝힘 (art §30 emberLine inset 21, ADD 0.6 → 1.0 → 0.8)
    const ember = sc.add.graphics().setBlendMode(Phaser.BlendModes.ADD);
    ember.lineStyle(2, R.stamp.halo, 1).strokeRect(F.x + 21, F.y + 21, size - 42, size - 42);
    ember.setAlpha(0);
    frame.add(ember);
    this.root.add(frame);
    // 액자 아래: 무기 이름 · 첫 한마디 · '왜' · 시험 결과
    let y = F.textTop;
    const parts: Phaser.GameObjects.GameObject[] = [];
    const name = new GlowText(sc, 0, 0, f.weaponName, 'ink_accent', { scale: 2 });
    name.placeCenter(W / 2, y);
    parts.push(name);
    y += name.displayHeight + 4;
    const voice = new GlowText(sc, 0, 0, quoteVoice(f.line), voiceLook(weapon).style, { wrap: 520, align: 'center' });
    voice.placeCenter(W / 2, y);
    parts.push(voice);
    y += voice.displayHeight + 6;
    const why = new GlowText(sc, 0, 0, f.why, 'ink_body', { wrap: 560, align: 'center' });
    why.placeCenter(W / 2, y);
    parts.push(why);
    y += why.displayHeight + 4;
    if (f.gift) {
      const gift = new GlowText(sc, 0, 0, f.gift, 'ink_faint', { wrap: 560, align: 'center' });
      gift.placeCenter(W / 2, y);
      parts.push(gift);
    }
    this.root.add(parts);
    this.root.add(hintRow(sc, r.hint, W / 2, UI_SCREEN.HEIGHT - R.hintBottom));
    // 액자가 먼저 내려앉고 불씨 테가 한 번 밝아진 뒤, 아래 글이 차례로
    frame.setAlpha(0).setY(-8);
    sc.tweens.add({ targets: frame, alpha: 1, y: 0, duration: F.inMs, ease: 'Quad.easeOut' });
    sc.tweens.chain({
      targets: ember,
      tweens: [
        { alpha: 0.6, duration: 1, delay: F.inMs },
        { alpha: 1, duration: F.pulseMs / 2 },
        { alpha: 0.8, duration: F.pulseMs / 2 },
      ],
    });
    parts.forEach((o, i) => {
      (o as unknown as Phaser.GameObjects.Components.Alpha).setAlpha(0);
      sc.tweens.add({ targets: o, alpha: 1, delay: F.inMs + F.pulseMs / 2 + i * 140, duration: 260 });
    });
    debugExpose('ritualFate', {
      weapon: f.weapon,
      name: f.weaponName,
      why: f.why,
      gift: f.gift ?? null,
      look: lookKey,
    });
  }
}

/** 읽혀 있는 무기 미리보기 키 (시스템 `looks/<무기>_base` → UI 사본) — 없으면 null */
export function uiLookKey(scene: Phaser.Scene, weapon: string): string | null {
  const sys = `looks/${weapon}_base`;
  if (scene.textures.exists(sys)) return sys;
  const k = `ui:${sys}`;
  return scene.textures.exists(k) ? k : null;
}

/** 무기 미리보기를 UI 사본 키로 읽는다 (이미 있으면 바로 done) */
export function loadLook(scene: Phaser.Scene, weapon: string, done: () => void): void {
  if (uiLookKey(scene, weapon)) {
    done();
    return;
  }
  ensureImage(scene, `ui:looks/${weapon}_base`, `${R.lookUrl}${weapon}_base.png`, () => done());
}

/**
 * 62 루프 1 P0-2 회피 시험 장 (계약 §20 phase 'trial'): 탄생 전장과 사수는 시스템이 그린다 — UI 는 투명하게 두고
 * 오른쪽 위 과제 목록(체크 · 지금 과제 강조 · 키캡)과, 과제 이름 카드(state 'card' — 누르면 `ritual.next`), 아래 안내 줄만.
 * [Enter] 건너뛴다 → `ritual.skip` · [Esc] 3획부터 다시 → `ritual.back`.
 */
export class RitualTrialPage implements RitualPage {
  private root: Phaser.GameObjects.Container;
  private list?: Phaser.GameObjects.Container;
  private card?: Phaser.GameObjects.Container;
  private sig = '';
  private cardSig = '';

  constructor(
    private scene: Phaser.Scene,
    r: UiRitual,
  ) {
    this.root = scene.add.container(0, 0).setDepth(R.depth);
    this.root.add(hintRow(scene, r.hint, UI_SCREEN.WIDTH / 2, UI_SCREEN.HEIGHT - R.hintBottom));
    this.update(r);
  }

  update(r: UiRitual): void {
    const t = r.trial;
    const sig = JSON.stringify(t?.tasks ?? []) + (t?.current ?? '');
    if (sig !== this.sig) {
      this.sig = sig;
      this.drawList(r);
    }
    const cardSig = t?.state === 'card' ? (t.current ?? '') : '';
    if (cardSig !== this.cardSig) {
      this.cardSig = cardSig;
      this.drawCard(r);
    }
  }

  key(e: KeyboardEvent): boolean {
    if (e.key === 'Enter') {
      uiCommands.ritual.skip();
      return true;
    }
    if (e.key === 'Escape') {
      uiCommands.ritual.back();
      return true;
    }
    return false;
  }

  destroy(): void {
    this.scene.tweens.killTweensOf(this.root.list);
    this.root.destroy();
  }

  private drawList(r: UiRitual): void {
    this.list?.destroy();
    const tasks = r.trial?.tasks ?? [];
    if (!tasks.length) return;
    const sc = this.scene;
    const T = R.tasks;
    const head = new GlowText(sc, 0, 0, ritualText('tasksHead'), 'ink_accent');
    const g = sc.add.graphics();
    const rows: { objs: Phaser.GameObjects.Container[]; w: number }[] = tasks.map((task) => {
      const now = task.id === r.trial?.current && !task.done;
      const objs: Phaser.GameObjects.Container[] = [];
      let tx = T.box + 6;
      const vk = task.verb ? verbKey(task.verb, null) : null;
      if (vk) {
        const gl = keyGlyph(sc, vk.key, 0, task.done);
        gl.obj.setX(tx);
        objs.push(gl.obj);
        tx += gl.width + 4;
      }
      const label = new GlowText(sc, tx, 0, task.label, task.done ? 'ink_faint' : now ? 'ink_accent' : 'ink_body');
      objs.push(label);
      return { objs, w: tx + label.displayWidth };
    });
    // 폭은 가장 긴 줄에 맞춘다 (줄바꿈 없이 — 겹침 방지)
    const w = Math.max(T.w, head.displayWidth + T.pad * 2, ...rows.map((rw) => rw.w + T.pad * 2));
    const h = T.pad * 2 + head.displayHeight + 4 + tasks.length * T.rowH;
    const x = T.right - w;
    const objs: Phaser.GameObjects.GameObject[] = [inkPanel(sc, x, T.top, w, h), head, g];
    head.setPosition(x + T.pad, T.top + T.pad - 2);
    let y = T.top + T.pad + head.displayHeight + 4;
    tasks.forEach((task, i) => {
      drawCheck(g, x + T.pad, y + 3, T.box, task.done);
      for (const o of rows[i].objs) {
        o.setPosition(o.x + x + T.pad, y);
        objs.push(o);
      }
      y += T.rowH;
    });
    this.list = sc.add.container(0, 0, objs);
    this.root.add(this.list);
  }

  /** 과제 이름 카드 (위 가운데 하데스식 띠) — 누르면 넘긴다 */
  private drawCard(r: UiRitual): void {
    this.card?.destroy();
    this.card = undefined;
    const t = r.trial;
    const task = t?.state === 'card' ? t.tasks.find((k) => k.id === t.current) : undefined;
    if (!task) return;
    const sc = this.scene;
    const b = bannerCard(sc, [{ text: task.label, style: 'ink_body', scale: 2 }], 0);
    b.box.setY(R.taskCard.top);
    b.box.setSize(UI_SCREEN.WIDTH, b.h);
    b.box.setInteractive(
      new Phaser.Geom.Rectangle(UI_SCREEN.WIDTH / 2, b.h / 2, UI_SCREEN.WIDTH, b.h),
      Phaser.Geom.Rectangle.Contains,
    );
    b.box.on('pointerup', () => uiCommands.ritual.next());
    b.box.setAlpha(0);
    sc.tweens.add({ targets: b.box, alpha: 1, duration: 200 });
    this.card = b.box;
    this.root.add(b.box);
  }
}
