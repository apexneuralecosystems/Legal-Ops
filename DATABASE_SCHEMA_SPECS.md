# Legal Ops AI — Database Schema Specifications
## Complete Table Definitions

**Version**: 2.1  
**Date**: 29 January 2026

---

## Table of Contents

1. [Core Multi-Tenant Tables](#1-core-multi-tenant-tables)
2. [RBAC Tables](#2-rbac-tables)
3. [Client & Matter Tables](#3-client--matter-tables)
4. [Document & Content Tables](#4-document--content-tables)
5. [Billing & Time Tables](#5-billing--time-tables)
6. [Invoice Tables](#6-invoice-tables)
7. [Ledger Tables](#7-ledger-tables)
8. [Audit & Payment Tables](#8-audit--payment-tables)
9. [OCR & Document Processing Tables](#9-ocr--document-processing-tables)

---

## 9. OCR & Document Processing Tables

### ocr_documents

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PK | UUID v4 |
| matter_id | VARCHAR | FK→matters | |
| filename | VARCHAR(512) | NOT NULL | |
| file_path | VARCHAR(1024) | | S3/local path |
| file_hash | VARCHAR(64) | UNIQUE, NOT NULL | SHA-256 |
| file_size_bytes | INTEGER | | |
| mime_type | VARCHAR(100) | DEFAULT 'application/pdf' | |
| total_pages | INTEGER | | |
| ocr_status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | pending/processing/completed/failed |
| ocr_started_at | TIMESTAMP | | |
| ocr_completed_at | TIMESTAMP | | |
| ocr_engine | VARCHAR(50) | DEFAULT 'google_vision' | |
| extracted_metadata | JSON | DEFAULT {} | |
| primary_language | VARCHAR(10) | | |
| created_at | TIMESTAMP | DEFAULT NOW() | |
| created_by | VARCHAR(36) | | |

**Indexes**: `file_hash`

### ocr_pages

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PK | UUID v4 |
| document_id | VARCHAR(36) | FK→ocr_documents, NOT NULL | |
| page_number | INTEGER | NOT NULL | |
| raw_text | TEXT | NOT NULL | |
| cleaned_text | TEXT | | |
| bounding_boxes | JSON | | |
| blocks_json | JSON | | |
| ocr_confidence | FLOAT | | |
| word_count | INTEGER | | |
| char_count | INTEGER | | |
| is_header_page | BOOLEAN | DEFAULT FALSE | |
| is_blank | BOOLEAN | DEFAULT FALSE | |
| has_tables | BOOLEAN | DEFAULT FALSE | |
| has_signatures | BOOLEAN | DEFAULT FALSE | |
| detected_headers | JSON | DEFAULT [] | |
| detected_footers | JSON | DEFAULT [] | |
| created_at | TIMESTAMP | DEFAULT NOW() | |

**Indexes**: `document_id`

### ocr_chunks

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PK | UUID v4 |
| document_id | VARCHAR(36) | FK→ocr_documents, NOT NULL | |
| chunk_sequence | INTEGER | NOT NULL | |
| chunk_id_str | VARCHAR(100) | | |
| chunk_text | TEXT | NOT NULL | |
| token_count | INTEGER | NOT NULL | |
| source_page_start | INTEGER | NOT NULL | |
| source_page_end | INTEGER | NOT NULL | |
| source_char_start | INTEGER | | |
| source_char_end | INTEGER | | |
| language | VARCHAR(10) | DEFAULT 'en' | |
| chunk_type | VARCHAR(50) | | |
| section_ref | VARCHAR(100) | | |
| is_embeddable | BOOLEAN | DEFAULT TRUE | |
| embedding_model | VARCHAR(100) | | |
| embedded_at | TIMESTAMP | | |
| created_at | TIMESTAMP | DEFAULT NOW() | |

**Indexes**: `document_id`, `is_embeddable`

### ocr_processing_log

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PK | UUID v4 |
| document_id | VARCHAR(36) | FK→ocr_documents | |
| page_number | INTEGER | | |
| step_name | VARCHAR(100) | NOT NULL | |
| status | VARCHAR(20) | NOT NULL | |
| duration_ms | INTEGER | | |
| input_summary | TEXT | | |
| output_summary | TEXT | | |
| error_message | TEXT | | |
| created_at | TIMESTAMP | DEFAULT NOW() | |

**Indexes**: `document_id`

---

**End of Schema Specifications**

## 1. Core Multi-Tenant Tables

### organizations

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PK | UUID v4 |
| name | VARCHAR(255) | UNIQUE, NOT NULL | Full firm name |
| short_name | VARCHAR(50) | UNIQUE, NOT NULL | Abbreviation |
| business_reg_no | VARCHAR(50) | | SSM registration |
| sst_registration_no | VARCHAR(50) | | SST number |
| default_currency | VARCHAR(3) | DEFAULT 'MYR' | ISO currency |
| invoice_prefix | VARCHAR(10) | NOT NULL | e.g., 'INV' |
| invoice_counter | INTEGER | DEFAULT 0 | Next invoice number |
| is_active | BOOLEAN | DEFAULT TRUE | Soft active flag |
| created_at | TIMESTAMP | DEFAULT NOW() | |
| updated_at | TIMESTAMP | | |

### users (MODIFIED)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PK | UUID v4 |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Login email |
| password_hash | VARCHAR(255) | NOT NULL | Bcrypt hash |
| full_name | VARCHAR(255) | | Display name |
| username | VARCHAR(100) | UNIQUE | Optional username |
| is_active | BOOLEAN | DEFAULT TRUE | |
| is_superuser | BOOLEAN | DEFAULT FALSE | System admin |
| **last_used_organization_id** | VARCHAR(36) | FK→organizations | **NEW** |
| created_at | TIMESTAMP | DEFAULT NOW() | |
| updated_at | TIMESTAMP | | |
| deleted_at | TIMESTAMP | | Soft delete |

---

## 2. RBAC Tables

### permissions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PK | UUID v4 |
| code | VARCHAR(100) | UNIQUE, NOT NULL | e.g., 'invoices:approve' |
| name | VARCHAR(150) | NOT NULL | Human readable |
| description | TEXT | | Tooltip text |
| category | VARCHAR(50) | NOT NULL | matters/billing/trust/admin |
| is_sensitive | BOOLEAN | DEFAULT FALSE | Dangerous permission |
| created_at | TIMESTAMP | DEFAULT NOW() | |

**Indexes**: `code`

### roles

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PK | UUID v4 |
| organization_id | VARCHAR(36) | FK→organizations, NOT NULL | Owner org |
| code | VARCHAR(50) | NOT NULL | e.g., 'partner' |
| name | VARCHAR(100) | NOT NULL | Display name |
| description | TEXT | | |
| level | INTEGER | DEFAULT 100 | Lower = more senior |
| is_system_role | BOOLEAN | DEFAULT FALSE | Can't delete |
| created_at | TIMESTAMP | DEFAULT NOW() | |
| updated_at | TIMESTAMP | | |

**Unique**: (`organization_id`, `code`)  
**Indexes**: `organization_id`

### role_permissions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PK | UUID v4 |
| role_id | VARCHAR(36) | FK→roles, NOT NULL | |
| permission_id | VARCHAR(36) | FK→permissions, NOT NULL | |
| scope | VARCHAR(50) | DEFAULT 'all' | all/own/team/assigned |
| created_at | TIMESTAMP | DEFAULT NOW() | |

**Unique**: (`role_id`, `permission_id`)  
**Indexes**: `role_id`, `permission_id`

### memberships

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PK | UUID v4 |
| user_id | VARCHAR(36) | FK→users, NOT NULL | |
| organization_id | VARCHAR(36) | FK→organizations, NOT NULL | |
| role_id | VARCHAR(36) | FK→roles, NOT NULL | |
| status | VARCHAR(20) | DEFAULT 'active' | active/invited/suspended/left |
| joined_at | TIMESTAMP | DEFAULT NOW() | |
| left_at | TIMESTAMP | | |
| created_at | TIMESTAMP | DEFAULT NOW() | |
| updated_at | TIMESTAMP | | |

**Unique**: (`user_id`, `organization_id`)  
**Indexes**: `user_id`, `organization_id`, `role_id`

### membership_permission_overrides

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PK | UUID v4 |
| membership_id | VARCHAR(36) | FK→memberships, NOT NULL | |
| permission_id | VARCHAR(36) | FK→permissions, NOT NULL | |
| is_denied | BOOLEAN | DEFAULT FALSE | Grant (false) or Deny (true) |
| expires_at | TIMESTAMP | | Auto-expire |
| granted_by_id | VARCHAR(36) | FK→users | Who approved |
| reason | TEXT | | Justification |
| created_at | TIMESTAMP | DEFAULT NOW() | |

**Unique**: (`membership_id`, `permission_id`)  
**Indexes**: `membership_id`

### invites

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PK | UUID v4 |
| organization_id | VARCHAR(36) | FK→organizations, NOT NULL | |
| role_id | VARCHAR(36) | FK→roles, NOT NULL | Role on acceptance |
| email | VARCHAR(255) | NOT NULL | Invitee email |
| token | VARCHAR(100) | UNIQUE, NOT NULL | Secure random |
| status | VARCHAR(20) | DEFAULT 'pending' | pending/accepted/expired/revoked |
| invited_by_id | VARCHAR(36) | FK→users, NOT NULL | |
| expires_at | TIMESTAMP | NOT NULL | Default 7 days |
| accepted_at | TIMESTAMP | | |
| accepted_by_user_id | VARCHAR(36) | FK→users | |
| created_at | TIMESTAMP | DEFAULT NOW() | |

**Indexes**: `organization_id`, `email`, `token`

---

## 3. Client & Matter Tables

### clients

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PK | UUID v4 |
| organization_id | VARCHAR(36) | FK→organizations, NOT NULL | |
| name | VARCHAR(255) | NOT NULL | Client name |
| client_type | VARCHAR(30) | NOT NULL | individual/company |
| company_reg_no | VARCHAR(50) | | SSM number if company |
| sst_exempt | BOOLEAN | DEFAULT FALSE | SST exemption |
| tax_id | VARCHAR(50) | | Tax ID |
| email | VARCHAR(255) | | Contact email |
| phone | VARCHAR(50) | | Contact phone |
| address | TEXT | | Billing address |
| created_at | TIMESTAMP | DEFAULT NOW() | |
| created_by_id | VARCHAR(36) | FK→users | |

**Indexes**: `organization_id`, `name`

### matters (MODIFIED)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR | PK | UUID v4 |
| **organization_id** | VARCHAR(36) | FK→organizations, NOT NULL | **NEW** |
| **client_id** | VARCHAR(36) | FK→clients | **NEW** |
| title | VARCHAR(500) | NOT NULL | Matter title |
| matter_type | VARCHAR(50) | | e.g., litigation, advisory |
| status | VARCHAR(50) | DEFAULT 'intake' | |
| court | VARCHAR(200) | | Court name |
| jurisdiction | VARCHAR(100) | | |
| primary_language | VARCHAR(10) | | en/ms |
| parties | JSON | | Involved parties |
| key_dates | JSON | | Important dates |
| issues | JSON | | Legal issues |
| requested_remedies | JSON | | |
| **unbilled_ai_amount_myr** | NUMERIC(12,2) | DEFAULT 0 | **NEW** Running WIP |
| **total_billed_amount_myr** | NUMERIC(12,2) | DEFAULT 0 | **NEW** Historical |
| created_at | TIMESTAMP | DEFAULT NOW() | |
| updated_at | TIMESTAMP | | |
| created_by | VARCHAR(36) | FK→users | |

**Indexes**: `organization_id`, `client_id`, `status`

---

## 4. Document & Content Tables

### documents (MODIFIED)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR | PK | UUID v4 |
| **organization_id** | VARCHAR(36) | FK→organizations | **NEW** |
| matter_id | VARCHAR | FK→matters | |
| filename | VARCHAR(512) | NOT NULL | |
| original_filename | VARCHAR(512) | | |
| mime_type | VARCHAR(100) | | |
| file_path | VARCHAR(1024) | | S3/local path |
| file_size | INTEGER | | Bytes |
| source | VARCHAR(50) | | upload/email/scan |
| ocr_needed | BOOLEAN | DEFAULT FALSE | |
| ocr_completed | BOOLEAN | DEFAULT FALSE | |
| ocr_confidence | INTEGER | | 0-100 |
| file_hash | VARCHAR(64) | | SHA-256 |
| is_duplicate | BOOLEAN | DEFAULT FALSE | |
| created_at | TIMESTAMP | DEFAULT NOW() | |
| processed_at | TIMESTAMP | | |

**Indexes**: `organization_id`, `matter_id`

### segments (EXISTING - No changes)

### pleadings (EXISTING - No changes)

### research_cases (EXISTING - No changes)

---

## 5. Billing & Time Tables

### rates

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PK | UUID v4 |
| organization_id | VARCHAR(36) | FK→organizations, NOT NULL | |
| user_id | VARCHAR(36) | FK→users | Specific user rate |
| role | VARCHAR(50) | | Or role-based rate |
| hourly_rate_myr | NUMERIC(12,2) | NOT NULL | MYR per hour |
| effective_from | DATE | NOT NULL | |
| effective_to | DATE | | NULL = current |
| created_at | TIMESTAMP | DEFAULT NOW() | |
| created_by_id | VARCHAR(36) | FK→users | |

**Indexes**: `organization_id`, `user_id`, `effective_from`

### time_entries

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PK | UUID v4 |
| matter_id | VARCHAR | FK→matters, NOT NULL | |
| user_id | VARCHAR(36) | FK→users, NOT NULL | Who worked |
| rate_id | VARCHAR(36) | FK→rates, NOT NULL | Rate snapshot |
| description | TEXT | NOT NULL | Work description |
| minutes | INTEGER | NOT NULL | Duration |
| work_date | DATE | NOT NULL | |
| status | VARCHAR(30) | DEFAULT 'draft' | draft/submitted/approved/billed |
| approved_by_id | VARCHAR(36) | FK→users | |
| approved_at | TIMESTAMP | | |
| created_at | TIMESTAMP | DEFAULT NOW() | |

**Indexes**: `matter_id`, `user_id`, `status`, `work_date`

### expenses

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PK | UUID v4 |
| matter_id | VARCHAR | FK→matters, NOT NULL | |
| description | TEXT | NOT NULL | |
| amount_myr | NUMERIC(12,2) | NOT NULL | |
| is_disbursement | BOOLEAN | DEFAULT FALSE | Court fees, etc. |
| is_rechargeable | BOOLEAN | DEFAULT TRUE | Bill to client |
| expense_date | DATE | NOT NULL | |
| status | VARCHAR(30) | DEFAULT 'pending' | pending/approved/billed |
| created_at | TIMESTAMP | DEFAULT NOW() | |
| created_by_id | VARCHAR(36) | FK→users | |

**Indexes**: `matter_id`, `status`

### ai_usage_logs

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PK | UUID v4 |
| organization_id | VARCHAR(36) | FK→organizations, NOT NULL | |
| matter_id | VARCHAR | FK→matters, NOT NULL | |
| user_id | VARCHAR(36) | FK→users, NOT NULL | |
| membership_id | VARCHAR(36) | FK→memberships | |
| feature_type | VARCHAR(50) | NOT NULL | ocr/research/drafting/etc. |
| feature_details | JSON | | Request params |
| started_at | TIMESTAMP | NOT NULL | |
| completed_at | TIMESTAMP | | |
| duration_seconds | INTEGER | | |
| tokens_input | INTEGER | | LLM input |
| tokens_output | INTEGER | | LLM output |
| pages_processed | INTEGER | | OCR pages |
| rate_id | VARCHAR(36) | FK→rates, NOT NULL | Rate snapshot |
| raw_minutes | INTEGER | | Calculated time |
| billable_units | NUMERIC(4,1) | | 0.1 hr increments |
| unit_rate_myr | NUMERIC(12,2) | | Hourly rate |
| amount_myr | NUMERIC(12,2) | | Total charge |
| status | VARCHAR(30) | DEFAULT 'unbilled' | unbilled/in_prebill/billed/written_off |
| invoice_line_id | VARCHAR(36) | FK→invoice_lines | |
| written_off_by_id | VARCHAR(36) | FK→users | |
| written_off_reason | TEXT | | |
| created_at | TIMESTAMP | DEFAULT NOW() | |

**Indexes**: `organization_id`, `matter_id`, `user_id`, `status`, `created_at`

---

## 6. Invoice Tables

### invoices

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PK | UUID v4 |
| organization_id | VARCHAR(36) | FK→organizations, NOT NULL | |
| matter_id | VARCHAR | FK→matters | |
| client_id | VARCHAR(36) | FK→clients, NOT NULL | |
| invoice_number | VARCHAR(50) | UNIQUE, NOT NULL | Sequential |
| issue_date | DATE | NOT NULL | |
| due_date | DATE | NOT NULL | |
| subtotal_myr | NUMERIC(12,2) | NOT NULL | Before tax |
| sst_rate | NUMERIC(5,2) | DEFAULT 0.06 | 6% |
| sst_amount_myr | NUMERIC(12,2) | NOT NULL | Tax amount |
| total_myr | NUMERIC(12,2) | NOT NULL | Final total |
| status | VARCHAR(30) | DEFAULT 'draft' | draft/approved/issued/paid/void |
| notes | TEXT | | |
| created_by_id | VARCHAR(36) | FK→users | |
| approved_by_id | VARCHAR(36) | FK→users | Partner |
| issued_at | TIMESTAMP | | When finalized |
| immutable | BOOLEAN | DEFAULT FALSE | Lock after issue |
| created_at | TIMESTAMP | DEFAULT NOW() | |

**Indexes**: `organization_id`, `client_id`, `matter_id`, `status`, `invoice_number`

### invoice_lines

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PK | UUID v4 |
| invoice_id | VARCHAR(36) | FK→invoices, NOT NULL | |
| description | TEXT | NOT NULL | Line description |
| quantity | NUMERIC(10,2) | NOT NULL | Hours/units |
| unit_price_myr | NUMERIC(12,2) | NOT NULL | Rate |
| amount_myr | NUMERIC(12,2) | NOT NULL | Line total |
| source_type | VARCHAR(30) | | time_entry/expense/ai_usage |
| source_id | VARCHAR(36) | | FK to source |
| created_at | TIMESTAMP | DEFAULT NOW() | |

**Indexes**: `invoice_id`

---

## 7. Ledger Tables

### ledger_accounts

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PK | UUID v4 |
| organization_id | VARCHAR(36) | FK→organizations, NOT NULL | |
| code | VARCHAR(20) | NOT NULL | Account code |
| name | VARCHAR(100) | NOT NULL | Account name |
| account_type | VARCHAR(40) | NOT NULL | See below |
| client_id | VARCHAR(36) | FK→clients | For client ledgers |
| matter_id | VARCHAR | FK→matters | For matter ledgers |
| current_balance_myr | NUMERIC(14,2) | DEFAULT 0 | Running balance |
| created_at | TIMESTAMP | DEFAULT NOW() | |

**Account Types**:
- `trust_client_ledger` — Individual client trust
- `trust_control` — Trust control account
- `bank_trust` — Trust bank account
- `bank_office` — Office bank account
- `office_revenue` — Revenue account
- `office_ar` — Accounts receivable
- `sst_payable` — SST liability

**Unique**: (`organization_id`, `code`)  
**Indexes**: `organization_id`, `account_type`, `client_id`

### ledger_transactions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PK | UUID v4 |
| organization_id | VARCHAR(36) | FK→organizations, NOT NULL | |
| debit_account_id | VARCHAR(36) | FK→ledger_accounts, NOT NULL | |
| credit_account_id | VARCHAR(36) | FK→ledger_accounts, NOT NULL | |
| invoice_id | VARCHAR(36) | FK→invoices | Related invoice |
| matter_id | VARCHAR | FK→matters | |
| amount_myr | NUMERIC(14,2) | NOT NULL | Must be positive |
| transaction_date | DATE | NOT NULL | |
| description | TEXT | NOT NULL | |
| created_by_id | VARCHAR(36) | FK→users | |
| created_at | TIMESTAMP | DEFAULT NOW() | |

**Indexes**: `organization_id`, `debit_account_id`, `credit_account_id`, `transaction_date`

---

## 8. Audit & Payment Tables

### audit_logs (MODIFIED)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PK | UUID v4 |
| **organization_id** | VARCHAR(36) | FK→organizations | **NEW** |
| **membership_id** | VARCHAR(36) | FK→memberships | **NEW** |
| matter_id | VARCHAR | FK→matters | |
| agent_id | VARCHAR(50) | | AI agent ID |
| action_type | VARCHAR(50) | NOT NULL | create/update/delete |
| action_description | TEXT | | |
| version_tag | VARCHAR(50) | | |
| entity_type | VARCHAR(50) | | Table name |
| entity_id | VARCHAR(36) | | Row ID |
| changes | JSON | | Old → new values |
| human_reviewed | BOOLEAN | DEFAULT FALSE | |
| reviewer_id | VARCHAR(36) | FK→users | |
| review_timestamp | TIMESTAMP | | |
| timestamp_utc | TIMESTAMP | DEFAULT NOW() | |
| user_id | VARCHAR(36) | FK→users | |
| ip_address | VARCHAR(45) | | IPv4/v6 |

**Indexes**: `organization_id`, `entity_type`, `entity_id`, `timestamp_utc`

### subscriptions (EXISTING - No changes)

### payment_orders (EXISTING - No changes)

### user_usage (EXISTING - No changes)

---

## Migration Strategy

### Phase 1: Add nullable columns
```sql
ALTER TABLE users ADD COLUMN last_used_organization_id VARCHAR(36);
ALTER TABLE matters ADD COLUMN organization_id VARCHAR(36);
ALTER TABLE matters ADD COLUMN client_id VARCHAR(36);
ALTER TABLE documents ADD COLUMN organization_id VARCHAR(36);
ALTER TABLE audit_logs ADD COLUMN organization_id VARCHAR(36);
```

### Phase 2: Create new tables
Run Alembic migration with all new table definitions.

### Phase 3: Migrate existing data
```sql
-- Create default organization
INSERT INTO organizations (id, name, ...) VALUES ('default-org-id', 'Default Firm', ...);

-- Assign all existing matters
UPDATE matters SET organization_id = 'default-org-id';

-- Create default roles
INSERT INTO roles (...) VALUES (...);

-- Create memberships for existing users
INSERT INTO memberships (user_id, organization_id, role_id, ...)
SELECT id, 'default-org-id', 'partner-role-id', ...
FROM users;
```

### Phase 4: Add NOT NULL constraints
```sql
ALTER TABLE matters ALTER COLUMN organization_id SET NOT NULL;
```

---

**End of Schema Specifications**
