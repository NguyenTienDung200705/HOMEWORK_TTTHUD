-- ============================================================================
-- ÔN TẬP DDL – DML – CRUD (PostgreSQL 14+) - Cinema / IMDb Domain
-- Chạy: psql -h HOST -p PORT -U USER -d bigdata -v ON_ERROR_STOP=1 -f sql/03_crud_ddl_dml_review.sql
-- Sử dụng schema riêng "practice_cinema" để không đụng vào dữ liệu chính.
-- ============================================================================
\set QUIET on
\pset null '(NULL)'
DROP SCHEMA IF EXISTS practice_cinema CASCADE;
CREATE SCHEMA practice_cinema;
SET search_path TO practice_cinema;
\set QUIET off

\echo
\echo '################  PHẦN A – DDL (Data Definition Language)  ################'

\echo '--- A1. CREATE TABLE: Khóa chính tự sinh, khóa ngoại, CHECK, DEFAULT, UNIQUE ---'
CREATE TABLE production_studios (
    studio_id   integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    studio_name text NOT NULL UNIQUE,
    headquarters text,
    founded_year integer CHECK (founded_year >= 1880)
);

CREATE TABLE movies (
    movie_id    integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title       text NOT NULL,
    release_year integer CHECK (release_year >= 1880),
    runtime_min integer CHECK (runtime_min > 0),
    budget      numeric(14,2) DEFAULT 0 CHECK (budget >= 0),
    revenue     numeric(14,2) DEFAULT 0 CHECK (revenue >= 0),
    studio_id   integer REFERENCES production_studios (studio_id) ON DELETE SET NULL,
    rating      numeric(3,1) CHECK (rating BETWEEN 0.0 AND 10.0),
    status      text NOT NULL DEFAULT 'Released' CHECK (status IN ('Released', 'Post-Production', 'Cancelled'))
);

\echo '--- A2. ALTER TABLE: Thêm cột, sửa kiểu dữ liệu, đổi tên, thêm/bỏ ràng buộc ---'
ALTER TABLE movies ADD COLUMN language text DEFAULT 'English';
ALTER TABLE movies ALTER COLUMN language TYPE varchar(50);
ALTER TABLE movies RENAME COLUMN rating TO imdb_score;
ALTER TABLE movies ADD CONSTRAINT chk_movie_revenue CHECK (revenue >= 0);
ALTER TABLE movies DROP CONSTRAINT chk_movie_revenue;

\echo '--- A3. CREATE INDEX, VIEW, SEQUENCE ---'
CREATE INDEX idx_movies_year_score ON movies (release_year, imdb_score DESC);
CREATE INDEX idx_movies_studio     ON movies (studio_id);

CREATE VIEW v_top_grossing_movies AS
    SELECT m.title, m.release_year, s.studio_name, m.revenue, m.imdb_score
    FROM movies m
    LEFT JOIN production_studios s USING (studio_id)
    WHERE m.revenue > 0
    ORDER BY m.revenue DESC;

\echo
\echo '################  PHẦN B – CRUD & DML (INSERT, SELECT, UPDATE, DELETE)  ################'

\echo '--- B1. INSERT (Create): Đơn lẻ, nhiều dòng, RETURNING ---'
INSERT INTO production_studios (studio_name, headquarters, founded_year) VALUES
    ('Warner Bros.', 'Burbank, California', 1923),
    ('Universal Pictures', 'Universal City, California', 1912),
    ('Paramount Pictures', 'Hollywood, California', 1912)
RETURNING studio_id, studio_name;

INSERT INTO movies (title, release_year, runtime_min, budget, revenue, studio_id, imdb_score) VALUES
    ('Oppenheimer', 2023, 180, 100000000, 957000000, 2, 8.9),
    ('The Dark Knight', 2008, 152, 185000000, 1006000000, 1, 9.0),
    ('Inception', 2010, 148, 160000000, 836800000, 1, 8.8),
    ('Interstellar', 2014, 169, 165000000, 701700000, 1, 8.7),
    ('Top Gun: Maverick', 2022, 130, 170000000, 1495000000, 3, 8.3);

\echo '--- B2. SELECT (Read): Aggregations, GROUP BY, HAVING, Window Functions ---'
-- Tổng doanh thu và điểm trung bình theo studio
SELECT 
    coalesce(s.studio_name, 'Độc lập') AS studio,
    count(m.movie_id)                  AS so_luong_phim,
    round(avg(m.imdb_score), 2)        AS diem_tb,
    to_char(sum(m.revenue), '$999,999,999,999') AS tong_doanh_thu
FROM movies m
LEFT JOIN production_studios s USING (studio_id)
GROUP BY s.studio_name
HAVING count(m.movie_id) >= 1
ORDER BY sum(m.revenue) DESC;

-- Xếp hạng doanh thu phim bằng DENSE_RANK()
SELECT 
    title, release_year, imdb_score,
    revenue,
    DENSE_RANK() OVER (ORDER BY revenue DESC) AS rank_doanh_thu
FROM movies;

\echo '--- B3. UPDATE (Modify): UPDATE có điều kiện và UPDATE ... FROM ---'
-- Tăng điểm 0.1 cho các phim có doanh thu vượt 1 tỷ USD
UPDATE movies 
SET imdb_score = LEAST(10.0, imdb_score + 0.1)
WHERE revenue >= 1000000000
RETURNING title, imdb_score AS new_score;

\echo '--- B4. UPSERT: ON CONFLICT DO UPDATE / DO NOTHING ---'
INSERT INTO production_studios (studio_id, studio_name, headquarters, founded_year)
OVERRIDING SYSTEM VALUE
VALUES (1, 'Warner Bros. Discovery', 'New York', 1923)
ON CONFLICT (studio_id) 
DO UPDATE SET studio_name = EXCLUDED.studio_name, headquarters = EXCLUDED.headquarters
RETURNING studio_id, studio_name, headquarters;

\echo '--- B5. DELETE: Xóa với RETURNING ---'
DELETE FROM movies 
WHERE status = 'Cancelled'
RETURNING movie_id, title;

\echo 'Hoàn tất kịch bản ôn tập DDL/DML!'
