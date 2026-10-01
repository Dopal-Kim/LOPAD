import { describe, expect, it } from 'vitest';
import {
  FX_ACTION,
  animDurationMs,
  animKey,
  arrowFxId,
  facingOf,
  frameAt,
  frameDurations,
  frameIndices,
  fxSheetIds,
  sheetJsonPath,
  slashFxId,
  wantedSheets,
  type SheetJson,
} from './spriteDefs';

const walk: SheetJson = {
  image: 'player_walk.png',
  action: 'walk',
  frameWidth: 16,
  frameHeight: 24,
  frames: 8,
  directions: ['down', 'up', 'left', 'right'],
  fps: 9,
  frameDurationsMs: [110, 110, 110, 110, 110, 110, 110, 110],
  loop: true,
  pivot: { x: 8, y: 23 },
};

describe('sprite defs (계약 art-assets.md §1)', () => {
  it('키 규칙 <이름>_<동작>_<방향> 과 변형 접미', () => {
    expect(animKey('player', 'walk', 'down')).toBe('player_walk_down');
    expect(animKey('dummy', 'idle', 'left', '@f2')).toBe('dummy_idle_left@f2');
    expect(sheetJsonPath({ category: 'enemies', name: 'archer', action: 'hurt' })).toBe(
      'sprites/enemies/archer_hurt.json',
    );
  });

  it('프레임 번호 = row * frames + column (행 = directions 순서)', () => {
    expect(frameIndices(walk, 'down')).toEqual([0, 1, 2, 3, 4, 5, 6, 7]);
    expect(frameIndices(walk, 'left')[0]).toBe(16);
    expect(frameIndices({ ...walk, directions: ['right', 'left'] }, 'left')[0]).toBe(8);
  });

  it('frameDurationsMs 가 맞으면 그대로, 아니면 fps 균등', () => {
    expect(animDurationMs(walk)).toBe(880);
    const noDur = { ...walk, frameDurationsMs: undefined, fps: 10, frames: 4 };
    expect(frameDurations(noDur)).toEqual([100, 100, 100, 100]);
    expect(animDurationMs({ ...walk, frameDurationsMs: [1, 2] })).toBeCloseTo((8 * 1000) / 9, 3);
  });

  it('로드 대상: 주인공 6동작 + 적·보스 5동작 + 무기 attack + 이펙트', () => {
    const list = wantedSheets(['dummy', 'archer'], [], ['katana'], ['katana_slash', 'iai']);
    expect(list.filter((r) => r.name === 'player')).toHaveLength(6);
    expect(list.filter((r) => r.category === 'enemies')).toHaveLength(10);
    expect(list.filter((r) => r.category === 'weapons')).toEqual([
      { category: 'weapons', name: 'katana', action: 'attack' },
    ]);
    expect(list.filter((r) => r.category === 'fx').map((r) => r.action)).toEqual([FX_ACTION, FX_ACTION]);
    expect(sheetJsonPath({ category: 'weapons', name: 'bow', action: 'attack' })).toBe(
      'sprites/weapons/bow_attack.json',
    );
    expect(sheetJsonPath({ category: 'fx', name: 'iai', action: FX_ACTION })).toBe('sprites/fx/iai.json');
  });

  it('이펙트 목록 (계약 §3·§3.1): 근접 slash, 원거리 arrow·arrow_aimed, 1차 진화 id', () => {
    const ids = fxSheetIds({
      katana: { kind: 'melee', personality: { branches: [{ id: 'iai' }, { id: 'batto' }] } },
      bow: { kind: 'ranged', personality: { branches: [{ id: 'pierce' }, { id: 'scatter' }] } },
    });
    expect(ids).toEqual(['katana_slash', 'iai', 'batto', 'bow_arrow', 'bow_arrow_aimed', 'pierce', 'scatter']);
    expect(slashFxId('dagger')).toBe('dagger_slash');
    expect(arrowFxId('bow', true)).toBe('bow_arrow_aimed');
  });

  it('무기 오버레이: 같은 열의 프레임 번호, any 시트는 0행', () => {
    const weapon = { ...walk, frames: 4, directions: ['down', 'up', 'left', 'right'] };
    expect(frameAt(weapon, 'left', 1)).toBe(9);
    expect(frameAt(weapon, 'right', 9)).toBe(15);
    expect(frameAt({ ...weapon, directions: ['any'] }, 'up', 2)).toBe(2);
    expect(frameIndices({ ...weapon, directions: ['any'] }, 'right')).toEqual([0, 1, 2, 3]);
  });

  it('지배 축 방향', () => {
    expect(facingOf(1, 0.5, 'down')).toBe('right');
    expect(facingOf(-0.2, -1, 'down')).toBe('up');
    expect(facingOf(0, 0, 'left')).toBe('left');
  });
});

describe('sprite defs: 프레임 시작 시각·국면 애니 키 (결정 로그 J)', () => {
  it('frameStarts 는 누적 시작 ms, 배속으로 나눈다', async () => {
    const { frameStarts, phaseAnimKey } = await import('./spriteDefs');
    const def = {
      image: 'x.png',
      action: 'attack',
      frameWidth: 16,
      frameHeight: 24,
      frames: 4,
      directions: ['down', 'up', 'left', 'right'],
      fps: 11,
      frameDurationsMs: [100, 50, 110, 110],
      loop: false,
      pivot: { x: 8, y: 23 },
    };
    expect(frameStarts(def)).toEqual([0, 100, 150, 260]);
    expect(frameStarts(def, 2)).toEqual([0, 50, 75, 130]);
    expect(phaseAnimKey('stage1_attack_right@f2', [1, 2])).toBe('stage1_attack_right@f2#p1-2');
  });
});
