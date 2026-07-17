#!/bin/bash
cd /Users/lee/WorkBuddy/2026-07-16-13-29-53/lottery-ai-simulator
export PYTHONPATH=src
exec .venv/bin/python src/lottery_sim/cli.py dashboard --reports reports/users/admin/latest --host 0.0.0.0 --port 8765 --server stdlib
