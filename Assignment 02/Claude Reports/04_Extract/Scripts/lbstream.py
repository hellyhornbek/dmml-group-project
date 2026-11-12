"""Shared helper: streams listens out of ListenBrainz .tar.zst dumps without unpacking them."""
import re, subprocess, sys, tarfile, shutil, bisect, datetime

LINE_RE = re.compile(rb'^\{"user_id":(\d+),"user_name":"(?:[^"\\]|\\.)*","timestamp":(\d+)')
_BOUNDS = [int(datetime.datetime(y, 1, 1, tzinfo=datetime.timezone.utc).timestamp()) for y in range(1990, 2061)]

def year_of(ts):
    return 1990 + bisect.bisect_right(_BOUNDS, ts) - 1

def iter_lines(paths):
    """Yield every listen line (bytes) from the given .tar.zst files."""
    if not shutil.which('zstd'):
        sys.exit('zstd is missing. On a Mac install it with:  brew install zstd')
    for path in paths:
        proc = subprocess.Popen(['zstd', '-dc', path], stdout=subprocess.PIPE, bufsize=1 << 20)
        tf = tarfile.open(fileobj=proc.stdout, mode='r|')
        for m in tf:
            if m.isfile() and m.name.endswith('.listens'):
                f = tf.extractfile(m)
                for line in f:
                    yield line
        tf.close(); proc.stdout.close(); proc.wait()
