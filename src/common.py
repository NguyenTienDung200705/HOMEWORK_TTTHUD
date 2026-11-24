"""Cấu hình và hàm dùng chung cho hai cách nạp dữ liệu IMDb vào PostgreSQL.

Hai script load_method1_insert.py và load_method2_copy.py dùng CÙNG schema, CÙNG file TSV,
CÙNG cách đo thời gian; chỉ khác phần "nạp dữ liệu" nên so sánh là công bằng.
"""
import argparse
import gzip
import json
import os
import platform
import re
import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("DATA_DIR", ROOT / "data"))
SQL_DIR = ROOT / "sql"
RESULTS_DIR = ROOT / "results"

# Chuỗi kết nối; ghi đè bằng biến môi trường DATABASE_URL
# ví dụ: postgresql://postgres:matkhau@localhost:5432/bigdata
DSN = os.environ.get("DATABASE_URL", "host=127.0.0.1 port=5432 dbname=bigdata user=postgres")


def _nullable(fn):
    return lambda s: None if s in ("", r"\N", "\\N", "None", None) else fn(s)


# Mỗi bảng: tên, file TSV, danh sách (cột, hàm chuyển kiểu từ chuỗi TSV).
# Thứ tự trong TABLES là thứ tự nạp: bảng cha trước, bảng con sau (để thỏa khóa ngoại).
TABLES = [
    dict(name="name_basics", file="name.basics.tsv", columns=[
        ("nconst", str),
        ("primary_name", str),
        ("birth_year", _nullable(int)),
        ("death_year", _nullable(int)),
        ("primary_profession", _nullable(str)),
        ("known_for_titles", _nullable(str)),
    ]),
    dict(name="title_basics", file="title.basics.tsv", columns=[
        ("tconst", str),
        ("title_type", str),
        ("primary_title", str),
        ("original_title", _nullable(str)),
        ("is_adult", _nullable(int)),
        ("start_year", _nullable(int)),
        ("end_year", _nullable(int)),
        ("runtime_minutes", _nullable(int)),
        ("genres", _nullable(str)),
    ]),
    dict(name="title_ratings", file="title.ratings.tsv", columns=[
        ("tconst", str),
        ("average_rating", Decimal),
        ("num_votes", int),
    ]),
    dict(name="title_crew", file="title.crew.tsv", columns=[
        ("tconst", str),
        ("directors", _nullable(str)),
        ("writers", _nullable(str)),
    ]),
    dict(name="title_episode", file="title.episode.tsv", columns=[
        ("tconst", str),
        ("parent_tconst", str),
        ("season_number", _nullable(int)),
        ("episode_number", _nullable(int)),
    ]),
    dict(name="title_principals", file="title.principals.tsv", columns=[
        ("tconst", str),
        ("ordering", int),
        ("nconst", str),
        ("category", str),
        ("job", _nullable(str)),
        ("characters", _nullable(str)),
    ]),
    dict(name="title_akas", file="title.akas.tsv", columns=[
        ("title_id", str),
        ("ordering", int),
        ("title", str),
        ("region", _nullable(str)),
        ("language", _nullable(str)),
        ("types", _nullable(str)),
        ("attributes", _nullable(str)),
        ("is_original_title", _nullable(int)),
    ]),
]


def resolve_data_file(filename: str) -> Path | None:
    """Tìm file dữ liệu dạng thô (.tsv) hoặc nén (.tsv.gz)."""
    p_tsv = DATA_DIR / filename
    if p_tsv.exists():
        return p_tsv
    p_gz = DATA_DIR / f"{filename}.gz"
    if p_gz.exists():
        return p_gz
    return None


def open_data_file(path: Path, mode: str = "rt"):
    """Mở file dữ liệu trong suốt dù là text thường hay .gz."""
    is_text = "t" in mode or ("b" not in mode)
    if path.suffix == ".gz":
        return gzip.open(path, mode=mode, encoding="utf-8" if is_text else None, newline="" if is_text else None)
    return open(path, mode=mode, encoding="utf-8" if is_text else None, newline="" if is_text else None)


def base_parser(description: str) -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--schema", required=True, help="tên schema PostgreSQL sẽ tạo mới (vd: m1)")
    ap.add_argument("--defer-constraints", action="store_true",
                    help="nạp dữ liệu TRƯỚC, rồi mới tạo khóa/ràng buộc/index (nhanh hơn)")
    ap.add_argument("--tables", nargs="*", help="chỉ nạp các bảng này (mặc định: tất cả bảng có file trong data/)")
    ap.add_argument("--limit", type=int, default=0,
                    help="chỉ nạp tối đa N dòng mỗi bảng (0 = tất cả); dùng để đo mẫu nhanh.")
    return ap


