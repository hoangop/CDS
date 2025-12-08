import os
import time
import json
import re
import tempfile
import psycopg2
import requests
import pandas as pd
import google.generativeai as genai
import typing_extensions as typing
from bs4 import BeautifulSoup

# --- CẤU HÌNH API ---
API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyAFm53agSZhTicTqLYzuiQG7ZwPmpvZpf8")
genai.configure(api_key=API_KEY)

# --- CẤU HÌNH DB ---
DB_CONFIG = {
    "dbname": "cds_db",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5432"
}

# Schema for Gemini
class InternationalAdmission(typing.TypedDict):
    total_applicants_international: int
    total_admitted_international: int
    total_enrolled_international: int

def slugify(text, max_length=50):
    """Tạo ID đơn giản từ tên trường, truncate nếu quá dài."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text)
    if len(text) > max_length:
        text = text[:max_length]
    return text

def download_pdf_to_temp(url, school_name):
    """Download PDF từ URL vào temp file và trả về path."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    
    try:
        # Xử lý link Google Drive và Docs
        if "drive.google.com" in url or "docs.google.com" in url:
            file_id_match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
            if not file_id_match:
                file_id_match = re.search(r'id=([a-zA-Z0-9_-]+)', url)
            
            if file_id_match:
                file_id = file_id_match.group(1)
                url = f"https://drive.google.com/uc?export=download&id={file_id}"

        response = session.get(url, timeout=30, allow_redirects=True)
        
        # Kiểm tra Content-Type
        content_type = response.headers.get('Content-Type', '').lower()
        
        if response.status_code == 200:
            # Nếu nội dung quá nhỏ (< 2KB) và là HTML -> Có thể là trang lỗi
            if len(response.content) < 2000 and 'html' in content_type:
                print(f"  -> Cảnh báo: File tải về có vẻ là HTML lỗi ({len(response.content)} bytes).")
                return None

            # Tạo temp file
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', school_name)
            temp_file = tempfile.NamedTemporaryFile(
                mode='wb', 
                suffix='.pdf', 
                prefix=f'cds_{safe_name}_',
                delete=False
            )
            temp_file.write(response.content)
            temp_file.close()
            
            return temp_file.name
        else:
            print(f"  -> Lỗi tải {response.status_code}")
            return None
            
    except Exception as e:
        print(f"  -> Lỗi download: {e}")
        return None

def upload_to_gemini(path, mime_type="application/pdf"):
    """Uploads the given file to Gemini."""
    file = genai.upload_file(path, mime_type=mime_type)
    return file

def wait_for_files_active(files):
    """Waits for the given files to be active."""
    for name in (file.name for file in files):
        file = genai.get_file(name)
        while file.state.name == "PROCESSING":
            time.sleep(1)
            file = genai.get_file(name)
        if file.state.name != "ACTIVE":
            raise Exception(f"File {file.name} failed to process")

def parse_pdf_with_gemini_file_api(pdf_path):
    """Parse PDF với Gemini File API."""
    # 1. Upload File
    try:
        pdf_file = upload_to_gemini(pdf_path, mime_type="application/pdf")
    except Exception as e:
        print(f"Lỗi upload: {e}")
        return None

    # 2. Wait
    wait_for_files_active([pdf_file])

    # 3. Generate Content
    model_name = "gemini-2.0-flash-exp"
    model = genai.GenerativeModel(model_name=model_name)

    prompt = """
    You are a data extractor analyzing a university Common Data Set (CDS) document.
    
    TASK: Locate Table C1 "First-Time, First-Year Student Applicants".
    
    ACTION: Extract the ENTIRE table content into a structured JSON object.
    
    Return a JSON with this exact structure:
    {
        "applied": {
            "total": 0,
            "in_state": 0,
            "out_of_state": 0,
            "international": 0,
            "unknown": 0
        },
        "admitted": {
            "total": 0,
            "in_state": 0,
            "out_of_state": 0,
            "international": 0,
            "unknown": 0
        },
        "enrolled": {
            "total": 0,
            "in_state": 0,
            "out_of_state": 0,
            "international": 0,
            "unknown": 0
        }
    }
    
    IMPORTANT: 
    - Extract ALL numbers from the table.
    - If a cell is empty, use 0.
    - Remove commas from numbers (e.g. "1,200" -> 1200).
    """

    try:
        response = model.generate_content([pdf_file, prompt], 
                                        generation_config={"temperature": 0.0, "response_mime_type": "application/json"})
        
        # Clean up: Delete file from Gemini after processing
        try:
            genai.delete_file(pdf_file.name)
        except:
            pass  # Ignore cleanup errors
        
        return json.loads(response.text)
    except Exception as e:
        print(f"Lỗi parse: {e}")
        # Clean up on error too
        try:
            genai.delete_file(pdf_file.name)
        except:
            pass
        return None

