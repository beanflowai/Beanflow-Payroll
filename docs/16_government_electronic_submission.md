# Government Electronic Submission Guide

## Overview

This document provides comprehensive information about electronic submission methods for Canadian payroll compliance documents to government agencies (CRA and Service Canada).

### Summary of Submission Methods

| Document | Agency | System | Format | Deadline |
|----------|--------|--------|--------|----------|
| **T4/T4A** | CRA | Internet File Transfer | XML (T619) | Feb 28 following tax year |
| **T4 Summary** | CRA | Internet File Transfer | XML (T619) | Feb 28 following tax year |
| **ROE** | Service Canada | ROE Web | XML (Payroll Extract) | 5 days after interruption |
| **Remittance** | CRA | My Business Account | Online Payment | 15th of following month |
| **PD7A** | CRA | Manual/Online | PDF/Online | With remittance |

---

## 1. T4/T4A Submission to CRA

### 1.1 Electronic Filing Methods

CRA provides three methods for T4 electronic submission:

#### Method 1: Internet File Transfer (XML) - Recommended

**Official Portal**: https://www.canada.ca/en/revenue-agency/services/e-services/filing-information-returns-electronically-t4-t5-other-types-returns-overview/filing-information-returns-electronically-t4-t5-other-types-returns-file/filing-internet-file-transfer.html

**Requirements**:
- Valid payroll account number (format: `123456789RP0001`)
- Web Access Code (WAC) from CRA
- XML file following T619 schema (max 150 MB)

**Process**:
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Payroll System  │ ──► │ Generate XML    │ ──► │ CRA Internet    │
│ (Beanflow)      │     │ (T619 format)   │     │ File Transfer   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Confirmation    │
                                                │ Number Received │
                                                └─────────────────┘
```

#### Method 2: Web Forms (Manual Entry)

**Official Portal**: https://www.canada.ca/en/revenue-agency/services/e-services/filing-information-returns-electronically-t4-t5-other-types-returns-overview/filing-information-returns-electronically-t4-t5-other-types-returns-file/filing-web-forms.html

**Best for**: Small businesses with < 5 slips

**Features**:
- Free, secured application
- Creates XML automatically
- Can file, amend, or cancel returns

#### Method 3: My Business Account

**Official Portal**: https://www.canada.ca/en/revenue-agency/services/e-services/e-services-businesses/business-account.html

**Features**:
- Upload XML files directly
- View submission history
- Manage payroll account

### 1.2 T619 XML Schema (2025)

**Schema Download**: https://www.canada.ca/en/revenue-agency/services/e-services/filing-information-returns-electronically-t4-t5-other-types-returns-overview/filing-information-returns-electronically-t4-t5-other-types-returns-file/filing-internet-file-transfer/download-xml-schema.html

**Current Version**: xmlschm1-25-4.zip (version 1-25-4, updated December 10, 2024)

**Key 2025 Changes**:
1. **Single return type per submission**: Each submission can only contain one type of information return (e.g., only T4 or only T5)
2. **Updated T619 Electronic Transmittal record**: New format required starting January 2025
3. **T619 files replaced**: `layout-topologies.xsd` replaced by `T619_<FormType>.xsd` files

**XML Structure Example**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Return xmlns="http://www.cra-arc.gc.ca/xmlns/t4"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <T619>
    <!-- Electronic Transmittal Record -->
    <SummaryCount>1</SummaryCount>
    <LanguageCode>E</LanguageCode>
    <TransmitterNumber>MM123456</TransmitterNumber>
    <TransmitterName>Company Name</TransmitterName>
    <TransmitterAddress>...</TransmitterAddress>
    <ContactName>...</ContactName>
    <ContactPhone>...</ContactPhone>
    <ContactEmail>...</ContactEmail>
  </T619>
  <T4>
    <TaxationYear>2025</TaxationYear>
    <Summary>...</Summary>
    <Slips>
      <Slip>...</Slip>
    </Slips>
  </T4>
</Return>
```

