/**
 * 49라운드 계약 §11.4 무기 시험장 (씬 키 WeaponLab, 같은 전투 코드를 lab 플래그로 재사용):
 * 연습 런 준비 · 작은 아레나 · 허수아비 · L(무기·개성 갈래 메뉴) · Esc(타이틀) · 죽지 않음.
 */
import Phaser from 'phaser';
import { KEYS, LAB, TILE } from '../../core/Constants';
import { EventBus, Events } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { PLAYER_DATA, WEAPONS, WEAPON_RULES } from '../../data';
import { __system, uiCommands } from '../../contract/ui';
import { LabDummy } from '../../objects/LabDummy';
import { generateArena, type FloorLayout } from '../../systems/mapgen';
import { ROUTE } from '../../systems/route';
import {
  LAB_CANCEL_KEY,
  LAB_TO_BRANCH_KEY,
  labBranchMenu,
  labWeaponMenu,
  nextReinforce,
} from '../../systems/weaponLab';
import type { Game } from '../Game';
import type { GameInitData } from './shared';

export class LabMode {
  dummies: LabDummy[] = [];
  exitPending = false;
  private menuClosedAt = -Infinity;
  private readonly onKey = () => this.openWeaponMenu();
  private readonly onEsc = () => this.onEscape();

  constructor(
    private readonly g: Game,
    private readonly init: Pick<GameInitData, 'labWeapon' | 'labMenu'>,
  ) {}

  /** 연습 런: 세이브·노드 지도·탄생 없이 고른 무기로. 층 시작 UI 이벤트는 내지 않는다(스냅샷 lab = true) */
  prepareRun(): boolean {
    const want = this.init.labWeapon ?? gameState.weapon?.id;
    const weapon = want && WEAPONS[want] ? want : PLAYER_DATA.startWeapon;
    gameState.startRun(LAB.SEED, weapon, gameState.playerName);
    gameState.birthPending = false;
    EventBus.emit(Events.STAGE_STARTED, { stageIndex: gameState.stageIndex, stageId: gameState.stageId });
    return false;
  }

  /** 작은 아레나 (노드 전투장과 같은 생성기, 가장자리 장식 없음) */
  buildArena(): FloorLayout {
    const A = ROUTE.arena;
    return generateArena({
      roomId: 'lab',
      type: 'start',
      floor: 'start',
      w: LAB.ARENA_W,
      h: LAB.ARENA_H,
      margin: A.voidMarginTiles,
      spawnInset: A.spawnInsetTiles,
      exitInset: A.exitInsetTiles,
      spawnCenter: true,
    });
  }

  /** 허수아비 2개 배치 · L(메뉴)·Esc(타이틀) 키 · 재시작 직후 열 메뉴 */
  setup(): void {
    const g = this.g;
    const room = g.layout!.rooms[0];
    const c = g.world.roomCenter(room);
    const target = new LabDummy(g, c.x, c.y, 'target');
    const o = LAB.TURRET_OFFSET_TILES;
    const turret = new LabDummy(g, c.x + o.x * TILE, c.y + o.y * TILE, 'turret');
    this.dummies = [target, turret];
    for (const d of this.dummies) g.mobs.add(d);
    g.input.keyboard?.on(`keydown-${KEYS.LAB_MENU}`, this.onKey);
    g.input.keyboard?.on('keydown-ESC', this.onEsc);
    const open = this.init.labMenu;
    if (open === 'lab') this.openWeaponMenu();
    else if (open === 'labBranch') this.openBranchMenu();
  }

  /** 시험장은 죽지 않는다: HP 가 내려가면 다시 채운다 */
  update(): void {
    if (gameState.hp < gameState.maxHp * LAB.HEAL_BELOW_RATIO) {
      gameState.hp = gameState.maxHp;
      EventBus.emit(Events.PLAYER_HEALED, { hp: gameState.hp, maxHp: gameState.maxHp, amount: 0 });
    }
  }

  private get busy(): boolean {
    return this.g.menu.isOpen || this.g.transitioning || this.exitPending;
  }

