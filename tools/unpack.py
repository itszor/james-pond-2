#!/usr/bin/env python3
"""The game, unpacked by its own decompressors.

    unpack.py           game/!RoboCod/!RunImage -> unpacked/runimage (the
                        program as it runs, at &8000), its roots
                        (unpacked/runimage.roots), and unpacked/protect
                        (it with Files.59 in place at &22AAC)

!RunImage is packed twice. Its first word branches past a header (&8004:
where it unpacks to, 0, the packed length, the packed data's offset) to an
LZ unpacker (&8014): it reads the top of memory (OS_GetEnv), moves the
packed data up under it, unpacks it to &8144, copies a loop below the
stack that moves the result down to &8000, and jumps there. That is an
image packed by Acorn's squeeze: its first word branches to the unsqueezer
at its end (&37B24), which unpacks it in place and jumps to &8000 again,
now the program. Both run here under SuperSpider's tools/arm2.py, until
the second arrival at &8000; the squeeze header (the six words before the
unsqueezer) gives the program's length.

The program's &22AAC-&3B14C is a buffer the files in Files are loaded into,
packed (explode(): the program's own unpacker, &3CCC0, reading them with
OS_BGet). They are the objects' graphics, but for Files.59: code, the disc
check, which &3D06C loads there and calls (&3D0A0). unpacked/protect is the
program with it there, the one image its code is analysed in (recomp/:
only its part is translated, genprotect/).

The objects' handlers are reached only through the object types' records
(&3F1EC, &70 bytes each, types 0-&4E): words 1-4 are the handlers of an
object's four states, which &47C74 calls (&47CB4: mov pc, r12, with lr set
to return to &47CB8). unpacked/runimage.roots lists them, and that return.
"""
import os
import struct
import sys

SS = os.environ.get('SUPERSPIDER', os.path.expanduser('~/stuff/superspider'))
sys.path.insert(0, os.path.join(SS, 'tools'))
import arm2  # noqa: E402

TOP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
APP = os.path.join(TOP, 'game', '!RoboCod')
OUT = os.path.join(TOP, 'unpacked')
BASE = 0x8000
OVERLAY = 0x22AAC               # where Files' files are loaded
TYPES, TYPE_SIZE, NTYPES = 0x3F1EC, 0x70, 0x4F   # the object types' records
STATE_CALL_RETURN = 0x47CB8     # where the handlers return to
RAMTOP = BASE + 520 * 1024      # !RunPond2's WimpSlot
OS_GETENV, OS_SYNCHRONISECODEAREAS = 0x10, 0x6E


def find(d, name):
    """a RISC OS file in a host directory: any case, any ,load-exec suffix"""
    for f in os.listdir(d):
        if f.split(',')[0].lower() == name.lower():
            return os.path.join(d, f)
    raise FileNotFoundError(os.path.join(d, name))


def unpack(packed):
    m = arm2.ARM(memsize=0x1000000)
    m.mem[BASE:BASE + len(packed)] = packed

    def swi(m, n, pc):
        n &= ~0x20000
        if n == OS_GETENV:
            m.r[0], m.r[1], m.r[2] = 0, RAMTOP, 0
        elif n != OS_SYNCHRONISECODEAREAS:
            sys.exit('unpack: !RunImage calls SWI &%X at &%X while unpacking (not the known release?)' % (n, pc))
    m.swi_handler = swi
    m.r[15] = BASE
    squeezed = None
    for layer in ('LZ', 'squeeze'):
        m.step()
        while m.r[15] != BASE:
            m.step()
            if m.steps > 20_000_000:
                raise RuntimeError('unpack: %s: no end, pc=&%X' % (layer, m.r[15]))
        if squeezed is None:
            squeezed = bytes(m.mem[BASE:RAMTOP])
    # the squeeze header, from the first word's branch to the unsqueezer
    first = struct.unpack_from('<I', squeezed, 0)[0]
    if first >> 24 != 0xEA:
        sys.exit('unpack: !RunImage: not squeezed as expected')
    unsq = BASE + 8 + ((first & 0xFFFFFF) << 2)
    hdr = unsq - 0x24                               # (sub r0,pc,#&2C)
    out_len, in_len, tables = struct.unpack_from('<3I', squeezed, hdr - BASE)
    end = hdr - tables - in_len + out_len           # the packed data's start + its unpacked length
    if not unsq < end <= RAMTOP:
        sys.exit('unpack: !RunImage: unexpected squeeze header')
    return bytes(m.mem[BASE:end])


def explode(src):
    """a file in Files, as &3CCC0 unpacks it: a 4-byte header (its first
    byte 1: stored), then LZ - 16 flag bits at a time, low bit first, each
    a literal byte (0) or two bytes b, c (1): (b & 15) + 1 bytes copied from
    c + (b & &F0) << 4 back"""
    if src[0] == 1:
        return bytes(src[4:])
    out = bytearray()
    i, flags, n = 4, 0, 0
    while i < len(src):
        if n == 0:
            flags, n = src[i] | src[i + 1] << 8, 16
            i += 2
        bit, flags, n = flags & 1, flags >> 1, n - 1
        if bit:
            b, c = src[i], src[i + 1]
            i += 2
            back = c + ((b & 0xF0) << 4)
            for _ in range((b & 15) + 1):
                out.append(out[-back])
        else:
            out.append(src[i])
            i += 1
    return bytes(out)


def handlers(data):
    """the objects' state handlers: words 1-4 of each type's record (0: none)"""
    word = lambda a: struct.unpack_from('<I', data, a - BASE)[0]
    hs = set()
    for t in range(NTYPES):
        for s in range(1, 5):
            h = word(TYPES + TYPE_SIZE * t + 4 * s)
            if h == 0:
                continue
            if not (BASE <= h < BASE + len(data) and h & 3 == 0 and word(h) >> 28 == 0xE):
                sys.exit('unpack: !RunImage: type &%X state %d: &%X is not code' % (t, s, h))
            hs.add(h)
    return sorted(hs)


def main():
    os.makedirs(OUT, exist_ok=True)
    data = unpack(open(find(APP, '!RunImage'), 'rb').read())
    open(os.path.join(OUT, 'runimage'), 'wb').write(data)
    print('runimage: %d bytes at &%X-&%X' % (len(data), BASE, BASE + len(data)))
    hs = handlers(data)
    with open(os.path.join(OUT, 'runimage.roots'), 'w') as f:
        f.write('# the objects\' state handlers, from their types\' records (tools/unpack.py)\n')
        f.writelines('&%X\n' % h for h in hs)
        f.write('&%X\t# their return\n' % STATE_CALL_RETURN)
    print('runimage.roots: %d handlers' % len(hs))
    code = explode(open(find(os.path.join(APP, 'Files'), '59'), 'rb').read())
    at = OVERLAY - BASE
    if any(data[at:at + len(code)]):
        sys.exit('unpack: !RunImage: &%X is not the empty buffer expected' % OVERLAY)
    open(os.path.join(OUT, 'protect'), 'wb').write(data[:at] + code + data[at + len(code):])
    print('protect: Files.59, %d bytes at &%X-&%X' % (len(code), OVERLAY, OVERLAY + len(code)))


if __name__ == '__main__':
    main()
