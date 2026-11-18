# MIT License
#
# Copyright (c) 2026 Madis Kaal
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import os.path
import PIL.Image

IMAGE_SIZE=320

# resize and convert images given at command line into raw RGB bitmaps
# 
for f in sys.argv[1:]:
  image=PIL.Image.open(f)
  w,h=image.size
  print("%s %dx%d"%(f,w,h))
  hr=IMAGE_SIZE/w
  vr=IMAGE_SIZE/h
  ratio=min(hr,vr)
  if ratio!=1.0:
    nw=int(round(w*ratio,0))
    nh=int(round(h*ratio,0))
    print(" resizing to %dx%d"%(nw,nh))
    image=image.resize((nw,nh),PIL.Image.LANCZOS)
  image=image.convert("RGB")
  pixels=image.load()
  data=bytearray()
  for y in range(image.height):
    for x in range(image.width):
      data.extend(image.getpixel((x,y)))
  d,e=os.path.split(f)
  fe=f.rpartition(".")
  f=os.path.join(d,fe[0]+"."+"rgb")
  with open(f,"wb") as of:
    of.write(data)
  print(" wrote %d bytes to %s"%(len(data),f))
  