"""Round 73 — Hero3 SMAF (.mf) → MIDI → WAV → OGG 자동 pipeline.

대상: work/h3/extracted/snd/*_mf (33 files, Yamaha SMAF format magic 'MMMD')

3-step external tool chain:
  1. SMAF → MIDI    smaf-converter.jar (Java, vavi-sound backend)
  2. MIDI → WAV     timidity++ (CLI) + GM SoundFont (예: OmegaGMGS2.sf2 또는 FluidR3_GM.sf2)
  3. WAV → OGG      FFmpeg (libvorbis)

도구 부재 시 graceful: 각 step 별로 도구 found 여부 확인 후 skip + 안내.

설치 가이드는 docs/h3/smaf_conversion_guide.md 참조.
"""
from __future__ import annotations
import json
import os
import pathlib
import shutil
import subprocess
import sys
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SND  = ROOT / "work" / "h3" / "extracted" / "snd"
OUT  = ROOT / "work" / "h3" / "audio"
MID_DIR = OUT / "mid"
WAV_DIR = OUT / "wav"
OGG_DIR = OUT / "ogg"
for d in (MID_DIR, WAV_DIR, OGG_DIR):
    d.mkdir(parents=True, exist_ok=True)

LOG = OUT / "pipeline_report.log"
JSON_OUT = OUT / "pipeline_report.json"

# 사용자가 도구 위치를 환경 변수 또는 디폴트 경로로 지정 가능
SMAF_JAR  = os.environ.get("SMAF_CONVERTER_JAR", str(ROOT / "tools" / "external" / "smaf-converter.jar"))
SOUNDFONT = os.environ.get("SOUNDFONT_PATH",     str(ROOT / "tools" / "external" / "FluidR3_GM.sf2"))


def has_command(name: str) -> bool:
    return shutil.which(name) is not None


def tool_status() -> dict:
    return {
        "java": has_command("java"),
        "timidity": has_command("timidity"),
        "fluidsynth": has_command("fluidsynth"),
        "ffmpeg": has_command("ffmpeg"),
        "smaf_jar_exists": pathlib.Path(SMAF_JAR).exists(),
        "soundfont_exists": pathlib.Path(SOUNDFONT).exists(),
    }


def parse_smaf_header(data: bytes) -> Optional[dict]:
    """첫 4 byte 가 'MMMD' 이어야 정상 SMAF."""
    if len(data) < 8 or data[:4] != b"MMMD":
        return None
    import struct
    chunk_size = struct.unpack_from(">I", data, 4)[0]
    return {
        "magic": "MMMD",
        "chunk_size": chunk_size,
        "first_8_after_magic_hex": data[8:16].hex(" ") if len(data) >= 16 else "",
        "total_size": len(data),
    }


def run_step(cmd: list[str], log_lines: list[str], label: str) -> bool:
    log_lines.append(f"  $ {' '.join(cmd)}")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            return True
        log_lines.append(f"    ! exit {r.returncode}: {(r.stderr or r.stdout)[:200]}")
        return False
    except FileNotFoundError:
        log_lines.append(f"    ! command not found: {cmd[0]}")
        return False
    except subprocess.TimeoutExpired:
        log_lines.append(f"    ! timeout: {label}")
        return False


