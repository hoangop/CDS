import os
import psycopg2
import textwrap
from datetime import datetime

# Cấu hình Local DB
LOCAL_DB_CONFIG = {
    "dbname": "cds_db",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5432"
}

# Thư mục export
EXPORT_DIR = "data_pipeline/exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

def escape_sql_value(value):
    """Escape giá trị cho SQL INSERT statement."""
    if value is None:
        return "NULL"
    
    # Convert to string
    value_str = str(value)
    
    # Escape single quotes
    value_str = value_str.replace("'", "''")
    
    # Wrap in quotes
    return f"'{value_str}'"

def get_create_tables_sql():
    """Lấy SQL CREATE TABLE statements cho 5 bảng."""
    
    sql_statements = []
    
    # --- 1. Bảng MASTER: Institution_Master ---
    master_table = textwrap.dedent("""
    CREATE TABLE Institution_Master (
        Institution_ID VARCHAR(50) PRIMARY KEY,
        Name VARCHAR(255) NOT NULL,
        City_State_Zip VARCHAR(255),
        Control VARCHAR(50),
        Calendar_System VARCHAR(50),
        Degrees_Offered TEXT,
        Website_URL VARCHAR(255),
        Admissions_Email VARCHAR(255)
    );
    """)
    sql_statements.append(("Institution_Master", master_table))
    
    # --- 2. Bảng DETAIL 1: Enrollment_B ---
    enrollment_table = textwrap.dedent("""
    CREATE TABLE Enrollment_B (
        Institution_ID VARCHAR(50) NOT NULL,
        Academic_Year VARCHAR(10) NOT NULL,
        Total_UG_Students INTEGER,
        FT_First_Time_FY_Total INTEGER,
        Total_Nonresidents INTEGER,
        Total_Hispanic_Latino INTEGER,
        Total_Black INTEGER,
        Total_White INTEGER,
        Total_Asian INTEGER,
        Retention_Rate_FullTime FLOAT,
        Six_Year_Grad_Rate_Total FLOAT,
        PRIMARY KEY (Institution_ID, Academic_Year),
        FOREIGN KEY (Institution_ID) REFERENCES Institution_Master(Institution_ID)
    );
    """)
    sql_statements.append(("Enrollment_B", enrollment_table))
    
    # --- 3. Bảng DETAIL 2: Admission_C ---
    admission_table = textwrap.dedent("""
    CREATE TABLE Admission_C (
        Institution_ID VARCHAR(50) NOT NULL,
        Academic_Year VARCHAR(10) NOT NULL,
        Total_Applicants INTEGER,
        Total_Admitted INTEGER,
        Total_Enrolled INTEGER,
        Acceptance_Rate FLOAT,
        Applicants_In_State INTEGER,
        Admitted_In_State INTEGER,
        Enrolled_In_State INTEGER,
        Applicants_Out_of_State INTEGER,
        Admitted_Out_of_State INTEGER,
        Enrolled_Out_of_State INTEGER,
        Applicants_International INTEGER,
        Admitted_International INTEGER,
        Enrolled_International INTEGER,
        SAT_Comp_25th INTEGER,
        SAT_Comp_75th INTEGER,
        ACT_Comp_25th INTEGER,
        ACT_Comp_75th INTEGER,
        Rank_Top_10th_Percent FLOAT,
        Waitlist_Offered INTEGER,
        Waitlist_Admitted INTEGER,
        PRIMARY KEY (Institution_ID, Academic_Year),
        FOREIGN KEY (Institution_ID) REFERENCES Institution_Master(Institution_ID)
    );
    """)
    sql_statements.append(("Admission_C", admission_table))
    
    # --- 4. Bảng DETAIL 3: Admission_Factors_C7 ---
    admission_factors_table = textwrap.dedent("""
    CREATE TABLE Admission_Factors_C7 (
        Institution_ID VARCHAR(50) NOT NULL,
        Academic_Year VARCHAR(10) NOT NULL,
        Rigor_Secondary_Record VARCHAR(20),
        Academic_GPA VARCHAR(20),
        Standardized_Test_Scores VARCHAR(20),
        Application_Essay VARCHAR(20),
        Recommendation VARCHAR(20),
        Extracurricular_Activities VARCHAR(20),
        Talent_Ability VARCHAR(20),
        Character_Qualities VARCHAR(20),
        First_Generation VARCHAR(20),
        Alumni_Relation VARCHAR(20),
        PRIMARY KEY (Institution_ID, Academic_Year),
        FOREIGN KEY (Institution_ID) REFERENCES Institution_Master(Institution_ID)
    );
    """)
    sql_statements.append(("Admission_Factors_C7", admission_factors_table))
    
    # --- 5. Bảng DETAIL 4: FinancialAid_H ---
    financial_aid_table = textwrap.dedent("""
    CREATE TABLE FinancialAid_H (
        Institution_ID VARCHAR(50) NOT NULL,
        Academic_Year VARCHAR(10) NOT NULL,
        Tuition_FullTime_1stYear MONEY,
        Tuition_FullTime_UG MONEY,
        Required_Fees MONEY,
        Food_Housing_OnCampus MONEY,
        FT_First_Time_Need_Met INTEGER,
        Pct_Need_Met_Avg FLOAT,
        Avg_Grant_Award_NeedBased MONEY,
        Loan_Borrowers_Pct FLOAT,
        Loan_Borrowers_Avg_Cumulative MONEY,
        PRIMARY KEY (Institution_ID, Academic_Year),
        FOREIGN KEY (Institution_ID) REFERENCES Institution_Master(Institution_ID)
    );
    """)
    sql_statements.append(("FinancialAid_H", financial_aid_table))
    
    return sql_statements

