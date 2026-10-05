/**
 * 60라운드 엘리트 그림 (계약 art §22·§22.1 — EliteSystem 에서 분리, 6-1 정리 · 동작 그대로):
 * 호박 외곽선 `enemies/v3/<적>_<동작>_elite`(적 바로 아래 같은 프레임·피벗·flip·배율, 알파 맥동) · 머리 위 문장 `elite_emblem`
 * (행 = 접두어, 0열 평소 · 1열 발동, 높이 = JSON headTopByEnemy) · 통 갑옷 앞·뒤 판과 깨짐 · 술 김 · 두목 연결선·발밑 고리 ·
 * 들이켜는 줄기·마시기.
 */
import Phaser from 'phaser';
import { BUILD_ART, BUNDLE_FX, DEPTH } from '../../../core/Constants';
import { BUNDLE2 } from '../../../data/bundle2';
import type { ElitePrefixDef } from '../../../data/bundle2Types';
import type { Mob } from '../../../objects/Mob';
import { eliteAction } from '../../../systems/bundle2/bundleSheets';
import type { FxHandle } from '../../../systems/fx/fx';
import { spriteLibrary } from '../../../systems/sprites/sprites';
import { FX_ACTION, artScale, frameStarts, fxDrawScale, parseAnimKey } from '../../../systems/sprites/spriteDefs';
import type { Game } from '../../Game';

export interface EliteRec {
  mob: Mob;
  def: ElitePrefixDef;
  outline: Phaser.GameObjects.Sprite | null;
  emblem: Phaser.GameObjects.Sprite | null;
  /** 문장 열 (0 평소 · 1 발동) */
  emblemCol: number;
  armorBroken: boolean;
  enraged: boolean;
  drinks: number;
  baseScale: number;
  nextContactAt: number;
  nextTrailAt: number;
  phase: number;
  /** §22.1: 통 갑옷 뒤·앞 판 · 술 김 루프 */
  barrelBack: Phaser.GameObjects.Sprite | null;
  barrelFront: Phaser.GameObjects.Sprite | null;
  barrelHitUntil: number;
  vapor: FxHandle | null;
}

/** §22.1 두목 연결선·발밑 고리 (강화 대상마다) */
interface LinkRec {
  line: Phaser.GameObjects.Sprite | null;
  aura: FxHandle | null;
}

type BodyBox = { cx: number; cy: number; scale: number };

/** 시트 JSON 의 엘리트 메모 (headTopByEnemy · bodyBoxByEnemy · kinds · healFrame) */
type EliteSheetMeta = {
  headTopByEnemy?: Record<string, number>;
  bodyBoxByEnemy?: Record<string, BodyBox>;
  kinds?: string[];
  healFrame?: number;
};

export class EliteArt {
  /** 두목이 강화한 일반 적의 연결선·고리 */
  private readonly links = new Map<Mob, LinkRec>();

  constructor(private readonly g: Game) {}

  private meta(id: string): EliteSheetMeta | undefined {
    return spriteLibrary.sheet(id, FX_ACTION) as unknown as EliteSheetMeta | undefined;
  }

  /** 엘리트 그림 묶음 (외곽선 · 문장 · 통 갑옷 판 · 술 김) */
  parts(mob: Mob, def: ElitePrefixDef): Pick<EliteRec, 'outline' | 'emblem' | 'barrelBack' | 'barrelFront' | 'vapor'> {
    const barrel = def.id === 'barrelArmor';
    return {
      outline: this.g.add.sprite(mob.x, mob.y, '__DEFAULT').setVisible(false),
      emblem: this.fxSprite(BUILD_ART.ELITE_EMBLEM),
      barrelBack: barrel ? this.fxSprite(BUILD_ART.ELITE_BARREL) : null,
      barrelFront: barrel ? this.fxSprite(BUILD_ART.ELITE_BARREL) : null,
      vapor: def.id === 'drunkard' ? this.playVapor(mob) : null,
    };
  }

