import os
import time
import json
import re
import base64
import psycopg2
from duckduckgo_search import DDGS
from playwright.sync_api import sync_playwright
import google.generativeai as genai
from PIL import Image

# --- CẤU HÌNH ---
# API Key Gemini (Lấy từ biến môi trường hoặc hardcode tạm thời để test)
API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyAFm53agSZhTicTqLYzuiQG7ZwPmpvZpf8")
genai.configure(api_key=API_KEY)

DB_CONFIG = {
    "dbname": "cds_db",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5432"
}

# --- DATABASE FUNCTIONS ---

def setup_database():
    """Thêm cột Rank vào bảng Institution_Master nếu chưa có."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        print("Đang cập nhật Schema Database...")
        cur.execute("""
            ALTER TABLE Institution_Master 
            ADD COLUMN IF NOT EXISTS Rank_2025 INTEGER,
            ADD COLUMN IF NOT EXISTS Rank_Type VARCHAR(255);
        """)
        conn.commit()
        print("✓ Đã cập nhật Schema.")
    except Exception as e:
        print(f"❌ Lỗi Schema: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_schools_to_update(limit=10):
    """Lấy danh sách các trường chưa có Rank."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    # Ưu tiên các trường đã có dữ liệu tuyển sinh nhưng chưa có rank
    query = """
        SELECT im.Institution_ID, im.Name 
        FROM Institution_Master im
        JOIN Admission_C ac ON im.Institution_ID = ac.Institution_ID
        WHERE im.Rank_2025 IS NULL 
        AND ac.Total_Applicants > 0
        ORDER BY im.Name ASC
        LIMIT %s;
    """
    cur.execute(query, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def update_school_rank(inst_id, rank, rank_type):
    """Cập nhật rank vào DB."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE Institution_Master 
            SET Rank_2025 = %s, Rank_Type = %s
            WHERE Institution_ID = %s;
        """, (rank, rank_type, inst_id))
        conn.commit()
        print(f"✓ Đã lưu DB: {inst_id} -> #{rank} {rank_type}")
    except Exception as e:
        print(f"❌ Lỗi Update DB: {e}")
        conn.rollback()
    finally:
        conn.close()

# --- SEARCH & BROWSER FUNCTIONS ---

import requests
from bs4 import BeautifulSoup

