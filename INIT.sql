CREATE TABLE administrative_roles (
    role_id BIGINT PRIMARY KEY
);

CREATE TABLE active_queues (
    queue_id BIGINT PRIMARY KEY,
    game VARCHAR(50),
    max_players INT
);