import io, sys, zipfile, urllib.request, urllib.parse
B = "https://cse-cic-ids2018.s3.ca-central-1.amazonaws.com/"
class HttpFile(io.RawIOBase):
    def __init__(s, url):
        s.url, s.pos = url, 0
        s.size = int(urllib.request.urlopen(urllib.request.Request(url, method="HEAD")).headers["Content-Length"])
    def seekable(s): return True
    def readable(s): return True
    def tell(s): return s.pos
    def seek(s, off, wh=0):
        s.pos = off if wh == 0 else s.pos + off if wh == 1 else s.size + off; return s.pos
    def readinto(s, b):
        n = min(len(b), s.size - s.pos)
        if n <= 0: return 0
        r = urllib.request.Request(s.url, headers={"Range": f"bytes={s.pos}-{s.pos+n-1}"})
        d = urllib.request.urlopen(r).read(); b[:len(d)] = d; s.pos += len(d); return len(d)
def open_day(day):
    f = io.BufferedReader(HttpFile(B + urllib.parse.quote(f"Original Network Traffic and Log data/{day}/pcap.zip")), 1 << 20)
    return zipfile.ZipFile(f)
if __name__ == "__main__":
    z = open_day(sys.argv[1])
    for i in z.infolist(): print(i.compress_type, i.file_size, i.compress_size, i.filename)
