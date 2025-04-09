#!/bin/bash
# Conda Environment Management Script for BookBrainWrangler
# 
# This script provides functions to create, activate, update, and remove
# a conda environment for the BookBrainWrangler project.
#
# Usage:
#   ./conda_env.sh create [env_name] [python_version]   - Create a new conda environment
#   ./conda_env.sh activate [env_name]                 - Activate the conda environment
#   ./conda_env.sh update [env_name]                   - Update the conda environment
#   ./conda_env.sh remove [env_name]                   - Remove the conda environment
#   ./conda_env.sh info [env_name]                     - Display environment information
#
# Default values:
#   env_name: bookbrainwrangler
#   python_version: 3.10

# Set default values
ENV_NAME=${2:-"bookbrainwrangler"}
PYTHON_VERSION=${3:-"3.10"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to check if conda is installed
check_conda_installed() {
    if ! command -v conda &> /dev/null; then
        echo -e "${RED}Conda is not installed or not in PATH. Please install Conda first.${NC}"
        return 1
    fi
    return 0
}

# Function to check if the environment exists
check_env_exists() {
    local env_name=$1
    if conda env list | grep -q "\b${env_name}\b"; then
        return 0
    else
        return 1
    fi
}

# Function to create the conda environment
create_environment() {
    local env_name=$1
    local python_version=$2
    
    if check_env_exists "$env_name"; then
        echo -e "${YELLOW}Environment '$env_name' already exists. Use 'update' to update it.${NC}"
        return
    fi
    
    echo -e "${CYAN}Creating conda environment '$env_name' with Python $python_version...${NC}"
    
    # Create the environment with Python
    conda create -n "$env_name" python="$python_version" -y
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create conda environment.${NC}"
        return
    fi
    
    # Install requirements
    echo -e "${CYAN}Installing requirements...${NC}"
    conda run -n "$env_name" pip install -r "$(pwd)/requirements.txt"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Conda environment '$env_name' created successfully.${NC}"
        echo -e "${CYAN}To activate the environment, run: source ./conda_env.sh activate${NC}"
    else
        echo -e "${RED}Failed to install requirements.${NC}"
    fi
}

# Function to activate the conda environment
activate_environment() {
    local env_name=$1
    
    if ! check_env_exists "$env_name"; then
        echo -e "${YELLOW}Environment '$env_name' does not exist. Create it first with 'create' action.${NC}"
        return
    fi
    
    echo -e "${CYAN}Activating conda environment '$env_name'...${NC}"
    echo -e "${GREEN}Run the following command in your shell:${NC}"
    echo -e "${YELLOW}conda activate $env_name${NC}"
    
    # Note: Direct activation doesn't work when script is executed, only when sourced
    echo -e "${CYAN}Note: You can also use 'source ./conda_env.sh activate' to activate directly.${NC}"
    
    # If script is sourced, try to activate the environment
    if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
        conda activate "$env_name"
        echo -e "${GREEN}Environment '$env_name' activated.${NC}"
    fi
}

# Function to update the conda environment
update_environment() {
    local env_name=$1
    
    if ! check_env_exists "$env_name"; then
        echo -e "${YELLOW}Environment '$env_name' does not exist. Create it first with 'create' action.${NC}"
        return
    fi
    
    echo -e "${CYAN}Updating conda environment '$env_name'...${NC}"
    
    # Update Python packages from requirements.txt
    conda run -n "$env_name" pip install -r "$(pwd)/requirements.txt" --upgrade
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Conda environment '$env_name' updated successfully.${NC}"
    else
        echo -e "${RED}Failed to update environment.${NC}"
    fi
}

# Function to remove the conda environment
remove_environment() {
    local env_name=$1
    
    if ! check_env_exists "$env_name"; then
        echo -e "${YELLOW}Environment '$env_name' does not exist.${NC}"
        return
    fi
    
    echo -e "${CYAN}Removing conda environment '$env_name'...${NC}"
    
    read -p "Are you sure you want to remove the environment '$env_name'? (y/n) " confirmation
    if [[ $confirmation == 'y' ]]; then
        conda env remove -n "$env_name" -y
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Conda environment '$env_name' removed successfully.${NC}"
        else
            echo -e "${RED}Failed to remove environment.${NC}"
        fi
    else
        echo -e "${YELLOW}Operation cancelled.${NC}"
    fi
}

# Function to show environment information
show_environment_info() {
    local env_name=$1
    
    if ! check_env_exists "$env_name"; then
        echo -e "${YELLOW}Environment '$env_name' does not exist.${NC}"
        return
    fi
    
    echo -e "${CYAN}Information about conda environment '$env_name':${NC}"
    conda env list | grep "$env_name"
    echo -e "\n${CYAN}Installed packages:${NC}"
    conda run -n "$env_name" pip list
}

# Main script execution
if ! check_conda_installed; then
    exit 1
fi

# Check for action parameter
if [ $# -eq 0 ]; then
    echo -e "${RED}Error: Missing action parameter.${NC}"
    echo "Usage: $0 [create|activate|update|remove|info] [env_name] [python_version]"
    exit 1
fi

ACTION=$1

case $ACTION in
    "create")
        create_environment "$ENV_NAME" "$PYTHON_VERSION"
        ;;
    "activate")
        activate_environment "$ENV_NAME"
        ;;
    "update")
        update_environment "$ENV_NAME"
        ;;
    "remove")
        remove_environment "$ENV_NAME"
        ;;
    "info")
        show_environment_info "$ENV_NAME"
        ;;
    *)
        echo -e "${RED}Invalid action: $ACTION${NC}"
        echo "Usage: $0 [create|activate|update|remove|info] [env_name] [python_version]"
        exit 1
        ;;
esac
