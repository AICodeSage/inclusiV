#!/bin/bash

# Exit on any error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting A2A Demo Agents...${NC}"

# Change to the agents directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source .venv/bin/activate
fi

# Array to store process IDs
pids=()

# Function to clean up processes
cleanup() {
    echo -e "\n${YELLOW}Shutting down all agents...${NC}"
    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping process $pid"
            kill "$pid"
        fi
    done
    wait
    echo -e "${GREEN}All agents stopped.${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start the agents
echo -e "${YELLOW}Starting MTN MoMo Transaction Agent...${NC}"
python momo_agent.py &
pids+=($!)

echo -e "${YELLOW}Starting MediRescue Advisor Agent...${NC}"
python medirescue_advisor.py &
pids+=($!)

echo -e "${YELLOW}Starting Insurance Agent...${NC}"
python insurance_agent.py &
pids+=($!)

echo -e "${YELLOW}Starting Business Research & Locator Agent...${NC}"
python research_agent.py &
pids+=($!)

echo -e "${GREEN}All agents started successfully!${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all agents${NC}"
echo ""

# Wait for all background processes
wait 