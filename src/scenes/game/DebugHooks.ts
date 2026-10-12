/**
 * `?debug=1` 검증 훅 연결 (게임 로직 아님). Game 의 상태를 debug/index.ts 의 형식으로 읽기 전용으로 넘긴다.
 */
import { gameState } from '../../core/GameState';
import type { Mob } from '../../objects/Mob';
import type { Pickup } from '../../objects/Pickup';
import { exposeDebug } from '../../debug';
import { audio } from '../../systems/audio/audio';
import { metaStore } from '../../systems/meta';
import { spriteLibrary } from '../../systems/sprites/sprites';
import { loadedWeaponSheets } from '../../systems/sprites/sheetLoader';
import type { Game } from '../Game';
import type { GameInitData } from './shared';
import { RES, logicalZoomOf } from '../../systems/display';
import { activeShots, combatDebug } from './debug/combatDebug';
import { routeInfo, textureBytes, worldDebug } from './debug/worldDebug';
import { runEndDebug } from './debug/runEndDebug';

export function exposeGameDebug(g: Game): void {
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
    sprites: () => ({
      ...spriteLibrary.summary(g),
      weaponLoaded: loadedWeaponSheets(),
      textureCount: g.textures.getTextureKeys().length,
      textureBytes: textureBytes(g),
    }),
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
        .map((p) => ({
          kind: p.kind,
          value: p.value,
          x: p.x,
          y: p.y,
          size: p.size,
          art: p.view.source,
          pull: p.pullSpeed,
        })),
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
    // 61 G: 각성 게이지를 value 까지 올린다 (줄이지 않는다 — 누적)
    setPersonality: (value) => {
      g.progress.gainGrowth(value - gameState.weapon.gauge);
    },
    growth: () => g.growth.debug(),
    weapon: () => {
      const w = gameState.weapon;
      return {
        id: w.id,
        displayName: w.displayName,
        path: [...w.path],
        stage: w.stage,
        gauge: w.gauge,
        marksDone: w.marksDone,
        branch: w.branchId,
        growthPath: w.pathId,
        traits: [...w.traits],
        temper: w.temper,
        growthOverlay: { ...g.player.overlay.growth.shown, look: g.player.overlay.growth.look },
        options: w.options.map((o) => ({ id: o.id, name: o.name })),
        mods: { ...w.mods },
        damageMult: w.damageMult,
        reachPx: w.reachPx,
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
    // 61 G: 노드 id 로 바로 각성 (연출 포함 — 눈금 없이)
    evolveTo: (id) => g.growth.awaken(gameState.weapon.stage === 0 ? 1 : 2, id),
    spawnEnemy: (id, x, y) => Boolean(g.director.spawnExtra(id, x, y)),
    hazards: () => g.hazards.summary(),
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
    // 62 루프 2 E: 출구 문 문턱 가운데로 (다음 프레임에 문으로 걸어 들어간다)
    gotoExit: () => {
      const p = g.doors.sillPoint();
      if (!p || !g.doors.exitOpen) return false;
      g.player.body.reset(p.x, p.y);
      return true;
    },
    doors: () => g.doors.debug(),
    openExit: () => g.route.debugOpenExit(),
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
    ...combatDebug(g),
    ...worldDebug(g),
  });
  // 62 루프 2 C: 층 끝·죽음·결산 검증 (`__lopadRunEnd.*` — ?debug 일 때만)
  if (typeof location !== 'undefined' && new URLSearchParams(location.search).has('debug'))
    (window as unknown as { __lopadRunEnd?: unknown }).__lopadRunEnd = runEndDebug(g);
}