  /** 그림 묶음 정리 */
  dropParts(rec: EliteRec): void {
    rec.outline?.destroy();
    rec.emblem?.destroy();
    this.dropBarrel(rec);
    this.g.fx.stop(rec.vapor, 0, false);
  }

  /** 통 갑옷 판만 정리 (깨짐) */
  dropBarrel(rec: EliteRec): void {
    rec.barrelBack?.destroy();
    rec.barrelFront?.destroy();
    rec.barrelBack = null;
    rec.barrelFront = null;
  }

  /** fx 시트의 정지 프레임용 스프라이트 (없으면 null) */
  private fxSprite(id: string): Phaser.GameObjects.Sprite | null {
    const tex = spriteLibrary.textureKey(id, FX_ACTION);
    if (!tex || !this.g.textures.exists(tex)) return null;
    return this.g.add.sprite(0, 0, tex, 0).setVisible(false);
  }

  /** 적 머리 꼭대기 (적 피벗 위 도트 — 시트 JSON headTopByEnemy, 없으면 기본값) */
  private headTop(id: string, mob: Mob): number {
    return this.meta(id)?.headTopByEnemy?.[mob.spriteId] ?? BUNDLE_FX.ELITE_HEAD_TOP_DOTS;
  }

  private bodyBox(id: string, mob: Mob): BodyBox | null {
    return this.meta(id)?.bodyBoxByEnemy?.[mob.spriteId] ?? null;
  }

  /** 술 김 (적 머리 꼭대기 − 8 도트, 문장 아래 — 따라감) */
  private playVapor(mob: Mob): FxHandle | null {
    const id = BUILD_ART.ELITE_VAPOR;
    const def = spriteLibrary.sheet(id, FX_ACTION);
    if (!def || !this.g.fx.has(id)) return null;
    const k = artScale(def) * mob.visual.drawScale;
    return this.g.fx.play(id, mob.x, mob.y, {
      follow: mob,
      followOffset: { x: 0, y: -(this.headTop(id, mob) - 8) * k },
      depthOffset: DEPTH.OVERLAY_STEP * 3,
      scaleMult: mob.visual.drawScale,
      hooks: false,
    });
  }

  /** elite_barrel_armor_break: 적 발밑 가로 가운데(bodyBox cx) · scale = bodyBox.scale */
  barrelBreak(mob: Mob): void {
    const box = this.bodyBox(BUILD_ART.ELITE_BARREL_BREAK, mob);
    const def = spriteLibrary.sheet(BUILD_ART.ELITE_BARREL_BREAK, FX_ACTION);
    if (def && box)
      this.g.fx.play(BUILD_ART.ELITE_BARREL_BREAK, mob.x + box.cx * artScale(def) * mob.visual.drawScale, mob.y, {
        depth: mob.depth + DEPTH.OVERLAY_STEP * 4,
        scaleMult: box.scale,
        flipX: mob.flipX,
      });
  }

