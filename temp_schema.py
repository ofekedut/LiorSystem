CREATE_SCHEMA_QUERIES = [
    """CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS 39418
    BEGIN
      NEW.updated_at = NOW();
      RETURN NEW;
    END;
    39418 LANGUAGE plpgsql;""",
    """DO 39418 BEGIN 
       CREATE TYPE required_for AS ENUM ('employees','self-employed','business-owners','all'); 
       EXCEPTION WHEN duplicate_object THEN null; 
       END39418;""",
    """DO 39418 BEGIN 
       CREATE TYPE validation_operator AS ENUM (
           'equals','not_equals','greater_than','less_than','between','contains',
           'starts_with','ends_with','before','after'
       ); 
       EXCEPTION WHEN duplicate_object THEN null; 
       END39418;""",
    """DO 39418 BEGIN 
       CREATE TYPE case_status AS ENUM ('active', 'inactive', 'pending'); 
       EXCEPTION WHEN duplicate_object THEN null; 
       END39418;""",
    """DO 39418 BEGIN 
       CREATE TYPE person_role AS ENUM ('primary', 'cosigner', 'guarantor'); 
       EXCEPTION WHEN duplicate_object THEN null; 
       END39418;""",
