CREATE TABLE IF NOT EXISTS submission (
    id VARCHAR(8) PRIMARY KEY,
    title TEXT NOT NULL,
    author VARCHAR(32),
    created TIMESTAMP NOT NULL,
    score INT NOT NULL,
    upvote_ratio FLOAT(2) UNSIGNED NOT NULL
    );
CREATE TABLE IF NOT EXISTS comment (
    id VARCHAR(8) PRIMARY KEY,
    body TEXT,
    author VARCHAR(32),
    created TIMESTAMP NOT NULL,
    score INT NOT NULL
    );
CREATE TABLE IF NOT EXISTS user (
    username VARCHAR(32) PRIMARY KEY,
    created TIMESTAMP NOT NULL,
    score INT NOT NULL,
    active_subreddits JSON NOT NULL
    );
    