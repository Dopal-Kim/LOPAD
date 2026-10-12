/**
 * 62 루프 1 (P15 · 계약 UI §20) 시작 의식 규칙 (Phaser 의존 없음): 획 ↔ 무기 규칙 줄 · 왜 이 무기인지 · 손이 기억한 무기 ·
 * 획이 기우는 무기 · 영혼 강화 귀퉁이 · 회피 시험 등급 · 부채꼴 각도 · 자리 비율 → 좌표.
 * 무기 결정 규칙은 그대로 3획만으로(`personality.chooseWeapon`, 49라운드 2절). 화면에는 수치를 내보내지 않는다.
 */
import type { UiRitualLegend } from '../../contract/ui';
import type { PersonalityData, WeaponTable } from '../../data/types';
import type { RitualData, RitualTrialData, TrialGrade } from '../../data/ritual';
import { chooseWeapon, strokeFeatures, type Stroke } from '../personality';
import type { DiaryRecord } from '../narrative/diary';
import { upgradeCost, type MetaConfig, type MetaData } from '../meta';

/** 획 ↔ 무기 규칙 (무기 표 순서) */
export function legendOf(data: Pick<RitualData, 'legend'>, weapons: WeaponTable): UiRitualLegend[] {
  return Object.entries(weapons)
    .filter(([id]) => Boolean(data.legend[id]))
    .map(([id, w]) => ({ weapon: id, weaponName: w.name, line: data.legend[id] }));
}

/** 왜 이 무기인지 한 줄 (모르는 무기면 '') */
export function whyOf(data: Pick<RitualData, 'why'>, weapon: string, source: 'strokes' | 'remembered'): string {
  return data.why[weapon]?.[source] ?? '';
}

/** 지금까지 그은 획이 기우는 무기 (획이 없으면 undefined) — 획 판정 연출용 */
export function leaningWeapon(strokes: Stroke[], weapons: WeaponTable, P: PersonalityData): string | undefined {
  if (strokes.length === 0) return undefined;
  return chooseWeapon(strokeFeatures(strokes, P), weapons, P).id || undefined;
}

/** 두 번째 생: 손이 기억한 무기 = 지난 생 무기 (기록이 없거나 지금 무기 표에 없으면 null — 3획으로) */
export function rememberedWeapon(diary: Pick<DiaryRecord, 'pastLives'>, weapons: WeaponTable): string | null {
  const last = diary.pastLives[diary.pastLives.length - 1];
  return last && weapons[last.weapon] ? last.weapon : null;
}

/** 영혼 강화 귀퉁이: 보유 영혼 · 지금 살 수 있는 강화가 있나 */
export function metaCorner(meta: Pick<MetaData, 'souls' | 'upgrades'>, config: Pick<MetaConfig, 'upgrades'>) {
  const canBuy = config.upgrades.some((u) => {
    const lv = meta.upgrades[u.id] ?? 0;
    return lv < u.maxLevel && meta.souls >= upgradeCost(u, lv);
  });
  return { souls: meta.souls, canBuy };
}

/** 회피 시험 등급 (맞은 수 합계) → 등급 · 시작 감각 보너스 */
export function gradeHits(
  hits: number,
  T: Pick<RitualTrialData, 'grade' | 'bonus'>,
): { grade: TrialGrade; bonus: number } {
  const grade: TrialGrade = hits <= T.grade.S ? 'S' : hits <= T.grade.A ? 'A' : hits <= T.grade.B ? 'B' : 'C';
  return { grade, bonus: T.bonus[grade] };
}

/** 부채꼴 각도 (가운데 = aim, count 발을 deg 폭에 고르게). count 1 이면 [aim] */
export function fanAngles(aim: number, count: number, deg: number): number[] {
  const n = Math.max(1, Math.round(count));
  if (n === 1) return [aim];
  const span = (deg * Math.PI) / 180;
  return Array.from({ length: n }, (_, i) => aim - span / 2 + (span * i) / (n - 1));
}

/** 자리 비율 [x, y] (가운데 기준 반 폭·반 높이) → 월드 좌표 */
export function spotAt(
  ratio: readonly [number, number],
  area: { x: number; y: number; w: number; h: number },
): { x: number; y: number } {
  return { x: area.x + area.w / 2 + (ratio[0] * area.w) / 2, y: area.y + area.h / 2 + (ratio[1] * area.h) / 2 };
}

/** 이 사격(volley 번째)을 쏠 사수 번호 — 여럿이면 차례로 */
export function shooterFor(volley: number, shooters: number): number {
  return ((volley % shooters) + shooters) % shooters;
}

/** 이름 다듬기: 앞뒤 공백 제거 · 최대 maxLen 글자 (한글 조합 글자 단위) */
export function cleanName(raw: string, maxLen: number): string {
  return Array.from(raw.trim()).slice(0, maxLen).join('');
}
