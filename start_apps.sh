#!/bin/bash
echo "cd /home/project"
echo "git clone https://github.com/nordeim/ledgersg.git"

cd /home/project/ledgersg/apps/backend && source /opt/venv/bin/activate && python manage.py runserver 0.0.0.0:8000

/bin/bash -c "cd /home/project/ledgersg/apps/web && nohup node .next/standalone/server.js > /tmp/next-server.log 2>&1 &"
