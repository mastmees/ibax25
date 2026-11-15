/*
 * lz_compress.h - Lightweight LZ77-variant compression for microcontrollers
 *
 * Output buffer format (produced by lz_compress, consumed by lz_decompress):
 *
 *   Byte 0:    0x00  data was NOT compressed (raw copy)
 *              0x01  data IS LZ-compressed
 *   Bytes 1-2: original (pre-compression) data length, little-endian uint16
 *   Bytes 3+:  payload (raw or LZ stream)
 *
 * The +3 overhead of the header must be accounted for when sizing buffers:
 *   minimum output buffer for compress   = in_size + 3
 *   minimum output buffer for decompress = original data length (bytes 1-2)
 */

#ifndef LZ_COMPRESS_H
#define LZ_COMPRESS_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Compress a data buffer using a lightweight LZ77-variant algorithm.
 *
 * The function first attempts LZ compression.  If the compressed result would
 * be equal to or larger than the source, the source data is copied to the
 * output unchanged (header byte 0x00).  Either way the output is prefixed with
 * a 3-byte header (see format above).
 *
 * @param in        Pointer to the source data to compress.
 * @param in_size   Number of source bytes.
 * @param out       Pointer to the output buffer.
 * @param out_size  Size of the output buffer in bytes.
 *                  Must be at least (in_size + 3) to guarantee success.
 *
 * @retval  1  LZ compression succeeded; result is smaller than source.
 *             Output header byte is 0x01.
 * @retval  2  Compressed result >= source size; raw copy stored.
 *             Output header byte is 0x00.
 * @retval  0  Output buffer is too small to hold any result; output unchanged.
 */
int lz_compress(const uint8_t *in,  uint16_t in_size,
                uint8_t       *out, uint16_t out_size);

/**
 * @brief Decompress (or copy) data produced by lz_compress().
 *
 * Reads the 3-byte header to determine the mode and original size, then either
 * copies the raw payload (header 0x00) or decompresses the LZ stream (0x01).
 *
 * @param in        Pointer to the compressed/stored buffer (including header).
 * @param in_size   Total number of input bytes (including the 3-byte header).
 * @param out       Pointer to the output buffer for the decompressed data.
 * @param out_size  Size of the output buffer in bytes.
 *                  Must be >= the original data length stored in bytes 1-2.
 *
 * @retval  1  Success: output buffer holds the original data.
 * @retval  0  Failure: output buffer too small, or stream is malformed/truncated.
 */
int lz_decompress(const uint8_t *in,  uint16_t in_size,
                  uint8_t       *out, uint16_t out_size);

#ifdef __cplusplus
}
#endif

#endif /* LZ_COMPRESS_H */
