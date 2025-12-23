# Demo Legal Case Documents

This folder contains sample legal case documents for testing the Malaysian Legal AI Agent system.

## Available Test Cases

### 1. Employment Breach Case
**File**: `employment_breach_case.txt`
- **Type**: Employment contract dispute
- **Language**: English
- **Claim Amount**: RM 189,000
- **Issues**: Notice period breach, non-compete violation, confidential info misappropriation
- **Complexity**: Medium
- **Good for testing**: Intake workflow, Issue planning, Drafting

### 2. Property Contract Breach (Malay)
**File**: `property_contract_breach_malay.txt`
- **Type**: Land sale contract dispute
- **Language**: Bahasa Malaysia
- **Claim Amount**: RM 1,955,000
- **Issues**: Non-payment, contract breach, penalty claims
- **Complexity**: Medium-High
- **Good for testing**: Translation workflow, Malay processing, Bilingual features

### 3. Supplier Dispute
**File**: `supplier_dispute.txt`
- **Type**: Supply agreement breach
- **Language**: English
- **Claim Amount**: RM 593,000
- **Issues**: Delivery failures, quality issues, consequential damages
- **Complexity**: Low-Medium
- **Good for testing**: Quick intake, Basic drafting

### 4. Loan Default Case
**File**: `loan_default_case.txt`
- **Type**: Banking & finance recovery
- **Language**: English
- **Claim Amount**: RM 90,300
- **Issues**: Loan default, recovery action, secured lending
- **Complexity**: Medium
- **Good for testing**: Research workflow (banking cases), Evidence preparation

## How to Use These Cases

### Option 1: Upload via Web UI (Recommended)
1. Open http://localhost:8006
2. Click "Upload Documents"
3. Select one or more demo files
4. Choose "File Upload" as source type
5. Click "Start Intake Workflow"
6. Watch the AI process the case!

### Option 2: Test Different Workflows

**Test Intake Workflow:**
- Upload any of the demo files
- System will extract parties, issues, dates, amounts
- Creates a matter card with risk assessment

**Test Translation:**
- Upload `property_contract_breach_malay.txt`
- System detects Malay language
- Translates to English automatically

**Test Drafting:**
- First complete intake with any case
- Go to Drafting page
- Select the created matter
- Generate bilingual pleadings

**Test Research:**
- Go to Research page
- Search: "contract breach Malaysia"
- or "employment termination"
- or "loan default banking"
- Get relevant Malaysian cases

## Expected Results

For each case, the system should:
- ✅ Extract party names correctly
- ✅ Identify legal issues (breach of contract, etc.)
- ✅ Calculate claim amounts
- ✅ Detect dates and timelines
- ✅ Assign appropriate risk scores
- ✅ Suggest relevant Malaysian statutes
- ✅ Create bilingual matter summaries

## Tips for Testing

1. **Start Simple**: Use `supplier_dispute.txt` first (shortest file)
2. **Test Translation**: Use `property_contract_breach_malay.txt`
3. **Test Complex**: Use `employment_breach_case.txt` (most detailed)
4. **Mix Languages**: Upload both English and Malay files together

## What to Look For

- Matter card creation with correct details
- Risk scores (should be medium-high for larger claims)
- Proper bilingual headings
- Suggested legal bases (Contract Act 1950, etc.)
- Realistic timeline and deadlines

---

**Note**: These are fictional cases created for testing purposes only.
