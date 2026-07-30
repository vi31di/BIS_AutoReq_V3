-- SQLite Database Schema Definition for local prototyping

-- 1. DOCUMENTS - one row per version of a standard
CREATE TABLE IF NOT EXISTS is_documents (
    document_address TEXT PRIMARY KEY,   -- "IS8130-1984"
    is_number TEXT NOT NULL,
    revision_label TEXT NOT NULL,
    valid_from DATE,
    valid_to DATE,
    is_current BOOLEAN DEFAULT 1,
    superseded_by TEXT
);

-- 2. CLAUSES - one row per section/clause
CREATE TABLE IF NOT EXISTS clauses_meta (
    clause_address TEXT PRIMARY KEY,     -- "IS8130-1984_S6.1"
    document_address TEXT REFERENCES is_documents(document_address) ON DELETE CASCADE,
    heading_text TEXT,
    section_number TEXT,
    body_text TEXT
);

-- 3. TABLES - one row per table found in a document
CREATE TABLE IF NOT EXISTS tables_meta (
    table_address TEXT PRIMARY KEY,      -- "IS8130-1984_T1"
    document_address TEXT REFERENCES is_documents(document_address) ON DELETE CASCADE,
    caption_text TEXT,
    table_type TEXT,                     -- 'relational' | 'matrix' | 'reference_index'
    facets TEXT DEFAULT '{}',            -- JSON string in SQLite
    search_vector TEXT                   -- Not used in SQLite
);

-- 4. CELLS - finest-grained actual data
CREATE TABLE IF NOT EXISTS table_cells (
    cell_address TEXT PRIMARY KEY,       -- "IS8130-1984_T1_R2.5_Cplain"
    table_address TEXT REFERENCES tables_meta(table_address) ON DELETE CASCADE,
    row_label TEXT,
    col_label TEXT,
    value TEXT,
    bbox TEXT,                           -- JSON string in SQLite
    confidence REAL,
    page INTEGER,
    source TEXT
);

-- 5. EDGES - every reference: column-based or clause-based
CREATE TABLE IF NOT EXISTS edges (
    edge_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_address TEXT NOT NULL,
    target_address TEXT NOT NULL,
    target_facets TEXT,                  -- JSON string in SQLite
    edge_type TEXT NOT NULL              -- 'column_reference' | 'clause_value_reference' | 'clause_table_reference' | 'clause_group_reference'
);

-- 6. CACHE - disposable, regenerable
CREATE TABLE IF NOT EXISTS resolution_cache (
    query_hash TEXT PRIMARY KEY,
    resolved_cell_address TEXT,
    value TEXT,
    path_taken TEXT,                     -- JSON string in SQLite
    document_versions_used TEXT,          -- CSV or JSON array string
    resolved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_clauses_doc ON clauses_meta(document_address);
CREATE INDEX IF NOT EXISTS idx_tables_doc ON tables_meta(document_address);
CREATE INDEX IF NOT EXISTS idx_cells_table ON table_cells(table_address);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_address);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_address);
