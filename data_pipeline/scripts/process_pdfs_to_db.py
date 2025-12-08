import os
import time
import json
import re
import psycopg2
import google.generativeai as genai
import typing_extensions as typing

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
    # Truncate nếu quá dài
    if len(text) > max_length:
        text = text[:max_length]
    return text

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
        return json.loads(response.text)
    except Exception as e:
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

def main():
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'raw_data', 'pdfs')
    
    if not os.path.exists(data_dir):
        print("Không tìm thấy thư mục pdfs.")
        return

    pdf_files = [f for f in os.listdir(data_dir) if f.endswith('.pdf')]
    if not pdf_files:
        print("Không có file PDF nào.")
        return

    # SẮP XẾP FILE ĐỂ CHẠY CÓ THỨ TỰ
    pdf_files.sort()
    
    print(f"Bắt đầu xử lý toàn bộ {len(pdf_files)} file...")
    print(f"{'SCHOOL NAME':<35} | {'TTL APP':<8} | {'TTL ADM':<8} | {'INT APP':<8} | {'INT ADM':<8} | {'INT RATE':<8} | {'DB STATUS':<10}")
    print("-" * 120)

    success_count = 0
    error_count = 0

    for index, pdf_file in enumerate(pdf_files):
        full_path = os.path.join(data_dir, pdf_file)
        # Làm sạch tên trường
        school_name = pdf_file.replace('.pdf', '').replace('_2024-25', '').replace('_2024_25', '')
        display_name = school_name[:33]
        
        # Hiển thị tiến độ
        progress = f"[{index+1}/{len(pdf_files)}]"
        
        # Kiểm tra nếu đã có trong DB (Optional - để tiết kiệm API nếu chạy lại)
        # (Tạm thời chạy đè để update data mới nhất)

        result = parse_pdf_with_gemini_file_api(full_path)
        
        # Sleep để tránh rate limit (Gemini Flash Exp khá nhanh nhưng vẫn nên cẩn thận)
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
            
            # Lưu vào DB - chỉ báo SAVED nếu thực sự có data và commit thành công
            saved = upsert_to_db(school_name, result)
            if saved:
                db_status = "SAVED"
                success_count += 1
            else:
                db_status = "NO DATA"
                error_count += 1

            print(f"{display_name:<35} | {total_apps:<8} | {total_adm:<8} | {int_apps:<8} | {int_adm:<8} | {rate_str:<8} | {db_status:<10}")
        else:
            print(f"{display_name:<35} | {'ERR':<8} | {'ERR':<8} | {'ERR':<8} | {'ERR':<8} | {'ERR':<8} | {'FAIL':<10}")
            error_count += 1

    print("\n" + "="*50)
    print(f"HOÀN TẤT! Thành công: {success_count}, Lỗi: {error_count}")
    print("="*50)

if __name__ == "__main__":
    main()
