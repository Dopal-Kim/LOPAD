import Phaser from 'phaser';
import { COLORS, DEPTH, GAME, KEYS, PROTOTYPE, SCENES } from '../core/Constants';
import { PERSONALITY, STORY, WEAPONS } from '../data';
import { fill } from '../systems/story';
import type { Affinity } from '../data/types';
import { chooseWeapon, rhythmFeatures, strokeFeatures, type RhythmSample, type Stroke } from '../systems/personality';
import { META_CONFIG, buyUpgrade, metaStore, upgradeCost } from '../systems/meta';
import { TextMenu } from '../systems/TextMenu';
import { setMenuSelect } from '../contract/host';
import { UI_EVENTS, __system } from '../contract/ui';

type Phase = 'meta' | 'name' | 'strokes' | 'rhythm' | 'fate';

/**
 * 개성 선택 (기획 1장): "가장 강한 것"을 3획으로 그리고, 5초간 자유롭게 입력한 리듬을 합쳐
 * 성향 벡터를 만들고 가장 가까운 무기를 '운명'으로 정한다.
 * 화면·연출은 시스템 파트 플레이스홀더이며 UI·아트 파트 산출물로 교체 대상.
 */
const NAME_MAX = 12;

export class Setup extends Phaser.Scene {
  private phase: Phase = 'strokes';
  private strokes: Stroke[] = [];
  private current: Stroke | null = null;
  private gfx: Phaser.GameObjects.Graphics;
  private label: Phaser.GameObjects.Text;
  private rhythm: RhythmSample = { frames: 0, movingFrames: 0, attacks: 0, dashes: 0 };
  private rhythmEndAt = 0;
  private keys: Record<string, Phaser.Input.Keyboard.Key>;
  private features?: Affinity;
  private menu: TextMenu;
  private onEnter?: (e: KeyboardEvent) => void;
  /** 일기장 이름 입력 (26라운드): DOM input, 최대 12자 */
  private nameInput?: Phaser.GameObjects.DOMElement;
  private playerName = '';

  constructor() {
    super(SCENES.SETUP);
  }

  create(): void {
    this.phase = 'meta';
    this.strokes = [];
    this.current = null;
    this.playerName = '';
    this.rhythm = { frames: 0, movingFrames: 0, attacks: 0, dashes: 0 };
    this.gfx = this.add.graphics().setDepth(DEPTH.ATTACK);
    this.label = this.add
      .text(GAME.WIDTH / 2, 24, '', { font: '12px monospace', color: COLORS.GAMEOVER_TEXT, align: 'center' })
      .setOrigin(0.5, 0)
      .setDepth(DEPTH.DEBUG);
    const kb = this.input.keyboard!;
    this.keys = {
      up: kb.addKey(KEYS.UP),
      down: kb.addKey(KEYS.DOWN),
      left: kb.addKey(KEYS.LEFT),
      right: kb.addKey(KEYS.RIGHT),
      dash: kb.addKey(KEYS.DASH),
    };
    this.input.mouse?.disableContextMenu();

    this.input.on('pointerdown', this.onPointerDown, this);
    this.input.on('pointermove', this.onPointerMove, this);
    this.input.on('pointerup', this.onPointerUp, this);
    this.events.once('shutdown', () => {
      this.input.off('pointerdown', this.onPointerDown, this);
      this.input.off('pointermove', this.onPointerMove, this);
      this.input.off('pointerup', this.onPointerUp, this);
      this.nameInput?.destroy();
      this.nameInput = undefined;
      this.input.keyboard?.enableGlobalCapture();
    });
    this.menu = new TextMenu(this);
    setMenuSelect((id, key) => {
      if (id === 'meta' && key === 'enter') this.beginName();
      else this.menu.select(key, id);
    });
    this.events.once('shutdown', () => setMenuSelect(null));
    this.openMetaMenu();
  }

  /** 런 시작 전: 영혼으로 영구 강화 구매, 도감 요약. Enter 로 개성 선택 시작 (임시 텍스트) */
  private openMetaMenu(): void {
    const meta = metaStore.read();
    const lines = META_CONFIG.upgrades.map((u, i) => {
      const lv = meta.upgrades[u.id] ?? 0;
      const maxed = lv >= u.maxLevel;
      const cost = maxed ? 0 : upgradeCost(u, lv);
      return {
        key: String(i + 1),
        label: `${u.name}  Lv ${lv}/${u.maxLevel}${maxed ? '  MAX' : `  ${cost} 영혼`}`,
        enabled: !maxed && meta.souls >= cost,
      };
    });
    const codex = Object.entries(WEAPONS)
      .map(([id, w]) => {
        const c = meta.codex[id];
        return c ? `${w.name} ★${c.maxStage} 처치 ${c.kills} 최고 ${c.bestFloor}층` : `${w.name} -`;
      })
      .join('  ·  ');
    this.menu.open(
      'meta',
      `영혼 ${meta.souls}   (런 ${meta.runs}회, 클리어 ${meta.clears}회, 최고 ${meta.bestFloor}층)`,
      lines,
      (key) => {
        const u = META_CONFIG.upgrades[Number(key) - 1];
        const next = buyUpgrade(metaStore.read(), u.id);
        if (next) {
          metaStore.write(next);
          this.openMetaMenu();
        }
      },
      `도감: ${codex}\n\n[Enter] 일기장을 펼친다`,
    );
    if (!this.onEnter) {
      this.onEnter = (e: KeyboardEvent) => {
        if (e.key === 'Enter' && this.phase === 'meta') this.beginName();
      };
      this.input.keyboard?.on('keydown', this.onEnter);
      this.events.once('shutdown', () => {
        if (this.onEnter) this.input.keyboard?.off('keydown', this.onEnter);
        this.onEnter = undefined;
        this.menu.close();
      });
    }
  }