def find_usnews_url_and_capture(school_name, output_path="temp_screenshot.png"):
    """Dùng Playwright để Search Google VÀ Chụp ảnh luôn (All-in-one)."""
    print(f"🔍 Searching & Capturing: {school_name}...")
    
    try:
        with sync_playwright() as p:
            # Giả lập browser mạnh hơn nữa
            browser = p.chromium.launch(headless=True, args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-position=0,0',
                '--ignore-certificate-errors',
                '--ignore-ssl-errors',
                '--disable-http2', # QUAN TRỌNG: Tắt HTTP2 để tránh lỗi protocol error
                '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            ])
            
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                locale="en-US",
                timezone_id="America/New_York",
                device_scale_factor=1,
                has_touch=False,
                is_mobile=False,
                java_script_enabled=True,
            )
            
            # Thêm headers giả lập
            context.set_extra_http_headers({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"macOS"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1"
            })

            # Script che dấu vết
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            """)
            
            page = context.new_page()
            
            # 1. Vào Google
            try:
                page.goto("https://www.google.com", timeout=30000)
            except Exception:
                print("   ⚠️ Lỗi truy cập Google, thử Bing...")
                page.goto("https://www.bing.com", timeout=30000)

            time.sleep(2)
            
            # 2. Search
            query = f"{school_name} us news ranking site:usnews.com/best-colleges"
            
            # Check xem đang ở Google hay Bing để fill đúng selector
            if "google" in page.url:
                page.fill("textarea[name='q']", query)
                page.press("textarea[name='q']", "Enter")
                page.wait_for_selector("#search", timeout=10000)
            else:
                page.fill("input[name='q']", query)
                page.press("input[name='q']", "Enter")
                time.sleep(3)
            
            time.sleep(2)
            
            # 3. Lấy link đầu tiên
            target_url = None
            
            # Logic lấy link cho cả Google và Bing
            links = page.locator("a[href*='usnews.com/best-colleges/']")
            count = links.count()
            
            for i in range(count):
                href = links.nth(i).get_attribute("href")
                if href and "rankings" not in href and "search" not in href and "google" not in href:
                    target_url = href
                    print(f"   -> Found URL: {target_url}")
                    break
            
            if not target_url:
                print("   ⚠️ Không tìm thấy link phù hợp.")
                browser.close()
                return False

            # 4. Vào trang đích
            print(f"   📸 Accessing: {target_url}")
            
            # Thử load trang với chiến thuật retry
            try:
                response = page.goto(target_url, timeout=60000, wait_until="domcontentloaded")
                if response and response.status == 403:
                    print("   ❌ Bị chặn 403 Forbidden.")
                    browser.close()
                    return False
            except Exception as e:
                print(f"   ❌ Lỗi load trang: {e}")
                browser.close()
                return False
            
            # Đợi load và bypass popup nếu có
            time.sleep(5)
            
            # Tắt popup quảng cáo nếu có (thử)
            try:
                page.evaluate("document.querySelectorAll('div[class*=\"popup\"], div[class*=\"modal\"]').forEach(el => el.remove());")
            except:
                pass

            # Cuộn trang để trigger lazy load
            page.mouse.wheel(0, 500)
            time.sleep(3)
            
            # Chụp ảnh
            page.screenshot(path=output_path, clip={"x": 0, "y": 0, "width": 1280, "height": 1200})
            print("   ✓ Đã chụp ảnh.")
            
            browser.close()
            return True
            
    except Exception as e:
        print(f"❌ Lỗi Browser: {e}")
        return False

# --- LLM EXTRACT FUNCTION ---

def extract_rank_from_image(image_path):
    """Gửi ảnh cho Gemini để lấy Rank và Type."""
    print("   🤖 Asking Gemini...")
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = """
        Look at this screenshot of a US News university profile page.
        Your task is to find the University Ranking information.
        
        1. Look for a large number preceded by a '#' symbol (e.g., #17, #1, #105). This is the rank.
        2. Look for the text immediately following or near that number (e.g., "National Universities", "Liberal Arts Colleges", "Regional Universities West"). This is the rank type.
        
        Return the result as a purely valid JSON object. Do not include markdown formatting.
        Format:
        {
            "rank": <integer or null>,
            "type": "<string or null>"
        }
        
        If you cannot find the rank, return null.
        """
        
        img = Image.open(image_path)
        response = model.generate_content([prompt, img])
        
        # Clean response text (remove markdown ```json ... ```)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
            
        data = json.loads(text)
        print(f"   -> Result: {data}")
        return data
    except Exception as e:
        print(f"   ❌ Lỗi LLM: {e}")
        return None

# --- MAIN FLOW ---

def main():
    setup_database()
    
    # Lấy danh sách trường cần update (tăng limit lên 50)
    schools = get_schools_to_update(limit=200)
    
    if not schools:
        print("Không có trường nào cần cập nhật.")
        return

    print(f"Đã tìm thấy {len(schools)} trường cần cập nhật rank.\n")

    for inst_id, name in schools:
        print("-" * 50)
        print(f"Đang xử lý: {name}")
        
        img_path = f"temp_rank_{inst_id}.png"
        
        # Gọi hàm All-in-one: Search + Capture
        success = find_usnews_url_and_capture(name, img_path)
        
        if success:
            # Trích xuất bằng AI
            result = extract_rank_from_image(img_path)
            
            # Cập nhật DB
            if result and result.get('rank'):
                update_school_rank(inst_id, result['rank'], result['type'])
            else:
                print("   ⚠️ Không trích xuất được rank từ ảnh.")
                
            # Dọn dẹp file ảnh
            if os.path.exists(img_path):
                os.remove(img_path)
        else:
            print("   ⚠️ Thất bại khi tìm kiếm/chụp ảnh.")
            
        # Nghỉ nhẹ
        time.sleep(2)

    print("\n================ DONE ================")

if __name__ == "__main__":
    main()

