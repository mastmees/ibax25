# Image Broadcast over AX25

## Design objectives

Images must take reasonable time to transmit

Must not be computationally expensive to encode, as it is aimed at
microcontroller on cubesat

Must be possible to encode using very small amount of microcontroller RAM

Receiving viewable parital image should be possible no matter which part is
lost

Improving image over multiple broadcasts must be possible

Must be simple to decode

Sending high resolution images is not an objective

## Image formats

Based on experiments done with ibax25.py, 3 formats were chosen

1. 8-bit indexed color with fixed palette (web-safe colors)
2. 4-bit greyscale
3. 1-bit b/w

Starting from uncompressed 24-bit RGB image, 8 bit color image is 3x smaller,
4-bit greyscale is 6x smaller, and 1-bit b/w image is 24x smaller

Such a big reduction in color space would produce very poor images,
so for photo images dithering is a must-have.

## No compression

As the objective is to have a partial image no matter what bits are lost,
each segment that is sent would have to be separately compressed. The
minimal memory requirement limits the compression options further.

Tests done with LZ compression resulted in 20-30% overall size reduction for
dithered color images what did not have much black background. For 4-bit
dithered greyscale images the size reduction was marginal, for 1-bit images
the compression did not reduce the image size. Again, this is mainly because
of compressing each image segment separately. Other compression methods may
work significantly better, but this would most likely conflict with several
development objectives.

## Transmission

Images are transmitted in segments as AX25 U-type frames. SSID of a sender
is used to define image 'channel', there may be multiple image channels in
use at a same time.

In each channel, AX25 frame payload starts with 6 byte header, uint16 values
are little-endian:

| field | type |
| ----- | ---- |
| image_id | uint8 |
| row | uint16 |
| column | uint16 |
| format | uint8 |

The rest of the payload is pixel data in the specified format. The length of
the pixel data is not given, it is implied from the AX25 frame length.

Also notably there is no information about the image dimensions. If the decoder
would rely on this information for decoding, then each segment should
contain additional two fields, adding overhead. It is expected that the
image segments contain the entire row, in case the row is split the decoder
can deduct the image width from the received data. If the first segment
had 160 pixels starting from column 0, then the image may be 160 pixels
wide, or another segment may arrive with another 160 pixels from column 160,
making the image 320 pixels wide. The decoder may start out with no image,
or with some arbitrary width canvas, and expand the canvas as the data
arrives.

### Image ID

an arbitrary number that changes whenever transmission switches to a new
image. as long as the image ID is the same, any received segment can be used
to update the currently received image

### row

number of the row for the received segment. rows start from 0, at the top of
the image

### column

number of the column where the received segment starts on the given row.
columns start from 0, on the left edge of the image

### format

pixel format specifier

| bit | function |
| --- | -------- |
| 7 | reserved, 0 |
| 6 | greyscale=0, color=1 |
| 5 | bpp |
| 4 | bpp |
| 3 | bpp |
| 2 | bpp |
| 1 | bpp |
| 0 | bpp |

6 bit bits per pixel value allows for 1..31 bpp image formats in future,
for currently defined image formats

8 bit color is 01001000 = 0x48
4 bit greyscale is 0x00000100 = 0x04
1 bit b&w is 0x00000001 = 0x01

0 bpp is a special case, indicating that the segment containst utf-8
encoded text string. multiple text strings may be transmitted along with the
image, using row number to differentiate. this is for filename, image title,
or whatever.

## web-safe color palette

web-safe color palette defines a fixed palette of 216 colors where each
color component gets 6 different values. Finding the nearest colour from RGB
value does not require palette search, it is directly computable with
integer arithmetic

```
  // r,g,b are RGB components as 8 bit unsigned values
  r=((uint16_t)r+25)/51
  g=((uint16_t)g+25)/51
  b=((uint16_t)b+25)//51
  webcolor=r*36+g*6+b
```

## color to greyscale

Although any other ratios could be used, a typical RGB to 8-bit converstion
using integer arithmetic would be

```
  grey_level=((uint32_t)r*299+(uint32_t)g*587+(uint16_t)b*114)/1000
```
