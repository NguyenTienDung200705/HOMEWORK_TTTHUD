-- ============================================================================
-- BÀI TẬP THỰC HÀNH CRUD / DDL / DML (PostgreSQL 14+) - Cinema Domain
-- ============================================================================
\set QUIET on
\pset null '(NULL)'
DROP SCHEMA IF EXISTS practice_ex CASCADE;
CREATE SCHEMA practice_ex;
SET search_path TO practice_ex;
\set QUIET off

\echo '=== BÀI 1 (DDL). Tạo bảng actors (actor_id tự tăng, name, birth_year, nationality) và castings ==='
CREATE TABLE actors (
    actor_id    integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        text NOT NULL,
    birth_year  integer CHECK (birth_year >= 1850),
    nationality text DEFAULT 'Unknown'
);

CREATE TABLE movies (
    movie_id    integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title       text NOT NULL,
    release_year integer NOT NULL,
    rating      numeric(3,1) CHECK (rating BETWEEN 0.0 AND 10.0)
);

CREATE TABLE castings (
    movie_id    integer REFERENCES movies (movie_id) ON DELETE CASCADE,
    actor_id    integer REFERENCES actors (actor_id) ON DELETE CASCADE,
    role_name   text NOT NULL,
    pay_amount  numeric(12,2) DEFAULT 0 CHECK (pay_amount >= 0),
    PRIMARY KEY (movie_id, actor_id, role_name)
);

\echo '=== BÀI 2 (INSERT). Thêm diễn viên, phim và phân vai bằng một hoặc nhiều câu lệnh ==='
INSERT INTO actors (name, birth_year, nationality) VALUES
    ('Cillian Murphy', 1976, 'Irish'),
    ('Christian Bale', 1974, 'British'),
    ('Heath Ledger',   1979, 'Australian');

INSERT INTO movies (title, release_year, rating) VALUES
    ('Oppenheimer',      2023, 8.9),
    ('The Dark Knight',  2008, 9.0),
    ('Inception',        2010, 8.8);

INSERT INTO castings (movie_id, actor_id, role_name, pay_amount) VALUES
    (1, 1, 'J. Robert Oppenheimer', 10000000),
    (2, 2, 'Bruce Wayne / Batman',  20000000),
    (2, 3, 'Joker',                 15000000),
    (3, 1, 'Robert Fischer',         5000000);

\echo '=== BÀI 3 (SELECT & JOIN). Thống kê mỗi diễn viên đã tham gia bao nhiêu phim và tổng thù lao ==='
SELECT 
    a.name,
    count(c.movie_id)              AS so_phim,
    to_char(sum(c.pay_amount), '$999,999,999') AS tong_thu_lao
FROM actors a
LEFT JOIN castings c USING (actor_id)
GROUP BY a.actor_id, a.name
ORDER BY sum(c.pay_amount) DESC NULLS LAST;

\echo '=== BÀI 4 (UPDATE ... FROM). Tăng 10% thù lao cho mọi vai diễn trong các phim có rating >= 9.0 ==='
UPDATE castings c
SET pay_amount = c.pay_amount * 1.10
FROM movies m
WHERE m.movie_id = c.movie_id AND m.rating >= 9.0
RETURNING c.role_name, c.pay_amount;

\echo '=== BÀI 5 (DELETE). Xóa các phim có rating dưới 5.0 (cascade tự động xóa castings liên quan) ==='
DELETE FROM movies WHERE rating < 5.0 RETURNING movie_id, title;
