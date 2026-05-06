"""Unpack data.vfs.mp3 based on MIDASKernelManager::getAssetSizeFromVFS layout.

Format (per entry, little-endian):
    uint32 hash
    uint32 data_length
    bytes  data[data_length]

Repeated until file end. No encryption at this layer.
"""
from __future__ import annotations
import struct, pathlib, sys

VFS = pathlib.Path(r"D:/testrepo/work/h5/extracted/assets/data.vfs.mp3")
OUT = pathlib.Path(r"D:/testrepo/work/h5/vfs_entries")
OUT.mkdir(parents=True, exist_ok=True)

MAGIC_SNIFFERS = {
    b"\x89PNG\r\n\x1a\n": "png",
    b"OggS": "ogg",
    b"PK\x03\x04": "zip",
    b"RIFF": "wav_or_riff",
    b"\xff\xd8\xff": "jpg",
    b"GIF8": "gif",
    b"BM": "bmp",
    b"ID3": "mp3",
    b"\xff\xfb": "mp3",
    b"\xff\xf3": "mp3",
}

def sniff(data: bytes) -> str:
    for sig, ext in MAGIC_SNIFFERS.items():
        if data.startswith(sig):
            return ext
    if all(0x20 <= b < 0x7f or b in (9, 10, 13) for b in data[:64]):
        return "txt"
    return "bin"

def main():
    raw = VFS.read_bytes()
    print(f"VFS size: {len(raw):,} bytes")

    pos = 0
    n = 0
    type_counts: dict[str, int] = {}
    catalog = []

    while pos + 8 <= len(raw):
        h, ln = struct.unpack_from("<II", raw, pos)
        if ln < 0 or pos + 8 + ln > len(raw):
            print(f"[stop] entry {n} @ 0x{pos:x}: invalid length {ln}")
            break
        data = raw[pos+8 : pos+8+ln]
        ext = sniff(data)
        type_counts[ext] = type_counts.get(ext, 0) + 1

        out = OUT / f"{n:05d}_{h:08x}.{ext}"
        out.write_bytes(data)

        catalog.append((n, pos, h, ln, ext))
        pos += 8 + ln
        n += 1

    print(f"\nExtracted {n} entries -> {OUT}")
    print(f"Final position: 0x{pos:x} / 0x{len(raw):x}  (remaining: {len(raw)-pos} bytes)")
    print(f"\nType breakdown:")
    for k, v in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {k:15s} {v:6d}")

    catalog_path = OUT.parent / "vfs_catalog.tsv"
    with catalog_path.open("w", encoding="utf-8") as f:
        f.write("index\toffset\thash\tlength\ttype\n")
        for row in catalog:
            f.write(f"{row[0]}\t0x{row[1]:x}\t0x{row[2]:08x}\t{row[3]}\t{row[4]}\n")
    print(f"Catalog: {catalog_path}")

if __name__ == "__main__":
    main()
