CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    court_id INTEGER NOT NULL,
    booking_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    status VARCHAR(50) DEFAULT 'Confirmada' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE INDEX idx_bookings_user_id ON bookings (user_id);
CREATE INDEX idx_bookings_court_id ON bookings (court_id);
CREATE INDEX idx_bookings_date_time ON bookings (booking_date, start_time, end_time);
CREATE INDEX idx_bookings_status ON bookings (status);