"""Paper figures for the NTLFlowLyzer IAT leak, built from files in this folder.
  fig_code_calculate_IAT.png  the faulty function at upstream commit d99cd53, with one of its callers
  fig_A_combined.png          Wireshark screenshot (left) + published BCCC rows (right), matching values boxed
Run: python3 make_figures.py   (needs Pillow; reads ~/Desktop/NTLFlowLyzer for the source code)"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.expanduser("~/Desktop/NTLFlowLyzer/NTLFlowLyzer/features")
MONO = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 19)
MONO_B = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 19)
SANS = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
SANS_B = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
RED, INK, GREY = (200, 30, 30), (25, 25, 25), (95, 95, 95)

# ---------------------------------------------------------------- code panel
def code_block(path, first, last, marks):
    """marks: {line_no: (fill colour, note)}; returns (header, [(no, text, fill, note)])."""
    lines = open(path).read().split("\n")
    return [(n, lines[n - 1], *marks.get(n, (None, ""))) for n in range(first, last + 1)]


YEL, PINK = (255, 243, 176), (255, 214, 214)
blocks = [
    ("NTLFlowLyzer/features/utils.py  (upstream commit d99cd53)", code_block(f"{SRC}/utils.py", 20, 27, {
        22: (YEL, "skipped when the direction holds exactly one packet"),
        23: (YEL, ""), 24: (YEL, ""), 25: (YEL, ""),
        27: (PINK, "returns [packet timestamp], not [] (0 packets -> [])")})),
    ("NTLFlowLyzer/features/IAT_related.py  (one of the callers)", code_block(f"{SRC}/IAT_related.py", 11, 17, {
        14: (PINK, "times = [t], with t ~ 1.5e9 (Unix epoch seconds)"),
        16: (PINK, "mean([t]) = t: the absolute capture time becomes the feature")})),
]
lh, pad, gutter = 30, 24, 60
code_w = int(max(MONO.getlength(t) for _, b in blocks for _, t, _, _ in b)) + 40
note_w = int(max(SANS.getlength(n) for _, b in blocks for *_, n in b)) + 40
W = pad + gutter + code_w + note_w + pad
H = pad + sum(lh * (len(b) + 2) for _, b in blocks) + pad
im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
y = pad
for title, rows in blocks:
    d.text((pad, y), title, font=SANS_B, fill=INK); y += lh + 6
    for no, text, fill, note in rows:
        if fill:
            d.rectangle([pad + gutter - 6, y - 2, pad + gutter + code_w, y + lh - 4], fill=fill)
        d.text((pad, y), f"{no:>3}", font=MONO, fill=(150, 150, 150))
        d.text((pad + gutter, y), text, font=MONO, fill=INK)
        if note:
            d.text((pad + gutter + code_w + 20, y + 2), "<- " + note, font=SANS, fill=RED if fill == PINK else GREY)
        y += lh
    y += lh - 6
im.save(f"{HERE}/fig_code_calculate_IAT.png")
print("fig_code_calculate_IAT.png", im.size)

# ---------------------------------------------------------------- Figure A, combined
left = Image.open(f"{HERE}/wire_A_left_cic2018_pcap.png").convert("RGB")
txt = open(f"{HERE}/published_bccc_port59823_rows_transposed.txt").read().rstrip("\n").split("\n")
T = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 22)
tl = 32
rw = int(max(T.getlength(l) for l in txt)) + 50
right = Image.new("RGB", (rw, tl * len(txt) + 40), "white"); rd = ImageDraw.Draw(right)
boxes_r = []
for i, l in enumerate(txt):
    yy = 20 + i * tl
    rd.text((25, yy), l, font=T, fill=INK)
    if "IAT" in l and "1519330475.230912" in l:
        x0 = 25 + T.getlength(l[:l.index("1519330475.230912")])
        boxes_r.append((x0 - 6, yy - 3, x0 + T.getlength("1519330475.230912") + 6, yy + tl - 5))
    if l.startswith("label"):
        x0 = 25 + T.getlength(l[:l.rindex("SQL_Injection")])
        rd.rectangle([x0 - 6, yy - 3, x0 + T.getlength("SQL_Injection") + 6, yy + tl - 5], outline=(240, 140, 0), width=3)
for b in boxes_r:
    rd.rectangle(b, outline=RED, width=3)
# column headings of the transposed table: 0 = the 12-packet flow, 1 = the one-packet ghost flow
gap, head = 90, 110
SUB = ["column 0: the 12-packet flow", "column 1: the trailing ACK, split off as a one-packet flow"]
CAP = ["Red: IAT max / min / total of the one-packet flow,", "identical to the arrival time of frame 45048 (red, left).",
       "Orange: the fragment is labelled SQL_Injection."]
textw = max(SANS_B.getlength("Published BCCC-CSE-CIC-IDS2018 rows for this connection"),
            *(SANS.getlength(t) for t in SUB + CAP))
CW = left.width + gap + int(max(right.width, textw)) + 30
CH = head + max(left.height, right.height) + 70
c = Image.new("RGB", (CW, CH), "white"); cd = ImageDraw.Draw(c)
c.paste(left, (0, head)); ry = head + 120
c.paste(right, (left.width + gap, ry))
cd.text((0, 20), "Original CSE-CIC-IDS2018 capture (Wireshark), victim 172.31.69.28, connection :59823",
        font=SANS_B, fill=INK)
cd.text((0, 56), "Frame 45048, the server's final ACK, arrives at 1519330475.230912 s", font=SANS, fill=GREY)
rx = left.width + gap
cd.text((rx, 20), "Published BCCC-CSE-CIC-IDS2018 rows for this connection", font=SANS_B, fill=INK)
for i, t in enumerate(SUB):
    cd.text((rx, 56 + 26 * i), t, font=SANS, fill=GREY)
# boxes on the screenshot: Time of frame 45048 in the packet list, and the Epoch Arrival Time line
lb = [(81, 318, 241, 336), (40, 593, 408, 612)]
for x0, y0, x1, y1 in lb:
    cd.rectangle([x0, head + y0, x1, head + y1], outline=RED, width=3)
for i, t in enumerate(CAP):
    cd.text((rx, ry + right.height + 20 + 28 * i), t, font=SANS, fill=(240, 140, 0) if t.startswith("Orange") else RED)
c.save(f"{HERE}/fig_A_combined.png")
print("fig_A_combined.png", c.size)
