-- Create protocols table
CREATE TABLE IF NOT EXISTS protocols (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- Create camera_types table
CREATE TABLE IF NOT EXISTS camera_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- Create devices table
CREATE TABLE IF NOT EXISTS devices (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    ip INET NOT NULL,
    port INTEGER NOT NULL CHECK (port > 0 AND port < 65536),
    protocol_id INTEGER NOT NULL,
    camera_type_id INTEGER NOT NULL,
    username VARCHAR(100),
    password VARCHAR(100),
    FOREIGN KEY (protocol_id) REFERENCES protocols(id) ON DELETE RESTRICT,
    FOREIGN KEY (camera_type_id) REFERENCES camera_types(id) ON DELETE RESTRICT
);

-- Optional seed data for protocols
INSERT INTO protocols (name)
VALUES ('udp'), ('rtmp'), ('rtp'), ('http')
ON CONFLICT DO NOTHING;

-- Optional seed data for camera types
INSERT INTO camera_types (name)
VALUES ('IP Camera'), ('Analog Camera'), ('Thermal Camera'), ('PTZ Camera')
ON CONFLICT DO NOTHING;