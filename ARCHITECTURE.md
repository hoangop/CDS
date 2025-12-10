# CDS Analytics - System Architecture

## 📋 Product Overview

**CDS Analytics** is a comprehensive web application for analyzing and comparing university admission data from the Common Data Set (CDS). The system allows users to:

- Browse 230+ U.S. universities with admission statistics
- Compare acceptance rates (overall and international students)
- View U.S. News rankings (2025)
- Search and filter institutions by name or alphabetically
- Access detailed admission data for each institution

**Target Users:** Prospective students, education consultants, researchers, and parents researching U.S. university admissions.

---

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT                               │
│                  (Browser - React/Next.js)                  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    BACKEND API                              │
│              (FastAPI + SQLAlchemy)                         │
│              Port: 8000 (Docker)                            │
└────────────────────────┬────────────────────────────────────┘
                         │ SQL
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   DATABASE                                  │
│                (PostgreSQL 15)                              │
│              Port: 5432 (Docker)                            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  DATA PIPELINE                              │
│         (Python Scripts - PDF Parser, Scraper)              │
│  - process_pdfs_to_db.py  (Gemini Vision API)             │
│  - update_rankings.py     (Playwright + Gemini)            │
└─────────────────────────────────────────────────────────────┘
```

### Deployment

**Local Development:**
- All services run in Docker containers via `docker-compose.yml`
- Frontend: `localhost:3000`
- Backend: `localhost:8000`
- Database: `localhost:5432`

**Production (Planned):**
- Frontend: AWS Amplify / Vercel
- Backend: AWS ECS / App Runner
- Database: AWS RDS PostgreSQL
- File Storage: AWS S3

---

## 🗄️ Database Schema

### Tables

#### 1. `institution_master`
Primary table storing university information.

```sql
CREATE TABLE institution_master (
    institution_id VARCHAR(50) PRIMARY KEY,  -- Slug or numeric ID
    name VARCHAR(255) NOT NULL,
    city_state_zip VARCHAR(255),
    control VARCHAR(50),                     -- Public/Private
    website_url VARCHAR(255),
    rank_2025 INTEGER,                       -- US News rank
    rank_type VARCHAR(255)                   -- e.g., "National Universities"
);
```

**Key Points:**
- `institution_id`: Slugified name (e.g., `harvard_university`) or College Scorecard ID
- `rank_2025` and `rank_type`: Populated by `update_rankings.py`

#### 2. `admission_c`
Admission statistics table (CDS Section C1).

```sql
CREATE TABLE admission_c (
    institution_id VARCHAR(50) REFERENCES institution_master(institution_id),
    academic_year VARCHAR(10),
    total_applicants INTEGER,
    total_admitted INTEGER,
    total_enrolled INTEGER,
    acceptance_rate FLOAT,
    applicants_international INTEGER,
    admitted_international INTEGER,
    enrolled_international INTEGER,
    PRIMARY KEY (institution_id, academic_year)
);
```

**Key Points:**
- Linked to `institution_master` via `institution_id`
- International data extracted from CDS PDF C1 table
- `academic_year`: e.g., "2023-2024"

### Data Sources

1. **College Scorecard API** (Primary for basic info)
2. **CDS PDFs** (Primary for admission data) - Parsed via Gemini Vision API
3. **US News Website** (Rankings) - Scraped via Playwright + Gemini Vision

---

## 🖥️ Frontend Architecture

### Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** TailwindCSS
- **State Management:** React Hooks (`useState`, `useEffect`)
- **HTTP Client:** Fetch API

### File Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx              # Home page (institution list)
│   │   ├── school/[id]/page.tsx  # School detail page
│   │   ├── layout.tsx            # Root layout
│   │   └── globals.css           # Global styles
│   ├── components/
│   │   └── Navbar.tsx            # Navigation bar
│   └── lib/
│       └── api.ts                # API helper functions
├── public/                       # Static assets
├── package.json
├── tsconfig.json
└── tailwind.config.js
```

### Key Pages

#### 1. Home Page (`/`)
**File:** `src/app/page.tsx`

