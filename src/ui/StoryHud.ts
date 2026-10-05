import Phaser from 'phaser';
import { UI_SCREEN } from '../contract/ui';
import { debugExpose } from './debug';
import { GlowText } from './glow';
import { KIT, NinePanel, SLICE, inkPanel, rule } from './kit';
import { sameStepText } from './tutorialView';
import {
  canShowHead,
  enqueueStory,
  quoteVoice,
  readStoryLine,
  revealSteps,
  storyHoldMs,
  voiceJitter,
  voiceLook,
  voiceWeapon,
  type StoryChannel,
  type StoryLineView,
} from './storyView';
import { swatch } from './StructureHud';
import { storyText } from './text';
import { CLUE_UI, ENEMY_INTRO_UI, EVENT_UI, SPEECH_UI, STORY_UI, VOICE_UI } from './themeStory';
import { TimedCard } from './timedCard';

export interface StoryHudOptions {
  /** 자막을 지금 띄워도 되는가 (글꼴 준비 · 탄생 연출 아님) */
  canRun: () => boolean;
  /** 메뉴 씬이 떠 있는가 (이벤트 문장은 메뉴가 닫힌 뒤) */
  menuOpen: () => boolean;
  /** 하단 가운데 자막의 아래 끝 y (보스 막대·전투 묶음 위) */
  centerBottom: () => number;
  /** 원한의 한마디 자리: 무기 줄 왼쪽 x · 전투 묶음 위 끝 y */
  voiceAnchor: () => { x: number; bottom: number };
  /** 지금 무기 이름 (스냅샷 `weapon.name`) — 한마디 페이로드에 무기가 없을 때 */
  weaponName: () => string;
  stageIndex: () => number;
  /** 한 줄이 떴다 (보스 처치 뒤 메뉴 기다림을 늘이는 데 쓴다) */
  onShown?: (channel: StoryChannel, holdMs: number) => void;
}

interface Showing {
  view: StoryLineView;
  box: Phaser.GameObjects.Container;
  timers: Phaser.Time.TimerEvent[];
  holdMs: number;
}

/**
 * 61라운드 단계 2 서사 표시 (P8) — HudScene 의 자막을 옮겨 와 STORY 를 한 차례로 그린다 (텍스트 팩 B1 '겹치면 큐에 넣어 뒤에').
 * 자리(`storyView.storyChannel`):
 *  - caption: 기존 자막(층·보스·휴식·개성 변화·사망) — 하단 가운데 ink_body, 3.6초.
 *  - notice: 공지 1.8초 — 차례를 앞지른다(떠 있던 서사 줄은 차례 맨 앞으로 되돌아간다).
 *  - speech: 군주 대사 — 하단 가운데 대사 + 왼쪽 위 화자 이름표(잉크 패널, 강조색 이름).
 *  - voice: 원한의 한마디 — 전투 묶음 바로 위, 무기 빛 세로 줄 + 따옴표 한 줄. 무기마다 글씨 색·등장·떨림이 다르다(VOICE_LOOK). 이름 없음.
 *  - event: 이벤트 도입·결과 문장 — 하단 가운데 종이 띠(지문체). 메뉴가 떠 있으면 닫힌 뒤.
 *  - clue: 조사 기록 — 가운데 위 일기장 쪽지, 줄이 하나씩 적힌다. Enter·Esc·누르기로 덮는다(전투·메뉴·층 전환에도 닫힘).
 * 신규 적 첫 등장 소개(`enemyIntro`)는 화면 위쪽 짧은 이름 자막(차례 따로).
 * 망령(주인공)의 말은 없다 — UI 가 붙이는 낱말도 지문·안내뿐(textStory.ts).
 */
export class StoryHud {
  private queue: StoryLineView[] = [];
  private cur?: Showing;
  private note?: { box: Phaser.GameObjects.Container; lines: string[]; title: string; shown: number; at: number };
  private noteTimers: Phaser.Time.TimerEvent[] = [];
  private intros: { name: string; desc: string | null }[] = [];
  private intro?: TimedCard;

  constructor(
    private scene: Phaser.Scene,
    private opts: StoryHudOptions,
  ) {}

  /** 조사 쪽지가 떠 있다 (Esc·Enter 를 받는다) */
  get noteOpen(): boolean {
    return Boolean(this.note);
  }

