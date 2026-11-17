#pragma once

#include <stdint.h>

#define MAX_WIDTH 320

class IBAX25
{
uint16_t w,h;
uint8_t bpp;
uint8_t l0[MAX_WIDTH*3],
        l1[MAX_WIDTH*3];

protected:

  virtual uint16_t imgread(uint32_t offset,uint8_t *buf,uint16_t nbytes) = 0;
  virtual uint16_t imgwrite(uint32_t offset,uint8_t *buf,uint16_t nbytes) = 0; 

  static void nearest_web_safe_color(uint8_t *color,uint8_t* websafecolor)
  {
    uint16_t r,g,b;
    r=color[0];
    g=color[1];
    b=color[2];
    r+=25;
    r=r-(r%51);
    g+=25;
    g=g-(g%51);
    b+=25;
    b=b-(b%51);
    websafecolor[0]=r;
    websafecolor[1]=g;
    websafecolor[2]=b;
  }

  static uint8_t rgb_to_col(uint8_t r,uint8_t g,uint8_t b)
  {
    uint16_t ri,gi,bi;
    ri=((uint16_t)r+25)/51;
    gi=((uint16_t)g+25)/51;
    bi=((uint16_t)b+25)/51;
    return ri*36+gi*6+bi;
  }
  
  static uint8_t rgb_to_grey(uint8_t r,uint8_t g,uint8_t b)
  {
    return ((uint32_t)r*299+(uint32_t)g*587+(uint16_t)b*114)/1000;
  }

  static uint8_t grey_to_grey4(uint8_t i)
  {
    if (i<9)   return 0;
    if (i<26)  return 1;
    if (i<43)  return 2;
    if (i<60)  return 3;
    if (i<77)  return 4;
    if (i<94)  return 5;
    if (i<111) return 6;
    if (i<128) return 7;
    if (i<145) return 8;
    if (i<162) return 9;
    if (i<179) return 10;
    if (i<196) return 11;
    if (i<213) return 12;
    if (i<230) return 13;
    if (i<247) return 14;
    return 15;
  }
  
    
  static uint8_t grey_to_grey2(uint8_t i)
  {
    if (i<43)  return 0;
    if (i<128) return 1;
    if (i<213) return 2;
    return 3;
  }
        
  static uint8_t grey_to_bw(uint8_t c)
  {
    return (c<128)?0:1;
  }
  
  static uint8_t bw_reducer(uint8_t c)
  {
    return (c<128)?0:255;
  }
  
  static uint8_t greyscale2_reducer(uint8_t c)
  {
    if (c<43)
      return 0;
    if (c>=213)
      return 255;
    if (c>128)
      return 170;
    return 86;
  }

  static uint8_t greyscale4_reducer(uint8_t c)
  {
    if (c<9) return 0;
    if (c<26) return 9+(26-9)/2;
    if (c<43) return 26+(43+26)/2;
    if (c<60) return 43+(60-43)/2;
    if (c<77) return 60+(77-60)/2;
    if (c<94) return 77+(94-77)/2;
    if (c<111) return 94+(111-94)/2;
    if (c<128) return 111+(128-111)/2;
    if (c<145) return 128+(145-128)/2;
    if (c<162) return 145+(162-145)/2;
    if (c<179) return 162+(179-162)/2;
    if (c<196) return 179+(196-179)/2;
    if (c<213) return 196+(312-196)/2;
    if (c<230) return 213+(230-213)/2;
    if (c<247) return 230+(247-230)/2;
    return 247+(255-247)/2;
  }
    
  static uint8_t limit(int16_t c)
  {
    if (c<0)
      c=0;
    if (c>255)
      c=255;
    return c;
  }
    
public:

  IBAX25() : w(0),h(0),bpp(24) {}
  IBAX25(uint16_t width,uint16_t height,uint8_t bitsperpixel=24) : w(width),h(height),bpp(bitsperpixel) {}

  uint32_t bitmapsize()
  {
    return ((w*h*bpp)/8);
  }
    
  void set_size(uint16_t width,uint16_t height,uint8_t bitsperpixel=24)
  {
    w=width;
    h=height;
    bpp=bitsperpixel;
  }
  
  uint8_t rgb_to_greyscale8()
  {
    uint8_t *grey,*rgb;
    if (bpp!=24)
      return 1;
    for (uint16_t y=0;y<h;y++) {
      imgread(y*w*3,l0,w*3);
      grey=rgb=l0;
      for (uint16_t x=0;x<w;x++) {
        *grey++=rgb_to_grey(rgb[0],rgb[1],rgb[2]);
        rgb+=3;
      }
      imgwrite(y*w,l0,w);
    }
    bpp=8;
    return 0;
  }
  