**Features:**
- Search box (debounced 300ms)
- Alphabet filter (A-Z + ALL)
- Table with columns:
  - Institution Name
  - Rank (#1, #2, etc.)
  - Rank Type
  - Overall Rate
  - Int'l Rate
- Pagination (20 items/page)

**API Call:**
```typescript
const url = `${getApiUrl('/schools')}?q={search}&letter={letter}&limit=1000`;
```

#### 2. School Detail Page (`/school/[id]`)
**File:** `src/app/school/[id]/page.tsx`

**Features:**
- Detailed admission statistics
- Comparison table (Total vs International)
- Applied, Admitted, Enrolled counts
- Acceptance rates

**API Call:**
```typescript
const url = `${getApiUrl(`/schools/${id}`)}`;
```

### Design System

**Colors:**
- Primary: Indigo (`indigo-600`)
- Accent: Amber (for rankings), Blue (for international data)
- Background: Gradient (`from-slate-50 via-blue-50 to-indigo-50`)

**Typography:**
- Headings: `font-serif` (elegant, formal)
- Body: Default sans-serif
- Numbers: `font-bold`, right-aligned

**Components:**
- Rounded corners (`rounded-lg`, `rounded-xl`)
- Subtle shadows (`shadow-md`, `shadow-xl`)
- Hover effects (`hover:bg-indigo-50`)
- Alternating row colors (zebra striping)

---

## ⚙️ Backend Architecture

### Tech Stack

- **Framework:** FastAPI
- **ORM:** SQLAlchemy
- **Database Driver:** psycopg2-binary
- **Language:** Python 3.9+
- **Validation:** Pydantic v2

### File Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── api/
│   │   └── endpoints.py     # API routes
│   ├── models/
│   │   └── cds.py          # SQLAlchemy models
│   └── core/
│       └── database.py      # DB connection, session
├── requirements.txt
└── Dockerfile
```

### API Endpoints

#### GET `/api/v1/schools`
List all institutions with basic admission data.

**Query Parameters:**
- `q` (optional): Search query (name filter)
- `letter` (optional): Filter by first letter (A-Z)
- `skip` (optional): Pagination offset (default: 0)
- `limit` (optional): Max results (default: 100)

**Response:**
```json
[
  {
    "institution_id": "harvard_university",
    "name": "Harvard University",
    "city_state_zip": "Cambridge, MA 02138",
    "website_url": "https://www.harvard.edu",
    "rank_2025": 3,
    "rank_type": "National Universities",
    "total_applicants": 56000,
    "total_admitted": 1950,
    "applicants_international": 15000,
    "admitted_international": 450
  }
]
```

#### GET `/api/v1/schools/{school_id}`
Get detailed information for a specific school.

**Response:**
```json
{
  "institution_id": "harvard_university",
  "name": "Harvard University",
  "city_state_zip": "Cambridge, MA 02138",
  "website_url": "https://www.harvard.edu",
  "admission_data": [
    {
      "academic_year": "2023-2024",
      "total_applicants": 56000,
      "total_admitted": 1950,
      "total_enrolled": 1650,
      "applicants_international": 15000,
      "admitted_international": 450,
      "enrolled_international": 350
    }
  ]
}
```

### Database Connection

**Configuration:** `backend/app/core/database.py`

```python
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@db:5432/cds_db"
)
```

**Docker Service Name:** `db` (resolves to PostgreSQL container)

### Pydantic Models (v2 Syntax)

**IMPORTANT:** The project uses Pydantic v2. Always use:

```python
from pydantic import BaseModel, ConfigDict

class SchoolListItem(BaseModel):
    institution_id: str
    name: str
    rank_2025: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)  # NOT orm_mode = True

# Converting SQLAlchemy object to Pydantic:
item = SchoolListItem.model_validate(school)  # NOT from_orm()

# Converting Pydantic to dict:
data = item.model_dump()  # NOT dict()
```

---

## 🔧 Data Pipeline

### Scripts Location

All data pipeline scripts are in `data_pipeline/scripts/`.

### 1. PDF Processing (`process_pdfs_to_db.py`)

**Purpose:** Extract admission data from CDS PDF files using Gemini Vision API.

**Key Features:**
- Uploads PDFs to Google Gemini File API
- Sends structured prompt to extract C1 table data
- Parses JSON response
- Upserts data to `institution_master` and `admission_c` tables

**Usage:**
```bash
./venv/bin/python data_pipeline/scripts/process_pdfs_to_db.py
```

**Environment Variables:**
- `GOOGLE_API_KEY`: Gemini API key

**Important Notes:**
- Rate limited: Uses `time.sleep(3)` between requests
- Truncates `institution_id` to 50 characters
- Checks for existing institutions by name to avoid duplicates
- Only inserts admission data if `total_applicants > 0`

### 2. Ranking Scraper (`update_rankings.py`)

**Purpose:** Fetch US News rankings and update `rank_2025`, `rank_type` in DB.

**Key Features:**
- Uses `googlesearch-python` to find US News college page URLs
- Launches Playwright (headless Chromium) to access page
- Takes screenshot
- Sends screenshot to Gemini Vision API to extract rank
- Updates database

**Anti-Detection Measures:**
- Random User-Agent rotation (7 different agents)
- Random viewport sizes
- Random delays (3-8 seconds between requests)
- Fresh browser context for each school

**Usage:**
```bash
./venv/bin/python data_pipeline/scripts/update_rankings.py
```

**Configuration:**
```python
# Adjust limit in main() function
schools = get_schools_to_update(limit=50)
```

**Rate Limiting:**
- Processes 5-50 schools per run
- ~5-10 seconds per school
- If blocked by Google/US News, wait 1+ hours before resuming

---

## 🐳 Docker Setup

### Services

**File:** `docker-compose.yml`

```yaml
services:
  db:
    image: postgres:15-alpine
    ports: ["5432:5432"]
    environment:
      POSTGRES_DB: cds_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
  
  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [db]
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/cds_db
  
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000/api/v1
```

### Common Commands

```bash
# Start all services
docker-compose up -d

