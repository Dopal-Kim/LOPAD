import {
  EVENT_UI,
  SPEECH_UI,
  STORY_UI,
  VOICE_DEFAULT,
  VOICE_LOOK,
  VOICE_UI,
  type VoiceLook,
  type VoiceWeaponId,
} from './themeStory';

/**
 * 61라운드 단계 2 서사 표시 — STORY 자막 읽기·차례·머묾 (순수 계산, Phaser·계약 값 import 없음).
 *
 * 계약 `STORY` 는 `{ kind, text }` 이고, 시스템 C2 가 kind 에 `voice`(원한의 한마디)·`speech`(군주 대사, `speaker`)·
 * `clue`(조사 기록 여러 줄)·`event`(이벤트 도입·결과 문장)를 더한다(텍스트 팩 61 §0.1). 계약 코드에 아직 없을 수 있어
 * 페이로드를 `unknown` 으로 받아 여기서 읽는다 — 필드가 생기면 그대로 쓰고, 없으면 기본값(아래).
 *  - 여러 줄: `lines: string[]` 이 있으면 그것, 없으면 `text` 를 줄바꿈으로 나눈다.
 *  - 화자: `speaker`. 무기: `weapon`(id 'katana'… 또는 이름) — 없으면 HUD 가 스냅샷 무기로 정한다.
 *  - 장면: `scene`(텍스트 팩 B1 장면 키 pickup·firstKill·crisis·bossBefore·bossKill). 제목: `title`(조사 쪽지 제목).
 *  - 머묾: `holdMs`(시스템 힌트 — 위기 한마디 1500 등). 있으면 그것, 없으면 UI 기본(`storyHoldMs`).
 * (시스템 작업 트리 계약: `UiStoryLine.speaker`·`weapon`(id)·`lines`·`holdMs` — 2026-10-05 확인)
 */
export type StoryKindR61 =
  'floor' | 'boss' | 'rest' | 'notice' | 'evolution' | 'death' | 'voice' | 'speech' | 'clue' | 'event';

/** 그리는 자리: caption 하단 가운데 · notice 하단 가운데(바로, 앞지름) · voice 전투 묶음 위 · speech 하단 이름표 + 대사 ·
 * event 하단 종이 띠 · clue 가운데 쪽지 */
export type StoryChannel = 'caption' | 'notice' | 'voice' | 'speech' | 'event' | 'clue';

export interface StoryLineView {
  /** 알 수 없는 kind 는 그대로 두고 caption 으로 그린다 */
  kind: string;
  channel: StoryChannel;
  /** 한 줄로 이은 글 (여러 줄이면 줄바꿈으로) */
  text: string;
  lines: string[];
  speaker: string | null;
  weapon: string | null;
  scene: string | null;
  title: string | null;
  /** 시스템이 준 머묾 ms (없으면 null) */
  holdMs: number | null;
}

const CHANNEL: Record<string, StoryChannel> = {
  notice: 'notice',
  voice: 'voice',
  speech: 'speech',
  event: 'event',
  clue: 'clue',
};

export function storyChannel(kind: string): StoryChannel {
  return CHANNEL[kind] ?? 'caption';
}

function str(v: unknown): string | null {
  return typeof v === 'string' && v.trim().length > 0 ? v.trim() : null;
}

/** STORY 페이로드 읽기. 글이 하나도 없으면 null */
export function readStoryLine(p: unknown): StoryLineView | null {
  if (!p || typeof p !== 'object') return null;
  const o = p as Record<string, unknown>;
  const kind = str(o.kind) ?? 'notice';
  const fromArr = Array.isArray(o.lines) ? o.lines.map(str).filter((l): l is string => l !== null) : [];
  const text = typeof o.text === 'string' ? o.text : '';
  const lines = fromArr.length
    ? fromArr
    : text
        .split(/\r?\n/)
        .map((l) => l.trim())
        .filter(Boolean);
  if (!lines.length) return null;
  return {
    kind,
    channel: storyChannel(kind),
    text: lines.join('\n'),
    lines,
    speaker: str(o.speaker),
    weapon: str(o.weapon) ?? str(o.weaponId),
    scene: str(o.scene),
    title: str(o.title),
    holdMs: typeof o.holdMs === 'number' && Number.isFinite(o.holdMs) && o.holdMs > 0 ? Math.round(o.holdMs) : null,
  };
}

/** 글자 수 (공백 제외 — 읽는 시간) */
export function readLen(text: string): number {
  return text.replace(/\s/g, '').length;
}

function clampMs(base: number, per: number, len: number, min: number, max: number): number {
  return Math.round(Math.max(min, Math.min(max, base + per * len)));
}

