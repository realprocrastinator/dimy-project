# can either take bytes type or hex string
def bytes_or_hexstr_to_decimal(s, typename):
    # int in python can handle arbitary large number
    if typename == "bytes":
        return int(s.hex(), 16)
    elif typename == "str":
        return int(s, 16)
    else:
        raise TypeError("Can only handle str or bytes type.")

def ephid_bytes_or_hexstr_to_decimal(ephid, length = 16):
    if isinstance(ephid, bytes):
        if (len(ephid) != length):
            raise ValueError(f"EphID must be {length} bytes long")
        return bytes_or_hexstr_to_decimal(ephid, "bytes")
    
    elif isinstance(ephid, str):
        # hex string takes two bytes to represent a byte in raw hex!
        if (len(ephid) != length * 2):
            raise ValueError(f"EphID must be {length} bytes long")
        return bytes_or_hexstr_to_decimal(ephid, "str")
    
    else:
        raise TypeError("Can only handle str or bytes type.")

def ephid_decimal_to_bytes(n, length = 16):
    if not isinstance(n, int):
        raise TypeError("Can only handle int type.")
    
    # 128 bit to 16 bytes, since python uses big endian to represent bytes, we respect!
    return n.to_bytes(length, "big")



if __name__ == "__main__":
    try:
        bytes_or_hexstr_to_decimal("hi", "notbytes")
    except TypeError as e:
        print("Test Invalid input pass.\n")

    assert(bytes_or_hexstr_to_decimal((1234).to_bytes(16, "big"), "bytes") == 1234)
    assert(bytes_or_hexstr_to_decimal((1234).to_bytes(16, "big").hex(), "str") == 1234)
    
    print("Test bytes_or_hexstr_to_decimal passed\n")

    assert(ephid_bytes_or_hexstr_to_decimal((567856785678567856785678).to_bytes(16, "big")) == 567856785678567856785678)
    assert(ephid_bytes_or_hexstr_to_decimal((567856785678567856785678).to_bytes(16, "big").hex()) == 567856785678567856785678)
    
    print("Test ephid_bytes_or_hexstr_to_decimal passed\n")

    test_bytes = b"\x78\x3f\x93\xfa\x14\x76\x73\x7d\xc9\x0e"
    assert(ephid_decimal_to_bytes(567856785678567856785678) == bytes(b"\x00" * (16 - len(test_bytes))) + test_bytes)
    assert(ephid_decimal_to_bytes(567856785678567856785678).hex() ==  "00" * (16 - len(test_bytes)) + hex(567856785678567856785678)[2:])
    
    print("Test ephid_decimal_to_bytes passed\n")


    
