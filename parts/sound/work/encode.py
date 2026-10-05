# -*- coding: utf-8 -*-
"""
LOPAD 음향 파트 — 배포 형식 인코딩·검증 (57라운드 Q17 '소리 OGG 전환')

build.py 가 합성한 WAV(작업 캐시 `parts/sound/work/wav/`, 저장소에 두지 않음)를
배포 형식 두 가지로 만든다.

  1순위 `.ogg`  Ogg Vorbis (libvorbis)        — Chrome·Edge·Firefox
  2순위 `.m4a`  AAC-LC in MP4 (ffmpeg aac)    — Ogg 를 못 여는 Safari 대비

이음매·길이 규칙
- OGG: 마지막 페이지 granule = 원본 샘플 수(샘플 정확). ffmpeg 6.1 디코더는 한 페이지에 다 들어가는
  짧은 파일의 끝을 잘못 자르므로(-128 또는 +수백 샘플) SFX 는 페이지를 50 ms 로 잘게 나눈다.
- M4A: 무비 timescale = 샘플레이트로 두어 edit list(elst) 길이가 샘플 정확. 루프 파일은 앞뒤에
  루프의 반대쪽 끝을 LOOP_PAD 샘플씩 이어 붙여 인코딩한 뒤 elst 의 mediaTime 을 그만큼 밀어
  표시 구간을 [0, N) 로 맞춘다 — AAC 첫 프레임 열화가 루프 경계에 오지 않게 한다.
- 결과는 결정적(bitexact). 같은 ffmpeg/libvorbis 버전이면 바이트가 같다.

의존성: 파이썬 표준 라이브러리 + ffmpeg. libvorbisfile(시스템 라이브러리)이 있으면 검증에서
참조 디코더(Firefox 계열)로 OGG 길이를 한 번 더 대조한다(없으면 건너뜀).
"""
import array
import ctypes
import ctypes.util
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import wave

FFMPEG = os.environ.get('FFMPEG') or shutil.which('ffmpeg') or '/usr/bin/ffmpeg'
BITEXACT = ['-fflags', '+bitexact', '-flags:a', '+bitexact', '-map_metadata', '-1']

# 품질 — 57라운드 시험 인코딩 기준 제안값(도영 님 확정 전, sound-design.md 7장)
PROFILE = {
    'bgm': dict(ogg_q=4, ogg_page_us=1000000, m4a_kbps=64),
    'sfx': dict(ogg_q=4, ogg_page_us=50000, m4a_kbps=96),
}
FORMATS = ('ogg', 'm4a')
MIME = {'ogg': 'audio/ogg; codecs="vorbis"', 'm4a': 'audio/mp4; codecs="mp4a.40.2"'}
LOOP_PAD = 2048  # M4A 루프 감싸기 패딩(샘플). AAC 프레임 1024 × 2


# ---------------------------------------------------------------------------
# WAV 입출력
# ---------------------------------------------------------------------------

def read_wav_ch(path):
    """(인터리브 샘플, 샘플레이트, 채널 수). 61라운드 1층 BGM 은 스테레오."""
    with wave.open(path, 'rb') as w:
        sr = w.getframerate()
        ch = w.getnchannels()
        raw = w.readframes(w.getnframes())
    a = array.array('h')
    a.frombytes(raw)
    if sys.byteorder == 'big':
        a.byteswap()
    return a, sr, ch


def read_wav(path):
    a, sr, _ = read_wav_ch(path)
    return a, sr


def _write_wav(path, a, sr, ch=1):
    b = array.array('h', a)
    if sys.byteorder == 'big':
        b.byteswap()
    with wave.open(path, 'wb') as w:
        w.setnchannels(ch)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b.tobytes())


def _ff(args):
    subprocess.run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-y'] + args, check=True)


# ---------------------------------------------------------------------------
# MP4 edit list 손질 (루프 감싸기 패딩용)
# ---------------------------------------------------------------------------