def upsert_to_db(school_name, data, year="2024-2025"):
    """Lưu dữ liệu vào Database."""
    if not data:
        return False

    # Kiểm tra xem có data thực sự không (ít nhất 1 số > 0)
    total_apps = data.get("applied", {}).get("total", 0) or 0
    total_adm = data.get("admitted", {}).get("total", 0) or 0
    total_enr = data.get("enrolled", {}).get("total", 0) or 0
    
    # Nếu tất cả đều 0, không insert
    if total_apps == 0 and total_adm == 0 and total_enr == 0:
        return False

    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Tạo ID từ tên trường (truncate nếu quá dài)
        inst_id = slugify(school_name, max_length=50)
        
        # Kiểm tra xem đã có institution với cùng tên chưa (để tránh duplicate)
        cur.execute("""
            SELECT Institution_ID FROM Institution_Master 
            WHERE Name = %s 
            LIMIT 1;
        """, (school_name,))
        existing = cur.fetchone()
        
        if existing:
            # Nếu đã có, dùng ID cũ (có thể là ID số từ Scorecard)
            inst_id = existing[0]
        else:
            # Nếu chưa có, tạo mới với slug ID
            cur.execute("""
                INSERT INTO Institution_Master (Institution_ID, Name)
                VALUES (%s, %s)
                ON CONFLICT (Institution_ID) DO UPDATE SET Name = EXCLUDED.Name;
            """, (inst_id, school_name))
        
        # 2. Upsert Admission_C
        cur.execute("""
            INSERT INTO Admission_C (
                Institution_ID, Academic_Year,
                Total_Applicants, Total_Admitted, Total_Enrolled,
                Applicants_International, Admitted_International, Enrolled_International
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (Institution_ID, Academic_Year) 
            DO UPDATE SET
                Total_Applicants = EXCLUDED.Total_Applicants,
                Total_Admitted = EXCLUDED.Total_Admitted,
                Total_Enrolled = EXCLUDED.Total_Enrolled,
                Applicants_International = EXCLUDED.Applicants_International,
                Admitted_International = EXCLUDED.Admitted_International,
                Enrolled_International = EXCLUDED.Enrolled_International;
        """, (
            inst_id, year,
            total_apps,
            total_adm,
            total_enr,
            data.get("applied", {}).get("international", 0) or 0,
            data.get("admitted", {}).get("international", 0) or 0,
            data.get("enrolled", {}).get("international", 0) or 0
        ))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Lỗi DB ({school_name}): {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def get_cds_links_from_web(target_year="2024-25"):
    """Lấy danh sách CDS links trực tiếp từ website."""
    url = "https://www.collegetransitions.com/dataverse/common-data-set-repository"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }

    print(f"Đang truy cập: {url}...")
    try:
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        if response.encoding is None or response.encoding == 'ISO-8859-1':
            response.encoding = response.apparent_encoding
            
    except requests.exceptions.RequestException as e:
        print(f"Lỗi kết nối: {e}")
        return []

    print(f"Tải thành công. Kích thước: {len(response.text)} ký tự.")
    
    try:
        soup = BeautifulSoup(response.text, 'lxml')
    except Exception:
        soup = BeautifulSoup(response.text, 'html.parser')
    
    # Tìm bảng dữ liệu
    table = soup.find('table')
    
    if not table:
        print("Không tìm thấy thẻ <table>.")
        return []

    # Tìm dòng header
    headers_row = table.find('thead')
    if headers_row:
        headers_row = headers_row.find('tr')
    else:
        headers_row = table.find('tr')

    if not headers_row:
        print("Không tìm thấy dòng header trong bảng.")
        return []

    columns = headers_row.find_all(['th', 'td'])
    col_names = [col.get_text(strip=True) for col in columns]
    print(f"Các cột: {col_names}")

    target_col_index = -1
    
    # Tìm cột chứa năm
    for i, col in enumerate(col_names):
        if target_year in col or (target_year.replace("-", "") in col.replace("-", "")):
            target_col_index = i
            print(f"-> Chọn cột '{col}' (Index: {i})")
            break
            
    if target_col_index == -1:
        print(f"Không tìm thấy cột cho năm {target_year}. Các cột hiện có: {col_names}")
        # Thử tìm cột chứa "2024" bất kỳ
        for i, col in enumerate(col_names):
            if "2024" in col:
                target_col_index = i
                print(f"-> Fallback: Chọn cột '{col}' (Index: {i})")
                break
        
        if target_col_index == -1:
            return []

    # Quét dữ liệu
    results = []
    rows = table.find_all('tr')
    
    if rows and rows[0].get_text(strip=True) == headers_row.get_text(strip=True):
        rows = rows[1:]
        
    print(f"Đang xử lý {len(rows)} dòng dữ liệu...")

    for row in rows:
        cells = row.find_all(['td', 'th'])
        if not cells: 
            continue
            
        school_name = cells[0].get_text(strip=True)
        if not school_name: 
            continue

        try:
            target_cell = cells[target_col_index]
            link_tag = target_cell.find('a')
            
            pdf_url = ""
            if link_tag and link_tag.has_attr('href'):
                pdf_url = link_tag['href']

            if pdf_url:
                results.append({
                    "School Name": school_name,
                    "CDS URL": pdf_url,
                    "Year": target_year
                })
        except IndexError:
            continue

    if results:
        print(f"\n✅ Đã lấy được {len(results)} trường từ website.")
        return results
    else:
        print("Không tìm thấy link nào.")
        return []

