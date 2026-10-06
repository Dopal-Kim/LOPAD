/**
 * 61 단계 5 (P13) 무기 시험장 개성 메뉴 (L → 각성 갈래 · 게이지 → t): 이 무기 개성 14장을 바로 켜고 끄기 · 공명 상태 ·
 * 시험용 술 웅덩이(하나는 불)와 움직이는 적(밀기·띄우기·묶기 시험 — 허수아비는 움직이지 않는다). 메뉴 id 는 'labBranch' 를 쓴다
 * (계약 §11.4 메뉴 id 그대로 — 제목만 다르다).
 */
import Phaser from 'phaser';
import { TILE } from '../../core/Constants';
import { gameState } from '../../core/GameState';
import { TRAITS, growthBranches } from '../../data/growth';
import { Enemy } from '../../objects/Enemy';
import { activeResonances, resonancesOf } from '../../systems/growth/resonance';
import { labTraitMenu } from '../../systems/weapon/weaponLab';
import type { Game } from '../Game';

/** 시험장에 부르는 적 (징집병 둘 · 결사병 · 짐꾼) */
const LAB_ENEMIES = ['dummy', 'dummy', 'charger', 'porter'] as const;

export class LabTraits {
  constructor(
    private readonly g: Game,
    private readonly back: () => void,
    private readonly close: () => void,
  ) {}

  open(): void {
    const g = this.g;
    const w = gameState.weapon;
    const mine = TRAITS.filter((t) => t.weapon === w.id);
    const branchNames = Object.fromEntries(growthBranches(w.id).map((b) => [b.id, b.name]));
    const on = new Set(activeResonances(w.id, w.traitDefs).map((r) => r.id));
    const resonance = resonancesOf(w.id).map((r) => ({ name: r.name, line: r.line, on: on.has(r.id) }));
    const { lines, actions } = labTraitMenu(mine, w.traits, w.branchId, { branchNames, resonance });
    g.menu.open(
      'labBranch',
      `무기 시험장 · ${w.displayName} · 개성`,
      lines,
      (key) => {
        const a = actions.get(key);
        if (!a) return;
        if (a.kind === 'close') return this.close();
        if (a.kind === 'back') return this.back();
        if (a.kind === 'toggle') this.toggle(a.id);
        else if (a.kind === 'all') {
          for (const t of mine) if (!t.branch || t.branch === w.branchId) this.set(t.id, true);
        } else if (a.kind === 'none') {
          for (const id of [...w.traits]) this.set(id, false);
        } else if (a.kind === 'env') this.placePools();
        else if (a.kind === 'enemies') this.spawnEnemies();
        this.open(); // 지금 상태로 갱신
      },
      '골라서 바로 켜고 끄기 · 0 닫기 · 9 갈래 메뉴',
      { cancelKey: '9' },
    );
  }

  private toggle(id: string): void {
    this.set(id, !gameState.weapon.traits.includes(id));
  }

  /** 켜기 = 개성 획득 경로 그대로(이벤트·알림·그림 로드), 끄기 = 목록에서 뺌 */
  private set(id: string, on: boolean): void {
    const w = gameState.weapon;
    const has = w.traits.includes(id);
    if (on && !has) this.g.growth.gainTrait(id);
    else if (!on && has) {
      w.traits = w.traits.filter((t) => t !== id);
      gameState.build.touch();
    }
  }

  /** 허수아비 둘레 술 웅덩이 셋 (첫째는 바로 불) */
  private placePools(): void {
    const g = this.g;
    const c = this.center();
    const spots = [
      { x: c.x - TILE * 2.5, y: c.y + TILE * 1.5 },
      { x: c.x + TILE * 2.5, y: c.y + TILE * 1.5 },
      { x: c.x, y: c.y - TILE * 2.5 },
    ];
    spots.forEach((p, i) => {
      if (!g.world.isWalkableAt(p.x, p.y)) return;
      const pool = g.build.fx.liquorPool(p.x, p.y, TILE * 0.9, 20000);
      if (i === 0) g.pools.ignite(pool);
    });
  }

  /** 움직이는 적 넷 (아레나 가운데 둘레) */
  private spawnEnemies(): void {
    const g = this.g;
    const c = this.center();
    LAB_ENEMIES.forEach((id, i) => {
      const a = (i / LAB_ENEMIES.length) * Math.PI * 2 + 0.4;
      const x = c.x + Math.cos(a) * TILE * 4;
      const y = c.y + Math.sin(a) * TILE * 3;
      if (!g.world.isWalkableAt(x, y)) return;
      g.mobs.add(new Enemy(g, x, y, id));
    });
  }

  private center(): Phaser.Math.Vector2 {
    const g = this.g;
    const room = g.layout?.rooms[0];
    const c = room ? g.world.roomCenter(room) : { x: g.player.x, y: g.player.y };
    return new Phaser.Math.Vector2(c.x, c.y);
  }
}
