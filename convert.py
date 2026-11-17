import sys
import os.path
import PIL.Image

IMAGE_SIZE=320

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
  