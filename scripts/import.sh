#!/bin/bash

# If you want to visit a remote server, modify it
BASE_URL="http://localhost:8000"

# Token is not required in local, if you set the ADMIN_AUTH_ENABLED and ADMIN_JWT_SECRET in a remote server, you put key here
TOKEN=""

print_usage() {
    echo "Usage: sh import.sh AGENT_ID"
    exit 1
}

# Check if correct number of arguments provided
if [ $# -ne 1 ]; then
    print_usage
fi

AGENT_ID="$1"
YAML_FILE="${AGENT_ID}.yaml"
if [ ! -f "${YAML_FILE}" ]; then
    echo "Error: File ${YAML_FILE} does not exist!"
    exit 1
fi

echo "Importing agent ${AGENT_ID}"
# Using the provided import command
HTTP_STATUS=$(curl -s -w "%{http_code}" -X PUT -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: multipart/form-data" \
     -F "file=@${YAML_FILE}" "${BASE_URL}/agents/${AGENT_ID}/import" -o "${AGENT_ID}.response")

if [ $HTTP_STATUS -ge 400 ]; then
    echo "Import failed with HTTP status ${HTTP_STATUS}"
    cat "${AGENT_ID}.response"
    rm "${AGENT_ID}.response"
    exit 1
fi

rm "${AGENT_ID}.response"
echo "Import succeeded"
