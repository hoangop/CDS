import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import os

def sanitize_filename(name):
    """Chuyển đổi tên trường thành tên file hợp lệ"""
    # Thay thế các ký tự không hợp lệ bằng gạch dưới
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def download_cds_files(csv_file):
    """Tải file PDF từ danh sách trong CSV và cập nhật đường dẫn local"""
    if not os.path.exists(csv_file):
        print(f"File {csv_file} không tồn tại.")
        return

    print(f"Đang đọc dữ liệu từ {csv_file}...")
    df = pd.read_csv(csv_file)
    
    if 'CDS URL' not in df.columns or 'School Name' not in df.columns:
        print("File CSV thiếu cột 'CDS URL' hoặc 'School Name'.")
        return

    # Tạo thư mục data nếu chưa có
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    print(f"Thư mục lưu trữ: {data_dir}")
    
    # Thêm cột Local Path nếu chưa có
    if 'Local Path' not in df.columns:
        df['Local Path'] = ''

    total_files = len(df)
    success_count = 0
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    for index, row in df.iterrows():
        url = row['CDS URL']
        school_name = row['School Name']
        year = row['Year'] if 'Year' in row else 'Unknown'
        
        if pd.isna(url) or not str(url).startswith('http'):
            print(f"[{index+1}/{total_files}] Bỏ qua {school_name}: Link không hợp lệ.")
            continue
            
        # Tạo tên file: TenTruong_Nam.pdf
        safe_name = sanitize_filename(school_name)
        filename = f"{safe_name}_{sanitize_filename(str(year))}.pdf"
        local_path = os.path.join(data_dir, filename)
        
        # Kiểm tra nếu file đã tồn tại để tránh tải lại (tùy chọn)
        if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
             print(f"[{index+1}/{total_files}] Đã tồn tại: {filename}")
             df.at[index, 'Local Path'] = local_path
             success_count += 1
             continue

        print(f"[{index+1}/{total_files}] Đang tải: {filename}...")
        
        try:
            # Xử lý link Google Drive và Docs
            if "drive.google.com" in url or "docs.google.com" in url:
                # Chuyển link view sang link export download
                file_id_match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
                if not file_id_match:
                    # Thử tìm id trong pattern khác của docs
                    file_id_match = re.search(r'id=([a-zA-Z0-9_-]+)', url)
                
                if file_id_match:
                    file_id = file_id_match.group(1)
                    # URL export chuẩn cho cả Docs và Drive
                    url = f"https://drive.google.com/uc?export=download&id={file_id}"

            response = session.get(url, timeout=30, allow_redirects=True)
            
            # Kiểm tra Content-Type
            content_type = response.headers.get('Content-Type', '').lower()
            
            if response.status_code == 200:
                # Nếu nội dung quá nhỏ (< 2KB) và là HTML -> Có thể là trang lỗi hoặc redirect chưa xong
                if len(response.content) < 2000 and 'html' in content_type:
                    print(f"  -> Cảnh báo: File tải về có vẻ là HTML lỗi ({len(response.content)} bytes). Bỏ qua.")
                    continue

                with open(local_path, 'wb') as f:
                    f.write(response.content)
                
                df.at[index, 'Local Path'] = local_path
                success_count += 1
                # Delay nhỏ
                time.sleep(0.5)
            else:
                print(f"  -> Lỗi tải {response.status_code}")
                
        except Exception as e:
            print(f"  -> Lỗi: {e}")

    # Lưu lại file CSV cập nhật
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"\nHoàn tất! Đã tải {success_count}/{total_files} file.")
    print(f"File CSV đã được cập nhật: {csv_file}")

