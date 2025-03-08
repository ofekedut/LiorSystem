CREATE_SCHEMA_QUERIES = [
    # ### 1. Functions and Enum Types
    # Define utility functions and custom enum types used across the schema.
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

    # ### 2. Independent Lookup Tables
    # Create tables with no foreign key dependencies first.
    """CREATE TABLE IF NOT EXISTS document_types (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL UNIQUE,
        value TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );""",
    """CREATE TABLE IF NOT EXISTS person_roles (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL UNIQUE,
        value TEXT NOT NULL UNIQUE
    );""",
    """CREATE TABLE IF NOT EXISTS fin_org_types (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL UNIQUE,
        value TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );""",
    """CREATE TABLE IF NOT EXISTS loan_goals (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL UNIQUE,
        value TEXT NOT NULL UNIQUE
    );""",
    """CREATE TABLE IF NOT EXISTS person_marital_statuses (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL UNIQUE,
        value TEXT NOT NULL UNIQUE
    );""",
    """CREATE TABLE IF NOT EXISTS employment_types (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL UNIQUE,
        value TEXT NOT NULL UNIQUE
    );""",
    """CREATE TABLE IF NOT EXISTS bank_account_type (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL UNIQUE,
        value TEXT NOT NULL UNIQUE
    );""",
    """CREATE TABLE IF NOT EXISTS credit_card_types (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL UNIQUE,
        value TEXT NOT NULL UNIQUE
    );""",
    """CREATE TABLE IF NOT EXISTS loan_types (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL UNIQUE,
        value TEXT NOT NULL UNIQUE
    );""",
    """CREATE TABLE IF NOT EXISTS income_sources_types (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL UNIQUE,
        value TEXT NOT NULL UNIQUE
    );""",
    """CREATE TABLE IF NOT EXISTS related_person_relationships_types (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL UNIQUE,
        value TEXT NOT NULL UNIQUE
    );""",
    """CREATE TABLE IF NOT EXISTS company_types (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL UNIQUE,
        value TEXT NOT NULL UNIQUE
    );""",
    """CREATE TABLE IF NOT EXISTS asset_types (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL UNIQUE,
        value TEXT NOT NULL UNIQUE
    );""",
    """CREATE TABLE IF NOT EXISTS document_categories (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL UNIQUE,
        value TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );""",

    # ### 3. Users Table
    # Create the users table, which is referenced by other tables.
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

    # ### 4. Documents Table
    # Depends on document_types and document_categories.
    """CREATE TABLE IF NOT EXISTS documents (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL UNIQUE CHECK (length(name) > 0),
        description TEXT,
        document_type_id UUID NOT NULL REFERENCES document_types(id),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        category_id UUID REFERENCES document_categories(id),
        period_type TEXT,
        periods_required INTEGER CHECK (periods_required > 0),
        has_multiple_periods BOOLEAN NOT NULL,
        CONSTRAINT valid_period CHECK (
            (period_type IS NULL AND periods_required IS NULL) OR
            (period_type IS NOT NULL AND periods_required IS NOT NULL)
        )
    );""",

    # ### 5. Cases Table (Initial Creation)
    # Created without primary_contact_id to avoid circular dependency with case_persons.
    """CREATE TABLE IF NOT EXISTS cases (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL CHECK (length(name) > 0),
        status case_status NOT NULL DEFAULT 'active',
        is_default BOOLEAN NOT NULL DEFAULT FALSE,
        title TEXT,
        description TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        case_purpose TEXT,
        loan_type_id UUID REFERENCES loan_types(id)
    );""",

    # ### 6. Case Persons Table
    # Depends on cases, person_roles, and person_marital_statuses.
    """CREATE TABLE IF NOT EXISTS case_persons (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
        first_name VARCHAR(50) NOT NULL CHECK (LENGTH(first_name) >= 2),
        last_name VARCHAR(50) NOT NULL CHECK (LENGTH(last_name) >= 2),
        id_number VARCHAR(50) NOT NULL CHECK (LENGTH(id_number) >= 5),
        gender person_gender NOT NULL,
        role_id UUID REFERENCES person_roles(id),
        birth_date DATE NOT NULL,
        phone VARCHAR(20) CHECK (phone ~ '^\\+?[0-9]{8,15}$'),
        email VARCHAR(255) CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$'),
        status VARCHAR(10) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
        marital_status_id UUID REFERENCES person_marital_statuses(id),
        address TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );""",

    # ### 7. Add primary_contact_id to Cases
    # Add the foreign key to case_persons after case_persons is created.
    """ALTER TABLE cases 
       ADD COLUMN IF NOT EXISTS primary_contact_id UUID,
       ADD CONSTRAINT fk_cases_primary_contact_id 
       FOREIGN KEY (primary_contact_id) REFERENCES case_persons(id);""",

    # ### 8. Tables Depending on Cases, Documents, and Users
    """CREATE TABLE IF NOT EXISTS case_assets (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        case_id UUID NOT NULL REFERENCES cases(id),
        value TEXT NOT NULL
    );""",
    """drop TABLE IF EXISTS case_documents ;""",
    """CREATE TABLE IF NOT EXISTS case_documents (
        case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
        document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        status document_status NOT NULL,
        processing_status document_processing_status NOT NULL DEFAULT 'pending',
        uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        reviewed_at TIMESTAMP WITH TIME ZONE,
        file_path TEXT DEFAULT NULL,
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
        role_id UUID REFERENCES person_roles(id),
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
    """CREATE TABLE IF NOT EXISTS cases_monday_relation (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        case_id UUID NOT NULL REFERENCES cases(id),
        monday_id UUID NOT NULL
    );""",
    """CREATE TABLE IF NOT EXISTS processing_states (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
        document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        step_name TEXT NOT NULL,
        state TEXT NOT NULL,
        message TEXT,
        started_at TIMESTAMP WITH TIME ZONE,
        completed_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        UNIQUE(case_id, document_id, step_name)
    );""",
    """CREATE TABLE IF NOT EXISTS pending_processing_documents (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
        document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending'
    );""",

    # ### 9. Tables with Nested Dependencies
    """CREATE TABLE IF NOT EXISTS person_assets (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        person_id UUID NOT NULL REFERENCES case_persons(id) ON DELETE CASCADE,
        asset_type_id UUID NOT NULL REFERENCES asset_types(id),
        description TEXT NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );""",
    """CREATE TABLE IF NOT EXISTS person_employment_history (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        person_id UUID NOT NULL REFERENCES case_persons(id) ON DELETE CASCADE,
        employer_name TEXT NOT NULL,
        position TEXT NOT NULL,
        employment_type_id UUID NOT NULL REFERENCES employment_types(id),
        current_employer BOOLEAN NOT NULL DEFAULT false,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );""",
    """CREATE TABLE IF NOT EXISTS person_income_sources (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        person_id UUID NOT NULL REFERENCES case_persons(id) ON DELETE CASCADE,
        label TEXT NOT NULL,
        income_source_type_id UUID NOT NULL REFERENCES income_sources_types(id),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );""",
    """CREATE TABLE IF NOT EXISTS person_bank_accounts (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        person_id UUID NOT NULL REFERENCES case_persons(id) ON DELETE CASCADE,
        account_type_id UUID NOT NULL REFERENCES bank_account_type(id),
        bank_name TEXT NOT NULL,
        account_number TEXT NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );""",
    """CREATE TABLE IF NOT EXISTS person_credit_cards (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        person_id UUID NOT NULL REFERENCES case_persons(id) ON DELETE CASCADE,
        issuer TEXT NOT NULL,
        card_type_id UUID NOT NULL REFERENCES credit_card_types(id),
        last_four INTEGER NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );""",
    """CREATE TABLE IF NOT EXISTS person_loans (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        person_id UUID NOT NULL REFERENCES case_persons(id) ON DELETE CASCADE,
        loan_type_id UUID NOT NULL REFERENCES loan_types(id),
        lender TEXT NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );""",
    """CREATE TABLE IF NOT EXISTS case_person_relations (
        from_person_id UUID NOT NULL REFERENCES case_persons(id) ON DELETE CASCADE,
        to_person_id UUID NOT NULL REFERENCES case_persons(id) ON DELETE CASCADE,
        relationship_type_id UUID REFERENCES related_person_relationships_types(id),
        PRIMARY KEY (from_person_id, to_person_id)
    );""",
    """CREATE TABLE IF NOT EXISTS case_person_assets (
        case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
        person_id UUID NOT NULL REFERENCES case_persons(id) ON DELETE CASCADE,
        asset_id UUID NOT NULL REFERENCES person_assets(id) ON DELETE CASCADE,
        relationship_type TEXT NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        PRIMARY KEY (case_id, person_id, asset_id)
    );""",
    """CREATE TABLE IF NOT EXISTS case_person_documents (
        case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
        person_id UUID NOT NULL REFERENCES case_persons(id) ON DELETE CASCADE,
        document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        is_primary BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        PRIMARY KEY (case_id, person_id, document_id)
    );""",
    """CREATE TABLE IF NOT EXISTS fin_orgs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL CHECK (length(name) > 0),
        type_id UUID REFERENCES fin_org_types(id),
        settings JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );""",
    """CREATE TABLE IF NOT EXISTS fin_org_contacts (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        fin_org_id UUID NOT NULL REFERENCES fin_orgs(id) ON DELETE CASCADE,
        full_name TEXT NOT NULL CHECK (length(full_name) > 0),
        email TEXT NOT NULL CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$'),
        phone TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );""",
    """CREATE TABLE IF NOT EXISTS document_entity_relations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        entity_type TEXT NOT NULL,
        entity_id UUID NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        CONSTRAINT unique_document_entity UNIQUE (document_id, entity_type, entity_id)
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
        field_type TEXT NOT NULL,
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
    """CREATE TABLE IF NOT EXISTS processing_step_results (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        processing_state_id UUID NOT NULL REFERENCES processing_states(id) ON DELETE CASCADE,
        result JSONB NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        UNIQUE(processing_state_id)
    );""",
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

    # ### 10. Indexes
    # Add indexes to improve query performance.
    """CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);""",
    """CREATE INDEX IF NOT EXISTS idx_cases_last_active ON cases(last_active);""",
    """CREATE INDEX IF NOT EXISTS idx_case_persons_name ON case_persons(first_name, last_name);""",
    """CREATE INDEX IF NOT EXISTS idx_case_persons_id_number ON case_persons(id_number);""",
    """CREATE INDEX IF NOT EXISTS idx_case_persons_role_id ON case_persons(role_id);""",
    """CREATE INDEX IF NOT EXISTS idx_case_companies_role_id ON case_companies(role_id);""",
    """CREATE INDEX IF NOT EXISTS idx_documents_document_type_id ON documents(document_type_id);""",
    """CREATE INDEX IF NOT EXISTS idx_documents_category_id ON documents(category_id);""",
    """CREATE INDEX IF NOT EXISTS idx_document_entity_relations_document_id ON document_entity_relations(document_id);""",
    """CREATE INDEX IF NOT EXISTS idx_document_entity_relations_entity ON document_entity_relations(entity_type, entity_id);""",
    """CREATE INDEX IF NOT EXISTS idx_pending_processing_document_case_id ON pending_processing_documents(case_id);""",
    """CREATE INDEX IF NOT EXISTS idx_case_person_assets_case_id ON case_person_assets(case_id);""",
    """CREATE INDEX IF NOT EXISTS idx_case_person_assets_person_id ON case_person_assets(person_id);""",
    """CREATE INDEX IF NOT EXISTS idx_case_person_assets_asset_id ON case_person_assets(asset_id);""",
    """CREATE INDEX IF NOT EXISTS idx_case_person_documents_case_id ON case_person_documents(case_id);""",
    """CREATE INDEX IF NOT EXISTS idx_case_person_documents_person_id ON case_person_documents(person_id);""",
    """CREATE INDEX IF NOT EXISTS idx_case_person_documents_document_id ON case_person_documents(document_id);""",
    """CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);""",
    """CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);""",
    """CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);""",
    """CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login);""",
    """CREATE INDEX IF NOT EXISTS idx_users_lockout ON users(lockout_until);""",
    """CREATE INDEX IF NOT EXISTS idx_users_deleted ON users(deleted_at);""",

    # ### 11. Triggers
    # Add triggers to automatically update the updated_at column.
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
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_person_assets_timestamp'
      ) THEN
        CREATE TRIGGER update_person_assets_timestamp
        BEFORE UPDATE ON person_assets
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
      END IF;
    END$$;""",
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_person_employment_history_timestamp'
      ) THEN
        CREATE TRIGGER update_person_employment_history_timestamp
        BEFORE UPDATE ON person_employment_history
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
      END IF;
    END$$;""",
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_person_income_sources_timestamp'
      ) THEN
        CREATE TRIGGER update_person_income_sources_timestamp
        BEFORE UPDATE ON person_income_sources
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
      END IF;
    END$$;""",
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_person_bank_accounts_timestamp'
      ) THEN
        CREATE TRIGGER update_person_bank_accounts_timestamp
        BEFORE UPDATE ON person_bank_accounts
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
      END IF;
    END$$;""",
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_person_credit_cards_timestamp'
      ) THEN
        CREATE TRIGGER update_person_credit_cards_timestamp
        BEFORE UPDATE ON person_credit_cards
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
      END IF;
    END$$;""",
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_person_loans_timestamp'
      ) THEN
        CREATE TRIGGER update_person_loans_timestamp
        BEFORE UPDATE ON person_loans
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
      END IF;
    END$$;""",
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_document_entity_relations_timestamp'
      ) THEN
        CREATE TRIGGER update_document_entity_relations_timestamp
        BEFORE UPDATE ON document_entity_relations
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
      END IF;
    END$$;""",
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_case_loans_timestamp'
      ) THEN
        CREATE TRIGGER update_case_loans_timestamp
        BEFORE UPDATE ON case_loans
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
      END IF;
    END$$;""",
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_case_companies_timestamp'
      ) THEN
        CREATE TRIGGER update_case_companies_timestamp
        BEFORE UPDATE ON case_companies
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
      END IF;
    END$$;""",
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_case_desired_products_timestamp'
      ) THEN
        CREATE TRIGGER update_case_desired_products_timestamp
        BEFORE UPDATE ON case_desired_products
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
      END IF;
    END$$;""",
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_users_timestamp'
      ) THEN
        CREATE TRIGGER update_users_timestamp
        BEFORE UPDATE ON users
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
      END IF;
    END$$;""",
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_processing_states_timestamp'
      ) THEN
        CREATE TRIGGER update_processing_states_timestamp
        BEFORE UPDATE ON processing_states
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
      END IF;
    END$$;""",
    """DO $$ BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_processing_step_results_timestamp'
      ) THEN
        CREATE TRIGGER update_processing_step_results_timestamp
        BEFORE UPDATE ON processing_step_results
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
      END IF;
    END$$;""",
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

    # ### 12. Additional Functions
    # Utility function to retrieve category ID by value.
    """CREATE OR REPLACE FUNCTION get_category_id_by_value(category_value TEXT) 
       RETURNS UUID AS $$
       DECLARE
         category_id UUID;
       BEGIN
         SELECT id INTO category_id FROM document_categories WHERE value = category_value;
         RETURN category_id;
       END;
       $$ LANGUAGE plpgsql;""",
]
DROP_ALL_QUERIES = """
DO $$
BEGIN
    DROP TABLE IF EXISTS pending_processing_documents CASCADE;
    DROP TABLE IF EXISTS processing_step_results CASCADE; -- Added missing table
    DROP TABLE IF EXISTS processing_states CASCADE; -- Added missing table
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
    DROP TABLE IF EXISTS cases_monday_relation CASCADE; -- Added missing table
    DROP TABLE IF EXISTS loan_types CASCADE;
    DROP TABLE IF EXISTS loan_goals CASCADE;
    DROP TABLE IF EXISTS person_marital_statuses CASCADE;
    DROP TABLE IF EXISTS employment_types CASCADE;
    DROP TABLE IF EXISTS bank_account_type CASCADE;
    DROP TABLE IF EXISTS credit_card_types CASCADE; -- Added missing table
    DROP TABLE IF EXISTS income_sources_types CASCADE; -- Added missing table
    DROP TABLE IF EXISTS related_person_relationships_types CASCADE; -- Added missing table
    DROP TABLE IF EXISTS company_types CASCADE; -- Added missing table
    DROP TABLE IF EXISTS document_categories CASCADE;
    drop table if exists fin_org_types CASCADE;
    DROP TABLE IF EXISTS document_types CASCADE;
    DROP TABLE IF EXISTS fin_org_contacts CASCADE; 
    DROP TABLE IF EXISTS fin_orgs CASCADE;
    DROP TABLE IF EXISTS login_attempts CASCADE;
    DROP TABLE IF EXISTS token_blacklist CASCADE; 
    DROP TABLE IF EXISTS users CASCADE;
    DROP TYPE IF EXISTS document_processing_status CASCADE;
    DROP TYPE IF EXISTS user_role CASCADE;
    DROP TYPE IF EXISTS person_gender CASCADE;
    DROP TYPE IF EXISTS case_status CASCADE;
    DROP TYPE IF EXISTS case_person_relation CASCADE;
    DROP TYPE IF EXISTS validation_operator CASCADE;
    DROP table IF EXISTS cases CASCADE;
    DROP table IF EXISTS case_loans CASCADE;
    DROP TYPE IF EXISTS document_status CASCADE; 
    DROP TYPE IF EXISTS loan_status CASCADE; 
    DROP FUNCTION IF EXISTS set_updated_at cascade;
    DROP FUNCTION IF EXISTS get_category_id_by_value cascade;
END$$;"""
