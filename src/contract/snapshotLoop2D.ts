/**
 * 62 루프 2 시스템 D 스냅샷 덧붙임 (계약 UI §22 — snapshot.ts 를 덜 건드리려 따로). UI 파트는 import 금지.
 * - 키 재설정(P1-16): E 안내 `interactable.key`·노점 사기 키·4동사 대쉬 키캡을 묶인 키 이름으로
 * - 노점 카드(P1-13) · 전체화면(P1-16) · 월드 팻말(P1-17) · 자동 저장 표시(P2-5)
 */
import { settings, keyLabel } from '../systems/settings';
import type { UiShopOffer, UiSnapshot, UiWorldSign } from './ui';

/** 전체화면 여부 (hostLoop2D 가 넣는다 — 이 파일은 Phaser 없이 테스트에서도 불러진다) */
let fullscreenProbe: () => boolean = () => false;
export function setFullscreenProbe(fn: () => boolean): void {
  fullscreenProbe = fn;
}

export interface Loop2DSnapshotContext {
  shopOffer?: UiShopOffer | null;
  signs?: readonly UiWorldSign[];
  /** 노드 지도 런 (자동 저장 대상) */
  autoSave?: boolean;
}

export function withLoop2D(ctx: Loop2DSnapshotContext, snap: UiSnapshot): UiSnapshot {
  const keys = settings.current().keys;
  const interact = keyLabel(keys.interact);
  const dash = keyLabel(keys.dash);
  if (snap.interactable) snap.interactable.key = interact;
  if (snap.weaponVerbs)
    snap.weaponVerbs = {
      ...snap.weaponVerbs,
      verbs: snap.weaponVerbs.verbs.map((v) => (v.slot === 'dash' ? { ...v, key: dash } : v)),
    };
  snap.shopOffer = ctx.shopOffer
    ? { ...ctx.shopOffer, buyKey: interact, line: { ...ctx.shopOffer.line }, screen: { ...ctx.shopOffer.screen } }
    : null;
  snap.signs = (ctx.signs ?? []).map((s) => ({ ...s, screen: { ...s.screen } }));
  snap.fullscreen = fullscreenProbe();
  snap.autoSave = Boolean(ctx.autoSave);
  return snap;
}
