/**
 * 49라운드 계약 §11.4 무기 시험장 (씬 키 WeaponLab, 같은 전투 코드를 lab 플래그로 재사용):
 * 연습 런 준비 · 작은 아레나 · 허수아비 · L(무기·개성 갈래 메뉴) · 죽지 않음.
 * 53라운드 UI 요청 B3: Esc 를 직접 읽지 않는다 — 메뉴는 cancelKey(UI 가 Esc 로 보냄), 메뉴가 없으면 UI 일시정지(타이틀은 거기서)
 */
import { KEYS, LAB, TILE } from '../../core/Constants';
import { EventBus, Events } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { WEAPONS } from '../../data';
import { branchByNode, pathByNode } from '../../data/growth';
import { effectiveKind, nextMarkOf } from '../../systems/growth/growth';
import { LabDummy } from '../../objects/LabDummy';
import { generateArena, type FloorLayout } from '../../systems/mapgen';
import { oncePerKeyEvent } from '../../systems/keyEvents';
import { ROUTE } from '../../systems/route';
import {
  LAB_CANCEL_KEY,
  LAB_GAUGE_STEP,
  LAB_TO_BRANCH_KEY,
  LAB_TO_WEAPONS_KEY,
  labBranchMenu,
  labWeaponMenu,
} from '../../systems/weapon/weaponLab';
import type { Game } from '../Game';
import { labWeaponFor } from './runWeapon';
import { urlParams, type GameInitData } from './shared';

export class LabMode {
  dummies: LabDummy[] = [];
  exitPending = false;
  /** L — 같은 keydown 객체 재전달은 무시 (keyEvents) */
  private readonly onKey = oncePerKeyEvent<KeyboardEvent>(() => this.openWeaponMenu());

  constructor(
    private readonly g: Game,
    private readonly init: Pick<GameInitData, 'labWeapon' | 'labMenu'>,
  ) {}

  /** 연습 런: 세이브·노드 지도·탄생 없이 고른 무기로. 층 시작 UI 이벤트는 내지 않는다(스냅샷 lab = true) */
  prepareRun(): boolean {
    gameState.startRun(LAB.SEED, labWeaponFor(this.init), gameState.playerName);
    gameState.birthPending = false;
    // 61라운드 P4: 시험장은 층 노출 제한 없음 (태그 10·세트 6단계·갈래·길 전부)
    gameState.build.setFloor(null);
    // 51라운드 검증: `?branch=<1차 노드>[,<2차 노드>]` 로 갈래를 바로 (트리에 없는 id 는 거른다)
    const branch = urlParams().get('branch');
    if (branch) gameState.weapon.setPath(branch.split(','));
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
      `L 열기 · Esc 닫기`,
      { cancelKey: LAB_CANCEL_KEY },
    );
  }

  /** 61 G 무기 성장 시험 (MENU_OPEN id 'labBranch'): 갈래·길 아무 단계나 즉시 · 각성 게이지 자유 조작 · 패시브·저주 시험 */
  openBranchMenu(): void {
    const g = this.g;
    if (!g.lab || this.exitPending || g.transitioning) return;
    const w = gameState.weapon;
    const next = nextMarkOf(gameState.build.floor, w.marksDone);
    const KIND: Record<string, string> = {
      trait: '개성 발현',
      awaken1: '1차 각성',
      awaken2: '2차 각성',
      temper: '단련',
    };
    const names: Record<string, { name: string; line: string }> = {};
    for (const b of w.def.personality.branches) {
      const gb = branchByNode(w.id, b.id);
      if (gb) names[b.id] = { name: gb.name, line: gb.line };
      for (const c of b.next ?? []) {
        const gp = pathByNode(w.id, c.id);
        if (gp) names[c.id] = { name: gp.path.name, line: gp.path.line };
      }
    }
    const { lines, actions } = labBranchMenu(w.def, w.path, {
      gauge: w.gauge,
      next: { at: next.at, name: KIND[effectiveKind(next.kind, w.stage)] ?? next.kind },
      curseActive: gameState.build.curse !== null,
      names,
    });
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
        // 57라운드 빌드 시험: 패시브 3지선다 · 저주 2택 (닫히면 갈래 메뉴로 돌아온다)
        if (a.kind === 'passive') {
          g.menu.close();
          if (!g.buildMenus.openPassiveMenu('lab', {}, () => this.openBranchMenu())) this.openBranchMenu();
          return;
        }
        if (a.kind === 'curse') {
          g.menu.close();
          if (!g.buildMenus.openCurseMenu(undefined, () => this.openBranchMenu())) this.openBranchMenu();
          return;
        }
        // 61 G: 게이지를 올리면 메뉴를 닫는다 — 눈금 메뉴(개성 발현·각성)가 그대로 열린다
        if (a.kind === 'gauge' || a.kind === 'nextMark') {
          const add = a.kind === 'gauge' ? LAB_GAUGE_STEP : Math.max(0, next.at - w.gauge);
          this.closeMenu();
          g.growth.labGain(add);
          return;
        }
        if (a.kind === 'reset') g.growth.labReset();
        else g.growth.labSetPath(a.path);
        for (const d of this.dummies) d.resetStats();
        this.openBranchMenu(); // 같은 메뉴를 갱신 (지금 표시)
      },
      `골라서 바로 적용 · 0 닫기 · Esc 무기 목록`,
      // 53라운드 UI 요청 B2: Esc = 무기 목록으로 돌아감
      { cancelKey: LAB_TO_WEAPONS_KEY },
    );
  }

  private closeMenu(): void {
    const g = this.g;
    g.menu.close();
    g.setFrozen(false);
    g.inputSystem.read(); // 메뉴를 닫은 클릭·키가 공격으로 새지 않게
  }

  destroy(): void {
    this.g.input.keyboard?.off(`keydown-${KEYS.LAB_MENU}`, this.onKey);
    this.dummies = [];
  }
}
