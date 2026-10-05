/**
 * `?debug=1` 검증 훅 — 감각·적 행동·연격·무기 기본기 (60라운드 6-1: DebugHooks 에서 분리, 동작 그대로)
 */
import Phaser from 'phaser';
import { FEEL } from '../../../core/Constants';
import { gameState } from '../../../core/GameState';
import type { Boss } from '../../../objects/Boss';
import type { Enemy } from '../../../objects/Enemy';
import type { Mob } from '../../../objects/Mob';
import type { Projectile } from '../../../objects/Projectile';
import { audio } from '../../../systems/audio/audio';
import { CHARGE_SFX } from '../../../systems/audio/audioMap';
import { feelSettings, setFeel } from '../../../systems/feel';
import { fontStatus } from '../../../systems/fonts';
import type { Game } from '../../Game';
import { logicalZoomOf } from '../../../systems/display';
import type { DebugApi } from '../../../debug';

/** 살아 있는 투사체만 */
export const activeShots = (group: Phaser.GameObjects.Group): Projectile[] =>
  (group.getChildren() as Projectile[]).filter((p) => p.active);

export function combatDebug(
  g: Game,
): Pick<
  DebugApi,
  | 'feel'
  | 'setFeel'
  | 'shoved'
  | 'telegraph'
  | 'projectiles'
  | 'behavior'
  | 'lastSlam'
  | 'trails'
  | 'screen'
  | 'aimFx'
  | 'combo'
  | 'hitShapes'
  | 'birth'
  | 'skipBirth'
  | 'weaponState'
  | 'setResource'
  | 'weaponKit'
  | 'freeze'
  | 'setGauge'
