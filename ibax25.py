import sys
import os.path
import math
import struct
import random
import tkinter as tk
from tkinter import filedialog,font
from PIL import Image,ImageTk
from imageproc import imageproc
from lz_compress import lz_compress
from collections import deque

IMAGE_WIDTH = 320
IMAGE_HEIGHT = 240
RADIO_BITRATE = 9600

AX25HEADER = bytearray((
  ord('C')<<1,
  ord('Q')<<1,
  ord(' ')<<1,
  ord(' ')<<1,
  ord(' ')<<1,
  ord(' ')<<1,
  0,
  ord('M')<<1,
  ord('S')<<1,
  ord('T')<<1,
  ord('1')<<1,
  ord(' ')<<1,
  ord(' ')<<1,
  0x81,
  0x03,
  0xf0))

class App(tk.Tk):

  def __init__(self, *args,**kwargs):
    tk.Tk.__init__(self, *args, **kwargs)
    #self.geometry("1000x600")

    self.processor=imageproc()
    self.result_bpp=8
    self.in_color=True
    self.image_id=0
    self.received_image_id=None
    self.remote_text=""
    
    self.send_queue=deque()
    self.receive_queue=deque()
    
    if IMAGE_WIDTH&7:
      print("Image width must be multiple of 8")
      sys.exit(1)
      
    if "Comic Sans MS" in font.families():
      self.font=font.Font(family="Comic Sans MS",size=10,weight="normal")
    elif "Comic Neue" in font.families():
      self.font=font.Font(family="Comic Neue",size=10,weight="normal")
    else:
      self.font=font.Font(family="Helvetica",size=10,weight="normal")
      
    self.controls = tk.Frame(self,relief=tk.FLAT)
    self.controls.grid(row=0,column=0,sticky="new",padx=10)
    self.content = tk.Frame(self,relief=tk.FLAT)
    self.content.grid(row=1,column=0,sticky="new",padx=10)
    
    tk.Button(self.controls,text="Load...",command=self.open_image
      ).grid(row=0,column=0)
    tk.Button(self.controls,text="8 bit",command=self.convert_to_8bit
      ).grid(row=0,column=1,sticky="W")
    tk.Button(self.controls,text="8 bit dithered",command=self.convert_to_8bit_dithered
      ).grid(row=1,column=1,sticky="W")
    tk.Button(self.controls,text="8 bit grey",command=self.convert_to_8bit_greyscale
      ).grid(row=0,column=2,sticky="W")
    tk.Button(self.controls,text="4 bit greyscale",command=self.convert_to_4bit_greyscale
      ).grid(row=0,column=3,sticky="W")
    tk.Button(self.controls,text="4 bit grey d",command=self.convert_to_4bit_greyscale_dithered
      ).grid(row=1,column=3,sticky="W")
    tk.Button(self.controls,text="2 bit greyscale",command=self.convert_to_2bit_greyscale
      ).grid(row=0,column=4,sticky="W")
    tk.Button(self.controls,text="2 bit grey d",command=self.convert_to_2bit_greyscale_dithered
      ).grid(row=1,column=4,sticky="W")
    tk.Button(self.controls,text="1 bit",command=self.convert_to_1bit
      ).grid(row=0,column=5,sticky="W")
    tk.Button(self.controls,text="1 bit dithered",command=self.convert_to_1bit_dithered
      ).grid(row=1,column=5,sticky="W")
    tk.Button(self.controls,text="Transmit image",command=self.transmit_image
      ).grid(row=0,column=7,sticky="w")
    self.packetloss=tk.IntVar()
    self.packetloss.set(0)
    tk.Label(self.controls,text="Packet loss%"
      ).grid(row=1,column=6,sticky="w")
    tk.Entry(self.controls,textvariable=self.packetloss,width=6
      ).grid(row=1,column=7,sticky="w")
    self.source_image_name=""      
    self.source_image=Image.new("RGB",(IMAGE_WIDTH,IMAGE_HEIGHT))
    self.result_image=Image.new("RGB",(IMAGE_WIDTH,IMAGE_HEIGHT))
    self.remote_image=Image.new("RGB",(IMAGE_WIDTH,IMAGE_HEIGHT))
    self.source_tkimage=ImageTk.PhotoImage(self.source_image)
    self.result_tkimage=ImageTk.PhotoImage(self.result_image)
    self.remote_tkimage=ImageTk.PhotoImage(self.remote_image)   
    self.source_canvas=tk.Canvas(self.content,width=IMAGE_WIDTH+36,
      height=IMAGE_HEIGHT+123,background="white",bd=0, highlightthickness=0)
    self.source_canvas.grid(row=0,column=0,sticky="nw",padx=20,pady=20)
    self.result_canvas=tk.Canvas(self.content,width=IMAGE_WIDTH+36,
      height=IMAGE_HEIGHT+123,background="white",bd=0, highlightthickness=0)
    self.result_canvas.grid(row=0,column=1,sticky="nw",padx=20,pady=20)    
    self.remote_canvas=tk.Canvas(self.content,width=IMAGE_WIDTH+36,
      height=IMAGE_HEIGHT+123,background="white",bd=0,highlightthickness=0)
    self.remote_canvas.grid(row=0,column=2,sticky="nw",padx=20,pady=20)  
    self.source_canvas.create_image(18,18,image=self.source_tkimage,anchor=tk.NW)
    self.result_canvas.create_image(18,18,image=self.result_tkimage,anchor=tk.NW)
    self.remote_canvas.create_image(18,18,image=self.remote_tkimage,anchor=tk.NW)
    self.winx=0
    self.winy=0
    self.load_state()
    self.geometry("+%d+%d"%(self.winx,self.winy))
    self.update_idletasks()
    self.resizable(False, False)
    self.protocol("WM_DELETE_WINDOW", self.on_exit)

  def on_exit(self):
    self.save_state()
    self.destroy()

  def save_state(self):
    self.winx=self.winfo_x()
    self.winy=self.winfo_y()
    with open(".ibax25.state","wt") as f:
      f.write("file=%s\n"%self.source_image_name)
      f.write("winx=%d\n"%self.winfo_x())
      f.write("winy=%d\n"%self.winfo_y())

  def load_state(self):
    if not os.path.exists(".ibax25.state"):
      return
    for l in open(".ibax25.state","rt").readlines():
      p=l.partition("=")
      if p[1]=="=":
        k=p[0].strip().lower()
        v=p[2].partition("#")[0].strip()
        if k=="file" and os.path.exists(v):
          self.load_image(v)
        elif k=="winx":
          self.winx=int(v)
        elif k=="winy":
          self.winy=int(v)
    
  def open_image(self):    
    f=filedialog.askopenfilename(initialdir=".")
    if f:
      self.load_image(f)
      
  def load_image(self,f):
    self.source_image_name=f
    if f.lower().endswith(".rgb"):
      pixels=bytearray(open(f,"rb").read())
      image=Image.frombytes("RGB",(320,len(pixels)//3//320),pixels)
    else:
      image=Image.open(f)
    hr=IMAGE_WIDTH/image.size[0]
    vr=IMAGE_HEIGHT/image.size[1]
    ratio=min(hr,vr)
    nw=int(image.size[0]*ratio)
    nh=int(image.size[1]*ratio)
    image=image.resize((nw,nh)).convert("RGB")
    self.image_tint=self.processor.nearest_web_safe_color((255,255,255))
    square=Image.new("RGB",(IMAGE_WIDTH,IMAGE_HEIGHT))
    x=(IMAGE_WIDTH-nw)//2
    y=(IMAGE_HEIGHT-nh)//2
    square.paste(image,(x,y))
    self.source_image=square
    self.source_tkimage=ImageTk.PhotoImage(self.source_image)
    self.source_canvas.delete("ALL")
    self.source_canvas.create_image(18,18,image=self.source_tkimage,anchor=tk.NW)
    self.source_canvas.create_text(18,IMAGE_HEIGHT+30,
      text="RGB %d bytes"%(IMAGE_HEIGHT*IMAGE_WIDTH*3),anchor=tk.NW,font=self.font)
    self.convert_to_8bit()
    
  def txcalc(self,rowbytes):
    maxpayload=350
    frames=math.ceil(rowbytes/maxpayload)
    flist=[rowbytes//frames]*(frames-1)
    flist.append(rowbytes-(rowbytes//frames*(frames-1)))
    txtime=0
    for f in flist:
      bits=int((f+16+16+2)*8*1.03)
      txtime+=(1/RADIO_BITRATE)*bits
    return frames,txtime

  def transmit_image(self):
    pixels=self.result_image.load()
    w,h=self.result_image.size
    for y in range(h):
      if not y or random.random()<0.01:
        line=bytearray(AX25HEADER)
        line.extend(struct.pack("<BHHB",self.image_id,0,0,0))
        line.extend(os.path.basename(self.source_image_name).encode('utf8'))
        self.send_queue.append(line)

      line=bytearray(AX25HEADER)
      format=self.result_bpp
      if self.in_color:
        format|=0x40
      line.extend(struct.pack("<BHHB",self.image_id,y,0,format))
      for x in range(w):
        c=pixels[x,y]
        if self.result_bpp==8:
          if self.in_color:
            line.append(self.processor.map_to_8bit(c))
          else:
            line.append(c[0])
        elif self.result_bpp==4:
          if not (x&1):
            line.append(((pixels[x,y][0]//17)<<4) | (pixels[x+1,y][1]//17))
        elif self.result_bpp==2:
          if (x&3)==0:
            b=(pixels[x,y][0]//85)<<6
            b|=(pixels[x+1,y][0]//85)<<4
            b|=(pixels[x+2,y][0]//85)<<2
            b|=(pixels[x+3,y][0]//85)            
            line.append(b)
        elif self.result_bpp==1:
          if (x&7)==0:
            b=0
            for i in range(8):
              if pixels[x+i,y][0]:
                b|=(0x80>>i)
            line.append(b)
      self.send_queue.append(line)    
    self.after(0,self.transmit_line)

  def transmit_line(self):
    if len(self.receive_queue):
      self.after(0,self.receive_line)
    if not len(self.send_queue):
      return
    line=self.send_queue.popleft()
    self.receive_queue.append(line)
    txtime=int((1/RADIO_BITRATE)*1000*((len(line)+4)*8)*1.03)
    self.after(txtime,self.transmit_line)

  def receive_line(self):
    if len(self.receive_queue):
      line=self.receive_queue.popleft()
      if len(line)>16+6:
        if line[13]&15==1:
          if random.random()*100<self.packetloss.get():
            return
          line=line[16:]
          imageid,y,x,format=struct.unpack("<BHHB",line[0:6])
          if imageid!=self.received_image_id:
            self.received_image_id=imageid
            self.remote_image=Image.new("RGB",(IMAGE_WIDTH,IMAGE_HEIGHT))
          pixels=self.remote_image.load()
          in_color=True if format&64 else False
          bpp=format&63
          for b in line[6:]:
            if bpp==0:
              self.remote_text=line[6:].decode('utf8')      
            elif bpp==8:
              if in_color:
                pixels[x,y]=self.processor.map_to_rgb(b)
              else:
                pixels[x,y]=self.processor.greyscale_to_rgb(b)
              x+=1
            elif bpp==4:
              pixels[x,y]=self.processor.greyscale_to_rgb((b>>4)*17)
              pixels[x+1,y]=self.processor.greyscale_to_rgb((b&15)*17)
              x+=2
            elif bpp==2:
              pixels[x,y]=self.processor.greyscale_to_rgb((b>>6)*85)
              pixels[x+1,y]=self.processor.greyscale_to_rgb(((b>>4)&3)*85)
              pixels[x+2,y]=self.processor.greyscale_to_rgb(((b>>2)&3)*85)
              pixels[x+3,y]=self.processor.greyscale_to_rgb((b&3)*85)
              x+=4
            elif bpp==1:
              for i in range(8):
                pixels[x+i,y]=(255,255,255) if b&(0x80>>i) else (0,0,0)
              x+=8
          self.remote_canvas.delete("all")
          self.remote_canvas.create_text(18,IMAGE_HEIGHT+30,
              text=self.remote_text,anchor=tk.NW,font=self.font)
          self.remote_tkimage=ImageTk.PhotoImage(self.remote_image)
          self.remote_canvas.create_image(18,18,image=self.remote_tkimage,anchor=tk.NW)
      self.update_idletasks()
      
  def update_result(self,bpp,in_color=True):
    self.result_bpp=bpp
    self.in_color=in_color
    self.image_id=(self.image_id+1)%256
    self.send_queue.clear()
    self.result_tkimage=ImageTk.PhotoImage(self.result_image)
    self.result_canvas.delete("all")
    self.result_canvas.create_image(18,18,image=self.result_tkimage,anchor=tk.NW)
    
    w,h=self.result_image.size
    rowbytes=w*bpp/8
    f,t=self.txcalc(rowbytes)
    self.result_canvas.create_text(18,IMAGE_HEIGHT+30,
      text="%d bpp %d bytes, %d frames, %d seconds"%(bpp,rowbytes*h,
      f*h,round(t*h,0)),anchor=tk.NW,font=self.font)

    pixels=self.result_image.load()
    total=0
    tt=0
    frames=0
    for y in range(h):
      line=bytearray()
      for x in range(w):
        c=pixels[x,y]
        if bpp==8:
          if in_color:
            line.append(self.processor.map_to_8bit(c))
          else:
            line.append(c[0])
        elif bpp==4:
          if not (x&1):
            line.append((c[0]&0xf0) | (pixels[x+1,y][0]>>4))
        elif bpp==2:
          if (x&3)==0:
            b=self.processor.truncate_to_2bit_greyscale(c)[0]
            b|=self.processor.truncate_to_2bit_greyscale(pixels[x+1,y])[0]>>2
            b|=self.processor.truncate_to_2bit_greyscale(pixels[x+2,y])[0]>>4
            b|=self.processor.truncate_to_2bit_greyscale(pixels[x+3,y])[0]>>6            
            line.append(b)
        elif bpp==1:
          if (x&7)==0:
            b=0
            for i in range(8):
              if pixels[x+i,i][0]:
                b|=(0x80>>i)
            line.append(b)
      r=lz_compress(line)
      a,b=self.txcalc(len(r))
      frames+=a
      tt+=b
      total+=(len(r)-3)
    self.result_canvas.create_text(18,IMAGE_HEIGHT+50,
      text="LZ %d bytes, %d frames, %d seconds"%(total,frames,round(tt,0)),anchor=tk.NW,font=self.font)
      
  def convert(self,reduce,render):
    sourcepixels=self.source_image.load()
    resultpixels=self.result_image.load()
    width,height=self.source_image.size
    for y in range(height):
      for x in range(width):
        c=sourcepixels[x,y]
        ci=reduce(c)                 # self.processor.map_to_8bit(c)
        resultpixels[x,y]=render(ci) #self.processor.map_to_rgb(ci)

  def convert_and_dither(self,reduce,render):
    pixels=self.result_image.load()
    width,height=self.result_image.size
    for y in range(height):
      for x in range(width):
          old=pixels[x,y]
          r,g,b=reduce(old) # self.processor.nearest_web_safe_color(old)
          r=max(0,min(r,255))
          g=max(0,min(g,255))
          b=max(0,min(b,255))
          pixels[x,y]=render((r,g,b))
          re=old[0]-r # errors in each color channel
          ge=old[1]-g
          be=old[2]-b
          # distribute error to neighbours with F-S coefficients
          if x + 1 < width:
              r,g,b=pixels[x+1,y]
              r=max(0,min(r+re*7//16,255))
              g=max(0,min(g+ge*7//16,255))
              b=max(0,min(b+be*7//16,255))
              pixels[x+1,y]=(r,g,b)
          if y + 1 < height:
              if x > 0:
                r,g,b=pixels[x-1,y+1]
                r=max(0,min(r+re*3//16,255))
                g=max(0,min(g+ge*3//16,255))
                b=max(0,min(b+be*3//16,255))
                pixels[x-1,y+1]=(r,g,b)

              r,g,b=pixels[x,y+1]
              r=max(0,min(r+re*5//16,255))
              g=max(0,min(g+ge*5//16,255))
              b=max(0,min(b+be*5//16,255))
              pixels[x,y+1]=(r,g,b)
              
              if x + 1 < width:
                r,g,b=pixels[x+1,y+1]
                r=max(0,min(r+re*1//16,255))
                g=max(0,min(g+ge*1//16,255))
                b=max(0,min(b+be*1//16,255))
                pixels[x+1,y+1]=(r,g,b)

  def convert_to_8bit(self):
    self.convert(
      self.processor.map_to_8bit,
      self.processor.map_to_rgb)
    self.update_result(8,True)

  def convert_to_8bit_dithered(self):
    self.result_image=self.source_image.copy()
    self.convert_and_dither(
      self.processor.nearest_web_safe_color,
      lambda c : c)
    self.update_result(8,True)

  def convert_to_8bit_greyscale(self):
    self.convert(
      self.processor.map_to_8bit_greyscale,
      self.processor.greyscale_to_rgb)
    self.update_result(8,False)

  def convert_to_4bit_greyscale(self):
    self.convert(
      lambda c: self.processor.truncate_to_4bit_greyscale(c)[0],
      lambda c : (c,c,c))
    self.update_result(4,False)

  def convert_to_4bit_greyscale_dithered(self):
    self.convert(
      self.processor.map_to_8bit_greyscale,
      self.processor.greyscale_to_rgb)
    self.convert_and_dither(
      self.processor.truncate_to_4bit_greyscale,
      lambda c : c)
    self.update_result(4,False)

  def convert_to_2bit_greyscale(self):
    self.convert(
      lambda c: self.processor.truncate_to_2bit_greyscale(c)[0],
      lambda c : (c,c,c))
    self.update_result(2,False)

  def convert_to_2bit_greyscale_dithered(self):
    self.convert(
      self.processor.map_to_8bit_greyscale,
      self.processor.greyscale_to_rgb)
    self.convert_and_dither(
      self.processor.truncate_to_2bit_greyscale,
      lambda c : c)
    self.update_result(2,False)
  
  def convert_to_1bit(self):
    self.convert(
      lambda c : 0 if self.processor.map_to_8bit_greyscale(c)<128 else 1,
      lambda c : (255,255,255) if c else (0,0,0))
    self.update_result(1,False)
    
  def convert_to_1bit_dithered(self):
    self.convert(
      self.processor.map_to_8bit_greyscale,
      self.processor.greyscale_to_rgb)
    self.convert_and_dither(
      self.processor.truncate_to_1bit_greyscale,
      lambda c : c)
    self.update_result(1,False)
    

app = App()
app.mainloop()
