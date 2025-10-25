# Prep Pad 🍳

**The AI Recipe Prep Assistant** - Transform any recipe into an optimized, voice-controlled cooking experience.

## 🎯 What It Does

Following a recipe while cooking is chaotic. You constantly have to re-read steps, wash your hands to check your phone, and figure out timing. Prep Pad solves this by:

1. **Scraping any recipe URL** from cooking blogs/websites
2. **AI-powered optimization** that rewrites recipes into prep-first workflows
3. **Voice-controlled guidance** - hands-free cooking with commands like "Next", "Repeat", "What prep?"

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

3. **Run the server:**
   ```bash
   python run_server.py
   ```

4. **Test it:**
   - API Docs: `http://localhost:8000/docs`
   - Try parsing a recipe URL!

## 🧪 Example Usage

```bash
curl -X POST "http://localhost:8000/api/parse_recipe" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.allrecipes.com/recipe/213742/cheesy-chicken-broccoli-casserole/"}'
```

## 🏗️ Architecture

- **Backend**: FastAPI with SQLModel
- **AI**: GPT-4 for recipe optimization
- **Database**: SQLite (auto-created)
- **Vector Store**: Pinecone for cooking knowledge
- **Web Scraping**: BeautifulSoup for recipe extraction

## 📁 Project Structure

```
backend/
├── app/
│   ├── agents/          # AI agents for recipe optimization
│   ├── models/          # Database models
│   ├── schemas/         # API schemas
│   └── db/             # Database configuration
├── routes/             # API endpoints
├── scrapers/           # Recipe web scraping
└── vector_store/       # Pinecone integration
```

## 🎤 Voice Commands

- `"next"` - Move to next step
- `"repeat"` - Repeat current step
- `"what prep"` - Show prep phase
- `"pause"` - Pause cooking
- `"resume"` - Resume cooking
- `"time"` - Get remaining time
- `"ingredients"` - List ingredients

## 🔧 API Endpoints

- `POST /api/parse_recipe` - Parse recipe from URL
- `GET /api/recipes` - Get saved recipes
- `POST /api/start_cooking/{id}` - Start cooking session
- `POST /api/voice_command` - Process voice commands

---

**Transform any messy recipe blog into a clean, efficient cooking workflow!** 🎯