  /** 지금 떠 있는 줄의 글 (튜토리얼 단계 카드와 같은 문구면 거둔다) */
  get currentText(): string {
    return this.cur?.view.text ?? '';
  }

  /** STORY 페이로드 (잘못된 것은 버린다) */
  push(p: unknown): void {
    const v = readStoryLine(p);
    if (!v) return;
    if (v.channel === 'clue') {
      this.addClue(v);
      return;
    }
    if (v.channel === 'notice') {
      this.showNotice(v);
      return;
    }
    this.queue = enqueueStory(this.queue, v);
    this.pump();
  }

  /** 짧은 안내 한 줄 (공지와 같은 자리·시간) */
  notice(text: string): void {
    this.push({ kind: 'notice', text });
  }

  /** 매 STATE: 막혀 있던 차례를 풀고, 전투가 시작되면 쪽지를 덮는다 */
  tick(inCombat: boolean): void {
    if (this.note && inCombat) this.closeNote();
    this.pump();
  }

  /** 튜토리얼 단계 카드와 같은 문구의 자막은 거둔다 (떠 있는 것·쌓인 것 모두) */
  dropSame(text: string): void {
    this.queue = this.queue.filter((q) => !sameStepText(q.text, text));
    if (this.cur && sameStepText(this.cur.view.text, text)) this.finish(false);
  }

  /** 조사 쪽지를 덮는다 */
  closeNote(): void {
    for (const t of this.noteTimers) t.remove();
    this.noteTimers = [];
    if (this.note) {
      this.scene.tweens.killTweensOf([this.note.box, ...this.note.box.list]);
      this.note.box.destroy();
    }
    this.note = undefined;
    debugExpose('clueNote', null);
  }

  /** 신규 적 첫 등장 소개 (페이로드 `{ name, desc? }`) */
  enemyIntro(p: unknown): void {
    if (!p || typeof p !== 'object') return;
    const o = p as Record<string, unknown>;
    const name = typeof o.name === 'string' ? o.name.trim() : '';
    if (!name) return;
    const desc = typeof o.desc === 'string' && o.desc.trim() ? o.desc.trim() : null;
    if (this.intros.length >= ENEMY_INTRO_UI.queueMax) this.intros.shift();
    this.intros.push({ name, desc });
    if (!this.intro?.alive) this.nextIntro();
  }

  /** 런 끝·층 전환: 쌓인 것과 떠 있는 것을 모두 치운다 */
  reset(): void {
    this.queue = [];
    this.finish(false);
    this.closeNote();
    this.intros = [];
    this.intro?.cancel();
    this.intro = undefined;
  }

  destroy(): void {
    this.reset();
  }

  // ---- 차례

  private pump(): void {
    if (this.cur) return;
    const head = this.queue[0];
    if (!canShowHead(head, !this.opts.canRun(), this.opts.menuOpen())) {
      this.expose();
      return;
    }
    this.queue.shift();
    this.show(head);
  }

  /** 공지: 떠 있는 서사 줄은 차례 맨 앞으로 되돌리고 바로 띄운다 (공지끼리는 바꿔 끼움) */
  private showNotice(v: StoryLineView): void {
    if (!this.opts.canRun()) {
      this.queue = enqueueStory(this.queue, v);
      return;
    }
    if (this.cur && this.cur.view.channel !== 'notice') this.queue.unshift(this.cur.view);
    this.finish(false);
    this.show(v);
  }

  private show(v: StoryLineView): void {
    const holdMs = storyHoldMs(v);
    let box: Phaser.GameObjects.Container;
    const timers: Phaser.Time.TimerEvent[] = [];
    switch (v.channel) {
      case 'voice':
        box = this.buildVoice(v, timers);
        break;
      case 'speech':
        box = this.buildSpeech(v);
        break;
      case 'event':
        box = this.buildEvent(v);
        break;
      default:
        box = this.buildCaption(v);
    }
    box.setDepth(STORY_UI.depth);
    const s: Showing = { view: v, box, timers, holdMs };
    this.cur = s;
    timers.push(
      this.scene.time.delayedCall(holdMs, () => {
        if (this.cur !== s) return;
        this.scene.tweens.add({
          targets: box,
          alpha: 0,
          duration: STORY_UI.fadeMs,
          onComplete: () => {
            if (this.cur === s) this.finish(true);
          },
        });
      }),
    );
    this.opts.onShown?.(v.channel, holdMs + STORY_UI.fadeMs);
    this.expose();
  }

