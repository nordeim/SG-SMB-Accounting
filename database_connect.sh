exit 0

PGPASSWORD=ledgersg_secret_to_change psql -h localhost -U ledgersg -d ledgersg_dev -f database_schema.sql 

. /opt/venv/bin/activate && cd /home/project/Ledger-SG/apps/backend && python -m pytest tests/test_api_endpoints.py --reuse-db -v --tb=short

. /opt/venv/bin/activate && cd /home/project/Ledger-SG/apps/backend && python -m pytest tests/test_api_endpoints.py --reuse-db -v --tb=short --no-migrations

. /opt/venv/bin/activate && cd /home/project/Ledger-SG/apps/backend && python -c "
import psycopg
conn = psycopg.connect('host=localhost dbname=ledgersg_dev user=ledgersg password=ledgersg_secret_to_change')
cur = conn.cursor()
cur.execute(\"SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema IN ('core', 'coa', 'gst', 'journal', 'invoicing', 'banking', 'audit') AND table_type = 'BASE TABLE' ORDER BY table_schema, table_name\")
tables = cur.fetchall()
print('Tables in database:')
for t in tables:
    print(f'  {t[0]}.{t[1]}')
print(f'\\nTotal: {len(tables)} tables')
"

Tables in database:
  audit.event_log
  banking.bank_account
  banking.bank_transaction
  banking.payment
  banking.payment_allocation
  coa.account
  coa.account_sub_type
  coa.account_type
  core.app_user
  core.currency
  core.document_sequence
  core.exchange_rate
  core.fiscal_period
  core.fiscal_year
  core.organisation
  core.organisation_setting
  core.role
  core.user_organisation
  gst.peppol_transmission_log
  gst.return
  gst.tax_code
  gst.threshold_snapshot
  invoicing.contact
  invoicing.document
  invoicing.document_attachment
  invoicing.document_line
  journal.entry