def process_links_to_db(links_data, year="2024-25"):
    """Xử lý danh sách links và update DB."""
    if not links_data:
        print("Không có dữ liệu để xử lý.")
        return

    total_files = len(links_data)
    success_count = 0
    error_count = 0
    skip_count = 0
    
    print(f"\n{'SCHOOL NAME':<35} | {'TTL APP':<8} | {'TTL ADM':<8} | {'INT APP':<8} | {'INT ADM':<8} | {'INT RATE':<8} | {'STATUS':<10}")
    print("-" * 120)

    for index, item in enumerate(links_data):
        url = item['CDS URL']
        school_name = item['School Name']
        csv_year = item.get('Year', year)
        
        if not url or not str(url).startswith('http'):
            print(f"[{index+1}/{total_files}] {school_name[:33]:<35} | {'SKIP':<8} | {'SKIP':<8} | {'SKIP':<8} | {'SKIP':<8} | {'SKIP':<8} | {'NO URL':<10}")
            skip_count += 1
            continue

        display_name = school_name[:33]
        progress = f"[{index+1}/{total_files}]"
        
        # Download PDF vào temp file
        print(f"{progress} Đang tải PDF: {display_name}...", end=" ", flush=True)
        temp_pdf_path = download_pdf_to_temp(url, school_name)
        
        if not temp_pdf_path:
            print(f"{'ERR':<8} | {'ERR':<8} | {'ERR':<8} | {'ERR':<8} | {'ERR':<8} | {'DOWNLOAD FAIL':<10}")
            error_count += 1
            continue

        try:
            # Parse với Gemini
            result = parse_pdf_with_gemini_file_api(temp_pdf_path)
            
            # Sleep để tránh rate limit
            time.sleep(2)
            
            db_status = "SKIP"
            total_apps = 0
            total_adm = 0
            int_apps = 0
            int_adm = 0
            rate_str = "N/A"

            if result:
                # Xử lý trường hợp Gemini trả về list
                if isinstance(result, list):
                    result = result[0] if len(result) > 0 else {}

                # Lấy data an toàn từ JSON nested
                total_apps = result.get("applied", {}).get("total", 0)
                total_adm = result.get("admitted", {}).get("total", 0)
                
                int_apps = result.get("applied", {}).get("international", 0)
                int_adm = result.get("admitted", {}).get("international", 0)
                
                if int_apps > 0 and int_adm > 0:
                    rate = (int_adm / int_apps) * 100
                    rate_str = f"{rate:.1f}%"
                elif int_apps > 0:
                    rate_str = "0.0%"
                
                # Lưu vào DB
                saved = upsert_to_db(school_name, result, csv_year)
                if saved:
                    db_status = "SAVED"
                    success_count += 1
                else:
                    db_status = "NO DATA"
                    error_count += 1

                print(f"{total_apps:<8} | {total_adm:<8} | {int_apps:<8} | {int_adm:<8} | {rate_str:<8} | {db_status:<10}")
            else:
                print(f"{'ERR':<8} | {'ERR':<8} | {'ERR':<8} | {'ERR':<8} | {'ERR':<8} | {'PARSE FAIL':<10}")
                error_count += 1
                
        except Exception as e:
            print(f"{'ERR':<8} | {'ERR':<8} | {'ERR':<8} | {'ERR':<8} | {'ERR':<8} | {f'ERROR: {str(e)[:8]}':<10}")
            error_count += 1
        finally:
            # Xóa temp file ngay sau khi xử lý xong
            try:
                if temp_pdf_path and os.path.exists(temp_pdf_path):
                    os.unlink(temp_pdf_path)
            except Exception as e:
                print(f"  (Cảnh báo: Không xóa được temp file: {e})")

    print("\n" + "="*120)
    print(f"HOÀN TẤT! Thành công: {success_count}, Lỗi: {error_count}, Bỏ qua: {skip_count}")
    print("="*120)

