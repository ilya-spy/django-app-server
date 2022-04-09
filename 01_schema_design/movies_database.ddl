CREATE SCHEMA IF NOT EXISTS content;

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

-- Устанавливаем расширения для генерации UUID
CREATE EXTENSION "uuid-ossp";

-- Генерируем данные в интервале с 1900 по 2021 год с шагом в час. В итоге сгенерируется 1060681 записей

INSERT INTO content.film_work (id, title, type, creation_date, rating) SELECT uuid_generate_v4(), 'some name', case when RANDOM() < 0.3 THEN 'movie' ELSE 'tv_show' END , date::DATE, floor(random() * 100)
FROM generate_series(
  '1900-01-01'::DATE,
  '2021-01-01'::DATE,
  '1 hour'::interval
) date;

EXPLAIN ANALYZE SELECT * FROM content.film_work WHERE creation_date = '2020-04-01';

CREATE INDEX film_work_creation_date_idx ON content.film_work(creation_date);

CREATE TABLE IF NOT EXISTS content.person (
    id uuid PRIMARY KEY,
    full_name TEXT NOT NULL,
    created timestamp with time zone,
    modified timestamp with time zone
);

CREATE TABLE IF NOT EXISTS content.person_film_work (
    id uuid PRIMARY KEY,
    film_work_id uuid NOT NULL,
    person_id uuid NOT NULL,
    role TEXT NOT NULL,
    created timestamp with time zone
);

-- Создадим уникальный композитный индекс (нельзя добавить персону дважды к фильму)
CREATE UNIQUE INDEX film_work_person_idx ON content.person_film_work (film_work_id, person_id); 

-- Искать с помощью композитного индекса
SELECT * FROM content.person_film_work WHERE film_work_id = '24804716-0b7d-4c8f-8afe-fea8b0a890c7' 
SELECT * FROM content.person_film_work WHERE film_work_id ='24804716-0b7d-4c8f-8afe-fea8b0a890c7' AND person_id = '0745df17-c2f4-440a-9514-e4cabc1327b4'; 

CREATE TABLE IF NOT EXISTS content.genre (
    id uuid PRIMARY KEY,
  	name TEXT NOT NULL,
    description TEXT,
    created timestamp with time zone,
    modified timestamp with time zone
);

CREATE TABLE IF NOT EXISTS content.genre_film_work (
    id uuid PRIMARY KEY,
    film_work_id uuid NOT NULL,
    genre_id uuid NOT NULL,
    created timestamp with time zone
);
