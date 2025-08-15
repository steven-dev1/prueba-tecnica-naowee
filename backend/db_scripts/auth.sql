CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'Usuario' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reset_token VARCHAR(255) UNIQUE,
    reset_token_expiration TIMESTAMP
);