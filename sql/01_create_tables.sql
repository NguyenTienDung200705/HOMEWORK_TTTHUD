-- ============================================================================
-- DDL: IMDb Non-Commercial Datasets Schema (PostgreSQL 14+)
-- Khai báo bảng + kiểu dữ liệu + NOT NULL.
-- Khóa chính, khóa ngoại, ràng buộc và index nằm ở 02_constraints.sql
-- để có thể hỗ trợ kiểm thử nạp dữ liệu TRƯỚC hoặc SAU khi tạo ràng buộc.
-- ============================================================================

CREATE TABLE IF NOT EXISTS name_basics (
    nconst             text NOT NULL,
    primary_name       text NOT NULL,
    birth_year         integer,
    death_year         integer,
    primary_profession text,
    known_for_titles   text
);

CREATE TABLE IF NOT EXISTS title_basics (
    tconst          text NOT NULL,
    title_type      text NOT NULL,
    primary_title   text NOT NULL,
    original_title  text,
    is_adult        smallint DEFAULT 0,
    start_year      integer,
    end_year        integer,
    runtime_minutes integer,
    genres          text
);

CREATE TABLE IF NOT EXISTS title_ratings (
    tconst         text NOT NULL,
    average_rating numeric(3,1) NOT NULL,
    num_votes      integer NOT NULL
);

CREATE TABLE IF NOT EXISTS title_crew (
    tconst    text NOT NULL,
    directors text,
    writers   text
);

CREATE TABLE IF NOT EXISTS title_episode (
    tconst         text NOT NULL,
    parent_tconst  text NOT NULL,
    season_number  integer,
    episode_number integer
);

CREATE TABLE IF NOT EXISTS title_principals (
    tconst     text NOT NULL,
    ordering   integer NOT NULL,
    nconst     text NOT NULL,
    category   text NOT NULL,
    job        text,
    characters text
);

CREATE TABLE IF NOT EXISTS title_akas (
    title_id          text NOT NULL,
    ordering          integer NOT NULL,
    title             text NOT NULL,
    region            text,
    language          text,
    types             text,
    attributes        text,
    is_original_title smallint
);
