/**
 * Game 씬 연출 풀·렌더러 만들기 (53라운드 정리 6-1 — Game.ts 에서 분리, 동작 그대로).
 * 층 램프 + 시트 JSON §3.2 필드(shake·flash·secondStage·trail)를 감각 계층으로 연결한다.
 * 55라운드: JSON trail 은 칼끝 잔상 리본(ribbon_ash, Q7 — 색·수명은 리본 규칙)으로 그린다 · 재 파편 입자.
 */
import { DEPTH, FEEL } from '../../core/Constants';
import { PALETTE } from '../../data';
import { AimLine } from '../../systems/fx/aimFx';
import { DamageNumberPool } from '../../systems/fx/damageNumbers';
import { FxPool } from '../../systems/fx/fx';
import { AshParticles } from '../../systems/fx/ashParticles';
import { HitFx } from '../../systems/fx/hitFx';
import { resolveFxColor } from '../../systems/palette';
import { ScreenFx } from '../../systems/fx/screenFx';
import { TelegraphFx } from '../../systems/telegraph';
import { RibbonRenderer } from '../../systems/fx/ribbon';
import type { Game } from '../Game';

export function createFx(g: Game, floor: number): void {
  g.fx = new FxPool(g);
  g.numbers = new DamageNumberPool(g);
  g.numbers.setFloor(floor);
  g.ash = new AshParticles(g);
  g.hitFx = new HitFx(g, g.fx, g.ash);
  g.hitFx.setFloor(floor);
  g.telegraph = new TelegraphFx(g);
  g.telegraph.setFloor(floor);
  g.ribbons = new RibbonRenderer(g, () => g.playNow());
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
      const h = g.ribbons.start(() => req.source(), { depth: req.depth - DEPTH.OVERLAY_STEP / 2 }); // 시트 바로 아래(캐릭터 위)
      return h ? () => h.stop() : null;
    },
    bodyCenterUpPx: FEEL.SECONDARY.BODY_CENTER_UP_PX,
  };
  g.pack.reset();
  g.hitStop.reset();
  g.shake.reset();
}
