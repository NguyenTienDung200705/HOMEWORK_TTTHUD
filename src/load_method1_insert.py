#!/usr/bin/env python3
"""CÁCH 1 – Nạp thủ công (manual insert) bằng Python: đọc TSV, ép kiểu, INSERT theo lô.

Quy trình cho mỗi bảng:
    Đọc TSV (hỗ trợ .tsv và .tsv.gz) -> chuyển kiểu từng ô ('\\N' -> None, int, str...)
    -> gom thành batch -> cursor.executemany("INSERT INTO ... VALUES (%s, ...)")
    -> COMMIT sau mỗi lô.

Tham số --batch-size:
    1       : mỗi dòng một INSERT + COMMIT (cực kỳ chậm, minh họa overhead giao dịch)
    10000   : mặc định, tối ưu thông lượng batch

Ví dụ:
    python src/load_method1_insert.py --schema m1
    python src/load_method1_insert.py --schema m1 --defer-constraints
    python src/load_method1_insert.py --schema m1_sample --batch-size 1000 --limit 50000
"""
import csv

from common import base_parser, open_data_file, run


def load_table(conn, table, path, limit, batch_size):
    cols = [c for c, _ in table["columns"]]
    convs = [f for _, f in table["columns"]]
    sql = (f"INSERT INTO {table['name']} ({', '.join(cols)}) "
           f"VALUES ({', '.join(['%s'] * len(cols))})")
    conn.autocommit = False
    n = 0

    with open_data_file(path, "rt") as f, conn.cursor() as cur:
        reader = csv.reader(f, delimiter="\t")
        # Bỏ qua dòng tiêu đề
        next(reader, None)
        batch = []
        for row in reader:
            if not row:
                continue
            # Đảm bảo số cột khớp hoặc đệm None nếu thiếu
            if len(row) < len(convs):
                row = row + ["\\N"] * (len(convs) - len(row))
            elif len(row) > len(convs):
                row = row[:len(convs)]

            batch.append(tuple(conv(v) for conv, v in zip(convs, row)))
            if len(batch) >= batch_size:
                cur.executemany(sql, batch)
                conn.commit()
                n += len(batch)
                batch.clear()
                if n % 500_000 < batch_size:
                    print(f"    ... {table['name']}: {n:,} dòng", flush=True)
                if limit and n >= limit:
                    break

        if batch and not (limit and n >= limit):
            cur.executemany(sql, batch)
            conn.commit()
            n += len(batch)

    conn.autocommit = True
    return n


if __name__ == "__main__":
    ap = base_parser(__doc__)
    ap.add_argument("--batch-size", type=int, default=10_000,
                    help="kích thước lô cho executemany (mặc định: 10000)")
    args = ap.parse_args()
    method = "method1_insert" + ("" if args.batch_size == 10_000 else f"_batch{args.batch_size}")
    run(method, args, lambda conn, t, p, lim: load_table(conn, t, p, lim, args.batch_size))
