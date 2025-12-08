# CDS Project

## Setup

### Tạo môi trường virtual environment

```bash
python3 -m venv venv
```

### Kích hoạt virtual environment

**Trên macOS/Linux:**
```bash
source venv/bin/activate
```

**Trên Windows:**
```bash
venv\Scripts\activate
```

### Cài đặt dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Chạy script CDS Download

```bash
python code/cds_download.py
```

Script sẽ:
- Truy cập trang Common Data Set Repository
- Tìm và tải danh sách các links CDS cho năm 2024-2025
- Lưu kết quả vào file CSV

**Lưu ý:** Nếu gặp lỗi 403 Forbidden, website có thể đang chặn truy cập tự động. Có thể cần sử dụng Selenium với trình duyệt thật.

## Requirements

- Python 3.x
- Các packages trong `requirements.txt`:
  - requests
  - beautifulsoup4
  - pandas
  - lxml

