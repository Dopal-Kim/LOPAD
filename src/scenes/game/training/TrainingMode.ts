/**
 * 61 단계 6 (P14 §1 · 계약 UI §19) 수련장 — Game 의 시험장 모드(lab) 위에서 도는 방 하나 (씬 키 Training).
 * - 지도 마당(방 없음): 수련장 지도 메뉴('training' — 줄 room = 방 id)를 열고, 고르면 그림 속 입구 전환('training')으로 그 방.
 * - 방: 준비물(TrainingRoomKit) · 훈련 예고(TrainingDrills) · 과제 판정(systems/training/tasks) · 출구로 나가면 전환('exitRoom') → 지도 마당.
 * - 무기 방: 대표 개성 2장을 켜 두고, 허수아비·적을 칠 때마다 각성 게이지 → 눈금 메뉴(개성·1차 각성) → L 로 다른 갈래 깨우기.
 * - 런과 분리: 세이브·게이지·전표는 맡겨 둔 런과 무관(session), 기록은 메타 `diary.training` 만.
 */
import { KEYS, TILE } from '../../../core/Constants';
import { EventBus, Events, type TrainingStampPayload, type TrainingTaskPayload } from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import { TRAITS, growthBranches } from '../../../data/growth';
import { TRAINING, trainingRoom, trainingText, type TrainingRoomDef } from '../../../data/training';
import {
  UI_EVENTS,
  UI_SCREEN,
  __system,
  uiCommands,
  type UiMenuLine,
  type UiTraining,
  type UiTrainingStamp,
  type UiTrainingTask,
} from '../../../contract/ui';
import { audio } from '../../../systems/audio/audio';
import { TRAINING_BGM_STATE } from '../../../systems/audio/audioTraining';
import { oncePerKeyEvent } from '../../../systems/keyEvents';
import { diaryNow, updateDiary, type TrainingRecord } from '../../../systems/narrative/diary';
import {
  allStamped,
  buildTrainingUi,
  recordStamp,
  recordTaskDone,
  recordVisit,
  startProgress,
} from '../../../systems/training/record';
import { TaskTracker } from '../../../systems/training/tasks';
import { transitionGate } from '../../../systems/transition/transitionGate';
import type { DrillShape } from '../../../systems/training/drills';
import type { Game } from '../../Game';
import type { GameInitData } from '../shared';
import { MAP_TRAINING, loadPaint, mapRoomPoint, paintLoaded, withDoor } from '../PaintArt';
import { trainingDoorName } from '../../../systems/transition/doorNames';
import { fadeCover, screenOfWorld } from '../TransitionFx';
import { trainingSession } from './session';
import { TrainingDrills } from './TrainingDrills';
import { TrainingRoomKit } from './TrainingRoomKit';
import { TrainingProps } from './TrainingProps';

/** 지도 마당 id (스냅샷 room) */
export const TRAINING_HALL = 'hall';
/** 수련장 지도 메뉴 그만두기 (= 수련장 나가기) */
const MAP_CANCEL_KEY = '0';
/** 훈련 예고 모양 → 과제 id */
const DRILL_TASK: Record<DrillShape, string> = { circle: 'readCircle', line: 'readLine', cone: 'readFan' };

export class TrainingMode {
  readonly room: TrainingRoomDef | null;
  private tracker: TaskTracker | null = null;
  private record: TrainingRecord;
  private kit: TrainingRoomKit | null = null;
  private drills: TrainingDrills | null = null;
  private props: TrainingProps | null = null;
  private subs: { event: string; fn: (p: unknown) => void }[] = [];
  /** 출구에서 벗어나야 다시 나간다 (들어온 자리) */
  private exitArmed = false;
  private leaving = false;
  private traitIds: string[] = [];
  private branchIds: string[] = [];
  private eliteName = '';
  /** 이번 방문 첫 각성 안내 (런에 이어지지 않음) */
  private noCarrySaid = false;
  private readonly onKey = oncePerKeyEvent<KeyboardEvent>(() => this.openBranchMenu());
  /** 디버그 기록 */
  readonly log: { t: number; ev: string; info?: unknown }[] = [];

  constructor(
    private readonly g: Game,
    roomId: string | undefined,
  ) {
    this.room = roomId ? trainingRoom(roomId) : null;
    this.record = diaryNow().training;
  }

