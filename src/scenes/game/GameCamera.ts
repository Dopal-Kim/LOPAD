/**
 * 게임 월드 카메라: 플레이어 부드러운 추종(32라운드) + 흔들림(35라운드).
 * 목표만 영역으로 클램프하므로 방 전환 시 미끄러진다. 확대 배율(월드 → 화면)만큼 보이는 월드가 작다.
 */
import Phaser from 'phaser';
import { BORDER, CAMERA } from '../../core/Constants';
import { logicalZoomOf, worldZoom } from '../../systems/display';
import type { Game } from '../Game';

export class GameCamera {
  /** 카메라 중심 (반올림 전). 스크롤은 매 프레임 여기서 반올림해 적용 */
  private readonly center = new Phaser.Math.Vector2();
  /** 53라운드 Q8: 북쪽 끝에서 카메라를 위로 올린 양 (월드, 보간 중) */
  private lookUp = 0;
  /**
   * 61라운드 보스 등장·처치 연출: 주인공 대신 이 점을 본다 (rateMs = 약 95% 다가가는 시간). 풀면 returnMs 동안 데드존 없이
   * 주인공 쪽으로 돌아간다 (`setFocus(null, ms)`)
   */
  private focus: { x: number; y: number; rateMs: number } | null = null;
  private returnUntil = 0;
  private returnMs = 0;
  /** P19 E (계약 free-combat §4): 지금 논리 배율 (목표로 옮겨 가는 중) · 마지막으로 카메라에 넣은 값 · 전투 중(살아 있는 적 ≥ 1) */
  private zoom: number = CAMERA.ZOOM;
  private appliedZoom = 0;
  private combat = false;

  constructor(private readonly g: Game) {}

  setFocus(at: { x: number; y: number } | null, ms: number): void {
    if (at) {
      this.focus = { x: at.x, y: at.y, rateMs: Math.max(1, ms) };
      return;
    }
    if (!this.focus) return;
    this.focus = null;
    this.returnMs = Math.max(1, ms);
    this.returnUntil = this.g.time.now + ms;
  }

  get focusing(): boolean {
    return this.focus !== null;
  }

  /** P19 E: 탐색 1.75 · 전투 중 1.6 · 보스 1.5 */
  private zoomTarget(): number {
    if (this.g.nodeKind === 'boss') return CAMERA.ZOOM_BOSS;
    return this.combat ? CAMERA.ZOOM_COMBAT : CAMERA.ZOOM;
  }

  /**
   * P19 E: 배율을 목표로 (탐색 ↔ 전투 폭을 ZOOM_EASE_MS 에 걸쳐 같은 빠르기로). force(진입·연출) 는 값만 맞추고 카메라는 그대로 —
   * 탄생 연출이 자기 배율을 넣는 중이라서. 바뀔 때만 넣는다 (보스 처치 확대 tween 을 덮지 않게)
   */
  private updateZoom(force: boolean, deltaMs: number): void {
    this.combat = this.g.mobs.countActive(true) > 0;
    const want = this.zoomTarget();
    if (force) {
      this.zoom = want;
      return;
    }
    const step = (Math.abs(CAMERA.ZOOM - CAMERA.ZOOM_COMBAT) * deltaMs) / CAMERA.ZOOM_EASE_MS;
    this.zoom += Math.sign(want - this.zoom) * Math.min(Math.abs(want - this.zoom), step);
    const left = Math.max(0, this.punchUntil - this.g.time.now) / this.punchMs;
    const z = this.zoom * (1 + this.punchAmt * left);
    if (Math.abs(z - this.appliedZoom) < 1e-4) return;
    this.g.cameras.main.setZoom(worldZoom(z));
    this.appliedZoom = z;
  }

  /**
   * P19: 짧은 줌 펀치 (대검 판정 순간 등 — S1 이 부른다). amount = 배율 가산 비율(0.04 = 4% 확대), ms 동안 선형으로 0 으로.
   * 신호(`toUi().zoom`)는 기본 배율 그대로 (화면 좌표는 cam.zoom 을 쓰는 worldToLogicalScreen 이라 펀치도 반영된다)
   */
  punch(amount: number, ms: number): void {
    this.punchAmt = amount;
    this.punchMs = Math.max(1, ms);
    this.punchUntil = this.g.time.now + this.punchMs;
  }

  private punchAmt = 0;
  private punchMs = 1;
  private punchUntil = 0;

  /** 지금 논리 배율 (연출 확대의 기준) */
  get logicalZoom(): number {
    return this.zoom;
  }