  /** 일기장 첫 장: 이름을 적는다. 비우면 '―' 로 기록된다 (26라운드) */
  private beginName(): void {
    if (this.phase !== 'meta') return; // 메뉴 선택과 keydown 이 둘 다 Enter 를 전달하므로 한 번만
    this.menu.close();
    this.phase = 'name';
    this.label.setText(`${STORY.diary.first}\n\n이름을 적고 Enter`);
    const kb = this.input.keyboard!;
    kb.disableGlobalCapture();
    this.nameInput = this.add
      .dom(
        GAME.WIDTH / 2,
        GAME.HEIGHT / 2,
        'input',
        'width:200px;font:14px monospace;background:#101018;color:#e8e8f0;border:1px solid #777;padding:4px;text-align:center;outline:none',
      )
      .setDepth(DEPTH.DEBUG);
    const node = this.nameInput.node as HTMLInputElement;
    node.maxLength = NAME_MAX;
    node.placeholder = '이름';
    node.id = 'lopad-name';
    node.addEventListener('keydown', (e) => {
      e.stopPropagation();
      if (e.key === 'Enter') this.finishName(node.value);
    });
    node.focus();
  }

  private finishName(raw: string): void {
    if (this.phase !== 'name') return;
    this.playerName = raw.trim().slice(0, NAME_MAX);
    this.nameInput?.destroy();
    this.nameInput = undefined;
    this.input.keyboard?.enableGlobalCapture();
    this.beginStrokes();
  }

  private beginStrokes(): void {
    this.menu.close();
    this.phase = 'strokes';
    this.updateLabel();
  }

  update(time: number): void {
    if (this.phase !== 'rhythm') return;
    this.rhythm.frames += 1;
    if (this.keys.up.isDown || this.keys.down.isDown || this.keys.left.isDown || this.keys.right.isDown)
      this.rhythm.movingFrames += 1;
    if (Phaser.Input.Keyboard.JustDown(this.keys.dash)) this.rhythm.dashes += 1;
    const left = Math.max(0, this.rhythmEndAt - time);
    this.label.setText(
      `이제 5초 동안 자신답게 움직여 보세요 (WASD · 클릭 · 스페이스)\n남은 시간 ${(left / 1000).toFixed(1)}초`,
    );
    if (left <= 0) this.decideFate();
  }

  private onPointerDown(p: Phaser.Input.Pointer): void {
    if (this.phase === 'strokes') {
      this.current = [{ x: p.x, y: p.y, t: p.downTime }];
    } else if (this.phase === 'rhythm') {
      this.rhythm.attacks += 1;
    }
  }

  private onPointerMove(p: Phaser.Input.Pointer): void {
    if (this.phase !== 'strokes' || !this.current || !p.isDown) return;
    const last = this.current[this.current.length - 1];
    if (Math.hypot(p.x - last.x, p.y - last.y) < 2) return;
    this.current.push({ x: p.x, y: p.y, t: p.moveTime });
    this.gfx.lineStyle(2, COLORS.STROKE, 1);
    this.gfx.lineBetween(last.x, last.y, p.x, p.y);
  }

  private onPointerUp(p: Phaser.Input.Pointer): void {
    if (this.phase !== 'strokes' || !this.current) return;
    this.current.push({ x: p.x, y: p.y, t: p.upTime });
    if (this.current.length >= PERSONALITY.strokes.minPoints) this.strokes.push(this.current);
    this.current = null;
    if (this.strokes.length >= PERSONALITY.strokes.count) {
      this.phase = 'rhythm';
      this.rhythmEndAt = this.time.now + PERSONALITY.rhythm.durationMs;
    }
    this.updateLabel();
  }

  private updateLabel(): void {
    if (this.phase === 'strokes') {
      this.label.setText(
        `${STORY.diary.beforeFate}  (${this.strokes.length}/${PERSONALITY.strokes.count})\n마우스를 누른 채 긋고 떼면 한 획`,
      );
    }
  }

  private decideFate(): void {
    this.phase = 'fate';
    const f: Affinity = { ...strokeFeatures(this.strokes, PERSONALITY), ...rhythmFeatures(this.rhythm, PERSONALITY) };
    this.features = f;
    const { id } = chooseWeapon(f, WEAPONS, PERSONALITY);
    const w = WEAPONS[id];
    __system.emit(UI_EVENTS.FATE_DECIDED, { weaponName: w.name, features: f });
    this.label.setText(
      `${this.playerName || '―'}\n\n${fill(STORY.diary.fate, { weapon: w.name })}\n\n(획 길이 ${f.strokeLength.toFixed(2)} 속도 ${f.strokeSpeed.toFixed(2)} 직선 ${f.straightness.toFixed(2)} · 이동 ${f.keyMove.toFixed(2)} 공격 ${f.keyAttack.toFixed(2)} 대쉬 ${f.keyDash.toFixed(2)})`,
    );
    this.time.delayedCall(PROTOTYPE.FATE_BANNER_MS, () =>
      this.scene.start(SCENES.GAME, { mode: 'new', weapon: id, playerName: this.playerName }),
    );
  }

  /** 디버그/테스트용 */
  get debugFeatures(): Affinity | undefined {
    return this.features;
  }
}
