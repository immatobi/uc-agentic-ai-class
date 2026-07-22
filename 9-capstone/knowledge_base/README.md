# Northstar CRM Knowledge Base

These documents are the starter knowledge base for the final capstone project, **Production-Ready Customer Support Agent**.

Students can load these files into their vector store and use them to test retrieval, routing, troubleshooting, onboarding, escalation, and source-grounded answering.

## Suggested Loader Path

Use this folder as the document source:

```text
capstone_project/knowledge_base
```

## Included Documents

- `product_overview.txt`: Northstar CRM features, modules, limitations, and product-answering behavior.
- `pricing_and_billing.txt`: Starter, Pro, and Business plans, billing cycles, invoices, failed payments, and duplicate-charge escalation.
- `account_access_guide.txt`: Login, password reset, invitations, roles, browser troubleshooting, and access-related escalation.
- `integrations_guide.txt`: Gmail, Microsoft 365, web forms, calendar activity, and integration troubleshooting.
- `troubleshooting_playbook.txt`: Step-by-step handling for duplicate contacts, missing imports, email sync, slow loading, login problems, and pipeline issues.
- `escalation_policy.txt`: Priority levels, assignment teams, escalation format, safe information collection, and restricted information.
- `csv_import_guide.txt`: CSV file requirements, import steps, duplicate prevention, validation errors, and post-import review.
- `email_sync_guide.txt`: Email sync setup, supported providers, missing email troubleshooting, duplicate contacts from sync, and privacy escalation.
- `security_policy.txt`: Security-sensitive issue handling, immediate safety steps, audit logs, former employee access, and unsafe claims to avoid.
- `onboarding_checklist.txt`: 30-day onboarding plan, spreadsheet migration checklist, adoption tips, and Customer Success escalation triggers.
- `sla_and_support_hours.txt`: Support channels, response targets, priorities, plan-level support expectations, and after-hours guidance.

## Retrieval Test Coverage

The documents include realistic coverage for the required capstone scenarios:

- CSV contact imports.
- Pro plan features.
- Connecting Gmail or Microsoft 365 email.
- Duplicate contacts after import or sync.
- Login issues before an urgent sales demo.
- Duplicate or unexpected billing charges.
- Suspected unauthorized access.
- 30-day onboarding for a five-person sales team.
- Migration from spreadsheets.
- General questions that should not retrieve sources.

Students should not hard-code responses to these examples. The retrieval tests should prove the documents are loaded and cited.
