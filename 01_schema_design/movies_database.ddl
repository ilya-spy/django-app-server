
--- Initial schema setup
CREATE SCHEMA IF NOT EXISTS content;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


--- Create film_work
CREATE TABLE IF NOT EXISTS content.film_work (
    id uuid PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    creation_date DATE,
    rating FLOAT,
    type TEXT NOT NULL,
    created timestamp with time zone,
    modified timestamp with time zone
);

--- Populate yearly stub marks into film_work
INSERT INTO content.film_work 
    (id, title, description, type, creation_date, rating, created, modified)
    SELECT uuid_generate_v4(),
            'Yearly mark stub',
            'This entry is to indicate yearly marks in film works history view',
            case when RANDOM() < 0.4 THEN 'movie' ELSE 'tv_show' END,
            date::DATE,
            floor(random() * 100),
            NOW()::DATE,
            NOW()::DATE
    FROM generate_series(
    '1900-01-01'::DATE,
    '2022-01-01'::DATE,
    '1 year'::interval
    ) date;

--- Explain and fix film_work query, using creation_date
EXPLAIN ANALYZE SELECT * FROM content.film_work WHERE creation_date = '2020-04-01';
CREATE INDEX IF NOT EXISTS film_work_creation_date_idx ON
    content.film_work(creation_date);


--- Create person
CREATE TABLE IF NOT EXISTS content.person (
    id uuid PRIMARY KEY,
    full_name TEXT NOT NULL,
    created timestamp with time zone,
    modified timestamp with time zone
);

--- Create person_film_work relation
CREATE TABLE IF NOT EXISTS content.person_film_work (
    id uuid PRIMARY KEY,
    film_work_id uuid NOT NULL,
    person_id uuid NOT NULL,
    role TEXT NOT NULL,
    created timestamp with time zone
);

-- Put unique constraint - each person could play each role only once in each filw_work
CREATE UNIQUE INDEX IF NOT EXISTS film_work_person_role ON
    content.person_film_work (film_work_id, person_id, role);


-- Create genre
CREATE TABLE IF NOT EXISTS content.genre (
    id uuid PRIMARY KEY,
  	name TEXT NOT NULL,
    description TEXT,
    created timestamp with time zone,
    modified timestamp with time zone
);

-- Create genre_dilm_work relation
CREATE TABLE IF NOT EXISTS content.genre_film_work (
    id uuid PRIMARY KEY,
    film_work_id uuid NOT NULL,
    genre_id uuid NOT NULL,
    created timestamp with time zone
);

-- Put unique constraint - each filmwork could reference particular genre only once
CREATE UNIQUE INDEX IF NOT EXISTS film_work_genre ON
    content.genre_film_work (film_work_id, genre_id);