  /** 떠 있는 줄을 치운다. next = true 면 다음 차례 */
  private finish(next: boolean): void {
    const s = this.cur;
    this.cur = undefined;
    if (s) {
      for (const t of s.timers) t.remove();
      this.scene.tweens.killTweensOf([s.box, ...s.box.list]);
      s.box.destroy();
    }
    if (next) this.pump();
    else this.expose();
  }

  // ---- 자리별 그림

  private glow(
    text: string,
    style: Parameters<GlowText['setGlowStyle']>[0],
    opts: { wrap?: number; align?: 'left' | 'center' } = {},
  ): GlowText {
    return new GlowText(this.scene, 0, 0, text, style, { ...opts, stageIndex: this.opts.stageIndex() });
  }

  /** 기존 자막·공지: 하단 가운데 ink_body (패널 없음) */
  private buildCaption(v: StoryLineView): Phaser.GameObjects.Container {
    const t = this.glow(v.text, 'ink_body', { wrap: STORY_UI.captionWrap, align: 'center' });
    t.placeCenter(UI_SCREEN.WIDTH / 2, this.opts.centerBottom() - t.displayHeight);
    return this.scene.add.container(0, 0, [t]);
  }

  /** 군주 대사: 하단 가운데 대사 + 왼쪽 위 화자 이름표 */
  private buildSpeech(v: StoryLineView): Phaser.GameObjects.Container {
    const t = this.glow(v.text, 'ink_body', { wrap: STORY_UI.captionWrap, align: 'center' });
    t.placeCenter(UI_SCREEN.WIDTH / 2, this.opts.centerBottom() - t.displayHeight);
    const objs: Phaser.GameObjects.GameObject[] = [];
    if (v.speaker) {
      const name = this.glow(v.speaker, 'ink_accent');
      const pw = name.displayWidth + SPEECH_UI.platePadX * 2;
      const px = Math.max(8, t.x - 4);
      const py = t.y - SPEECH_UI.plateH - SPEECH_UI.plateGap;
      const plate = inkPanel(this.scene, px, py, pw, SPEECH_UI.plateH);
      name.setPosition(px + SPEECH_UI.platePadX, py + Math.round((SPEECH_UI.plateH - name.displayHeight) / 2));
      objs.push(plate, name);
    }
    objs.push(t);
    debugExpose('storySpeech', { speaker: v.speaker, text: v.text });
    return this.fadeIn(this.scene.add.container(0, 0, objs));
  }

  /** 이벤트 문장: 하단 가운데 종이 띠 (지문체) */
  private buildEvent(v: StoryLineView): Phaser.GameObjects.Container {
    const E = EVENT_UI;
    const t = this.glow(v.lines.join('\n'), 'page_body', { wrap: E.wrap, align: 'center' });
    const min = SLICE.panelPaper.l + SLICE.panelPaper.r;
    const w = Math.max(min, t.displayWidth + E.padX * 2);
    const h = Math.max(min, t.displayHeight + E.padY * 2);
    const x = Math.round(UI_SCREEN.WIDTH / 2 - w / 2);
    const y = this.opts.centerBottom() - h;
    const panel = new NinePanel(this.scene, x, y, KIT.panelPaper, SLICE.panelPaper, w, h);
    t.setPosition(Math.round(x + w / 2 - t.displayWidth / 2), Math.round(y + h / 2 - t.displayHeight / 2));
    debugExpose('storyEvent', { text: v.text });
    return this.fadeIn(this.scene.add.container(0, 0, [panel, t]));
  }