  /** 이 방 id 가 만취 그림자 방인가 (preload — 보스 시트) */
  static isBossRoom(id: string | undefined): boolean {
    return Boolean(id && trainingRoom(id)?.setup.boss);
  }

  /** 만취 그림자 방 (보스 노드 전장) */
  get bossRoom(): boolean {
    return Boolean(this.room?.setup.boss);
  }

  /** 각성 게이지가 오를 수 있나 — 무기 방의 '각성 게이지 채우기' 과제가 남은 동안만 */
  get allowsGrowth(): boolean {
    return Boolean(this.room?.setup.gauge) && !this.tracker?.isDone('gauge');
  }

  get hall(): boolean {
    return this.room === null;
  }

  /** LabMode.prepareRun 뒤 (연습 런이 만들어진 뒤) */
  prepare(): void {
    const s = this.room?.setup;
    if (s?.potions !== undefined) gameState.potions = s.potions;
  }

  /** 월드·주인공·모듈이 다 만들어진 뒤 */
  setup(): void {
    const g = this.g;
    audio.setState(TRAINING_BGM_STATE);
    // 지도 마당: 수련장 지도 그림 + 방 입구 그림 2장 (art §28 — door_training_training · door_training_boss)
    if (!this.room) loadPaint(g, [MAP_TRAINING, trainingDoorName(false), trainingDoorName(true)]);
    if (!this.room) {
      g.ui.story('notice', trainingText('hall.enter'));
      this.openMap();
      return;
    }
    const room = this.room;
    this.record = updateDiary((d) => ({ ...d, training: recordVisit(d.training) })).training;
    const w = gameState.weapon;
    this.branchIds = room.weapon ? growthBranches(w.id).map((b) => b.id) : [];
    this.traitIds = room.weapon ? [...(TRAINING.traitPicks[w.id] ?? [])] : [];
    this.tracker = new TaskTracker(
      room.tasks,
      { branches: this.branchIds, traits: this.traitIds },
      TRAINING.tuning.drillMs + 200,
      startProgress(this.record, room.id),
    );
    for (const event of this.tracker.events()) {
      const fn = (p: unknown) => this.onEvent(event, p);
      EventBus.on(event, fn, this);
      this.subs.push({ event, fn });
    }
    if (room.setup.gauge) this.listen(Events.ENEMY_DAMAGED, () => this.feedGauge());
    this.listen(Events.WEAPON_AWAKEN, () => this.onAwaken());
    if (room.setup.boss) this.listen(Events.BOSS_DIED, () => this.onBossDown());
    this.kit = new TrainingRoomKit(g, room, TRAINING.tuning, () => !this.tracker?.allDone);
    this.kit.setup();
    // art §28 소품 (표지판·도장 판·무기 걸이·연습 깃발) — 작은 시트 지연 로드
    const kit = this.kit;
    this.props = new TrainingProps(g, room, () => kit.center());
    this.props.load({ stamped: this.record.stamped.includes(room.id), flagAt: kit.markerAt });
    this.listen(Events.TRAINING_REACH, () => this.props?.set('flag', 'reached'));
    const drills = room.setup.drills ?? [];
    if (drills.length > 0)
      this.drills = new TrainingDrills(
        g,
        drills,
        TRAINING.tuning,
        (s) => this.tracker?.isDone(DRILL_TASK[s]) ?? true,
        () => !this.tracker?.allDone,
      );
    // 마시기 과제: 가득 찬 몸은 마실 수 없다 — 조금 다친 채로 시작
    if (room.tasks.some((t) => t.id === 'drinkDraught')) gameState.hp = Math.ceil(gameState.maxHp * 0.7);
    for (const id of this.traitIds) g.growth.gainTrait(id);
    // 출구는 늘 열려 있다 (아무 때나 지도로)
    const e = g.layout?.arena?.exit;
    if (e) g.world.placeExitAt(e.x, e.y);
    g.input.keyboard?.on(`keydown-${KEYS.LAB_MENU}`, this.onKey);
    const stamped = this.record.stamped.includes(room.id);
    g.ui.story('notice', trainingText(`${room.id}.enter`));
    if (stamped) g.ui.story('notice', trainingText('common.reenter'));
    const voice = room.weapon ? trainingText(`${room.weapon}.voice.start`) : '';
    if (voice) __system.emit(UI_EVENTS.STORY, { kind: 'voice', text: voice, weapon: room.weapon ?? undefined });
    this.note('enter', room.id);
  }

