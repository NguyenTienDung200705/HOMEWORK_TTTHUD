# Ôn tập SQL: CRUD, DML, DDL

Đi kèm hai file chạy được: `sql/03_crud_ddl_dml_review.sql` (ví dụ có chú thích, chạy từ đầu đến cuối) và
`sql/04_exercises.sql` (12 bài tập có lời giải). Cú pháp theo **PostgreSQL**; chỗ nào MySQL khác thì có ghi chú.

## 1. Bản đồ các nhóm lệnh

| Nhóm | Mục đích | Lệnh chính | Ghi chú |
|---|---|---|---|
| **DDL** – Data Definition | Định nghĩa/thay đổi **cấu trúc** | `CREATE`, `ALTER`, `DROP`, `TRUNCATE`, `RENAME` | Tác động lên bảng, index, view, schema… |
| **DML** – Data Manipulation | Thay đổi **dữ liệu** | `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `COPY` | Nằm trong giao dịch |
| **DQL** – Data Query | Đọc dữ liệu | `SELECT` | Một số giáo trình xếp SELECT vào DML |
| **DCL** – Data Control | Phân quyền | `GRANT`, `REVOKE` | |
| **TCL** – Transaction Control | Giao dịch | `BEGIN`, `COMMIT`, `ROLLBACK`, `SAVEPOINT` | |

**CRUD** là cách gọi theo thao tác của ứng dụng, ánh xạ sang SQL:

| CRUD | SQL | Điều cần nhớ |
|---|---|---|
| **C**reate | `INSERT` | Liệt kê cột rõ ràng; `RETURNING` để lấy khóa vừa sinh |
| **R**ead | `SELECT` | `WHERE` lọc dòng, `GROUP BY/HAVING` nhóm, `ORDER BY` + `LIMIT` |
| **U**pdate | `UPDATE … SET … WHERE` | **Quên `WHERE` = sửa mọi dòng** |
| **D**elete | `DELETE FROM … WHERE` | **Quên `WHERE` = xóa mọi dòng** |

## 2. DDL

```sql
CREATE TABLE employees (
    emp_id    integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name text          NOT NULL,
    email     text          UNIQUE,
    salary    numeric(12,2) NOT NULL DEFAULT 0 CHECK (salary >= 0),
    dept_id   integer       REFERENCES departments (dept_id) ON DELETE SET NULL
);
ALTER TABLE employees ADD COLUMN mobile text;              -- thêm cột
ALTER TABLE employees ALTER COLUMN mobile TYPE varchar(15);-- đổi kiểu
ALTER TABLE employees RENAME COLUMN mobile TO phone;       -- đổi tên
ALTER TABLE employees ADD CONSTRAINT chk CHECK (salary < 1e9);
ALTER TABLE employees DROP COLUMN phone;
CREATE INDEX idx_emp_dept ON employees (dept_id);
DROP TABLE employees;                                      -- xóa cả cấu trúc
```

**Ràng buộc (constraint):** `PRIMARY KEY` (duy nhất + không NULL), `UNIQUE` (duy nhất, cho phép NULL),
`NOT NULL`, `CHECK (điều kiện)`, `FOREIGN KEY … REFERENCES` (+ `ON DELETE CASCADE | SET NULL | RESTRICT`), `DEFAULT`.

### So sánh ba cách "xóa"

| | `DELETE` | `TRUNCATE` | `DROP TABLE` |
|---|---|---|---|
| Loại lệnh | DML | DDL | DDL |
| Xóa gì | các dòng theo `WHERE` | **toàn bộ** dòng | cả bảng (cấu trúc + dữ liệu) |
| Có `WHERE` | có | không | không |
| Tốc độ trên bảng lớn | chậm (xóa từng dòng, ghi log từng dòng) | rất nhanh | rất nhanh |
| Đặt lại bộ đếm identity | không | có với `RESTART IDENTITY` | – |
| Hoàn tác được | có (trong giao dịch) | có ở PostgreSQL; **MySQL thì không** | có ở PostgreSQL; MySQL không |

## 3. DML

```sql
-- INSERT
INSERT INTO departments (name) VALUES ('Kỹ thuật');                       -- 1 dòng
INSERT INTO departments (name) VALUES ('Nhân sự'), ('Kế toán');           -- nhiều dòng
INSERT INTO archive SELECT * FROM employees WHERE salary < 15e6;          -- từ truy vấn
INSERT INTO employees (full_name, email) VALUES ('An', 'an@x.vn') RETURNING emp_id;
-- Upsert: trùng khóa thì cập nhật / bỏ qua
INSERT INTO employees (full_name, email, salary) VALUES ('An', 'an@x.vn', 1)
ON CONFLICT (email) DO UPDATE SET salary = EXCLUDED.salary;               -- MySQL: ON DUPLICATE KEY UPDATE
ON CONFLICT (email) DO NOTHING;                                            -- MySQL: INSERT IGNORE

-- UPDATE
UPDATE employees SET salary = salary * 1.1 WHERE dept_id = 1;
UPDATE employees e SET salary = e.salary + 5e5
FROM departments d WHERE d.dept_id = e.dept_id AND d.name = 'Nhân sự';    -- cập nhật theo bảng khác

