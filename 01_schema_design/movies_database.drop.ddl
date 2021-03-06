
-- Drop content tables
DROP TABLE IF EXISTS content.genre_film_work;
DROP TABLE IF EXISTS content.person_film_work;
DROP TABLE IF EXISTS content.genre;
DROP TABLE IF EXISTS content.person;
DROP TABLE IF EXISTS content.film_work;

-- Drop schema itself
DROP SCHEMA IF EXISTS content CASCADE;
DROP EXTENSION IF EXISTS "uuid-ossp" CASCADE;