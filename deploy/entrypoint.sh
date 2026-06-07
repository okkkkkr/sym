#!/bin/sh
set -e

nginx
python /opt/sym/run.py