def export_table_data_to_sql(table_name, db_config):
    """Export data từ một bảng ra SQL INSERT statements."""
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # Lấy tất cả columns
        cur.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table_name.lower()}'
            ORDER BY ordinal_position;
        """)
        columns_info = cur.fetchall()
        
        if not columns_info:
            print(f"⚠️  Bảng {table_name} không tồn tại, bỏ qua.")
            cur.close()
            conn.close()
            return None
        
        columns = [col[0] for col in columns_info]
        columns_str = ', '.join(columns)
        
        # Lấy tất cả data
        cur.execute(f"SELECT * FROM {table_name}")
        rows = cur.fetchall()
        
        if not rows:
            print(f"⚠️  Bảng {table_name} rỗng, bỏ qua.")
            cur.close()
            conn.close()
            return None
        
        # Generate SQL INSERT statements
        sql_statements = []
        sql_statements.append(f"-- ========================================")
        sql_statements.append(f"-- Bảng: {table_name}")
        sql_statements.append(f"-- Số lượng rows: {len(rows)}")
        sql_statements.append(f"-- ========================================")
        sql_statements.append("")
        sql_statements.append(f"-- INSERT dữ liệu")
        sql_statements.append("")
        
        # Generate INSERT cho mỗi row
        for idx, row in enumerate(rows, 1):
            values = []
            for val in row:
                values.append(escape_sql_value(val))
            
            values_str = ', '.join(values)
            sql_statements.append(f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});")
            
            # Thêm comment mỗi 50 rows để dễ đọc
            if idx % 50 == 0:
                sql_statements.append(f"-- Đã insert {idx}/{len(rows)} rows")
        
        sql_statements.append("")
        sql_statements.append(f"-- ✅ Hoàn tất {table_name}: {len(rows)} rows")
        sql_statements.append("")
        sql_statements.append("")
        
        cur.close()
        conn.close()
        
        sql_content = '\n'.join(sql_statements)
        
        print(f"✅ Exported {len(rows)} rows từ {table_name}")
        return sql_content
        
    except Exception as e:
        print(f"❌ Lỗi export {table_name}: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_complete_sql():
    """Generate SQL hoàn chỉnh: DROP, CREATE, INSERT."""
    
    print("="*60)
    print("📤 EXPORT DATABASE TO SQL (DROP + CREATE + INSERT)")
    print("="*60)
    print(f"Source: Local DB ({LOCAL_DB_CONFIG['host']}:{LOCAL_DB_CONFIG['port']})")
    print(f"Export directory: {EXPORT_DIR}")
    print()
    
    all_sql_content = []
    
    # Header
    all_sql_content.append("-- ========================================")
    all_sql_content.append("-- CDS DATABASE MIGRATION SQL")
    all_sql_content.append(f"-- Export Date: {datetime.now().isoformat()}")
    all_sql_content.append("-- ========================================")
    all_sql_content.append("")
    all_sql_content.append("-- Hướng dẫn:")
    all_sql_content.append("-- 1. Copy toàn bộ nội dung file này")
    all_sql_content.append("-- 2. Vào GCP Console → SQL → Query Editor")
    all_sql_content.append("-- 3. Paste và click 'Run'")
    all_sql_content.append("")
    all_sql_content.append("-- ⚠️  LƯU Ý: Script sẽ:")
    all_sql_content.append("--    - Kiểm tra và DROP các bảng cũ (nếu tồn tại)")
    all_sql_content.append("--    - Tạo lại 5 bảng mới")
    all_sql_content.append("--    - INSERT data vào 2 bảng: Institution_Master và Admission_C")
    all_sql_content.append("")
    all_sql_content.append("")
    
    # Part 1: DROP TABLES
    all_sql_content.append("-- ========================================")
    all_sql_content.append("-- PART 1: DROP TABLES (nếu tồn tại)")
    all_sql_content.append("-- ========================================")
    all_sql_content.append("")
    all_sql_content.append("-- Xóa các bảng cũ (theo thứ tự để tránh foreign key constraint)")
    all_sql_content.append("DROP TABLE IF EXISTS FinancialAid_H CASCADE;")
    all_sql_content.append("DROP TABLE IF EXISTS Admission_Factors_C7 CASCADE;")
    all_sql_content.append("DROP TABLE IF EXISTS Admission_C CASCADE;")
    all_sql_content.append("DROP TABLE IF EXISTS Enrollment_B CASCADE;")
    all_sql_content.append("DROP TABLE IF EXISTS Institution_Master CASCADE;")
    all_sql_content.append("")
    all_sql_content.append("-- ✅ Đã xóa các bảng cũ (nếu có)")
    all_sql_content.append("")
    all_sql_content.append("")
    
    # Part 2: CREATE TABLES
    all_sql_content.append("-- ========================================")
    all_sql_content.append("-- PART 2: CREATE TABLES (5 bảng)")
    all_sql_content.append("-- ========================================")
    all_sql_content.append("")
    
    create_statements = get_create_tables_sql()
    for table_name, create_sql in create_statements:
        all_sql_content.append(f"-- Tạo bảng: {table_name}")
        all_sql_content.append(create_sql.strip())
        all_sql_content.append("")
    
    all_sql_content.append("-- ✅ Đã tạo 5 bảng mới")
    all_sql_content.append("")
    all_sql_content.append("")
    
    # Part 3: INSERT DATA
    all_sql_content.append("-- ========================================")
    all_sql_content.append("-- PART 3: INSERT DATA (2 bảng)")
    all_sql_content.append("-- ========================================")
    all_sql_content.append("")
    
    # Export data cho 2 bảng
    tables_to_export = ["Institution_Master", "Admission_C"]
    
    for table_name in tables_to_export:
        sql_content = export_table_data_to_sql(table_name, LOCAL_DB_CONFIG)
        if sql_content:
            all_sql_content.append(sql_content)
    
    # Footer
    all_sql_content.append("-- ========================================")
    all_sql_content.append("-- ✅ HOÀN TẤT MIGRATION")
    all_sql_content.append("-- ========================================")
    all_sql_content.append("")
    all_sql_content.append("-- Đã hoàn tất:")
    all_sql_content.append("-- ✅ DROP các bảng cũ (nếu có)")
    all_sql_content.append("-- ✅ CREATE 5 bảng mới")
    all_sql_content.append("-- ✅ INSERT data vào Institution_Master")
    all_sql_content.append("-- ✅ INSERT data vào Admission_C")
    all_sql_content.append("")
    
    # Tạo file
    combined_content = '\n'.join(all_sql_content)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    combined_filename = f"{EXPORT_DIR}/CDS_MIGRATION_{timestamp}.sql"
    
    with open(combined_filename, 'w', encoding='utf-8') as f:
        f.write(combined_content)
    
    print()
    print("="*60)
    print("✅ Hoàn tất!")
    print("="*60)
    print(f"\n📄 File SQL đã tạo:")
    print(f"   {combined_filename}")
    print()
    print("📝 Cách sử dụng:")
    print("   1. Mở file SQL vừa tạo")
    print("   2. Copy toàn bộ nội dung (Cmd+A, Cmd+C)")
    print("   3. Vào GCP Console → SQL → Query Editor")
    print("   4. Paste và click 'Run'")
    print()
    print("⚠️  Lưu ý:")
    print("   - Script sẽ DROP và tạo lại 5 bảng")
    print("   - Chỉ INSERT data vào 2 bảng: Institution_Master và Admission_C")
    print()
    
    return combined_filename

if __name__ == "__main__":
    generate_complete_sql()

