"""무기 발현 대장(weapon-ledger.html) 생성기. data/weapons.json·personality.json 과 assets/sprites/fx·weapons 시트를 내장한다."""
import json, base64, os, glob
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
w = json.load(open(f'{ROOT}/data/weapons.json', encoding='utf-8'))
p = json.load(open(f'{ROOT}/data/personality.json', encoding='utf-8'))
FX_BY_WEAPON = {
  'katana': ['katana_slash', 'iai', 'batto', 'wide', 'zangetsu', 'longinvuln', 'dashcrit'],
  'greatsword': ['greatsword_slash', 'crush', 'weight', 'quake', 'pulverize', 'ironwall', 'giant'],
  'dagger': ['dagger_slash', 'twin', 'gale', 'dance', 'bleed', 'afterimage', 'assassin'],
  'bow': ['bow_arrow', 'bow_arrow_aimed', 'pierce', 'scatter', 'flash', 'heavyarrow', 'heavyarrow_hit', 'rain', 'seek'],
}
FX_SECONDARY = ['parry_flash', 'guard_wave', 'shadowstep_ghost', 'aim_charge', 'aim_line', 'dash_dust', 'dash_trail']
FX_COMMON = ['hit_spark', 'blood', 'crit_burst', 'knock_dust', 'player_hit', 'telegraph_line', 'telegraph_circle', 'telegraph_cone', 'enemy_bullet', 'boss_fan_shot', 'muzzle_flash']
FX_LABEL = {'katana_slash':'기본 베기','greatsword_slash':'기본 베기','dagger_slash':'기본 베기','bow_arrow':'기본 화살','bow_arrow_aimed':'조준 화살',
  'iai':'거합(1차)','batto':'발도술(1차)','wide':'만월(2차)','zangetsu':'잔월(2차)','longinvuln':'허보(2차)','dashcrit':'급소(2차)',
  'crush':'파쇄(1차)','weight':'중압(1차)','quake':'지진(2차)','pulverize':'분쇄(2차)','ironwall':'철벽(2차)','giant':'거인(2차)',
  'twin':'쌍격(1차)','gale':'질풍(1차)','dance':'난무(2차)','bleed':'출혈(2차)','afterimage':'잔상(2차)','assassin':'암살(2차)',
  'pierce':'관통(1차)','scatter':'산탄(1차)','flash':'섬광(2차)','heavyarrow':'중시 화살(2차)','heavyarrow_hit':'중시 적중(2차)','rain':'폭우(2차)','seek':'추적(2차)',
  'parry_flash':'패링 성공','guard_wave':'가드 밀쳐내기','shadowstep_ghost':'그림자 걸음 잔상','aim_charge':'조준 차지 링','aim_line':'조준 궤적','dash_dust':'대쉬 먼지','dash_trail':'대쉬 잔상',
  'hit_spark':'적중 섬광','blood':'피','crit_burst':'치명타 버스트','knock_dust':'넉백 먼지','player_hit':'플레이어 피격','telegraph_line':'예고 선','telegraph_circle':'예고 원','telegraph_cone':'예고 부채꼴','enemy_bullet':'적 탄','boss_fan_shot':'보스 부채꼴 탄','muzzle_flash':'총구 화염'}
def sheet(dirname, fid):
    j = f'{ROOT}/assets/sprites/{dirname}/{fid}.json'; g = f'{ROOT}/assets/sprites/{dirname}/{fid}.png'
    if not (os.path.exists(j) and os.path.exists(g)): return None
    d = json.load(open(j, encoding='utf-8'))
    keep = {k: d.get(k) for k in ('frameWidth','frameHeight','frames','directions','frameDurationsMs','loop','pivot','anchor','spawn','depth','rotate','tile','tailFrames','note')}
    keep['png'] = 'data:image/png;base64,' + base64.b64encode(open(g,'rb').read()).decode()
    keep['label'] = FX_LABEL.get(fid, fid)
    return keep
fx = {}
for ids in list(FX_BY_WEAPON.values()) + [FX_SECONDARY, FX_COMMON]:
    for fid in ids:
        s = sheet('fx', fid)
        if s: fx[fid] = s
overlays = {wid: sheet('weapons', f'{wid}_attack') for wid in FX_BY_WEAPON}
icons = {wid: sheet('weapons', f'{wid}_icon') for wid in FX_BY_WEAPON}
data = {'weapons': w['weapons'], 'rules': w['rules'], 'personality': p,
        'fx': fx, 'fxByWeapon': FX_BY_WEAPON, 'fxSecondary': FX_SECONDARY, 'fxCommon': FX_COMMON,
        'overlays': {k: v for k, v in overlays.items() if v}, 'icons': {k: v for k, v in icons.items() if v}}
tpl = open(f'{ROOT}/parts/producer/tools/ledger.template.html', encoding='utf-8').read()
out = tpl.replace('__DATA__', json.dumps(data, ensure_ascii=False))
open(f'{ROOT}/parts/producer/tools/weapon-ledger.html', 'w', encoding='utf-8').write(out)
print('ok', len(out)//1024, 'KB', 'fx', len(fx))
