CREATE TABLE IF NOT EXISTS notifications (
  event_id VARCHAR(36) PRIMARY KEY,
  itinerary_id VARCHAR(36) NOT NULL,
  status VARCHAR(64) NOT NULL
);