  /**
   * 들이켜는 연출: 죽은 적 머리 위(60 도트)에서 줄기(elite_guzzle_trail)가 엘리트 머리로 0.35초 → 마시기(elite_guzzle_drink)
   * healFrame 에 apply. 시트가 없으면 바로 apply
   */
  guzzle(r: EliteRec, fromX: number, fromY: number, apply: () => void): void {
    const g = this.g;
    const trailDef = spriteLibrary.sheet(BUILD_ART.ELITE_GUZZLE_TRAIL, FX_ACTION);
    const drinkDef = spriteLibrary.sheet(BUILD_ART.ELITE_GUZZLE_DRINK, FX_ACTION);
    const arrive = () => {
      if (!r.mob.active) return;
      if (!drinkDef || !g.fx.has(BUILD_ART.ELITE_GUZZLE_DRINK)) return apply();
      const k = artScale(drinkDef) * r.mob.visual.drawScale;
      g.fx.play(BUILD_ART.ELITE_GUZZLE_DRINK, r.mob.x, r.mob.y, {
        follow: r.mob,
        followOffset: { x: 0, y: -(this.headTop(BUILD_ART.ELITE_GUZZLE_DRINK, r.mob) - 70) * k },
        depthOffset: DEPTH.OVERLAY_STEP * 4,
        scaleMult: r.mob.visual.drawScale,
      });
      const hf = this.meta(BUILD_ART.ELITE_GUZZLE_DRINK)?.healFrame ?? 4;
      g.time.delayedCall(frameStarts(drinkDef)[hf] ?? 0, apply);
    };
    if (!trailDef || !g.fx.has(BUILD_ART.ELITE_GUZZLE_TRAIL)) return arrive();
    const k = artScale(trailDef);
    const sx = fromX;
    const sy = fromY - 60 * k;
    const head = () => ({ x: r.mob.x, y: r.mob.y - this.headTop(BUILD_ART.ELITE_GUZZLE_DRINK, r.mob) * k });
    const h = g.fx.play(BUILD_ART.ELITE_GUZZLE_TRAIL, sx, sy, { depth: DEPTH.HIT_FX, hooks: false, durationMs: 400 });
    const ms = 350;
    const arc = 30 * k;
    if (h)
      g.tweens.addCounter({
        from: 0,
        to: 1,
        duration: ms,
        onUpdate: (tw) => {
          const t = tw.getValue() ?? 0;
          const e = head();
          const x = sx + (e.x - sx) * t;
          const y = sy + (e.y - sy) * t - Math.sin(t * Math.PI) * arc;
          h.sprite.setRotation(Math.atan2(y - h.sprite.y, x - h.sprite.x)).setPosition(x, y);
        },
      });
    g.time.delayedCall(ms, () => {
      if (h) g.fx.stop(h, 0, false);
      arrive();
    });
  }

  /**
   * 두목 연결선 (elite_ringleader_link — 두목 pivot 위 60 → 대상 pivot 위 60, 회전) · 대상 발밑 고리 (elite_ringleader_aura).
   * 반복 타일 시트를 한 장으로 길이에 맞춰 늘린다 (임시 — 타일 반복은 다음 정리)
   */
  drawLink(leader: Mob, ally: Mob): void {
    const g = this.g;
    let rec = this.links.get(ally);
    if (!rec) {
      const aura = g.fx.has(BUILD_ART.ELITE_AURA)
        ? g.fx.play(BUILD_ART.ELITE_AURA, ally.x, ally.y, {
            follow: ally,
            depthOffset: -DEPTH.OVERLAY_STEP * 2,
            scaleMult: ally.spriteId === 'charger' ? 1.25 : 1,
            hooks: false,
          })
        : null;
      rec = { line: this.fxSprite(BUILD_ART.ELITE_LINK), aura };
      if (rec.line) {
        const key = spriteLibrary.animKey(BUILD_ART.ELITE_LINK, FX_ACTION, 'any');
        if (key && g.anims.exists(key)) rec.line.play(key);
      }
      this.links.set(ally, rec);
    }
    const line = rec.line;
    const def = spriteLibrary.sheet(BUILD_ART.ELITE_LINK, FX_ACTION);
    if (!line || !def) return;
    const k = artScale(def);
    const ax = leader.x;
    const ay = leader.y - 60 * k;
    const bx = ally.x;
    const by = ally.y - 60 * k;
    const len = Math.hypot(bx - ax, by - ay);
    const w = def.frameWidth * fxDrawScale(def);
    line
      .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
      .setPosition(ax, ay)
      .setRotation(Math.atan2(by - ay, bx - ax))
      .setScale(w > 0 ? (len / w) * fxDrawScale(def) : fxDrawScale(def), fxDrawScale(def))
      .setDepth(DEPTH.HIT_FX - 0.2)
      .setVisible(true);
  }

  unlink(m: Mob): void {
    const rec = this.links.get(m);
    if (!rec) return;
    rec.line?.destroy();
    this.g.fx.stop(rec.aura, 0, false);
    this.links.delete(m);
  }

