import { describe, expect, it } from 'vitest';
import {
  canShowHead,
  enqueueStory,
  quoteVoice,
  readStoryLine,
  revealSteps,
  storyChannel,
  storyHoldMs,
  voiceJitter,
  voiceLook,
  voiceWeapon,
} from './storyView';
import { STORY_UI, VOICE_UI } from './themeStory';

describe('readStoryLine', () => {
  it('기존 자막과 새 4종을 읽는다', () => {
    expect(readStoryLine({ kind: 'boss', text: '만취가 일어난다' })).toMatchObject({
      channel: 'caption',
      lines: ['만취가 일어난다'],
    });
    expect(readStoryLine({ kind: 'speech', text: '첫 잔은 외상이다.', speaker: '만취' })).toMatchObject({
      channel: 'speech',
      speaker: '만취',
    });
    expect(readStoryLine({ kind: 'voice', text: '하나.', weapon: 'katana', scene: 'bossKill' })).toMatchObject({
      channel: 'voice',
      weapon: 'katana',
      scene: 'bossKill',
    });
  });
  it('여러 줄: lines 가 있으면 그것, 없으면 줄바꿈으로 나눈다', () => {
    expect(readStoryLine({ kind: 'clue', text: '가', lines: ['하나', ' ', '둘'] })?.lines).toEqual(['하나', '둘']);
    expect(readStoryLine({ kind: 'clue', text: '하나\n\n 둘 ' })?.lines).toEqual(['하나', '둘']);
  });
  it('글이 없거나 잘못된 페이로드는 null, 알 수 없는 kind 는 caption', () => {
    expect(readStoryLine(null)).toBeNull();
    expect(readStoryLine({ kind: 'speech', text: '  ' })).toBeNull();
    expect(readStoryLine({ kind: 'whisper', text: '가' })?.channel).toBe('caption');
    expect(storyChannel('event')).toBe('event');
  });
});

describe('storyHoldMs', () => {
  it('공지·기존 자막은 예전 값, 위기 한마디는 짧게', () => {
    expect(storyHoldMs({ channel: 'notice', text: '가나다', scene: null })).toBe(STORY_UI.noticeHoldMs);
    expect(storyHoldMs({ channel: 'caption', text: '가나다', scene: null })).toBe(STORY_UI.captionHoldMs);
    expect(storyHoldMs({ channel: 'voice', text: '물러서지 마라. 뒤는 벽 밖이다.', scene: 'crisis' })).toBe(
      VOICE_UI.crisisMs,
    );
  });
  it('시스템 힌트 holdMs 가 먼저', () => {
    expect(readStoryLine({ kind: 'voice', text: '가', holdMs: 1500 })?.holdMs).toBe(1500);
    expect(readStoryLine({ kind: 'voice', text: '가', holdMs: -3 })?.holdMs).toBeNull();
    expect(storyHoldMs({ channel: 'speech', text: '가', scene: null, holdMs: 999 })).toBe(999);
  });
  it('길수록 오래, 하한·상한 안', () => {
    const short = storyHoldMs({ channel: 'speech', text: '가', scene: null });
    const long = storyHoldMs({ channel: 'speech', text: '가'.repeat(200), scene: null });
    expect(short).toBeLessThan(long);
    expect(storyHoldMs({ channel: 'voice', text: '가'.repeat(200), scene: null })).toBe(VOICE_UI.maxMs);
  });
});

describe('voice', () => {
  it('무기 id·이름으로 고르고, 모르면 기본', () => {
    expect(voiceWeapon(null, '대검')).toBe('greatsword');
    expect(voiceWeapon('bow', '대검')).toBe('bow');
    expect(voiceWeapon('???')).toBe('katana');
    expect(voiceLook('dagger').style).toBe('voice_dagger');
  });
  it('따옴표는 한 번만', () => {
    expect(quoteVoice(' 쉿. ')).toBe('“쉿.”');
    expect(quoteVoice('“쉿.”')).toBe('“쉿.”');
  });
  it('한 글자씩·낱말씩 등장 (따옴표는 처음부터, 끝 따옴표는 마지막에)', () => {
    expect(revealSteps('“가나”', 'type')).toEqual(['“가', '“가나”']);
    expect(revealSteps('“하나요. 셌어요.”', 'word')).toEqual(['“하나요.', '“하나요. 셌어요.”']);
    expect(revealSteps('“가나”', 'slide')).toEqual(['“가나”']);
  });
  it('떨림: 칼·활 없음, 대검은 처음만 세로, 단검은 내내 가로 (정수)', () => {
    expect(voiceJitter(voiceLook('katana'), 100)).toEqual({ dx: 0, dy: 0 });
    expect(voiceJitter(voiceLook('greatsword'), 5000)).toEqual({ dx: 0, dy: 0 });
    const g = voiceJitter(voiceLook('greatsword'), 100);
    expect(g.dx).toBe(0);
    const d = [0, 90, 180, 270, 360].map((t) => voiceJitter(voiceLook('dagger'), 9000 + t));
    expect(d.every((j) => j.dy === 0 && Number.isInteger(j.dx) && Math.abs(j.dx) <= 1)).toBe(true);
  });
});

describe('enqueueStory · canShowHead', () => {
  it('공지는 맨 앞, 상한을 넘으면 기존 자막부터 버린다', () => {
    let q: { channel: 'caption' | 'notice' | 'voice' | 'speech' | 'event' | 'clue'; id: number }[] = [];
    q = enqueueStory(q, { channel: 'caption', id: 1 }, 3);
    q = enqueueStory(q, { channel: 'speech', id: 2 }, 3);
    q = enqueueStory(q, { channel: 'voice', id: 3 }, 3);
    q = enqueueStory(q, { channel: 'notice', id: 4 }, 3);
    expect(q.map((x) => x.id)).toEqual([4, 2, 3]);
  });
  it('이벤트 문장은 메뉴가 닫힌 뒤', () => {
    expect(canShowHead({ channel: 'event' }, false, true)).toBe(false);
    expect(canShowHead({ channel: 'event' }, false, false)).toBe(true);
    expect(canShowHead({ channel: 'speech' }, false, true)).toBe(true);
    expect(canShowHead({ channel: 'speech' }, true, false)).toBe(false);
    expect(canShowHead(undefined, false, false)).toBe(false);
  });
});