> {
  return {
    feel: () => ({
      settings: { ...feelSettings },
      constants: FEEL,
      hitstop: {
        active: g.hitStop.active(g.time.now),
        remainingMs: g.hitStop.remaining(g.time.now),
        count: g.hitStop.count,
        physicsPaused: g.physics.world.isPaused,
      },
      shake: {
        offset: { ...g.shake.offset },
        active: g.shake.activeCount,
        count: g.shake.count,
        last: g.shake.last,
      },
      numbers: g.numbers.summary(),
      numbersCount: g.numbers.count,
      font: { family: g.numbers.fontFamily, loaded: fontStatus(FEEL.DAMAGE_TEXT.FONT_FAMILY) ?? null },
      hitFx: g.hitFx.summary(),
    }),
    setFeel: (patch) => setFeel(patch),
    shoved: () => (g.mobs.getChildren() as Mob[]).filter((m) => m.isShoved).length,
    telegraph: () => ({
      markers: g.telegraph.summary(),
      sheets: {
        line: g.telegraph.has('line'),
        circle: g.telegraph.has('circle'),
        cone: g.telegraph.has('cone'),
        aura: g.telegraph.has('aura'),
      },
    }),
    projectiles: () =>
      activeShots(g.projectiles).map((p) => ({
        x: p.x,
        y: p.y,
        vx: p.body.velocity.x,
        vy: p.body.velocity.y,
        attack: p.attack,
        texture: p.texture.key,
        frame: p.frame.name,
        anim: p.anims.currentAnim?.key ?? null,
        rotation: p.rotation,
        reflected: p.reflected,
      })),
    behavior: () =>
      (g.mobs.getChildren() as Mob[])
        .filter((m) => m.active)
        .map((m) => {
          const e = m as unknown as Partial<Enemy> & Partial<Boss>;
          return {
            id: m.spriteId,
            state: e.behaviorState ?? e.patternState ?? '?',
            shots: e.shotsSinceReload ?? null,
            pattern: e.pattern ?? null,
            patternLog: e.patternLog ? [...e.patternLog] : null,
            summoned: e.summoned ?? null,
            phase: e.phase ? gameState.bossPhase : null,
            vx: m.body.velocity.x,
            vy: m.body.velocity.y,
            x: m.x,
            y: m.y,
          };
        }),
    lastSlam: () => g.combat.debugLastSlam,
    trails: () => ({ active: g.ribbons.activeCount, count: g.ribbons.count, list: g.ribbons.summary() }),
    screen: () => g.screenFx.summary(),
    aimFx: () => ({
      line: g.aimLine.visible,
      lineSheet: g.aimLine.sheet,
      lineId: g.aimLine.id,
      lineFrame: g.aimLine.frame,
      charge: g.motion.aimChargeFrame,
    }),
    combo: () => {
      const c = g.player.combo;
      return {
        weapon: gameState.weapon.id,
        hasCombo: Boolean(c),
        lastIndex: c?.lastIndex ?? null,
        lastStartedAt: c?.lastStartedAt ?? null,
        readyAt: c ? c.readyAt() : null,
        nextIndex: c ? c.nextIndex(g.time.now) : null,
        now: g.time.now,
        lastSwing: g.strikes.debugLastSwing,
        swingFx: g.strikes.debugSwingFx,
        // 51라운드: 공격 시각 기록(템포 실측) · 활 마지막 발사·적중
        log: g.strikes.attackLog.slice(),
        bow: { shot: g.strikes.bow.debugLastShot, hit: g.strikes.bow.debugLastHit },
        overlay: { frame: g.player.overlay.frame, action: g.player.overlay.action },
        anim: g.player.animKey,
        // 55라운드 §17: 순환·관성·차지 · 최근 판정(후속 판정 포함) · 판정 모양 오버레이
        melee: g.player.melee.debug(g.time.now),
        swings: g.strikes.swingLog.slice(),
        hitShapes: { enabled: g.strikes.overlay.enabled, drawn: g.strikes.overlay.drawn },
      };
    },
    hitShapes: (on) => {
      if (on !== undefined) g.strikes.overlay.enabled = on;
      return g.strikes.overlay.enabled;
    },
    birth: () => ({
      active: g.birth.active,
      pending: gameState.birthPending,
      ...(g.birth.seq?.state ?? {}),
      camZoom: logicalZoomOf(g.cameras.main),
      playerVisible: g.player.visible,
      playerAlpha: g.player.alpha,
    }),
    skipBirth: () => g.birth.forceSkip(),
    weaponState: () => g.player.debugWeapon(g.time.now),
    setResource: (value) => {
      const r = g.player.resource;
      if (!r) return false;
      if (r.kind === 'stamina') {
        // 소모 경로로 (바닥 판정·회복 지연 포함)
        r.value = r.max;
        r.spend(Math.max(0, r.max - value), g.time.now);
      } else r.value = Phaser.Math.Clamp(value, 0, r.max);
      return true;
    },
    weaponKit: () => {
      const pl = g.player;
      const now = g.time.now;
      return {
        weapon: gameState.weapon.id,
        action: pl.action,
        groggy: pl.groggy,
        resource: pl.resource?.debug(now) ?? null,
        gauge: pl.gauges.debug(now),
        bladeTint: pl.gauges.bladeTint,
        draw: pl.secondaryDriver.drawStateAt(now),
        aimJitter: pl.aimJitter(now),
        lastRelease: pl.secondaryDriver.lastRelease,
        defense: pl.defense.lastOutcome,
        brands: g.strikes.brands.summary(),
        issen: g.strikes.issen.debugLast,
        crackLine: g.strikes.crackLine.debugLast,
        // 56라운드 2단계 새 기본기
        moves: pl.moves.debug(now),
        moveStrikes: g.strikes.moves.debugLast,
        arrowRain: g.strikes.rain.debugLast,
        lift: pl.visual.liftPx,
        callouts: {
          count: g.feedback.callouts.count,
          last: g.feedback.callouts.last,
          live: g.feedback.callouts.summary(),
        },
        focusScale: g.feedback.focusScale,
        physicsTimeScale: g.physics.world.timeScale,
        bladeFlashes: pl.overlay.flashCount,
        chargeLoopRate: audio.loopRateOf(CHARGE_SFX.loop),
      };
    },
    freeze: (on) => {
      if (on) g.scene.pause();
      else g.scene.resume();
    },
    setGauge: (value) => {
      const gg = g.player.gauges.gauge;
      if (!gg) return false;
      gg.value = Phaser.Math.Clamp(value, 0, gg.max);
      return true;
    },
  };
}
