/**
 * 대검 동작 (56라운드 2단계 Q41·Q54·Q55·Q61·Q63, 계약 art §18.8 → 61라운드 P1 4동사):
 * - 어깨 태클 `greatsword_tackle` — 기본 대쉬 공격: 돌진 40, 판정이 몸과 함께 이동·적을 밀고 감, fx 는 첫 접촉 순간
 * - 버티기 올려베기 `greatsword_brace_upswing` — 중압 갈래: 막은 직후 우클릭을 떼면. 슈퍼아머 0.46초(피해 그대로·울분으로 쌓임),
 *   울분 소모 시 ember ×1.5·60°
 * - 공중제비 도약 찍기 `greatsword_leap_slam` — 파쇄 갈래: 대쉬 공격이 태클 대신. 착지 쐐기 + 끝 충격원 + 링 0.6R, 공중 무적 없음
 * ('막다가 떼면 돌진'은 61라운드에 삭제 — 가드 우클릭 한 동사에 겹치던 입력)
 * 판정·fx 는 씬(PlayerStrikes·MoveStrikes)이 PLAYER_ATTACKED `move` 로.
 */
import { gameState } from '../../core/GameState';
import type { BraceMoveDef, LeapMoveDef, RushMoveDef } from '../../data/types';
import type { InputState } from '../../systems/InputSystem';
import { weaponRangeScale } from '../../systems/weapon/playerScale';
import type { Player } from '../Player';
import { addTravel, aimDir, emitSkill, fireMoveStrike } from './moveStrike';

/** 어깨 태클 (대쉬 공격 자리): 판정이 몸과 함께 · 돌진 구간 · 밀고 감 */
export function startTackle(p: Player, input: InputState, time: number, def: RushMoveDef): number {
  emitSkill('tackle', 'start');
  const a = aimDir(p, input);
  const { total } = fireMoveStrike(p, input, time, def, {
    move: 'tackle',
    allowDash: true,
    extra: {
      rush: {
        dashFromMs: def.dash.fromMs,
        dashToMs: def.dash.fromMs + def.dash.ms,
        dashPx: def.dash.px,
        carryExtraPx: def.carryExtraPx,
        ...(def.contactFx ? { contactFx: def.contactFx } : {}),
      },
    },
  });
  addTravel(p, a.x, a.y, def.dash, time);
  return total;
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

/** 공중제비 도약 찍기 (파쇄 갈래 — 대쉬 공격 자리): 착지 쐐기·균열 행·피해는 데이터, 도약은 플레이어 시계 이동(벽에 막히면 그 자리 착지). 반환 = 동작 길이 ms */
export function startLeap(p: Player, input: InputState, time: number, def: LeapMoveDef): number {
  const a = aimDir(p, input);
  const grudge = def.consumesGrudge ? p.gauges.consumeGrudge() : { damageMult: 1, rangeMult: 1 };
  const R = currentRadius();
  emitSkill('leap', 'takeoff');
  const { total } = fireMoveStrike(p, input, time, def, {
    move: 'leap_slam',
    allowDash: true,
    hit: { damageMult: def.hit.damageMult * grudge.damageMult },
    shapeScale: { lengthMult: def.lengthMult * grudge.rangeMult },
    ...(def.crackRow ? { crack: def.crackRow } : {}),
    extra: {
      leap: {
        stage: 0,
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

/** 현재 판정 반경 R (combo.radiusPx × 갈래·강화 배율 × 58라운드 주인공 판정 배율) */
function currentRadius(): number {
  const w = gameState.weapon;
  return (w.def.combo?.radiusPx ?? 0) * weaponRangeScale(w);
}