### 1.3 Electronic Filing Threshold

**As of January 2024**:
- **> 5 slips**: Must file electronically
- **≤ 5 slips**: Can file paper or electronic

**Penalties for non-compliance**: Calculated per slip for incorrect format

### 1.4 System Maintenance Schedule

- **December 22, 2025**: Electronic filing unavailable (maintenance)
- **January 12, 2026**: System reopens with 2026 version

### 1.5 Commercial Payroll Software Integration

Major payroll providers handle T4 submission as follows:

| Provider | Method | Automation Level |
|----------|--------|------------------|
| **Wagepoint** | Auto-submit via WAC | Fully automated |
| **ADP** | Auto-generate + submit | Requires Enhanced+ plan |
| **Ceridian Dayforce** | Auto-generate + submit | Enterprise tier |
| **QuickBooks** | Generate XML, manual upload | Semi-automated |

**How they achieve "automatic" submission**:
1. User provides CRA credentials/WAC during setup
2. Software generates compliant XML
3. Software submits on behalf of user via CRA APIs
4. Returns confirmation to user

---

## 2. ROE Submission to Service Canada

### 2.1 ROE Web System

**Official Portal**: https://www.canada.ca/en/employment-social-development/programs/ei/ei-list/ei-roe/access-roe.html

**ROE User Guide**: https://www.canada.ca/en/employment-social-development/programs/ei/ei-list/reports/completing-single-roe.html

### 2.2 Submission Methods

#### Method 1: ROE Web Online Form (Manual)

- Login via GCKey or Sign-In Partner
- Fill form manually
- Best for occasional ROEs

#### Method 2: Payroll Extract (XML Batch Upload) - Recommended

**Payroll Extract Guide**: https://www.canada.ca/en/employment-social-development/programs/ei/ei-list/reports/payroll-extract.html

**Features**:
- Upload up to **1,200 ROEs** at once
- Upload up to **10 files** simultaneously
- File format: XML with `.BLK` extension

**Process**:
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Payroll System  │ ──► │ Generate XML    │ ──► │ ROE Web         │
│ Export ROE data │     │ (.BLK file)     │     │ Payroll Extract │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
                                              ┌──────────────────────┐
                                              │ Status Tracking:     │
                                              │ Received → Processing│
                                              │ → Completed/Invalid  │
                                              └──────────────────────┘
```

#### Method 3: ROE Web Assistant

- Guided completion for users unfamiliar with ROE
- Enhanced help and plain language
- Same validation as online form

### 2.3 ROE XML Schema

**Schema Documentation**: https://www.canada.ca/en/employment-social-development/programs/ei/ei-list/ei-roe/user-requirements/functional.html

**Appendix E (Technical Specs)**: https://www.canada.ca/en/employment-social-development/programs/ei/ei-list/ei-roe/user-requirements/appendix-e.html

**XML Structure**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<ROEHEADER version="2.0"
           transmitterNumber="123456789RP0001"
           transmitterName="Company Name"
           contactName="John Doe"
           contactPhone="4165551234">
  <ROE>
    <SIN>123456789</SIN>
    <EMPLOYEE_FIRST_NAME>Jane</EMPLOYEE_FIRST_NAME>
    <EMPLOYEE_LAST_NAME>Smith</EMPLOYEE_LAST_NAME>
    <EMPLOYEE_ADDRESS>...</EMPLOYEE_ADDRESS>
    <FIRST_DAY_WORKED>2023-01-15</FIRST_DAY_WORKED>
    <LAST_DAY_PAID>2025-03-31</LAST_DAY_PAID>
    <FINAL_PAY_PERIOD_END_DATE>2025-04-15</FINAL_PAY_PERIOD_END_DATE>
    <PAY_PERIOD_TYPE>B</PAY_PERIOD_TYPE> <!-- B=Bi-weekly -->
    <REASON_FOR_ISSUING>A</REASON_FOR_ISSUING>
    <TOTAL_INSURABLE_HOURS>2080</TOTAL_INSURABLE_HOURS>
    <INSURABLE_EARNINGS>
      <PERIOD number="1">2500.00</PERIOD>
      <PERIOD number="2">2500.00</PERIOD>
      <!-- Up to 53 periods for weekly, 27 for bi-weekly -->
    </INSURABLE_EARNINGS>
    <VACATION_PAY>1200.00</VACATION_PAY>
  </ROE>
</ROEHEADER>
```

