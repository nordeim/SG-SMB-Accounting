• Implementation Complete

🔴 Root Cause Identified & Fixed

 Issue                   Location          Fix
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Wrong settings module   wsgi.py line 14   Added DJANGO_SETTINGS_MODULE=config.settings.service to entrypoint

The Problem Chain:

wsgi.py defaults to 'config.settings.production'
                ↓
production.py adds 'file' handler to LOGGING
                ↓
File handler points to /var/log/ledgersg/django.log
                ↓
Directory doesn't exist in container
                ↓
ValueError: Unable to configure handler 'file'
                ↓
Backend crashes

🔧 Fixes Applied

 File                Change
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 docker/Dockerfile   Added DJANGO_SETTINGS_MODULE=config.settings.service to .env file
 docker/Dockerfile   Exported DJANGO_SETTINGS_MODULE before Gunicorn start
 docker/Dockerfile   Passed DJANGO_SETTINGS_MODULE to Gunicorn subprocess
 docker/Dockerfile   Updated boot.py log file paths (removed non-existent backend_error/access)

Key Changes

1. Environment Variable Export

# Export Django settings module for container environment
export DJANGO_SETTINGS_MODULE=config.settings.service

# Start Django with Gunicorn
sudo -u user nohup bash -c "
    export DJANGO_SETTINGS_MODULE=config.settings.service &&
    ...
"

2. .env File Update

DJANGO_SETTINGS_MODULE=config.settings.service  # ← Added
DEBUG=False
SECRET_KEY=...
...

Expected Result After Deploy

════════════════════════════════════════════════════════════════
   Service Status Summary
════════════════════════════════════════════════════════════════
  ✅ Backend API:    http://localhost:8000 (Gunicorn)
  ✅ Frontend:       http://localhost:3000
  ✅ Redis:          localhost:6379
  ✅ PostgreSQL:     localhost:5432
  ℹ  Monitor:        http://localhost:7860 (boot.py)

🎉 All critical services are ready!

The backend should now use config.settings.service (which has console-only logging) instead of config.settings.production (which had the problematic file handler).

---

• Excellent question! Let me analyze this carefully.

The $ Escaping Analysis

Looking at the current pattern in the Dockerfile:

COPY <<'ENTRYEOF' /usr/local/bin/entrypoint.sh
#!/bin/bash
...
cat > .env << ENVEOF
DJANGO_SETTINGS_MODULE=config.settings.service
SECRET_KEY=django-secret-key-for-hf-space-$(date +%s)
DB_NAME=${DB_NAME}
...
ENVEOF
...
ENTRYEOF

🔍 Two Layers of Heredoc

 Layer                  Delimiter               Expansion Behavior
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Outer (Dockerfile)     <<'ENTRYEOF' (quoted)   ❌ No expansion - content preserved literally
 Inner (Shell script)   << ENVEOF (unquoted)    ✅ Expansion happens at runtime

The Answer: NO Escaping Needed ✓

Why:

1. The outer COPY <<'ENTRYEOF' (quoted) preserves everything literally into entrypoint.sh
2. The inner cat > .env << ENVEOF (unquoted) in the shell script causes expansion at runtime
3. This is exactly what we want - runtime values!

Current Behavior (Correct)

# At container runtime, entrypoint.sh executes:
cat > .env << ENVEOF
SECRET_KEY=django-secret-key-for-hf-space-$(date +%s)  # → Expands to: django-secret-key-for-hf-space-1740742893
DB_NAME=${DB_NAME}                                      # → Expands to: ledgersg_dev
ENVEOF

If You Escaped (Would Be Wrong)

cat > .env << ENVEOF
SECRET_KEY=django-secret-key-for-hf-space-\$(date +%s)  # → Literal: django-secret-key-for-hf-space-$(date +%s)
DB_NAME=\${DB_NAME}                                     # → Literal: ${DB_NAME}
ENVEOF

Result: .env file would contain literal $(date +%s) and ${DB_NAME} strings instead of values.

---

Summary

 Current Pattern   Result
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 $(date +%s)       ✅ Expands to timestamp at runtime
 ${DB_NAME}        ✅ Expands to database name at runtime
 \$(date +%s)      ❌ Would be literal string (wrong)
 \${DB_NAME}       ❌ Would be literal string (wrong)

The current pattern is correct - no escaping needed because the inner unquoted heredoc (<< ENVEOF) is designed to expand variables at runtime.