def get_cds_links(target_year="2024-25"):
    # URL của trang Repository (College Transitions)
    url = "https://www.collegetransitions.com/dataverse/common-data-set-repository"
    
    # Header giả lập trình duyệt đầy đủ
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }

    print(f"Đang truy cập: {url}...")
    try:
        # Sử dụng session
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        # Xử lý encoding
        if response.encoding is None or response.encoding == 'ISO-8859-1':
            response.encoding = response.apparent_encoding
            
    except requests.exceptions.RequestException as e:
        print(f"Lỗi kết nối: {e}")
        return

    # In thông tin debug
    print(f"Tải thành công. Kích thước: {len(response.text)} ký tự.")
    
    # Sử dụng lxml để parse tốt hơn
    try:
        soup = BeautifulSoup(response.text, 'lxml')
    except Exception:
        soup = BeautifulSoup(response.text, 'html.parser')
    
    # --- TÌM BẢNG DỮ LIỆU ---
    # Thử tìm thẻ table trước
    table = soup.find('table')
    
    # Nếu không thấy table, tìm xem có phải nội dung bị ẩn trong script hay div khác không
    if not table:
        print("Không tìm thấy thẻ <table>.")
        # Logic mở rộng: Có thể trang dùng div làm bảng hoặc render bằng JS
        # Tìm div có class chứa 'table' hoặc 'grid'
        candidates = soup.find_all('div', class_=re.compile(r'table|grid', re.I))
        print(f"Tìm thấy {len(candidates)} thẻ div có class chứa 'table'/'grid'.")
        
        # Debug: In ra 500 ký tự đầu của body để xem cấu trúc
        body = soup.find('body')
        if body:
            print(f"Cấu trúc body (500 chars): {body.get_text()[:500]}...")
        return

    # --- XỬ LÝ HEADER ---
    # Tìm dòng header
    headers_row = table.find('thead')
    if headers_row:
        headers_row = headers_row.find('tr')
    else:
        # Nếu không có thead, lấy dòng đầu tiên của tbody hoặc table
        headers_row = table.find('tr')

    if not headers_row:
        print("Không tìm thấy dòng header trong bảng.")
        return

    columns = headers_row.find_all(['th', 'td'])
    col_names = [col.get_text(strip=True) for col in columns]
    print(f"Các cột: {col_names}")

    target_col_index = -1
    
    # Tìm cột chứa năm (ví dụ "2024-25")
    # Lưu ý: Tìm string chứa "2024" và "25" hoặc khớp chính xác
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
             return

    # --- QUÉT DỮ LIỆU ---
    results = []
    # Lấy tất cả các dòng, bỏ qua dòng header
    rows = table.find_all('tr')
    
    # Bỏ dòng đầu nếu nó là header (so sánh nội dung text)
    if rows and rows[0].get_text(strip=True) == headers_row.get_text(strip=True):
        rows = rows[1:]
        
    print(f"Đang xử lý {len(rows)} dòng dữ liệu...")

    for row in rows:
        cells = row.find_all(['td', 'th'])
        if not cells: 
            continue
            
        # Cột 0 là tên trường
        school_name = cells[0].get_text(strip=True)
        if not school_name: continue

        try:
            target_cell = cells[target_col_index]
            # Link thường nằm trong thẻ <a>
            link_tag = target_cell.find('a')
            
            pdf_url = ""
            if link_tag and link_tag.has_attr('href'):
                pdf_url = link_tag['href']
                
                # Xử lý link Google Drive redirect nếu cần (tùy chọn)
                if "google.com/url" in pdf_url:
                     # Đôi khi link là redirect của google, nhưng ta cứ lấy raw link trước
                     pass

            if pdf_url:
                results.append({
                    "School Name": school_name,
                    "CDS URL": pdf_url,
                    "Year": target_year
                })
        except IndexError:
            continue

    # --- LƯU FILE ---
    if results:
        df = pd.DataFrame(results)
        filename = f"CDS_Links_{target_year.replace('-', '_')}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\nThành công! Đã lấy được {len(results)} trường.")
        print(f"Lưu tại: {filename}")
        print(df.head())
        
        # Hỏi user có muốn tải file luôn không
        # Trong môi trường script tự động, ta có thể gọi luôn
        print("\nBắt đầu tải các file PDF...")
        download_cds_files(filename)
        
    else:
        print("Không tìm thấy link nào.")

if __name__ == "__main__":
    # Cập nhật năm mục tiêu thành '2024-25' theo format của web
    get_cds_links(target_year="2024-25")