# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.media import (convert_mp4, convert_wav, cut_clip, get_duration,
                         sample_images)
from utils.rpc_server import RPCView
from utils.workspace import local, remote


# Create your views here.
class VideoizeService(RPCView):
    def covert(self, uri, resolution=720):
        filepath = local(uri)
        opath = convert_mp4(filepath)
        return remote(opath)

    def wav(self, uri):
        filepath = local(uri)
        opath = convert_wav(filepath)
        return remote(opath)

    def cut_clip(self, uri, from_ts, duration):
        filepath = local(uri)
        opath = cut_clip(filepath, from_ts, duration)
        return remote(opath)

    def get_duration(self, uri):
        filepath = local(uri)
        return get_duration(filepath)

    def sample_images(self, uri, fps):
        filepath = local(uri)
        images = sample_images(filepath, fps)
        return [remote(image) for image in images]
