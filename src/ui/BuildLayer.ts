import Phaser from 'phaser';
import type {
  UiConsumableUsed,
  UiCurse,
  UiCurseEnded,
  UiDualTrait,
  UiNodeGraded,
  UiPerfectSuccess,
  UiSnapshot,
  UiTagSetChanged,
} from '../contract/ui';
import { BuildChips, PerfectPop } from './BuildHud';
import { buildOf, perfectText, setChangeToast } from './buildView';
import { ElitePlates } from './EliteHud';
import { fill } from './text';
import { r60Text } from './text';
import { LAYOUT } from './theme';
import { PERFECT } from './themeBuild';
import { GradeCard, TrialChip } from './TrialHud';

export type ToastTone = 'gain' | 'loss' | 'mixed' | 'warn' | 'info';

export interface BuildLayerHooks {
  /** 우하단 결과 토스트 (구조물 결과와 같은 자리) */
  toast: (tone: ToastTone, text: string) => void;
  /** 가운데 배너 차례 */
  banner: (text: string) => void;
}

export interface BuildLayerFrame {
  stageIndex: number;
  /** 메뉴·지도·일시정지·결과가 떠 있다 (이름표·성과 칩 숨김) */
  overlay: boolean;
  /** 구조물 상태 칩 아래 끝 y (빌드 칩은 그 아래) */
  chipsBottom: number;
  /** 도전 판(투견 링·성소)이 떠 있다 (성과 칩은 그 아래로) */
  challengeOn: boolean;
}

/**
 * 57·60라운드 계약 §14 HUD 묶음 (HudScene 이 하나 만들고 STATE·이벤트를 넘긴다):
 * 빌드 칩(태그·세트·저주) · 완벽 성공 문구 · 엘리트 이름표 · 성과 진행 칩 · 성과 도장 카드, 그리고 §14.11 이벤트 알림
 * (세트 단계·이중 개성·저주·숨은 길·소모품 사용 → 토스트·배너). 소모품 칸은 하단 묶음 안이라 HudScene 이 그린다.
 */
export class BuildLayer {
  private chips: BuildChips;
  private pop: PerfectPop;
  private plates: ElitePlates;
  private trial: TrialChip;
  private grade: GradeCard;
  /** 태그별 마지막 세트 단계 (TAG_SET_CHANGED 가 오름인지 내림인지) — 처음 보는 태그는 스냅샷으로 채운다 */
  private stages = new Map<string, number>();
  private bundleTop = 0;
  private stageIndex = 0;
  private goldName = '';

  constructor(
    scene: Phaser.Scene,
    private hooks: BuildLayerHooks,
  ) {
    this.chips = new BuildChips(scene, LAYOUT.edge);
    this.pop = new PerfectPop(scene);
    this.plates = new ElitePlates(scene);
    this.trial = new TrialChip(scene);
    this.grade = new GradeCard(scene);
  }

  render(s: UiSnapshot, f: BuildLayerFrame, bundleTop: number): void {
    this.bundleTop = bundleTop;
    this.stageIndex = f.stageIndex;
    this.goldName = s.names?.gold ?? '';
    const build = buildOf(s);
    for (const t of build.tags) if (!this.stages.has(t.id)) this.stages.set(t.id, t.stage);
    const lab = Boolean(s.lab);
    this.chips.render(build, f.stageIndex, f.chipsBottom + 4);
    this.plates.render(s.elites, !f.overlay, f.stageIndex);
    this.trial.render(s.nodeTrial, !f.overlay && !lab, f.challengeOn, f.stageIndex);
  }

  // ---- §14.11 이벤트
  tagSetChanged(p: UiTagSetChanged): void {
    const t = setChangeToast(p, p?.tag ? this.stages.get(p.tag) : undefined, r60Text);
    if (p?.tag && typeof p.stage === 'number') this.stages.set(p.tag, p.stage);
    if (t) this.hooks.toast(t.tone, t.text);
  }

  dualTraitGained(p: UiDualTrait): void {
    if (p?.name) this.hooks.banner(fill(r60Text('dualGained'), { name: p.name }));
  }

  curseGained(p: UiCurse): void {
    if (!p?.name) return;
    const line = fill(r60Text('curseGained'), { name: p.name });
    this.hooks.toast('loss', p.penalty ? `${line}\n${p.penalty}` : line);
  }

  curseEnded(p: UiCurseEnded): void {
    if (p?.name) this.hooks.toast('gain', fill(r60Text('curseEnded'), { name: p.name }));
  }

  perfect(p: UiPerfectSuccess): void {
    // 간파 칩은 종류와 관계없이 한 번 깜빡 (간파 = 완벽 성공 태그, §14.1)
    this.chips.flash('insight');
    if (p?.kind && PERFECT.hudKinds.includes(p.kind))
      this.pop.show(perfectText(p, r60Text), this.bundleTop, this.stageIndex);
  }

  nodeGraded(p: UiNodeGraded): void {
    this.grade.show(p, this.goldName, this.stageIndex);
  }

  hiddenFound(): void {
    this.hooks.toast('info', r60Text('hiddenFoundToast'));
  }

  consumableUsed(p: UiConsumableUsed): void {
    if (p?.name) this.hooks.toast('info', fill(r60Text('consumableUsed'), { name: p.name, left: p.left ?? 0 }));
  }

  /** 런 끝·층 시작: 연출을 치우고 세트 단계 기억을 지운다 */
  reset(): void {
    this.stages.clear();
    this.grade.clear();
    this.pop.destroy();
  }

  destroy(): void {
    this.chips.destroy();
    this.pop.destroy();
    this.plates.destroy();
    this.trial.destroy();
    this.grade.destroy();
    this.stages.clear();
  }
}
