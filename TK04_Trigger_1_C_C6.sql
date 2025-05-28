-- =====================================================
-- AUTHENTICATION TRIGGERS & STORED PROCEDURES
-- =====================================================

-- STORED PROCEDURE: Check Username Duplication during Registration
CREATE OR REPLACE FUNCTION check_username_duplicate(p_username VARCHAR(50))
RETURNS TEXT AS $$
BEGIN
    -- Check if username already exists
    IF EXISTS (SELECT 1 FROM pengguna WHERE username = p_username) THEN
        RETURN 'ERROR: Username "' || p_username || '" sudah digunakan, silakan pilih username lain.';
    END IF;
    
    -- If no duplicate found, return success
    RETURN 'SUCCESS';
END;
$$ LANGUAGE plpgsql;

-- TRIGGER FUNCTION: Prevent Username Duplication on Insert
CREATE OR REPLACE FUNCTION prevent_duplicate_username()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if username already exists
    IF EXISTS (SELECT 1 FROM pengguna WHERE username = NEW.username AND username != COALESCE(OLD.username, '')) THEN
        RAISE EXCEPTION 'ERROR: Username "%" sudah digunakan, silakan pilih username lain.', NEW.username;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- TRIGGER: Apply username duplication check on INSERT and UPDATE
DROP TRIGGER IF EXISTS trigger_check_username_duplicate ON pengguna;
CREATE TRIGGER trigger_check_username_duplicate
    BEFORE INSERT OR UPDATE ON pengguna
    FOR EACH ROW
    EXECUTE FUNCTION prevent_duplicate_username();

-- STORED PROCEDURE: Verify Login Credentials
CREATE OR REPLACE FUNCTION verify_login_credentials(p_email VARCHAR(100), p_password VARCHAR(50))
RETURNS TABLE(
    result_status TEXT,
    result_message TEXT,
    user_data JSON
) AS $$
DECLARE
    user_record RECORD;
    user_role TEXT;
