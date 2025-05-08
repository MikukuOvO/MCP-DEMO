#!/bin/sh

# Kill any existing Python processes running the MCP servers
pkill -f "python.*mcp_servers/.*_mcp_server.py"

# Wait a moment for processes to clean up
sleep 1

# Run each Python server file in the mcp_servers directory
for server_file in mcp_servers/*_mcp_server.py; do
    if [ -f "$server_file" ]; then
        echo "Starting server: $server_file"
        python "$server_file" &
    fi
done

# Function to handle script termination
cleanup() {
    echo "Shutting down servers..."
    pkill -f "python.*mcp_servers/.*_mcp_server.py"
    exit 0
}

# Set up trap for SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

# Wait for all background processes
wait