_MP4_CONTAINERS = {'moov', 'trak', 'mdia', 'minf', 'stbl', 'edts'}


def _mp4_atoms(b, off, end, out):
    while off < end:
        size, typ = struct.unpack('>I4s', b[off:off + 8])
        typ = typ.decode('latin1')
        out.append((typ, off, size))
        if typ in _MP4_CONTAINERS:
            _mp4_atoms(b, off + 8, off + size, out)
        off += size
    return out


def mp4_edit(path):
    """(elst 표시 길이, elst mediaTime, mvhd timescale, mdhd timescale)."""
    b = open(path, 'rb').read()
    info = {}
    for typ, o, _ in _mp4_atoms(b, 0, len(b), []):
        if typ == 'mvhd' and b[o + 8] == 0:
            info['mvhd'] = struct.unpack('>I', b[o + 20:o + 24])[0]
        elif typ == 'mdhd' and b[o + 8] == 0:
            info['mdhd'] = struct.unpack('>I', b[o + 20:o + 24])[0]
        elif typ == 'elst' and b[o + 8] == 0 and struct.unpack('>I', b[o + 12:o + 16])[0] == 1:
            info['seg'], info['media'] = struct.unpack('>Ii', b[o + 16:o + 24])
    return info.get('seg'), info.get('media'), info.get('mvhd'), info.get('mdhd')


def _mp4_trim(path, skip, n):
    """elst mediaTime += skip, 표시 길이(elst·mvhd·tkhd) = n. timescale 이 샘플레이트일 때만."""
    b = bytearray(open(path, 'rb').read())
    atoms = _mp4_atoms(b, 0, len(b), [])
    names = [t for t, _, _ in atoms]
    if names.count('elst') != 1 or names.count('trak') != 1:
        raise RuntimeError('예상 밖 MP4 구조: %s' % path)
    ts = {}
    for typ, o, _ in atoms:
        if b[o + 8] != 0 and typ in ('mvhd', 'tkhd', 'mdhd', 'elst'):
            raise RuntimeError('64비트 MP4 헤더는 지원 안 함: %s' % path)
        if typ == 'mvhd':
            ts['mvhd'] = struct.unpack('>I', b[o + 20:o + 24])[0]
            struct.pack_into('>I', b, o + 24, n)
        elif typ == 'tkhd':
            struct.pack_into('>I', b, o + 28, n)
        elif typ == 'mdhd':
            ts['mdhd'] = struct.unpack('>I', b[o + 20:o + 24])[0]
        elif typ == 'elst':
            if struct.unpack('>I', b[o + 12:o + 16])[0] != 1:
                raise RuntimeError('elst 항목이 1개가 아님: %s' % path)
            media = struct.unpack('>i', b[o + 20:o + 24])[0]
            struct.pack_into('>Ii', b, o + 16, n, media + skip)
    if ts.get('mvhd') != ts.get('mdhd'):
        raise RuntimeError('timescale 불일치 %r: %s' % (ts, path))
    with open(path, 'wb') as f:
        f.write(bytes(b))


# ---------------------------------------------------------------------------
# 인코딩
# ---------------------------------------------------------------------------