  /**
   * 원한의 한마디: 전투 묶음 바로 위 한 줄 — 무기 빛 세로 줄 + 따옴표 글. 무기마다 글씨 색(스타일)·등장(베어 들어옴·내려앉음·
   * 한 글자씩·낱말씩)·떨림이 다르다 (themeStory VOICE_LOOK).
   */
  private buildVoice(v: StoryLineView, timers: Phaser.Time.TimerEvent[]): Phaser.GameObjects.Container {
    const id = voiceWeapon(v.weapon, this.opts.weaponName());
    const look = voiceLook(id);
    const full = quoteVoice(v.lines.join(' '));
    const steps = revealSteps(full, look.enter);
    const t = this.glow(steps[0], look.style, { wrap: 420 });
    const a = this.opts.voiceAnchor();
    // 글 상자 높이는 다 보인 글로 잡는다 (한 글자씩 나와도 줄이 흔들리지 않게)
    const probe = this.glow(full, look.style, { wrap: 420 });
    const h = probe.displayHeight;
    probe.destroy();
    const x0 = a.x;
    const y0 = a.bottom - VOICE_UI.gapAboveBundle - h;
    const bar = this.scene.add.graphics();
    bar.fillStyle(swatch(this.scene, this.opts.stageIndex(), look.bar), 1).fillRect(0, 3, VOICE_UI.barW, h - 6);
    const tx = VOICE_UI.barW + VOICE_UI.barGap;
    t.setPosition(tx, 0);
    const box = this.scene.add.container(x0, y0, [bar, t]).setAlpha(0);
    const enterFrom = {
      x: look.enter === 'slide' ? -look.enterValue : 0,
      y: look.enter === 'drop' ? -look.enterValue : 0,
    };
    box.setPosition(x0 + enterFrom.x, y0 + enterFrom.y);
    this.scene.tweens.add({
      targets: box,
      alpha: 1,
      x: x0,
      y: y0,
      duration: VOICE_UI.inMs,
      ease: look.enter === 'drop' ? 'Quad.easeIn' : 'Quad.easeOut',
    });
    if (steps.length > 1) {
      let i = 0;
      timers.push(
        this.scene.time.addEvent({
          delay: look.enterValue,
          repeat: steps.length - 2,
          callback: () => {
            i += 1;
            if (t.active) t.setText(steps[Math.min(i, steps.length - 1)]);
          },
        }),
      );
    }
    if (look.jitterAmp > 0 && look.jitterEveryMs > 0) {
      const t0 = this.scene.time.now;
      timers.push(
        this.scene.time.addEvent({
          delay: look.jitterEveryMs,
          loop: true,
          callback: () => {
            if (!t.active) return;
            const j = voiceJitter(look, this.scene.time.now - t0);
            t.setPosition(tx + j.dx, j.dy);
          },
        }),
      );
    }
    debugExpose('storyVoice', { weapon: id, style: look.style, text: full, scene: v.scene });
    return box;
  }

  private fadeIn(box: Phaser.GameObjects.Container): Phaser.GameObjects.Container {
    box.setAlpha(0);
    this.scene.tweens.add({ targets: box, alpha: 1, duration: 200 });
    return box;
  }

  // ---- 조사 쪽지

  /** 조사 기록: 쪽지가 떠 있고 조금 전에 온 줄이면 같은 쪽지에 잇는다, 아니면 새 쪽지 */
  private addClue(v: StoryLineView): void {
    const now = this.scene.time.now;
    const title = v.title ?? storyText('clueTitle');
    if (this.note && now - this.note.at <= CLUE_UI.joinMs && this.note.title === title) {
      this.note.lines.push(...v.lines);
      this.note.at = now;
      this.drawNote();
      return;
    }
    this.closeNote();
    this.note = { box: this.scene.add.container(0, 0), lines: [...v.lines], title, shown: 0, at: now };
    this.drawNote();
    // 줄이 하나씩 적힌다
    this.noteTimers.push(
      this.scene.time.addEvent({
        delay: CLUE_UI.lineEveryMs,
        loop: true,
        callback: () => this.revealNoteLine(),
      }),
      this.scene.time.delayedCall(CLUE_UI.autoCloseMs, () => this.closeNote()),
    );
    this.revealNoteLine();
  }

  private revealNoteLine(): void {
    const n = this.note;
    if (!n || n.shown >= n.lines.length) return;
    n.shown += 1;
    const t = n.box.getByName(`line${n.shown - 1}`) as GlowText | null;
    if (t) this.scene.tweens.add({ targets: t, alpha: 1, duration: CLUE_UI.lineInMs });
    if (n.shown >= n.lines.length) {
      const foot = n.box.getByName('foot') as GlowText | null;
      if (foot) this.scene.tweens.add({ targets: foot, alpha: 1, duration: CLUE_UI.lineInMs });
    }
    this.exposeNote();
  }

