import type Phaser from 'phaser';
import { bannerCard, type AlertSpec } from './HudAlerts';
import { r53Text } from './text';
import { ALERT_UI as A } from './themeAlerts';

/**
 * 62 P0-6 방 시작 카드 하나: '주의 · 적이 다가온다'(ENEMY_INCOMING)와 '문이 닫혔다'(시스템 공지)를 한 장으로 합친다.
 * 둘 중 먼저 온 것이 카드를 세우고, 뒤에 온 것은 같은 key 로 합쳐져 줄이 하나 늘어난다.
 */
export interface RoomStartParts {
  warn: boolean;
  /** 문 닫힘 공지 문장 (없으면 null) */
  lock: string | null;
  holdMs: number;
}

export const ROOM_START_KEY = 'roomStart';

export function roomStartAlert(parts: RoomStartParts, stageIndex: number): AlertSpec {
  const lines: string[] = [];
  if (parts.warn) lines.push(r53Text('warnLine'));
  if (parts.lock) lines.push(trimEnd(parts.lock));
  const body = lines.join(' · ');
  return {
    kind: 'warn',
    key: ROOM_START_KEY,
    label: [parts.warn ? r53Text('warnTitle') : '', body].filter(Boolean).join(' / '),
    timing: { ...A.warn, holdMs: Math.max(A.warn.holdMs, parts.holdMs) },
    build: (sc) =>
      bannerCard(
        sc,
        parts.warn
          ? [
              { text: r53Text('warnTitle'), style: 'ink_accent', scale: 2, gap: 2 },
              { text: body, style: 'ink_body' },
            ]
          : [{ text: body, style: 'ink_body' }],
        stageIndex,
      ),
    onShow: (box) => {
      if (!parts.warn) return;
      blinkFirstText(box);
    },
    merge: (prev) => {
      const p = (prev as AlertSpec & { parts?: RoomStartParts }).parts;
      if (!p) return null;
      const merged: RoomStartParts = {
        warn: p.warn || parts.warn,
        lock: p.lock ?? parts.lock,
        holdMs: Math.max(p.holdMs, parts.holdMs),
      };
      return roomStartAlert(merged, stageIndex);
    },
    parts,
  } as AlertSpec & { parts: RoomStartParts };
}

/** 짧은 안내 한 줄 (옛 가운데 배너 — 세트 단계 등) */
export function infoAlert(text: string, stageIndex: number): AlertSpec {
  return {
    kind: 'info',
    key: `info:${text}`,
    label: text,
    timing: A.info,
    build: (sc) => bannerCard(sc, [{ text, style: 'ink_body' }], stageIndex),
    merge: (prev) => prev,
  };
}

/** 카드의 첫 글(제목)을 계단 알파로 몇 번 깜빡인다 (키트 허용 알파 1 ↔ 0.55) */
function blinkFirstText(box: Phaser.GameObjects.Container): void {
  const title = box.list.find((o) => o.type === 'Container') as Phaser.GameObjects.Container | undefined;
  if (!title) return;
  box.scene.time.addEvent({
    delay: A.warn.blinkMs,
    repeat: A.warn.blinks * 2 - 1,
    callback: () => {
      if (title.active) title.setAlpha(title.alpha < 1 ? 1 : 0.55);
    },
  });
}

function trimEnd(s: string): string {
  return s.trim().replace(/[.。]+$/, '');
}