def encode_file(kind, wav_path, out_dir, loop):
    """WAV 하나 → out_dir/<이름>.ogg, .m4a. 돌려주기: {fmt: 경로}."""
    prof = PROFILE[kind]
    name = os.path.splitext(os.path.basename(wav_path))[0]
    os.makedirs(out_dir, exist_ok=True)
    out = {fmt: os.path.join(out_dir, '%s.%s' % (name, fmt)) for fmt in FORMATS}

    _ff(['-i', wav_path, '-c:a', 'libvorbis', '-q:a', str(prof['ogg_q']),
         '-page_duration', str(prof['ogg_page_us'])] + BITEXACT + [out['ogg']])

    a, sr, ch = read_wav_ch(wav_path)
    # ffmpeg 6.1 기본 twoloop 코더는 저역 과도(예: guard_push 28 Hz)에서 피크가 +5.7 dB 튀어 fast 코더 사용
    # 스테레오(61라운드 1층 BGM)는 채널당 같은 비트레이트 = 프로필 × 채널 수 (BGM 64 → 128 kbps)
    aac = ['-c:a', 'aac', '-b:a', '%dk' % (prof['m4a_kbps'] * ch), '-aac_coder', 'fast', '-aac_pns', '0',
           '-movie_timescale', str(sr)] + BITEXACT
    if loop and len(a) // ch > LOOP_PAD:
        n = len(a) // ch
        pad = LOOP_PAD * ch
        padded = a[len(a) - pad:] + a + a[:pad]
        with tempfile.TemporaryDirectory() as td:
            tmp = os.path.join(td, name + '.wav')
            _write_wav(tmp, padded, sr, ch)
            _ff(['-i', tmp] + aac + [out['m4a']])
        _mp4_trim(out['m4a'], LOOP_PAD, n)
    else:
        _ff(['-i', wav_path] + aac + [out['m4a']])
    return out


# ---------------------------------------------------------------------------
# 디코딩 (검증용)
# ---------------------------------------------------------------------------

def decode_ffmpeg(path, sr, ch=1):
    r = subprocess.run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-i', path,
                        '-f', 's16le', '-ac', str(ch), '-ar', str(sr), '-'],
                       capture_output=True, check=True)
    a = array.array('h')
    a.frombytes(r.stdout)
    if sys.byteorder == 'big':
        a.byteswap()
    return a


_VF = None


def _vorbisfile():
    global _VF
    if _VF is None:
        lib = ctypes.util.find_library('vorbisfile')
        try:
            _VF = ctypes.CDLL(lib) if lib else False
        except OSError:
            _VF = False
        if _VF:
            _VF.ov_pcm_total.restype = ctypes.c_int64
            _VF.ov_read.restype = ctypes.c_long
    return _VF


def decode_vorbisfile(path):
    """libvorbisfile 참조 디코더. 라이브러리가 없으면 None."""
    vf = _vorbisfile()
    if not vf:
        return None
    st = ctypes.create_string_buffer(8192)  # OggVorbis_File(약 1 KB)보다 넉넉히
    if vf.ov_fopen(path.encode(), st) != 0:
        raise RuntimeError('ov_fopen 실패: %s' % path)
    out = bytearray()
    buf = ctypes.create_string_buffer(16384)
    bs = ctypes.c_int()
    big = 1 if sys.byteorder == 'big' else 0
    while True:
        n = vf.ov_read(st, buf, 16384, big, 2, 1, ctypes.byref(bs))
        if n < 0:
            raise RuntimeError('ov_read 오류 %d: %s' % (n, path))
        if n == 0:
            break
        out += buf.raw[:n]
    vf.ov_clear(st)
    a = array.array('h')
    a.frombytes(bytes(out))
    return a


# ---------------------------------------------------------------------------
# 지표
# ---------------------------------------------------------------------------

def peak_db(a):
    p = max((abs(x) for x in a), default=0)
    return 20 * math.log10(p / 32767.0) if p else -999.0


def clipped(a):
    return sum(1 for x in a if abs(x) >= 32767)


def seam_ratio(o, d):
    """루프 이음매 검사. 돌려주기: (튐 비율, 이음매 오차 dBFS).

    튐 비율 = 디코드 결과의 이음매 한 칸 변화 |d[0]-d[N-1]| ÷ 같은 디코드 결과 안쪽 인접 샘플 변화의
    99.9 백분위. ≤ 1 이면 이음매가 파일 안의 평범한 한 칸보다 크지 않다(클릭 없음).
    이음매 오차 = (d[0]-d[N-1]) 와 원본 (o[0]-o[N-1]) 의 차이 — 손실 압축이 이음매에 더한 변화(참고값)."""
    n = len(o)
    d = d[:n]
    steps = sorted(abs(d[i] - d[i - 1]) for i in range(1, n))
    p999 = max(steps[min(len(steps) - 1, int(len(steps) * 0.999))], 1)
    jump = abs(d[0] - d[n - 1])
    err = abs((d[0] - d[n - 1]) - (o[0] - o[n - 1]))
    return jump / p999, 20 * math.log10(max(err, 1) / 32767.0)


