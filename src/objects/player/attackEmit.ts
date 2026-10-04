/**
 * 공격 1회 알림 (51라운드 정리 — Player 에서 분리): 조준 방향으로 몸·무기 애니 재생(연격 = 그 타 시트를 그 타 길이에,
 * 판정 프레임은 hitAtMs 에 · 활 = 다음 발 간격에, 발사 프레임은 drawMs 에) → 시트 메모로 휘두름·발사·다음 타 허용 시각 →
 * `PLAYER_ATTACKED` 페이로드.
 * 55라운드 §17: 몸 시트 = 그림 이름 표(`combo.art`)의 로드된 첫 후보, 판정 모양·막타·후속 판정은 타 데이터를 그대로 싣는다.
 * 타별 판정 모양이 있는 새 연격은 다음 타 허용을 데이터(cancelFromMs)로만 정한다(대체 시트의 cancelFromFrame 은 옛 연격용).
 */
import Phaser from 'phaser';
import { EventBus, Events, type PlayerAttackPayload } from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import { artCandidates, hitArtKey, pickArt } from '../../systems/comboArt';
import type { InputState } from '../../systems/InputSystem';
import { facingOf } from '../../systems/spriteDefs';
import type { Player } from '../Player';
import type { ComboStrike } from './heavyMoves';

/** 51라운드 Q4: 넣은 채 첫 타 보너스 표시 (발도·끌어내기) */
export type AttackExtra = Pick<PlayerAttackPayload, 'firstStrike' | 'knockbackMult'>;

/** 연격 타의 그림 키 (차지 = 차지 hit.art, 없으면 `combo<n>`) */
function strikeArt(combo: ComboStrike): string {
  return combo.hit.art ?? hitArtKey(gameState.weapon.def.combo, combo.index);
}

/** 연격 타의 몸 동작 `<무기>_<이름>` (그림 표의 로드된 첫 후보, 없으면 attack) */
export function strikeBodyAction(p: Player, combo: ComboStrike): string {
  const id = gameState.weapon.id;
  const names = artCandidates(gameState.weapon.def.combo, strikeArt(combo), 'body');
  const name = pickArt(names, (n) => p.visual.hasAction(`${id}_${n}`));
  return name ? `${id}_${name}` : 'attack';
}

export function emitPlayerAttack(
  p: Player,
  input: InputState,
  time: number,
  a: Pick<PlayerAttackPayload, 'kind' | 'damageMult' | 'sizeMult' | 'forceCrit' | 'primed'>,
  combo: ComboStrike | null,
  extra?: AttackExtra,
): PlayerAttackPayload {
  const visual = p.visual;
  const aim = new Phaser.Math.Vector2(input.aimX - p.x, input.aimY - p.y);
  if (aim.lengthSq() > 0) aim.normalize();
  else aim.copy(p.facingVec);
  // 공격 애니는 조준 방향으로. 연격이면 그 타의 시트(없으면 attack)를 그 타 길이에, 아니면 다음 공격 가능 시점(쿨다운)에 맞춰
  const action = combo ? strikeBodyAction(p, combo) : 'attack';
  const shot = gameState.weapon.def.kind === 'ranged' ? gameState.weapon.shotTiming : null;
  const fit = combo ? combo.durationMs : (shot?.cooldownMs ?? gameState.weapon.hitbox.cooldownMs);
  const aimDir = facingOf(aim.x, aim.y, visual.facing);
  // 51라운드 Q3: 판정·발사 프레임 시각을 따로 맞춘다 (연격 hitAtMs = 예비 동작, 활 drawMs = 시위 당김)
  const key = p.poses.keyFrame(action, combo, shot);
  // 조준 사격은 활 조준 시트의 발사 프레임 (없으면 기존 attack)
  if (!(a.kind === 'aimed' && p.poses.playAimRelease(aimDir, time)))
    visual.oneShot(action, aimDir, time, fit, key ?? undefined);
  // 연격 시트 JSON 메모: hitFrames[0](없으면 impactFrame) 시작 = 휘두름 시점, cancelFromFrame 시작 = 다음 타 허용
  const sheet = action !== 'attack' ? visual.sheet(action) : undefined;
  const hf = sheet?.hitFrames?.[0] ?? (typeof sheet?.impactFrame === 'number' ? sheet.impactFrame : undefined);
  if (typeof sheet?.cancelFromFrame === 'number' && !combo?.hit.hitShape && combo?.charge === undefined)
    p.combo?.overrideCancel(visual.frameStartMs(sheet.cancelFromFrame));
  const charge = combo?.charge;
  const followUps = combo ? [...(combo.hit.followUps ?? []), ...(combo.extraFollowUps ?? [])] : [];
  const payload: PlayerAttackPayload = {
    x: p.x,
    y: p.y,
    dirX: aim.x,
    dirY: aim.y,
    ...a,
    swingDelayMs: hf !== undefined ? visual.frameStartMs(hf) : visual.lastImpactMs,
    releaseDelayMs: visual.frameStartMs(shot?.releaseFrame ?? 2),
    comboIndex: charge === undefined ? combo?.index : undefined,
    comboCount: charge === undefined ? combo?.count : undefined,
    activeMs: combo ? Math.max(combo.hit.activeMs, p.poses.activeWindowMs(sheet)) : undefined,
    durationMs: combo?.durationMs,
    bodyAction: action,
    bodyFrameStartsMs: [...visual.lastFrameStarts],
  };
  if (combo) {
    payload.heavy = combo.heavy ?? combo.hit.heavy;
    payload.art = strikeArt(combo);
    if (combo.hit.hitShape) payload.hitShape = combo.hit.hitShape;
    if (combo.shapeScale) payload.shapeScale = combo.shapeScale;
    if (followUps.length > 0) payload.followUps = followUps;
    if (charge !== undefined) payload.charge = charge;
    if (combo.momentum !== undefined) payload.momentum = combo.momentum;
  }
  // 49라운드 과열: 가열 단계 (이펙트 강화)
  const res = p.gear.resource;
  if (res?.kind === 'heat') payload.heatStage = res.stage;
  if (extra) Object.assign(payload, extra);
  EventBus.emit(Events.PLAYER_ATTACKED, payload);
  return payload;
}
