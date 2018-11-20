'''
Simple tqdm wrapper on urllib.request for downloading large files
Based on https://github.com/tqdm/tqdm/blob/master/examples/tqdm_wget.py
'''
import socket
import urllib.request
import urllib.error
from tqdm import tqdm


class TqdmUpTo(tqdm):
    """
    tqdm instance wrapped for urlretrieve reporthook
    Provides `update_to(n)` which uses `tqdm.update(delta_n)`.
    Inspired by [twine#242](https://github.com/pypa/twine/pull/242),
    [here](https://github.com/pypa/twine/commit/42e55e06).
    """

    def update_to(self, b=1, bsize=1, tsize=None):
        """
        b  : int, optional
            Number of blocks transferred so far [default: 1].
        bsize  : int, optional
            Size of each block (in tqdm units) [default: 1].
        tsize  : int, optional
            Total size (in tqdm units). If [default: None] remains unchanged.
        """
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)  # will also set self.n = b * bsize


def download_file(source, desc=None, retries=5):
    """
    Download a single file from the give source url to a temporary location,
        displaying a progress bar while downloading, then returns the location
        of the downloaded file
    """
    socket.setdefaulttimeout(30)
    attempt = 0
    while attempt < retries:
        try:
            with TqdmUpTo(unit='B', unit_scale=True, unit_divisor=1024,
                          miniters=1, desc=desc) as t:
                file, _ = urllib.request.urlretrieve(source,
                                                     reporthook=t.update_to)
                break
        except (socket.timeout, urllib.error.URLError):
            attempt += 1
            t.write(f'Starting attempt {attempt + 1}')

    if file is None:
        raise RuntimeError(f"Couldn't download {source} in {retries} attempts")

    return file
