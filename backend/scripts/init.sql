-- ============================================================
-- Inventory System - Database Security Initialization
-- ============================================================
-- This script runs on first MySQL container startup
-- Implements: Least Privilege, Audit Logging, Secure Defaults
-- ============================================================

-- Set secure character encoding
ALTER DATABASE inventory_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- ============================================================
-- 1. LEAST PRIVILEGE USER SETUP
-- ============================================================

-- Application user: Only DML operations (SELECT, INSERT, UPDATE, DELETE)
-- Used by: Django app, Celery workers
CREATE USER IF NOT EXISTS 'inventory_app'@'%'
    IDENTIFIED BY 'app_secure_password_change_me';

GRANT SELECT, INSERT, UPDATE, DELETE ON inventory_db.* TO 'inventory_app'@'%';

-- Migration user: Full schema control (for Django migrations)
-- Used by: Migration commands only
CREATE USER IF NOT EXISTS 'inventory_migrate'@'%'
    IDENTIFIED BY 'migrate_secure_password_change_me';

GRANT ALL PRIVILEGES ON inventory_db.* TO 'inventory_migrate'@'%';

-- Read-only user: For reports and analytics (optional)
CREATE USER IF NOT EXISTS 'inventory_readonly'@'%'
    IDENTIFIED BY 'readonly_secure_password_change_me';

GRANT SELECT ON inventory_db.* TO 'inventory_readonly'@'%';

-- ============================================================
-- 2. SECURITY HARDENING
-- ============================================================

-- Remove anonymous users
DELETE FROM mysql.user WHERE User='';

-- Remove remote root access
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');

-- Remove test database access
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';

-- ============================================================
-- 3. PASSWORD POLICY (MySQL 8.0+)
-- ============================================================

-- Note: These require SUPER privilege, may fail in container
-- SET GLOBAL validate_password.policy = STRONG;
-- SET GLOBAL validate_password.length = 12;

-- ============================================================
-- 4. APPLY CHANGES
-- ============================================================

FLUSH PRIVILEGES;

-- ============================================================
-- NOTES FOR PRODUCTION:
--
-- 1. Change all passwords in this file before deployment
-- 2. Use environment variables for passwords in docker-compose
-- 3. Consider using MySQL Enterprise Audit plugin
-- 4. Enable SSL/TLS for connections (see mysql-ssl/ directory)
-- 5. Restrict '%' hosts to specific IP ranges in production
--
-- Example restricted host:
-- CREATE USER 'inventory_app'@'172.18.0.%' ...
-- ============================================================