  /**
   * 계약 free-combat §4 `UiSnapshot.camera` — zoom = 논리 배율, view = 보이는 월드 사각형 (worldView 와 같은 값을 스크롤·배율에서
   * 바로 계산 — Phaser worldView 는 그리기 전에야 갱신돼 한 프레임 늦다)
   */
  toUi(): { zoom: number; combat: boolean; view: { x: number; y: number; w: number; h: number } } {
    const cam = this.g.cameras.main;
    const z = cam.zoom || 1;
    const w = cam.width / z;
    const h = cam.height / z;
    const r = (v: number) => Math.round(v * 10) / 10;
    return {
      zoom: +this.zoom.toFixed(3),
      combat: this.combat,
      view: { x: r(cam.scrollX + (cam.width - w) / 2), y: r(cam.scrollY + (cam.height - h) / 2), w: r(w), h: r(h) },
    };
  }

  update(force: boolean, deltaMs = 0): void {
    const g = this.g;
    this.updateZoom(force, deltaMs);
    const cam = g.cameras.main;
    // 48라운드 Q1: 확대 배율만큼 보이는 월드가 작다 → 클램프는 보이는 반폭, 스크롤은 (중심 - 캔버스 반폭)
    // 52라운드: zoom = 실제 배율(캔버스 px), lz = 논리 배율 (데드존·스냅·흔들림 px 는 논리 화면 px)
    const zoom = cam.zoom || 1;
    const lz = logicalZoomOf(cam);
    const region = g.world.cameraRegion(g.player.x, g.player.y);
    const halfW = cam.width / (2 * zoom);
    const halfH = cam.height / (2 * zoom);
    const dzX = CAMERA.DEADZONE_X / lz;
    const dzY = CAMERA.DEADZONE_Y / lz;
    const px = this.focus?.x ?? g.player.x;
    const py = this.focus?.y ?? g.player.y;
    let tx = px;
    let ty = py;
    // 61라운드 연출 초점·복귀: 데드존 없이, 지수 접근 (rateMs 에 약 95%)
    const steer = force ? 0 : (this.focus?.rateMs ?? (g.time.now < this.returnUntil ? this.returnMs : 0));
    if (!force && steer <= 0) {
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
    } else if (steer > 0) {
      const k = 1 - Math.exp((-3 * deltaMs) / steer);
      this.center.x += (tx - this.center.x) * k;
      this.center.y += (ty - this.center.y) * k;
    } else {
      // 60fps 기준 lerp 비율을 프레임 시간에 맞춰 보정
      const t = 1 - Math.pow(1 - CAMERA.FOLLOW_LERP, deltaMs / (1000 / 60));
      this.center.x += (tx - this.center.x) * t;
      this.center.y += (ty - this.center.y) * t;
      const snap = CAMERA.SNAP_PX / lz;
      if (Math.abs(tx - this.center.x) < snap) this.center.x = tx;
      if (Math.abs(ty - this.center.y) < snap) this.center.y = ty;
    }
    // 53라운드 Q8: 외벽 테두리 지역에서 북쪽 끝에 다가가면 카메라를 위로 (집 위층·지붕이 보이게), 부드럽게
    const look = g.border?.lookUpAt(py) ?? 0;
    if (force) this.lookUp = look;
    else this.lookUp += (look - this.lookUp) * (1 - Math.pow(1 - BORDER.LOOKUP_LERP, deltaMs / (1000 / 60)));
    const viewY =
      this.lookUp > 0 ? clampCenter(this.center.y - this.lookUp, region.top, region.bottom, halfH) : this.center.y;
    // 흔들림(35라운드): 추종 보간·반올림이 끝난 스크롤에 오프셋만 더한다. 진폭은 논리 화면 px → 월드 px 로 ÷lz (체감 유지).
    // 스크롤은 실제 캔버스 px 단위로 반올림 (52라운드: 1920×1080 이라 이전보다 2배 촘촘)
    const sh = g.shake.sample(g.time.now);
    const snapTo = (v: number) => Math.round(v * zoom) / zoom;
    cam.setScroll(snapTo(this.center.x - cam.width / 2) + sh.x / lz, snapTo(viewY - cam.height / 2) + sh.y / lz);
  }

  /** 디버그: 북쪽 치우침 (월드) */
  get lookUpPx(): number {
    return this.lookUp;
  }
}

/** 화면 절반(half)을 고려해 중심 좌표를 [lo, hi] 영역 안으로. 영역이 화면보다 작으면 가운데 */
function clampCenter(center: number, lo: number, hi: number, half: number): number {
  if (hi - lo <= half * 2) return (lo + hi) / 2;
  return Phaser.Math.Clamp(center, lo + half, hi - half);
}
