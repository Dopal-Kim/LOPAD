import { describe, expect, it } from 'vitest';
import { NoticeEcho, noticeHead, setEchoHeads, traitEchoHeads } from './noticeEcho';

describe('NoticeEcho (62 루프 3 UI H · P1-N2 알림 한 번만)', () => {
  it('개성 이름으로 시작하는 공지는 메아리', () => {
    const e = new NoticeEcho();
    e.remember(traitEchoHeads('발도풍'), 0);
    expect(e.echoes('발도풍 — 검기를 가득 채운 발도는 앞으로 검풍이 날아간다', 100)).toBe(true);
    expect(e.echoes('문이 닫혔다.', 100)).toBe(false);
  });
  it('세트 단계 공지(숫자 문장)는 메아리', () => {
    const e = new NoticeEcho();
    e.remember(setEchoHeads({ name: '중량', stage: 2, effectName: '중량 2' }), 0);
    expect(e.echoes('중량 2 — 강공 피해 +20%', 500)).toBe(true);
  });
  it('시간이 지나면 잊는다', () => {
    const e = new NoticeEcho(1000);
    e.remember(['발도풍'], 0);
    expect(e.echoes('발도풍 — …', 1500)).toBe(false);
  });
  it('머리말은 공백·문장부호를 뺀다', () => {
    expect(noticeHead('중량 2 — 강공 피해')).toBe('중량2');
    expect(noticeHead('그냥 한 줄.')).toBe('그냥한줄');
  });
});