  /** 쪽지를 (다시) 그린다: 종이 · 제목 · 괘선 · 줄(아직 안 적힌 줄은 투명) · 덮기 안내 */
  private drawNote(): void {
    const n = this.note;
    if (!n) return;
    const C = CLUE_UI;
    this.scene.tweens.killTweensOf(n.box.list);
    n.box.removeAll(true);
    const inner = C.w - C.pad * 2;
    const title = this.glow(n.title, 'page_title').setPosition(C.pad, C.pad);
    let y = C.pad + title.displayHeight + C.titleGap;
    const r = rule(this.scene, C.pad, y, inner);
    y += 4 + C.titleGap;
    const lines = n.lines.map((l, i) => {
      const t = this.glow(l, 'page_body', { wrap: inner }).setPosition(C.pad, y);
      t.setName(`line${i}`).setAlpha(i < n.shown ? 1 : 0);
      y += t.displayHeight + C.lineGap;
      return t;
    });
    y += C.footGap - C.lineGap;
    const foot = this.glow(storyText('clueClose'), 'page_faint');
    foot
      .placeRight(C.w - C.pad, y)
      .setName('foot')
      .setAlpha(n.shown >= n.lines.length ? 1 : 0);
    y += foot.displayHeight + C.pad;
    const h = Math.max(SLICE.panelPaper.t + SLICE.panelPaper.b, y);
    const panel = new NinePanel(this.scene, 0, 0, KIT.panelPaper, SLICE.panelPaper, C.w, h);
    // 누르면 덮는다 (쪽지 전체)
    const zone = this.scene.add.zone(0, 0, C.w, h).setOrigin(0, 0).setInteractive({ useHandCursor: true });
    zone.on('pointerup', () => this.closeNote());
    n.box.add([panel, zone, title, r, ...lines, foot]);
    n.box.setPosition(Math.round(UI_SCREEN.WIDTH / 2 - C.w / 2), C.top).setDepth(C.depth);
    this.exposeNote();
  }

  // ---- 신규 적 소개

  private nextIntro(): void {
    const it = this.intros.shift();
    if (!it) return;
    const I = ENEMY_INTRO_UI;
    const si = this.opts.stageIndex();
    const name = this.glow(it.name, 'ink_accent');
    const cx = UI_SCREEN.WIDTH / 2;
    name.placeCenter(cx, 0);
    const objs: Phaser.GameObjects.GameObject[] = [];
    const tag = this.glow(storyText('enemyIntroTag'), 'ink_faint');
    tag.placeCenter(cx, 0);
    name.setY(tag.displayHeight);
    const g = this.scene.add.graphics();
    const midY = name.y + Math.round(name.displayHeight / 2);
    g.fillStyle(swatch(this.scene, si, { gray: 0 }), 1)
      .fillRect(name.x - I.ruleGap - I.ruleW, midY - 1, I.ruleW, 3)
      .fillRect(name.x + name.displayWidth + I.ruleGap, midY - 1, I.ruleW, 3);
    g.fillStyle(swatch(this.scene, si, { slot: I.ruleSlot }), 1)
      .fillRect(name.x - I.ruleGap - I.ruleW, midY, I.ruleW, 1)
      .fillRect(name.x + name.displayWidth + I.ruleGap, midY, I.ruleW, 1);
    objs.push(tag, g, name);
    if (it.desc) {
      const d = this.glow(it.desc, 'ink_faint');
      d.placeCenter(cx, name.y + name.displayHeight);
      objs.push(d);
    }
    const box = this.scene.add.container(0, I.top, objs).setDepth(STORY_UI.depth);
    this.intro = new TimedCard(this.scene, box, { inMs: I.inMs, holdMs: I.holdMs, outMs: I.fadeMs, drop: 4 }, () =>
      this.nextIntro(),
    );
    debugExpose('enemyIntro', { name: it.name, desc: it.desc });
  }

  // ---- 디버그

  private expose(): void {
    debugExpose('story', {
      showing: this.cur ? { channel: this.cur.view.channel, text: this.cur.view.text, holdMs: this.cur.holdMs } : null,
      queued: this.queue.map((q) => `${q.channel}:${q.text}`),
    });
  }

  private exposeNote(): void {
    const n = this.note;
    debugExpose('clueNote', n ? { title: n.title, lines: n.lines, shown: n.shown } : null);
  }
}
