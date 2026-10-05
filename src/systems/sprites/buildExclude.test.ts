/**
 * 60라운드 (57 Q42 · 60 Q28) 빌드 제외 목록(`data/buildExclude.json`) 점검: 시스템이 로드하는 시트(부팅 + 모든 무기 + 각성)의
 * 후보 경로는 하나도 빠지지 않고, 옛 1단 진화 시트·꽂아내리기 그림은 빠진다.
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
    ])
      expect(excluded(rel), rel).toBe(true);
    // 새 갈래·각성 시트는 남는다
    for (const rel of [
      'sprites/fx/v3/katana_fall_wide.json',
      'sprites/fx/v3/bow_arrow_rapid.json',
      'sprites/fx/v3/katana_rise_awaken.json',
    ])
      expect(excluded(rel), rel).toBe(false);
  });
});
