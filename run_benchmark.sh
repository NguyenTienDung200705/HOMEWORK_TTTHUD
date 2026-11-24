#!/usr/bin/env bash
# Chạy tuần tự các bài đo hiệu năng nạp dữ liệu IMDb vào PostgreSQL.
set -euo pipefail
cd "$(dirname "$0")/src"
PY=${PYTHON:-python}

echo "======================================================================"
echo "##### 1/4. Cách 2: COPY tốc độ cao (Khóa/Index tạo TRƯỚC khi nạp)"
echo "======================================================================"
$PY load_method2_copy.py --schema m2

echo "======================================================================"
echo "##### 2/4. Cách 2 biến thể: COPY + Trì hoãn Khóa/Index SAU khi nạp"
echo "======================================================================"
$PY load_method2_copy.py --schema m3 --defer-constraints

echo "======================================================================"
echo "##### 3/4. Cách 1: INSERT theo lô 10.000 dòng (Khóa/Index tạo TRƯỚC)"
echo "======================================================================"
$PY load_method1_insert.py --schema m1

echo "======================================================================"
echo "##### 4/4. Kiểm chứng tính đồng nhất dữ liệu giữa các schema"
echo "======================================================================"
$PY verify.py m1 m2 m3

echo "======================================================================"
echo "##### TỔNG HỢP BÁO CÁO KẾT QUẢ"
echo "======================================================================"
$PY summarize.py
