/**
 * 61라운드 E 보스방 VRAM: 노드 종류에 따라 시트 묶음을 올리고 내린다 + 씬 도중 지연 로드·해제 (sheetLoader 의 같은 로드 길).
 * - 보스 노드 preload: 보스 묶음(없는 것만)을 올리고, 보스가 부하를 부르지 않으면 일반 적 시트(부팅 묶음의 enemies)를 내린다.
 * - 다른 노드 preload: 내려 둔 적 시트를 다시 올리고, 보스 묶음·지연 묶음을 내린다 (다음 런 1층 전투에 보스 141MB 가 남지 않게).
 * - 씬 도중(`loadSheetsNow`): 로드 큐에 넣고 바로 시작 — 끝나면 등록 후 done (림·결정타 fx).
 * 텍스처를 내리기 전에 그 텍스처를 그리는 스프라이트가 없어야 한다 (`releaseSheets` 호출 쪽이 확인 — BossVram).
 */
import Phaser from 'phaser';
import { BOSSES } from '../../data';
import { bossIdsInScope } from '../../data/scope';
import { bossLazyRequests } from '../boss/bossSheets';
import { aliasBossFallbacks, queueRequests } from './sheetLoader';
import { bootSheetRequests, bossSheetRequests } from './sheetSets';
import { sheetTextureKey, type SheetRequest } from './sheetPaths';
import { spriteLibrary } from './sprites';

/** 텍스처가 아직 없는 요청만 */
export function missingRequests(scene: Phaser.Scene, reqs: readonly SheetRequest[]): SheetRequest[] {
  return reqs.filter((r) => !scene.textures.exists(sheetTextureKey(r.name, r.action)));
}

/** 텍스처가 있는 요청 (내릴 대상) */
function presentRequests(scene: Phaser.Scene, reqs: readonly SheetRequest[]): SheetRequest[] {
  return reqs.filter((r) => scene.textures.exists(sheetTextureKey(r.name, r.action)));
}

/** 씬 도중 지연 로드: 없는 것만 로드 큐에 넣고 시작. 로드할 것이 없으면 바로 done. 반환 = 로드를 시작했는지 */
export function loadSheetsNow(
  scene: Phaser.Scene,
  reqs: readonly SheetRequest[],
  done: () => void = () => {},
): boolean {
  const started = queueRequests(scene, missingRequests(scene, reqs), done);
  if (started && !scene.load.isLoading()) scene.load.start();
  return started;
}

/** 시트를 내린다 (등록·애니·텍스처·층 변형). 반환 = 지운 텍스처 수 */
export function releaseSheets(scene: Phaser.Scene, reqs: readonly SheetRequest[]): number {
  const have = presentRequests(scene, reqs);
  return have.length > 0 ? spriteLibrary.removeSheets(scene, have) : 0;
}

/** 일반 적 몸·엘리트 외곽선 시트 (부팅 묶음의 enemies 분류) */
export function enemySheetRequests(): SheetRequest[] {
  return bootSheetRequests().filter((r) => r.category === 'enemies');
}

/** 이 보스가 싸움 중 일반 적을 부르는지 (부하 소환 패턴이 어느 국면 pick 에 있으면) — 부르면 적 시트를 내리지 않는다 */
export function bossSummons(bossId: string): boolean {
  const def = BOSSES[bossId];
  return Boolean(def?.phases.some((p) => p.pick.includes('summon')));
}

/**
 * 노드 preload: 보스 노드면 보스 묶음(없는 것만) + 적 시트 내림(부하 소환이 없을 때), 아니면 적 시트(없는 것만) + 보스 묶음·지연 묶음 내림.
 * 반환 = 로드할 파일이 있어 로드를 걸었는지 (Game 이 '불러오는 중' 표시)
 */
export function prepareNodeSheets(scene: Phaser.Scene, toBoss: boolean, bossId: string | null): boolean {
  if (toBoss) {
    if (!bossId || !bossSummons(bossId)) releaseSheets(scene, enemySheetRequests());
    return queueRequests(scene, missingRequests(scene, bossSheetRequests()), aliasBossFallbacks);
  }
  releaseSheets(scene, [...bossSheetRequests(), ...bossLazyRequests(bossIdsInScope())]);
  return queueRequests(scene, missingRequests(scene, enemySheetRequests()), () => {});
}
