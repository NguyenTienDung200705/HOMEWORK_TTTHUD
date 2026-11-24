#!/usr/bin/env python3
"""Tải bộ dữ liệu chính thức IMDb Non-Commercial Datasets từ https://datasets.imdbws.com/

IMDb cung cấp các file nén dạng .tsv.gz, cập nhật hàng ngày.
Script này hỗ trợ tải có thanh tiến trình, kiểm tra file và tùy chọn giải nén sang .tsv.

Ví dụ sử dụng:
    python src/download_imdb.py                      # Tải toàn bộ các bảng vào data/
    python src/download_imdb.py --tables title.basics title.ratings
    python src/download_imdb.py --decompress         # Giải nén .tsv.gz thành .tsv sau khi tải
"""
import argparse
import gzip
import os
import shutil
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = Path(os.environ.get("DATA_DIR", ROOT / "data"))

IMDB_BASE_URL = "https://datasets.imdbws.com"

DATASET_FILES = {
    "name.basics": "name.basics.tsv.gz",
    "title.basics": "title.basics.tsv.gz",
    "title.ratings": "title.ratings.tsv.gz",
    "title.crew": "title.crew.tsv.gz",
    "title.episode": "title.episode.tsv.gz",
    "title.principals": "title.principals.tsv.gz",
    "title.akas": "title.akas.tsv.gz",
}


def download_file(url: str, dest: Path) -> None:
    print(f"\n[DOWNLOAD] Bắt đầu tải: {url}")
    dest_tmp = dest.with_suffix(dest.suffix + ".part")
    t0 = time.perf_counter()

    def report_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        elapsed = time.perf_counter() - t0
        speed = (downloaded / (1024 * 1024)) / max(elapsed, 0.001)
        if total_size > 0:
            percent = downloaded * 100 / total_size
            sys.stdout.write(
                f"\r  -> {percent:5.1f}% | {downloaded / (1024*1024):.1f}/{total_size / (1024*1024):.1f} MB "
                f"({speed:.2f} MB/s)  "
            )
        else:
            sys.stdout.write(f"\r  -> {downloaded / (1024*1024):.1f} MB ({speed:.2f} MB/s)  ")
        sys.stdout.flush()

    try:
        urllib.request.urlretrieve(url, dest_tmp, reporthook=report_progress)
        print()
        dest_tmp.replace(dest)
        print(f"  ✓ Hoàn thành: {dest.name} ({dest.stat().st_size / (1024*1024):.2f} MB)")
    except Exception as e:
        if dest_tmp.exists():
            dest_tmp.unlink()
        raise RuntimeError(f"Lỗi khi tải {url}: {e}")


def decompress_gz(gz_path: Path, tsv_path: Path) -> None:
    print(f"[EXTRACT] Đang giải nén {gz_path.name} -> {tsv_path.name}...")
    t0 = time.perf_counter()
    with gzip.open(gz_path, "rb") as f_in, open(tsv_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out, length=16 * 1024 * 1024)
    dt = time.perf_counter() - t0
    print(f"  ✓ Giải nén xong: {tsv_path.name} ({tsv_path.stat().st_size / (1024*1024):.2f} MB trong {dt:.1f}s)")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Thư mục lưu dataset (mặc định: data/)")
    parser.add_argument("--tables", nargs="*", help="Chỉ tải các bảng này (vd: title.basics name.basics)")
    parser.add_argument("--decompress", action="store_true", help="Giải nén file .tsv.gz sang .tsv")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    targets = []
    if args.tables:
        for t in args.tables:
            clean_name = t.replace(".tsv", "").replace(".gz", "")
            if clean_name in DATASET_FILES:
                targets.append((clean_name, DATASET_FILES[clean_name]))
            else:
                print(f"[CẢNH BÁO] Không nhận diện được bảng '{t}', bỏ qua.")
    else:
        targets = list(DATASET_FILES.items())

    print(f"=== BỘ TẢI DỮ LIỆU CHÍNH THỨC IMDB DATASET ===")
    print(f"Đích lưu: {args.out.resolve()}")
    print(f"Số file cần tải: {len(targets)}")

    for key, fname in targets:
        url = f"{IMDB_BASE_URL}/{fname}"
        gz_dest = args.out / fname
        tsv_dest = args.out / fname.replace(".gz", "")

        # Kiểm tra nếu file đã có sẵn
        if tsv_dest.exists():
            print(f"\n[BỎ QUA] Đã tồn tại file đã giải nén: {tsv_dest.name}")
            continue
        if not gz_dest.exists():
            download_file(url, gz_dest)
        else:
            print(f"\n[BỎ QUA] Đã tồn tại file nén: {gz_dest.name}")

        if args.decompress and not tsv_dest.exists():
            decompress_gz(gz_dest, tsv_dest)

    print("\n[THÀNH CÔNG] Toàn bộ dữ liệu IMDb đã sẵn sàng!")


if __name__ == "__main__":
    main()
