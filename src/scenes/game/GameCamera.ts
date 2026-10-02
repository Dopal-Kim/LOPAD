/**
 * 게임 월드 카메라: 플레이어 부드러운 추종(32라운드) + 흔들림(35라운드).
 * 목표만 영역으로 클램프하므로 방 전환 시 미끄러진다. 확대 배율(월드 → 화면)만큼 보이는 월드가 작다.
 */
import Phaser from 'phaser';
import { CAMERA } from '../../core/Constants';
import type { Game } from '../Game';

export class GameCamera {
  /** 카메라 중심 (반올림 전). 스크롤은 매 프레임 여기서 반올림해 적용 */
  private readonly center = new Phaser.Math.Vector2();

  constructor(private readonly g: Game) {}

  update(force: boolean, deltaMs = 0): void {
    const g = this.g;
    const cam = g.cameras.main;
    // 48라운드 Q1: 확대 배율만큼 보이는 월드가 작다 → 클램프는 보이는 반폭, 스크롤은 (중심 - 캔버스 반폭)
    const zoom = cam.zoom || 1;
    const region = g.world.cameraRegion(g.player.x, g.player.y);
    const halfW = cam.width / (2 * zoom);
    const halfH = cam.height / (2 * zoom);
    const dzX = CAMERA.DEADZONE_X / zoom;
    const dzY = CAMERA.DEADZONE_Y / zoom;
    const px = g.player.x;
    const py = g.player.y;
    let tx = px;
    let ty = py;
    if (!force) {
      // 데드존: 중심에서 이만큼 벗어나야 따라간다 (화면 px 기준)
      const cx = this.center.x;
      const cy = this.center.y;
      tx = px > cx + dzX ? px - dzX : px < cx - dzX ? px + dzX : cx;
      ty = py > cy + dzY ? py - dzY : py < cy - dzY ? py + dzY : cy;
    }
    tx = clampCenter(tx, region.left, region.right, halfW);
    ty = clampCenter(ty, region.top, region.bottom, halfH);
    if (force) {
      this.center.set(tx, ty);
    } else {
      // 60fps 기준 lerp 비율을 프레임 시간에 맞춰 보정
      const t = 1 - Math.pow(1 - CAMERA.FOLLOW_LERP, deltaMs / (1000 / 60));
      this.center.x += (tx - this.center.x) * t;
      this.center.y += (ty - this.center.y) * t;
      const snap = CAMERA.SNAP_PX / zoom;
      if (Math.abs(tx - this.center.x) < snap) this.center.x = tx;
      if (Math.abs(ty - this.center.y) < snap) this.center.y = ty;
    }
    // 흔들림(35라운드): 추종 보간·반올림이 끝난 스크롤에 오프셋만 더한다. 진폭은 화면 px → 월드 px 로 ÷zoom (체감 유지)
    const sh = g.shake.sample(g.time.now);
    const snapTo = (v: number) => Math.round(v * zoom) / zoom;
    cam.setScroll(
      snapTo(this.center.x - cam.width / 2) + sh.x / zoom,
      snapTo(this.center.y - cam.height / 2) + sh.y / zoom,
    );
  }
}

/** 화면 절반(half)을 고려해 중심 좌표를 [lo, hi] 영역 안으로. 영역이 화면보다 작으면 가운데 */
function clampCenter(center: number, lo: number, hi: number, half: number): number {
  if (hi - lo <= half * 2) return (lo + hi) / 2;
  return Phaser.Math.Clamp(center, lo + half, hi - half);
}