BEGIN
    -- Check if user exists with given email
    SELECT p.*, 
           CASE 
               WHEN EXISTS (SELECT 1 FROM pengunjung WHERE username_p = p.username) THEN 'pengunjung'
               WHEN EXISTS (SELECT 1 FROM dokter_hewan WHERE username_dh = p.username) THEN 'dokter_hewan'
               WHEN EXISTS (SELECT 1 FROM penjaga_hewan WHERE username_jh = p.username) THEN 'penjaga_hewan'
               WHEN EXISTS (SELECT 1 FROM pelatih_hewan WHERE username_lh = p.username) THEN 'pelatih_hewan'
               WHEN EXISTS (SELECT 1 FROM staf_admin WHERE username_sa = p.username) THEN 'staf_admin'
               ELSE 'incomplete_registration'
           END as role
    INTO user_record
    FROM pengguna p 
    WHERE p.email = p_email;
    
    -- If user not found
    IF NOT FOUND THEN
        RETURN QUERY SELECT 
            'ERROR'::TEXT,
            'Username atau password salah, silakan coba lagi.'::TEXT,
            NULL::JSON;
        RETURN;
    END IF;
    
    -- If user has incomplete registration
    IF user_record.role = 'incomplete_registration' THEN
        RETURN QUERY SELECT 
            'ERROR'::TEXT,
            'Registrasi Anda belum lengkap. Silakan hubungi administrator.'::TEXT,
            NULL::JSON;
        RETURN;
    END IF;
    
    -- Verify password
    IF user_record.password = p_password THEN
        -- Login successful
        RETURN QUERY SELECT 
            'SUCCESS'::TEXT,
            'Login berhasil.'::TEXT,
            row_to_json(user_record)::JSON;
    ELSE
        -- Wrong password
        RETURN QUERY SELECT 
            'ERROR'::TEXT,
            'Username atau password salah, silakan coba lagi.'::TEXT,
            NULL::JSON;
    END IF;
    
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- TRIGGER FUNCTION: Log Registration Activity
CREATE OR REPLACE FUNCTION log_registration_activity()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert log entry for new user registration
    INSERT INTO activity_log (
        username, 
        activity_type, 
        activity_description, 
        timestamp
    ) VALUES (
        NEW.username,
        'REGISTRATION',
        'New user registered with email: ' || NEW.email,
        NOW()
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create activity_log table 
CREATE TABLE IF NOT EXISTS activity_log (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50),
    activity_type VARCHAR(50),
    activity_description TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- TRIGGER: Log registration activity
DROP TRIGGER IF EXISTS trigger_log_registration ON pengguna;
CREATE TRIGGER trigger_log_registration
    AFTER INSERT ON pengguna
    FOR EACH ROW
    EXECUTE FUNCTION log_registration_activity();

-- STORED PROCEDURE: Complete Registration Validation
CREATE OR REPLACE FUNCTION validate_complete_registration(
    p_username VARCHAR(50),
    p_email VARCHAR(100),
    p_role VARCHAR(20)
)
RETURNS TEXT AS $$
DECLARE
    role_exists BOOLEAN := FALSE;
BEGIN
    -- Check if username already exists
    IF EXISTS (SELECT 1 FROM pengguna WHERE username = p_username) THEN
        RETURN 'ERROR: Username "' || p_username || '" sudah digunakan, silakan pilih username lain.';
    END IF;
    
    -- Check if email already exists
    IF EXISTS (SELECT 1 FROM pengguna WHERE email = p_email) THEN
        RETURN 'ERROR: Email "' || p_email || '" sudah digunakan, silakan pilih email lain.';
    END IF;
    
    -- Additional role-specific validations can be added here
    CASE p_role
        WHEN 'dokter_hewan' THEN
            -- Future: Add STR number validation
            NULL;
        WHEN 'pengunjung' THEN
            -- Future: Add visitor-specific validation
            NULL;
        WHEN 'penjaga_hewan', 'pelatih_hewan', 'staf_admin' THEN
            -- Future: Add staff-specific validation
            NULL;
        ELSE
            RETURN 'ERROR: Role tidak valid.';
    END CASE;
    
    RETURN 'SUCCESS: Validation passed.';
END;
$$ LANGUAGE plpgsql;

-- FUNCTION: Get User Role Information
CREATE OR REPLACE FUNCTION get_user_role_info(p_username VARCHAR(50))
RETURNS TABLE(
    username VARCHAR(50),
    role VARCHAR(20),
    role_table VARCHAR(50),
    additional_info JSON
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.username,
        CASE 
            WHEN EXISTS (SELECT 1 FROM pengunjung WHERE username_p = p.username) THEN 'pengunjung'::VARCHAR(20)
            WHEN EXISTS (SELECT 1 FROM dokter_hewan WHERE username_dh = p.username) THEN 'dokter_hewan'::VARCHAR(20)
            WHEN EXISTS (SELECT 1 FROM penjaga_hewan WHERE username_jh = p.username) THEN 'penjaga_hewan'::VARCHAR(20)
            WHEN EXISTS (SELECT 1 FROM pelatih_hewan WHERE username_lh = p.username) THEN 'pelatih_hewan'::VARCHAR(20)
            WHEN EXISTS (SELECT 1 FROM staf_admin WHERE username_sa = p.username) THEN 'staf_admin'::VARCHAR(20)
            ELSE 'incomplete_registration'::VARCHAR(20)
        END as user_role,
        CASE 
            WHEN EXISTS (SELECT 1 FROM pengunjung WHERE username_p = p.username) THEN 'pengunjung'::VARCHAR(50)
            WHEN EXISTS (SELECT 1 FROM dokter_hewan WHERE username_dh = p.username) THEN 'dokter_hewan'::VARCHAR(50)
            WHEN EXISTS (SELECT 1 FROM penjaga_hewan WHERE username_jh = p.username) THEN 'penjaga_hewan'::VARCHAR(50)
            WHEN EXISTS (SELECT 1 FROM pelatih_hewan WHERE username_lh = p.username) THEN 'pelatih_hewan'::VARCHAR(50)
            WHEN EXISTS (SELECT 1 FROM staf_admin WHERE username_sa = p.username) THEN 'staf_admin'::VARCHAR(50)
            ELSE 'none'::VARCHAR(50)
        END as table_name,
        '{}'::JSON as info
    FROM pengguna p 
    WHERE p.username = p_username;
END;
$$ LANGUAGE plpgsql;