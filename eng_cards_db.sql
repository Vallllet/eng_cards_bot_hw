DROP TABLE users;

CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(60) NOT NULL
);

CREATE TABLE IF NOT EXISTS zero(
        id SERIAL PRIMARY KEY,
        eng VARCHAR(40) NOT NULL UNIQUE CHECK(eng ~*'[a-z]+'),
        ru VARCHAR(40) NOT NULL CHECK(ru ~*'[а-яё]+')
);

INSERT INTO zero (eng,ru)
VALUES ('brown', 'коричневый'),
       ('red', 'красный'),
       ('blue', 'голубой'),
       ('she', 'она'),
       ('he', 'он'),
       ('they', 'они'),
       ('yellow', 'желтый'),
       ('purple', 'фиолетовый'),
       ('green', 'зелёный'),
       ('black', 'черный')
;

CREATE TABLE IF NOT EXISTS user_567 as (SELECT *FROM zero);

ALTER TABLE name1
ADD COLUMN id SERIAL PRIMARY KEY,
ADD CONSTRAINT eng_only CHECK(eng ~*'[a-z]+'),
ADD CONSTRAINT eng_un UNIQUE (eng),
ALTER COLUMN eng SET NOT NULL,
ADD CONSTRAINT ru_only CHECK(ru ~*'[а-яё]+'),
ALTER COLUMN ru SET NOT NULL;