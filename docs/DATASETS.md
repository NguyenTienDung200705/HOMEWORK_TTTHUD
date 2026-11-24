# Tài liệu Bộ Dữ liệu: IMDb Non-Commercial Datasets & Các Dataset Lớn

---

## 1. Giới thiệu bộ dữ liệu chính: IMDb Non-Commercial Datasets

Dự án sử dụng bộ dữ liệu chính thức **IMDb Non-Commercial Datasets**, được cung cấp trực tiếp bởi IMDb tại địa chỉ:
- Cổng thông tin: [https://developer.imdb.com/non-commercial-datasets/](https://developer.imdb.com/non-commercial-datasets/)
- Đường dẫn tải trực tiếp: [https://datasets.imdbws.com/](https://datasets.imdbws.com/)
- Điều khoản cấp phép: Miễn phí cho mục đích học tập, nghiên cứu và phi thương mại.

### Định dạng và đặc điểm kỹ thuật
- **Định dạng file:** Tab-Separated Values (TSV, `.tsv`), được lưu trữ dạng nén `.tsv.gz` (gzip).
- **Mã hóa:** UTF-8.
- **Giá trị rỗng (NULL):** Được biểu diễn bằng chuỗi `\N`.
- **Dòng tiêu đề:** Dòng đầu tiên của mỗi file chứa tên cột.
- **Dấu phân cách:** Ký tự tab (`\t`). Ký tự ngoặc kép `"` trong tên phim là ký tự nguyên bản, không dùng để đóng gói chuỗi (TSV thuần túy).

---

## 2. Thỏa mãn các tiêu chí của đề bài

Đề bài yêu cầu:
1. **Có nhiều file (.csv, .tsv, .txt...):** Bộ IMDb cung cấp **7 file dữ liệu độc lập** liên kết chặt chẽ qua các khóa `tconst` và `nconst`.
2. **Mỗi file có hơn 1 triệu dòng:** Toàn bộ 7 file đều có từ 1,5 triệu dòng đến hơn 58 triệu dòng.
3. **Có dataset / file có hơn 10 triệu dòng:** Có tới **5 file vượt mốc 10 triệu dòng** (`name.basics`, `title.basics`, `title.crew`, `title.akas`, `title.principals`).

### Bảng thống kê chi tiết các file trong bộ IMDb

| Tên file nén | Bảng tương ứng | Số dòng thực tế (xấp xỉ) | Kích thước file nén (.gz) | Kích thước giải nén (.tsv) | Khóa chính / Khóa ngoại | Thỏa điều kiện |
|---|---|---:|---:|---:|---|:---:|
| `title.basics.tsv.gz` | `title_basics` | **~11.000.000** | ~180 MB | ~950 MB | PK: `tconst` | **> 10 triệu** ✔ |
| `name.basics.tsv.gz` | `name_basics` | **~14.000.000** | ~280 MB | ~1.100 MB | PK: `nconst` | **> 10 triệu** ✔ |
| `title.ratings.tsv.gz` | `title_ratings` | **~1.550.000** | ~7 MB | ~28 MB | PK/FK: `tconst` → `title_basics` | **> 1 triệu** ✔ |
| `title.crew.tsv.gz` | `title_crew` | **~11.000.000** | ~65 MB | ~310 MB | PK/FK: `tconst` → `title_basics` | **> 10 triệu** ✔ |
| `title.episode.tsv.gz` | `title_episode` | **~8.200.000** | ~45 MB | ~210 MB | PK/FK: `tconst`, FK: `parentTconst` | **> 1 triệu** ✔ |
| `title.principals.tsv.gz` | `title_principals` | **~58.000.000** | ~550 MB | ~2.900 MB | PK: (`tconst`, `ordering`), FK → titles, names | **> 10 triệu** ✔ |
| `title.akas.tsv.gz` | `title_akas` | **~42.000.000** | ~380 MB | ~2.100 MB | PK: (`titleId`, `ordering`), FK → titles | **> 10 triệu** ✔ |
| **Tổng cộng** | **7 bảng quan hệ** | **~145.750.000** | **~1,5 GB** | **~7,6 GB** | **Mô hình phim ảnh hoàn chỉnh** | **Đạt xuất sắc** |

---

## 3. Cấu trúc trường dữ liệu của từng bảng IMDb

### 1. `title_basics` (`title.basics.tsv`)
- `tconst` (string, PK): Mã định danh duy nhất của tác phẩm (vd: `tt0000001`).
- `titleType` (string): Thể loại sản phẩm (`movie`, `short`, `tvSeries`, `tvEpisode`, `video`...).
- `primaryTitle` (string): Tên phát hành thương mại phổ biến.
- `originalTitle` (string): Tên gốc của tác phẩm.
- `isAdult` (int): 0: Không phải nội dung người lớn; 1: Nội dung người lớn.
- `startYear` (int): Năm bắt đầu phát hành (`YYYY`).
- `endYear` (int): Năm kết thúc đối với TV Series (`YYYY`), hoặc `\N`.
- `runtimeMinutes` (int): Thời lượng tác phẩm tính theo phút.
- `genres` (string): Danh sách thể loại cách nhau bởi dấu phẩy (tối đa 3 thể loại).

### 2. `name_basics` (`name.basics.tsv`)
- `nconst` (string, PK): Mã định danh nhân sự/nghệ sĩ (vd: `nm0000001`).
- `primaryName` (string): Họ và tên phổ biến nhất.
- `birthYear` (int): Năm sinh (`YYYY`).
- `deathYear` (int): Năm mất nếu có, hoặc `\N`.
- `primaryProfession` (string): Top 3 nghề nghiệp chính cách nhau bởi dấu phẩy.
- `knownForTitles` (string): Danh sách mã `tconst` các tác phẩm tiêu biểu.

### 3. `title_ratings` (`title.ratings.tsv`)
- `tconst` (string, PK, FK): Mã tác phẩm tham chiếu đến `title_basics`.
- `averageRating` (numeric): Điểm đánh giá trung bình theo trọng số (thang điểm 1.0 - 10.0).
- `numVotes` (int): Tổng số lượt bình chọn từ người dùng.

### 4. `title_crew` (`title.crew.tsv`)
- `tconst` (string, PK, FK): Mã tác phẩm tham chiếu đến `title_basics`.
- `directors` (string): Danh sách các mã `nconst` đạo diễn.
- `writers` (string): Danh sách các mã `nconst` biên kịch.

### 5. `title_episode` (`title.episode.tsv`)
- `tconst` (string, PK, FK): Mã định danh tập phim (tham chiếu `title_basics`).
- `parentTconst` (string, FK): Mã định danh TV Series cha (tham chiếu `title_basics`).
- `seasonNumber` (int): Mùa phát sóng.
- `episodeNumber` (int): Số thứ tự tập trong mùa.

### 6. `title_principals` (`title.principals.tsv`)
- `tconst` (string, PK, FK): Tham chiếu `title_basics`.
- `ordering` (int, PK): Thứ tự xuất hiện trong danh sách vai diễn / đoàn làm phim.
- `nconst` (string, FK): Tham chiếu `name_basics`.
- `category` (string): Vai trò (`actor`, `actress`, `director`, `producer`...).
- `job` (string): Chức danh cụ thể nếu có.
- `characters` (string): Tên nhân vật đảm nhận (định dạng mảng JSON hoặc chuỗi).

### 7. `title_akas` (`title.akas.tsv`)
- `titleId` (string, PK, FK): Tham chiếu `title_basics`.
- `ordering` (int, PK): Thứ tự định danh của tiêu đề phụ.
- `title` (string): Tên phát hành theo vùng/ngôn ngữ địa phương.
- `region` (string): Mã quốc gia/vùng (vd: `US`, `VN`, `FR`).
- `language` (string): Ngôn ngữ của tiêu đề.
- `types` / `attributes`: Ghi chú định danh bổ sung.
- `isOriginalTitle` (int): 0 hoặc 1.

---

## 4. Các Dataset Khác Thỏa Mãn Điều Kiện Hơn 10 Triệu Dòng

Theo yêu cầu mở rộng của đề tài (*"nếu tìm được thêm một dataset khác có nhiều hơn 10 triệu dòng thì rất tốt"*), dưới đây là các bộ dữ liệu lớn uy tín trong giới khoa học dữ liệu và kỹ thuật dữ liệu:

### 1. NYC TLC Trip Record Data (New York City Taxi & Limousine Commission)
- **Nguồn:** [https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
- **Quy mô:** Hơn **30 - 40 triệu dòng mỗi năm** (mỗi tháng một file chứa từ 2 đến 4 triệu dòng). Dữ liệu lịch sử tích lũy từ 2009 đến nay đạt hơn **1 tỷ dòng**.
- **Định dạng:** Apache Parquet (các phiên bản cũ cung cấp CSV).
- **Nội dung:** Ghi nhận từng chuyến xe taxi vàng (Yellow Taxi), taxi xanh (Green Taxi) và xe công nghệ (For-Hire Vehicles - Uber/Lyft), bao gồm thời gian đón/trả, tọa độ GPS, cự ly, giá cước, tiền tip, hình thức thanh toán.

### 2. Amazon Product Reviews 2023 (UCSD / McAuley Lab)
- **Nguồn:** [https://amazon-reviews-2023.github.io/](https://amazon-reviews-2023.github.io/)
- **Quy mô:** Hơn **571 triệu dòng đánh giá** (reviews) và 48 triệu sản phẩm (metadata).
- **Định dạng:** JSONLines (`.jsonl.gz`).
- **Nội dung:** Lịch sử đánh giá của khách hàng trên sàn thương mại điện tử Amazon qua nhiều danh mục (Sách, Điện tử, Thời trang...). Phù hợp cho bài toán phân tích đánh giá, khuyến nghị sản phẩm và nạp kho dữ liệu phân tích (OLAP).

### 3. MovieLens 25M / 32M (GroupLens Research)
- **Nguồn:** [https://grouplens.org/datasets/movielens/](https://grouplens.org/datasets/movielens/)
- **Quy mô:** File `ratings.csv` chứa **25 đến 32 triệu dòng**, `genome-scores.csv` chứa **15 triệu dòng**.
- **Định dạng:** CSV chuẩn.
- **Nội dung:** Điểm đánh giá (1-5 sao) và nhãn tag của hàng trăm nghìn người dùng đối với các bộ phim điện ảnh.

### 4. Wikipedia Pageviews & Clickstream Dumps
- **Nguồn:** [https://dumps.wikimedia.org/other/pageview_complete/](https://dumps.wikimedia.org/other/pageview_complete/)
- **Quy mô:** Hàng trăm triệu dòng mỗi tháng, hàng tỷ lượt clickstream ghi nhận hành vi chuyển hướng giữa các bài viết trên bách khoa toàn thư mở Wikipedia.
- **Định dạng:** TSV nén gzip.

---

## 5. Hướng Dẫn Tải và Sử Dụng Dữ Liệu IMDb trong Dự Án

### Cách 1: Tải trực tiếp dữ liệu chính thức bằng script Python
Dự án cung cấp sẵn công cụ `src/download_imdb.py`:
```bash
# Tải toàn bộ 7 file chính thức vào thư mục data/
python src/download_imdb.py

# Hoặc chỉ tải một số bảng mong muốn:
python src/download_imdb.py --tables title.basics name.basics title.ratings

# Nếu muốn tự động giải nén sang .tsv:
python src/download_imdb.py --decompress
```
*(Lưu ý: Bộ nạp của dự án hỗ trợ đọc trực tiếp file `.tsv.gz` dạng stream, do đó bạn **không bắt buộc phải giải nén** giúp tiết kiệm đáng kể dung lượng ổ cứng).*

### Cách 2: Sinh dữ liệu giả lập chuẩn cấu trúc IMDb (Khuyên dùng khi kiểm thử nhanh)
Nếu đang làm việc trong môi trường hạn chế băng thông hoặc không đủ dung lượng ổ đĩa cho 10-20 GB dữ liệu thô:
```bash
# Sinh dữ liệu mẫu nhỏ (~585 nghìn dòng) để chạy kiểm thử logic trong 1-2 giây:
python src/generate_data.py --scale 0.01

# Sinh dữ liệu quy mô vừa (~2,9 triệu dòng, các file > 1 triệu dòng):
python src/generate_data.py --scale 0.05

# Sinh dữ liệu toàn phần (~58,5 triệu dòng, thỏa mãn > 10 triệu dòng):
python src/generate_data.py --scale 1.0
```
Dữ liệu sinh ra tuân thủ tuyệt đối cấu trúc cột, kiểu dữ liệu, định dạng `\t`, giá trị `\N` và quan hệ khóa chính/khóa ngoại của IMDb.
