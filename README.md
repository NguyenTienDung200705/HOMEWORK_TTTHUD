# Nạp Dữ Liệu Lớn IMDb Vào PostgreSQL Bằng Python – So Sánh Chi Tiết INSERT và COPY

Dự án thực hành nạp dữ liệu lớn thỏa mãn các tiêu chí:
- **Nhiều file:** Sử dụng bộ dữ liệu chuẩn **IMDb Non-Commercial Datasets** với 7 bảng quan hệ.
- **Mỗi file có hơn 1 triệu dòng:** Toàn bộ các file đều có từ 1,5 triệu đến 58 triệu dòng.
- **Có file / dataset vượt mốc 10 triệu dòng:** Có tới 5 file vượt 10 triệu dòng (`title.principals` ~58M, `title.akas` ~42M, `name.basics` ~14M, `title.basics` ~11M, `title.crew` ~11M).
- **Nạp vào CSDL quan hệ nhiều bảng:** 7 bảng có khóa chính, khóa ngoại, ràng buộc CHECK và chỉ mục.
- **2 phương pháp nạp bằng Python:** So sánh chuyên sâu giữa Nạp thủ công theo lô (`cur.executemany`) và Nạp hàng loạt (`COPY ... FROM STDIN`).
- **Ôn tập DDL / DML / CRUD:** Kịch bản thực hành và bài tập có lời giải xoay quanh nghiệp vụ điện ảnh.

---

## 1. Cấu Trúc Dự Án

| Thư mục / Tập tin | Vai trò |
|---|---|
| [`docs/REPORT.md`](docs/REPORT.md) | **Báo cáo kỹ thuật chi tiết**: Hướng dẫn thực hiện, phân tích đo lường và so sánh ưu/nhược điểm |
| [`docs/DATASETS.md`](docs/DATASETS.md) | Tài liệu chi tiết về bộ dữ liệu IMDb và các dataset > 10 triệu dòng khác (NYC TLC, Amazon Reviews...) |
| [`docs/ON_TAP_SQL.md`](docs/ON_TAP_SQL.md) | Hướng dẫn ôn tập lý thuyết DDL, DML, CRUD kèm bài tập |
| [`sql/01_create_tables.sql`](sql/01_create_tables.sql) | DDL tạo bảng trần (không chứa khóa/index để hỗ trợ đo lường nạp trước) |
| [`sql/02_constraints.sql`](sql/02_constraints.sql) | Tạo khóa chính, khóa ngoại, ràng buộc CHECK và chỉ mục (INDEX) |
| [`sql/03_crud_ddl_dml_review.sql`](sql/03_crud_ddl_dml_review.sql) | Kịch bản ôn tập DDL, CRUD, View, Window Function, UPSERT |
| [`sql/04_exercises.sql`](sql/04_exercises.sql) | Bộ bài tập thực hành SQL có lời giải chi tiết |
| [`src/download_imdb.py`](src/download_imdb.py) | Script tự động tải bộ dữ liệu chính thức từ https://datasets.imdbws.com/ |
| [`src/generate_data.py`](src/generate_data.py) | Script sinh dữ liệu giả lập chuẩn cấu trúc TSV của IMDb với tham số `--scale` |
| [`src/load_method1_insert.py`](src/load_method1_insert.py) | **Cách 1**: Nạp thủ công theo lô bằng Python `executemany` |
| [`src/load_method2_copy.py`](src/load_method2_copy.py) | **Cách 2**: Nạp hàng loạt tốc độ cao bằng PostgreSQL `COPY` |
| [`src/verify.py`](src/verify.py) | Kiểm chứng số dòng và đối chiếu hàm băm Checksum giữa các schema |
| [`src/summarize.py`](src/summarize.py) | Tổng hợp số liệu đo lường thành bảng báo cáo Markdown |

---

## 2. Hướng Dẫn Chạy Nhanh

### 2.1 Cài đặt môi trường
```bash
# Tạo môi trường ảo và cài đặt thư viện:
pip install -r requirements.txt

# Thiết lập chuỗi kết nối PostgreSQL (CSDL 'bigdata' cần tồn tại):
export DATABASE_URL="postgresql://postgres:matkhau@localhost:5432/bigdata"
# Trên Windows PowerShell:
# $env:DATABASE_URL="postgresql://postgres:matkhau@localhost:5432/bigdata"
```

### 2.2 Chuẩn bị dữ liệu

**Cách A: Tải dữ liệu thật từ IMDb:**
```bash
python src/download_imdb.py
```

**Cách B: Sinh dữ liệu giả lập chuẩn IMDb (Khuyên dùng khi thử nghiệm nhanh):**
```bash
# Sinh bản mẫu nhỏ (~585.000 dòng, hoàn thành trong 1 giây để test logic):
python src/generate_data.py --scale 0.01

# Hoặc sinh bản quy mô chuẩn (> 58,5 triệu dòng):
python src/generate_data.py --scale 1.0
```

### 2.3 Thực thi nạp và so sánh

```bash
# Cách 1: INSERT theo lô 10.000 dòng (Khóa tạo trước):
python src/load_method1_insert.py --schema m1

# Cách 2: COPY tốc độ cao (Khóa tạo trước):
python src/load_method2_copy.py --schema m2

# Cách 2 biến thể tối ưu: COPY bảng trần trước, tạo Khóa/Index SAU:
python src/load_method2_copy.py --schema m3 --defer-constraints

# Kiểm chứng tính toàn vẹn và đối chiếu checksum:
python src/verify.py m1 m2 m3

# Xuất báo cáo tổng kết:
python src/summarize.py
```

---

## 3. Kết Quả Đo Lường Nổi Bật

| Cấu hình | Thời gian nạp dữ liệu | Tạo Khóa/Index | **Tổng thời gian** | Thông lượng |
|---|---:|---:|---:|---:|
| Cách 1 – INSERT theo lô, Khóa tạo TRƯỚC | 915,4 s | 12,3 s | **927,7 s** | ~63.000 dòng/s |
| Cách 2 – COPY, Khóa tạo TRƯỚC | 480,5 s | 12,3 s | **492,8 s** | ~118.700 dòng/s |
| Cách 2 – COPY, Khóa tạo **SAU** (Tối ưu) | **42,8 s** | 68,1 s | **110,9 s** | **~527.500 dòng/s** |

- **COPY nhanh gấp ~1,9 lần so với INSERT** trong cùng điều kiện khóa tạo trước.
- **COPY kết hợp tạo Khóa sau (Deferred Constraints) nhanh gấp ~8,4 lần** so với INSERT theo lô truyền thống.
- Chi tiết phân tích kỹ thuật và so sánh ưu nhược điểm 10 tiêu chí: xem tại [`docs/REPORT.md`](docs/REPORT.md).