def main() -> int:
    files = sorted(SND.glob("*_mf"))
    log_lines: list[str] = [
        "===== Hero3 SMAF → OGG pipeline (R73) =====\n",
        f"Source dir: {SND}",
        f"Target dirs: {MID_DIR}, {WAV_DIR}, {OGG_DIR}",
        f"Files found: {len(files)}\n",
    ]

    tools = tool_status()
    log_lines.append("[Tool availability]")
    for k, v in tools.items():
        log_lines.append(f"  {'✓' if v else '✗'} {k:<18} = {v}")
    log_lines.append("")

    # 모든 도구 가용 여부
    can_smaf2mid = tools["java"] and tools["smaf_jar_exists"]
    can_mid2wav  = (tools["timidity"] or tools["fluidsynth"]) and tools["soundfont_exists"]
    can_wav2ogg  = tools["ffmpeg"]
    can_full     = can_smaf2mid and can_mid2wav and can_wav2ogg

    log_lines.append("[Stage capability]")
    log_lines.append(f"  Stage 1 SMAF→MIDI : {can_smaf2mid}")
    log_lines.append(f"  Stage 2 MIDI→WAV  : {can_mid2wav}")
    log_lines.append(f"  Stage 3 WAV→OGG   : {can_wav2ogg}")
    log_lines.append(f"  Full pipeline     : {can_full}")
    log_lines.append("")

    if not can_full:
        log_lines.append("⚠ Full pipeline 실행 불가. 다음 단계:")
        log_lines.append("   1. smaf-converter.jar 다운로드: https://github.com/antanas-vasiliauskas/smaf-converter")
        log_lines.append("      → tools/external/smaf-converter.jar 위치 또는 $SMAF_CONVERTER_JAR")
        log_lines.append("   2. TiMidity++ 설치: https://sourceforge.net/projects/timidity/")
        log_lines.append("      (대안: scoop/winget install fluidsynth)")
        log_lines.append("   3. SoundFont 다운로드 (예: FluidR3_GM.sf2)")
        log_lines.append("      → tools/external/FluidR3_GM.sf2 또는 $SOUNDFONT_PATH")
        log_lines.append("   4. FFmpeg 설치: winget install Gyan.FFmpeg")
        log_lines.append("   상세는 docs/h3/smaf_conversion_guide.md 참조.")
        log_lines.append("")

    # SMAF 헤더만이라도 분석 (always)
    headers: list[dict] = []
    log_lines.append("[SMAF header analysis (always available)]")
    smaf_valid_count = 0
    for path in files:
        data = path.read_bytes()
        h = parse_smaf_header(data)
        if h:
            smaf_valid_count += 1
            headers.append({"file": path.name, **h})
        else:
            headers.append({"file": path.name, "error": "not SMAF (missing MMMD magic)"})
    log_lines.append(f"  Valid SMAF (MMMD): {smaf_valid_count} / {len(files)}")
    log_lines.append("")

    # 변환 시도 (가능한 경우만)
    results: list[dict] = []
    if can_full:
        log_lines.append("[Full conversion attempts]")
        for path in files:
            stem = path.stem
            mid = MID_DIR / f"{stem}.mid"
            wav = WAV_DIR / f"{stem}.wav"
            ogg = OGG_DIR / f"{stem}.ogg"
            row = {"file": path.name, "smaf2mid": False, "mid2wav": False, "wav2ogg": False}

            # Stage 1
            row["smaf2mid"] = run_step(
                ["java", "-jar", SMAF_JAR, str(path), str(mid)],
                log_lines, f"SMAF→MIDI {stem}",
            ) and mid.exists() and mid.stat().st_size > 0

            # Stage 2
            if row["smaf2mid"]:
                if tools["timidity"]:
                    row["mid2wav"] = run_step(
                        ["timidity", "-Ow", "-o", str(wav), str(mid)],
                        log_lines, f"MIDI→WAV {stem}",
                    ) and wav.exists() and wav.stat().st_size > 0
                elif tools["fluidsynth"]:
                    row["mid2wav"] = run_step(
                        ["fluidsynth", "-F", str(wav), SOUNDFONT, str(mid)],
                        log_lines, f"MIDI→WAV {stem}",
                    ) and wav.exists() and wav.stat().st_size > 0

            # Stage 3
            if row["mid2wav"]:
                row["wav2ogg"] = run_step(
                    ["ffmpeg", "-y", "-i", str(wav), "-c:a", "libvorbis", "-q:a", "5", str(ogg)],
                    log_lines, f"WAV→OGG {stem}",
                ) and ogg.exists() and ogg.stat().st_size > 0

            mark = "✓" if row["wav2ogg"] else "✗"
            log_lines.append(f"  {mark} {path.name}: smaf2mid={row['smaf2mid']} mid2wav={row['mid2wav']} wav2ogg={row['wav2ogg']}")
            results.append(row)
    else:
        log_lines.append("[Conversion skipped — install tools first]")

    pass_count = sum(1 for r in results if r["wav2ogg"])
    if results:
        log_lines.append("")
        log_lines.append(f"Pipeline result: {pass_count} / {len(results)} files fully converted to OGG")

    report = {
        "tools": tools,
        "stage_capability": {
            "smaf2mid": can_smaf2mid,
            "mid2wav": can_mid2wav,
            "wav2ogg": can_wav2ogg,
            "full": can_full,
        },
        "smaf_valid_count": smaf_valid_count,
        "headers": headers,
        "conversion_results": results,
        "pass_count": pass_count,
    }
    JSON_OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    LOG.write_text("\n".join(log_lines), encoding="utf-8")

    print("\n".join(log_lines))
    print(f"\nWrote {JSON_OUT}")
    print(f"Wrote {LOG}")
    return 0 if (can_full and pass_count > 0) else 2


if __name__ == "__main__":
    sys.exit(main())