### 2.4 Testing Environment

**ROE Web Demo Site**: Available for testing payroll extract files

**Validation Process**:
1. Generate XML using ROE Web schema (XSD)
2. Validate locally using XSD validator
3. Upload to demo site for testing
4. Review validation results
5. Submit to production when ready

### 2.5 Status Tracking

After upload, track status in ROE Web:

| Status | Description |
|--------|-------------|
| **Received** | File received, waiting to be processed |
| **Processing** | File being validated |
| **Process Completed** | Available under View |
| **Invalid File** | Format invalid, needs correction |

### 2.6 Handling Rejected ROEs

**Options for "Failed" ROEs**:
1. Select and fix individually via Online Form
2. Correct in payroll software and re-upload XML with only corrected ROEs

### 2.7 Import Feature

**Purpose**: Extract ROE Serial Numbers back into payroll software

**Use Cases**:
- Reference for issued ROEs
- Required for issuing amended ROEs
- Record keeping

### 2.8 Registration Requirements

**Primary Officer Validation**:
1. Sign in via GCKey or Sign-In Partner
2. Validate identity:
   - Online via CRA account, OR
   - In person at Service Canada Centre (photo ID required)

---

## 3. Remittance to CRA

### 3.1 Payment Methods

| Method | Description | Best For |
|--------|-------------|----------|
| **My Payment** | Online through CRA My Business Account | All employers |
| **Pre-Authorized Debit** | Automatic debit from bank account | Regular remitters |
| **Wire Transfer** | Bank wire to CRA | Large amounts |
| **Cheque + PD7A** | Mail cheque with voucher | Legacy/backup |

### 3.2 Online Payment via My Business Account

**Portal**: https://www.canada.ca/en/revenue-agency/services/e-services/e-services-businesses/business-account.html

**Process**:
1. Login to My Business Account
2. Navigate to "Make a payment"
3. Select payroll account
4. Enter amount and period
5. Complete payment

### 3.3 PD7A Remittance Voucher

**Form**: https://www.canada.ca/en/revenue-agency/services/forms-publications/forms/pd7a.html

**Usage**: Required when paying by cheque

**Mail to**:
```
Sudbury Tax Centre
1050 Notre Dame Avenue
Sudbury ON P3A 5C1
```

---

## 4. Implementation Phases for Beanflow

### Phase 1: Document Generation (MVP)

**Goal**: Generate compliant documents for manual upload

| Document | Output | User Action Required |
|----------|--------|---------------------|
| T4 | XML file + PDF | Upload XML to CRA Internet File Transfer |
| T4 Summary | XML file + PDF | Included in T4 XML submission |
| ROE | XML file (.BLK) + PDF | Upload to ROE Web Payroll Extract |
| PD7A | PDF | Download, print, mail with cheque |

**Implementation**:
- [x] T4SlipData model
- [x] T4XMLGenerator (T619 format)
- [x] T4PDFGenerator
- [x] RecordOfEmployment model
- [x] ROEXMLGenerator (ROE Web format)
- [x] ROEPDFGenerator
- [x] PD7ARemittanceVoucher model
- [x] PD7APDFGenerator

### Phase 2: Semi-Automated Submission

**Goal**: Reduce manual steps with guided workflow

**Features**:
1. **Pre-submission validation**
   - Validate XML against official schema
   - Check for common errors
   - Display validation report

2. **Direct links to government portals**
   - Deep links to CRA Internet File Transfer
   - Deep links to ROE Web Payroll Extract

