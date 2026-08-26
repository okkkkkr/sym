#!/bin/sh
set -eu

secret_path=/run/secrets/admin_htpasswd
runtime_path=/etc/nginx/admin.htpasswd

if [ ! -r "$secret_path" ]; then
    echo "admin Basic Auth secret is missing or unreadable" >&2
    exit 1
fi

cp "$secret_path" "$runtime_path"
chown root:nginx "$runtime_path"
chmod 0640 "$runtime_path"
