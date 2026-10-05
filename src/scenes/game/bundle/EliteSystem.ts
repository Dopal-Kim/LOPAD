/**
 * 60라운드 (g) 엘리트 접두어 1층 6종 (data/bundle2.json elite — 57 Q38 확정안): 엘리트 = 일반 적 + 접두어 1, HP ×2.5·그림 ×1.15.
 * 그림 (계약 art §22·§22.1)은 `EliteArt` (6-1 정리로 분리 — 외곽선·문장·통 갑옷·술 김·연결선·들이켜기). 이름표는 UI(UiSnapshot.elites — 계약 §14.9).
 * 접두어 규칙: 고주망태(휘는 걸음·피격 경직 절반·죽으면 술 웅덩이) · 불붙은(접촉 불 피해·지나간 자리 불씨) ·
 * 통 갑옷(받는 피해 −30%·경직 면역, 첫 강공에 깨짐) · 성난(HP 50% 이하 이동·공격 +40%) ·
 * 패거리 두목(주변 일반 적 이동 +20%·공격 간격 −20%, 죽으면 주변 1초 경직) · 들이켜는(주변 적이 죽으면 HP +15%·크기 +5%, 3회).
 */
import Phaser from 'phaser';
import { EventBus, Events, type ElitePrefixPayload, type EliteSpawnedPayload } from '../../../core/EventBus';
import { BUNDLE2, prefixDef } from '../../../data/bundle2';
import type { ElitePrefixDef, ElitePrefixId } from '../../../data/bundle2Types';
import type { UiElite } from '../../../contract/ui';
import type { Mob } from '../../../objects/Mob';
import { worldToLogicalScreen } from '../../../systems/display';
import { ENEMIES } from '../../../data';
import type { Game } from '../../Game';
import { T } from '../shared';
import { EliteArt, type EliteRec } from './EliteArt';

export type ElitePrefixPhase = 'break' | 'trigger' | 'drink' | 'death';
export type { ElitePrefixPayload, EliteSpawnedPayload } from '../../../core/EventBus';

export class EliteSystem {
  private readonly list: EliteRec[] = [];
  /** 두목이 강화한 일반 적 (매 프레임 다시 고른다) */
  private boosted = new Set<Mob>();
  private readonly art: EliteArt;

  constructor(private readonly g: Game) {
    this.art = new EliteArt(g);
  }

  /** 이 적에 붙을 수 있는 접두어 (원하는 것이 안 맞으면 붙을 수 있는 것 중 무작위) */
  pickFor(mob: Mob, want: ElitePrefixId | null): ElitePrefixDef | null {
    const ok = BUNDLE2.elite.prefixes.filter((p) => p.enemies.includes(mob.spriteId));
    if (ok.length === 0) return null;
    const w = want ? ok.find((p) => p.id === want) : undefined;
    return w ?? ok[Math.floor(this.g.rng.next() * ok.length)];
  }

  /** 일반 적을 엘리트로 (이미 엘리트·보스면 false) */
  makeElite(mob: Mob, want: ElitePrefixId | null): boolean {
    if (mob.elite || mob.isBoss || !mob.active) return false;
    const def = this.pickFor(mob, want);
    if (!def) return false;
    const E = BUNDLE2.elite;
    const enemyName = ENEMIES[mob.spriteId]?.name ?? mob.spriteId;
    mob.elite = { prefix: def.id, name: `${def.name} ${enemyName}` };
    mob.scaleMaxHp(E.hpMult);
    mob.visual.setDrawScale(mob.visual.drawScale * E.sizeMult);
    if (def.id === 'drunkard') mob.hitStunMult = def.params.hitStunMult ?? 0.5;
    if (def.id === 'barrelArmor') {
      mob.damageTakenMult = 1 + (def.params.damageTaken ?? -0.3);
      mob.stunImmune = true;
    }
    const rec: EliteRec = {
      mob,
      def,
      ...this.art.parts(mob, def),
      emblemCol: 0,
      armorBroken: false,
      enraged: false,
      drinks: 0,
      baseScale: mob.visual.drawScale,
      nextContactAt: 0,
      nextTrailAt: 0,
      phase: this.g.rng.next() * Math.PI * 2,
      barrelHitUntil: 0,
    };
    this.list.push(rec);
    mob.once(Phaser.GameObjects.Events.DESTROY, () => this.drop(rec));
    EventBus.emit(Events.ELITE_SPAWNED, { id: mob.spriteId, prefix: def.id } satisfies EliteSpawnedPayload);
    return true;
  }

  private drop(rec: EliteRec): void {
    this.art.dropParts(rec);
    if (rec.def.id === 'ringleader') this.art.clearLinks();
    const i = this.list.indexOf(rec);
    if (i >= 0) this.list.splice(i, 1);
  }

