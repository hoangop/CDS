# CDS Analytics - Quick Start Guide

## 🚀 5-Minute Setup

### Prerequisites

- Docker Desktop installed and running
- Python 3.9+
- Git

### Step 1: Clone & Setup

```bash
git clone https://github.com/hoangop/CDS.git
cd CDS_project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# or: venv\Scripts\activate  # Windows
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Start Services

```bash
docker-compose up -d
```

Wait ~30 seconds for services to initialize.

### Step 4: Create Database

```bash
./venv/bin/python data_pipeline/scripts/create_db.py
```

### Step 5: Access Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/api/v1/schools
- **API Docs:** http://localhost:8000/docs

---

## 📊 Import Data (Optional)

### Option 1: From CSV (Fast - 230 schools)

```bash
./venv/bin/python data_pipeline/scripts/import_from_csv.py
```

### Option 2: From PDFs (Slow - requires Gemini API)

```bash
# Set API key
export GOOGLE_API_KEY="your-key-here"

# Process PDFs
./venv/bin/python data_pipeline/scripts/process_pdfs_to_db.py
```

### Option 3: Get Rankings (Very Slow - web scraping)

```bash
./venv/bin/python data_pipeline/scripts/update_rankings.py
```

⚠️ **Warning:** Ranking script may take 1-2 hours for all schools and may get blocked. Use sparingly.

---

## 🧪 Test Everything

```bash
./venv/bin/python test_system.py
```

Expected output:
```
✅ ALL TESTS PASSED!
📊 Total Institutions: 230
🏆 Schools with Rankings: 83
```

---

## 🛠️ Common Tasks

### Restart Backend (after code changes)

```bash
docker-compose restart backend
```

### View Logs

```bash
# Backend
docker logs cds_project-backend-1 --tail 50

# Frontend
docker logs cds_project-frontend-1 --tail 50
```

### Stop All Services

```bash
docker-compose down
```

### Database Access

```bash
# Connect to PostgreSQL
docker exec -it cds_project-db-1 psql -U postgres -d cds_db

# Example queries
SELECT COUNT(*) FROM institution_master;
SELECT name, rank_2025, rank_type FROM institution_master WHERE rank_2025 IS NOT NULL LIMIT 10;
```

---

## 🐛 Troubleshooting

### Backend returns 500 error

```bash
# Check logs
docker logs cds_project-backend-1 --tail 50

# Restart
docker-compose restart backend
```

### Frontend shows "No schools found"

```bash
# Test API
curl http://localhost:8000/api/v1/schools?limit=5

# If empty, import data
./venv/bin/python data_pipeline/scripts/import_from_csv.py
```

### Port already in use

```bash
# Find and kill process using port 3000
lsof -ti:3000 | xargs kill -9

# Or use different ports in docker-compose.yml
```

---

## 📚 Next Steps

Read [ARCHITECTURE.md](./ARCHITECTURE.md) for:
- Detailed system architecture
- API documentation
- Database schema
- Coding conventions
- Development workflow

---

## 🔑 API Keys

### Google Gemini API (for PDF parsing and ranking)

1. Get free key: https://ai.google.dev/
2. Set environment variable:
   ```bash
   export GOOGLE_API_KEY="your-key-here"
   ```

---

## 📞 Help

- **GitHub Issues:** https://github.com/hoangop/CDS/issues
- **Architecture Doc:** [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Project Structure:** See file tree in ARCHITECTURE.md

---

**Estimated Setup Time:** 5-10 minutes (without data import)  
**With Data Import:** 15-30 minutes  
**With Rankings:** 2-3 hours (automated)

