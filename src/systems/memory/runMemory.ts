/**
 * 62 루프 2 시스템 C (P16 §1·§4) 이번 생에 지닌 '기억' (GameState.memory — 새 런마다 새로, 세이브에 남긴다). Phaser 의존 없음.
 * 기억의 소품 하나 · 손이 기억한 모양 · 첫 개성 발현 카드 수(회피 시험 등급 + 먹 묻은 붓) · 찌그러진 투구 남은 횟수 · 다시 뽑기.
 */
import { keepsakeEffect } from './memory';

export interface RunMemorySave {
  keepsake: string | null;
  aspect: string | null;
  firstTraitCards: number;
  firstTraitDone: boolean;
  hitBlocks: number;
  rerolls?: number;
}

export class RunMemory {
  keepsake: string | null = null;
  aspect: string | null = null;
  /** 첫 개성 발현 카드 수 (0 = 기본 — growth.traitChoices) */
  firstTraitCards = 0;
  /** 첫 개성 발현 메뉴를 이미 열었다 */
  firstTraitDone = false;
  /** 찌그러진 투구: 남은 '첫 피격 무효' 횟수 */
  hitBlocks = 0;
  /** 개성 '다시 뽑기' 남은 수 (장터 먹물 한 병 · 사연) — 다음 개성 발현 메뉴에 한 줄 */
  rerolls = 0;

  /** 새 런 시작: 소품 효과 중 런 상태로 남는 것(잔·붓)을 채운다. trialCards = 회피 시험 등급이 정한 카드 수(0 = 기본) */
  begin(o: {
    keepsake?: string | null;
    aspect?: string | null;
    trialCards?: number;
    baseCards: number;
    maxCards: number;
  }): void {
    this.keepsake = o.keepsake ?? null;
    this.aspect = o.aspect ?? null;
    const fx = keepsakeEffect(this.keepsake);
    const base = o.trialCards && o.trialCards > 0 ? o.trialCards : o.baseCards;
    const cards = base + (fx.firstTraitCards ?? 0);
    this.firstTraitCards = cards > o.baseCards ? Math.min(o.maxCards, cards) : 0;
    this.firstTraitDone = false;
    this.hitBlocks = fx.firstHitBlock ?? 0;
    this.rerolls = 0;
  }

  /** 이번 개성 발현 메뉴의 카드 수 (첫 번째만 늘어난다 — 부르면 '썼다'로 남긴다) */
  takeTraitCards(base: number): number {
    if (this.firstTraitDone) return base;
    this.firstTraitDone = true;
    return Math.max(base, this.firstTraitCards);
  }

  /** 다시 뽑기 하나를 쓴다 (남았으면 true) */
  takeReroll(): boolean {
    if (this.rerolls <= 0) return false;
    this.rerolls -= 1;
    return true;
  }

  /** 찌그러진 투구: 맞을 피해를 한 번 막는다 (남았으면 true) */
  takeHitBlock(): boolean {
    if (this.hitBlocks <= 0) return false;
    this.hitBlocks -= 1;
    return true;
  }

  /** 대쉬 충전 + (매듭 끈) */
  get dashCharges(): number {
    return keepsakeEffect(this.keepsake).dashCharges ?? 0;
  }

  toSave(): RunMemorySave {
    return {
      keepsake: this.keepsake,
      aspect: this.aspect,
      firstTraitCards: this.firstTraitCards,
      firstTraitDone: this.firstTraitDone,
      hitBlocks: this.hitBlocks,
      rerolls: this.rerolls,
    };
  }

  restore(s: Partial<RunMemorySave> | undefined): void {
    this.keepsake = typeof s?.keepsake === 'string' ? s.keepsake : null;
    this.aspect = typeof s?.aspect === 'string' ? s.aspect : null;
    this.firstTraitCards = Math.max(0, Math.floor(Number(s?.firstTraitCards) || 0));
    this.firstTraitDone = Boolean(s?.firstTraitDone);
    this.hitBlocks = Math.max(0, Math.floor(Number(s?.hitBlocks) || 0));
    this.rerolls = Math.max(0, Math.floor(Number(s?.rerolls) || 0));
  }
}
