/**
 * `?debug=1` 검증 훅 연결 (게임 로직 아님). Game 의 상태를 debug/index.ts 의 형식으로 읽기 전용으로 넘긴다.
 */
import Phaser from 'phaser';
import { FEEL, TILE } from '../../core/Constants';
import { gameState } from '../../core/GameState';
import type { Boss } from '../../objects/Boss';
import type { Enemy } from '../../objects/Enemy';
import type { Mob } from '../../objects/Mob';
import type { Pickup } from '../../objects/Pickup';
import type { Projectile } from '../../objects/Projectile';
import { exposeDebug } from '../../debug';
import { isBossPatternName } from '../../data/bossPatterns';
import { audio } from '../../systems/audio';
import { CHARGE_SFX } from '../../systems/audioMap';
import { feelSettings, setFeel } from '../../systems/feel';
import { fontStatus } from '../../systems/fonts';
import { metaStore } from '../../systems/meta';
import { sanitizeScar } from '../../systems/setup/scar';
import { spriteLibrary } from '../../systems/sprites';
import type { Game } from '../Game';
import type { GameInitData } from './shared';
import { RES, logicalZoomOf } from '../../systems/display';

/** 53라운드 Q4 검증용 견본 상흔 (정규화 3획: 긴 사선 · 갈래 · 짧은 가로) */
const DEBUG_SCAR = {
  v: 1,
  aspect: 460 / 420,
  strokes: [
    [0.22, 0.12, 0.38, 0.34, 0.5, 0.52, 0.63, 0.74, 0.78, 0.9],
    [0.5, 0.52, 0.36, 0.66, 0.28, 0.84],
    [0.56, 0.3, 0.7, 0.26, 0.84, 0.32],
  ],
};