def process_csv_to_db(csv_file, year="2024-25"):
    """Đọc CSV với URLs, download PDF tạm thời, xử lý và update DB."""
    if not os.path.exists(csv_file):
        print(f"File {csv_file} không tồn tại.")
        return

    print(f"Đang đọc dữ liệu từ {csv_file}...")
    df = pd.read_csv(csv_file)
    
    if 'CDS URL' not in df.columns or 'School Name' not in df.columns:
        print("File CSV thiếu cột 'CDS URL' hoặc 'School Name'.")
        return

    total_files = len(df)
    success_count = 0
    error_count = 0
    skip_count = 0
    
    print(f"\n{'SCHOOL NAME':<35} | {'TTL APP':<8} | {'TTL ADM':<8} | {'INT APP':<8} | {'INT ADM':<8} | {'INT RATE':<8} | {'STATUS':<10}")
    print("-" * 120)

    for index, row in df.iterrows():
        url = row['CDS URL']
        school_name = row['School Name']
        csv_year = row['Year'] if 'Year' in row else year
        
        if pd.isna(url) or not str(url).startswith('http'):
            print(f"[{index+1}/{total_files}] {school_name[:33]:<35} | {'SKIP':<8} | {'SKIP':<8} | {'SKIP':<8} | {'SKIP':<8} | {'SKIP':<8} | {'NO URL':<10}")
            skip_count += 1
            continue

        display_name = school_name[:33]
        progress = f"[{index+1}/{total_files}]"
        
        # Download PDF vào temp file
        print(f"{progress} Đang tải PDF: {display_name}...", end=" ", flush=True)
        temp_pdf_path = download_pdf_to_temp(url, school_name)
        
        if not temp_pdf_path:
            print(f"{'ERR':<8} | {'ERR':<8} | {'ERR':<8} | {'ERR':<8} | {'ERR':<8} | {'DOWNLOAD FAIL':<10}")
            error_count += 1
            continue

        try:
            # Parse với Gemini
            result = parse_pdf_with_gemini_file_api(temp_pdf_path)
            
            # Sleep để tránh rate limit
            time.sleep(2)
            
            db_status = "SKIP"
            total_apps = 0
            total_adm = 0
            int_apps = 0
            int_adm = 0
            rate_str = "N/A"

            if result:
                # Xử lý trường hợp Gemini trả về list
                if isinstance(result, list):
                    result = result[0] if len(result) > 0 else {}

                # Lấy data an toàn từ JSON nested
                total_apps = result.get("applied", {}).get("total", 0)
                total_adm = result.get("admitted", {}).get("total", 0)
                
                int_apps = result.get("applied", {}).get("international", 0)
                int_adm = result.get("admitted", {}).get("international", 0)
                
                if int_apps > 0 and int_adm > 0:
                    rate = (int_adm / int_apps) * 100
                    rate_str = f"{rate:.1f}%"
                elif int_apps > 0:
                    rate_str = "0.0%"
                
                # Lưu vào DB
                saved = upsert_to_db(school_name, result, csv_year)
                if saved:
                    db_status = "SAVED"
                    success_count += 1
                else:
                    db_status = "NO DATA"
                    error_count += 1

                print(f"{total_apps:<8} | {total_adm:<8} | {int_apps:<8} | {int_adm:<8} | {rate_str:<8} | {db_status:<10}")
            else:
                print(f"{'ERR':<8} | {'ERR':<8} | {'ERR':<8} | {'ERR':<8} | {'ERR':<8} | {'PARSE FAIL':<10}")
                error_count += 1
                
        except Exception as e:
            print(f"{'ERR':<8} | {'ERR':<8} | {'ERR':<8} | {'ERR':<8} | {'ERR':<8} | {f'ERROR: {str(e)[:8]}':<10}")
            error_count += 1
        finally:
            # Xóa temp file ngay sau khi xử lý xong
            try:
                if temp_pdf_path and os.path.exists(temp_pdf_path):
                    os.unlink(temp_pdf_path)
            except Exception as e:
                print(f"  (Cảnh báo: Không xóa được temp file: {e})")

    print("\n" + "="*120)
    print(f"HOÀN TẤT! Thành công: {success_count}, Lỗi: {error_count}, Bỏ qua: {skip_count}")
    print("="*120)

