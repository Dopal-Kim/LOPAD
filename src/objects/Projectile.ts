import Phaser from 'phaser';
import { COLORS, DEPTH } from '../core/Constants';
import { placeholderTexture } from './EntityVisual';
import type { ProjectileSpec } from './Mob';

type Body = Phaser.Physics.Arcade.Body;
export type ProjectileOwner = 'enemy' | 'player';

/** 투사체 외형: 아트 텍스처(화살)가 있으면 그것을, 없으면 단색 사각형 */
export interface ProjectileVisual {
  /** spriteLibrary 텍스처 키 (현재 층 변형). 없으면 플레이스홀더 */
  texture?: string | null;
  /** 진행 각도로 회전 (우향으로 그려진 시트, 계약 §3.1 `rotate`) */
  rotate?: boolean;
  /** 원점 (시트 pivot ÷ 프레임 크기). 없으면 중심 */
  originX?: number;
  originY?: number;
  /** 루프 애니 키 (보스 부채꼴 탄 2프레임 맥동). 없으면 0번 프레임 고정 */
  anim?: string | null;
}

/** 투사체. 벽에 닿거나 수명이 끝나면 비활성화되어 풀로 돌아간다. */
export class Projectile extends Phaser.GameObjects.Sprite {
  declare body: Body;
  attack = 0;
  owner: ProjectileOwner = 'enemy';
  /** 패링으로 반사됨: 플레이어 대신 적을 맞힌다 */
  reflected = false;
  /** 남은 관통 횟수 (플레이어 투사체). Infinity = 무한 관통 */
  pierceLeft = 0;
  /** 유도 선회 속도 (rad/s). 0 이면 유도 없음 */
  homingTurn = 0;
  /** 적중 시 적 경직 ms (조준 사격 중시) */
  hitStunMs = 0;
  /** 치명타로 굴려진 플레이어 투사체 (피격음 분기) */
  crit = false;
  /** 아트 텍스처 사용 중 (틴트 대신 원색, 속도 방향으로 회전) */
  private textured = false;
  private rotateToVelocity = false;
  /** 같은 적을 두 번 맞히지 않기 위한 기록 */
  private hitSet = new Set<unknown>();
  private expireAt = 0;

  constructor(scene: Phaser.Scene) {
    super(scene, 0, 0, placeholderTexture(scene, 4, 4));
    scene.add.existing(this);
    scene.physics.add.existing(this);
    this.setDepth(DEPTH.PROJECTILE);
    this.deactivate();
  }

  launch(
    x: number,
    y: number,
    dirX: number,
    dirY: number,
    spec: ProjectileSpec,
    time: number,
    owner: ProjectileOwner = 'enemy',
    pierce = 0,
    visual: ProjectileVisual = {},
  ): void {
    this.attack = spec.attack;
    this.owner = owner;
    this.reflected = false;
    this.pierceLeft = pierce;
    this.homingTurn = 0;
    this.hitStunMs = 0;
    this.crit = false;
    this.hitSet.clear();
    this.expireAt = time + spec.lifeMs;
    const texture = visual.texture && this.scene.textures.exists(visual.texture) ? visual.texture : null;
    this.textured = texture !== null;
    this.rotateToVelocity = this.textured && Boolean(visual.rotate);
    this.anims.stop();
    if (texture) {
      this.setTexture(texture, 0)
        .setOrigin(visual.originX ?? 0.5, visual.originY ?? 0.5)
        .clearTint();
      if (visual.anim && this.scene.anims.exists(visual.anim)) this.play(visual.anim, true);
    } else {
      this.setTexture(placeholderTexture(this.scene, spec.size, spec.size)).setOrigin(0.5, 0.5);
      this.setTint(owner === 'player' ? COLORS.PLAYER_SHOT : COLORS.PROJECTILE);
    }
    // 판정 크기는 외형과 무관하게 spec.size 정사각형, 중심 정렬
    this.body.setSize(spec.size, spec.size, true);
    this.setPosition(x, y);
    this.setActive(true).setVisible(true);
    this.body.enable = true;
    this.body.reset(x, y);
    this.body.setVelocity(dirX * spec.speedPx, dirY * spec.speedPx);
    this.setRotation(this.rotateToVelocity ? Math.atan2(dirY, dirX) : 0);
  }

  /** 적에게 맞았을 때 호출. 이미 맞힌 적이면 false. 관통이 남으면 계속 날아간다 */
  registerHit(target: unknown): boolean {
    if (this.hitSet.has(target)) return false;
    this.hitSet.add(target);
    if (this.pierceLeft > 0) this.pierceLeft -= 1;
    else this.deactivate();
    return true;
  }

  /** 유도: 목표 방향으로 속도 벡터를 최대 homingTurn × dt 만큼 돌린다 */
  steerToward(x: number, y: number, deltaMs: number): void {
    if (this.homingTurn <= 0) return;
    const v = this.body.velocity;
    const speed = v.length();
    if (speed <= 0) return;
    const want = Math.atan2(y - this.y, x - this.x);
    const cur = Math.atan2(v.y, v.x);
    const next = Phaser.Math.Angle.RotateTo(cur, want, this.homingTurn * (deltaMs / 1000));
    this.body.setVelocity(Math.cos(next) * speed, Math.sin(next) * speed);
  }

  reflect(mult: number): void {
    this.reflected = true;
    this.attack = Math.round(this.attack * mult);
    this.body.setVelocity(-this.body.velocity.x, -this.body.velocity.y);
    if (this.textured) this.setRotation(this.rotation + Math.PI);
    else this.setTint(COLORS.PROJECTILE_REFLECTED);
  }

  tick(time: number): void {
    if (!this.active) return;
    if (time >= this.expireAt || !this.body.blocked.none) {
      this.deactivate();
      return;
    }
    if (this.rotateToVelocity) {
      const v = this.body.velocity;
      if (v.lengthSq() > 0) this.setRotation(Math.atan2(v.y, v.x));
    }
  }

  /** 히트스톱: 루프 애니 정지·재개 */
  setAnimPaused(on: boolean): void {
    if (!this.anims.currentAnim) return;
    if (on) this.anims.pause();
    else this.anims.resume();
  }

  deactivate(): void {
    this.setActive(false).setVisible(false);
    this.anims.stop();
    this.body.enable = false;
    this.body.setVelocity(0, 0);
  }
}
