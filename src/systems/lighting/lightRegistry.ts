/**
 * 50라운드 광원 목록 (씬마다 하나). 소품·구조물·이펙트·세트 그림이 광원을 등록하고 조명 렌더러(Lighting)가 매 프레임 읽는다.
 * 그림 쪽이 조명 시스템을 직접 참조하지 않도록 씬 키로 찾는다 (조명이 꺼진 씬에서도 등록은 무해하다).
 * 계약 art §9: JSON `light` 를 가진 소품·구조물·이펙트는 광원 — 없으면 data/lighting.json fallback(시트 id) 이 임시로 대신한다.
 */
import { LIGHTING } from '../../data';
import type { LightDefData } from '../../data/types';
import type { LightSpec } from '../sprites/spriteDefs';
import { hexColor } from './lightMath';

/** 위치를 따라갈 대상 (스프라이트 등) */
export interface LightAnchor {
  x: number;
  y: number;
  active?: boolean;
  visible?: boolean;
}

export interface LightSource {
  readonly id: number;
  x: number;
  y: number;
  anchor: LightAnchor | null;
  offsetY: number;
  /** 대상에서 오른쪽으로 (월드 px) */
  offsetX: number;
  color: number;
  radius: number;
  intensity: number;
  flicker: number;
  /** 이 시각(씬 ms)이 지나면 사라진다 (Infinity = 직접 지울 때까지) */
  until: number;
  /** 시작 시각 (순간광 감쇠용) */
  bornAt: number;
  /** 순간광: 수명 동안 세기가 줄어든다 */
  fade: boolean;
  /** 꺼둠 (상태에 따라 켜고 끄는 광원 — 모닥불 불씨 등) */
  enabled: boolean;
}

const DEFAULT_COLOR = 0xffe6c2;

export class LightRegistry {
  private readonly list = new Map<number, LightSource>();
  private serial = 1;

  /** 광원 추가. anchor 가 있으면 매 프레임 그 위치(+offsetY 위로)를 따른다. anchor 가 비활성이 되면 자동으로 지운다 */
  add(
    def: LightDefData | LightSpec,
    at: {
      x: number;
      y: number;
      anchor?: LightAnchor | null;
      until?: number;
      now?: number;
      fade?: boolean;
      /** 대상 기준 광원 위치 (월드 px, 있으면 def.offsetY 대신) */
      dx?: number;
      dy?: number;
    },
  ): LightSource {
    const src: LightSource = {
      id: this.serial++,
      x: at.x,
      y: at.y,
      anchor: at.anchor ?? null,
      offsetY: at.dy !== undefined ? -at.dy : (def.offsetY ?? 0),
      offsetX: at.dx ?? 0,
      color: hexColor(def.color, DEFAULT_COLOR),
      radius: def.radius,
      intensity: def.intensity ?? 1,
      flicker: typeof def.flicker === 'number' ? def.flicker : (def.flicker?.amp ?? 0),
      until: at.until ?? Infinity,
      bornAt: at.now ?? 0,
      fade: Boolean(at.fade),
      enabled: true,
    };
    this.list.set(src.id, src);
    return src;
  }

  remove(src: LightSource | null | undefined): void {
    if (src) this.list.delete(src.id);
  }

  /** 살아 있는 광원 (만료·대상 사라짐은 지우고, 위치는 대상으로 갱신) */
  live(now: number): LightSource[] {
    const out: LightSource[] = [];
    for (const s of this.list.values()) {
      if (now >= s.until || (s.anchor && s.anchor.active === false)) {
        this.list.delete(s.id);
        continue;
      }
      if (s.anchor) {
        s.x = s.anchor.x + s.offsetX;
        s.y = s.anchor.y - s.offsetY;
      }
      if (s.enabled && s.anchor?.visible !== false) out.push(s);
    }
    return out;
  }

  get size(): number {
    return this.list.size;
  }

  clear(): void {
    this.list.clear();
  }
}

const registries = new WeakMap<object, LightRegistry>();

/** 씬의 광원 목록 (없으면 만든다) */
export function lightRegistryOf(scene: object): LightRegistry {
  let r = registries.get(scene);
  if (!r) {
    r = new LightRegistry();
    registries.set(scene, r);
  }
  return r;
}

/** 씬 정리 (shutdown) */
export function dropLightRegistry(scene: object): void {
  registries.get(scene)?.clear();
  registries.delete(scene);
}

/**
 * 시트의 광원: 시트 JSON `light`(월드 단위로 바뀐 것) → data/lighting.json fallback[시트 id] → 무기 이펙트면 weaponFx → 없음.
 * `sheetId` 는 시트 이름(파일 이름, 예: bonfire·fire_pool·set_outer_lamppost)
 */
export function lightFor(
  sheetId: string,
  def: { light?: LightSpec; weapon?: string } | null | undefined,
): LightDefData | LightSpec | null {
  if (def?.light && def.light.radius > 0) return def.light;
  const fb = LIGHTING.fallback[sheetId];
  if (fb && !sheetId.startsWith('_')) return fb;
  if (def?.weapon) return LIGHTING.weaponFx;
  return null;
}
