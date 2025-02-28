CREATE_SCHEMA_QUERIES = [
    """CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
    BEGIN
      NEW.updated_at = NOW();
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;""",
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
    """create table if not exists document_types (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        name text not null unique,
        value text not null unique,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );""",
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_document_types_timestamp'
      ) THEN
        CREATE TRIGGER update_document_types_timestamp
        BEFORE UPDATE ON document_types
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
      END IF;
    END$$;""",
    """INSERT INTO document_types (name, value) 
       VALUES ('One Time', 'one-time'), ('Updatable', 'updatable'), ('Recurring', 'recurring')
       ON CONFLICT (value) DO NOTHING;""",
    """CREATE TABLE IF NOT EXISTS person_roles (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name text not null unique ,
        value text not null  unique 
    );""",
    """INSERT INTO person_roles (id, name, value)
    VALUES 
        (gen_random_uuid(), 'Primary', 'primary'),
        (gen_random_uuid(), 'Cosigner', 'cosigner'),
        (gen_random_uuid(), 'Guarantor', 'guarantor')
    ON CONFLICT (value) DO NOTHING;""",
    """
    create table if not exists fin_org_types (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        name text not null unique,
        value text not null unique,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );
    """,
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_fin_org_types_timestamp'
      ) THEN
        CREATE TRIGGER update_fin_org_types_timestamp
        BEFORE UPDATE ON fin_org_types
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
      END IF;
    END$$;""",
    """
    create table if not exists loan_types (
        id uuid PRIMARY KEY,
        name text not null  unique ,
        value text not null unique 
    );
    """,
    """INSERT INTO loan_types (id, name, value)
    VALUES 
        (gen_random_uuid(), 'Single Family Home', 'single_family_home'),
        (gen_random_uuid(), 'Multi Family Home', 'multi_family_home'),
        (gen_random_uuid(), 'Condominium', 'condominium'),
        (gen_random_uuid(), 'Townhouse', 'townhouse'),
        (gen_random_uuid(), 'Personal Loan', 'personal_loan'),
        (gen_random_uuid(), 'Auto Loan', 'auto_loan'),
        (gen_random_uuid(), 'Business Loan', 'business_loan')
    ON CONFLICT (value) DO NOTHING;""",
    """create table if not exists loan_goals (
        id uuid PRIMARY KEY,
        name text not null  unique ,
        value text not null unique 
    );
    """,
    """INSERT INTO loan_goals (id, name, value)
    VALUES 
        (gen_random_uuid(), 'Primary Residence', 'primary_residence'),
        (gen_random_uuid(), 'Secondary Residence', 'secondary_residence'),
        (gen_random_uuid(), 'Investment Property', 'investment_property'),
        (gen_random_uuid(), 'Refinance', 'refinance'),
        (gen_random_uuid(), 'Home Improvement', 'home_improvement'),
        (gen_random_uuid(), 'Debt Consolidation', 'debt_consolidation')
    ON CONFLICT (value) DO NOTHING;""",
    """create table if not exists person_martial_statuses (
        id uuid PRIMARY KEY,
        name text not null  unique ,
        value text not null unique 
    );
    """,
    """INSERT INTO person_martial_statuses (id, name, value)
    VALUES 
        (gen_random_uuid(), 'Single', 'single'),
        (gen_random_uuid(), 'Married', 'married'),
        (gen_random_uuid(), 'Divorced', 'divorced'),
        (gen_random_uuid(), 'Widowed', 'widowed'),
        (gen_random_uuid(), 'Separated', 'separated')
    ON CONFLICT (value) DO NOTHING;""",
    """create table if not exists employment_types(
        id uuid PRIMARY KEY,
        name text not null  unique ,
        value text not null unique 
    );
    """,
    """INSERT INTO employment_types (id, name, value)
    VALUES 
        (gen_random_uuid(), 'Full Time', 'full_time'),
        (gen_random_uuid(), 'Part Time', 'part_time'),
        (gen_random_uuid(), 'Self Employed', 'self_employed'),
        (gen_random_uuid(), 'Contractor', 'contractor'),
        (gen_random_uuid(), 'Unemployed', 'unemployed'),
        (gen_random_uuid(), 'Retired', 'retired')
    ON CONFLICT (value) DO NOTHING;""",
    """create table if not exists bank_account_type(
        id uuid PRIMARY KEY,
        name text not null  unique ,
        value text not null unique 
    );
    """,
    """create table if not exists credit_card_types(
        id uuid PRIMARY KEY,
        name text not null  unique ,
        value text not null unique 
    );
    """,
    """create table if not exists loan_types(
        id uuid PRIMARY KEY,
        name text not null  unique ,
        value text not null unique 
    );
    """,
    """create table if not exists income_sources_types(
        id uuid PRIMARY KEY,
        name text not null  unique ,
        value text not null unique 
    );
    """,
    """create table if not exists related_person_relationships_types(
        id uuid PRIMARY KEY,
        name text not null  unique ,
        value text not null unique 
    );
    """,
    """create table if not exists company_types (
        id uuid PRIMARY KEY,
        name text not null  unique ,
        value text not null unique 
    );
    """,
    """create table if not exists asset_types (
        id uuid PRIMARY KEY,
        name text not null unique,
        value text not null unique 
    );
    """,
    """INSERT INTO asset_types (id, name, value)
    VALUES 
        (gen_random_uuid(), 'Car', 'car'),
        (gen_random_uuid(), 'Real Estate', 'real_estate'),
        (gen_random_uuid(), 'Cash', 'cash'),
        (gen_random_uuid(), 'Stock', 'stock'),
        (gen_random_uuid(), 'Jewelry', 'jewelry'),
        (gen_random_uuid(), 'Cryptocurrency', 'crypto'),
        (gen_random_uuid(), 'Art', 'art'),
        (gen_random_uuid(), 'Collectibles', 'collectibles')
    ON CONFLICT (value) DO NOTHING;""",
    """create table if not exists document_categories (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        name text not null unique,
        value text not null unique,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );
    """,
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_document_categories_timestamp'
      ) THEN
        CREATE TRIGGER update_document_categories_timestamp
        BEFORE UPDATE ON document_categories
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
      END IF;
    END$$;""",
    """INSERT INTO document_categories (name, value) 
       VALUES ('Identification', 'identification'), ('Financial', 'financial'), ('Property', 'property'), ('Employment', 'employment'), ('Tax', 'tax')
       ON CONFLICT (value) DO NOTHING;""",
    """CREATE OR REPLACE FUNCTION get_category_id_by_value(category_value TEXT) 
       RETURNS UUID AS $$
       DECLARE
         category_id UUID;
       BEGIN
         SELECT id INTO category_id FROM document_categories WHERE value = category_value;
         RETURN category_id;
       END;
       $$ LANGUAGE plpgsql;""",
    """INSERT INTO document_categories (id, name, value) 
       VALUES 
           (gen_random_uuid(), 'Bank Account', 'bank_account'),
           (gen_random_uuid(), 'Credit Card', 'credit_card'),
           (gen_random_uuid(), 'Loan', 'loan'),
           (gen_random_uuid(), 'Asset', 'asset'),
           (gen_random_uuid(), 'Income', 'income'),
           (gen_random_uuid(), 'Personal', 'personal'),
           (gen_random_uuid(), 'Company', 'company')
       ON CONFLICT (value) DO NOTHING;""",
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
        document_type_id UUID NOT NULL REFERENCES document_types(id),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        category TEXT NOT NULL,
        category_id UUID REFERENCES document_categories(id),
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
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        field_type text not null,
        is_required BOOLEAN NOT NULL DEFAULT false
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

    # ----- Trigger to populate category_id from category -----
    """CREATE OR REPLACE FUNCTION set_category_id() RETURNS TRIGGER AS $$
    BEGIN
      IF NEW.category_id IS NULL THEN
        SELECT id INTO NEW.category_id FROM document_categories WHERE value = NEW.category;
      END IF;
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;""",
    
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_documents_category_id'
      ) THEN
        CREATE TRIGGER update_documents_category_id
        BEFORE INSERT OR UPDATE ON documents
        FOR EACH ROW
        EXECUTE PROCEDURE set_category_id();
      END IF;
    END$$;""",

    # Also create index on the new category_id field
    """CREATE INDEX IF NOT EXISTS idx_documents_category_id ON documents(category_id);""",

    # ----- Indexes for Document Tables -----
    """CREATE INDEX IF NOT EXISTS idx_documents_name ON documents(name);""",
    """CREATE INDEX IF NOT EXISTS idx_documents_type_category ON documents(document_type_id, category);""",
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

    """CREATE TABLE IF NOT EXISTS document_entity_relations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        entity_type TEXT NOT NULL, -- 'person_asset', 'bank_account', 'credit_card', 'loan', 'income_source', 'employment', 'company'
        entity_id UUID NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        CONSTRAINT unique_document_entity UNIQUE (document_id, entity_type, entity_id)
    );""",
    
    """CREATE INDEX IF NOT EXISTS idx_document_entity_relations_document_id 
    ON document_entity_relations(document_id);""",
    
    """CREATE INDEX IF NOT EXISTS idx_document_entity_relations_entity 
    ON document_entity_relations(entity_type, entity_id);""",

    # =====================================
    # 6. Cases & Related Tables (Using UUID)
    # =====================================
    """CREATE TABLE IF NOT EXISTS cases (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL CHECK (length(name) > 0),
        status case_status NOT NULL DEFAULT 'active',
        is_default BOOLEAN NOT NULL DEFAULT FALSE,
        primary_contact_id UUID,
        title TEXT,
        description TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        case_purpose TEXT,
        loan_type TEXT
    );""",
    """CREATE TABLE IF NOT EXISTS case_persons (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
        first_name VARCHAR(50) NOT NULL CHECK (LENGTH(first_name) >= 2),
        last_name VARCHAR(50) NOT NULL CHECK (LENGTH(last_name) >= 2),
        id_number VARCHAR(50) NOT NULL UNIQUE CHECK (LENGTH(id_number) >= 5),
        gender person_gender NOT NULL,
        role TEXT NOT NULL,
        role_id UUID REFERENCES person_roles(id),
        birth_date DATE NOT NULL,
        phone VARCHAR(20) CHECK (phone ~ '^\\+?[0-9]{8,15}$'),
        email VARCHAR(255) CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$'),
        marital_status TEXT,
        status VARCHAR(10) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
        marital_status_id UUID REFERENCES person_martial_statuses(id),
        address TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );""",
    """
    create table if not exists case_assets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id uuid not null references cases(id),
    value text not null
    );
    """,
    """CREATE TABLE IF NOT EXISTS person_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES case_persons(id) ON DELETE CASCADE,
    asset_type_id UUID NOT NULL REFERENCES asset_types(id),
    description TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );
    """,
    """CREATE TABLE IF NOT EXISTS person_employment_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES case_persons(id) ON DELETE CASCADE,
    employer_name TEXT NOT NULL,
    position TEXT NOT NULL,
    employment_type_id UUID NOT NULL REFERENCES employment_types(id),
    current_employer BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );
    """,
    """CREATE TABLE IF NOT EXISTS person_income_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES case_persons(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    income_source_type_id UUID NOT NULL REFERENCES income_sources_types(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );
    """,
    """CREATE TABLE IF NOT EXISTS person_bank_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES case_persons(id) ON DELETE CASCADE,
    account_type_id UUID NOT NULL REFERENCES bank_account_type(id),
    bank_name TEXT NOT NULL,
    account_number TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );
    """,
    """CREATE TABLE IF NOT EXISTS person_credit_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES case_persons(id) ON DELETE CASCADE,
    issuer TEXT NOT NULL,
    card_type_id UUID NOT NULL REFERENCES credit_card_types(id),
    last_four INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );
    """,
    """CREATE TABLE IF NOT EXISTS person_loans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES case_persons(id) ON DELETE CASCADE,
    loan_type_id UUID NOT NULL REFERENCES loan_types(id),
    lender TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );
    """,
    """CREATE TABLE IF NOT EXISTS cases_monday_relation (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        case_id UUID NOT NULL REFERENCES cases(id),
        monday_id UUID NOT NULL
    );""",

    """CREATE OR REPLACE FUNCTION set_role_id() RETURNS TRIGGER AS $$
    BEGIN
      IF NEW.role_id IS NULL THEN
        SELECT id INTO NEW.role_id FROM person_roles WHERE value = NEW.role;
      END IF;
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;""",
    """CREATE TRIGGER set_role_id_trigger
    BEFORE INSERT OR UPDATE ON case_persons
    FOR EACH ROW
    EXECUTE FUNCTION set_role_id();
    """,
    """CREATE OR REPLACE FUNCTION set_marital_status_id() RETURNS TRIGGER AS $$
    BEGIN
      IF NEW.marital_status_id IS NULL AND NEW.marital_status IS NOT NULL THEN
        SELECT id INTO NEW.marital_status_id FROM person_martial_statuses WHERE value = NEW.marital_status;
      END IF;
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;""",
    """CREATE TRIGGER set_marital_status_id_trigger
    BEFORE INSERT OR UPDATE ON case_persons
    FOR EACH ROW
    EXECUTE FUNCTION set_marital_status_id();
    """,
    '''alter table cases add column if not exists primary_contact_id uuid references case_persons(id);
    '''
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
        file_path TEXT default null,
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

    """CREATE TABLE IF NOT EXISTS case_companies (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        company_type_id UUID NOT NULL REFERENCES company_types(id),
        role TEXT NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );""",
    
    """CREATE TABLE IF NOT EXISTS case_desired_products (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
        loan_type_id UUID NOT NULL REFERENCES loan_types(id),
        loan_goal_id UUID NOT NULL REFERENCES loan_goals(id),
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    UNIQUE(processing_state_id)
);
''',
    """CREATE INDEX IF NOT EXISTS idx_pending_processing_document_case_id
    ON pending_processing_documents(case_id);""",
    """ALTER TABLE cases 
       ADD CONSTRAINT fk_cases_primary_contact_id 
       FOREIGN KEY (primary_contact_id) REFERENCES case_persons(id);""",
    """CREATE TABLE IF NOT EXISTS case_person_assets (
        case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
        person_id UUID NOT NULL REFERENCES case_persons(id) ON DELETE CASCADE,
        asset_id UUID NOT NULL REFERENCES person_assets(id) ON DELETE CASCADE,
        relationship_type TEXT NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        PRIMARY KEY (case_id, person_id, asset_id)
    );""",
    """CREATE INDEX IF NOT EXISTS idx_case_person_assets_case_id ON case_person_assets(case_id);""",
    """CREATE INDEX IF NOT EXISTS idx_case_person_assets_person_id ON case_person_assets(person_id);""",
    """CREATE INDEX IF NOT EXISTS idx_case_person_assets_asset_id ON case_person_assets(asset_id);""",
    """CREATE TABLE IF NOT EXISTS case_person_documents (
        case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
        person_id UUID NOT NULL REFERENCES case_persons(id) ON DELETE CASCADE,
        document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        is_primary BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        PRIMARY KEY (case_id, person_id, document_id)
    );""",
    """CREATE INDEX IF NOT EXISTS idx_case_person_documents_case_id ON case_person_documents(case_id);""",
    """CREATE INDEX IF NOT EXISTS idx_case_person_documents_person_id ON case_person_documents(person_id);""",
    """CREATE INDEX IF NOT EXISTS idx_case_person_documents_document_id ON case_person_documents(document_id);""",
]

DROP_ALL_QUERIES = """
DO $$
BEGIN
    DROP TABLE IF EXISTS pending_processing_documents CASCADE;
    DROP TABLE IF EXISTS document_processing_errors CASCADE;
    DROP TABLE IF EXISTS document_processing_steps CASCADE;
    DROP TABLE IF EXISTS documents_data CASCADE;
    DROP TABLE IF EXISTS documents_required_for CASCADE;
    DROP TABLE IF EXISTS validation_rules CASCADE;
    DROP TABLE IF EXISTS document_fields CASCADE;
    DROP TABLE IF EXISTS documents CASCADE;
    DROP TABLE IF EXISTS document_entity_relations CASCADE;
    DROP TABLE IF EXISTS case_person_relations CASCADE;
    DROP TABLE IF EXISTS person_loans CASCADE;
    DROP TABLE IF EXISTS person_credit_cards CASCADE;
    DROP TABLE IF EXISTS person_bank_accounts CASCADE;
    DROP TABLE IF EXISTS person_income_sources CASCADE;
    DROP TABLE IF EXISTS person_employment_history CASCADE;
    DROP TABLE IF EXISTS case_assets CASCADE;
    DROP TABLE IF EXISTS person_assets CASCADE;
    DROP TABLE IF EXISTS case_person_assets CASCADE;
    DROP TABLE IF EXISTS case_person_documents CASCADE;
    DROP TABLE IF EXISTS asset_types CASCADE;
    DROP TABLE IF EXISTS case_companies CASCADE;
    DROP TABLE IF EXISTS case_desired_products CASCADE;
    DROP TABLE IF EXISTS case_persons CASCADE;
    DROP TABLE IF EXISTS cases CASCADE;
    DROP TABLE IF EXISTS loan_types CASCADE;
    DROP TABLE IF EXISTS loan_goals CASCADE;
    DROP TABLE IF EXISTS person_martial_statuses CASCADE;
    DROP TABLE IF EXISTS employment_types CASCADE;
    DROP TABLE IF EXISTS bank_account_type CASCADE;
    DROP TABLE IF EXISTS document_categories CASCADE;
    DROP TABLE IF EXISTS document_types CASCADE;
    DROP TABLE IF EXISTS finorg_contacts CASCADE;
    DROP TABLE IF EXISTS finorgs CASCADE;
    DROP TABLE IF EXISTS login_attempts CASCADE;
    DROP TABLE IF EXISTS users CASCADE; 
    DROP TYPE IF EXISTS document_processing_state CASCADE;
    DROP TYPE IF EXISTS user_role CASCADE;
    DROP TYPE IF EXISTS person_gender CASCADE;
    DROP TYPE IF EXISTS case_status CASCADE;
    DROP TYPE IF EXISTS case_person_relation CASCADE;
    DROP TYPE IF EXISTS validation_operator CASCADE;
    DROP TYPE IF EXISTS required_for CASCADE;
    DROP TYPE IF EXISTS document_category CASCADE;
END$$;
"""