def connect(schema: str) -> psycopg.Connection:
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", schema):
        raise SystemExit(f"Tên schema không hợp lệ: {schema!r}")
    conn = psycopg.connect(DSN, autocommit=True)
    conn.execute(f"SET search_path TO {schema}")
    return conn


def run_sql_file(conn, name: str) -> float:
    t = time.perf_counter()
    sql_content = (SQL_DIR / name).read_text(encoding="utf-8")
    conn.execute(sql_content)
    return time.perf_counter() - t


def run(method: str, args, load_table_fn) -> dict:
    """Khung chạy chung: tạo schema -> (ràng buộc) -> nạp từng bảng -> (ràng buộc) -> đo kích thước."""
    # Lọc danh sách bảng muốn nạp
    selected_tables = [t for t in TABLES if not args.tables or t["name"] in args.tables]
    # Chỉ nạp những bảng có file dữ liệu tồn tại trong DATA_DIR
    tables = []
    for t in selected_tables:
        fpath = resolve_data_file(t["file"])
        if fpath:
            tables.append((t, fpath))
        else:
            print(f"[CẢNH BÁO] Không tìm thấy {t['file']} (hoặc .gz) trong {DATA_DIR}, bỏ qua bảng {t['name']}")

    if not tables:
        raise SystemExit(f"LỖI: Không tìm thấy bất kỳ file dataset nào trong {DATA_DIR}!")

    conn = connect("public")
    conn.execute(f"DROP SCHEMA IF EXISTS {args.schema} CASCADE")
    conn.execute(f"CREATE SCHEMA {args.schema}")
    conn.close()
    conn = connect(args.schema)

    result = {
        "method": method, "schema": args.schema, "defer_constraints": args.defer_constraints,
        "limit": args.limit, "started": datetime.now().isoformat(timespec="seconds"),
        "host": f"{platform.system()} {platform.release()}, Python {platform.python_version()}",
        "postgres": conn.execute("SHOW server_version").fetchone()[0],
        "tables": {}, "timing": {},
    }
    result["timing"]["create_tables_s"] = round(run_sql_file(conn, "01_create_tables.sql"), 3)
    if not args.defer_constraints:
        result["timing"]["constraints_before_load_s"] = round(run_sql_file(conn, "02_constraints.sql"), 3)

    t_load = time.perf_counter()
    for t, path in tables:
        t0 = time.perf_counter()
        rows = load_table_fn(conn, t, path, args.limit)
        dt = time.perf_counter() - t0
        dt_effective = max(dt, 0.0001)
        result["tables"][t["name"]] = {"rows": rows, "seconds": round(dt, 2), "rows_per_s": round(rows / dt_effective)}
        print(f"[{method}] {t['name']:<18} {rows:>12,} dòng  {dt:8.2f}s  {rows/dt_effective:>10,.0f} dòng/s", flush=True)
    result["timing"]["load_only_s"] = round(time.perf_counter() - t_load, 2)

    if args.defer_constraints:
        result["timing"]["constraints_after_load_s"] = round(run_sql_file(conn, "02_constraints.sql"), 2)
        print(f"[{method}] tạo khóa/ràng buộc/index sau khi nạp: {result['timing']['constraints_after_load_s']}s", flush=True)

    conn.execute("ANALYZE")
    # Tổng = tạo bảng + ràng buộc (trước hoặc sau) + nạp dữ liệu
    result["timing"]["total_s"] = round(sum(v for k, v in result["timing"].items() if k != "total_s"), 2)
    size = conn.execute(
        "SELECT pg_size_pretty(sum(pg_total_relation_size(c.oid))), sum(pg_total_relation_size(c.oid)) "
        "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = %s AND c.relkind = 'r'", (args.schema,)).fetchone()
    result["db_size"], result["db_size_bytes"] = size[0], int(size[1]) if size and size[1] else 0
    result["total_rows"] = sum(v["rows"] for v in result["tables"].values())
    conn.close()

    suffix = "_deferred" if args.defer_constraints else ""
    if args.limit:
        suffix += f"_limit{args.limit}"
    out = RESULTS_DIR / f"{method}{suffix}.json"
    RESULTS_DIR.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[{method}] TỔNG: {result['timing']['total_s']}s; "
          f"{result['total_rows']:,} dòng; dung lượng {result['db_size']} -> {out.name}", flush=True)
    return result
