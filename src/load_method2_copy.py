#!/usr/bin/env python3
"""CÁCH 2 – Nạp hàng loạt tốc độ cao (bulk load) bằng lệnh COPY của PostgreSQL.

Python hoạt động như một đường ống dữ liệu (pipeline) hiệu năng cao:
đọc file theo khối (1 MB) và truyền trực tiếp vào stream COPY ... FROM STDIN của PostgreSQL.
Engine PostgreSQL bằng mã C đảm nhiệm hoàn toàn việc phân giải TSV, chuyển đổi kiểu,
và ghi tuần tự vào các trang bảng (table pages).

Hỗ trợ trực tiếp cả file text TSV và file nén .tsv.gz (giải nén on-the-fly dạng stream).

Mỗi bảng được nạp trong MỘT giao dịch duy nhất.

Ví dụ:
    python src/load_method2_copy.py --schema m2
    python src/load_method2_copy.py --schema m3 --defer-constraints   # nạp trước, tạo khóa/index sau
"""
import gzip
from common import base_parser, run

CHUNK_BYTES = 1 << 20  # 1 MB chunk


def load_table(conn, table, path, limit):
    cols = ", ".join(c for c, _ in table["columns"])
    # Định dạng TSV của IMDb: tab-separated, null là \N, trích dẫn tắt bằng QUOTE E'\b' để tránh lỗi ký tự ngoặc kép trong tên phim
    stmt = (
        f"COPY {table['name']} ({cols}) FROM STDIN WITH "
        f"(FORMAT csv, DELIMITER E'\\t', QUOTE E'\\b', ESCAPE '\\', NULL '\\N', HEADER true)"
    )
    conn.autocommit = False

    opener = gzip.open if path.suffix == ".gz" else open

    with opener(path, "rb") as f, conn.cursor() as cur:
        with cur.copy(stmt) as cp:
            if limit:
                # Chế độ đo mẫu: chỉ đọc header + limit dòng đầu
                for _ in range(limit + 1):
                    line = f.readline()
                    if not line:
                        break
                    cp.write(line)
            else:
                while chunk := f.read(CHUNK_BYTES):
                    cp.write(chunk)
        n = cur.rowcount

    conn.commit()
    conn.autocommit = True
    return n


if __name__ == "__main__":
    args = base_parser(__doc__).parse_args()
    method = "method2_copy"
    run(method, args, load_table)