  private prefixEvent(def: ElitePrefixDef, phase: ElitePrefixPhase, count?: number): void {
    EventBus.emit(Events.ELITE_PREFIX, {
      prefix: def.id,
      phase,
      ...(count !== undefined ? { count } : {}),
    } satisfies ElitePrefixPayload);
  }

  /** 강공 적중 (GameCombat.hitMob — 통 갑옷 깨짐) */
  onHeavyHit(mob: Mob): void {
    const rec = this.list.find((r) => r.mob === mob);
    if (!rec || rec.def.id !== 'barrelArmor' || rec.armorBroken) return;
    rec.armorBroken = true;
    rec.emblemCol = 1;
    mob.damageTakenMult = 1;
    mob.stunImmune = false;
    this.art.dropBarrel(rec);
    this.art.barrelBreak(mob);
    this.prefixEvent(rec.def, 'break');
  }

  /** 통 갑옷이 막아낸 맞음 (1·2열 잠깐) */
  onArmorBlock(mob: Mob): void {
    const rec = this.list.find((r) => r.mob === mob);
    if (rec && rec.def.id === 'barrelArmor' && !rec.armorBroken) rec.barrelHitUntil = this.g.time.now + 160;
  }

  /** 처치 (Progression.onKill 뒤): 고주망태 웅덩이 · 두목 쓰러짐 · 들이켜는 주변 처치 */
  onKill(mob: Mob): void {
    const now = this.g.time.now;
    const rec = this.list.find((r) => r.mob === mob);
    if (rec?.def.id === 'drunkard' && this.g.build) {
      const P = rec.def.params;
      this.g.build.fx.liquorPool(mob.x, mob.y, T(P.deathPoolTiles ?? 1), P.deathPoolMs ?? 6000);
    }
    if (rec?.def.id === 'ringleader') {
      const P = rec.def.params;
      for (const m of this.mobsNear(mob.x, mob.y, T(P.radiusTiles ?? 4))) {
        if (m === mob) continue;
        m.stun(now, P.deathStunMs ?? 1000, 'hit');
        this.g.build?.art.stagger(m, P.deathStunMs ?? 1000);
      }
      this.art.clearLinks();
      this.prefixEvent(rec.def, 'death');
    }
    for (const r of this.list) {
      if (r.mob === mob || r.def.id !== 'guzzler' || !r.mob.active) continue;
      const P = r.def.params;
      if (r.drinks >= (P.maxDrinks ?? 3) || Math.hypot(r.mob.x - mob.x, r.mob.y - mob.y) > T(P.radiusTiles ?? 5))
        continue;
      r.drinks += 1;
      this.guzzle(r, mob.x, mob.y, P);
    }
  }

  /** 들이켜는: 줄기·마시기 연출(EliteArt.guzzle)의 healFrame 에 HP·크기 증가 · 문장 1열 · 음향 ELITE_PREFIX drink */
  private guzzle(r: EliteRec, fromX: number, fromY: number, P: Record<string, number>): void {
    this.art.guzzle(r, fromX, fromY, () => {
      if (!r.mob.active) return;
      r.mob.healRatio(P.healRatio ?? 0.15);
      r.mob.visual.setDrawScale(r.baseScale * (1 + (P.growPerDrink ?? 0.05) * r.drinks));
      r.emblemCol = 1;
      this.g.time.delayedCall(400, () => (r.emblemCol = 0));
      this.prefixEvent(r.def, 'drink', r.drinks);
    });
  }

  private mobsNear(x: number, y: number, r: number): Mob[] {
    return (this.g.mobs.getChildren() as Mob[]).filter((m) => m.active && Math.hypot(m.x - x, m.y - y) <= r);
  }

  /** 매 프레임 (적 갱신 뒤): 규칙 · 외곽선·문장 그림 */
  lateUpdate(now: number): void {
    const boosted = new Set<Mob>();
    for (const r of [...this.list]) {
      const m = r.mob;
      if (!m.active) continue;
      this.rule(r, now, boosted);
      this.art.draw(r, now);
    }
    // 두목 강화가 끝난 적은 원래대로 (연결선·고리도 끔)
    for (const m of this.boosted) {
      if (boosted.has(m)) continue;
      this.art.unlink(m);
      if (!m.active || m.elite) continue;
      m.eliteSpeedMult = 1;
      m.attackRateMult = 1;
    }
    this.boosted = boosted;
  }

