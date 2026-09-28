CREATE TABLE IF NOT EXISTS itineraries (
  id VARCHAR(36) PRIMARY KEY,
  user_name VARCHAR(255) NOT NULL,
  departure_airport_id VARCHAR(255) NOT NULL,
  arrival_airport_id VARCHAR(255) NOT NULL,
  travel_date DATE NOT NULL,
  duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0)
);
