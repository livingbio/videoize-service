#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2016 lizongzhe
#
# Distributed under terms of the MIT license.
import json
import os
import re
import subprocess
import tempfile


def is_effict_frame(frame_info):
    return not sum(frame_info['stdev']) < 10


def create_tempdir():
    return tempfile.mkdtemp()


def quick_execute(cmd, ignore_error=False):
    print "Exe", cmd
    process = subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE
    )
    message = process.communicate()[1]
    print message
    rc = process.returncode

    if not ignore_error:
        assert rc == 0, u'EXE: %s\n%s' % (cmd, message)

    return message


def __parse_frames_log(ffmpeg_log):
    lines = re.split("[\r\n]", ffmpeg_log)
    img_logs = [line for line in lines if "pts_time" in line]
    frames = []
    for img_log in img_logs:
        img_info = dict(re.findall(
            "(\w+)\s*:\s*([^ \[]+|\[[^\]]*\])", img_log.replace(' \x08', '')))
        img_info['pts_time'] = float(img_info['pts_time'])
        img_info['n'] = int(img_info['n'])
        img_info['stdev'] = json.loads(img_info['stdev'].replace(' ', ','))
        img_info['mean'] = json.loads(img_info['mean'].replace(' ', ','))
        frames.append(img_info)

    return frames


def __parse_duration(ffmpeg_log):
    duration_str = re.search("Duration:\s+([\d:.]*)", ffmpeg_log).groups()[0]
    duration = __time_to_second(duration_str)
    return duration


def __time_to_second(time_str):
    hour_str, minute_str, second_str, _ = re.match(
        "(\d{1,2}):(\d{1,2}):(\d{1,2}(\.\d+)?)", time_str).groups()
    hour, minute, second = int(hour_str), int(minute_str), float(second_str)
    total_seconds = hour * 3600 + minute * 60 + second
    return total_seconds


def __second_to_time(total_seconds):
    total_seconds = float(total_seconds)

    hour = int(total_seconds / 3600)
    minute = int((total_seconds % 3600) / 60)
    seconds = int(total_seconds % 60)
    point = str(total_seconds % 1.0).split(".")[1]

    return "{:0>2}:{:0>2}:{:0>2}.{}".format(hour, minute, seconds, point)


def __check_has_output(ffmpeg_log):
    assert "Output file is empty, nothing was encoded" not in ffmpeg_log


def cut_frame(video, seconds=0, file_name=None):
    if not file_name:
        tempdir = create_tempdir()
        file_name = "{}/frame.jpg".format(tempdir)
    time = __second_to_time(seconds)

    command = [
        "ffmpeg",
        "-i", video,
        "-ss", time,
        "-vframes", "1",
        "-filter", "showinfo",
        file_name,
    ]
    proc_log = quick_execute(command)

    frame_infos = __parse_frames_log(proc_log)
    __check_has_output(proc_log)

    frame_info = frame_infos[-1]
    frame_info['file_name'] = file_name

    return frame_info


def cut_preview(video, start=0, duration=3600, file_name=None):
    if not file_name:
        tempdir = create_tempdir()
        file_name = "{}/preview.jpg".format(tempdir)

    command = [
        "ffmpeg",
        "-skip_frame", "nokey",
        "-i", video,
        "-ss", __second_to_time(start),
        "-t", __second_to_time(duration),
        "-filter", "select='eq(pict_type\,PICT_TYPE_I)',showinfo",
        "-vframes", "1",
        file_name,
    ]
    proc_log = quick_execute(command)

    __check_has_output(proc_log), "get preview error"

    frame_infos = __parse_frames_log(proc_log)

    frame_info = frame_infos[-1]
    frame_info['file_name'] = file_name

    # new fill layers solid coler
    if not is_effict_frame(frame_info):
        os.remove(file_name)
        begin = frame_info['pts_time'] + 0.1
        duration = duration - (begin - start)
        return cut_preview(video, begin, duration)
    else:
        return frame_info


def cut_frames(video, fps=2, tempdir=None):
    if not tempdir:
        tempdir = create_tempdir()

    img_template = "{}/%d.jpg".format(tempdir)

    command = [
        "ffmpeg",
        '-y',
        "-i", video,
        "-filter", "fps={},showinfo".format(fps),
        "-vsync", "0",
        "-an",
        img_template,
    ]

    proc_log = quick_execute(command)
    frames = __parse_frames_log(proc_log)

    for frame in frames:
        frame['file_name'] = img_template % (frame['n'] + 1)

    return frames


def get_duration(video):
    command = [
        "ffmpeg",
        "-i", video,
    ]
    proc_log = quick_execute(command, ignore_error=True)
    duration = __parse_duration(proc_log)
    return duration


def get_dimension(videofile):
    lines = quick_execute(['ffmpeg', '-i', videofile], ignore_error=True).split('\n')

    for line in lines:
        rx = re.compile(r'.+Video.+, (\d{2,4})x(\d{2,4}).+')
        m = rx.match(line)

        if m is not None:
            w = int(m.group(1))
            h = int(m.group(2))

            return w, h


def scene_cut(video, threshold=0.3):
    command = [
        "ffmpeg",
        '-y',
        "-i", video,
        "-filter", "select='gt(scene\\,{0})',showinfo".format(threshold),
        "-vsync", "0",
        "-an",
        "-f", "null", "/dev/null"
    ]

    proc_log = quick_execute(command)
    frame_infos = __parse_frames_log(proc_log)

    return frame_infos


def gif(filepath, start_time, duration):
    opath = "./static/gif/%s.%s-%s.gif" % (filepath, start_time, duration)
    if os.path.exists(opath):
        return opath

    quick_execute([
        "ffmpeg",
        "-ss",
        str(start_time),
        "-t",
        str(duration),
        "-i",
        filepath,
        "-filter_complex",
        "fps=10,scale=320:-1:",
        opath
    ])

    return opath
