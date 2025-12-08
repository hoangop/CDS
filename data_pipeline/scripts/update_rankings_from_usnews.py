import os
import re
import time
import requests
import psycopg2
from bs4 import BeautifulSoup
from urllib.parse import quote

# Cấu hình DB
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "cds_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

# Headers để tránh bị block
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

def create_rank_column():
    """Thêm cột rank_2025 và các cột khác nếu chưa có."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Kiểm tra và thêm các cột
        columns_to_add = [
            ("rank_2025", "INTEGER"),
            ("state", "VARCHAR(50)"),
            ("city", "VARCHAR(100)"),
            ("institution_type", "VARCHAR(100)")
        ]
        
        for col_name, col_type in columns_to_add:
            # Kiểm tra cột đã tồn tại chưa
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='institution_master' 
                AND column_name=%s
            """, (col_name,))
            
            if not cur.fetchone():
                print(f"Adding column: {col_name} {col_type}")
                cur.execute(f"ALTER TABLE institution_master ADD COLUMN {col_name} {col_type}")
            else:
                print(f"Column {col_name} already exists")
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database schema updated!")
        return True
        
    except Exception as e:
        print(f"❌ Error updating schema: {e}")
        return False

def slugify_school_name(name):
    """Convert school name to URL slug (giống USNews format)."""
    # Lowercase và remove special characters
    slug = name.lower()
    
    # Replace & with and
    slug = slug.replace('&', 'and')
    
    # Remove all non-alphanumeric except spaces and hyphens
    slug = re.sub(r'[^\w\s-]', '', slug)
    
    # Replace spaces and multiple hyphens with single hyphen
    slug = re.sub(r'[-\s]+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    return slug

def search_usnews_url(school_name):
    """Search USNews để tìm URL của school."""
    try:
        # Try direct URL first
        slug = slugify_school_name(school_name)
        
        # USNews URLs thường có format: /best-colleges/{slug}-{id}
        # Nhưng chúng ta không có ID, nên search trước
        search_url = f"https://www.usnews.com/best-colleges/search?name={quote(school_name)}"
        
        session = requests.Session()
        response = session.get(search_url, headers=HEADERS, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Tìm link đến school page
            # USNews search results thường có links dạng /best-colleges/{slug}
            links = soup.find_all('a', href=re.compile(r'/best-colleges/[^/]+$'))
            
            if links:
                school_url = "https://www.usnews.com" + links[0]['href']
                return school_url
        
        return None
        
    except Exception as e:
        print(f"  Error searching: {e}")
        return None

def scrape_usnews_data(url):
    """Scrape thông tin từ USNews school page."""
    try:
        session = requests.Session()
        response = session.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code != 200:
            print(f"  HTTP {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        data = {
            'rank': None,
            'city': None,
            'state': None,
            'type': None
        }
        
        # Extract rank
        # USNews thường có rank trong class như "RankList__Rank" hoặc text "Ranked #X"
        rank_patterns = [
            soup.find(text=re.compile(r'#\d+')),
            soup.find('div', class_=re.compile(r'rank', re.I)),
            soup.find('span', class_=re.compile(r'rank', re.I))
        ]
        
        for pattern in rank_patterns:
            if pattern:
                rank_text = pattern.get_text() if hasattr(pattern, 'get_text') else str(pattern)
                rank_match = re.search(r'#?(\d+)', rank_text)
                if rank_match:
                    data['rank'] = int(rank_match.group(1))
                    break
        
        # Extract location (city, state)
        # USNews thường có format "City, State" hoặc trong meta tags
        location_patterns = [
            soup.find('div', class_=re.compile(r'location', re.I)),
            soup.find('span', class_=re.compile(r'location', re.I)),
            soup.find(text=re.compile(r',\s*[A-Z]{2}'))  # Pattern: City, ST
        ]
        
        for pattern in location_patterns:
            if pattern:
                location_text = pattern.get_text() if hasattr(pattern, 'get_text') else str(pattern)
                # Try to parse "City, State" format
                location_match = re.search(r'([^,]+),\s*([A-Z]{2})', location_text)
                if location_match:
                    data['city'] = location_match.group(1).strip()
                    data['state'] = location_match.group(2).strip()
                    break
        
        # Extract institution type
        # USNews có categories như "Private", "Public", "Liberal Arts College"
        type_patterns = [
            soup.find('div', class_=re.compile(r'type|category', re.I)),
            soup.find(text=re.compile(r'Private|Public|Liberal Arts', re.I))
        ]
        
        for pattern in type_patterns:
            if pattern:
                type_text = pattern.get_text() if hasattr(pattern, 'get_text') else str(pattern)
                # Extract type keywords
                if 'Private' in type_text:
                    data['type'] = 'Private'
                elif 'Public' in type_text:
                    data['type'] = 'Public'
                if 'Liberal Arts' in type_text:
                    data['type'] = data.get('type', '') + ' Liberal Arts College'
                if data['type']:
                    break
        
        return data
        
    except Exception as e:
        print(f"  Error scraping: {e}")
        return None

def update_school_data(institution_id, data):
    """Update school data trong database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Build UPDATE query
        updates = []
        values = []
        
        if data.get('rank'):
            updates.append("rank_2025 = %s")
            values.append(data['rank'])
        
        if data.get('city'):
            updates.append("city = %s")
            values.append(data['city'])
        
        if data.get('state'):
            updates.append("state = %s")
            values.append(data['state'])
        
        if data.get('type'):
            updates.append("institution_type = %s")
            values.append(data['type'])
        
        if updates:
            values.append(institution_id)
            query = f"""
                UPDATE institution_master 
                SET {', '.join(updates)}
                WHERE institution_id = %s
            """
            cur.execute(query, values)
            conn.commit()
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"  Error updating DB: {e}")
        return False

def process_all_schools(limit=None):
    """Process tất cả schools trong database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Lấy danh sách schools chưa có rank
        query = """
            SELECT institution_id, name 
            FROM institution_master 
            WHERE rank_2025 IS NULL 
            ORDER BY name
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cur.execute(query)
        schools = cur.fetchall()
        
        cur.close()
        conn.close()
        
        print(f"\n{'='*80}")
        print(f"SCRAPING USNEWS RANKINGS FOR {len(schools)} SCHOOLS")
        print(f"{'='*80}\n")
        print(f"{'SCHOOL NAME':<40} | {'RANK':<6} | {'CITY':<15} | {'STATE':<6} | {'TYPE':<15}")
        print(f"{'-'*80}")
        
        success_count = 0
        fail_count = 0
        
        for idx, (institution_id, name) in enumerate(schools, 1):
            print(f"[{idx}/{len(schools)}] {name[:38]:<38} | ", end="", flush=True)
            
            # Search USNews URL
            url = search_usnews_url(name)
            
            if not url:
                print(f"{'N/A':<6} | {'N/A':<15} | {'N/A':<6} | {'URL NOT FOUND':<15}")
                fail_count += 1
                time.sleep(2)  # Rate limiting
                continue
            
            # Scrape data
            data = scrape_usnews_data(url)
            
            if data and any(data.values()):
                # Update database
                if update_school_data(institution_id, data):
                    rank_str = str(data.get('rank', 'N/A'))
                    city_str = data.get('city', 'N/A')[:15]
                    state_str = data.get('state', 'N/A')
                    type_str = data.get('type', 'N/A')[:15]
                    
                    print(f"{rank_str:<6} | {city_str:<15} | {state_str:<6} | {type_str:<15}")
                    success_count += 1
                else:
                    print(f"{'ERR':<6} | {'DB UPDATE FAILED':<15}")
                    fail_count += 1
            else:
                print(f"{'N/A':<6} | {'N/A':<15} | {'N/A':<6} | {'DATA NOT FOUND':<15}")
                fail_count += 1
            
            # Rate limiting - tránh bị block
            time.sleep(3)  # 3 seconds between requests
        
        print(f"\n{'='*80}")
        print(f"COMPLETED! Success: {success_count} | Failed: {fail_count}")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    print("🎓 USNews Rankings Scraper")
    print("=" * 60)
    
    # Step 1: Create columns
    print("\n📊 Step 1: Creating database columns...")
    if not create_rank_column():
        print("Failed to create columns. Exiting.")
        sys.exit(1)
    
    # Step 2: Process schools
    print("\n🔍 Step 2: Scraping USNews data...")
    
    # Allow limit from command line
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    
    if limit:
        print(f"Processing first {limit} schools...")
    else:
        print("Processing all schools...")
    
    process_all_schools(limit=limit)
    
    print("\n✅ Done!")

