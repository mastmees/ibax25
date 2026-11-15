#pragma once

#include <stdint.h>

class IBAX25
{
uint16_t w,h;
uint8_t bpp;

protected:
  virtual uint16_t imgread(uint32_t offset,uint8_t *buf,uint16_t nbytes) = 0;
  virtual uint16_t imgwrite(uint32_t offset,uint8_t *buf,uint16_t nbytes) = 0; 

  
  void nearest_web_safe_color(uint8_t *color,uint8_t* websafecolor)
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
    
  uint8_t rgb_to_col(uint8_t r,uint8_t g,uint8_t b)
  {
    return ((uint16_t)r+25)*36/51+((uint16_t)g+25)*6/51+((uint16_t)b+25)/51;
  }
  
  uint8_t rgb_to_grey(uint8_t r,uint8_t g,uint8_t b)
  {
    return ((uint32_t)r*299+(uint32_t)g*587+(uint16_t)b*114)/1000;
  }

  uint8_t grey_to_grey4(uint8_t i)
  {
    if (i<9)
      return 0;
    if (i<26)
      return 1;
    if (i<43)
      return 2;
    if (i<60)
      return 3;
    if (i<77)
      return 4;
    if (i<94)
      return 5;
    if (i<111)
      return 6;
    if (i<128)
      return 7;
    if (i<145)
      return 8;
    if (i<162)
      return 9;
    if (i<179)
      return 10;
    if (i<196)
      return 11;
    if (i<213)
      return 12;
    if (i<230)
      return 13;
    if (i<247)
      return 14;
    return 15;
  }
  
  uint8_t grey_to_grey2(uint8_t i)
  {
    if (i<43)
      return 0;
    if (i<128)
      return 1;
    if (i<213)
      return 2;
    return 3;
  }
        
  uint8_t grey_to_bw(uint8_t c)
  {
    return (c<128)?0:1;
  }
  
    
public:

  IBAX25() : w(0),h(0),bpp(24) {}
  IBAX25(uint16_t width,uint16_t height,uint8_t bitsperpixel=24) : w(width),h(height),bpp(bitsperpixel) {}
  
  void set_size(uint16_t width,uint16_t height,uint8_t bitsperpixel=24)
  {
    w=width;
    h=height;
    bpp=bitsperpixel;
  }
  
  uint8_t rgb_to_greyscale8()
  {
    uint32_t r=0;
    uint8_t rgb[3];
    if (bpp!=24)
      return 1;
    for (uint16_t y=0;y<h;y++) {
      for (uint16_t x=0;x<w;x++) {
        imgread((y*w+x)*3,rgb,sizeof(rgb));
        rgb[0]=rgb_to_grey(rgb[0],rgb[1],rgb[2]);
        imgwrite(r++,rgb,1);
      }
    }
    bpp=8;
    return 0;
  }
  
  uint8_t rgb_to_color8()
  {
    uint32_t r=0;
    uint8_t rgb[3];
    if (bpp!=24)
      return 0;
    for (uint16_t y=0;y<h;y++) {
      for (uint16_t x=0;x<w;x++) {
        imgread((y*w+x)*3,rgb,sizeof(rgb));
        rgb[0]=rgb_to_col(rgb[0],rgb[1],rgb[2]);
        imgwrite(r++,rgb,1);
      }
    }
    bpp=8;
    return 0;
  }
  
  uint8_t greyscale8_to_greyscale4()
  {
    uint8_t c;
    uint32_t r=0;
    if (bpp!=8)
      return 1;
    for (uint16_t y=0;y<h;y++) {
      for (uint16_t x=0;x<w;x++) {
        imgread(r,&c,1);
        c=grey_to_grey4(c);
        imgwrite(r++,&c,1);
      }
    }
    return 0;
  }
  
  uint8_t greyscale8_to_greyscale2()
  {
    uint8_t c;
    uint32_t r=0;
    if (bpp!=8)
      return 1;
    for (uint16_t y=0;y<h;y++) {
      for (uint16_t x=0;x<w;x++) {
        imgread(r,&c,1);
        c=grey_to_grey2(c);
        imgwrite(r++,&c,1);
      }
    }
    return 0;
  }
  
  uint8_t greyscale8_to_bw1()
  {
    uint8_t c;
    uint32_t r=0;
    if (bpp!=8)
      return 1;
    for (uint16_t y=0;y<h;y++) {
      for (uint16_t x=0;x<w;x++) {
        imgread(r,&c,1);
        c=grey_to_bw(c);
        imgwrite(r++,&c,1);
      }
    }
    return 0;
  }
  
};
