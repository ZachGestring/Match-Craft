CREATE TABLE IF NOT EXISTS administrative_roles (
    role_id BIGINT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS active_queues (
    queue_id BIGINT PRIMARY KEY,
    game VARCHAR(50),
    max_players INT
);