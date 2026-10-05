/**
 * 60라운드 (57 Q42 · 60 Q28 · Q35) 빌드 제외 목록(`data/buildExclude.json`) 점검: 시스템이 로드하는 시트(부팅 + 모든 무기 + 각성 —
 * 갈래×각성 합친 그림 포함)의 후보 경로는 하나도 빠지지 않고, 옛 1단 진화 시트·꽂아내리기 그림·컨셉 fx·더 옛 진화 fx 는 빠진다.
 */
import { describe, expect, it } from 'vitest';
import exclude from '../../../data/buildExclude.json';
import { WEAPONS } from '../../data';
import { allSheetRequests, awakenSheetRequests } from './sheetSets';
import { sheetJsonCandidates } from './spriteMeta';

const patterns = exclude.patterns.map((p) => new RegExp(p));
const excluded = (rel: string) => patterns.some((r) => r.test(rel));

describe('빌드 제외 (data/buildExclude.json)', () => {
  it('로드하는 시트(후보 경로 전부)는 빌드에서 빠지지 않는다', () => {
    const reqs = [...allSheetRequests(), ...Object.keys(WEAPONS).flatMap(awakenSheetRequests)];
    const hit = reqs.flatMap((r) => sheetJsonCandidates(r)).filter(excluded);
    expect(hit).toEqual([]);
  });

  it('옛 2단·1단 진화 시트와 꽂아내리기 그림은 빠진다 (그림 png 포함)', () => {
    for (const rel of [
      'sprites/fx/v3/zangetsu.json',
      'sprites/fx/v3/iai.json',
      'sprites/fx/batto.png',
      'sprites/fx/v3/katana_combo2_iai.json',
      'sprites/fx/v3/greatsword_combo1_weight.png',
      'sprites/fx/v3/dagger_combo3_twin.json',
      'sprites/fx/v3/greatsword_plunge_wave.json',
      'sprites/weapons/v3/greatsword_charge_plunge.png',
      'sprites/weapons/v3/greatsword_charge_plunge_grudge2.json',
      'sprites/player/v3/player_greatsword_charge_plunge.json',
      // 60 Q35: 컨셉 fx 11종 · 더 옛 진화 fx (루트·v3)
      'sprites/fx/concept_assassin.json',
      'sprites/fx/concept_heavyarrow_bolt.png',
      'sprites/fx/concept_telegraph_line.json',
      'sprites/fx/concept_zangetsu.png',
      'sprites/fx/flash.json',
      'sprites/fx/v3/flash.png',
      'sprites/fx/heavyarrow.png',
      'sprites/fx/v3/heavyarrow_hit.json',
      'sprites/fx/rain.json',
      'sprites/fx/scatter.png',
      'sprites/fx/seek.json',
      // 61 E 아트 2 '이제 안 쓰는 그림'
      'sprites/fx/v3/greatsword_guard_rush.json',
      'sprites/player/v3/player_greatsword_guard_rush.png',
      'sprites/weapons/v3/greatsword_guard_rush_grudge2.json',
      'sprites/weapons/v3/greatsword_guard_rush_awaken.png',
      'sprites/fx/v3/katana_issen_shadow.json',
      'sprites/fx/v3/katana_thrust_ki1.png',
      'sprites/weapons/v3/katana_thrust_ki3.json',
      'sprites/fx/v3/dagger_overheat_cool.png',
      'sprites/fx/v3/dagger_combo2_heat3.json',
    ])
      expect(excluded(rel), rel).toBe(true);
    // 새 갈래·각성 시트는 남는다
    for (const rel of [
      'sprites/fx/v3/katana_fall_wide.json',
      'sprites/fx/v3/bow_arrow_rapid.json',
      'sprites/fx/v3/katana_rise_awaken.json',
      'sprites/fx/v3/katana_fall_wide_awaken.json',
      'sprites/fx/v3/dagger_combo3_double_awaken.json',
      // 61 E 새 그림 (가속 단계 · 발도 검기 단 · 무기 휴대 검기)
      'sprites/fx/v3/dagger_combo1_accel2.json',
      'sprites/fx/v3/katana_iai_ki2.png',
      'sprites/weapons/v3/katana_iai_ki1.json',
      'sprites/fx/v3/dagger_flurry_heat2.json',
      // 이름이 비슷한 쓰는 시트 (Q35 패턴이 넘치지 않는지)
      'sprites/fx/v3/muzzle_flash.json',
      'sprites/fx/v3/parry_flash.png',
      'sprites/fx/v3/telegraph_line.json',
      // 무기 아이콘 4종은 유지 (Q35)
      'sprites/weapons/katana_icon.png',
      'sprites/weapons/v3/bow_icon.json',
    ])
      expect(excluded(rel), rel).toBe(false);
  });
});
