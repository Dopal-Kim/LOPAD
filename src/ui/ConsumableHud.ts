import Phaser from 'phaser';
import type { consumableView } from './buildView';
import { GlowText } from './glow';
import { accentHex } from './kit';
import { KeyCap } from './keycap';
import { GRAY, hexToNum } from './theme';
import { CONSUMABLE } from './themeBuild';

/** 병 그림 (8×12 칸, 1 = 몸 G12 · 2 = 마개 G08 · 3 = 불씨(투척) 층 강조 22) — 소모품 아이콘 3종이 오기 전 임시 */
const BOTTLE = [
  '...22...',
  '...22...',
  '..1111..',
  '...11...',
  '..1111..',
  '.111111.',
  '.111111.',
  '.111111.',
  '.111111.',
  '.111111.',
  '.111111.',
  '..1111..',
];

type View = NonNullable<ReturnType<typeof consumableView>>;

/**
 * 60라운드 계약 §14.8 소모품 칸 — 하단 묶음 1행 독주(Q) 오른쪽: 병 그림 + 'n/m' + 사용 키(시스템 `consumable.key`, 현재 C).
 * 61라운드: 왼쪽 아래 전투 묶음 아래 행, 사용 키는 키캡.
 * 빈 칸이면 병 윤곽만 흐리게 + '빈 칸'. 이름은 사용 토스트·일기장에서. 투척(throw)은 마개 자리에 불씨 점.
 * Container(Graphics → 글) 하나라 하단 묶음과 함께 setY 로 움직인다.
 */
export class ConsumableChip extends Phaser.GameObjects.Container {
  private g: Phaser.GameObjects.Graphics;
  private countT: GlowText;
  private keyT: KeyCap;
  private sig = '';
  /** 그린 폭 (`w` 는 Phaser Transform 의 4번째 좌표라 setPosition 이 0 으로 되돌린다 — 61라운드 이름 바꿈) */
  boxW = 0;

  constructor(scene: Phaser.Scene, x: number, y: number, stageIndex: number) {
    super(scene, x, y);
    this.g = scene.add.graphics();
    this.countT = new GlowText(scene, 0, 1, '', 'ink_body', { stageIndex });
    // 61라운드: 사용 키를 키캡으로 (독주 Q 와 같은 문체)
    this.keyT = new KeyCap(scene, 0, 0, 'C', true);
    this.add([this.g, this.countT, this.keyT]);
    scene.add.existing(this);
  }

  setStageIndex(si: number): void {
    this.countT.setStageIndex(si);
    this.sig = '';
  }

  /** maxW = 쓸 수 있는 폭 — 빈 칸 글('빈 칸')이 넘치면 병 윤곽 + 키만 */
  render(v: View | null, si: number, maxW = Infinity): void {
    const sig = v ? `${si}|${v.key}|${v.empty}|${v.count}|${v.kind}|${v.name}|${maxW}` : '';
    if (sig === this.sig) return;
    this.sig = sig;
    this.setVisible(Boolean(v));
    if (!v) {
      this.boxW = 0;
      return;
    }
    const g = this.g.clear();
    const body = hexToNum(GRAY[12]);
    const cap = v.kind === 'throw' ? hexToNum(accentHex(this.scene, si, 22)) : hexToNum(GRAY[8]);
    const dim = hexToNum(GRAY[5]);
    const oy = 2;
    BOTTLE.forEach((row, y) =>
      [...row].forEach((c, x) => {
        if (c === '.') return;
        if (v.empty) {
          // 빈 칸: 윤곽만 (이웃이 비어 있는 칸)
          const edge = [
            [x - 1, y],
            [x + 1, y],
            [x, y - 1],
            [x, y + 1],
          ].some(([ax, ay]) => (BOTTLE[ay]?.[ax] ?? '.') === '.');
          if (edge) g.fillStyle(dim, 1).fillRect(x, y + oy, 1, 1);
          return;
        }
        g.fillStyle(c === '1' ? body : cap, 1).fillRect(x, y + oy, 1, 1);
      }),
    );
    let x = CONSUMABLE.iconW + 4;
    this.countT
      .setText(v.empty ? v.name : v.count)
      .setGlowStyle(v.empty ? 'ink_faint' : 'ink_body')
      .setX(x)
      .setAlpha(v.empty ? CONSUMABLE.emptyAlpha : 1);
    x += this.countT.textW + 6;
    this.keyT.setLabel(v.key).setFaint(v.empty).setX(x);
    this.boxW = x + this.keyT.width;
    if (v.empty && this.boxW > maxW) {
      this.countT.setText('');
      x = CONSUMABLE.iconW + 4;
      this.keyT.setX(x);
      this.boxW = x + this.keyT.width;
    }
  }
}