# Restart a service
docker-compose restart backend

# View logs
docker logs cds_project-backend-1 --tail 50

# Stop all
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

---

## 💻 Development Workflow

### Initial Setup

```bash
# 1. Clone repository
git clone https://github.com/hoangop/CDS.git
cd CDS_project

# 2. Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Start Docker services
docker-compose up -d

# 5. Create database schema
./venv/bin/python data_pipeline/scripts/create_db.py

# 6. (Optional) Import data
./venv/bin/python data_pipeline/scripts/import_from_csv.py
./venv/bin/python data_pipeline/scripts/process_pdfs_to_db.py
./venv/bin/python data_pipeline/scripts/update_rankings.py
```

### Making Changes

#### Frontend Changes

1. Edit files in `frontend/src/`
2. Frontend hot-reloads automatically (Next.js dev server)
3. If Dockerfile changed: `docker-compose up -d --build frontend`

#### Backend Changes

1. Edit files in `backend/app/`
2. Restart backend: `docker-compose restart backend`
3. If requirements.txt changed: `docker-compose up -d --build backend`

#### Database Schema Changes

1. Edit `data_pipeline/scripts/create_db.py`
2. Run: `./venv/bin/python data_pipeline/scripts/create_db.py`
3. Update `backend/app/models/cds.py` to match new schema
4. Restart backend: `docker-compose restart backend`

### Testing

```bash
# Test entire system
./venv/bin/python test_system.py

# Test API directly
curl http://localhost:8000/api/v1/schools?limit=5 | python3 -m json.tool

# Test frontend
open http://localhost:3000
```

---

## 📝 Coding Conventions

### Python (Backend + Scripts)

- **Style:** PEP 8
- **Naming:**
  - Functions: `snake_case` (e.g., `get_schools_to_update()`)
  - Classes: `PascalCase` (e.g., `Institution_Master`)
  - Constants: `UPPER_SNAKE_CASE` (e.g., `DATABASE_URL`)
- **Type Hints:** Use for function parameters and returns
- **Docstrings:** Use for all public functions

```python
def get_schools(
    q: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[SchoolListItem]:
    """
    Lấy danh sách trường kèm số liệu tuyển sinh cơ bản.
    
    Args:
        q: Search query
        limit: Max results
        db: Database session
    
    Returns:
        List of SchoolListItem objects
    """
```

### TypeScript (Frontend)

- **Style:** Standard TypeScript conventions
- **Naming:**
  - Components: `PascalCase` (e.g., `Navbar`)
  - Functions: `camelCase` (e.g., `calcRate`)
  - Types/Interfaces: `PascalCase` (e.g., `School`)
  - Constants: `camelCase` or `UPPER_SNAKE_CASE`
- **Interfaces:** Define for all data structures

```typescript
interface School {
  institution_id: string;
  name: string;
  rank_2025?: number;
  rank_type?: string;
}
```

### Git Commits

- **Format:** `<type>: <description>`
- **Types:**
  - `feat`: New feature
  - `fix`: Bug fix
  - `refactor`: Code refactoring
  - `docs`: Documentation
  - `style`: Formatting, CSS
  - `chore`: Maintenance, dependencies

**Examples:**
```
feat: Add pagination to home page
fix: Correct international acceptance rate calculation
refactor: Extract API helpers to lib/api.ts
```

---

## 🔍 Common Issues & Solutions

### Issue: Backend returns 500 Internal Server Error

**Cause:** Model mismatch between SQLAlchemy and database schema.

**Solution:**
1. Check backend logs: `docker logs cds_project-backend-1 --tail 50`
2. Ensure `backend/app/models/cds.py` matches DB schema
3. Restart backend: `docker-compose restart backend`

### Issue: Frontend shows "No schools found"

**Cause:** API not returning data or CORS issue.

**Solution:**
1. Check API: `curl http://localhost:8000/api/v1/schools?limit=5`
2. Verify CORS is enabled in `backend/app/main.py`
3. Check browser console for errors

### Issue: update_rankings.py fails with timeout

**Cause:** Google/US News detected bot and blocked requests.

