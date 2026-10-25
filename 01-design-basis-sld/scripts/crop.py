import sys
from PIL import Image
im = Image.open(sys.argv[1]); W, H = im.size; s = W / 420
x1, y1, x2, y2 = map(float, sys.argv[3:7])
im.crop((int(x1*s), int((297-y2)*s), int(x2*s), int((297-y1)*s))).save(sys.argv[2])
