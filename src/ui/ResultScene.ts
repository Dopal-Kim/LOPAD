import Phaser from 'phaser';
import { UI_SCREEN, uiCommands, type UiEndChoice, type UiMemoryBook, type UiResult } from '../contract/ui';
import { GlowText } from './glow';
import { fill } from './fmt';
import { DARK_BG, KIT, accentHex, book, fontsReady, preloadKit, rule, setupKit } from './kit';
import { takeKey } from './keyGate';
import { UI_SCENE_KEYS } from './keys';
import { LAYOUT, hexToNum } from './theme';
import { SelectList } from './widgets';
import type { ChoiceGate } from './choiceGate';
import { armBar, keyTime, openGate } from './choiceArm';
import { MemoryBookView } from './MemoryBook';
import { nextLine } from './memoryView';
import { preloadResultMap } from './ResultMap';
import { deathPages, floorEndPages, type PagesOut } from './ResultPages';
import { endButtons, legacySummary, resultKind, type EndButton } from './resultView';
import { l2eText } from './textLoop2E';
import { RESULT_UI as RU } from './themeLoop2E';

/**
 * 결과 화면 = 결산 일기장 두 쪽 펼침 (62 루프 2 UI E — 계약 C `UiResult.summary`·`floorEnd`, 그림은 ResultPages.ts).
 *  - 사망 결산: 처치자 초상 · 지나온 길 미니맵(망령 표식) · 시간·처치·받은 피해 · 지닌 것 아이콘 줄 · 영혼 +n · 다음 기억 한 줄
 *  - 층 끝: '1층 끝' 일기장 마지막 장 — 오른쪽 빈 괘선 장에 '여기까지 적었다. 다음 장은 아직 그려지지 않았다.'를 한 글자씩 쓴 뒤 버튼
 *  - 버튼: [1] 다시 태어난다 · [2] 기억을 떠올린다(기억 장 덧그림 — MemoryBook) · [3] 일기장을 덮는다 → `uiCommands.endChoice`
 *    (없으면 startNewRun · toTitle). Esc = 일기장을 덮는다. 시드는 '세부 보기 (D)' 안.
 *  - 입력은 UI D 공통 무장 게이트(choiceGate) — 쓰러지는 순간 누르던 키·클릭으로 고르지 않는다. 층 끝은 버튼이 뜰 때 연다.
 * 옛 감각(눈 아이콘)·전표 줄은 지웠다(P16 §1 · 용어집).
 */
export class ResultScene extends Phaser.Scene {
  private list?: SelectList;
  private alive = false;
  /** 62 루프 2 UI D: 결산 버튼 무장 (쓰러지는 순간 누르던 키·클릭으로 고르지 않게 — choiceGate.ts) */
  private gate?: ChoiceGate;
  private memory?: MemoryBookView;
  private memoryChanged = false;
  private out?: PagesOut;
  private seedText?: GlowText;
  private seed = '';

  constructor() {
    super(UI_SCENE_KEYS.RESULT);
  }

  preload(): void {
    preloadKit(this);
    preloadResultMap(this);
  }

  create(r: UiResult): void {
    this.alive = true;
    this.list = undefined;
    this.memory = undefined;
    this.gate = undefined;
    setupKit(this);
    this.cameras.main.setBackgroundColor(DARK_BG);
    // 51라운드 §6: Esc = 한 단계 뒤로 (결과 화면의 앞은 타이틀 — '일기장을 덮는다' 와 같다)
    this.input.keyboard?.on('keydown-ESC', this.onEsc);
    this.input.keyboard?.on('keydown-D', this.onDetail);
    this.events.once('shutdown', () => {
      this.alive = false;
      this.input.keyboard?.off('keydown-ESC', this.onEsc);
      this.input.keyboard?.off('keydown-D', this.onDetail);
      this.memory?.destroy();
      this.memory = undefined;
      this.list?.destroy();
    });
    fontsReady().then(() => {
      if (this.alive) this.build(r);
    });
  }

  private onEsc = (e?: KeyboardEvent): void => {
    if (e?.repeat || this.memory || !this.list || !takeKey(e)) return;
    if (e && this.gate && !this.gate.keyOk(e.code, keyTime(e), e.repeat)) return;
    this.end('closeDiary');
  };

  private onDetail = (e?: KeyboardEvent): void => {
    if (e?.repeat || this.memory || !this.seedText) return;
    this.seedText.setText(fill(l2eText('detailOpen'), { seed: this.seed }));
  };

  /** 결과 화면 두 선택 (계약 C `endChoice` — 없으면 옛 명령) */
  private end(c: UiEndChoice): void {
    if (uiCommands.endChoice(c)) return;
    if (c === 'reborn') uiCommands.startNewRun();
    else uiCommands.toTitle();
  }

