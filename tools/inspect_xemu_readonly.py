#!/usr/bin/env python3
"""Read-only QCOW2/FATX directory probe for xemu Xbox E: partition."""
import struct
import zlib

IMAGE = '/home/deck/Emulation/storage/xemu/xbox_hdd.qcow2'
E_OFFSET = 0xABE80000
E_SIZE = 0x1312D6000

def be32(b): return int.from_bytes(b, 'big')
def be64(b): return int.from_bytes(b, 'big')
def le32(b): return int.from_bytes(b, 'little')

class Reader:
    def __init__(self, path):
        self.f = open(path, 'rb')
        hd = self.raw(0, 104)
        self.qcow = hd[:4] == b'QFI\xfb'
        if not self.qcow:
            print('Image format: RAW')
            return
        version = be32(hd[4:8])
        self.bits = be32(hd[20:24])
        self.cs = 1 << self.bits
        self.l1_size = be32(hd[36:40])
        self.l1_offset = be64(hd[40:48])
        self.l1 = self.raw(self.l1_offset, self.l1_size * 8)
        if version not in (2, 3) or self.bits < 9 or self.bits > 21 or be64(hd[8:16]):
            raise ValueError('Unsupported QCOW2 format')
        if version == 3 and (be64(hd[72:80]) & ~1):
            raise ValueError('Unsupported QCOW2 incompatible features')
        self.l2cache = {}
        print(f'Image format: QCOW2 v{version}, cluster size {self.cs}')

    def raw(self, off, n):
        self.f.seek(off)
        b = self.f.read(n)
        if len(b) != n:
            raise IOError(f'Short file read at {off:#x}')
        return b

    def read(self, off, n):
        if not self.qcow:
            return self.raw(off, n)
        out = bytearray()
        per = self.cs // 8
        mask = 0x00fffffffffffe00
        while n:
            guest_cluster = off // self.cs
            inside = off % self.cs
            take = min(n, self.cs - inside)
            i, j = divmod(guest_cluster, per)
            if i >= self.l1_size:
                raise ValueError('QCOW2 offset outside L1')
            l1e = be64(self.l1[i * 8:i * 8 + 8]) & mask
            if l1e:
                if i not in self.l2cache:
                    self.l2cache[i] = self.raw(l1e, self.cs)
                l2e = be64(self.l2cache[i][j * 8:j * 8 + 8])
            else:
                l2e = 0
            if l2e & (1 << 62):
                xb = 62 - (self.bits - 8)
                comp_off = l2e & ((1 << xb) - 1)
                sectors = (l2e >> xb) & ((1 << (62 - xb)) - 1)
                length = (sectors + 1) * 512 - (comp_off & 511)
                data = zlib.decompress(self.raw(comp_off, length), -15)
                if len(data) != self.cs:
                    raise ValueError('QCOW2 decompressed cluster size mismatch')
                out.extend(data[inside:inside + take])
            elif not (l2e & mask) or (l2e & 1):
                out.extend(b'\0' * take)
            else:
                out.extend(self.raw((l2e & mask) + inside, take))
            off += take
            n -= take
        return bytes(out)

r = Reader(IMAGE)
sb = r.read(E_OFFSET, 16)
if sb[:4] != b'FATX':
    raise ValueError('No FATX E: partition found')
spc = le32(sb[8:12])
if not spc or spc > 1024 or (spc & (spc - 1)):
    raise ValueError('Invalid FATX cluster size')
ccs = spc * 512
nclus = E_SIZE // ccs
esz = 2 if nclus < 0xfff0 else 4
fat_off = E_OFFSET + 0x1000
fat_size = ((nclus * esz + 0xfff) // 0x1000) * 0x1000
data_off = fat_off + fat_size
root = le32(sb[12:16])
print(f'FATX E: cluster size {ccs}, root cluster {root}')

def next_cluster(c):
    v = int.from_bytes(r.read(fat_off + c * esz, esz), 'little')
    return 0 if v >= (0xfff0 if esz == 2 else 0xfffffff0) else v

def directory(cluster, label):
    print(f'\n{label} (cluster {cluster})')
    seen = set()
    entries = []
    for _ in range(32):
        if not 1 <= cluster < nclus or cluster in seen:
            print('  [Invalid or circular cluster chain]')
            break
        seen.add(cluster)
        block = r.read(data_off + (cluster - 1) * ccs, ccs)
        end = False
        for p in range(0, len(block), 64):
            e = block[p:p+64]
            length = e[0]
            if length in (0, 0xff):
                end = True
                break
            if length == 0xe5 or length > 42:
                continue
            name = e[2:2 + length].decode('ascii', 'replace')
            is_dir = bool(e[1] & 0x10)
            child = le32(e[44:48])
            size = le32(e[48:52])
            entries.append((name, is_dir, child))
            print(f'  {"DIR " if is_dir else "FILE"} {name}  {"cluster=" + str(child) if is_dir else "bytes=" + str(size)}')
        if end:
            break
        cluster = next_cluster(cluster)
        if not cluster:
            break
    return entries

def find(entries, name):
    return next((c for n, d, c in entries if d and n.lower() == name.lower()), None)

root_entries = directory(root, 'E:/')
udata = find(root_entries, 'UDATA')
if not udata:
    print('\nRESULT: No UDATA directory found')
else:
    ud_entries = directory(udata, 'E:/UDATA')
    title = find(ud_entries, '54430003')
    if not title:
        print('\nRESULT: Ninja Gaiden title directory missing')
    else:
        game_entries = directory(title, 'E:/UDATA/54430003')
        for name, is_dir, child in game_entries:
            if is_dir:
                directory(child, f'E:/UDATA/54430003/{name}')
print('\nInspection complete. No writes performed.')
