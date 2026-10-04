/**
 * 스프라이트 시트 정의 (계약 contracts/art-assets.md §1). Phaser 의존 없음.
 * 로드 대상 목록·키 규칙·재생 시간 계산을 담당하고, 실제 로드·애니 등록은 systems/sprites/sprites.ts.
 * 57라운드 B7: 방향·동작 이름·시트 JSON 형식·프레임 시간·경로/키 파일로 나누고 여기서 다시 내보낸다.
 */
export * from './spriteDirs';
export * from './spriteActions';
export * from './sheetJson';
export * from './sheetFrames';
export * from './sheetPaths';
