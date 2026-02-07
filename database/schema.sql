-- Eagle Harbor Data Center Monitor Database Schema

-- Create subscribers table
CREATE TABLE IF NOT EXISTS subscribers (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(100) UNIQUE,
    unsubscribe_token VARCHAR(100) UNIQUE NOT NULL,
    subscribed_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_subscribers_email ON subscribers(email);
CREATE INDEX idx_subscribers_active ON subscribers(is_active);

-- Create articles table
CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    url VARCHAR(1000) UNIQUE NOT NULL,
    summary TEXT,
    content TEXT,
    source VARCHAR(200) NOT NULL,
    published_date TIMESTAMP,
    discovered_date TIMESTAMP DEFAULT NOW(),
    priority_score INTEGER,
    relevance_score INTEGER,
    category VARCHAR(100),
    county VARCHAR(100),
    event_date TIMESTAMP,
    notified BOOLEAN DEFAULT FALSE,
    analyzed BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_articles_url ON articles(url);
CREATE INDEX idx_articles_discovered ON articles(discovered_date DESC);
CREATE INDEX idx_articles_priority ON articles(priority_score DESC);
CREATE INDEX idx_articles_relevance ON articles(relevance_score DESC);
CREATE INDEX idx_articles_notified ON articles(notified);

-- Create alerts_sent table
CREATE TABLE IF NOT EXISTS alerts_sent (
    id SERIAL PRIMARY KEY,
    subject VARCHAR(500),
    sent_to TEXT[],
    article_ids INTEGER[],
    sent_at TIMESTAMP DEFAULT NOW(),
    alert_type VARCHAR(50)
);

CREATE INDEX idx_alerts_sent_at ON alerts_sent(sent_at DESC);

-- Full-text search on articles
CREATE INDEX idx_articles_search ON articles USING GIN(to_tsvector('english', title || ' ' || COALESCE(content, '')));


-- ── Amendment Watchlist Tables ──────────────────────────────────────────────

-- Tracked legislation / amendments
CREATE TABLE IF NOT EXISTS watched_matters (
    id SERIAL PRIMARY KEY,
    matter_id INTEGER UNIQUE NOT NULL,
    matter_file VARCHAR(100),
    matter_type VARCHAR(100),
    title VARCHAR(500) NOT NULL,
    body_name VARCHAR(200),
    current_status VARCHAR(200),
    last_action_date TIMESTAMP,
    legistar_url VARCHAR(1000),
    watch_reason TEXT,
    auto_detected BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    priority VARCHAR(20) DEFAULT 'high',
    approval_path VARCHAR(100),
    qualified_definition TEXT,
    power_provisions TEXT,
    infrastructure_triggers TEXT,
    compatibility_standards TEXT,
    created_date TIMESTAMP DEFAULT NOW(),
    updated_date TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_watched_matters_matter_id ON watched_matters(matter_id);
CREATE INDEX idx_watched_matters_active ON watched_matters(is_active);

-- Status transition history
CREATE TABLE IF NOT EXISTS matter_histories (
    id SERIAL PRIMARY KEY,
    matter_id INTEGER NOT NULL REFERENCES watched_matters(matter_id),
    legistar_history_id INTEGER UNIQUE,
    action_date TIMESTAMP,
    action_text VARCHAR(500),
    action_body VARCHAR(200),
    result VARCHAR(100),
    vote_info VARCHAR(200),
    minutes_note TEXT,
    previous_status VARCHAR(200),
    new_status VARCHAR(200),
    is_milestone BOOLEAN DEFAULT FALSE,
    notified BOOLEAN DEFAULT FALSE,
    discovered_date TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_matter_histories_matter_id ON matter_histories(matter_id);
CREATE INDEX idx_matter_histories_action_date ON matter_histories(action_date DESC);

-- Attachments (draft text, staff reports, memos)
CREATE TABLE IF NOT EXISTS matter_attachments (
    id SERIAL PRIMARY KEY,
    matter_id INTEGER NOT NULL REFERENCES watched_matters(matter_id),
    legistar_attachment_id INTEGER UNIQUE,
    name VARCHAR(500),
    hyperlink VARCHAR(1000),
    file_type VARCHAR(50),
    content_text TEXT,
    ai_summary TEXT,
    ai_analysis JSONB,
    analyzed BOOLEAN DEFAULT FALSE,
    discovered_date TIMESTAMP DEFAULT NOW(),
    notified BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_matter_attachments_matter_id ON matter_attachments(matter_id);

-- Roll-call votes
CREATE TABLE IF NOT EXISTS matter_votes (
    id SERIAL PRIMARY KEY,
    matter_id INTEGER NOT NULL REFERENCES watched_matters(matter_id),
    legistar_vote_id INTEGER UNIQUE,
    vote_date TIMESTAMP,
    body_name VARCHAR(200),
    result VARCHAR(100),
    tally VARCHAR(50),
    roll_call JSONB,
    notified BOOLEAN DEFAULT FALSE,
    discovered_date TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_matter_votes_matter_id ON matter_votes(matter_id);
CREATE INDEX idx_matter_votes_date ON matter_votes(vote_date DESC);
