CREATE_SCHEMA_QUERIES = [
    """
    CREATE EXTENSION IF NOT EXISTS pgvector;
"""
    """CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
    BEGIN
      NEW.updated_at = NOW();
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;""",

    # =====================================
    # 1. Enum Types
    # =====================================
    """DO $$ BEGIN 
       CREATE TYPE document_type AS ENUM ('one-time','updatable','recurring'); 
       EXCEPTION WHEN duplicate_object THEN null; 
       END$$;""",
    """DO $$ BEGIN 
       CREATE TYPE document_category AS ENUM ('identification','financial','property','employment','tax'); 
       EXCEPTION WHEN duplicate_object THEN null; 
       END$$;""",
    """DO $$ BEGIN 
       CREATE TYPE required_for AS ENUM ('employees','self-employed','business-owners','all'); 
       EXCEPTION WHEN duplicate_object THEN null; 
       END$$;""",
    """DO $$ BEGIN 
       CREATE TYPE validation_operator AS ENUM (
           'equals','not_equals','greater_than','less_than','between','contains',
           'starts_with','ends_with','before','after'
       ); 
       EXCEPTION WHEN duplicate_object THEN null; 
       END$$;""",
    """DO $$ BEGIN 
       CREATE TYPE case_status AS ENUM ('active', 'inactive', 'pending'); 
       EXCEPTION WHEN duplicate_object THEN null; 
       END$$;""",
    """DO $$ BEGIN 
       CREATE TYPE person_role AS ENUM ('primary', 'cosigner', 'guarantor'); 
       EXCEPTION WHEN duplicate_object THEN null; 
       END$$;""",
    """DO $$ BEGIN 
       CREATE TYPE person_gender AS ENUM ('male', 'female'); 
       EXCEPTION WHEN duplicate_object THEN null; 
       END$$;""",
    """DO $$ BEGIN 
       CREATE TYPE document_status AS ENUM ('pending', 'approved', 'rejected'); 
       EXCEPTION WHEN duplicate_object THEN null; 
       END$$;""",
    """DO $$ BEGIN 
       CREATE TYPE document_processing_status AS ENUM ('processed', 'pending', 'error', 'userActionRequired'); 
       EXCEPTION WHEN duplicate_object THEN null; 
       END$$;""",
    """DO $$ BEGIN 
       CREATE TYPE loan_status AS ENUM ('active', 'closed', 'defaulted'); 
       EXCEPTION WHEN duplicate_object THEN null; 
       END$$;""",

    # =====================================
    # 2. Utility Tables (Tokens, Attempts)
    # =====================================
    """CREATE TABLE IF NOT EXISTS token_blacklist (
        jti UUID PRIMARY KEY,
        user_id UUID NOT NULL,
        expires_at TIMESTAMP WITH TIME ZONE NOT NULL
    );""",
    """CREATE TABLE IF NOT EXISTS login_attempts (
        email VARCHAR(255) PRIMARY KEY,
        attempts INT NOT NULL DEFAULT 1,
        last_attempt TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        locked_until TIMESTAMP WITH TIME ZONE
    );""",

    # =====================================
    # 3. Users Table (Already Using UUID)
    # =====================================
    """CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email VARCHAR(255) UNIQUE NOT NULL CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$'),
        first_name VARCHAR(50) NOT NULL CHECK (LENGTH(first_name) >= 2),
        last_name VARCHAR(50) NOT NULL CHECK (LENGTH(last_name) >= 2),
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(10) NOT NULL CHECK (role IN ('admin', 'user')) DEFAULT 'user',
        status VARCHAR(10) NOT NULL CHECK (status IN ('active', 'inactive', 'suspended')) DEFAULT 'active',
        phone VARCHAR(20) CHECK (phone ~ '^\\+?[0-9]{8,15}$'),
        department VARCHAR(100),
        position VARCHAR(100),
        avatar VARCHAR(255),
        preferences JSONB NOT NULL DEFAULT '{
                        "language": "he",
                        "notifications": {
                            "email": true,
                            "system": true,
                            "types": {
                                "cases": true,
                                "documents": true,
                                "system": true
                            }
                        },
                        "timezone": "UTC"
                    }'::jsonb,
        last_login TIMESTAMP WITH TIME ZONE,
        last_failed_login TIMESTAMP WITH TIME ZONE,
        failed_login_attempts INT DEFAULT 0,
        lockout_until TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        deleted_at TIMESTAMP WITH TIME ZONE,
        email_verified BOOLEAN DEFAULT false
    );""",
    """CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);""",
    """CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);""",
    """CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);""",
    """CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login);""",
    """CREATE INDEX IF NOT EXISTS idx_users_lockout ON users(lockout_until);""",
    """CREATE INDEX IF NOT EXISTS idx_users_deleted ON users(deleted_at);""",

    # =====================================
    # 4. FinOrgs & FinOrgContacts
    # =====================================
    """CREATE TABLE IF NOT EXISTS fin_orgs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL CHECK (length(name) > 0),
        type TEXT NOT NULL CHECK (length(type) > 0),
        settings JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );""",
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_fin_orgs_timestamp'
      ) THEN
        CREATE TRIGGER update_fin_orgs_timestamp
        BEFORE UPDATE ON fin_orgs
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
      END IF;
    END$$;""",
    """CREATE TABLE IF NOT EXISTS fin_org_contacts (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        fin_org_id UUID NOT NULL REFERENCES fin_orgs(id) ON DELETE CASCADE,
        full_name TEXT NOT NULL CHECK (length(full_name) > 0),
        email TEXT NOT NULL CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$'),
        phone TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );""",
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_fin_org_contacts_timestamp'
      ) THEN
        CREATE TRIGGER update_fin_org_contacts_timestamp
        BEFORE UPDATE ON fin_org_contacts
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
      END IF;
    END$$;""",

    # =====================================
    # 5. Documents & Related Tables
    # =====================================
    """CREATE TABLE IF NOT EXISTS documents (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL CHECK (length(name) > 0),
        description TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        document_type document_type NOT NULL,
        category document_category NOT NULL,
        period_type TEXT,
        periods_required INTEGER CHECK (periods_required > 0),
        has_multiple_periods BOOLEAN NOT NULL,
        CONSTRAINT valid_period CHECK (
            (period_type IS NULL AND periods_required IS NULL) OR
            (period_type IS NOT NULL AND periods_required IS NOT NULL)
        )
    );""",

    """CREATE TABLE IF NOT EXISTS documents_required_for (
        document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        required_for required_for NOT NULL,
        PRIMARY KEY(document_id, required_for)
    );""",

    """CREATE TABLE IF NOT EXISTS document_fields (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        name TEXT NOT NULL CHECK (length(name) > 0),
        type TEXT NOT NULL CHECK (type = ANY(ARRAY['string','number','date','currency'])),
        is_identifier BOOLEAN NOT NULL DEFAULT false,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );""",

    """CREATE TABLE IF NOT EXISTS validation_rules (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        field TEXT NOT NULL CHECK (length(field) > 0),
        operator validation_operator NOT NULL,
        value JSONB,
        error_message TEXT NOT NULL CHECK (length(error_message) > 0),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );""",

    # ----- Indexes for Document Tables -----
    """CREATE INDEX IF NOT EXISTS idx_documents_name ON documents(name);""",
    """CREATE INDEX IF NOT EXISTS idx_documents_type_category ON documents(document_type, category);""",
    """CREATE INDEX IF NOT EXISTS idx_document_fields_document_id ON document_fields(document_id);""",
    """CREATE INDEX IF NOT EXISTS idx_validation_rules_document_id ON validation_rules(document_id);""",
    """CREATE INDEX IF NOT EXISTS idx_validation_rules_field ON validation_rules(field);""",
    """CREATE INDEX IF NOT EXISTS idx_documents_required_for_document_id ON documents_required_for(document_id);""",

    # ----- Trigger for updating documents.updated_at -----
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_documents_timestamp'
      ) THEN
        CREATE TRIGGER update_documents_timestamp
        BEFORE UPDATE ON documents
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
      END IF;
    END$$;""",

    # =====================================
    # 6. Cases & Related Tables (Using UUID)
    # =====================================
    """CREATE TABLE IF NOT EXISTS cases (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL CHECK (length(name) > 0),
        status case_status NOT NULL,
        activity_level SMALLINT NOT NULL CHECK (activity_level BETWEEN 0 AND 100),
        last_active TIMESTAMP WITH TIME ZONE NOT NULL,
        project_count INTEGER NOT NULL DEFAULT 0 CHECK (project_count >= 0),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );""",

    """CREATE TABLE IF NOT EXISTS case_persons (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
        first_name VARCHAR(50) NOT NULL CHECK (length(first_name) >= 2),
        last_name VARCHAR(50) NOT NULL CHECK (length(last_name) >= 2),
        id_number VARCHAR(50) NOT NULL UNIQUE CHECK (length(id_number) >= 5),
        age SMALLINT CHECK (age BETWEEN 0 AND 150),
        gender person_gender NOT NULL,
        role person_role NOT NULL,
        birth_date DATE NOT NULL,
        phone VARCHAR(20) CHECK (phone ~ '^\\+?[0-9]{8,15}$'),
        email VARCHAR(255) CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$'),
        status VARCHAR(10) NOT NULL CHECK (status IN ('active', 'inactive')),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );""",

    """CREATE TABLE IF NOT EXISTS case_person_relations (
        from_person_id UUID NOT NULL REFERENCES case_persons(id) ON DELETE CASCADE,
        to_person_id   UUID NOT NULL REFERENCES case_persons(id) ON DELETE CASCADE,
        relationship_type TEXT NOT NULL CHECK (length(relationship_type) > 0),
        PRIMARY KEY (from_person_id, to_person_id)
    );""",

    """CREATE TABLE IF NOT EXISTS case_documents (
        case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
        document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        status document_status NOT NULL,
        processing_status document_processing_status NOT NULL,
        uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        reviewed_at TIMESTAMP WITH TIME ZONE,
        uploaded_by UUID REFERENCES users(id),
        PRIMARY KEY (case_id, document_id)
    );""",

    """CREATE TABLE IF NOT EXISTS case_loans (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
        amount NUMERIC(15,2) NOT NULL CHECK (amount > 0),
        status loan_status NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );""",

    # ----- Indexes for Cases -----
    """CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);""",
    """CREATE INDEX IF NOT EXISTS idx_cases_last_active ON cases(last_active);""",
    """CREATE INDEX IF NOT EXISTS idx_case_persons_name ON case_persons(first_name, last_name);""",
    """CREATE INDEX IF NOT EXISTS idx_case_persons_id_number ON case_persons(id_number);""",
    """CREATE INDEX IF NOT EXISTS idx_case_documents_status ON case_documents(status);""",
    """CREATE INDEX IF NOT EXISTS idx_case_documents_processing ON case_documents(processing_status);""",
    """CREATE INDEX IF NOT EXISTS idx_case_loans_status ON case_loans(status);""",

    # ----- Triggers for updating timestamps on cases/case_persons -----
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_cases_timestamp'
      ) THEN
        CREATE TRIGGER update_cases_timestamp
        BEFORE UPDATE ON cases
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
      END IF;
    END$$;""",
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_case_persons_timestamp'
      ) THEN
        CREATE TRIGGER update_case_persons_timestamp
        BEFORE UPDATE ON case_persons
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
      END IF;
    END$$;""",
    # --- Tables for new documents uploaded and pending processing. ---
    # Table to record the processing state of a document at a specific step.
    '''CREATE TABLE IF NOT EXISTS processing_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    step_name TEXT NOT NULL,  -- Name of the processing step defined in code
    state TEXT NOT NULL,      -- e.g., 'pending', 'in_progress', 'completed', 'failed'
    message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    UNIQUE(case_id, document_id, step_name)
);
    ''',
    # Table to reference a document pending its initial processing for a case.
    '''CREATE TABLE IF NOT EXISTS pending_processing_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'  -- e.g., 'pending', 'processing', 'completed'
);
    ''',
    '''
  CREATE TABLE IF NOT EXISTS processing_step_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    processing_state_id UUID NOT NULL REFERENCES processing_states(id) ON DELETE CASCADE,
    result JSONB NOT NULL,
    embedding_prop vector(1536),  -- Adjust the dimension (e.g., 1536) as needed; nullable by default.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    UNIQUE(processing_state_id)
);
''',
]

DROP_ALL_QUERIES = """
DO $$
DECLARE
    _stmt TEXT;
