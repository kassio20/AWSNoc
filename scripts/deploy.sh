#!/bin/bash

echo "🚀 SelectNOC IA - Deploy Script"
echo "================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}❌ Don't run this script as root${NC}"
    exit 1
fi

# Create logs directory
mkdir -p logs

echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo -e "${YELLOW}🗄️ Setting up database...${NC}"
python database/scripts/database_manager.py

echo -e "${YELLOW}⚙️ Configuring systemd service...${NC}"
sudo cp deployment/selectnoc.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable selectnoc

echo -e "${YELLOW}🌐 Configuring Nginx...${NC}"
sudo cp deployment/nginx.conf /etc/nginx/sites-available/selectnoc
sudo ln -sf /etc/nginx/sites-available/selectnoc /etc/nginx/sites-enabled/
sudo systemctl restart nginx

echo -e "${YELLOW}🚀 Starting SelectNOC service...${NC}"
sudo systemctl start selectnoc

echo -e "${GREEN}✅ Deploy completed successfully!${NC}"
echo -e "${GREEN}🌍 Access: http://$(curl -s ifconfig.me)${NC}"
echo -e "${GREEN}📊 API Docs: http://$(curl -s ifconfig.me)/docs${NC}"
echo -e "${GREEN}📝 Logs: tail -f logs/app.log${NC}"
