-- Tabla para almacenar la información de las canchas de fútbol
CREATE TABLE courts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    location VARCHAR(255) NOT NULL,
    capacity INTEGER NOT NULL, -- Capacidad de jugadores, ej. 5, 7, 11
    price_per_hour NUMERIC(10, 2) NOT NULL, -- Precio por hora de reserva
    is_active BOOLEAN DEFAULT TRUE, -- Indica si la cancha está disponible
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar el rendimiento de búsqueda
CREATE INDEX idx_courts_name ON courts (name);
CREATE INDEX idx_courts_location ON courts (location);
CREATE INDEX idx_courts_is_active ON courts (is_active);

-- Datos iniciales (opcional, pero útil para empezar a probar)
INSERT INTO courts (name, location, capacity, price_per_hour) VALUES
('Cancha Principal A', 'Zona Deportiva Central', 11, 50.00) ON CONFLICT (name) DO NOTHING;
INSERT INTO courts (name, location, capacity, price_per_hour) VALUES
('Cancha Auxiliar B', 'Sector Oeste', 7, 35.00) ON CONFLICT (name) DO NOTHING;
INSERT INTO courts (name, location, capacity, price_per_hour) VALUES
('Mini-Cancha C', 'Zona Recreativa', 5, 25.00) ON CONFLICT (name) DO NOTHING;
