import io
import struct
import logging


def decompress(compressed: io.BufferedReader):
    # Not using BinaryReader and BinaryRandom here to combat the horrible performance a bit.
    logging.debug("Decompressing Yaz0 file...")
    # Read the header.
    if (compressed.read(4) != b"Yaz0"):
        raise AssertionError("Invalid Yaz0 header.")
    decompressed_size = struct.unpack(">I", compressed.read(4))[0]
    compressed.seek(8, io.SEEK_CUR)  # Padding
    # Decompress the data into an array. Cache methods to avoid looking them up in the loop.
    decompressed = bytearray()
    _divmod = divmod
    _read = compressed.read
    _append = decompressed.append
    _extend = decompressed.extend
    while len(decompressed) < decompressed_size:
        # Read the configuration byte of a decompression setting group, and go through each bit of it.
        group_config = _read(1)[0]
        for i in (128, 64, 32, 16, 8, 4, 2, 1):
            # Check if the bit of the current chunk is set.
            if (group_config & i):
                # Bit is set, copy 1 raw byte to the output.
                _extend(_read(1))
            # This does not make sense for the last byte.
            elif (len(decompressed) < decompressed_size):
                # Bit is not set and data copying configuration follows, either 2 or 3 bytes long.
                offset = _read_uint16(compressed)
                # If the nibble of the first back byte of offset is 0, the config is 3 bytes long.
                if (offset > 4095):
                    # Nibble is not 0, determining nibble + 0x02 bytes to read, the remainder being the real offset.
                    data_size = (offset >> 12) + 0x02
                    offset &= 0x0FFF
                else:
                    # Nibble is 0, the number of bytes to read is in third byte, which is size + 0x12.
                    data_size = _read(1)[0] + 0x12
                # Append bytes from the current offset.
                offset += 1
                if (data_size == offset):
                    chunk = decompressed[-offset:]
                elif (data_size < offset):
                    chunk = decompressed[-offset:data_size - offset]
                else:
                    copies, remainder = _divmod(data_size, offset)
                    chunk = decompressed[-offset:] * copies
                    if (remainder):
                        chunk += decompressed[-offset:-offset + remainder]
                _extend(chunk)
    # Return the decompressed data.
    return io.BytesIO(decompressed)


def _read_uint16(file):
    # Faster than struct.unpack.
    buffer = file.read(2)
    return (buffer[0] << 8) + buffer[1]
