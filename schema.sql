-- schema.sql

-- Drop existing tables in FK-safe order (optional for development)
DROP TABLE IF EXISTS rankings CASCADE;
DROP TABLE IF EXISTS view CASCADE;
DROP TABLE IF EXISTS artist_calendar CASCADE;
DROP TABLE IF EXISTS collaboration CASCADE;
DROP TABLE IF EXISTS distributor CASCADE;
DROP TABLE IF EXISTS production_name CASCADE;
DROP TABLE IF EXISTS artists CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Users table for authentication & RBAC
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    username        VARCHAR(50) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    role            VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'manager', 'user')),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Projects
CREATE TABLE projects (
    ProjectID       VARCHAR(20) PRIMARY KEY,
    ReleaseDate     DATE,
    Description     TEXT,
    Type            VARCHAR(50),
    Title           VARCHAR(255),
    SongLink        TEXT,
    AlbumArt        TEXT
);

-- Artists
CREATE TABLE artists_table (
    ArtistID        VARCHAR(20) PRIMARY KEY,
    Name            VARCHAR(255) NOT NULL,
    PhotoURL        TEXT,
    LastProjectID   VARCHAR(20),
    CONSTRAINT fk_artists_last_project
        FOREIGN KEY (LastProjectID)
        REFERENCES projects (ProjectID)
        ON DELETE SET NULL
);

-- Production companies
CREATE TABLE production_name (
    ProductionID    VARCHAR(20) PRIMARY KEY,
    Name            VARCHAR(255) NOT NULL,
    LogoURL         TEXT,
    MarketValue     BIGINT,
    LastProject     VARCHAR(20)  -- optional reference to projects
);

-- Distributors
CREATE TABLE distributor (
    DistributorID   VARCHAR(20) PRIMARY KEY,
    Name            VARCHAR(255) NOT NULL,
    LogoURL         TEXT,
    URL             TEXT,
    MarketValue     BIGINT
);

-- Collaboration junction table
CREATE TABLE collaboration (
    ColabID         VARCHAR(20) PRIMARY KEY,
    ArtistID        VARCHAR(20) NOT NULL,
    ProductionID    VARCHAR(20) NOT NULL,
    DistributorID   VARCHAR(20) NOT NULL,
    ProjectID       VARCHAR(20) NOT NULL,
    CONSTRAINT fk_colab_artist
        FOREIGN KEY (ArtistID)
        REFERENCES artists_table (ArtistID)
        ON DELETE CASCADE,
    CONSTRAINT fk_colab_production
        FOREIGN KEY (ProductionID)
        REFERENCES production_name (ProductionID)
        ON DELETE CASCADE,
    CONSTRAINT fk_colab_distributor
        FOREIGN KEY (DistributorID)
        REFERENCES distributor (DistributorID)
        ON DELETE CASCADE,
    CONSTRAINT fk_colab_project
        FOREIGN KEY (ProjectID)
        REFERENCES projects (ProjectID)
        ON DELETE CASCADE
);

-- Artist calendar
CREATE TABLE artist_calendar (
    EventID         VARCHAR(20) PRIMARY KEY,
    ArtistID        VARCHAR(20) NOT NULL,
    EventDate       DATE NOT NULL,
    Description     TEXT,
    CONSTRAINT fk_calendar_artist
        FOREIGN KEY (ArtistID)
        REFERENCES artists_table (ArtistID)
        ON DELETE CASCADE
);

-- Views / stats
CREATE TABLE view (
    StatID          VARCHAR(20) PRIMARY KEY,
    ProjectID       VARCHAR(20) NOT NULL,
    ViewsCount      BIGINT NOT NULL,
    RecordedDate    DATE NOT NULL,
    CONSTRAINT fk_view_project
        FOREIGN KEY (ProjectID)
        REFERENCES projects (ProjectID)
        ON DELETE CASCADE
);

-- Rankings
CREATE TABLE rankings (
    RankingID       VARCHAR(20) PRIMARY KEY,
    ArtistID        VARCHAR(20) NOT NULL,
    RankingPosition INT NOT NULL,
    CONSTRAINT fk_rankings_artist
        FOREIGN KEY (ArtistID)
        REFERENCES artists_table (ArtistID)
        ON DELETE CASCADE
);

-- Optional: simple index examples
CREATE INDEX idx_view_projectid ON view (ProjectID);
CREATE INDEX idx_rankings_position ON rankings (RankingPosition);
