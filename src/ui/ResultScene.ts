import Phaser from 'phaser';
import { UI_SCREEN, uiCommands, type UiResult } from '../contract/ui';
import { GlowText } from './glow';
import { DARK_BG, ICON, KIT, book, fontsReady, icon, preloadKit, rule, setupKit } from './kit';
import { takeKey } from './keyGate';
import { UI_SCENE_KEYS } from './keys';
import { uiText } from './text';
import { LAYOUT } from './theme';
import { SelectList } from './widgets';

const PAGE_W = 292;
const PAGE_H = 400;
const PAD = 20;

/**
 * 런 결과 = 두 페이지 펼침 (책 틀 632×432, 페이지 292×400 ×2 + spine).
 * 왼쪽: 제목 '한 생을 다 썼다'(클리어) / '쓰러졌다'(사망) + 닫힌 일기장 + 기록.
 * 오른쪽: 스토리 문장(line) · 엔딩 부제 · [1] 다시 태어난다 / [2] 일기장을 덮는다 · 도장.
 */
export class ResultScene extends Phaser.Scene {
  private list?: SelectList;
  private alive = false;

  constructor() {
    super(UI_SCENE_KEYS.RESULT);
  }

  preload(): void {
    preloadKit(this);
  }

  create(r: UiResult): void {
    this.alive = true;
    setupKit(this);
    this.cameras.main.setBackgroundColor(DARK_BG);
    // 51라운드 §6: Esc = 한 단계 뒤로 (결과 화면의 앞은 타이틀 — '일기장을 덮는다' 와 같다)
    this.input.keyboard?.on('keydown-ESC', this.onEsc);
    this.events.once('shutdown', () => {
      this.alive = false;
      this.input.keyboard?.off('keydown-ESC', this.onEsc);
      this.list?.destroy();
    });
    fontsReady().then(() => {
      if (this.alive) this.build(r);
    });
  }

  private onEsc = (e?: KeyboardEvent): void => {
    if (e?.repeat || !this.list || !takeKey(e)) return;
    uiCommands.toTitle();
  };