  clearLinks(): void {
    for (const m of [...this.links.keys()]) this.unlink(m);
  }

  /** 외곽선(적 바로 아래 같은 프레임) · 통 갑옷 판 · 문장(머리 위) */
  draw(r: EliteRec, now: number): void {
    const m = r.mob;
    const o = r.outline;
    if (o) {
      const parsed = m.visual.current ? parseAnimKey(m.visual.current, m.visual.sheetName) : null;
      const tex = parsed ? spriteLibrary.textureKey(m.visual.sheetName, eliteAction(parsed.action)) : null;
      if (tex && this.g.textures.exists(tex)) {
        if (o.texture.key !== tex) o.setTexture(tex);
        const P = BUNDLE2.elite.outlinePulse;
        const t = (Math.sin((now / P.periodMs) * Math.PI * 2) + 1) / 2;
        o.setFrame(m.frame.name)
          .setOrigin(m.originX, m.originY)
          .setScale(m.scaleX, m.scaleY)
          .setFlipX(m.flipX)
          .setPosition(m.x, m.y)
          .setDepth(m.depth - BUNDLE_FX.ELITE_OUTLINE_DEPTH)
          .setAlpha(m.alpha * (P.alphaMin + (P.alphaMax - P.alphaMin) * t))
          .setVisible(m.visible);
      } else o.setVisible(false);
    }
    this.drawBarrel(r, now);
    this.drawEmblem(r);
  }

  /** 문장 (행 = 접두어 emblemRow, 열 = emblemCol) — 높이 = 엘리트 문장 시트 headTopByEnemy × 적 그림 배율 */
  private drawEmblem(r: EliteRec): void {
    const e = r.emblem;
    if (!e) return;
    const m = r.mob;
    const def = spriteLibrary.sheet(BUILD_ART.ELITE_EMBLEM, FX_ACTION);
    if (!def) return;
    const meta = this.meta(BUILD_ART.ELITE_EMBLEM);
    const row = Math.max(0, meta?.kinds?.indexOf(r.def.emblemRow) ?? 0);
    const k = artScale(def);
    const head = this.headTop(BUILD_ART.ELITE_EMBLEM, m) * (m.visual.drawScale || 1);
    e.setFrame(String(row * def.frames + Math.min(def.frames - 1, r.emblemCol)))
      .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
      .setScale(k)
      .setPosition(m.x, m.y - (head + BUNDLE_FX.ELITE_EMBLEM_GAP_DOTS) * k)
      .setDepth(DEPTH.HIT_FX - 0.1)
      .setVisible(m.visible);
  }

  /** 통 갑옷 판 (back = 적 아래·외곽선 위 / front = 적 위, bodyBox 자리·배율 × 엘리트 배율, flipX 같이) */
  private drawBarrel(r: EliteRec, now: number): void {
    const m = r.mob;
    const def = spriteLibrary.sheet(BUILD_ART.ELITE_BARREL, FX_ACTION);
    const box = this.bodyBox(BUILD_ART.ELITE_BARREL, m);
    if (!def || !box) return;
    const ek = BUNDLE2.elite.sizeMult;
    const k = artScale(def) * ek;
    const col = now < r.barrelHitUntil ? 1 + (Math.floor(now / 80) % 2) : 0;
    const x = m.x + box.cx * k * (m.flipX ? -1 : 1);
    const y = m.y + (box.cy + 22) * k;
    const place = (s: Phaser.GameObjects.Sprite | null, row: number, depth: number) =>
      s
        ?.setFrame(String(row * def.frames + col))
        .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
        .setScale(artScale(def) * box.scale * ek)
        .setFlipX(m.flipX)
        .setPosition(x, y)
        .setDepth(depth)
        .setVisible(m.visible);
    place(r.barrelBack, 0, m.depth - BUNDLE_FX.ELITE_OUTLINE_DEPTH * 0.5);
    place(r.barrelFront, 1, m.depth + DEPTH.OVERLAY_STEP * 0.5);
  }
}
