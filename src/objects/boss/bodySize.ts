/**
 * 54라운드 Q13~Q16: 보스 판정 크기를 그림 크기에 비례 (보스 그림 192×240 안팎으로 키움 — 시트 값만 바뀌어도 그대로 동작).
 * `bodyFromArt` = idle 시트 한 프레임의 월드 크기(도트 × pixelScale 배율)에 곱할 비율. 시트가 없거나 비율이 없으면 data size 그대로.
 * 돌진 판정·접촉 거리·술통 맞힘은 모두 이 바디로 잰다
 */
export function bossBodySize(
  size: readonly [number, number],
  ratio: { w: number; h: number } | undefined,
  sheet: { frameWidth: number; frameHeight: number; scale: number } | null,
): [number, number] {
  if (!ratio || !sheet) return [size[0], size[1]];
  return [
    Math.max(8, Math.round(sheet.frameWidth * sheet.scale * ratio.w)),
    Math.max(8, Math.round(sheet.frameHeight * sheet.scale * ratio.h)),
  ];
}
