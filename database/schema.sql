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
    category VARCHAR(100),
    county VARCHAR(100),
    notified BOOLEAN DEFAULT FALSE,
    analyzed BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_articles_url ON articles(url);
CREATE INDEX idx_articles_discovered ON articles(discovered_date DESC);
CREATE INDEX idx_articles_priority ON articles(priority_score DESC);
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
