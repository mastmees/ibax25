/*
MIT License

Copyright (c) 2026 Madis Kaal

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include "ibax25.hpp"

uint8_t *pixels;

class IBAX : public IBAX25
{

  uint16_t imgread(uint32_t offset,uint8_t *buf,uint16_t nbytes)
  {
    memcpy(buf,&pixels[offset],nbytes);
    return nbytes;
  }
  
  uint16_t imgwrite(uint32_t offset,uint8_t *buf,uint16_t nbytes)
  {
    memcpy(&pixels[offset],buf,nbytes);
    return nbytes;
  }

};

IBAX image;

void save(const char *fn,uint32_t nbytes)
{
  FILE *fp=fopen(fn,"wb");
  if (fp) {
    fwrite(pixels,1,nbytes,fp);
    fclose(fp);
  }
}

bool load(const char *fn)
{
FILE *fp=fopen(fn,"rb");
uint32_t fs;
  if (!fp)
    return false;
  fseek(fp,0,SEEK_END);
  fs=ftell(fp);
  if (pixels)
    free(pixels);
  pixels=(uint8_t *)malloc(fs);
  if (pixels) {
    rewind(fp);
    if (fread(pixels,1,fs,fp)!=fs) {
      free(pixels);
      pixels=NULL;
    }
    image.set_size(320,240,24);
  }
  fclose(fp);
  return pixels!=NULL;
}

int main(int argc,char **argv)
{
  if (load("test.rgb")) {
    image.rgb_to_color8();
    save("test.colr8",image.bitmapsize());
  }
  if (load("test.rgb")) {
    image.rgb_to_greyscale8();
    save("test.grey8",image.bitmapsize());
  }
  if (load("test.rgb")) {
    image.rgb_to_greyscale8();
    image.greyscale8_to_greyscale4();
    save("test.grey4",image.bitmapsize());
  }
  if (load("test.rgb")) {
    image.rgb_to_greyscale8();
    image.greyscale8_to_greyscale2();
    save("test.grey2",image.bitmapsize());
  }
  if (load("test.rgb")) {
    image.rgb_to_greyscale8();
    image.greyscale8_to_bw1();
    save("test.bw",image.bitmapsize());
  }
  return 0;
}
