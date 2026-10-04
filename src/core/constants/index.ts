/** 모든 설정값. 게임 수치(스탯·적·보스·스테이지)는 data/*.json, 엔진·화면·연출 값은 여기. */
/**
 * 57라운드 B6: 도메인별 파일로 분리하고 여기서 다시 내보낸다. 기존 `core/Constants` import 는 그대로 동작한다.
 */
export * from './display';
export * from './colors';
export * from './assets';
export * from './world';
export * from './feel';
export * from './enemy';
export * from './player';
export * from './scenes';
export { BOSS_FX } from './boss';
export { MOVE_FX } from './moves';
export { BUILD_FX } from './build';
