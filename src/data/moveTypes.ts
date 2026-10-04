/**
 * 56라운드 2단계 새 기본기 데이터 형식 (data/weapons.json 무기별 `moves` — 결정 2026-10-04-round-56 Q40~Q43·Q52~Q55·Q60~Q63,
 * 계약 art §18.6~§18.9). 시각·판정·이동은 아트 시트 JSON 값을 옮긴 임시값이고 시스템 데이터가 기준(§17).
 * 판정 모양은 연격과 같은 R 기준(`combo.radiusPx`, 없으면 reach + width/2) · 각도 = 조준 0° 시계 +.
 * 시트의 프레임 구성(holdFrames·loopFrames·releaseFrame 등)은 몸 시트 JSON 에서 읽고, 없으면 한 번 재생으로 대신한다.
 * `…Fx` 는 휘두름 fx 밖의 보조 이펙트 이름 — 시트 id = `<무기>_<이름>` (Preloader 가 `moveFxNames` 로 로드).
 */
import type { ComboHitDef, HitShapeSpec } from './comboTypes';

/** 이동 구간 (몸 시트 시각 기준): fromMs 부터 ms 동안 px (easeOut 이면 앞이 빠르게) */
export interface MoveTravelDef {
  px: number;
  fromMs: number;
  ms: number;
  easing?: 'linear' | 'easeOut';
}

/** 한 번 휘두르는 새 기본기 공통 — 연격 파이프라인(판정 모양·휘두름 이펙트·히트스톱)을 그대로 쓴다 */
export interface MoveStrikeDef {
  /** 그림 이름 표(`combo.art`) 키 — 몸 `player_<무기>_<이름>`·무기·fx */
  art: string;
  hit: ComboHitDef;
  /** 기력 소모 (기력 무기만, 없으면 0) */
  staminaCost?: number;
}

/** 칼 간파 반격 (Q40·Q55): 패링 성공 직후 windowMs 안 좌클릭 — 조준 방향의 해부 왼쪽으로 비켜서며 반격 */
export interface CounterMoveDef extends MoveStrikeDef {
  windowMs: number;
  sidestep: MoveTravelDef;
}

/**
 * 칼 대치 일격 (Q40·Q53·Q55·Q60): F 로 넣은 채 좌클릭을 누르는 동안 유지 루프, 떼면 발도(언제 떼도 같은 일격, 넣기 첫 타 치명).
 * 판정·끝은 뗀 시각 기준 (`release`). 유지 readyAfterHoldMs 의 반짝임(`readyFx`)은 연출만
 */
export interface IaiMoveDef extends MoveStrikeDef {
  readyAfterHoldMs: number;
  /** 준비 반짝임 fx (칼집 입구 koiguchiAnchors) */
  readyFx: string;
  release: {
    /** 뗀 뒤 판정 시작 · 판정 유지 · 딸깍(선 터짐 — 연출) · 끝 */
    hitMs: number;
    activeMs: number;
    clickMs: number;
    totalMs: number;
  };
}

/** 대검 어깨 태클·막다가 떼면 돌진 (Q41·Q55): 돌진하며 몸 앞 사각형이 함께 이동, 적마다 1회, 적을 밀고 감 */
export interface RushMoveDef extends MoveStrikeDef {
  dash: MoveTravelDef;
  /** 밀고 가는 적의 이동 (돌진 끝까지 남은 거리 + 이만큼 더) */
  carryExtraPx: number;
  /** 막다가 떼면 돌진: 퍼펙트 가드 뒤 이 시간 안에 떼면 돌진 (태클은 없음) */
  windowMs?: number;
  /** 태클: 첫 접촉 순간 몸을 따라가는 fx · 돌진: 돌진 출발에 고정된 바닥 fx(땅 홈, 주인공 아래) */
  contactFx?: string;
  groundFx?: string;
}

/** 대검 버티기 올려베기 (Q41·Q54·Q61): 가드 중 좌클릭 — 슈퍼아머(맞은 피해 그대로, 울분으로 쌓임) · 울분 소모 시 강화 */
export interface BraceMoveDef extends MoveStrikeDef {
  superArmorMs: number;
  /** 울분 소모판: 그림 키(ember fx) · 판정 모양 · 이 비율 이상 쌓였을 때만 소모 */
  rageArt: string;
  rageHitShape: HitShapeSpec;
  rageMinRatio: number;
  /** 슈퍼아머 중 피격마다 몸 위 fx */
  absorbFx: string;
}

