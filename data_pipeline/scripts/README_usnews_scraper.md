# USNews Rankings Scraper

Script để scrape thông tin ranking và chi tiết từ USNews.com và update vào database.

## Chức năng

- Thêm cột `rank_2025`, `state`, `city`, `institution_type` vào bảng `institution_master`
- Search từng trường trên USNews.com
- Scrape thông tin: rank, city, state, type
- Update vào database

## Cài đặt dependencies

```bash
# Đã có trong requirements.txt
pip install requests beautifulsoup4 lxml psycopg2-binary
```

## Sử dụng

### 1. Test với một vài trường trước (khuyến nghị)

```bash
source venv/bin/activate

# Test với 5 trường đầu tiên
python data_pipeline/scripts/update_rankings_from_usnews.py 5

# Test với 10 trường
python data_pipeline/scripts/update_rankings_from_usnews.py 10
```

### 2. Chạy cho tất cả trường

```bash
# Chạy cho tất cả trường (có rate limiting 3s/request)
python data_pipeline/scripts/update_rankings_from_usnews.py
```

### 3. Chạy trên production database

```bash
# Setup Cloud SQL Proxy trước
./cloud-sql-proxy cds-analyticsanalytivcs:asia-southeast1:cds-db

# Terminal khác
export DB_PASSWORD="dxb5ktn1sNo2jTGfOvqK3hnXT"
python data_pipeline/scripts/update_rankings_from_usnews.py
```

## Output

Script sẽ hiển thị bảng với thông tin:

```
SCHOOL NAME                              | RANK   | CITY            | STATE  | TYPE           
--------------------------------------------------------------------------------
Agnes Scott College                      | 76     | Decatur         | GA     | Private Liberal
American University                      | 105    | Washington      | DC     | Private       
...
```

## Lưu ý

1. **Rate Limiting**: Script có delay 3s giữa các requests để tránh bị block
2. **URL Detection**: Script tự động search và tìm URL của school
3. **Data Parsing**: Có thể không scrape được 100% do USNews thay đổi HTML structure
4. **Re-run**: Có thể chạy lại script, chỉ update schools chưa có rank

## Troubleshooting

### Bị block bởi USNews

- Tăng delay time trong script (dòng `time.sleep(3)` → `time.sleep(5)`)
- Chạy ít schools một lúc (dùng limit)
- Đợi vài giờ rồi chạy tiếp

### Không scrape được data

- Kiểm tra URL có đúng không
- USNews có thể đã thay đổi HTML structure → cần update selectors

### Lỗi database

- Kiểm tra connection string
- Đảm bảo các cột đã được tạo (script tự động tạo)

## Cột được thêm vào database

| Column Name | Type | Description |
|-------------|------|-------------|
| `rank_2025` | INTEGER | US News National Ranking 2025 |
| `state` | VARCHAR(50) | State abbreviation (e.g., "CA", "NY") |
| `city` | VARCHAR(100) | City name |
| `institution_type` | VARCHAR(100) | Type (e.g., "Private", "Public") |

