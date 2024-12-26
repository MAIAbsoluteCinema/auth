CREATE TABLE conn_ids (
    id SERIAL PRIMARY KEY,       -- автоинкрементный идентификатор
    firebase_id VARCHAR(255) UNIQUE NOT NULL -- уникальный идентификатор Firebase пользователя
);