  private listen(event: string, fn: (p: unknown) => void): void {
    EventBus.on(event, fn, this);
    this.subs.push({ event, fn });
  }

  update(time: number): void {
    const g = this.g;
    if (!this.room || !this.tracker) return;
    for (const id of this.tracker.tick(time)) this.complete(id);
    this.kit?.update(time);
    this.drills?.update(time);
    // 출구: 걸어 들어가면 지도로 (전투 중이어도 — 수련장은 아무 때나 나간다)
    const onExit = g.world.isExitAt(g.player.x, g.player.y);
    if (!onExit) this.exitArmed = true;
    else if (this.exitArmed && !this.leaving && !g.menu.isOpen && !g.frozen && !transitionGate.locked) this.exitRoom();
  }

  // --- 과제 ---

  private onEvent(event: string, payload: unknown): void {
    if (!this.tracker || this.leaving) return;
    for (const id of this.tracker.onEvent(event, payload, this.g.time.now)) this.complete(id);
  }

  private complete(id: string): void {
    const room = this.room;
    if (!room || !this.tracker) return;
    const label = this.label(id);
    this.record = updateDiary((d) => ({ ...d, training: recordTaskDone(d.training, room.id, id) })).training;
    EventBus.emit(Events.TRAINING_TASK, { room: room.id, id } satisfies TrainingTaskPayload);
    __system.emit(UI_EVENTS.TRAINING_TASK, { room: room.id, id, label } satisfies UiTrainingTask);
    this.note('task', id);
    if (this.tracker.allDone) this.stamp();
  }

  /** 도장: 방 과제를 모두 마침 */
  private stamp(): void {
    const room = this.room;
    if (!room) return;
    const first = !this.record.stamped.includes(room.id);
    this.record = updateDiary((d) => ({ ...d, training: recordStamp(d.training, room.id) })).training;
    const all = allStamped(
      this.record,
      TRAINING.rooms.map((r) => r.id),
    );
    EventBus.emit(Events.TRAINING_STAMP, { room: room.id, all } satisfies TrainingStampPayload);
    __system.emit(UI_EVENTS.TRAINING_STAMP, {
      room: room.id,
      name: trainingText(`${room.id}.name`),
      all,
    } satisfies UiTrainingStamp);
    this.props?.stamp();
    this.g.ui.story('notice', trainingText('common.stamp'));
    if (all && first) this.g.ui.story('notice', trainingText('common.allStamped'));
    const voice = room.weapon ? trainingText(`${room.weapon}.voice.stamp`) : '';
    if (voice) __system.emit(UI_EVENTS.STORY, { kind: 'voice', text: voice, weapon: room.weapon ?? undefined });
    this.note('stamp', room.id);
  }

  /** 과제 문장 ({trait1}·{trait2}·{elite} 채움) */
  private label(id: string): string {
    const room = this.room;
    if (!room) return '';
    const traitName = (n: number) => TRAITS.find((t) => t.id === this.traitIds[n])?.name ?? '';
    if (id === 'elite') {
      // 엘리트 이름표(접두어가 붙은 이름)를 본 적이 있으면 그 이름, 없으면 '우두머리 쓰러뜨리기'
      const seen = this.g.bundle?.elitesUi()[0]?.name;
      if (seen) this.eliteName = seen;
      if (!this.eliteName) return trainingText(`${room.id}.task.eliteFallback`);
    }
    return trainingText(`${room.id}.task.${id}`, { trait1: traitName(0), trait2: traitName(1), elite: this.eliteName });
  }

  /** 무기 방: 각성 게이지 과제가 남았으면 허수아비·적을 칠 때마다 게이지 */
  private feedGauge(): void {
    if (!this.tracker || this.tracker.isDone('gauge') || this.leaving) return;
    this.g.growth.gain(TRAINING.tuning.gaugePerHit);
  }

