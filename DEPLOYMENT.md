# Prep Pad - Running, Testing & Deployment Guide 🍳

## 🚀 Quick Start (Local Development)

### 1. **Setup Environment**
```bash
# Clone the repository (if not already done)
git clone https://github.com/AryahiNittur/prep-pad.git
cd prep-pad

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your API keys:
# - OPENAI_API_KEY=your_openai_key
# - PINECONE_API_KEY=your_pinecone_key
# - PINECONE_ENVIRONMENT=your_pinecone_env
# - PINECONE_INDEX_NAME=your_pinecone_index
```

### 2. **Run the Server**
```bash
# Option 1: Using the startup script
python run_server.py

# Option 2: Direct uvicorn command
uvicorn backend.app.main:app --reload --port 8000

# Option 3: With custom host/port
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. **Verify It's Working**
```bash
# Check if server is running
curl http://localhost:8000/
# Should return: {"message":"Welcome to Prep Pad - Your Recipe Prep Assistant!"}

# View API documentation
open http://localhost:8000/docs
```

---

## 🧪 Testing

### **API Testing with curl**

#### 1. **Test Recipe Parsing**
```bash
curl -X POST "http://localhost:8000/api/parse_recipe" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.allrecipes.com/recipe/213742/cheesy-chicken-broccoli-casserole/"}'
```

#### 2. **Get All Recipes**
```bash
curl http://localhost:8000/api/recipes
```

#### 3. **Start Cooking Session**
```bash
curl -X POST "http://localhost:8000/api/start_cooking/1"
```

#### 4. **Test Voice Commands**
```bash
curl -X POST "http://localhost:8000/api/voice_command" \
     -H "Content-Type: application/json" \
     -d '{"command": "next", "session_id": 1}'
```

### **Testing with Python Scripts**

Create `test_prep_pad.py`:
```python
import requests
import json

BASE_URL = "http://localhost:8000"

def test_recipe_parsing():
    """Test recipe parsing functionality"""
    url = "https://www.allrecipes.com/recipe/213742/cheesy-chicken-broccoli-casserole/"
    
    response = requests.post(f"{BASE_URL}/api/parse_recipe", 
                           json={"url": url})
    
    if response.status_code == 200:
        recipe = response.json()
        print(f"✅ Recipe parsed: {recipe['title']}")
        print(f"Prep steps: {len(recipe['prep_phase'])}")
        print(f"Cook steps: {len(recipe['cook_phase'])}")
        return recipe
    else:
        print(f"❌ Error: {response.text}")
        return None

def test_cooking_session(recipe_id):
    """Test cooking session management"""
    # Start cooking session
    response = requests.post(f"{BASE_URL}/api/start_cooking/{recipe_id}")
    
    if response.status_code == 200:
        session = response.json()
        print(f"✅ Cooking session started: {session['session_id']}")
        return session['session_id']
    else:
        print(f"❌ Error starting session: {response.text}")
        return None

def test_voice_commands(session_id):
    """Test voice command processing"""
    commands = ["next", "repeat", "what prep", "time", "ingredients"]
    
    for cmd in commands:
        response = requests.post(f"{BASE_URL}/api/voice_command",
                               json={"command": cmd, "session_id": session_id})
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ '{cmd}': {result['response']}")
        else:
            print(f"❌ Error with '{cmd}': {response.text}")

if __name__ == "__main__":
    print("🧪 Testing Prep Pad...")
    
    # Test recipe parsing
    recipe = test_recipe_parsing()
    
    if recipe:
        # Test cooking session
        session_id = test_cooking_session(1)  # Assuming recipe ID 1
        
        if session_id:
            # Test voice commands
            test_voice_commands(session_id)
    
    print("✅ Testing complete!")
```

Run tests:
```bash
python test_prep_pad.py
```

---

## 🚀 Deployment Options

### **Option 1: Docker Deployment**

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  prep-pad:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - PINECONE_ENVIRONMENT=${PINECONE_ENVIRONMENT}
      - PINECONE_INDEX_NAME=${PINECONE_INDEX_NAME}
      - DATABASE_URL=sqlite:///./prep_pad.db
    volumes:
      - ./prep_pad.db:/app/prep_pad.db
    restart: unless-stopped
```

Deploy with Docker:
```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### **Option 2: Cloud Deployment (Railway)**

1. **Install Railway CLI**:
```bash
npm install -g @railway/cli
```

2. **Login and deploy**:
```bash
railway login
railway init
railway up
```

3. **Set environment variables** in Railway dashboard:
- `OPENAI_API_KEY`
- `PINECONE_API_KEY`
- `PINECONE_ENVIRONMENT`
- `PINECONE_INDEX_NAME`

### **Option 3: Heroku Deployment**

Create `Procfile`:
```
web: uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

Deploy to Heroku:
```bash
# Install Heroku CLI, then:
heroku create prep-pad-app
heroku config:set OPENAI_API_KEY=your_key
heroku config:set PINECONE_API_KEY=your_key
heroku config:set PINECONE_ENVIRONMENT=your_env
heroku config:set PINECONE_INDEX_NAME=your_index
git push heroku main
```

### **Option 4: VPS Deployment (DigitalOcean/AWS)**

1. **Set up server**:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install nginx (for reverse proxy)
sudo apt install nginx -y
```

2. **Deploy application**:
```bash
# Clone repository
git clone https://github.com/AryahiNittur/prep-pad.git
cd prep-pad

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
nano .env  # Edit with your API keys

# Run with gunicorn for production
pip install gunicorn
gunicorn backend.app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

3. **Set up nginx reverse proxy**:
```bash
sudo nano /etc/nginx/sites-available/prep-pad
```

Add nginx config:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/prep-pad /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔧 Production Considerations

### **Environment Variables**
- Use strong, unique API keys
- Set `DATABASE_URL` to PostgreSQL for production
- Enable HTTPS with SSL certificates

### **Database**
- Switch from SQLite to PostgreSQL for production
- Set up database backups
- Use connection pooling

### **Monitoring**
- Add logging and monitoring
- Set up health checks
- Monitor API usage and performance

### **Security**
- Add authentication/authorization
- Rate limiting
- Input validation
- CORS configuration

---

## 📊 Health Checks

Add to `backend/app/main.py`:
```python
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Prep Pad",
        "version": "1.0.0",
        "database": "connected"
    }
```

Test health:
```bash
curl http://localhost:8000/health
```

---

## 🎯 Quick Commands Summary

```bash
# Local Development
python run_server.py

# Testing
python test_prep_pad.py

# Docker
docker-compose up --build

# Railway
railway up

# Heroku
git push heroku main

# Production Server
gunicorn backend.app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Prep Pad is ready to deploy!** 🚀