/** 머무는 시간 (사라짐 제외) */
export function storyHoldMs(v: Pick<StoryLineView, 'channel' | 'text' | 'scene'> & { holdMs?: number | null }): number {
  if (v.holdMs) return v.holdMs;
  const len = readLen(v.text);
  switch (v.channel) {
    case 'notice':
      return STORY_UI.noticeHoldMs;
    case 'voice':
      if (v.scene === 'crisis') return VOICE_UI.crisisMs;
      return clampMs(VOICE_UI.baseMs, VOICE_UI.perCharMs, len, VOICE_UI.minMs, VOICE_UI.maxMs);
    case 'speech':
      return clampMs(SPEECH_UI.baseMs, SPEECH_UI.perCharMs, len, SPEECH_UI.minMs, SPEECH_UI.maxMs);
    case 'event':
      return clampMs(EVENT_UI.baseMs, EVENT_UI.perCharMs, len, EVENT_UI.minMs, EVENT_UI.maxMs);
    default:
      return STORY_UI.captionHoldMs;
  }
}

/** 무기 이름(스냅샷 `weapon.name`)·id → 목소리 무기 id */
const WEAPON_BY_NAME: Record<string, VoiceWeaponId> = {
  katana: 'katana',
  '사무라이 칼': 'katana',
  칼: 'katana',
  greatsword: 'greatsword',
  대검: 'greatsword',
  dagger: 'dagger',
  단검: 'dagger',
  bow: 'bow',
  활: 'bow',
};

export function voiceWeapon(...candidates: (string | null | undefined)[]): VoiceWeaponId {
  for (const c of candidates) {
    const id = c ? WEAPON_BY_NAME[c.trim()] : undefined;
    if (id) return id;
  }
  return VOICE_DEFAULT;
}

export function voiceLook(id: VoiceWeaponId): VoiceLook {
  return VOICE_LOOK[id];
}

/** 따옴표로 감싼 한마디 (이미 따옴표가 있으면 그대로) */
export function quoteVoice(text: string, open: string = VOICE_UI.open, close: string = VOICE_UI.close): string {
  const t = text.trim();
  if (/^["'“‘「『]/.test(t)) return t;
  return `${open}${t}${close}`;
}

/**
 * 등장 단계별로 보일 글 (type = 한 글자씩, word = 낱말씩). 따옴표는 처음부터 보인다.
 * 그 밖 등장은 처음부터 다 보인다 → [full]
 */
export function revealSteps(full: string, enter: VoiceLook['enter']): string[] {
  if (enter !== 'type' && enter !== 'word') return [full];
  const chars = Array.from(full);
  const head = /^["'“‘「『]/.test(full) ? chars[0] : '';
  const tail = /["'”’」』]$/.test(full) ? chars[chars.length - 1] : '';
  const body = chars.slice(head ? 1 : 0, tail ? -1 : undefined).join('');
  const out: string[] = [];
  if (enter === 'type') {
    const b = Array.from(body);
    for (let i = 1; i <= b.length; i++) out.push(head + b.slice(0, i).join('') + (i === b.length ? tail : ''));
  } else {
    const words = body.split(/(\s+)/);
    let acc = '';
    for (const w of words) {
      acc += w;
      if (w.trim()) out.push(head + acc);
    }
    if (out.length) out[out.length - 1] = head + body + tail;
  }
  return out.length ? out : [full];
}

/** 떨림 오프셋 (정수 px). jitterForMs 0 = 내내. 시각이 같으면 같은 값 (프레임마다 흔들리지 않게 간격으로 끊는다) */
export function voiceJitter(look: VoiceLook, elapsedMs: number): { dx: number; dy: number } {
  if (look.jitterAmp <= 0 || look.jitterEveryMs <= 0) return { dx: 0, dy: 0 };
  if (look.jitterForMs > 0 && elapsedMs >= look.jitterForMs) return { dx: 0, dy: 0 };
  const step = Math.floor(elapsedMs / look.jitterEveryMs);
  // 작은 해시로 -amp..amp (단검은 가로만 — 속삭임, 대검은 세로 위주 — 무게)
  const h = (Math.imul(step + 1, 2654435761) >>> 0) % (look.jitterAmp * 2 + 1);
  const v = h - look.jitterAmp;
  return look.enter === 'drop' ? { dx: 0, dy: v } : { dx: v, dy: 0 };
}

/**
 * 자막 차례에 넣는다. 상한을 넘으면 오래된 기존 자막(caption)부터 버리고, 그래도 넘치면 맨 앞을 버린다.
 * 공지(notice)는 차례에 넣지 않는다(바로 그린다) — 여기 오면 맨 앞에 끼운다.
 */
export function enqueueStory<T extends { channel: StoryChannel }>(
  queue: T[],
  item: T,
  max: number = STORY_UI.queueMax,
): T[] {
  const q = item.channel === 'notice' ? [item, ...queue] : [...queue, item];
  while (q.length > max) {
    const i = q.findIndex((x) => x.channel === 'caption');
    q.splice(i >= 0 ? i : 0, 1);
  }
  return q;
}

/**
 * 차례 맨 앞을 지금 그릴 수 있는가. event(이벤트 결과)는 메뉴가 닫힌 뒤에(텍스트 팩 §0.1 '메뉴를 닫은 뒤 하단 자막').
 * 그 밖은 막힌 동안(탄생 연출·글꼴 전) 모두 기다린다.
 */
export function canShowHead(head: { channel: StoryChannel } | undefined, blocked: boolean, menuOpen: boolean): boolean {
  if (!head || blocked) return false;
  if (head.channel === 'event' && menuOpen) return false;
  return true;
}
