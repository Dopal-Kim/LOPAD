/**
 * P21 어두운 톤 · 잔혹 전투 · 상흔 묶음 (계약 dark-brutal) — Game 이 create 에서 만들고 update 에서 부른다.
 * GoreFx(피·상처·시체·사망 변형) · HeroWounds(주인공 상흔·저HP) · Execution(처형) · ColorGrade(월드 색 보정 — `?grade=0` 끔).
 * 아트 시트(fx v5·사망 변형·상흔·처형)는 매니페스트에 있는 것만 씬 도중 지연 로드 — 없으면 각 모듈의 임시 그림.
 */
import { gameState } from '../../../core/GameState';
import { ColorGrade } from '../../../systems/fx/colorGrade';
import { loadSheetsNow } from '../../../systems/sprites/lazySheets';
import { spriteLibrary } from '../../../systems/sprites/sprites';
import { urlParams } from '../shared';
import { brutalSheetRequests } from './brutalArt';
import { Execution } from './Execution';
import { GoreFx } from './GoreFx';
import { HeroWounds } from './HeroWounds';
import type { Game } from '../../Game';

export class Brutal {
  readonly gore: GoreFx;
  readonly wounds: HeroWounds;
  readonly execution: Execution;
  readonly grade: ColorGrade | null;

  constructor(g: Game) {
    this.gore = new GoreFx(g);
    this.grade = urlParams().get('grade') === '0' ? null : new ColorGrade(g, g.nodeArena?.regionId);
    if (this.grade) g.screenFx.desatSink = (v) => this.grade?.setExtraDesat(v);
    this.wounds = new HeroWounds(g);
    this.execution = new Execution(g);
    // 상흔 오버레이는 지금 올라와 있는 주인공 몸 시트마다
    const body = spriteLibrary
      .summary()
      .sheets.filter((id) => id.startsWith('player_'))
      .map((id) => id.slice('player_'.length));
    loadSheetsNow(g, brutalSheetRequests(gameState.weapon.id, body));
  }

  /** 매 프레임 (적 update 뒤) */
  update(time: number): void {
    this.gore.update(time);
    this.wounds.update(time);
    this.execution.update(time);
    this.grade?.update(time);
  }

  /** 디버그 (`__lopad.brutal()`) */
  summary(): Record<string, unknown> {
    return {
      gore: this.gore.summary(),
      wound: { ...this.wounds.toUi(), lowHp: this.wounds.lowHp, mode: this.wounds.mode },
      execution: {
        target: this.execution.target?.spriteId ?? null,
        count: this.execution.count,
        cancels: this.execution.cancels,
        lastAction: this.execution.lastAction,
      },
      grade: this.grade?.summary() ?? null,
    };
  }
}
