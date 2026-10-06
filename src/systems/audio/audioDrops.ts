/**
 * 61 단계 5 (P13) 음향 요청분 (계약 sound §11 — 음향 제작 대기 id 는 매니페스트 검사 밖, 없으면 다음 후보 또는 무음):
 * 기둥 무너짐 · 보스 포물선 술병 던짐 · 바닥 줍기 물건(전표 떨어짐·줍기 — 무더기 크기별 음정, 소모품 줍기).
 */
import { Events, type BossActionPayload, type PickupPayload } from '../../core/EventBus';
import { t, type AudioTrigger } from './audioTrigger';

const s = (name: string): string => `sfx/${name}`;

export const P13_SFX = {
  pillarCollapse: s('boss1_pillar_collapse'),
  lobBottle: s('boss1_lob_bottle'),
  voucherDrop: s('voucher_drop'),
  voucherPickup: s('voucher_pickup'),
  itemPickup: s('item_pickup'),
  /** 지금 있는 대체음 */
  fallback: {
    pillarCollapse: s('boss1_pillar_crack3'),
    lobBottle: s('boss1_torch_throw'),
    voucherPickup: s('pickup_gold'),
    itemPickup: s('pickup_potion'),
  },
} as const;

/** 전표 무더기 크기 → 재생 속도 (작을수록 높게 · 무더기일수록 낮고 묵직하게) */
export const VOUCHER_RATES: Record<'small' | 'mid' | 'large', number> = { small: 1.12, mid: 1, large: 0.88 };

const voucherRate = (p: PickupPayload): number => VOUCHER_RATES[p.size ?? 'small'];

export const DROP_AUDIO_TRIGGERS: readonly AudioTrigger[] = [
  t<BossActionPayload>({
    event: Events.BOSS_ACTION,
    note: '61 P13 기둥 무너짐(땅에 부딪히는 프레임) → boss1_pillar_collapse (없으면 boss1_pillar_crack3)',
    when: (p) => p.action === 'pillarCollapse',
    sfx: () => [P13_SFX.pillarCollapse, P13_SFX.fallback.pillarCollapse],
  }),
  t<BossActionPayload>({
    event: Events.BOSS_ACTION,
    note: '61 P13 포물선 술병 던짐(병 여럿이면 첫 병만) → boss1_lob_bottle (없으면 boss1_torch_throw) · 착탄은 행상 화염 술병 burst',
    when: (p) => p.action === 'lobThrow' && (p.index ?? 0) === 0,
    sfx: () => [P13_SFX.lobBottle, P13_SFX.fallback.lobBottle],
  }),
  t<PickupPayload>({
    event: Events.PICKUP_LANDED,
    note: '61 P13 전표가 땅에 떨어짐 → voucher_drop (무더기 크기별 음정, 없으면 무음)',
    when: (p) => p.kind === 'voucher',
    sfx: () => [P13_SFX.voucherDrop],
    rate: voucherRate,
  }),
  t<PickupPayload>({
    event: Events.PICKUP_COLLECTED,
    note: '61 P13 전표 줍기 → voucher_pickup (무더기 크기별 음정, 없으면 pickup_gold)',
    when: (p) => p.kind === 'voucher',
    sfx: () => [P13_SFX.voucherPickup, P13_SFX.fallback.voucherPickup],
    rate: voucherRate,
  }),
  t<PickupPayload>({
    event: Events.PICKUP_COLLECTED,
    note: '61 P13 소모품 줍기 → item_pickup (없으면 pickup_potion) · 물약은 기존 ITEM_PICKED pickup_potion',
    when: (p) => p.kind === 'consumable',
    sfx: () => [P13_SFX.itemPickup, P13_SFX.fallback.itemPickup],
  }),
];
