/**
 * 56라운드 2단계 대검 새 기본기 (Q41·Q54·Q55·Q61·Q63, 계약 art §18.8) — 모두 기본기:
 * - 어깨 태클 `greatsword_tackle` — 대쉬 공격 교체: 돌진 40, 판정이 몸과 함께 이동·적을 밀고 감, fx 는 첫 접촉 순간
 * - 버티기 올려베기 `greatsword_brace_upswing` — 가드 중 좌클릭: 슈퍼아머 0.46초(피해 그대로·울분으로 쌓임), 울분 소모 시 ember ×1.5·60°
 * - 공중제비 도약 찍기 `greatsword_leap_slam` — 차지 중 스페이스: 차지 단계 유지, 착지 쐐기 + 끝 충격원 + 링 0.6R, 공중 무적 없음
 * - 막다가 떼면 돌진 `greatsword_guard_rush` — 퍼펙트 가드 직후 우클릭을 떼면 밀쳐내기 대신 돌진 56, 적을 밀고 감, 땅 홈 fx
 * 판정·fx 는 씬(PlayerStrikes·MoveStrikes)이 PLAYER_ATTACKED `move` 로.
 */
import { gameState } from '../../core/GameState';
import type { BraceMoveDef, LeapMoveDef, RushMoveDef } from '../../data/types';
import type { InputState } from '../../systems/InputSystem';
import type { Player } from '../Player';
import { addTravel, aimDir, emitSkill, fireMoveStrike } from './moveStrike';

/** 돌진형 공통 (태클·돌진): 판정이 몸과 함께 · 돌진 구간 · 밀고 감 */
function startRush(
  p: Player,
  input: InputState,
  time: number,
  def: RushMoveDef,
  move: string,
  dashAttack: boolean,
): number {
  const a = aimDir(p, input);
  const first = dashAttack ? p.gear.firstStrike : null;
  const { total } = fireMoveStrike(p, input, time, def, {
    move,
    allowDash: dashAttack,
    first,
    extra: {
      rush: {
        dashFromMs: def.dash.fromMs,
        dashToMs: def.dash.fromMs + def.dash.ms,
        dashPx: def.dash.px,
        carryExtraPx: def.carryExtraPx,
        ...(def.contactFx ? { contactFx: def.contactFx } : {}),
        ...(def.groundFx ? { groundFx: def.groundFx } : {}),
      },
    },
  });
  addTravel(p, a.x, a.y, def.dash, time);
  return total;
}

/** 어깨 태클 (대쉬 공격 자리) */
export function startTackle(p: Player, input: InputState, time: number, def: RushMoveDef): number {
  emitSkill('tackle', 'start');
  return startRush(p, input, time, def, 'tackle', true);
}

/** 막다가 떼면 돌진 (퍼펙트 가드 직후 뗌) */
export function startGuardRush(p: Player, input: InputState, time: number, def: RushMoveDef): number {
  emitSkill('guard_rush', 'start');
  return startRush(p, input, time, def, 'guard_rush', false);
}

/**
 * 버티기 올려베기: 울분이 rageMinRatio 이상이면 전부 소모해 강화판(ember fx·판정 ×1.5·60°, 피해 = 차지와 같은 울분 배율).
 * 슈퍼아머 구간은 BasicMoves 가 잰다. 반환 = 동작 길이 ms
 */
export function startBrace(
  p: Player,
  input: InputState,
  time: number,
  def: BraceMoveDef,
  moving: boolean,
): { total: number; rage: boolean } {
  const g = p.gauges.grudge;
  const rage = Boolean(g && g.ratio >= def.rageMinRatio);
  const grudge = rage ? p.gauges.consumeGrudge() : null;
  emitSkill('brace_upswing', 'start', rage ? { rage: true } : {});
  const { total } = fireMoveStrike(p, input, time, def, {
    move: 'brace_upswing',
    moving,
    ...(rage && grudge
      ? {
          art: def.rageArt,
          hit: { hitShape: def.rageHitShape, damageMult: def.hit.damageMult * grudge.damageMult },
        }
      : {}),
  });
  return { total, rage };
}

/**
 * 공중제비 도약 찍기: 차지 단계(0~3)로 쐐기 길이·균열 행·피해(차지 단계 배율), 도약은 플레이어 시계 이동(벽에 막히면 그 자리 착지).
 * 반환 = 동작 길이 ms
 */
export function startLeap(p: Player, input: InputState, time: number, def: LeapMoveDef, stage: number): number {
  const a = aimDir(p, input);
  const C = gameState.weapon.def.combo?.charge;
  const st = stage > 0 ? C?.stages[Math.min(stage, C.stages.length) - 1] : undefined;
  const pick = <T>(list: readonly T[]): T => list[Math.min(stage, list.length - 1)];
  const grudge = def.consumesGrudge ? p.gauges.consumeGrudge() : { damageMult: 1, rangeMult: 1 };
  const lengthMult = pick(def.lengthMultByStage) * grudge.rangeMult;
  const R = currentRadius();
  emitSkill('leap', 'takeoff');
  const { total } = fireMoveStrike(p, input, time, def, {
    move: 'leap_slam',
    hit: { damageMult: def.hit.damageMult * (st?.damageMult ?? 1) * grudge.damageMult },
    shapeScale: { lengthMult },
    crack: pick(def.crackRowByStage),
    extra: {
      leap: {
        stage,
        ringRadiusPx: R * def.landingRing.radiusMult,
        ringDamageMult: def.landingRing.damageMult,
        spiralFx: def.spiralFx,
        startX: p.x,
        startY: p.y,
      },
    },
  });
  addTravel(p, a.x, a.y, def.leap, time);
  return total;
}

/** 현재 판정 반경 R (combo.radiusPx × 갈래·강화 배율) */
function currentRadius(): number {
  const w = gameState.weapon;
  const base = w.def.combo?.radiusPx ?? w.def.hitbox.reach + w.def.hitbox.width / 2;
  return base * (w.def.hitbox.reach > 0 ? w.hitbox.reach / w.def.hitbox.reach : 1);
}