3. **Submission tracking**
   - Mark documents as "submitted"
   - Record confirmation numbers
   - Track submission dates

### Phase 3: Automated Submission (Enterprise)

**Goal**: One-click submission for larger employers

**Requirements**:
1. **CRA Integration**
   - Store user's Web Access Code (WAC)
   - Implement secure credential storage
   - Submit via CRA APIs

2. **ROE Web Integration**
   - Store ROE Web credentials
   - Implement bulk upload API
   - Handle status polling

**Security Considerations**:
- Encrypt stored credentials
- Implement audit logging
- Require re-authentication for submissions
- Follow CRA/Service Canada security requirements

---

## 5. Compliance Deadlines and Penalties

### 5.1 T4 Filing

| Deadline | Penalty |
|----------|---------|
| **Feb 28** | On time |
| **Late filing** | $10-$100/slip |
| **Non-filing** | 10% of deductions + 2%/month (max 20 months) |

### 5.2 ROE Filing

| Deadline | Penalty |
|----------|---------|
| **5 days** after interruption | On time |
| **Late/Non-filing** | $2,000 - $12,000 |

### 5.3 Remittance

| Days Late | Penalty Rate |
|-----------|-------------|
| 1-3 days | 3% |
| 4-5 days | 5% |
| 6-7 days | 7% |
| 8+ days | 10% |
| Repeated failures | Additional 20% |

---

## 6. Official Resources

### CRA Resources

| Resource | URL |
|----------|-----|
| T4 Guide (RC4120) | https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/rc4120.html |
| Internet File Transfer | https://www.canada.ca/en/revenue-agency/services/e-services/filing-information-returns-electronically-t4-t5-other-types-returns-overview.html |
| XML Schema Download | https://www.canada.ca/en/revenue-agency/services/e-services/filing-information-returns-electronically-t4-t5-other-types-returns-overview/filing-information-returns-electronically-t4-t5-other-types-returns-file/filing-internet-file-transfer/download-xml-schema.html |
| My Business Account | https://www.canada.ca/en/revenue-agency/services/e-services/e-services-businesses/business-account.html |
| Remittance Guide (T4001) | https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/t4001.html |

### Service Canada Resources

| Resource | URL |
|----------|-----|
| ROE Guide | https://www.canada.ca/en/employment-social-development/programs/ei/ei-list/reports/roe-guide.html |
| ROE Web Access | https://www.canada.ca/en/employment-social-development/programs/ei/ei-list/ei-roe/access-roe.html |
| Payroll Extract Guide | https://www.canada.ca/en/employment-social-development/programs/ei/ei-list/reports/payroll-extract.html |
| ROE Web User Requirements | https://www.canada.ca/en/employment-social-development/programs/ei/ei-list/ei-roe/user-requirements/functional.html |
| ROE Registration | https://www.canada.ca/en/employment-social-development/programs/ei/ei-list/ei-roe/register-roe.html |

---

## 7. Technical Notes

### 7.1 XML Validation Tools

**For T4 (T619 schema)**:
```bash
# Using xmllint
xmllint --schema T619_T4.xsd t4_submission.xml --noout

# Using Python lxml
from lxml import etree
schema = etree.XMLSchema(etree.parse('T619_T4.xsd'))
doc = etree.parse('t4_submission.xml')
schema.validate(doc)
```

**For ROE**:
```bash
# Validate against ROE Web schema
xmllint --schema roe-web.xsd roe_batch.blk --noout
```

### 7.2 Character Encoding

- **Required**: UTF-8 for all XML files
- **BOM**: Not required, but accepted

### 7.3 File Size Limits

| Submission | Max Size |
|------------|----------|
| CRA Internet File Transfer | 150 MB |
| ROE Web Payroll Extract | 1,200 ROEs per file, 10 files per upload |

---

**Document Version**: 1.0
**Created**: 2025-12-31
**Last Updated**: 2025-12-31
**For**: Beanflow-Payroll System - Government Electronic Submission Reference