BEGIN
    -- Drop relationships first
    DROP TABLE IF EXISTS case_person_relations CASCADE;
    DROP TABLE IF EXISTS case_loans CASCADE;
    DROP TABLE IF EXISTS case_documents CASCADE;
    DROP TABLE IF EXISTS case_persons CASCADE;
    DROP TABLE IF EXISTS cases CASCADE;

    -- Drop enum types associated with cases
    DROP TYPE IF EXISTS loan_status CASCADE;
    DROP TYPE IF EXISTS document_status CASCADE;
    DROP TYPE IF EXISTS person_gender CASCADE;
    DROP TYPE IF EXISTS person_role CASCADE;
    DROP TYPE IF EXISTS case_status CASCADE;

    -- Drop document-related tables
    DROP TABLE IF EXISTS validation_rules CASCADE;
    DROP TABLE IF EXISTS document_fields CASCADE;
    DROP TABLE IF EXISTS documents_required_for CASCADE;
    DROP TABLE IF EXISTS documents CASCADE;

    -- Drop FinOrg & FinOrgContacts
    DROP TABLE IF EXISTS fin_org_contacts CASCADE;
    DROP TABLE IF EXISTS fin_orgs CASCADE;

    -- Drop users & utility
    DROP TABLE IF EXISTS users CASCADE;
    DROP FUNCTION IF EXISTS set_updated_at() CASCADE;
    DROP TYPE IF EXISTS validation_operator CASCADE;
    DROP TYPE IF EXISTS required_for CASCADE;
    DROP TYPE IF EXISTS document_category CASCADE;
    DROP TYPE IF EXISTS document_type CASCADE;
END$$;
"""
