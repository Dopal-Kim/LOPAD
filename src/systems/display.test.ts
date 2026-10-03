import { describe, expect, it } from 'vitest';
import type Phaser from 'phaser';
import {
  CANVAS_H,
  CANVAS_W,
  RES,
  displayZoom,
  makeLogicalCamera,
  screenFixed,
  toLogical,
  worldToLogicalScreen,
  worldZoom,
} from './display';

type Cam = Phaser.Cameras.Scene2D.Camera;
/** 화면 = (월드 - 스크롤×sf - 원점) × zoom + 원점 + x (Phaser 카메라 행렬과 같은 식) */
function project(
  c: {
    x: number;
    y: number;
    width: number;
    height: number;
    originX: number;
    originY: number;
    zoom: number;
    scrollX: number;
    scrollY: number;
  },
  wx: number,
  wy: number,
  sf = 1,
) {
  const ox = c.width * c.originX;
  const oy = c.height * c.originY;
  return { x: (wx - c.scrollX * sf - ox) * c.zoom + ox + c.x, y: (wy - c.scrollY * sf - oy) * c.zoom + oy + c.y };
}

describe('52라운드 내부 렌더 1920×1080 (display)', () => {
  it('캔버스 = 논리 960×540 × 2, 표시 배율은 52라운드 전과 같은 CSS 크기', () => {
    expect(RES).toBe(2);
    expect([CANVAS_W, CANVAS_H]).toEqual([1920, 1080]);
    expect(displayZoom(1920, 1080)).toBe(1); // 이전 960 × 2
    expect(displayZoom(1280, 720)).toBe(0.5); // 이전 960 × 1
    expect(displayZoom(960, 540)).toBe(0.5);
    expect(displayZoom(3840, 2160)).toBe(2);
    expect(displayZoom(800, 450)).toBe(0.5); // 최소 1배(논리)
    expect(worldZoom(2)).toBe(4);
    expect(toLogical(1920)).toBe(960);
  });

  it('월드 카메라(원점 가운데)의 scrollFactor 0 개체: 논리 (4,4) 에 논리 크기', () => {
    const cam = {
      x: 0,
      y: 0,
      width: CANVAS_W,
      height: CANVAS_H,
      originX: 0.5,
      originY: 0.5,
      zoom: worldZoom(2),
      scrollX: 123,
      scrollY: 45,
    };
    const at = screenFixed(cam as unknown as Cam, 4, 4);
    const s = project(cam, at.x, at.y, 0);
    expect(s.x / RES).toBeCloseTo(4);
    expect(s.y / RES).toBeCloseTo(4);
    expect(at.scale * cam.zoom).toBe(RES); // 글자 1px = 논리 1px
  });

  it('월드 → 논리 화면 좌표 (UiInteractable.screen): 카메라 중심 = (480, 270)', () => {
    const cam = {
      x: 0,
      y: 0,
      width: CANVAS_W,
      height: CANVAS_H,
      originX: 0.5,
      originY: 0.5,
      zoom: worldZoom(2),
      scrollX: 100,
      scrollY: 50,
    };
    const mid = { x: cam.scrollX + cam.width / 2, y: cam.scrollY + cam.height / 2 };
    const p = worldToLogicalScreen(cam as unknown as Cam, mid.x, mid.y);
    expect(p).toEqual({ x: 480, y: 270 });
    const q = worldToLogicalScreen(cam as unknown as Cam, mid.x + 10, mid.y);
    expect(q.x).toBe(480 + 10 * 2); // 월드 1 = 논리 2px
  });

  it('논리 카메라: zoom 2 · 원점 (0,0) → 씬 좌표 = 논리 화면 좌표, worldView 를 원점 기준으로 바로잡는다', () => {
    const calls: string[] = [];
    const cam = {
      x: 0,
      y: 0,
      width: CANVAS_W,
      height: CANVAS_H,
      originX: 0.5,
      originY: 0.5,
      zoom: 1,
      zoomX: 1,
      zoomY: 1,
      scrollX: 0,
      scrollY: 0,
      worldView: {
        setTo(x: number, y: number, w: number, h: number) {
          this.v = [x, y, w, h];
        },
        v: [] as number[],
      },
      midPoint: {
        set(x: number, y: number) {
          this.v = [x, y];
        },
        v: [] as number[],
      },
      setOrigin(x: number, y: number) {
        this.originX = x;
        this.originY = y;
        return this;
      },
      setZoom(z: number) {
        this.zoom = z;
        this.zoomX = z;
        this.zoomY = z;
        return this;
      },
      setScroll(x: number, y: number) {
        this.scrollX = x;
        this.scrollY = y;
        return this;
      },
      setRoundPixels() {
        return this;
      },
      preRender() {
        calls.push('base');
      },
    };
    makeLogicalCamera(cam as unknown as Cam);
    makeLogicalCamera(cam as unknown as Cam); // 두 번 걸어도 한 번만 감싼다
    expect(cam.zoom).toBe(2);
    for (const [x, y] of [
      [0, 0],
      [480, 270],
      [960, 540],
    ]) {
      for (const sf of [0, 1]) {
        const s = project(cam, x, y, sf);
        expect([s.x / RES, s.y / RES]).toEqual([x, y]);
      }
    }
    cam.preRender();
    expect(calls).toEqual(['base']);
    expect(cam.worldView.v).toEqual([0, 0, 960, 540]);
    expect(cam.midPoint.v).toEqual([480, 270]);
  });
});
