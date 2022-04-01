#!/usr/bin/env python
# coding: utf-8

# Copyright 2022 by BurnoutDV, <development@burnoutdv.com>
#
# This file is part of ffmpeg_progress.
#
# ffmpeg_progress is free software: you can redistribute
# it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# ffmpeg_progress is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# @license GPL-3.0-only <https://www.gnu.org/licenses/gpl-3.0.en.html>
import logging
import re
from datetime import timedelta

logger = logging.getLogger(__name__)

def str_to_timedelta(delta_str: str) -> timedelta:
    """
    Converts a string of the format "HH:MM:SS:MS" to a timedelta object

    Checks the correct structure by regex which might be somewhat expensive
    """
    if not re.match(r"^[0-9]{2}:[0-9]{2}:[0-9]{2}[.][0-9]{2}.*$", delta_str):
        if re.match(r"^[0-9]:[0-9]{2}:[0-9]{2}[.][0-9]{2}.*$", delta_str):
            logger.warning(f"timedelta correct '{delta_str}'")
            delta_str = "0" + delta_str
        else:
            logger.error(f"timedelta error '{delta_str}'")
            return timedelta(seconds=0)  # empty timedelta, not sure about that one, timedelta(0) is not falsey
    return timedelta(hours=int(delta_str[0:2]),
                     minutes=int(delta_str[3:5]),
                     seconds=int(delta_str[6:8]),
                     microseconds=int(delta_str[9:11]))


def format_timedelta(gamma: timedelta) -> str:
    return f"{str(gamma.seconds//3600):0>2}:{str(int(gamma.seconds//60%60)):0>2}:{str(gamma.seconds%60):0>2}"


def regex_ffmpeg_encoding(stderr: str) -> dict:
    pattern = r"^(frame=\s*)([0-9]+)\s+(fps=)\s*([0-9]+)\s+(q=)\s*([0-9]*[.]?[0-9]+)\s+(size=)\s*([0-9]+)..\s+(time=)\s*([0-9][0-9]:[0-9][0-9]:[0-9][0-9][.][0-9][0-9])\s+(bitrate=)\s*([0-9]*[.]?[0-9]+)(kbits\/s)\s+(speed=)\s*([0-9]*[.]?[0-9]+)x\s*"
    result = re.search(pattern, stderr)
    if not result:
        return {}
    data = {}
    ints = ['frames', 'fps', 'file_size']
    floats = ['q', 'enc_rate', 'speed']
    data['frames'] = result.group(2)
    data['fps'] = result.group(4)
    data['q'] = result.group(6)
    data['file_size'] = result.group(8)
    data['elapsed'] = result.group(10)  # time of the material that is already encoded, not encoding time
    data['enc_rate'] = result.group(12)
    data['enc_unit'] = result.group(13)
    data['speed'] = result.group(15)
    for key in ints:
        try:
            data[key] = int(data[key])
        except TypeError:
            logger.warning(f"Cannot convert {key} to INT")
    for key in floats:
        try:
            data[key] = float(data[key])
        except TypeError:
            logger.warning(f"Cannot convert {key} to FLOAT")
    try:
        data['elapsed'] = str_to_timedelta(data['elapsed'])
    except TypeError:
        logger.warning("Cannot convert time elapsed into timedelta object")
    return data


def extract_probe(ffmpeg_probe: dict) -> dict:
    for stream in ffmpeg_probe['streams']:
        if stream['codec_type'] == "video":
            raw_fps = int(stream['r_frame_rate'].split("/")[0])
            raw_delta = str_to_timedelta(stream['tags']['DURATION'])
            raw_frames = round(raw_delta.seconds*raw_fps + (raw_delta.microseconds/100)*raw_fps)
            return {
                "time_length": raw_delta,
                "file_size": int(ffmpeg_probe['format']['size'])*1024,  # ffmpeg gives us kbyte
                "fps": int(raw_fps),
                "est_frames": raw_frames
            }
    return {}


def sizeof_fmt(num: int, suffix="B") -> str:
    """
    Human readeable size, stolen from another repo

    https://stackoverflow.com/a/1094933

    https://web.archive.org/web/20111010015624/http://blogmag.net/blog/read/38/Print_human_readable_file_size
    :param int num: size in bytes
    :param str suffix: suffix after size identifier, like GiB
    """
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.2f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.2f} Yi{suffix}"