-- DELETE
DELETE FROM employees WHERE dept_id IS NULL;
DELETE FROM archive a USING employees e WHERE a.emp_id = e.emp_id;        -- xóa theo bảng khác

-- MERGE (PostgreSQL 15+, chuẩn SQL)
MERGE INTO employees e USING luong_moi n ON e.email = n.email
WHEN MATCHED THEN UPDATE SET salary = n.salary
WHEN NOT MATCHED THEN INSERT (full_name, email, salary) VALUES ('Mới', n.email, n.salary);
```

`COPY` (nạp/xuất hàng loạt từ/ra file) được giải thích kỹ trong `REPORT.md`.

## 4. Giao dịch (ACID) khi sửa dữ liệu

```sql
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;            -- hoặc ROLLBACK;  đặt SAVEPOINT để hoàn tác một phần
```

Thói quen an toàn khi `UPDATE`/`DELETE` trên dữ liệu thật:
1. Viết `SELECT` với **cùng điều kiện `WHERE`** trước, xem có đúng số dòng mong muốn không.
2. Mở `BEGIN;`, chạy lệnh sửa, kiểm tra kết quả, rồi mới `COMMIT;` (hoặc `ROLLBACK;`).
3. Dùng `RETURNING` để thấy ngay các dòng bị tác động.
4. Với bảng hàng chục triệu dòng, sửa/xóa **theo lô** (vd. 10.000–100.000 dòng/lần theo khoảng khóa chính) để không giữ khóa
   và không làm phình WAL.

## 5. Những lỗi ràng buộc thường gặp (xem Phần F của `03_crud_ddl_dml_review.sql`)

| Lỗi | Nguyên nhân | Mã lỗi PostgreSQL |
|---|---|---|
| `duplicate key value violates unique constraint` | chèn trùng PK/UNIQUE | `23505` |
| `violates check constraint` | vi phạm `CHECK` (vd. lương âm) | `23514` |
| `violates foreign key constraint` | tham chiếu/xóa bản ghi cha không hợp lệ | `23503` |
| `null value in column … violates not-null constraint` | thiếu giá trị cột `NOT NULL` | `23502` |
| `cannot insert a non-DEFAULT value into column … (GENERATED ALWAYS)` | tự gán giá trị cho cột identity | `428C9` |

## 6. PostgreSQL ↔ MySQL

| Nội dung | PostgreSQL | MySQL |
|---|---|---|
| Khóa tự tăng | `GENERATED … AS IDENTITY` / `SERIAL` | `AUTO_INCREMENT` |
| Lấy khóa vừa chèn | `RETURNING` | `LAST_INSERT_ID()` |
| Upsert | `ON CONFLICT … DO UPDATE` | `ON DUPLICATE KEY UPDATE` |
| DDL trong giao dịch | có thể `ROLLBACK` | tự `COMMIT` ngầm |
| Nạp hàng loạt | `COPY` / `\copy` | `LOAD DATA [LOCAL] INFILE` |
| `UPDATE … FROM`, `DELETE … USING` | có | cú pháp `UPDATE a JOIN b …` / `DELETE a FROM a JOIN b …` |

## 7. Bài tập (lời giải: `sql/04_exercises.sql`)

Dùng hai bảng `authors(author_id, name)` và `books(book_id, title, author_id, price, stock, published_on)`.

1. **DDL** – Tạo hai bảng với khóa chính tự tăng, `price >= 0`, `stock` mặc định 0, khóa ngoại `books.author_id`.
2. **INSERT** – Thêm 3 tác giả bằng *một* câu lệnh, rồi 5 cuốn sách.
3. **UPDATE** – Giảm 10% giá sách xuất bản trước 1950 còn hàng; in ra các dòng đã sửa.
4. **UPDATE … FROM** – Tăng 5.000 đồng cho mọi sách của tác giả "Nam Cao".
5. **DELETE** – Xóa sách chưa có ngày xuất bản và giá 0; in ra dòng đã xóa.
6. **SELECT** – Mỗi tác giả: số đầu sách, tổng tồn kho, giá cao nhất (tác giả chưa có sách vẫn hiện).
7. **ALTER** – Thêm cột `isbn UNIQUE`, đổi tên `stock` → `in_stock`, rồi xóa `isbn`.
8. **UPSERT** – Nhập kho: trùng tựa thì cộng thêm 10 vào tồn, chưa có thì thêm mới.
9. **Giao dịch** – Chuyển 5 cuốn tồn kho giữa hai sách trong một giao dịch.
10. **Ràng buộc** – Chứng minh khóa ngoại chặn xóa tác giả còn sách.
11. **TRUNCATE** – Xóa sạch `books` và đặt lại bộ đếm `book_id`.
12. **Tổng hợp** – Dùng CTE: xóa sách giá < 10.000 và ghi chúng vào `books_deleted` trong *một* câu lệnh.

Gợi ý tự kiểm tra: sau mỗi bài hãy `SELECT` lại để xác nhận số dòng thay đổi đúng như dự đoán.