def front_lag(o, d, lags=(-2048, -1024, 0, 1024, 2048), span=8192):
    """앞 정렬 확인: 앞 span 샘플에서 오차가 가장 작은 지연(코덱 프라이밍이 남으면 0 이 아님)."""
    best = None
    for lag in lags:
        e = 0
        cnt = 0
        for i in range(max(0, -lag), min(len(o), span)):
            j = i + lag
            if 0 <= j < len(d):
                e += (o[i] - d[j]) ** 2
                cnt += 1
        if cnt and (best is None or e / cnt < best[1]):
            best = (lag, e / cnt)
    return best[0] if best else 0


def _seam_ch(o, d, ch):
    """채널마다 seam_ratio → (가장 큰 튐 비율, 그 채널의 이음매 오차)."""
    if ch == 1:
        return seam_ratio(o, d)
    return max(seam_ratio(o[c::ch], d[c::ch]) for c in range(ch))


def check_encoded(kind, wav_path, enc, loop):
    """하나의 WAV 와 인코딩 결과를 대조. 돌려주기: (지표 dict, 문제 목록). 길이·이음매는 프레임(채널 묶음) 단위."""
    o, sr, ch = read_wav_ch(wav_path)
    n = len(o) // ch
    r = dict(sr=sr, samples=n, loop=loop, ch=ch)
    bad = []

    p = enc['ogg']
    r['ogg_kb'] = os.path.getsize(p) / 1024
    d = decode_ffmpeg(p, sr, ch)
    r['ogg_ff'] = len(d) // ch - n
    ref = decode_vorbisfile(p)
    r['ogg_vf'] = None if ref is None else len(ref) // ch - n
    use = ref if ref is not None else d
    r['ogg_peak'] = peak_db(use)
    r['ogg_clip'] = clipped(use)
    r['ogg_seam'] = _seam_ch(o, use, ch) if loop else None
    if r['ogg_ff'] != 0 or (r['ogg_vf'] not in (None, 0)):
        bad.append('ogg 길이')
    if r['ogg_clip']:
        bad.append('ogg 클리핑')
    if loop and r['ogg_seam'][0] > 1.0:
        bad.append('ogg 이음매')

    p = enc['m4a']
    r['m4a_kb'] = os.path.getsize(p) / 1024
    seg, media, mvts, mdts = mp4_edit(p)
    r['m4a_elst'] = seg
    r['m4a_media'] = media
    d = decode_ffmpeg(p, sr, ch)
    r['m4a_tail'] = len(d) // ch - n    # ffmpeg 6.1 은 elst 끝 자르기를 안 해 끝 패딩이 남는다
    r['m4a_lag'] = max((front_lag(o[c::ch], d[c::ch]) for c in range(ch)), key=abs)
    r['m4a_peak'] = peak_db(d[:n * ch])
    r['m4a_clip'] = clipped(d[:n * ch])
    r['m4a_seam'] = _seam_ch(o, d, ch) if loop else None
    if seg != n or mvts != sr or mdts != sr:
        bad.append('m4a elst')
    if r['m4a_lag'] != 0 or r['m4a_tail'] < 0:
        bad.append('m4a 정렬')
    if r['m4a_clip']:
        bad.append('m4a 클리핑')
    if loop and r['m4a_seam'][0] > 1.0:
        bad.append('m4a 이음매')
    return r, bad
