### Thời gian nạp từng bảng (giây)

| Bảng | Số dòng | Cách 1 – INSERT, khóa tạo TRƯỚC | Cách 1 – INSERT, khóa tạo SAU | Cách 2 – COPY, khóa tạo TRƯỚC | Cách 2 – COPY, khóa tạo SAU |
|---|---:|---:|---:|---:|---:|
| customers | 1,200,000 | 12.2 | 16.8 | 4.1 | 1.1 |
| products | 1,100,000 | 11.0 | 17.7 | 1.5 | 0.9 |
| orders | 2,000,000 | 36.5 | 28.3 | 19.6 | 1.1 |
| order_items | 5,000,000 | 127.2 | 75.9 | 87.5 | 3.1 |
| reviews | 1,500,000 | 44.7 | 23.1 | 25.6 | 1.1 |
| events | 12,000,000 | 141.2 | 170.6 | 59.6 | 9.5 |

### Tổng kết

| Cấu hình | Nạp dữ liệu (s) | Tạo khóa/index sau (s) | **Tổng (s)** | Thông lượng tổng (dòng/s) | Dung lượng DB |
|---|---:|---:|---:|---:|---:|
| Cách 1 – INSERT, khóa tạo TRƯỚC | 372.9 | 0.0 (trước) | **372.9** | 61,146 | 2612 MB |
| Cách 1 – INSERT, khóa tạo SAU | 332.5 | 25.2 | **357.7** | 63,737 | 2425 MB |
| Cách 2 – COPY, khóa tạo TRƯỚC | 198.0 | 0.0 (trước) | **198.0** | 115,163 | 2613 MB |
| Cách 2 – COPY, khóa tạo SAU | 16.7 | 28.6 | **45.3** | 502,978 | 2427 MB |

### Hệ số so với 'Cách 2 – COPY, khóa tạo TRƯỚC' (tổng thời gian)

- Cách 1 – INSERT, khóa tạo TRƯỚC: 1.88×
- Cách 1 – INSERT, khóa tạo SAU: 1.81×
- Cách 2 – COPY, khóa tạo TRƯỚC: 1.00×
- Cách 2 – COPY, khóa tạo SAU: 0.23×
- Cách 1 / Cách 2 khi cùng tạo khóa SAU: 7.9×
- Chỉ riêng phần nạp (bảng trần, không khóa/index): Cách 1 332.5s vs Cách 2 16.7s = 19.9×

### Độ nhạy theo kích thước lô – Cách 1 (bảng customers, 20.000 dòng, mỗi lô một COMMIT)

| Kích thước lô | Thời gian (s) | Dòng/s |
|---:|---:|---:|
| 1 | 8.66 | 2,309 |
| 10 | 1.69 | 11,867 |
| 100 | 0.41 | 48,972 |
| 1,000 | 0.29 | 68,934 |
| 10,000 | 0.21 | 94,432 |
