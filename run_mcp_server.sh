#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p logs

# Kill any existing Python MCP server processes
pkill -f "python.*mcp_servers/.*_mcp_server.py"

sleep 1

# Run each Python server in the background and log output
for server_file in mcp_servers/*_mcp_server.py; do
    if [ -f "$server_file" ]; then
        log_file="logs/$(basename "$server_file").log"
        echo "Starting server: $server_file (logging to $log_file)"
        python "$server_file" >> "$log_file" 2>&1 &
    fi
done

# Function to clean up on exit
cleanup() {
    echo "Shutting down all MCP servers..."
    pkill -f "python.*mcp_servers/.*_mcp_server.py"
    exit 0
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

echo "All MCP servers started. Press Ctrl+C to stop."

# Wait indefinitely so script stays alive
while true; do
    sleep 1
done
