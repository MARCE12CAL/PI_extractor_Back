-- BASE DE DATOS POSTGRESQL
CREATE DATABASE document_scanner_db;
\c document_scanner_db;

CREATE USER scanner_user WITH PASSWORD 'scanner_pass';
GRANT ALL PRIVILEGES ON DATABASE document_scanner_db TO scanner_user;

-- TABLA 1: TRABAJOS DE ESCANEO
CREATE TABLE scan_jobs (
    id SERIAL PRIMARY KEY,
    folder_path TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    total_files INTEGER DEFAULT 0,
    processed_files INTEGER DEFAULT 0,
    csv_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_scan_jobs_status ON scan_jobs(status);

-- TABLA 2: DOCUMENTOS ESCANEADOS
CREATE TABLE scanned_documents (
    id SERIAL PRIMARY KEY,
    scan_job_id INTEGER NOT NULL REFERENCES scan_jobs(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_type VARCHAR(50),
    has_errors BOOLEAN DEFAULT FALSE,
    empty_fields_count INTEGER DEFAULT 0,
    confidence_score FLOAT DEFAULT 0.0,
    output_pdf_path TEXT,
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scanned_docs_job ON scanned_documents(scan_job_id);
CREATE INDEX idx_scanned_docs_errors ON scanned_documents(has_errors);

-- TABLA 3: CAMPOS EXTRAÍDOS
CREATE TABLE document_fields (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES scanned_documents(id) ON DELETE CASCADE,
    field_name VARCHAR(255) NOT NULL,
    field_value TEXT,
    is_empty BOOLEAN DEFAULT FALSE,
    is_critical BOOLEAN DEFAULT FALSE,
    confidence FLOAT DEFAULT 0.0,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fields_document ON document_fields(document_id);
CREATE INDEX idx_fields_critical ON document_fields(is_critical);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO scanner_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO scanner_user;

COMMIT;
