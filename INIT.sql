-- Initialize database for RPI Match Craft Bot
-- Simple table to store administrative role IDs

-- Create the administrative roles table
CREATE TABLE IF NOT EXISTS declared_roles (
    role_id BIGINT PRIMARY KEY
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_declared_roles_role_id ON declared_roles(role_id);
