/**
 * Game 씬 연출 풀·렌더러 만들기 (53라운드 정리 6-1 — Game.ts 에서 분리, 동작 그대로).
 * 층 램프 + 시트 JSON §3.2 필드(shake·flash·secondStage·trail)를 감각 계층으로 연결한다.
 */
import { DEPTH, FEEL } from '../../core/Constants';
import { gameState } from '../../core/GameState';
import { PALETTE } from '../../data';
import { AimLine } from '../../systems/aimFx';
import { DamageNumberPool } from '../../systems/damageNumbers';
import { FxPool } from '../../systems/fx';
import { HitFx } from '../../systems/hitFx';
import { resolveFxColor } from '../../systems/palette';
import { ScreenFx } from '../../systems/screenFx';
import { TelegraphFx } from '../../systems/telegraph';
import { TrailRenderer } from '../../systems/trail';
import type { Game } from '../Game';

export function createFx(g: Game, floor: number): void {
  g.fx = new FxPool(g);
  g.numbers = new DamageNumberPool(g);
  g.numbers.setFloor(floor);
  g.hitFx = new HitFx(g, g.fx);
  g.hitFx.setFloor(floor);
  g.telegraph = new TelegraphFx(g);
  g.telegraph.setFloor(floor);
  g.trails = new TrailRenderer(g);
  g.trails.setContext(floor, gameState.weapon.id);
  g.screenFx = new ScreenFx(g);
  g.screenFx.setFloor(floor);
  g.aimLine = new AimLine(g);
  // 색은 '#hex' 와 팔레트 경로 둘 다 (resolveFxColor)
  const SF = FEEL.SCREEN.DEFAULT_FLASH;
  g.fx.hooks = {
    shake: (spec) => g.shake.add(g.time.now, spec.px, spec.ms),
    flash: (spec) =>
      g.screenFx.flash(resolveFxColor(PALETTE, spec.color) ?? SF.COLOR, spec.ms ?? SF.MS, spec.alpha ?? SF.ALPHA),
    trail: (req) => {
      const T = FEEL.TRAIL;
      const h = g.trails.start('sheet', req.source, {
        depth: req.depth - DEPTH.OVERLAY_STEP / 2, // 시트 바로 아래(캐릭터 위)
        color: resolveFxColor(PALETTE, req.spec.color) ?? undefined,
        alpha: req.spec.alpha,
        lifeMs: req.spec.ms,
        width: Math.max(1, Math.round(T.BAND_PX * (req.spec.widthRatio ?? T.WIDTH_RATIO))),
      });
      return h ? () => h.stop() : null;
    },
    bodyCenterUpPx: FEEL.SECONDARY.BODY_CENTER_UP_PX,
  };
  g.pack.reset();
  g.hitStop.reset();
  g.shake.reset();
}