  private build(r: UiResult): void {
    const W = UI_SCREEN.WIDTH;
    const H = UI_SCREEN.HEIGHT;
    const si = Math.max(0, r.floorReached - 1);
    const kind = resultKind(r);
    const bk = book(this, Math.round(W / 2), Math.round(H / 2), RU.pageW, RU.pageH, 2, `result:${kind}`);
    const L = bk.pages[0];
    const R = bk.pages[1];
    const innerW = RU.pageW - RU.pad * 2;
    this.out =
      kind === 'floorEnd' && r.floorEnd
        ? floorEndPages(this, r.floorEnd, r.summary, L, R, si)
        : deathPages(this, r, r.summary ?? legacySummary(r), L, R, si);
    // 62 P2-9: 시드는 세부 접기 안 — '세부 보기' 를 누르면(또는 D) 펼친다 (피드백 대조용)
    this.seed = r.seed;
    this.seedText = new GlowText(
      this,
      L.x + RU.pad,
      L.y + RU.pageH - RU.pad - 12,
      l2eText('detailClosed'),
      'page_faint',
    )
      .makeInteractive()
      .on('pointerup', () => this.onDetail());
    // 도장 (사망 · 층 끝)
    const stampKey = kind === 'floorEnd' || r.cleared ? KIT.stampClear : KIT.stampDead;
    const stamp = this.textures.exists(stampKey)
      ? this.add.image(R.x + RU.pageW - RU.pad - 24, R.y + RU.pageH - RU.pad - 24, stampKey).setAlpha(0)
      : null;
    const buttons = endButtons(r.floorEnd, buttonText(), Boolean(uiCommands.memory.book()));
    const at = this.out.buttonsAt;
    const show = (): void => {
      if (!this.alive) return;
      this.showButtons(buttons, R.x + RU.pad, this.out!.buttonsY, innerW, si);
      if (stamp) {
        stamp.setScale(1.25);
        this.tweens.add({ targets: stamp, alpha: LAYOUT.stampAlpha, scale: 1, duration: 220, ease: 'Back.easeOut' });
      }
    };
    if (at > 0) this.time.delayedCall(at, show);
    else show();
  }

  private showButtons(buttons: EndButton[], x: number, y: number, w: number, si: number): void {
    rule(this, x, y, w);
    this.gate = openGate();
    armBar(this, this.gate, x, y + 1, w, hexToNum(accentHex(this, si, 20)), 2);
    this.list = new SelectList(
      this,
      x,
      y + 4 + 10,
      (key) => {
        const b = buttons[Number(key) - 1];
        if (!b) return;
        if (b.key === 'memory') this.openMemory(si);
        else this.end(b.key);
      },
      // 62 루프 2: 렌더러 메뉴 소리는 UI 몫 (시스템 F — 이동·고르기)
      { stageIndex: si, detailWrap: w - 40, gate: this.gate, sounds: true },
    );
    this.list.setLines(buttons.map((b, i) => ({ key: String(i + 1), label: b.label, enabled: true })));
  }

  /** 기억 장 덧그림 (닫으면 결산으로 — 영혼 줄은 새 기억 장으로 바꾼다) */
  private openMemory(si: number): void {
    if (this.memory) return;
    this.list?.setEnabled(false);
    this.memory = new MemoryBookView(this, {
      stageIndex: si,
      gate: openGate(),
      depth: 50,
      book: () => uiCommands.memory.book(),
      recall: (id) => {
        const ok = uiCommands.memory.unlock(id);
        if (ok) this.memoryChanged = true;
        return ok;
      },
      setKeepsake: (id) => uiCommands.memory.setKeepsake(id),
      close: () => this.closeMemory(),
      handleEsc: true,
      live: true,
      backdrop: true,
    });
  }

  private closeMemory(): void {
    this.memory?.destroy();
    this.memory = undefined;
    // 닫은 키가 결산 버튼으로 넘어가지 않게 한 박자 뒤에
    this.time.delayedCall(0, () => this.list?.setEnabled(true));
    if (this.memoryChanged && this.out?.soulsLine) {
      const b: UiMemoryBook | null = uiCommands.memory.book();
      if (b) this.out.soulsLine.setText(nextLine(b.next));
    }
  }
}

/** 버튼 글 — 스토리 63 팩 deathSummary.buttons (옛 팩 result.retry 는 '영혼 → 유산' 꼬리가 있어 쓰지 않는다) */
function buttonText(): { reborn: string; memory: string; closeDiary: string } {
  return { reborn: l2eText('reborn'), memory: l2eText('memory'), closeDiary: l2eText('closeDiary') };
}