  private rule(r: EliteRec, now: number, boosted: Set<Mob>): void {
    const m = r.mob;
    const P = r.def.params;
    const pl = this.g.player;
    switch (r.def.id) {
      case 'drunkard': {
        // 휘는 걸음: 진행 방향에 수직으로 흔들림을 더한다 (보스 취권 곡선 예고와 같은 언어)
        const v = m.body.velocity;
        const sp = Math.hypot(v.x, v.y);
        if (sp > 1) {
          const k = Math.sin(now * 0.001 * Math.PI * 2 * (P.wobbleHz ?? 1.2) + r.phase) * T(P.wobbleTiles ?? 0.6) * 2;
          const px = -v.y / sp;
          const py = v.x / sp;
          v.x += px * k;
          v.y += py * k;
        }
        r.emblemCol = Math.floor(now / 400) % 2;
        break;
      }
      case 'burning': {
        r.emblemCol = Math.floor(now / 250) % 2;
        const reach = (m.body.halfWidth + pl.body.halfWidth) * 1.1;
        if (now >= r.nextContactAt && Math.hypot(pl.x - m.x, pl.y - m.y) <= reach) {
          r.nextContactAt = now + (P.contactTickMs ?? 500);
          pl.takeHit(P.contactDamage ?? 5, now);
        }
        if (now >= r.nextTrailAt && Math.hypot(m.body.velocity.x, m.body.velocity.y) > 1) {
          r.nextTrailAt = now + (P.trailEveryMs ?? 400);
          this.ember(m.x, m.y, P);
        }
        break;
      }
      case 'enraged':
        if (!r.enraged && m.hp / m.maxHp <= (P.hpRatio ?? 0.5)) {
          r.enraged = true;
          r.emblemCol = 1;
          m.eliteSpeedMult = P.speedMult ?? 1.4;
          m.attackRateMult = P.attackRateMult ?? 1.4;
          this.prefixEvent(r.def, 'trigger');
        }
        break;
      case 'ringleader':
        r.emblemCol = Math.floor(now / 600) % 2;
        for (const o of this.mobsNear(m.x, m.y, T(P.radiusTiles ?? 4))) {
          if (o === m || o.elite || o.isBoss) continue;
          o.eliteSpeedMult = P.allySpeedMult ?? 1.2;
          o.attackRateMult = P.allyAttackRateMult ?? 1.25;
          boosted.add(o);
          this.art.drawLink(m, o);
        }
        break;
      default:
        break;
    }
  }

  /** 불붙은: 지나간 자리 불씨 (주인공만 다침 — 적 피해 없음) */
  private ember(x: number, y: number, P: Record<string, number>): void {
    const r = T(P.trailTiles ?? 0.5);
    const ms = P.trailMs ?? 1000;
    const pool = this.g.pools.add(new Phaser.Geom.Rectangle(x - r, y - r, r * 2, r * 2), {
      owner: 'structure',
      lifeMs: ms,
      playerSlow: 0,
      enemySlow: 0,
      slip: 0,
      fireMs: ms,
      fireTickMs: P.trailTickMs ?? 500,
      firePlayerAttack: Math.max(1, Math.round((P.contactDamage ?? 5) * (P.trailTickMult ?? 0.1) * 10)),
      fireMobDamage: null,
      fireFx: 'fire_pool',
      spreadMsPerCell: null,
      linkGapPx: 0,
      color: 0xe07a2a,
      alpha: 0.2,
    });
    this.g.pools.ignite(pool);
  }

  /** 계약 §14.9 이름표 (화면 안의 살아 있는 엘리트) */
  toUi(): UiElite[] {
    const cam = this.g.cameras.main;
    const out: UiElite[] = [];
    for (const r of this.list) {
      const m = r.mob;
      if (!m.active || !m.elite) continue;
      const top = r.emblem?.visible ? r.emblem.getTopCenter().y : m.getTopCenter().y;
      const s = worldToLogicalScreen(cam, m.x, top ?? m.y);
      if (!cam.worldView.contains(m.x, m.y)) continue;
      out.push({
        id: `${m.spriteId}#${this.list.indexOf(r)}`,
        name: m.elite.name,
        prefixes: [r.def.name],
        hp: Math.max(0, Math.round(m.hp)),
        maxHp: m.maxHp,
        screen: { x: Math.round(s.x), y: Math.round(s.y) },
      });
    }
    return out;
  }

  debug(): Record<string, unknown>[] {
    return this.list.map((r) => ({
      id: r.mob.spriteId,
      prefix: r.def.id,
      hp: r.mob.hp,
      maxHp: r.mob.maxHp,
      broken: r.armorBroken,
      enraged: r.enraged,
      drinks: r.drinks,
      outline: r.outline?.visible ?? false,
      emblem: r.emblem?.visible ?? false,
    }));
  }

  destroy(): void {
    for (const r of [...this.list]) this.drop(r);
    this.art.clearLinks();
    this.boosted.clear();
  }
}

export { prefixDef };