  private build(r: UiResult): void {
    const W = UI_SCREEN.WIDTH;
    const H = UI_SCREEN.HEIGHT;
    const stageIndex = Math.max(0, r.floorReached - 1);
    const bk = book(
      this,
      Math.round(W / 2),
      Math.round(H / 2),
      PAGE_W,
      PAGE_H,
      2,
      `result:${r.cleared ? 'clear' : 'dead'}`,
    );
    const L = bk.pages[0];
    const R = bk.pages[1];
    const innerW = PAGE_W - PAD * 2;

    // ---- 왼쪽 페이지: 제목 · 닫힌 일기장 · 기록
    let y = L.y + 18;
    const title = new GlowText(
      this,
      0,
      0,
      r.cleared ? uiText('result', 'cleared', '한 생을 다 썼다') : uiText('result', 'died', '쓰러졌다'),
      'page_title',
      { font: 'title', stageIndex },
    );
    title.placeCenter(L.x + PAGE_W / 2, y);
    y += title.displayHeight + 6;
    rule(this, L.x + PAD, y, innerW);
    y += 4 + 12;
    if (this.textures.exists(KIT.diaryClosed)) {
      this.add.image(L.x + PAGE_W / 2, y + 32, KIT.diaryClosed);
      y += 64 + 12;
    }
    // 61 P7: 이름은 따로 그려 사망 시 번지게 한다 (smudgeLine)
    const nameT = new GlowText(this, L.x + PAD, y, r.playerName || '―', 'page_body', { stageIndex });
    const where = new GlowText(
      this,
      nameT.x + nameT.displayWidth + 8,
      y,
      `${r.stageName}  (도달 ${r.floorReached}층)`,
      'page_body',
      { wrap: innerW - nameT.displayWidth - 8, stageIndex },
    );
    y += Math.max(nameT.displayHeight, where.displayHeight) + 6;
    const body = (text: string, yy: number, x = L.x + PAD): GlowText =>
      new GlowText(this, x, yy, text, 'page_body', { wrap: innerW, stageIndex });
    body(`처치 ${r.kills}`, y);
    y += 18;
    // 재화·영혼·감각은 아이콘 + 수치 (names 는 결과 페이로드에 없다)
    icon(this, L.x + PAD, y - 1, ICON.gold);
    body(String(r.gold), y, L.x + PAD + 20);
    icon(this, L.x + PAD + 100, y - 1, ICON.sense);
    body(String(r.sense), y, L.x + PAD + 120);
    y += 20;
    icon(this, L.x + PAD, y - 1, ICON.souls);
    body(`+${r.soulsGained}  (보유 ${r.soulsTotal})`, y, L.x + PAD + 20);
    y += 20;
    body(`무기 ${r.weaponName}`, y);
    new GlowText(this, L.x + PAD, L.y + PAGE_H - PAD - 16, `시드 ${r.seed}`, 'page_faint');

    // ---- 오른쪽 페이지: 스토리 문장 · 엔딩 부제 · 선택 · 도장
    y = R.y + 22;
    if (r.line) {
      const line = new GlowText(this, R.x + PAD, y, r.line, 'page_body', { wrap: innerW, stageIndex });
      y += line.displayHeight + 10;
    }
    // 61 P7 (계약 `UiResult.smudgeLine`): 사망 문장 뒤 '이름이 번진다.' — 조금 늦게 나타나며 왼쪽 이름이 번진다
    const smudge = (r as { smudgeLine?: unknown }).smudgeLine;
    if (!r.cleared && typeof smudge === 'string' && smudge.trim()) {
      const sl = new GlowText(this, R.x + PAD, y, smudge.trim(), 'page_faint', { wrap: innerW, stageIndex }).setAlpha(
        0,
      );
      y += sl.displayHeight + 10;
      this.time.delayedCall(RESULT_SMUDGE.delayMs, () => {
        this.tweens.add({ targets: sl, alpha: 1, duration: RESULT_SMUDGE.inMs });
        smudgeName(this, nameT, r.playerName || '―', stageIndex);
      });
    }
    const endingKey =
      r.ending === 'destroy' ? 'clearedDestroy' : r.ending === 'understand' ? 'clearedUnderstand' : null;
    if (r.cleared && endingKey) {
      const sub = new GlowText(
        this,
        R.x + PAD,
        y,
        uiText('result', endingKey, r.ending === 'destroy' ? '다음 전장으로' : '처음으로 내일을 적었다'),
        'page_title',
        { wrap: innerW, stageIndex },
      );
      y += sub.displayHeight + 10;
    }
    rule(this, R.x + PAD, y, innerW);
    y += 4 + 12;
    this.list = new SelectList(
      this,
      R.x + PAD,
      y,
      (key) => {
        if (key === '1') uiCommands.startNewRun();
        else uiCommands.toTitle();
      },
      { stageIndex, detailWrap: innerW - 40 },
    );
    this.list.setLines([
      { key: '1', label: uiText('result', 'retry', '다시 태어난다 (영혼 → 개성 선택)'), enabled: true },
      { key: '2', label: uiText('result', 'toTitle', '일기장을 덮는다'), enabled: true },
    ]);
    const stampKey = r.cleared ? KIT.stampClear : KIT.stampDead;
    if (this.textures.exists(stampKey)) {
      this.add.image(R.x + PAGE_W - PAD - 24, R.y + PAGE_H - PAD - 24, stampKey).setAlpha(LAYOUT.stampAlpha);
    }
  }
}

/** 61 P7 이름 번짐 (결과 화면): 나타나는 때·시간, 번진 자국 오프셋 (정수 px — 흐림 금지라 겹친 사본으로 번짐) */
const RESULT_SMUDGE = {
  delayMs: 900,
  inMs: 700,
  offsets: [
    [1, 1],
    [2, 2],
    [3, 1],
  ] as [number, number][],
  /** 번진 뒤 원래 글자 알파 (허용 알파 0.55) */
  nameAlpha: 0.55,
} as const;

/** 이름 글자를 흐리게(허용 알파) 하고 오른쪽 아래로 흐린 사본을 겹쳐 '번진' 자국을 만든다 (page_faint) */
function smudgeName(scene: Phaser.Scene, name: GlowText, text: string, stageIndex: number): void {
  scene.tweens.add({ targets: name, alpha: RESULT_SMUDGE.nameAlpha, duration: RESULT_SMUDGE.inMs });
  for (const [dx, dy] of RESULT_SMUDGE.offsets) {
    const ghost = new GlowText(scene, name.x + dx, name.y + dy, text, 'page_faint', { stageIndex }).setAlpha(0);
    scene.tweens.add({ targets: ghost, alpha: 1, duration: RESULT_SMUDGE.inMs });
  }
}
