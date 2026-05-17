"""Round 49 / 2PC-prep: 18 stack-cached call site의 정확한 함수 경계 식별."""
import subprocess
import sys
from pathlib import Path

SITES_TO_CHECK = [
    0x857ba, 0x85ab8, 0x85b2e, 0x85e98, 0x86062, 0x861d2, 0x862de, 0x86a34,
    0x87c60, 0x88a44, 0x88ed2, 0x89b2c, 0x8a06a, 0x8ad44, 0x8d890, 0x901c4, 0x905be,
]

# Use find_function_containing.py
script = Path("tools/recon/find_function_containing.py")
args = ["python", str(script)] + [hex(s) for s in SITES_TO_CHECK]
result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr, file=sys.stderr)
