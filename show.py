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
from imageproc import imageproc
import tkinter as tk
from PIL import Image,ImageTk

# this tool is for viewing files produced by ibax_test

fn=sys.argv[1]
pixels=open(fn,"rb").read()
image=Image.new("RGB",(320,240))
image.load()
ip=imageproc()

if fn.endswith(".rgb"):
  format=24
elif fn.endswith(".colr8"):
  format=8
elif fn.endswith(".grey8"):
  format=18
elif fn.endswith(".grey4"):
  format=4
elif fn.endswith(".grey2"):
  format=2
elif fn.endswith(".bw") or fn.endswith(".grey1"):
  format=1
else:
  sys.exit(1)
  
for y in range(image.height):
  for x in range(image.width):
    if format==24:
      image.putpixel((x,y),
        (pixels[y*image.width*3+x*3],
        pixels[y*image.width*3+x*3+1],
        pixels[y*image.width*3+x*3+2]))
    elif format==8:
      p=pixels[y*image.width+x]
      image.putpixel((x,y),ip.map_to_rgb(p))
    elif format==18:
      p=pixels[y*image.width+x]
      image.putpixel((x,y),(p,p,p))
    elif format==4:
      p=pixels[y*image.width//2+x//2]
      if not x&1:
        p=(p>>4)*17
      else:
        p=(p&15)*17
      image.putpixel((x,y),(p,p,p))
    elif format==2:
      p=pixels[y*image.width//4+x//4]
      if x&3==0:
        p=(p>>6)*83
      elif x&3==1:
        p=((p>>4)&3)*83
      elif x&3==2:
        p=((p>>2)&3)*83
      elif x&3==3:
        p=(p&3)*83
      image.putpixel((x,y),(p,p,p))
    elif format==1:
      p=pixels[y*image.width//8+x//8]
      if x&7==7:
        p=255 if p&0x01 else 0
      elif x&7==6:
        p=255 if p&0x02 else 0
      elif x&7==5:
        p=255 if p&0x04 else 0
      elif x&7==4:
        p=255 if p&0x08 else 0
      elif x&7==3:
        p=255 if p&0x10 else 0
      elif x&7==2:
        p=255 if p&0x20 else 0
      elif x&7==1:
        p=255 if p&0x40 else 0
      elif x&7==0:
        p=255 if p&0x80 else 0
      image.putpixel((x,y),(p,p,p))

win=tk.Tk()
tkimg=ImageTk.PhotoImage(image)
frame=tk.Frame(win)
frame.grid(row=0,column=0)
tk.Label(frame,image=tkimg).grid(row=0,column=0)
win.mainloop()

