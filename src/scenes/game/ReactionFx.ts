/**
 * P19 반응 fx (계약 art-assets §34 — `fx/v3/react_*`): 반응 이벤트 → 아트 시트. 시트가 없으면 그리지 않는다(이벤트·피해는 그대로).
 * WALL_SLAM → 벽 금(1.6초 유지) + 먼지 · BOWLED → bowl · LAUNCHED/LANDED → launch/land 먼지 · FELL → 물보라(양조·연회장 술)·낭떠러지 ·
 * EXPLODED → explode_s/m/l(술병·술통·증류기) · STAGGERED → flinch_flash (버팀이 깨짐이면 + tele_chance_glint 기회 반짝)
 */
import { DEPTH } from '../../core/Constants';
import type {
  EnemyBowledPayload,
  EnemyFellPayload,
  EnemyLandedPayload,
  EnemyLaunchedPayload,
  EnemyStaggeredPayload,
  EnemyWallSlamPayload,
  HazardExplodedPayload,
} from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { REACTION_FX } from '../../systems/fx/fxIds';
import { regionIdOf } from '../../systems/route';
import type { Game } from '../Game';

/** 술이 흐르는 낙하 구역 지역 (물보라 대신 술 물보라) */
const LIQUOR_REGIONS: readonly string[] = ['brewery', 'hall'];

export class ReactionFx {
  /** 디버그: 마지막으로 띄운 fx */
  last: string | null = null;

  constructor(
    private readonly g: Game,
    /** 지금 노드의 지역 id (없으면 null) */
    private readonly region: () => string | null = () => {
      const r = gameState.route;
      const n = r?.current;
      return r && n ? (regionIdOf(r.graph.stageId, n.col) ?? null) : null;
    },
  ) {}

  private play(id: string, x: number, y: number, o: { ground?: boolean; holdMs?: number } = {}): void {
    const fx = this.g.fx;
    if (!fx.has(id)) return;
    const hold = o.holdMs ? Math.max(0, o.holdMs - fx.durationOf(id)) : 0;
    fx.play(id, x, y, {
      ...(o.ground ? { depth: DEPTH.FX_GROUND } : { depth: DEPTH.HIT_FX }),
      ...(hold > 0 ? { holdLastMs: hold } : {}),
    });
    this.last = id;
  }

  onWallSlam(p: EnemyWallSlamPayload): void {
    this.play(REACTION_FX.WALL_CRACK, p.x, p.y, { holdMs: REACTION_FX.WALL_CRACK_MS });
    this.play(REACTION_FX.WALL_DUST, p.x, p.y);
  }

  onBowled(p: EnemyBowledPayload): void {
    this.play(REACTION_FX.BOWL, p.x, p.y);
  }

  onLaunched(p: EnemyLaunchedPayload): void {
    this.play(REACTION_FX.LAUNCH, p.x, p.y, { ground: true });
  }

  onLanded(p: EnemyLandedPayload): void {
    this.play(REACTION_FX.LAND, p.x, p.y, { ground: true });
  }

  onFell(p: EnemyFellPayload): void {
    if (p.zone === 'drop') this.play(REACTION_FX.FALL_CHASM, p.x, p.y, { ground: true });
    else {
      const liquor = LIQUOR_REGIONS.includes(this.region() ?? '') && this.g.fx.has(REACTION_FX.FALL_SPLASH_LIQUOR);
      this.play(liquor ? REACTION_FX.FALL_SPLASH_LIQUOR : REACTION_FX.FALL_SPLASH, p.x, p.y, { ground: true });
    }
  }

  onExploded(p: HazardExplodedPayload): void {
    this.play(REACTION_FX.EXPLODE[p.kind], p.x, p.y);
  }

  onStaggered(p: EnemyStaggeredPayload): void {
    this.play(REACTION_FX.FLINCH, p.x, p.y);
    if (p.kind === 'stagger') this.play(REACTION_FX.CHANCE_GLINT, p.x, p.y, { ground: true });
  }
}