  void color_dither()
  {
    uint8_t old[3],*ptr,*pp;
    int16_t rerr,gerr,berr;
    imgread(0,l1,w*3);
    for (uint16_t y=0;y<h;y++) {
      memcpy(l0,l1,w*3);
      if (y<(h-1))
        imgread((y+1)*w*3,l1,w*3);
      ptr=l0;
      for (uint16_t x=0;x<w;x++) {
        old[0]=ptr[0];
        old[1]=ptr[1];
        old[2]=ptr[2];
        nearest_web_safe_color(old,ptr);
        rerr=(int16_t)old[0]-(int16_t)ptr[0];
        gerr=(int16_t)old[1]-(int16_t)ptr[1];
        berr=(int16_t)old[2]-(int16_t)ptr[2];
        ptr+=3;
        if ((x+1)<w) {
          pp=l0+(x+1)*3;
          pp[0]=limit((int16_t)pp[0]+((rerr*7)>>4));
          pp[1]=limit((int16_t)pp[1]+((gerr*7)>>4));
          pp[2]=limit((int16_t)pp[2]+((berr*7)>>4));
        }
        if ((y+1)<h) {
          if (x>0) {
            pp=l1+(x-1)*3;
            pp[0]=limit((int16_t)pp[0]+((rerr*3)>>4));
            pp[1]=limit((int16_t)pp[1]+((gerr*3)>>4));
            pp[2]=limit((int16_t)pp[2]+((berr*3)>>4));            
          }
          pp=l1+x*3;
          pp[0]=limit((int16_t)pp[0]+((rerr*5)>>4));
          pp[1]=limit((int16_t)pp[1]+((gerr*5)>>4));
          pp[2]=limit((int16_t)pp[2]+((berr*5)>>4));            
          if ((x+1)<w) {
            pp=l1+(x+1)*3;
            pp[0]=limit((int16_t)pp[0]+(rerr>>4));
            pp[1]=limit((int16_t)pp[1]+(gerr>>4));
            pp[2]=limit((int16_t)pp[2]+(berr>>4));            
          }
        }
      }
      imgwrite(y*w*3,l0,w*3);
    }
  }
  
  void grey_dither(uint8_t (*reducer)(uint8_t))
  {
    uint8_t *grey,old,reduced;
    int16_t err;
    imgread(0,l1,w);
    for (uint16_t y=0;y<h;y++) {
      memcpy(l0,l1,w);
      if (y<(h-1))
        imgread((y+1)*w,l1,w);
      grey=l0;
      for (uint16_t x=0;x<w;x++) {
        old=*grey;
        reduced=reducer(old);
        err=(int16_t)old-(int16_t)reduced;
        *grey++=reduced;
        if ((x+1)<w) {
          l0[x+1]=limit((int16_t)l0[x+1]+((err*7)>>4));
        }
        if ((y+1)<h) {
          if (x>0) {
            l1[x-1]=limit((int16_t)l1[x-1]+((err*3)>>4));
          }
          l1[x]=limit((int16_t)l1[x]+((err*5)>>4));
          if ((x+1)<w) {
            l1[x+1]=limit((int16_t)l1[x+1]+(err>>4));
          }
        }
      }
      imgwrite(y*w,l0,w);
    }
  }

  uint8_t rgb_to_color8()
  {
    uint8_t *color,*rgb;
    if (bpp!=24)
      return 1;
    color_dither();
    for (uint16_t y=0;y<h;y++) {
      imgread(y*w*3,l0,w*3);
      color=rgb=l0;
      for (uint16_t x=0;x<w;x++) {
        *color++=rgb_to_col(rgb[0],rgb[1],rgb[2]);
        rgb+=3;
      }
      imgwrite(y*w,l0,w);
    }
    bpp=8;
    return 0;
  }
        
  
  uint8_t greyscale8_to_greyscale4()
  {
    uint8_t *grey4,*grey;
    uint8_t g;
    if (bpp!=8)
      return 1;
    grey_dither(greyscale4_reducer);
    for (uint16_t y=0;y<h;y++) {
      imgread(y*w,l0,w);
      grey=grey4=l0;
      for (uint16_t x=0;x<(w>>1);x++) {
        g=grey_to_grey4(*grey++)<<4;
        g|=grey_to_grey4(*grey++);
        *grey4++=g;
      }
      imgwrite((y*w)>>1,l0,w>>1);
    }
    bpp=4;
    return 0;
  }
  
  uint8_t greyscale8_to_greyscale2()
  {
    uint8_t *grey2,*grey;
    uint8_t g;
    if (bpp!=8)
      return 1;
    grey_dither(greyscale2_reducer);
    for (uint16_t y=0;y<h;y++) {
      imgread(y*w,l0,w);
      grey=grey2=l0;
      for (uint16_t x=0;x<(w>>2);x++) {
        g=grey_to_grey2(*grey++)<<6;
        g|=grey_to_grey2(*grey++)<<4;
        g|=grey_to_grey2(*grey++)<<2;
        g|=grey_to_grey2(*grey++);
        *grey2++=g;
      }
      imgwrite((y*w)>>2,l0,w>>2);
    }
    bpp=2;
    return 0;
  }
  
  uint8_t greyscale8_to_bw1()
  {
    uint8_t g;
    uint8_t *grey,*bw;
    if (bpp!=8)
      return 1;
    grey_dither(bw_reducer);
    for (uint16_t y=0;y<h;y++) {
      imgread(y*w,l0,w);
      grey=bw=l0;
      for (uint16_t x=0;x<(w>>3);x++) {
        g=grey_to_bw(*grey++)<<7;
        g|=grey_to_bw(*grey++)<<6;
        g|=grey_to_bw(*grey++)<<5;
        g|=grey_to_bw(*grey++)<<4;
        g|=grey_to_bw(*grey++)<<3;
        g|=grey_to_bw(*grey++)<<2;
        g|=grey_to_bw(*grey++)<<1;
        g|=grey_to_bw(*grey++);
        *bw++=g;
      }
      imgwrite((y*w)>>3,l0,w>>3);
    }
    bpp=1;
    return 0;
  }

  
};


