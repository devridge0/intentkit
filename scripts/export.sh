#!/bin/bash

# If you want to visit a remote server, modify it
BASE_URL="http://localhost:8000"

# Token is not required in local, if you set the ADMIN_AUTH_ENABLED and ADMIN_JWT_SECRET in a remote server, you put key here
TOKEN=""

print_usage() {
    echo "Usage: sh export.sh AGENT_ID"
    exit 1
}

# Check if correct number of arguments provided
if [ $# -ne 1 ]; then
    print_usage
fi

AGENT_ID="$1"
echo "Exporting agent [${AGENT_ID}] ..."
# Using the provided export command
HTTP_STATUS=$(curl -s -w "%{http_code}" -H "Authorization: Bearer ${TOKEN}" --clobber "${BASE_URL}/agents/${AGENT_ID}/export" -o ${AGENT_ID}.yaml)

if [ $HTTP_STATUS -ge 400 ]; then
    echo "Export failed with HTTP status ${HTTP_STATUS}"
    exit 1
fi

echo "Export succeeded, the file is saved (typically as ${AGENT_ID}.yaml)"
