-- Tabla para definir los roles (ej. Administrador, Usuario)
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- Tabla para definir los permisos (ej. canchas:crear, reservas:cancelar)
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- Tabla de relación entre usuarios y roles (un usuario puede tener múltiples roles)
-- user_id aquí se asume que es el ID de un usuario del microservicio de Autenticación.
-- No hay una FK directa porque son bases de datos separadas.
CREATE TABLE user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

-- Tabla de relación entre roles y permisos (un rol tiene múltiples permisos)
CREATE TABLE role_permissions (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);

-- Datos iniciales (opcional, pero útil para empezar)
INSERT INTO roles (name) VALUES ('Administrador') ON CONFLICT (name) DO NOTHING;
INSERT INTO roles (name) VALUES ('Usuario') ON CONFLICT (name) DO NOTHING;

INSERT INTO permissions (name) VALUES ('roles:create') ON CONFLICT (name) DO NOTHING;
INSERT INTO permissions (name) VALUES ('roles:read') ON CONFLICT (name) DO NOTHING;
INSERT INTO permissions (name) VALUES ('roles:update') ON CONFLICT (name) DO NOTHING;
INSERT INTO permissions (name) VALUES ('roles:delete') ON CONFLICT (name) DO NOTHING;
INSERT INTO permissions (name) VALUES ('permissions:create') ON CONFLICT (name) DO NOTHING;
INSERT INTO permissions (name) VALUES ('permissions:read') ON CONFLICT (name) DO NOTHING;
INSERT INTO permissions (name) VALUES ('permissions:update') ON CONFLICT (name) DO NOTHING;
INSERT INTO permissions (name) VALUES ('permissions:delete') ON CONFLICT (name) DO NOTHING;
INSERT INTO permissions (name) VALUES ('users:manage_roles') ON CONFLICT (name) DO NOTHING;
INSERT INTO permissions (name) VALUES ('users:read') ON CONFLICT (name) DO NOTHING;
INSERT INTO permissions (name) VALUES ('canchas:create') ON CONFLICT (name) DO NOTHING;
INSERT INTO permissions (name) VALUES ('canchas:read') ON CONFLICT (name) DO NOTHING;
INSERT INTO permissions (name) VALUES ('canchas:update') ON CONFLICT (name) DO NOTHING;
INSERT INTO permissions (name) VALUES ('canchas:delete') ON CONFLICT (name) DO NOTHING;
INSERT INTO permissions (name) VALUES ('reservas:create') ON CONFLICT (name) DO NOTHING;
INSERT INTO permissions (name) VALUES ('reservas:read_own') ON CONFLICT (name) DO NOTHING;
INSERT INTO permissions (name) VALUES ('reservas:update_own') ON CONFLICT (name) DO NOTHING;
INSERT INTO permissions (name) VALUES ('reservas:cancel_own') ON CONFLICT (name) DO NOTHING;
INSERT INTO permissions (name) VALUES ('reservas:read_all') ON CONFLICT (name) DO NOTHING;
-- Puedes añadir más permisos según las necesidades de cada microservicio

-- Asignar todos los permisos al rol de Administrador
DO $$
DECLARE
    admin_role_id INTEGER;
    perm_id INTEGER;
BEGIN
    SELECT id INTO admin_role_id FROM roles WHERE name = 'Administrador';

    IF admin_role_id IS NOT NULL THEN
        FOR perm_id IN SELECT id FROM permissions LOOP
            INSERT INTO role_permissions (role_id, permission_id)
            VALUES (admin_role_id, perm_id)
            ON CONFLICT (role_id, permission_id) DO NOTHING;
        END LOOP;
    END IF;
END $$;