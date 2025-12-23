# Agadah Bot - Simplified

Generate youth workshop activities from Jewish stories.

## Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENROUTER_API_KEY
   ```

3. **Run:**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Open browser:**
   ```
   http://localhost:8000
   ```

### Docker Deployment

1. **Set environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENROUTER_API_KEY
   ```

2. **Build and run:**
   ```bash
   docker-compose up -d
   ```

3. **Access:**
   ```
   http://localhost:38472
   ```

## Deployment to Contabo VPS

1. **SSH to server:**
   ```bash
   ssh root@YOUR_SERVER_IP
   ```

2. **Install Docker** (if not installed):
   ```bash
   curl -fsSL https://get.docker.com | sh
   ```

3. **Clone repository:**
   ```bash
   git clone https://github.com/aviz85/agadah-bot-simple.git
   cd agadah-bot-simple
   ```

4. **Configure:**
   ```bash
   cp .env.example .env
   nano .env  # Add your OPENROUTER_API_KEY
   ```

5. **Deploy:**
   ```bash
   docker-compose up -d
   ```

6. **Check status:**
   ```bash
   docker-compose ps
   docker-compose logs -f
   ```

7. **Access:**
   ```
   http://YOUR_SERVER_IP:38472
   ```

## Architecture

- **4 Agents:** Input Processor → Content Finder → Activity Builder → Formatter
- **LLM:** OpenRouter (single API key)
- **Frontend:** Vanilla HTML/JS with SSE
- **Backend:** FastAPI
- **Data:** ~600 games from peula.net + agadah.org.il stories

## API Endpoints

- `GET /` - Homepage
- `GET /health` - Health check
- `GET /api/create?input=YOUR_INPUT` - Create activity (SSE stream)

## Example Inputs

- `פעילות על אהבת חינם לחטיבה, 40 דקות`
- `פעילות על חג הסיגד לתיכון, שעה`
- `רוצה פעילות על ערך האחדות לגילאי 12-14`

## License

MIT
