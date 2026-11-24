#!/usr/bin/env python3
"""Đọc results/*.json và xuất báo cáo so sánh bảng Markdown -> results/summary.md"""
import json
from pathlib import Path

R = Path(__file__).resolve().parents[1] / "results"
CONFIGS = [
    ("Cách 1 – INSERT, khóa tạo TRƯỚC", "method1_insert.json"),
    ("Cách 1 – INSERT, khóa tạo SAU", "method1_insert_deferred.json"),
    ("Cách 2 – COPY, khóa tạo TRƯỚC", "method2_copy.json"),
    ("Cách 2 – COPY, khóa tạo SAU", "method2_copy_deferred.json"),
]

TABLE_ORDER = [
    "name_basics", "title_basics", "title_ratings",
    "title_crew", "title_episode", "title_principals", "title_akas"
]


def fmt(sec):
    return f"{sec:,.1f}" if sec is not None else "N/A"


def main():
    available = {}
    for label, fname in CONFIGS:
        p = R / fname
        if p.exists():
            available[label] = json.loads(p.read_text(encoding="utf-8"))

    if not available:
        print("[THÔNG BÁO] Chưa có kết quả benchmark nào trong results/ (*.json).")
        return

    out = []
    out.append("# BÁO CÁO TỔNG HỢP HIỆU NĂNG NẠP DỮ LIỆU IMDB\n")

    # Xác định các bảng xuất hiện
    first = next(iter(available.values()))
    tables_present = [t for t in TABLE_ORDER if t in first.get("tables", {})]
    if not tables_present:
        tables_present = list(first.get("tables", {}).keys())

    out.append("### 1. Thời gian nạp từng bảng (giây)\n")
    headers = ["Bảng", "Số dòng"] + list(available.keys())
    out.append("| " + " | ".join(headers) + " |")
    out.append("|---|---:|" + "---:|" * len(available))

    for t in tables_present:
        row_cnt = first["tables"][t]["rows"]
        row_vals = [f"{t}", f"{row_cnt:,}"]
        for d in available.values():
            s = d["tables"].get(t, {}).get("seconds")
            row_vals.append(fmt(s))
        out.append("| " + " | ".join(row_vals) + " |")

    out.append("\n### 2. Tổng kết hiệu năng toàn diện\n")
    out.append("| Cấu hình | Thời gian nạp (s) | Tạo khóa/index (s) | **Tổng thời gian (s)** | Thông lượng (dòng/s) | Dung lượng DB |")
    out.append("|---|---:|---:|---:|---:|---:|")

    for label, d in available.items():
        tm = d["timing"]
        total = tm["total_s"]
        pre = tm.get("constraints_before_load_s", 0)
        post = tm.get("constraints_after_load_s", 0)
        extra = f"{fmt(pre)} (trước)" if pre else (f"{fmt(post)} (sau)" if post else "-")
        load_time = tm.get("load_only_s", 0)
        t_rows = d.get("total_rows", 0)
        tput = t_rows / max(total, 0.001)
        out.append(
            f"| {label} | {fmt(load_time)} | {extra} | **{fmt(total)}** | "
            f"{tput:,.0f} | {d.get('db_size', 'N/A')} |"
        )

    # So sánh tỉ lệ
    if "Cách 2 – COPY, khóa tạo TRƯỚC" in available:
        base = available["Cách 2 – COPY, khóa tạo TRƯỚC"]["timing"]["total_s"]
        out.append("\n### 3. Hệ số tốc độ (so với 'Cách 2 – COPY, khóa tạo TRƯỚC')\n")
        for label, d in available.items():
            ratio = d["timing"]["total_s"] / max(base, 0.001)
            out.append(f"- **{label}**: {ratio:.2f}×")

    summary_file = R / "summary.md"
    summary_content = "\n".join(out) + "\n"
    summary_file.write_text(summary_content, encoding="utf-8")
    print(f"✓ Đã cập nhật tóm tắt kết quả: {summary_file}")
    print(summary_content)


if __name__ == "__main__":
    main()
