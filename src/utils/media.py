import os

from moviepy.editor import VideoFileClip
from utils import ffmpeg_toolkits
from utils.workspace import cache


@cache(u'{0}.{1}.mp4')
def convert_mp4(filepath, resolution, opath):
    assert resolution in (600, 720, 1080)

    if filepath.endswith('.mp4') and ffmpeg_toolkits.get_dimension(filepath)[1] == resolution:
        os.system('qt-faststart %s %s' % (filepath, opath))
        if os.path.exists(opath):
            return opath
        else:
            return filepath

    ffmpeg_toolkits.quick_execute([
        'ffmpeg',
        '-i',
        filepath,
        '-vf',
        'scale=-1:%s' % resolution,
        '-strict',
        '-2',
        '-movflags',
        '+faststart',
        opath
    ])

    return opath


@cache(u'{0}.wav')
def convert_wav(path, opath):
    if path.endswith('.wav'):
        return path

    ffmpeg_toolkits.quick_execute([
        'ffmpeg',
        '-i',
        path,
        opath
    ])
    return opath


@cache(u'{0}-{1}-{2}.mp4')
def cut_clip(path, from_ts, duration, opath):
    ffmpeg_toolkits.quick_execute([
        'ffmpeg',
        '-ss',
        str(from_ts),
        '-t',
        str(duration),
        '-i',
        path,
        '-strict',
        '-2',
        '-movflags',
        '+faststart',
        opath
    ])
    return opath


@cache(u'{0}-tmp/')
def _sample_images(path, fps, opath):
    ffmpeg_toolkits.quick_execute([
        'ffmpeg',
        '-i',
        path,
        '-vf',
        'fps=%s' % fps,
        '{}/thumb%05d.jpg'.format(opath)
    ])

    return opath


def sample_images(path, fps):
    odir = _sample_images(path, fps)

    files = [os.path.join(odir, ifile) for ifile in os.listdir(odir)]
    files.sort()

    return files


def get_duration(filepath):
    clip = VideoFileClip(filepath)
    return clip.duration
