DROP TABLE IF EXISTS room_sessions CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS rooms CASCADE;

CREATE TABLE rooms (
    id SERIAL PRIMARY KEY,
    room_id VARCHAR(20) UNIQUE NOT NULL,
    language VARCHAR(30) NOT NULL DEFAULT 'python',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    room_id VARCHAR(20) UNIQUE NOT NULL,
    content TEXT DEFAULT '',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_room
        FOREIGN KEY(room_id)
        REFERENCES rooms(room_id)
        ON DELETE CASCADE
);

CREATE TABLE room_sessions (
    id SERIAL PRIMARY KEY,
    room_id VARCHAR(20),
    username VARCHAR(60),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    left_at TIMESTAMP,

    CONSTRAINT fk_session_room
        FOREIGN KEY(room_id)
        REFERENCES rooms(room_id)
        ON DELETE CASCADE
);

CREATE INDEX idx_roomid ON rooms(room_id);
CREATE INDEX idx_doc_room ON documents(room_id);
CREATE INDEX idx_session_room ON room_sessions(room_id);