export function exposeGameDebug(g: Game): void {
  const activeShots = (group: Phaser.GameObjects.Group) =>
    (group.getChildren() as Projectile[]).filter((p) => p.active);
  exposeDebug({
    world: g.world,
    director: g.director,
    player: g.player,
    mobs: () => [...(g.mobs.getChildren() as Mob[])],
    hurt: (m, amount, crit) => {
      if (g.combat.hitMob(m, amount, { crit: Boolean(crit), dirX: 1, dirY: 0 })) g.progress.onKill(m, 'attack');
    },
    fireAtPlayer: (distPx, speedPx, attack) => {
      g.combat.fire(g.player.x + distPx, g.player.y, -1, 0, { speedPx, attack, size: 4, lifeMs: 5000 });
    },
    playerInfo: () => ({
      x: g.player.x,
      y: g.player.y,
      action: g.player.action,
      anim: g.player.animKey,
      dir: g.player.facingDir,
      animated: g.player.visual.animated,
      overlayFrame: g.player.overlay.frame,
      moving: g.player.moving,
    }),
    sprites: () => spriteLibrary.summary(g),
    fx: () => g.fx.summary(),
    nextStage: () => {
      if (g.transitioning) return;
      g.transitioning = true;
      g.scene.restart({ mode: 'next' } satisfies GameInitData);
    },
    now: () => g.time.now,
    stage: () => ({
      index: gameState.stageIndex,
      id: gameState.stageId,
      name: gameState.stage.name,
      savesLeft: gameState.savesLeft,
      exitOpen: gameState.exitOpen,
      isLast: gameState.isLastStage,
    }),
    save: () => g.saveSlot.read(),
    lastAttack: () => g.strikes.debugLastAttack,
    lastResult: () => g.progress.debugLastResult,
    shots: () =>
      activeShots(g.playerShots).map((p) => ({
        x: p.x,
        y: p.y,
        vx: p.body.velocity.x,
        vy: p.body.velocity.y,
        attack: p.attack,
        pierce: p.pierceLeft,
        texture: p.texture.key,
        rotation: p.rotation,
      })),
    meta: () => metaStore.read(),
    economy: () => ({
      gold: gameState.gold,
      potions: gameState.potions,
      points: gameState.pointsPending,
      bonus: { ...gameState.bonus },
      rewardPending: gameState.rewardPending,
      shopOpen: g.economy.shopOpen,
      menuOpen: g.menu.isOpen,
      passives: { ...gameState.passives.owned },
    }),
    addPassive: (id: string) => gameState.passives.add(id),
    scenes: () => g.scene.manager.getScenes(true).map((s) => s.scene.key),
    pickups: () =>
      (g.pickups.getChildren() as Pickup[])
        .filter((p) => p.active)
        .map((p) => ({ kind: p.kind, value: p.value, x: p.x, y: p.y })),
    camera: () => {
      const r = g.world.cameraRegion(g.player.x, g.player.y);
      const cam = g.cameras.main;
      return {
        scrollX: cam.scrollX,
        scrollY: cam.scrollY,
        zoom: g.scale.zoom,
        camZoom: cam.zoom,
        // 52라운드: 실제 캔버스 = 논리 × resolution, logicalZoom = 월드 → 논리 화면 배율
        resolution: RES,
        logicalZoom: logicalZoomOf(cam),
        width: cam.width,
        height: cam.height,
        region: { x: r.x, y: r.y, w: r.width, h: r.height },
      };
    },
    stunAll: (ms) => {
      for (const m of g.mobs.getChildren() as Mob[]) m.stun(g.time.now, ms);
    },
    kill: (m) => {
      if (m.takeDamage(m.hp)) g.progress.onKill(m, 'attack');
    },
    setPersonality: (value) => {
      gameState.weapon.personality = 0;
      g.progress.gainPersonality(value);
    },
    weapon: () => {
      const w = gameState.weapon;
      return {
        id: w.id,
        displayName: w.displayName,
        path: [...w.path],
        stage: w.stage,
        reinforce: w.reinforce,
        personality: w.personality,
        threshold: w.threshold,
        choicePending: w.choicePending,
        canEvolve: w.canEvolve,
        options: w.options.map((o) => ({ id: o.id, name: o.name })),
        mods: { ...w.mods },
        damageMult: w.damageMult,
        hitboxWidth: w.hitbox.width,
        secondary: w.def.secondary.name,
        frozen: g.frozen,
      };
    },
    playerExtra: () => ({
      action: g.player.action,
      guarding: g.player.isGuarding,
      shadowPrimed: g.player.isShadowPrimed(g.time.now),
      aim: g.player.aimProgress(g.time.now),
      aimReady: g.player.isAimReady,
      shoved: g.player.isShoved,
    }),
    audio: () => audio.summary(),
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
    evolveTo: (id) => {
      if (!gameState.weapon.choicePending) return false;
      const before = gameState.weapon.path.length;
      g.progress.applyEvolution(id);
      return gameState.weapon.path.length > before;
    },
    spawnEnemy: (id, x, y) => g.director.spawnExtra(id, x, y),
    warpInfo: () => ({
      ...g.ui.warpState(),
      inCombat: g.director.inCombat,
      currentRoomId: gameState.roomId,
      lockedMs: 0,
      last: null,
    }),
    sprintInfo: () => ({
      allowed: g.player.sprintAllowed,
      sprinting: g.player.sprinting,
      mult: g.player.sprintMult,
      speedPx: g.player.speedPx * g.player.sprintMult,
      vx: g.player.body.velocity.x,
      vy: g.player.body.velocity.y,
      dust: g.motion.sprintDustCount,
      anim: g.player.animKey,
      strideRate: +g.player.poses.strideRate.toFixed(2),
      slowMult: +g.player.moveSlowMult.toFixed(2),
    }),
    structures: {
      list: () => g.structures.debugList(),
      state: () => g.structures.debugState(),
      standPoint: (id) => g.structures.standPoint(id),
      pressE: () => g.structures.debugPressE(),
      hit: (id) => g.structures.debugHit(id),
      interactable: () => g.structures.interactable(),
      statuses: () => g.structures.statuses(),
    },
    gotoFloor: (n) => {
      if (g.transitioning) return;
      g.transitioning = true;
      g.scene.restart({ mode: 'floor', floor: n - 1 } satisfies GameInitData);
    },
    route: () => routeInfo(g),
    openRouteChooser: () => g.route.openChooser(),
    chooseNode: (id) => g.route.chooseNode(id),
    cancelChoose: () => g.route.cancelChoose(),
    gotoNode: (id) => g.route.gotoNode(id),
    gotoExit: () => {
      const e = g.layout?.arena?.exit;
      if (!e || !g.route.exitOpen) return false;
      g.player.body.reset((e.x + 1) * TILE, (e.y + 1) * TILE);
      return true;
    },
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
    w56: () => {
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
        plunge: g.strikes.plunge.debugLast,
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
    lab: () => ({
      lab: g.lab,
      dummies: (g.labMode?.dummies ?? []).map((d) => ({
        role: d.role,
        x: d.x,
        y: d.y,
        totalDamage: d.totalDamage,
        hits: d.hits,
        shots: d.shots,
      })),
      menu: g.menu.menu ? { id: g.menu.menu.id, lines: g.menu.menu.lines.map((l) => l.label) } : null,
      frozen: g.frozen,
      exitPending: g.labMode?.exitPending ?? false,
    }),
    openLabMenu: (which) => {
      if (!g.labMode) return false;
      if (which === 'lab') g.labMode.openWeaponMenu();
      else g.labMode.openBranchMenu();
      return g.menu.isOpen;
    },
    lighting: () => g.lighting?.summary() ?? null,
    quarter: () =>
      g.world.quarter
        ? { ...g.world.quarter.summary, placements: g.world.bigProps, canal: g.world.canal, decals: g.world.decals }
        : null,
    border: () => (g.border ? { ...g.border.summary(), lookUp: +g.cam.lookUpPx.toFixed(1) } : null),
    scar: () => ({
      view: (({ x, y, width, height }) => ({ x, y, width, height }))(g.cameras.main.worldView),
      data: gameState.scar,
      state: g.player.scar.state,
      anchor: g.player.scar.lastAnchor,
      aboveLight: g.player.scar.aboveLight,
    }),
    injectScar: (scar) => {
      const s = sanitizeScar(scar ?? DEBUG_SCAR);
      if (!s) return false;
      gameState.scar = s;
      g.player.scar.refresh();
      return true;
    },
    boss: {
      info: () => findBoss(g)?.debugInfo ?? null,
      arena: () => g.bossArena?.summary() ?? null,
      force: (patterns, now) => {
        const b = findBoss(g);
        if (!b) return false;
        const list = patterns.filter(isBossPatternName);
        b.debugForce(list.length > 0 ? list : null, now);
        return true;
      },
      phase: (n) => {
        const b = findBoss(g);
        if (!b) return false;
        b.debugPhase(n);
        return true;
      },
      hitCup: () => g.bossArena?.debugHitCup() ?? false,
      geom: () => {
        const b = findBoss(g);
        return b ? { ...b.debugGeom, cup: g.bossArena?.debugCup() ?? null } : null;
      },
      tilt: (opts) => {
        const b = findBoss(g);
        if (!g.bossArena || !b) return null;
        g.bossArena.startTilt({
          ...b.params<Parameters<NonNullable<typeof g.bossArena>['startTilt']>[0]>('spin'),
          ...opts,
        });
        return g.bossArena.screen.summary();
      },
    },
    setBossHp: (hp) => {
      for (const m of g.mobs.getChildren() as Mob[]) {
        if (m.isBoss && m.active) {
          m.takeDamage(Math.max(0, m.hp - hp));
          return true;
        }
      }
      return false;
    },
  });
}

function findBoss(g: Game): Boss | null {
  for (const m of g.mobs.getChildren() as Mob[]) if (m.active && m.isBoss) return m as Boss;
  return null;
}

/** `route()` 디버그: 계약 UiRoute + 종류·클리어·출구·경로·선택지·전투장·지역·세트·튜토리얼·잠금 */
function routeInfo(g: Game): unknown {
  const route = gameState.route;
  if (!route) return null;
  const arena = g.nodeArena;
  const sp = arena?.setPiece;
  return {
    ...route.toUi(),
    kind: g.nodeKind,
    cleared: route.currentCleared,
    exitOpen: g.route.exitOpen,
    path: [...route.path],
    options: route.nextOptions().map((n) => ({ id: n.id, kind: n.kind, name: n.name })),
    kinds: route.graph.nodes.map((n) => ({ id: n.id, kind: n.kind, col: n.col, row: n.row })),
    arena: g.layout?.arena ?? null,
    region: arena ? { id: arena.regionId, tileset: arena.tileset, skin: g.world.skin.textureKey } : null,
    setPiece: sp
      ? {
          template: sp.template,
          fixed: sp.fixed,
          cover: sp.cover.length,
          center: sp.center,
          signs: sp.signs,
          dummies: sp.dummies,
          decor: sp.decor.map((d) => ({ name: d.name, role: d.role, sprites: d.sprites })),
          view: g.setPieceView?.summary ?? null,
        }
      : null,
    tutorial: g.tutorial
      ? { step: g.tutorial.machine.stepIndex, done: g.tutorial.done, skip: () => g.tutorial?.skip() }
      : null,
    room: g.layout?.rooms[0]
      ? { id: g.layout.rooms[0].id, type: g.layout.rooms[0].type, floor: g.layout.rooms[0].floor }
      : null,
    locked: g.route.locked(g.time.now),
  };
}
