/*
 * lz_compress.c - Lightweight LZ77-variant compression for microcontrollers
 *
 * Output buffer format:
 *   Byte 0:    0x00 = not compressed (raw copy follows)
 *              0x01 = LZ compressed
 *   Bytes 1-2: original (decompressed) data length, little-endian uint16
 *   Bytes 3+:  payload
 *
 * Compressed payload format:
 *   The stream is divided into groups of up to 8 items, each group preceded
 *   by a 1-byte flag byte.  Bit N of the flag byte (LSB = bit 0) describes
 *   item N in that group:
 *     0 → literal byte  (1 byte follows)
 *     1 → back-reference (2 bytes follow)
 *
 *   Back-reference word (16-bit, big-endian):
 *     bits [15:12]  length_field  (match length = length_field + MIN_MATCH)
 *     bits [11: 0]  offset_field  (look-back distance = offset_field + 1)
 *
 * Tuning (suits ~1 kB buffers on RAM-constrained MCUs):
 *   Window   : 4096 bytes  (12-bit offset field → offsets 1-4096)
 *   Min match:  3 bytes
 *   Max match:   18 bytes  (4-bit length field → values 3-18)
 */

#include <stdint.h>
#include <string.h>
#include "lz_compress.h"

#define LZ_WINDOW_BITS  12
#define LZ_WINDOW_SIZE  (1u << LZ_WINDOW_BITS)   /* 4096 */
#define LZ_MIN_MATCH    3
#define LZ_MAX_MATCH    18             /* MIN_MATCH + 15 */

/* ── compress ──────────────────────────────────────────────────────────────
 *
 * Returns:
 *   1  LZ compression successful; result is smaller than source
 *   2  compressed result >= source size; raw copy stored instead (header 0x00)
 *   0  output buffer too small to hold any result
 */
int lz_compress(const uint8_t *in,  uint16_t in_size,
        uint8_t     *out, uint16_t out_size)
{
  /* Need header (1) + original-size field (2) + at least 1 byte of payload */
  if (out_size < 4u)
    return 0;
  uint16_t in_pos  = 0;
  uint16_t out_pos = 3;     /* out[0] = header, out[1..2] = orig_size */
  /* Threshold: if the compressed stream reaches this size we fall back to
   * a raw copy.  The +3 accounts for the 3-byte header.           */
  uint16_t raw_threshold = (uint16_t)(in_size + 3u);
  while (in_pos < in_size) {
    /* Reserve one byte for the flag byte of the upcoming group */
    uint16_t flag_pos = out_pos++;
    if (out_pos > out_size)
      return 0;
    uint8_t flags = 0;
    uint8_t count = 0;
    while (count < 8u && in_pos < in_size) {
      /* ── find longest match in the look-back window ── */
      uint16_t best_len  = 0;
      uint16_t best_offset = 0;
      uint16_t win_start = (in_pos >= LZ_WINDOW_SIZE)
                 ? (uint16_t)(in_pos - LZ_WINDOW_SIZE) : 0u;
      for (uint16_t s = win_start; s < in_pos; s++) {
        uint16_t len = 0;
        while (len < LZ_MAX_MATCH &&
             (uint16_t)(in_pos + len) < in_size &&
             in[s + len] == in[in_pos + len]) {
          len++;
        }
        if (len > best_len) {
          best_len  = len;
          best_offset = (uint16_t)(in_pos - s);  /* 1 .. LZ_WINDOW_SIZE */
        }
      }
      if (best_len >= LZ_MIN_MATCH) {
        /* Back-reference: 2 bytes */
        if (out_pos + 2u > out_size) return 0;
        if (out_pos + 2u >= raw_threshold) goto copy_raw;
        uint8_t  lf   = (uint8_t)(best_len - LZ_MIN_MATCH);   /* 0-15  */
        uint16_t of   = (uint16_t)(best_offset - 1u);      /* 0-4095*/
        uint16_t word = (uint16_t)((uint16_t)lf << 12) | of;
        out[out_pos++] = (uint8_t)(word >> 8);
        out[out_pos++] = (uint8_t)(word & 0xFFu);
        flags |= (uint8_t)(1u << count);
        in_pos = (uint16_t)(in_pos + best_len);
      } else {
        /* Literal: 1 byte */
        if (out_pos + 1u > out_size) return 0;
        if (out_pos + 1u >= raw_threshold) goto copy_raw;
        out[out_pos++] = in[in_pos++];
      }
      count++;
    }
    out[flag_pos] = flags;
  }
  /* Final size check */
  if (out_pos >= raw_threshold) goto copy_raw;
  /* ── Success: write header ── */
  out[0] = 0x01;
  out[1] = (uint8_t)(in_size & 0xFFu);
  out[2] = (uint8_t)(in_size >> 8);
  return 1;

copy_raw:
  if (raw_threshold > out_size) return 0;
  out[0] = 0x00;
  out[1] = (uint8_t)(in_size & 0xFFu);
  out[2] = (uint8_t)(in_size >> 8);
  memcpy(out + 3, in, in_size);
  return 2;
}

/* ── decompress ────────────────────────────────────────────────────────────
 *
 * Returns:
 *   1  success (data decompressed or raw-copied)
 *   0  output buffer too small, or malformed / truncated stream
 */
int lz_decompress(const uint8_t *in,  uint16_t in_size,
          uint8_t     *out, uint16_t out_size)
{
  if (in_size < 3u) return 0;
  uint8_t  header  = in[0];
  uint16_t orig_sz = (uint16_t)in[1] | ((uint16_t)in[2] << 8);
  /* ── Raw copy ── */
  if (header == 0x00) {
    if (orig_sz > out_size)
      return 0;   /* output too small */
    if ((uint16_t)(orig_sz + 3u) > in_size)
      return 0; /* input truncated  */
    memcpy(out, in + 3, orig_sz);
    return 1;
  }
  if (header != 0x01)
    return 0;   /* unrecognised header byte */
  /* ── LZ decompress ── */
  if (orig_sz > out_size)
    return 0;
  uint16_t in_pos  = 3;
  uint16_t out_pos = 0;
  while (out_pos < orig_sz) {
    if (in_pos >= in_size)
      return 0;  /* stream truncated */
    uint8_t flags = in[in_pos++];
    for (uint8_t i = 0u; i < 8u && out_pos < orig_sz; i++) {
      if (flags & (uint8_t)(1u << i)) {
        /* Back-reference */
        if (in_pos + 2u > in_size)
          return 0;
        uint16_t word  = ((uint16_t)in[in_pos] << 8) | in[in_pos + 1u];
        in_pos = (uint16_t)(in_pos + 2u);
        uint16_t match_len = (uint16_t)(word >> 12) + LZ_MIN_MATCH;
        uint16_t offset  = (uint16_t)(word & 0x0FFFu) + 1u;
        if (offset > out_pos)
          return 0;  /* corrupt    */
        if (out_pos + match_len > out_size)
          return 0; /* output small */
        uint16_t cp = (uint16_t)(out_pos - offset);
        for (uint16_t j = 0u; j < match_len; j++) {
          out[out_pos++] = out[cp++];
        }
      } else {
        /* Literal */
        if (in_pos >= in_size)  return 0;
        if (out_pos >= out_size) return 0;
        out[out_pos++] = in[in_pos++];
      }
    }
  }
  return (out_pos == orig_sz) ? 1 : 0;
}
