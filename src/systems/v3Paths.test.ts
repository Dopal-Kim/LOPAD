import { describe, expect, it } from 'vitest';
import { LIGHTING } from '../data';
import { ROUTE, arenaSize } from './route';
import {
  bodyBaseAction,
  bodyVariantActions,
  carryActionFor,
  fxDrawScale,
  v3HitLift,
  type SheetJson,
} from './spriteDefs';
import { bodyActionFor, sheetJsonCandidates, v3Only } from './spriteMeta';
import { lightingAmbientFor } from './lighting/lightMath';
import { TileSkin, propSheetJsonPath, propSkinFor, propSkins } from '../world/tileskin';

type RuleSheet = Pick<SheetJson, 'bodySheetByWeapon'>;

/** 로드된 몸 시트 표 (동작 → JSON) */
function sheets(table: Record<string, RuleSheet>): (a: string) => RuleSheet | undefined {
  return (a) => table[a];
}

describe('53라운드 v3 경로 일반화', () => {
  it('Q19 무기별 기본 자세: 아트 규칙(bodySheetByWeapon) → 이름 규칙(<동작>_<무기>) → 기본 몸', () => {
    const rule = {
      bodySheetByWeapon: {
        katana: 'player_idle',
        greatsword: 'player_idle_free',
        dagger: 'player_idle_free',
        bow: 'player_idle_free',
      },
    };
    const loaded = sheets({ idle: {}, idle_free: rule, walk: {}, idle_bow: {} });
    expect(bodyActionFor('idle', 'katana', loaded)).toBe('idle');
    expect(bodyActionFor('idle', 'greatsword', loaded)).toBe('idle_free');
    // 아트 규칙이 이름 규칙보다 먼저
    expect(bodyActionFor('idle', 'bow', loaded)).toBe('idle_free');
    // 규칙도 이름 시트도 없으면 기본 (walk_free 가 아직 없다)
    expect(bodyActionFor('walk', 'greatsword', loaded)).toBe('walk');
    // 규칙이 없을 때 이름 규칙
    expect(bodyActionFor('idle', 'bow', sheets({ idle: {}, idle_bow: {} }))).toBe('idle_bow');
    // 규칙이 가리키는 시트가 로드되지 않았으면 기본으로 되돌림
    const dangling = sheets({ idle: { bodySheetByWeapon: { dagger: 'player_idle_dagger' } } });
    expect(bodyActionFor('idle', 'dagger', dangling)).toBe('idle');
    // 값이 객체면 기본 동작 → 시트
    const nested = sheets({ run: { bodySheetByWeapon: { bow: { run: 'player_run_free' } } }, run_free: {} });
    expect(bodyActionFor('run', 'bow', nested)).toBe('run_free');
    // 변형 대상이 아닌 동작은 그대로
    expect(bodyActionFor('hurt', 'bow', loaded)).toBe('hurt');
    // 아무 시트도 없으면(테스트·구 환경) 기본 그대로 — 기존 동작 유지
    expect(bodyActionFor('idle', 'bow', () => undefined)).toBe('idle');
  });

  it('Q19 변형 동작: 기본 동작 · 휴대 오버레이 동작 · 로드 목록', () => {
    expect(bodyBaseAction('walk_free')).toBe('walk');
    expect(bodyBaseAction('idle_bow')).toBe('idle');
    expect(bodyBaseAction('katana_combo1')).toBe('katana_combo1');
    expect(bodyBaseAction('bow_aim')).toBe('bow_aim');
    expect(carryActionFor('run_free')).toBe('run');
    expect(carryActionFor('dash')).toBe('dash');
    expect(bodyBaseAction('dash_free')).toBe('dash_free'); // 53라운드 Q46: 대쉬는 공통 시트
    expect(carryActionFor('hurt')).toBe('idle');
    expect(bodyVariantActions(['bow'])).toEqual([
      'idle_free',
      'idle_bow',
      'walk_free',
      'walk_bow',
      'run_free',
      'run_bow',
    ]);
  });

  it('4번 구 시트 정리: 주인공 전부·칼 오버레이·v3 적 3종은 v3 전용, 대검·단검·활 오버레이·이펙트는 v3 → 기존', () => {
    expect(v3Only({ category: 'player', name: 'player' })).toBe(true);
    expect(v3Only({ category: 'weapons', name: 'katana' })).toBe(true);
    for (const name of ['greatsword', 'dagger', 'bow']) expect(v3Only({ category: 'weapons', name })).toBe(false);
    expect(v3Only({ category: 'fx', name: 'katana_combo1' })).toBe(false);
    for (const name of ['dummy', 'archer', 'charger']) {
      expect(v3Only({ category: 'enemies', name })).toBe(true);
      expect(sheetJsonCandidates({ category: 'enemies', name, action: 'idle' })).toEqual([
        `sprites/enemies/v3/${name}_idle.json`,
      ]);
    }
    expect(v3Only({ category: 'bosses', name: 'stage1' })).toBe(false);
  });

  it('이펙트 v3 그리는 배율: 구 1 · v2 0.5 · v3 0.25, JSON scale 곱, scale "allowed" 는 1', () => {
    expect(fxDrawScale({})).toBe(1);
    expect(fxDrawScale({ pixelScale: 1 })).toBe(0.5);
    expect(fxDrawScale({ pixelScale: 0.5 })).toBe(0.25);
    expect(fxDrawScale({ pixelScale: 0.5, scale: 2 })).toBe(0.5);
    expect(fxDrawScale({ pixelScale: 0.5, scale: 'allowed' as unknown as number })).toBe(0.25);
  });

  it('적 v3: 피격 연출 높이만 그림 중심으로 (구 시트·v2 는 0 — 기존 자리)', () => {
    // v3 96×144 피벗 y 138 → 월드 34.5 높이, 중심 17.25 - 바디 16 의 절반 8 = 9.25
    expect(v3HitLift({ pivot: { x: 48, y: 138 }, pixelScale: 0.5 }, 16)).toBeCloseTo(9.25);
    expect(v3HitLift({ pivot: { x: 16, y: 46 }, pixelScale: 1 }, 16)).toBe(0);
    expect(v3HitLift({ pivot: { x: 8, y: 23 } }, 16)).toBe(0);
  });

  it('바닥 소품 v3: tiles/v3/<타일셋>_props, tiles 없는 시트도 읽는다, 없으면 null (기존 소품)', () => {
    expect(propSheetJsonPath('stage1_outer')).toBe('tiles/v3/stage1_outer_props.json');
    expect(propSkinFor('stage1_outer')).toBeNull();
    const skin = new TileSkin(
      'k',
      {
        image: 'p.png',
        tileWidth: 64,
        pixelScale: 0.5,
        props: [{ index: 3, name: 'crate', solid: true }],
        bigProps: [{ name: 'well', rect: { x: 0, y: 0, w: 128, h: 128 }, pivot: { x: 64, y: 120 }, footprint: [2, 2] }],
      } as never,
      true,
    );
    expect(skin.props).toHaveLength(1);
    expect(skin.bigProps.map((b) => b.name)).toEqual(['well']);
    expect(skin.worldScale).toBe(0.25);
    propSkins.set('stage1_outer', skin);
    expect(propSkinFor('stage1_outer')).toBe(skin);
    propSkins.clear();
    // pixelScale 이 없으면 칸 크기로 (32px = 0.5)
    expect(new TileSkin('k', { image: 'a', tiles: {}, tileWidth: 32 }, true).worldScale).toBe(0.5);
  });

  it('Q38 조명: 5지역 모두 켬 — 테두리 지역은 regions 에 없으면 default, ?light=0 은 끔', () => {
    const border = (r: string | null | undefined) => ['outer', 'waste', 'gate', 'brewery', 'hall'].includes(r ?? '');
    expect(LIGHTING.borderRegions).toBe(true);
    for (const r of ['outer', 'waste', 'gate', 'brewery', 'hall'])
      expect(lightingAmbientFor(r, null, true, border, LIGHTING)).not.toBeNull();
    expect(lightingAmbientFor('waste', '0', true, border, LIGHTING)).toBeNull();
    // 테두리가 없는 지역·꺼진 플래그는 예전처럼 끔
    expect(lightingAmbientFor('nowhere', null, true, border, LIGHTING)).toBeNull();
    expect(lightingAmbientFor('gate', null, true, border, { ...LIGHTING, borderRegions: false })).toBeNull();
    // 지역 보정값(황무지)은 regions 자기 값
    expect(lightingAmbientFor('waste', null, true, border, LIGHTING)?.ambient).toBe(LIGHTING.regions.waste.ambient);
  });

  it('UI 요청 B8: 튜토리얼 전장(탄생)만 크게, 그 밖은 기본 · 보스 그대로', () => {
    expect(arenaSize('birth')).toEqual(ROUTE.arena.tutorial);
    expect(arenaSize('battle')).toEqual(ROUTE.arena.default);
    expect(arenaSize('boss')).toEqual(ROUTE.arena.boss);
    const [w, h] = ROUTE.arena.tutorial!;
    expect(w * h).toBeGreaterThan(ROUTE.arena.default[0] * ROUTE.arena.default[1]);
  });
});
