import { SCENES } from '../core/Constants';
import { Game } from './Game';

/**
 * 49라운드 계약 §11.4 무기 시험장 (씬 키 'WeaponLab' — host.startWeaponLab 이 이 키로 시작).
 * 전투·연출·자원 코드는 Game 을 그대로 쓰고 lab 플래그로 런 준비·지도·허수아비·메뉴만 바꾼다:
 * 작은 아레나(카메라 2배), 중앙 허수아비(무한 체력·데미지 숫자), 일정 방향으로 투사체를 쏘는 사수 허수아비,
 * L = 무기 메뉴(MENU_OPEN 'lab') → 개성 갈래 메뉴('labBranch'), Esc = 타이틀. 스냅샷 lab = true, 세이브 없음, 죽지 않음
 */
export class WeaponLab extends Game {
  constructor() {
    super(SCENES.WEAPON_LAB, true);
  }
}