  private onAwaken(): void {
    const room = this.room;
    if (!room?.weapon || this.noCarrySaid) return;
    this.noCarrySaid = true;
    this.g.ui.story('notice', trainingText('common.noCarry'));
    const voice = trainingText(`${room.weapon}.voice.awaken`);
    if (voice) __system.emit(UI_EVENTS.STORY, { kind: 'voice', text: voice, weapon: room.weapon });
  }

  /** L (무기 방, 1차 각성 뒤): 다른 갈래 깨우기 — 갈래 카드 메뉴(`evolve` awaken1 줄) → 경로를 비우고 그 갈래로 각성 연출 */
  private openBranchMenu(): void {
    const g = this.g;
    const room = this.room;
    if (!room?.weapon || this.leaving || g.menu.isOpen || g.frozen || transitionGate.locked) return;
    const w = gameState.weapon;
    if (w.stage < 1) {
      g.ui.story('notice', trainingText(`${room.id}.task.gauge`));
      return;
    }
    const ui = g.growth.toUi();
    const defs = growthBranches(w.id);
    const lines: UiMenuLine[] = ui.branches.map((b, i) => ({
      key: String(i + 1),
      label: b.name,
      detail: b.line,
      enabled: b.id !== w.branchId,
      kind: 'awaken1',
      verb: b.verb,
      branch: b,
    }));
    g.setFrozen(true);
    g.player.haltForWarp();
    g.menu.open(
      'evolve',
      trainingText(`${room.id}.name`),
      lines,
      (key) => {
        if (key === MAP_CANCEL_KEY) return this.closeMenu();
        const def = defs[Number(key) - 1];
        if (!def || def.id === w.branchId) return;
        this.closeMenu();
        g.growth.labSetPath([]);
        g.growth.awaken(1, def.node);
      },
      '',
      { cancelKey: MAP_CANCEL_KEY },
    );
  }

  private closeMenu(): void {
    const g = this.g;
    g.menu.close();
    g.setFrozen(false);
    g.inputSystem.read();
  }

  // --- 지도 · 드나들기 ---

  /** 수련장 지도 (계약 §19 — 메뉴 'training', 줄 room·stamped) */
  openMap(): void {
    const g = this.g;
    if (!this.hall) return;
    const lines: UiMenuLine[] = TRAINING.rooms.map((r, i) => ({
      key: String(i + 1),
      label: trainingText(`${r.id}.name`),
      detail: trainingText(`${r.id}.enter`),
      enabled: true,
      room: r.id,
      stamped: this.record.stamped.includes(r.id),
    }));
    g.setFrozen(true);
    g.player.haltForWarp();
    g.menu.open(
      'training',
      trainingText('hall.name'),
      lines,
      (key) => {
        if (key === MAP_CANCEL_KEY) {
          g.menu.close();
          uiCommands.leaveTraining();
          return;
        }
        const r = TRAINING.rooms[Number(key) - 1];
        if (r) this.enterRoom(r.id);
      },
      trainingText('hall.exit'),
      { cancelKey: MAP_CANCEL_KEY },
    );
  }

  /** 지도에서 방 고름 → 그림 속 입구('training') → 덮이면 그 방으로 씬 재시작 */
  enterRoom(id: string): boolean {
    const g = this.g;
    const room = trainingRoom(id);
    if (!room || this.leaving) return false;
    this.leaving = true;
    const order = TRAINING.rooms.findIndex((r) => r.id === id);
    const from = mapRoomPoint(g, order, { w: UI_SCREEN.WIDTH, h: UI_SCREEN.HEIGHT });
    const go = () => {
      g.menu.close();
      g.transitioning = true;
      g.scene.restart({
        trainingRoom: id,
        labWeapon: room.weapon ?? trainingSession.weapon ?? undefined,
      } satisfies GameInitData);
    };
    const boss = Boolean(room.setup.boss);
    withDoor(g, trainingDoorName(boss), 1200, (doorKey) => {
      const ok = transitionGate.begin(
        {
          mode: 'training',
          region: 'training',
          nodeKind: boss ? 'boss' : 'training',
          nodeId: id,
          ...(doorKey ? { doorKey } : {}),
          ...(from ? { from } : {}),
        },
        go,
        (cover) => fadeCover(g, cover),
      );
      if (!ok) go();
    });
    return true;
  }