**Solution:**
1. Wait 1+ hours before retrying
2. Reduce `limit` in script (e.g., 5 schools at a time)
3. Use longer delays: increase `time.sleep()` values
4. Consider using a proxy service

### Issue: Pydantic validation error

**Cause:** Using Pydantic v1 syntax with v2 library.

**Solution:**
Replace:
- `orm_mode = True` → `model_config = ConfigDict(from_attributes=True)`
- `.from_orm()` → `.model_validate()`
- `.dict()` → `.model_dump()`

---

## 🌐 Environment Variables

### Backend

```bash
# Database connection
DATABASE_URL=postgresql://postgres:postgres@db:5432/cds_db

# (Production only)
ALLOWED_ORIGINS=https://cds-analytics.com
```

### Frontend

```bash
# API URL (must start with NEXT_PUBLIC_ to be accessible in browser)
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Data Pipeline

```bash
# Google Gemini API key
GOOGLE_API_KEY=AIzaSy...

# Database (if running outside Docker)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=cds_db
DB_USER=postgres
DB_PASSWORD=postgres
```

---

## 📚 Dependencies

### Backend (`backend/requirements.txt`)

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
```

### Frontend (`frontend/package.json`)

```json
{
  "dependencies": {
    "next": "14.0.3",
    "react": "^18",
    "react-dom": "^18"
  },
  "devDependencies": {
    "typescript": "^5",
    "tailwindcss": "^3",
    "autoprefixer": "^10",
    "postcss": "^8"
  }
}
```

### Data Pipeline (`requirements.txt`)

```
requests==2.32.3
beautifulsoup4==4.12.2
pandas==2.1.3
lxml==4.9.3
psycopg2-binary==2.9.9
google-generativeai==0.3.1
playwright==1.40.0
pillow==10.1.0
googlesearch-python==1.2.3
```

---

## 🚀 Future Enhancements

### Planned Features

1. **Comparison Tool:**
   - Side-by-side comparison of 2-5 schools
   - Acceptance rate trends over years
   - International student percentage

2. **Student Mapping:**
   - Visualize student data by country/region
   - Interactive map showing international student distribution

3. **Advanced Filters:**
   - Filter by rank range
   - Filter by acceptance rate
   - Filter by region/state
   - Filter by public/private

4. **User Accounts:**
   - Save favorite schools
   - Create custom comparison lists
   - Export data to PDF/CSV

5. **Historical Data:**
   - Track rank changes over years
   - Acceptance rate trends
   - Application volume trends

### Technical Improvements

1. **Backend:**
   - Add Redis caching for frequently accessed data
   - Implement pagination at database level (not client-side)
   - Add rate limiting middleware
   - Create automated tests (pytest)

2. **Frontend:**
   - Server-side rendering for better SEO
   - Add loading skeletons
   - Implement infinite scroll as pagination alternative
   - Add dark mode toggle

3. **Data Pipeline:**
   - Automate daily scraping (cron jobs)
   - Add data validation and quality checks
   - Create retry mechanism for failed scrapes
   - Store PDF files in S3

4. **DevOps:**
   - CI/CD pipeline (GitHub Actions)
   - Automated database backups
   - Monitoring and alerting (CloudWatch)
   - Load testing

---

## 📞 Support & Maintenance

### Database Maintenance

```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('cds_db'));

-- Count records
SELECT 
  (SELECT COUNT(*) FROM institution_master) as total_schools,
  (SELECT COUNT(*) FROM institution_master WHERE rank_2025 IS NOT NULL) as ranked_schools,
  (SELECT COUNT(*) FROM admission_c) as admission_records;

-- Find schools without data
SELECT name 
FROM institution_master im
LEFT JOIN admission_c ac ON im.institution_id = ac.institution_id
WHERE ac.institution_id IS NULL;
```

### Logs

```bash
# Backend API logs
docker logs cds_project-backend-1 -f

# Frontend logs
docker logs cds_project-frontend-1 -f

# Database logs
docker logs cds_project-db-1 -f
```

### Backup Database

```bash
# Export
docker exec cds_project-db-1 pg_dump -U postgres cds_db > backup.sql

# Import
docker exec -i cds_project-db-1 psql -U postgres cds_db < backup.sql
```

---

## 📖 Additional Resources

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Next.js Docs:** https://nextjs.org/docs
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/
- **Pydantic v2 Migration:** https://docs.pydantic.dev/latest/migration/
- **TailwindCSS Docs:** https://tailwindcss.com/docs
- **Google Gemini API:** https://ai.google.dev/docs
- **Common Data Set Initiative:** https://commondataset.org/

---

**Last Updated:** December 2024  
**Version:** 1.0  
**Maintainer:** hoangop@github