/** 대검 공중제비 도약 찍기 (Q41·Q55): 차지 중 스페이스 — 차지 단계 유지, 착지 쐐기 + 끝 충격원 + 착지 링, 공중 무적 없음 */
export interface LeapMoveDef extends MoveStrikeDef {
  leap: MoveTravelDef;
  /** 차지 단계(0·1·2·3) → 쐐기 길이 배율 (0단은 첫 값) · 균열 행 */
  lengthMultByStage: number[];
  crackRowByStage: string[];
  /** 착지 발밑 링 판정 (반지름 = R × 값) · 피해 배율 */
  landingRing: { radiusMult: number; damageMult: number };
  /** 나선 fx (도약 출발 발에 고정 — 벽에 막혀 짧게 뛰면 생략) */
  spiralFx: string;
  /** 차지처럼 울분을 소모하는가 (결정 없음 — 임시) */
  consumesGrudge: boolean;
}

/** 단검 등 뒤 치명 찌르기 (Q42·Q55): 그림자 걸음 직후 좌클릭 — 확정 치명, 전용 섬광만(공용 치명 fx 없음) */
export type BackstabMoveDef = MoveStrikeDef;

/** 단검 고속 난타 (Q42·Q55): 좌클릭 홀드 — 시작 → 루프(찌르기마다 판정) → 끝, 과열 단계로 fx 시트만 바꿈 */
export interface FlurryMoveDef extends MoveStrikeDef {
  /** 이만큼 누르고 있으면 난타 시작 (그 전에 뗀 누름은 기본 연격) */
  holdMs: number;
  /** 찌르기 한 번의 가열 · 이동 배율 */
  heatPerStab: number;
  moveMult: number;
  /** 과열 경계(비율, 오름차순) → fx 이름 (경계 수 + 1 개, 몸 프레임과 같은 열로 바꿔 낌) */
  heatBounds: number[];
  heatFx: string[];
}

/** 활 화살비 (Q43·Q52·Q55): 우클릭으로 가득 당긴 채 좌클릭 — 3발 연속 발사 → 커서 원 안 무작위 낙하점마다 작은 판정 */
export interface ArrowRainMoveDef {
  /** 몸·무기 동작 이름 (`player_<무기>_<이름>`) */
  art: string;
  durationMs: number;
  /** 몸 시트 releaseFrames 가 없을 때 발사 시각 */
  releasesAtMs: number[];
  ammoCost: number;
  /** 예고 원: 반지름 · 시트 행 (s·m·l) */
  markRadiusPx: number;
  markRow: string;
  /** 낙하: 개수 · 간격 · 첫 낙하(좌클릭부터) · 작은 판정 반지름 · 피해 배율(공격력 대비) */
  drops: number;
  dropIntervalMs: number;
  firstDropAtMs: number;
  dropRadiusPx: number;
  damageMult: number;
  /** fx 이름 (솟는 화살 · 예고 원 · 떨어지는 화살) */
  riseFx: string;
  markFx: string;
  fallFx: string;
}

/** 무기별 새 기본기 (있는 것만) */
export interface WeaponMovesDef {
  counter?: CounterMoveDef;
  iai?: IaiMoveDef;
  tackle?: RushMoveDef;
  brace?: BraceMoveDef;
  leap?: LeapMoveDef;
  guardRush?: RushMoveDef;
  backstab?: BackstabMoveDef;
  flurry?: FlurryMoveDef;
  arrowRain?: ArrowRainMoveDef;
}

/** 새 기본기 보조 fx 이름 전부 (Preloader 로드 목록 — 시트 id = `<무기>_<이름>`) */
export function moveFxNames(m: WeaponMovesDef | undefined): string[] {
  if (!m) return [];
  const out = [
    m.iai?.readyFx,
    m.tackle?.contactFx,
    m.tackle?.groundFx,
    m.guardRush?.contactFx,
    m.guardRush?.groundFx,
    m.brace?.absorbFx,
    m.leap?.spiralFx,
    ...(m.flurry?.heatFx ?? []),
    m.arrowRain?.riseFx,
    m.arrowRain?.markFx,
    m.arrowRain?.fallFx,
  ];
  return out.filter((n): n is string => typeof n === 'string' && n.length > 0);
}