  /** 방 출구 → 그림처럼 굳어 지도로 ('exitRoom') */
  private exitRoom(): void {
    const g = this.g;
    this.leaving = true;
    g.player.haltForWarp();
    const e = g.layout?.arena?.exit;
    const from = e ? screenOfWorld(g, (e.x + 1) * TILE, (e.y + 1) * TILE) : undefined;
    const go = () => {
      g.transitioning = true;
      g.scene.restart({ labWeapon: trainingSession.weapon ?? undefined } satisfies GameInitData);
    };
    const ok = transitionGate.begin(
      { mode: 'exitRoom', region: 'training', nodeKind: 'training', ...(from ? { from } : {}) },
      go,
      (cover) => fadeCover(g, cover),
    );
    if (!ok) go();
  }

  /** 수련장에서 쓰러짐 (시험장처럼 죽지 않는다 — BuildDefense.preventDeath) */
  onFall(): void {
    this.g.ui.story('notice', trainingText('common.fall'));
    this.note('fall');
  }

  /** 만취 그림자를 쓰러뜨림 (진짜가 아님) */
  onBossDown(): void {
    this.g.ui.story('notice', trainingText('shadow.defeat'));
  }

  // --- 계약 ---

  toUi(): UiTraining {
    const room = this.room;
    const rooms = TRAINING.rooms.map((r) => ({ id: r.id, name: trainingText(`${r.id}.name`) }));
    const mapKey = paintLoaded(this.g, MAP_TRAINING);
    if (!room || !this.tracker) {
      return buildTrainingUi({
        room: TRAINING_HALL,
        roomName: trainingText('hall.name'),
        line: trainingText('hall.enter'),
        tasks: [],
        record: this.record,
        rooms,
        mapKey,
      });
    }
    const t = this.tracker;
    return buildTrainingUi({
      room: room.id,
      roomName: trainingText(`${room.id}.name`),
      line: trainingText(`${room.id}.enter`),
      tasks: room.tasks.map((d) => ({
        id: d.id,
        label: this.label(d.id),
        done: t.isDone(d.id),
        ...(d.verb ? { verb: d.verb } : {}),
      })),
      record: this.record,
      rooms,
      mapKey,
    });
  }

  debug(): Record<string, unknown> {
    return {
      room: this.room?.id ?? TRAINING_HALL,
      exit: (() => {
        const e = this.g.layout?.arena?.exit;
        return e ? { x: (e.x + 1) * TILE, y: (e.y + 1) * TILE } : null;
      })(),
      marker: this.kit?.markerAt ?? null,
      gate: {
        leaving: this.leaving,
        exitArmed: this.exitArmed,
        onExit: this.g.world?.isExitAt(this.g.player?.x ?? 0, this.g.player?.y ?? 0) ?? false,
        frozen: this.g.frozen,
        menu: this.g.menu?.isOpen ?? false,
        locked: transitionGate.locked,
      },
      done: this.tracker ? [...this.tracker.done] : [],
      allDone: this.tracker?.allDone ?? false,
      traits: this.traitIds,
      branches: this.branchIds,
      drills: this.drills?.debug() ?? null,
      boss: this.kit?.boss ? { hp: this.kit.boss.hp, maxHp: this.kit.boss.maxHp } : null,
      record: this.record,
      session: { origin: trainingSession.origin, run: trainingSession.stash !== null, weapon: trainingSession.weapon },
      log: this.log.slice(-20),
    };
  }

  /** 디버그: 과제 하나 바로 완료 */
  debugComplete(id: string): boolean {
    if (!this.tracker?.complete(id)) return false;
    this.complete(id);
    return true;
  }

  private note(ev: string, info?: unknown): void {
    this.log.push({ t: Math.round(this.g.time.now), ev, ...(info !== undefined ? { info } : {}) });
    if (this.log.length > 40) this.log.shift();
  }

  destroy(): void {
    for (const s of this.subs) EventBus.off(s.event, s.fn, this);
    this.subs = [];
    this.g.input.keyboard?.off(`keydown-${KEYS.LAB_MENU}`, this.onKey);
    this.kit?.destroy();
    this.kit = null;
    this.props?.destroy();
    this.props = null;
    this.drills = null;
  }
}