if __name__ == "__main__":
    import sys
    
    year = "2024-25"
    
    # Cho phép truyền CSV file từ command line
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        year = sys.argv[2] if len(sys.argv) > 2 else "2024-25"
        process_csv_to_db(csv_file, year)
    else:
        # Nếu không có CSV, tự động lấy links từ website
        print("="*60)
        print("Không có file CSV. Đang lấy links trực tiếp từ website...")
        print("="*60)
        
        links_data = get_cds_links_from_web(target_year=year)
        
        if links_data:
            print(f"\nBắt đầu xử lý {len(links_data)} trường...")
            process_links_to_db(links_data, year)
        else:
            # Fallback: Tìm file CSV mới nhất nếu có
            csv_files = [f for f in os.listdir('.') if f.startswith('CDS_Links_') and f.endswith('.csv')]
            if csv_files:
                csv_file = max(csv_files, key=os.path.getctime)
                print(f"\nKhông lấy được từ web. Sử dụng file CSV mới nhất: {csv_file}")
                process_csv_to_db(csv_file, year)
            else:
                print("\n❌ Không tìm thấy dữ liệu. Vui lòng:")
                print("  1. Chạy script với file CSV: python process_direct_pdf_to_db.py <csv_file> [year]")
                print("  2. Hoặc đảm bảo website có thể truy cập được.")
                sys.exit(1)

