/** UI 파트 공개 지점 (계약 §5). 시스템 파트는 이 파일만 import 한다. */
import { HudScene } from './HudScene';
import { MenuScene } from './MenuScene';
import { PauseScene } from './PauseScene';
import { ResultScene } from './ResultScene';
import { TitleScene } from './TitleScene';
import { TransitionScene } from './TransitionScene';
import { UI_SCENE_KEYS } from './keys';

export const UI_SCENES = UI_SCENE_KEYS;
export const uiScenes = [TitleScene, HudScene, MenuScene, PauseScene, ResultScene, TransitionScene];
