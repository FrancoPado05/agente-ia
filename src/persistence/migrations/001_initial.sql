CREATE TABLE IF NOT EXISTS clients (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    phone_number_id TEXT NOT NULL UNIQUE,
    system_prompt   TEXT NOT NULL DEFAULT '',
    model_name      TEXT NOT NULL DEFAULT 'openai/gpt-4o-mini',
    temperature     REAL NOT NULL DEFAULT 0.7,
    max_tokens      INTEGER NOT NULL DEFAULT 1024,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS client_tools (
    client_id   TEXT NOT NULL REFERENCES clients(id),
    tool_id     TEXT NOT NULL,
    enabled     INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (client_id, tool_id)
);

CREATE TABLE IF NOT EXISTS conversations (
    id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    client_id   TEXT NOT NULL REFERENCES clients(id),
    phone_number TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'active',
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_conversations_client ON conversations(client_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations(updated_at);

CREATE TABLE IF NOT EXISTS messages (
    id              TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    client_id       TEXT NOT NULL REFERENCES clients(id),
    conversation_id TEXT NOT NULL REFERENCES conversations(id),
    role            TEXT NOT NULL,
    content         TEXT NOT NULL,
    metadata        TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(client_id, conversation_id);

CREATE TABLE IF NOT EXISTS tool_calls (
    id              TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    client_id       TEXT NOT NULL REFERENCES clients(id),
    conversation_id TEXT NOT NULL REFERENCES conversations(id),
    tool_name       TEXT NOT NULL,
    arguments       TEXT NOT NULL,
    result          TEXT,
    error           TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_tool_calls_conv ON tool_calls(client_id, conversation_id);
