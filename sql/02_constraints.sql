-- ============================================================================
-- Khóa chính, khóa ngoại, ràng buộc CHECK và Index cho IMDb Datasets
-- Có thể thực thi TRƯỚC khi nạp (mặc định) hoặc SAU khi nạp dữ liệu (--defer-constraints).
-- ============================================================================

-- 1. Khóa chính (Primary Keys)
ALTER TABLE name_basics       ADD CONSTRAINT name_basics_pkey       PRIMARY KEY (nconst);
ALTER TABLE title_basics      ADD CONSTRAINT title_basics_pkey      PRIMARY KEY (tconst);
ALTER TABLE title_ratings     ADD CONSTRAINT title_ratings_pkey     PRIMARY KEY (tconst);
ALTER TABLE title_crew        ADD CONSTRAINT title_crew_pkey        PRIMARY KEY (tconst);
ALTER TABLE title_episode     ADD CONSTRAINT title_episode_pkey     PRIMARY KEY (tconst);
ALTER TABLE title_principals  ADD CONSTRAINT title_principals_pkey  PRIMARY KEY (tconst, ordering);
ALTER TABLE title_akas        ADD CONSTRAINT title_akas_pkey        PRIMARY KEY (title_id, ordering);

-- 2. Ràng buộc CHECK
ALTER TABLE title_basics      ADD CONSTRAINT title_is_adult_chk     CHECK (is_adult IN (0, 1) OR is_adult IS NULL);
ALTER TABLE title_ratings     ADD CONSTRAINT ratings_avg_chk        CHECK (average_rating BETWEEN 0.0 AND 10.0);
ALTER TABLE title_ratings     ADD CONSTRAINT ratings_votes_chk      CHECK (num_votes >= 0);

-- 3. Khóa ngoại (Foreign Keys)
-- Chú ý: Các bảng con liên kết với title_basics và name_basics
ALTER TABLE title_ratings     ADD CONSTRAINT ratings_title_fk       FOREIGN KEY (tconst)        REFERENCES title_basics (tconst);
ALTER TABLE title_crew        ADD CONSTRAINT crew_title_fk          FOREIGN KEY (tconst)        REFERENCES title_basics (tconst);
ALTER TABLE title_episode     ADD CONSTRAINT episode_title_fk       FOREIGN KEY (tconst)        REFERENCES title_basics (tconst);
ALTER TABLE title_episode     ADD CONSTRAINT episode_parent_fk      FOREIGN KEY (parent_tconst) REFERENCES title_basics (tconst);
ALTER TABLE title_principals  ADD CONSTRAINT principals_title_fk    FOREIGN KEY (tconst)        REFERENCES title_basics (tconst);
ALTER TABLE title_principals  ADD CONSTRAINT principals_name_fk     FOREIGN KEY (nconst)        REFERENCES name_basics (nconst);
ALTER TABLE title_akas        ADD CONSTRAINT akas_title_fk          FOREIGN KEY (title_id)      REFERENCES title_basics (tconst);

-- 4. Index phụ (Tăng tốc truy vấn và liên kết quan hệ)
CREATE INDEX idx_title_type_year     ON title_basics (title_type, start_year);
CREATE INDEX idx_name_primary_name   ON name_basics (primary_name);
CREATE INDEX idx_ratings_votes       ON title_ratings (num_votes DESC);
CREATE INDEX idx_episode_parent      ON title_episode (parent_tconst);
CREATE INDEX idx_principals_nconst   ON title_principals (nconst);
CREATE INDEX idx_akas_title_id       ON title_akas (title_id);
