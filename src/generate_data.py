#!/usr/bin/env python3
"""Sinh bộ dữ liệu giả lập chuẩn cấu trúc IMDb Non-Commercial Datasets (định dạng TSV).

Phục vụ môi trường kiểm thử không có mạng / giới hạn dung lượng:
  * Chuẩn định dạng TSV của IMDb: phân cách bởi '\\t', giá trị NULL là '\\N'
  * Tạo dữ liệu có nhiều file, mỗi file > 1 triệu dòng (ở scale = 1.0)
  * Có nhiều file > 10 triệu dòng (name.basics, title.basics, title.crew, title.principals)
  * Đảm bảo tính toàn vẹn khóa ngoại (FK) giữa các bảng:
      - title_basics (PK: tconst 'tt%07d')
      - name_basics (PK: nconst 'nm%07d')
      - title_ratings, title_crew, title_episode, title_principals đều trỏ chuẩn xác
  * Hỗ trợ cờ --scale để sinh nhanh bản mẫu nhỏ (vd: --scale 0.05).

Sử dụng:
    python src/generate_data.py                 # scale = 1.0 (~58,5 triệu dòng)
    python src/generate_data.py --scale 0.05    # bản mẫu nhỏ (~2,9 triệu dòng, chạy trong vài giây)
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]

# Số dòng chuẩn ở scale = 1.0 (thỏa mãn tiêu chí > 1 triệu dòng và > 10 triệu dòng)
BASE_ROWS = {
    "name_basics": 12_000_000,        # > 10 triệu dòng
    "title_basics": 11_000_000,       # > 10 triệu dòng
    "title_ratings": 1_500_000,       # > 1 triệu dòng
    "title_crew": 11_000_000,         # > 10 triệu dòng
    "title_episode": 8_000_000,       # > 1 triệu dòng
    "title_principals": 15_000_000,   # > 10 triệu dòng
}

CHUNK_SIZE = 500_000

FIRST_NAMES = [
    "Tom", "Robert", "Christopher", "Leonardo", "Brad", "Emma", "Scarlett",
    "Jennifer", "Meryl", "Christian", "Keanu", "Morgan", "Johnny", "Matt",
    "Natalie", "Anne", "Hugh", "Cate", "Denzel", "Will", "Samuel", "Quentin",
    "Steven", "Martin", "James", "David", "Ridley", "Denis", "Guillermo", "Bong"
]
LAST_NAMES = [
    "Hanks", "Downey", "Nolan", "DiCaprio", "Pitt", "Stone", "Johansson",
    "Lawrence", "Streep", "Bale", "Reeves", "Freeman", "Depp", "Damon",
    "Portman", "Hathaway", "Jackman", "Blanchett", "Washington", "Smith",
    "Jackson", "Tarantino", "Spielberg", "Scorsese", "Cameron", "Fincher",
    "Scott", "Villeneuve", "del Toro", "Joon-ho"
]

PROFESSIONS = [
    "actor,producer", "actress,writer", "director,writer", "producer,director",
    "writer", "cinematographer", "composer", "sound_department", "editor", "miscellaneous"
]

TITLE_TYPES = ["movie", "tvSeries", "short", "tvEpisode", "tvMiniSeries", "video", "tvMovie"]
TITLE_WEIGHTS = [0.45, 0.20, 0.15, 0.10, 0.04, 0.04, 0.02]

GENRES_LIST = [
    "Drama", "Comedy", "Action,Adventure,Sci-Fi", "Crime,Drama,Mystery",
    "Horror,Thriller", "Documentary", "Animation,Adventure,Comedy",
    "Romance,Drama", "Biography,Drama,History", "Family,Fantasy"
]

ADJECTIVES = [
    "The Dark", "Eternal", "Inception of", "Lord of", "Pulp", "Fight", "Good",
    "Interstellar", "Gladiator", "Matrix", "Alien", "Avatar", "Godfather",
    "Silence of", "Brave", "Grand", "Lost", "Green", "Departed", "Prestige"
]
NOUNS = [
    "Knight", "Sunshine", "Dreams", "Rings", "Fiction", "Club", "Fellas",
    "Odyssey", "Warriors", "Revolutions", "Covenant", "Way of Water",
    "Empire", "Lambs", "Heart", "Hotel", "City", "Mile", "Shadows", "Illusion"
]

PRINCIPAL_CATEGORIES = ["actor", "actress", "director", "writer", "producer", "cinematographer", "composer", "editor"]
PRINCIPAL_WEIGHTS = [0.35, 0.30, 0.10, 0.10, 0.05, 0.04, 0.03, 0.03]


def fmt_tconst(idx: int) -> str:
    return f"tt{idx:07d}"


def fmt_nconst(idx: int) -> str:
    return f"nm{idx:07d}"


def generate_dataset(scale: float, seed: int, out_dir: Path) -> dict:
    rng = np.random.default_rng(seed)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = {k: max(10_000, int(v * scale)) for k, v in BASE_ROWS.items()}

    print(f"\n=== BẮT ĐẦU SINH DỮ LIỆU IMDB (SCALE = {scale}) ===")
    t_start = time.perf_counter()

    # 1. name_basics
    n_names = rows["name_basics"]
    print(f"Generating name.basics.tsv ({n_names:,} rows)...", flush=True)
    t0 = time.perf_counter()
    with open(out_dir / "name.basics.tsv", "w", encoding="utf-8", newline="") as f:
        f.write("nconst\tprimaryName\tbirthYear\tdeathYear\tprimaryProfession\tknownForTitles\n")
        for start in range(0, n_names, CHUNK_SIZE):
            m = min(CHUNK_SIZE, n_names - start)
            fn = rng.choice(FIRST_NAMES, size=m)
            ln = rng.choice(LAST_NAMES, size=m)
            names = [f"{f} {l}" for f, l in zip(fn, ln)]
            births = rng.integers(1890, 2010, size=m)
            has_death = rng.random(m) < 0.25
            deaths = np.where(has_death, births + rng.integers(40, 95, size=m), "\\N")
            profs = rng.choice(PROFESSIONS, size=m)
            # known for tconsts
            k_ref = rng.integers(1, max(2, int(rows["title_basics"] * 0.8)), size=m)
            knowns = [f"tt{k:07d}" for k in k_ref]

            lines = [
                f"nm{start + i + 1:07d}\t{names[i]}\t{births[i]}\t{deaths[i]}\t{profs[i]}\t{knowns[i]}\n"
                for i in range(m)
            ]
            f.writelines(lines)
    print(f"  ✓ name.basics.tsv hoàn thành trong {time.perf_counter() - t0:.1f}s")

    # 2. title_basics
    n_titles = rows["title_basics"]
    print(f"Generating title.basics.tsv ({n_titles:,} rows)...", flush=True)
    t0 = time.perf_counter()
    with open(out_dir / "title.basics.tsv", "w", encoding="utf-8", newline="") as f:
        f.write("tconst\ttitleType\tprimaryTitle\toriginalTitle\tisAdult\tstartYear\tendYear\truntimeMinutes\tgenres\n")
        for start in range(0, n_titles, CHUNK_SIZE):
            m = min(CHUNK_SIZE, n_titles - start)
            types = rng.choice(TITLE_TYPES, size=m, p=TITLE_WEIGHTS)
            adj = rng.choice(ADJECTIVES, size=m)
            noun = rng.choice(NOUNS, size=m)
            titles = [f"{a} {n} {start + i + 1}" for i, (a, n) in enumerate(zip(adj, noun))]
            adults = np.where(rng.random(m) < 0.02, 1, 0)
            years = rng.integers(1920, 2026, size=m)
            end_years = np.where(types == "tvSeries", years + rng.integers(1, 10, size=m), "\\N")
            has_runtime = rng.random(m) < 0.85
            runtimes = np.where(has_runtime, rng.integers(15, 210, size=m), "\\N")
            has_genres = rng.random(m) < 0.90
            genres = np.where(has_genres, rng.choice(GENRES_LIST, size=m), "\\N")

            lines = [
                f"tt{start + i + 1:07d}\t{types[i]}\t{titles[i]}\t{titles[i]}\t{adults[i]}\t{years[i]}\t{end_years[i]}\t{runtimes[i]}\t{genres[i]}\n"
                for i in range(m)
            ]
            f.writelines(lines)
    print(f"  ✓ title.basics.tsv hoàn thành trong {time.perf_counter() - t0:.1f}s")

    # 3. title_ratings
    n_ratings = rows["title_ratings"]
    print(f"Generating title.ratings.tsv ({n_ratings:,} rows)...", flush=True)
    t0 = time.perf_counter()
    # Chọn ngẫu nhiên n_ratings từ n_titles (FK hợp lệ)
    rated_indices = np.sort(rng.choice(n_titles, size=min(n_ratings, n_titles), replace=False)) + 1
    actual_ratings_count = len(rated_indices)
    with open(out_dir / "title.ratings.tsv", "w", encoding="utf-8", newline="") as f:
        f.write("tconst\taverageRating\tnumVotes\n")
        for start in range(0, actual_ratings_count, CHUNK_SIZE):
            m = min(CHUNK_SIZE, actual_ratings_count - start)
            sub_indices = rated_indices[start:start + m]
            # Phân phối điểm chuẩn quanh 6.5
            scores = np.clip(np.round(rng.normal(6.5, 1.4, size=m), 1), 1.0, 10.0)
            # Số vote phân phối log-uniform
            votes = np.exp(rng.uniform(np.log(10), np.log(2_500_000), size=m)).astype(int)
            lines = [
                f"tt{idx:07d}\t{scores[i]:.1f}\t{votes[i]}\n"
                for i, idx in enumerate(sub_indices)
            ]
            f.writelines(lines)
    print(f"  ✓ title.ratings.tsv hoàn thành trong {time.perf_counter() - t0:.1f}s")

    # 4. title_crew
    n_crew = rows["title_crew"]
    print(f"Generating title.crew.tsv ({n_crew:,} rows)...", flush=True)
    t0 = time.perf_counter()
    with open(out_dir / "title.crew.tsv", "w", encoding="utf-8", newline="") as f:
        f.write("tconst\tdirectors\twriters\n")
        for start in range(0, n_crew, CHUNK_SIZE):
            m = min(CHUNK_SIZE, n_crew - start)
            dir_ids = rng.integers(1, n_names + 1, size=m)
            wri_ids = rng.integers(1, n_names + 1, size=m)
            has_wri = rng.random(m) < 0.70
            wri_strs = [f"nm{wri_ids[i]:07d}" if has_wri[i] else "\\N" for i in range(m)]
            lines = [
                f"tt{start + i + 1:07d}\tnm{dir_ids[i]:07d}\t{wri_strs[i]}\n"
                for i in range(m)
            ]
            f.writelines(lines)
    print(f"  ✓ title.crew.tsv hoàn thành trong {time.perf_counter() - t0:.1f}s")

    # 5. title_episode
    n_eps = rows["title_episode"]
    print(f"Generating title.episode.tsv ({n_eps:,} rows)...", flush=True)
    t0 = time.perf_counter()
    # Tập con tconst làm episode, và tập cha làm parent (TV series)
    parent_max = max(2, int(n_titles * 0.2))
    with open(out_dir / "title.episode.tsv", "w", encoding="utf-8", newline="") as f:
        f.write("tconst\tparentTconst\tseasonNumber\tepisodeNumber\n")
        for start in range(0, n_eps, CHUNK_SIZE):
            m = min(CHUNK_SIZE, n_eps - start)
            # tconst trỏ vào các title có sẵn
            sub_t = (start + np.arange(1, m + 1)) % n_titles + 1
            # parent trỏ vào các title đầu (TV shows)
            parent_ids = rng.integers(1, parent_max, size=m)
            seasons = rng.integers(1, 15, size=m)
            episodes = rng.integers(1, 25, size=m)
            lines = [
                f"tt{sub_t[i]:07d}\ttt{parent_ids[i]:07d}\t{seasons[i]}\t{episodes[i]}\n"
                for i in range(m)
            ]
            f.writelines(lines)
    print(f"  ✓ title.episode.tsv hoàn thành trong {time.perf_counter() - t0:.1f}s")

    # 6. title_principals
    n_prin = rows["title_principals"]
    print(f"Generating title.principals.tsv ({n_prin:,} rows)...", flush=True)
    t0 = time.perf_counter()
    with open(out_dir / "title.principals.tsv", "w", encoding="utf-8", newline="") as f:
        f.write("tconst\tordering\tnconst\tcategory\tjob\tcharacters\n")
        for start in range(0, n_prin, CHUNK_SIZE):
            m = min(CHUNK_SIZE, n_prin - start)
            t_ids = rng.integers(1, n_titles + 1, size=m)
            orders = (start + np.arange(m)) % 10 + 1
            n_ids = rng.integers(1, n_names + 1, size=m)
            cats = rng.choice(PRINCIPAL_CATEGORIES, size=m, p=PRINCIPAL_WEIGHTS)
            has_chars = np.isin(cats, ["actor", "actress"])
            chars = np.where(has_chars, '["Character"]', "\\N")
            lines = [
                f"tt{t_ids[i]:07d}\t{orders[i]}\tnm{n_ids[i]:07d}\t{cats[i]}\t\\N\t{chars[i]}\n"
                for i in range(m)
            ]
            f.writelines(lines)
    print(f"  ✓ title.principals.tsv hoàn thành trong {time.perf_counter() - t0:.1f}s")

    total_rows = sum(rows.values())
    elapsed = time.perf_counter() - t_start
    manifest = {
        "dataset": "IMDb Non-Commercial Datasets (Mock/Synthetic)",
        "scale": scale,
        "seed": seed,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "rows": rows,
        "total_rows": total_rows,
        "generation_time_seconds": round(elapsed, 2),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[XONG] Sinh hoàn tất {total_rows:,} dòng trong {elapsed:.1f} giây. Lưu tại: {out_dir}")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scale", type=float, default=1.0, help="Tỉ lệ nhân số dòng (1.0 = ~58.5 triệu dòng)")
    parser.add_argument("--seed", type=int, default=20261124, help="Random seed cố định")
    parser.add_argument("--out", type=Path, default=ROOT / "data", help="Thư mục ghi file (mặc định: data/)")
    args = parser.parse_args()
    generate_dataset(args.scale, args.seed, args.out)
