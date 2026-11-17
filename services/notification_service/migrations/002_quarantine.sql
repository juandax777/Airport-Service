CREATE TABLE notification_quarantine (
  message_hash VARCHAR(64) PRIMARY KEY,
  envelope TEXT NOT NULL,
  received_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
