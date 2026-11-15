"""
lz_compress.py - Python port of the lightweight LZ77-variant compressor.

Format-compatible with the C implementation (lz_compress.c / lz_compress.h):

    Byte 0:    0x00 = not compressed (raw copy follows)
               0x01 = LZ compressed
    Bytes 1-2: original (decompressed) data length, little-endian uint16
    Bytes 3+:  payload

Compressed payload:
    Groups of up to 8 items, each preceded by a flag byte. Bit N (LSB=bit 0)
    of the flag byte describes item N:
        0 -> literal byte (1 byte follows)
        1 -> back-reference (2 bytes follow, big-endian word)

    Back-reference word:
        bits [15:12] = match_length - MIN_MATCH   (length 3-18)
        bits [11:0]  = offset - 1                  (distance 1-4096)
"""

LZ_WINDOW_SIZE = 4096   # 12-bit offset field
LZ_MIN_MATCH = 3
LZ_MAX_MATCH = 18       # MIN_MATCH + 15 (4-bit length field)


def lz_compress(data: bytearray) -> bytearray:
    """
    Compress `data` using the LZ77-variant algorithm.

    Returns a new bytearray containing the 3-byte header followed by either
    the LZ-compressed stream (header 0x01) or a raw copy of `data`
    (header 0x00) if compression would not reduce the size.
    """
    in_size = len(data)
    out = bytearray()

    pos = 0
    while pos < in_size:
        flag_pos = len(out)
        out.append(0)  # placeholder flag byte
        flags = 0

        for bit in range(8):
            if pos >= in_size:
                break

            best_len = 0
            best_offset = 0

            win_start = pos - LZ_WINDOW_SIZE if pos >= LZ_WINDOW_SIZE else 0

            for s in range(win_start, pos):
                max_len = min(LZ_MAX_MATCH, in_size - pos)
                length = 0
                while length < max_len and data[s + length] == data[pos + length]:
                    length += 1
                if length > best_len:
                    best_len = length
                    best_offset = pos - s

            if best_len >= LZ_MIN_MATCH:
                length_field = best_len - LZ_MIN_MATCH    # 0-15
                offset_field = best_offset - 1            # 0-4095
                word = (length_field << 12) | offset_field
                out.append((word >> 8) & 0xFF)
                out.append(word & 0xFF)
                flags |= (1 << bit)
                pos += best_len
            else:
                out.append(data[pos])
                pos += 1

        out[flag_pos] = flags

    # Fall back to raw copy if compression didn't help
    if len(out) >= in_size:
        result = bytearray(3 + in_size)
        result[0] = 0x00
        result[1] = in_size & 0xFF
        result[2] = (in_size >> 8) & 0xFF
        result[3:] = data
        return result

    result = bytearray(3)
    result[0] = 0x01
    result[1] = in_size & 0xFF
    result[2] = (in_size >> 8) & 0xFF
    result.extend(out)
    return result


def lz_decompress(data: bytearray) -> bytearray:
    """
    Decompress a buffer produced by lz_compress().

    Returns a new bytearray containing the original data.

    Raises ValueError if the input is too short or the stream is malformed.
    """
    if len(data) < 3:
        raise ValueError("input too short: missing header")

    header = data[0]
    orig_size = data[1] | (data[2] << 8)

    if header == 0x00:
        if len(data) < 3 + orig_size:
            raise ValueError("input truncated")
        return bytearray(data[3:3 + orig_size])

    if header != 0x01:
        raise ValueError(f"unrecognized header byte: 0x{header:02X}")

    out = bytearray()
    in_pos = 3
    in_size = len(data)

    while len(out) < orig_size:
        if in_pos >= in_size:
            raise ValueError("stream truncated (missing flag byte)")

        flags = data[in_pos]
        in_pos += 1

        for bit in range(8):
            if len(out) >= orig_size:
                break

            if flags & (1 << bit):
                if in_pos + 2 > in_size:
                    raise ValueError("stream truncated (missing back-reference)")

                word = (data[in_pos] << 8) | data[in_pos + 1]
                in_pos += 2

                match_len = (word >> 12) + LZ_MIN_MATCH
                offset = (word & 0x0FFF) + 1

                if offset > len(out):
                    raise ValueError("corrupt stream: offset exceeds output")

                cp = len(out) - offset
                for j in range(match_len):
                    out.append(out[cp + j])
            else:
                if in_pos >= in_size:
                    raise ValueError("stream truncated (missing literal)")
                out.append(data[in_pos])
                in_pos += 1

    if len(out) != orig_size:
        raise ValueError("decompressed size mismatch")

    return out
