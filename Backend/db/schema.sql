-- Create database
CREATE DATABASE IF NOT EXISTS trustbridge;
\c trustbridge;

-- Merchants table
CREATE TABLE IF NOT EXISTS merchants (
    id SERIAL PRIMARY KEY,
    merchant_id VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    district VARCHAR(50),
    business_type VARCHAR(50),
    phone VARCHAR(15),
    digital_footprint BOOLEAN DEFAULT FALSE,
    esewa_registered BOOLEAN DEFAULT FALSE,
    khalti_registered BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Trust scores (time-series — one row per scoring event)
CREATE TABLE IF NOT EXISTS trust_scores (
    id SERIAL PRIMARY KEY,
    merchant_id VARCHAR(10) REFERENCES merchants(merchant_id),
    final_score INTEGER CHECK (final_score BETWEEN 0 AND 100),
    confidence DECIMAL(4,2),
    segment VARCHAR(20),
    social_score INTEGER,
    psychometric_score INTEGER,
    behavioral_score INTEGER,
    lending_tier VARCHAR(2),
    fraud_flag BOOLEAN DEFAULT FALSE,
    full_result JSONB,
    scored_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast merchant lookup
CREATE INDEX IF NOT EXISTS idx_trust_scores_merchant ON trust_scores(merchant_id);
CREATE INDEX IF NOT EXISTS idx_trust_scores_time ON trust_scores(scored_at DESC);

-- Psychometric responses
CREATE TABLE IF NOT EXISTS psychometric_responses (
    id SERIAL PRIMARY KEY,
    merchant_id VARCHAR(10) REFERENCES merchants(merchant_id),
    responses JSONB NOT NULL,
    trait_scores JSONB,
    credit_personality VARCHAR(50),
    assessed_at TIMESTAMP DEFAULT NOW()
);
