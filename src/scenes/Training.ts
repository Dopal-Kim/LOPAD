import { SCENES } from '../core/Constants';
import { Game } from './Game';

/**
 * 61 단계 6 (P14 §1 · 계약 UI §19) 수련장 (씬 키 'Training' — host.startTraining 이 이 키로 시작).
 * 무기 시험장처럼 Game 을 lab 플래그로 쓰고(연습 런 · 세이브 없음 · 죽지 않음), 그 위에 수련장 방(scenes/game/training)을 얹는다.
 * 시작 데이터 `trainingRoom` 이 없으면 지도 마당 (수련장 지도 메뉴), 있으면 그 방.
 */
export class Training extends Game {
  constructor() {
    super(SCENES.TRAINING, true, true);
  }
}
