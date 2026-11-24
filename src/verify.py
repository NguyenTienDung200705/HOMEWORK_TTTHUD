#!/usr/bin/env python3
"""Kiểm chứng: dữ liệu nạp bằng các cách khác nhau phải GIỐNG HỆT nhau và khớp file TSV gốc.

Với mỗi schema: so số dòng với số dòng trong TSV, rồi so "checksum" (các phép tổng hợp đa thuộc tính)
giữa các schema để bảo đảm tính toàn vẹn dữ liệu tuyệt đối.

Sử dụng:
    python src/verify.py m1 m2
    python src/verify.py m1 m2 m3
"""
import gzip
import sys
from pathlib import Path

from common import DATA_DIR, TABLES, connect, resolve_data_file

# Mỗi bảng một biểu thức checksum bao phủ cả cột số, NULL, chuỗi và độ dài
CHECKSUMS = {
    "name_basics": (
        "sum(length(primary_name)) || '/' || "
        "count(*) filter (where death_year is not null) || '/' || "
        "sum(coalesce(birth_year, 0)::bigint)"
    ),
    "title_basics": (
        "sum(length(primary_title)) || '/' || "
        "count(*) filter (where start_year is null) || '/' || "
        "sum(coalesce(runtime_minutes, 0)::bigint) || '/' || "
        "sum(coalesce(is_adult, 0)::bigint)"
    ),
    "title_ratings": (
        "sum(average_rating) || '/' || "
        "sum(num_votes::bigint)"
    ),
    "title_crew": (
        "count(*) filter (where directors is null) || '/' || "
        "count(*) filter (where writers is null) || '/' || "
        "sum(length(coalesce(directors, '')))"
    ),
    "title_episode": (
        "sum(coalesce(season_number, 0)::bigint) || '/' || "
        "sum(coalesce(episode_number, 0)::bigint)"
    ),
    "title_principals": (
        "sum(ordering::bigint) || '/' || "
        "count(*) filter (where characters is null) || '/' || "
        "sum(length(category))"
    ),
    "title_akas": (
        "sum(ordering::bigint) || '/' || "
        "sum(length(title)) || '/' || "
        "count(*) filter (where is_original_title = 1)"
    ),
}


def count_tsv_rows(path: Path) -> int:
    """Đếm số dòng của file .tsv hoặc .tsv.gz nhanh bằng buffer."""
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as f:
        total_lines = sum(chunk.count(b"\n") for chunk in iter(lambda: f.read(1 << 24), b""))
    return max(0, total_lines - 1)  # Trừ 1 dòng header


def main(schemas):
    if not schemas:
        print("Cách dùng: python src/verify.py <schema1> <schema2> [schema3...]")
        sys.exit(1)

    # Chỉ kiểm tra những bảng có file tồn tại trong data/
    active_tables = []
    expected_rows = {}
    for t in TABLES:
        p = resolve_data_file(t["file"])
        if p:
            active_tables.append(t)
            print(f"[ĐẾM DÒNG FILE] Đang đếm {p.name}...", end="", flush=True)
            cnt = count_tsv_rows(p)
            expected_rows[t["name"]] = cnt
            print(f" -> {cnt:,} dòng")

    if not active_tables:
        print("[LỖI] Không tìm thấy dữ liệu nào để đối chiếu trong thư mục data/!")
        sys.exit(1)

    ok = True
    sig = {}
    print("\n=== ĐỐI CHIẾU SỐ DÒNG VÀ CHECKSUM VỚI CƠ SỞ DỮ LIỆU ===")
    for s in schemas:
        conn = connect(s)
        for t in active_tables:
            n = conn.execute(f"SELECT count(*) FROM {t['name']}").fetchone()[0]
            cs = conn.execute(f"SELECT {CHECKSUMS[t['name']]} FROM {t['name']}").fetchone()[0]
            sig[(s, t["name"])] = cs
            match_file = (n == expected_rows[t["name"]])
            flag = "OK " if match_file else "LỆCH"
            ok &= match_file
            print(f"{flag} [{s:<4}] {t['name']:<18} DB: {n:>12,} | File: {expected_rows[t['name']]:>12,} | Checksum: {cs}")
        conn.close()

    print("\n=== SO SÁNH CHECKSUM GIỮA CÁC SCHEMA NẠP ===")
    for t in active_tables:
        vals = {sig[(s, t["name"])] for s in schemas}
        same = len(vals) == 1
        ok &= same
        status = "OK " if same else "LỆCH"
        print(f"{status} Checksum bảng {t['name']:<18} giữa [{', '.join(schemas)}]: {'KHỚP HOÀN TOÀN' if same else 'BỊ LỆCH'}")

    print("\n" + "=" * 50)
    print("KẾT LUẬN CUỐI CÙNG:", "TẤT CẢ DỮ LIỆU KHỚP TUYỆT ĐỐI ✔" if ok else "CÓ SAI LỆCH DỮ LIỆU ❌")
    print("=" * 50)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(sys.argv[1:])
