#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include "ibax.hpp"

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

int main(int argc,char **argv)
{
FILE *fp;
uint32_t fs;
  if (argc>1) {
    fp=fopen(argv[1],"rb");
    fseek(fp,0,SEEK_END);
    fs=ftell(fp);
    pixels=(uint8_t *)malloc(fs);
    if (pixels) {
      rewind(fp);
      fread(pixels,1,fs,fp);
    }
    fclose(fp);
  }
  if (pixels)
    save("dump.rgb",fs);
  return 0;
}
