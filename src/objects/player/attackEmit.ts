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
import { artCandidates, hitArtKey, pickArt } from '../../systems/weapon/comboArt';
import { accelFxLevel } from '../../systems/weapon/swingSelect';
import type { InputState } from '../../systems/InputSystem';
import { facingOf, rowDirFor } from '../../systems/sprites/spriteDefs';
import { PLAYER_HIT_ORIGIN_UP_PX } from '../../systems/weapon/playerScale';
import type { Player } from '../Player';
import type { ComboStrike } from './heavyMoves';

/** 넉백 배율 · 56라운드 전용 동작·새 기본기 필드 (61라운드: 넣은 채 첫 타 보너스 삭제) */
export type AttackExtra = Pick<
  PlayerAttackPayload,
  | 'knockbackMult'
  | 'kenkiStage'
  | 'bowPower'
  | 'pierce'
  | 'crack'
  | 'issen'
  | 'crackLine'
  | 'move'
  | 'noImpactFx'
  | 'rush'
  | 'leap'
>;

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
  /** 56라운드 2단계: 몸 시트의 이 열만 제 시간으로 재생 (대치 일격 — 뗀 순간 releaseFrame 부터 끝까지) */
  frames?: number[],
): PlayerAttackPayload {
  const visual = p.visual;
  // 61 단계 4: 근접은 판정 원점(발 위 가슴 높이)에서 커서로 — 발에서 잰 방향이면 찌르기 축이 커서보다 원점 높이만큼 위로 지나갔다
  const fromY = gameState.weapon.def.kind === 'melee' ? p.y - PLAYER_HIT_ORIGIN_UP_PX : p.y;
  const aim = new Phaser.Math.Vector2(input.aimX - p.x, input.aimY - fromY);
  if (aim.lengthSq() > 0) aim.normalize();
  else aim.copy(p.facingVec);
  // 공격 애니는 조준 방향으로. 연격이면 그 타의 시트(없으면 attack)를 그 타 길이에, 아니면 다음 공격 가능 시점(쿨다운)에 맞춰
  const action = combo ? strikeBodyAction(p, combo) : 'attack';
  const shot = gameState.weapon.def.kind === 'ranged' ? gameState.weapon.shotTiming : null;
  const fit = combo ? combo.durationMs : (shot?.cooldownMs ?? gameState.weapon.shotTiming.cooldownMs);
  // 56라운드 Q6: 8행 시트(대검 연격·차지)는 조준각 8분할 행, 4행 시트는 기존 4방향
  const aimDir = rowDirFor(visual.sheet(action), aim.x, aim.y, visual.facing);
  // 51라운드 Q3: 판정·발사 프레임 시각을 따로 맞춘다 (연격 hitAtMs = 예비 동작, 활 drawMs = 시위 당김)
  const key = p.poses.keyFrame(action, combo, shot);
  // 조준 사격은 활 조준 시트의 발사 프레임 (없으면 기존 attack)
  const aimedRelease = a.kind === 'aimed' && p.poses.playAimRelease(facingOf(aim.x, aim.y, visual.facing), time);
  if (frames && frames.length > 0 && !aimedRelease) visual.playFrames(action, aimDir, frames, time);
  else if (!aimedRelease) visual.oneShot(action, aimDir, time, fit, key ?? undefined);
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
    // 56라운드 Q39 버그 수정: 조준 사격은 놓는 순간 화살 (놓기 시트 f0 시작) — 직전 동작의 프레임 시각을 쓰지 않는다
    releaseDelayMs: aimedRelease || a.kind === 'aimed' ? 0 : visual.frameStartMs(shot?.releaseFrame ?? 2),
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
    if (combo.crack) payload.crack = combo.crack;
  }
  // 49라운드 과열(61 가속): 단계 (난타·낙인) · 61 E 가속 그림 단계 = 이 타를 낼 때 공속 배율(가속 × 빌드 공속)
  const res = p.gear.resource;
  if (res?.kind === 'heat') {
    payload.heatStage = res.stage;
    payload.accelStage = accelFxLevel(res.speedMult * p.buildAttackSpeed);
  }
  // 60라운드 음향 칼 검기 단: 61라운드부터 검기를 소모한 동작(좌 홀드 발도)만 extra.kenkiStage 로 싣는다 — 찌르기는 늘 0
  if (extra) Object.assign(payload, extra);
  EventBus.emit(Events.PLAYER_ATTACKED, payload);
  return payload;
}
