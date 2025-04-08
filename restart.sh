# Define color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting makemigrations...${NC}"
python3 manage.py makemigrations
echo -e "${GREEN}makemigrations completed.${NC}"
read -p "Press Enter to continue..."

echo -e "${YELLOW}Starting migrate...${NC}"
python3 manage.py migrate
echo -e "${GREEN}migrate completed.${NC}"
read -p "Press Enter to continue..."

echo -e "${YELLOW}Restarting gunicorn-dev.service...${NC}"
systemctl restart gunicorn-dev.service
echo -e "${GREEN}gunicorn-dev.service restarted.${NC}"
read -p "Press Enter to continue..."

echo -e "${YELLOW}Restarting nginx...${NC}"
systemctl restart nginx
echo -e "${GREEN}nginx restarted.${NC}"
read -p "Press Enter to continue..."

echo -e "${YELLOW}Checking gunicorn-dev.service status...${NC}"
systemctl status gunicorn-dev.service
echo -e "${GREEN}gunicorn-dev.service status checked.${NC}"
read -p "Press Enter to continue..."

echo -e "${YELLOW}Checking nginx status...${NC}"
systemctl status nginx
echo -e "${GREEN}nginx status checked.${NC}"

echo -e "${GREEN}Script execution completed.${NC}"