  /** L: 무기 고르기 (MENU_OPEN id 'lab'). 게임은 메뉴 동안 멈춘다 */
  openWeaponMenu(): void {
    const g = this.g;
    if (!g.lab || this.exitPending || g.transitioning) return;
    const { lines, choices } = labWeaponMenu(WEAPONS, gameState.weapon.id);
    g.setFrozen(true);
    g.player.haltForWarp();
    g.menu.open(
      'lab',
      '무기 시험장 · 무기',
      lines,
      (key) => {
        if (key === LAB_CANCEL_KEY) return this.closeMenu();
        if (key === LAB_TO_BRANCH_KEY) return this.openBranchMenu();
        const pick = choices.find((c) => c.key === key);
        if (!pick) return;
        if (pick.weaponId === gameState.weapon.id) return this.openBranchMenu();
        // 무기를 바꾸면 씬을 다시 연다 (연격·자원·휴대·이펙트 맥락을 새로) → 개성 갈래 메뉴부터
        g.menu.close();
        g.transitioning = true;
        g.scene.restart({ labWeapon: pick.weaponId, labMenu: 'labBranch' } satisfies GameInitData);
      },
      `L 열기 · Esc 타이틀`,
      { cancelKey: LAB_CANCEL_KEY },
    );
  }

  /** 개성 갈래 (MENU_OPEN id 'labBranch'): 기본·1차·2차·강화를 아무거나 즉시 적용 */
  openBranchMenu(): void {
    const g = this.g;
    if (!g.lab || this.exitPending || g.transitioning) return;
    const w = gameState.weapon;
    const { lines, actions } = labBranchMenu(w.def, w.path, w.reinforce, WEAPON_RULES.reinforceMax);
    g.setFrozen(true);
    g.player.haltForWarp();
    g.menu.open(
      'labBranch',
      `무기 시험장 · ${w.displayName}`,
      lines,
      (key) => {
        const a = actions.get(key);
        if (!a) return;
        if (a.kind === 'close') return this.closeMenu();
        if (a.kind === 'weapons') return this.openWeaponMenu();
        if (a.kind === 'reinforce')
          w.restore({ path: w.path, reinforce: nextReinforce(w.reinforce, WEAPON_RULES.reinforceMax) });
        else w.restore({ path: a.path, reinforce: w.reinforce });
        w.personality = 0;
        w.choicePending = false;
        g.trails.setContext(gameState.stageIndex + 1, w.id);
        for (const d of this.dummies) d.resetStats();
        this.openBranchMenu(); // 같은 메뉴를 갱신 (지금 표시)
      },
      `골라서 바로 적용 · 0 닫기`,
      { cancelKey: LAB_CANCEL_KEY },
    );
  }

  private closeMenu(): void {
    const g = this.g;
    this.menuClosedAt = g.time.now;
    g.menu.close();
    g.setFrozen(false);
    g.inputSystem.read(); // 메뉴를 닫은 클릭·키가 공격으로 새지 않게
  }

  /** Esc: 메뉴가 열려 있으면 닫기(UI 렌더러가 있으면 UI 가 cancelKey 로 닫는다), 아니면 타이틀로 */
  private onEscape(): void {
    if (this.g.menu.isOpen) {
      if (!__system.rendererRegistered()) this.closeMenu();
      return;
    }
    // UI 가 같은 Esc 로 메뉴를 먼저 닫았으면(cancelKey) 타이틀로 가지 않는다
    if (this.g.time.now - this.menuClosedAt < LAB.ESC_AFTER_CLOSE_MS) return;
    this.requestExit();
  }

  /**
   * 타이틀 복귀. UI 가 같은 Esc 로 일시정지 화면을 띄울 수 있어(시험장에서는 pause() 가 아무것도 하지 않는다)
   * LAB.EXIT_DEFER_STEPS 스텝 뒤에 uiCommands.toTitle() — 그 사이 뜬 UI 씬까지 함께 정리된다
   */
  private requestExit(): void {
    if (this.exitPending || this.busy) return;
    this.exitPending = true;
    const g = this.g;
    const events = g.game.events;
    let left = LAB.EXIT_DEFER_STEPS;
    const step = () => {
      left -= 1;
      if (left > 0) events.once(Phaser.Core.Events.POST_STEP, step);
      // UI 가 같은 Esc 로 이미 toTitle() 을 불렀으면(시험장 씬이 멈춤) 다시 부르지 않는다
      else if (g.sys.isActive() || g.sys.isPaused()) uiCommands.toTitle();
    };
    events.once(Phaser.Core.Events.POST_STEP, step);
  }

  destroy(): void {
    this.g.input.keyboard?.off(`keydown-${KEYS.LAB_MENU}`, this.onKey);
    this.g.input.keyboard?.off('keydown-ESC', this.onEsc);
    this.dummies = [];
  }
}
