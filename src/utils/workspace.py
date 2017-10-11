import os
import shutil
import tempfile
import urllib
import urlparse
from contextlib import contextmanager
from os.path import basename, exists, join, splitext

from django.core.files import File
from django.core.files.storage import DefaultStorage


@contextmanager
def tmp(tmpdir="./tmp"):
    if not exists(tmpdir):
        os.makedirs(tmpdir)

    path = tempfile.mkdtemp(dir="./tmp")
    yield path

    if exists(path):
        shutil.rmtree(path)


def cache(outpath):
    def x(func):
        def inner(*args, **kwargs):
            path = outpath.format(*args, **kwargs)
            mode = 'folder' if path.endswith('/') else 'file'

            if mode == "folder":
                opath = './tmp/%s/' % path.split('/')[-2]
            else:
                opath = './tmp/%s' % basename(path)

            if exists(opath):
                return opath

            with tmp() as tmpfolder:
                tmppath = join(tmpfolder, basename(opath))
                if mode == "folder" and not exists(tmppath):
                    os.makedirs(tmppath)

                final_path = func(*args, opath=tmppath, **kwargs)

                if final_path == tmppath:
                    # HINT: https://stackoverflow.com/questions/7487307/oserror-directory-not-empty-raised-how-to-fix
                    shutil.move(final_path, opath)
                    return opath

                return final_path

        return inner

    return x


@cache("{0}")
def _local(name, url, opath):
    urllib.urlretrieve(url, opath)
    return opath


def _split_url(url):
    return splitext(basename(urlparse.urlsplit(url).path))


def local(file_or_url):
    if isinstance(file_or_url, File):
        return _local(file_or_url.name, file_or_url.url)

    return _local(os.path.basename(file_or_url), file_or_url)


def remote(filepath_or_url):
    if not os.path.exists(filepath_or_url):
        # should be url
        filepath = local(filepath_or_url)
    else:
        filepath = filepath_or_url

    path, ext = os.path.splitext(filepath)

    with open(filepath, 'rb') as ifile:
        storage = DefaultStorage()
        return storage.url(storage.save('{}.{}'.format(path, ext), File(ifile)))
