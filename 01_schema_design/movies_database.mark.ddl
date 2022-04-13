
--- Initial schema setup
CREATE SCHEMA IF NOT EXISTS content;
SET search_path TO public,content;

--- Force re-create extension to avoid connection failure
DROP EXTENSION IF EXISTS "uuid-ossp";
CREATE EXTENSION "uuid-ossp" SCHEMA content;

--- Populate yearly stub marks into film_work
INSERT INTO content.film_work 
    (id, title, description, type, creation_date, rating, created, modified)
    SELECT uuid_generate_v4(),
            'Yearly mark stub',
            '',
            case when RANDOM() < 0.4 THEN 'movie' ELSE 'tv_show' END,
            date::DATE,
            0.0,
            NOW()::DATE,
            NOW()::DATE
    FROM generate_series(
    '1900-01-01'::DATE,
    '2022-01-01'::DATE,
    '1 year'::interval
    ) date;
