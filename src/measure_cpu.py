#!/usr/bin/env python3
"""Đo CPU của tiến trình Python (phía client) khi nạp 1.000.000 dòng bảng events bằng từng cách.

Mục đích: kiểm chứng xem nút thắt cổ chai nằm ở Python (Cách 1) hay ở server (Cách 2).
CPU của server PostgreSQL KHÔNG nằm trong số này.
Dùng:  python src/measure_cpu.py
"""
import os
import subprocess
import sys
import time
from pathlib import Path

from common import RESULTS_DIR, connect

HERE = Path(__file__).resolve().parent
ROWS = 1_000_000

for script in ["load_method1_insert.py", "load_method2_copy.py"]:
    schema = "cpu_" + script.split("_")[1][:7]
    t0 = time.perf_counter()
    p = subprocess.Popen([sys.executable, str(HERE / script), "--schema", schema, "--tables", "events",
                          "--limit", str(ROWS)], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    _, status, ru = os.wait4(p.pid, 0)          # rusage RIÊNG của tiến trình con này
    wall = time.perf_counter() - t0
    err = p.stderr.read().decode()
    if status != 0:
        raise SystemExit(f"{script} lỗi:\n{err[-600:]}")
    cpu = ru.ru_utime + ru.ru_stime
    print(f"{script:<24} wall={wall:5.1f}s  python_cpu={cpu:5.1f}s (user {ru.ru_utime:.1f} + sys {ru.ru_stime:.1f})  "
          f"=> Python bận {100 * cpu / wall:3.0f}% thời gian")
    c = connect("public")
    c.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
    c.close()
    for f in RESULTS_DIR.glob(f"*limit{ROWS}*.json"):   # không giữ file kết quả của lần đo phụ này
        f.unlink()
