import textwrap
import psycopg2
from psycopg2 import sql

# Cấu hình kết nối DB (Localhost Docker)
DB_CONFIG = {
    "dbname": "cds_db",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5432"
}

def generate_cds_schema_sql():
    """Tạo lệnh SQL CREATE TABLE cho mô hình Master-Detail CDS."""

    sql_statements = []

    # --- 0. Xóa bảng cũ nếu tồn tại (Clean start) ---
    drop_tables = """
    DROP TABLE IF EXISTS FinancialAid_H CASCADE;
    DROP TABLE IF EXISTS Admission_Factors_C7 CASCADE;
    DROP TABLE IF EXISTS Admission_C CASCADE;
    DROP TABLE IF EXISTS Enrollment_B CASCADE;
    DROP TABLE IF EXISTS Institution_Master CASCADE;
    """
    sql_statements.append(drop_tables)

    # --- 1. Bảng MASTER: Institution_Master (Thông tin tĩnh) ---
    master_table = textwrap.dedent("""
    CREATE TABLE Institution_Master (
        Institution_ID VARCHAR(50) PRIMARY KEY,
        Name VARCHAR(255) NOT NULL,
        City_State_Zip VARCHAR(255),
        Control VARCHAR(50),               -- Ví dụ: Private (nonprofit), Public
        Calendar_System VARCHAR(50),        -- Ví dụ: Semester, Quarter
        Degrees_Offered TEXT,               -- Các bằng cấp (Lưu trữ dạng JSON hoặc Text)
        Website_URL VARCHAR(255),
        Admissions_Email VARCHAR(255)
    );
    """)
    sql_statements.append(master_table)

    # --- 2. Bảng DETAIL 1: Enrollment_B (Tuyển sinh và Duy trì) ---
    enrollment_table = textwrap.dedent("""
    CREATE TABLE Enrollment_B (
        Institution_ID VARCHAR(50) NOT NULL,
        Academic_Year VARCHAR(10) NOT NULL, -- Ví dụ: 2024-2025
        
        -- Dữ liệu B1 (Tổng SV)
        Total_UG_Students INTEGER,
        FT_First_Time_FY_Total INTEGER,
        
        -- Dữ liệu B2 (Chủng tộc)
        Total_Nonresidents INTEGER,
        Total_Hispanic_Latino INTEGER,
        Total_Black INTEGER,
        Total_White INTEGER,
        Total_Asian INTEGER,
        
        -- Dữ liệu B22 (Tỷ lệ duy trì)
        Retention_Rate_FullTime FLOAT, -- Tỷ lệ duy trì SV năm nhất (Fall 2023 Cohort -> Fall 2024) 
        
        -- Dữ liệu B (Tỷ lệ tốt nghiệp)
        Six_Year_Grad_Rate_Total FLOAT, -- Tỷ lệ tốt nghiệp 6 năm (2018 Cohort) [cite: 137]

        PRIMARY KEY (Institution_ID, Academic_Year),
        FOREIGN KEY (Institution_ID) REFERENCES Institution_Master(Institution_ID)
    );
    """)
    sql_statements.append(enrollment_table)

    # --- 3. Bảng DETAIL 2: Admission_C (Ứng tuyển, Chấp nhận, Điểm thi) ---
    admission_table = textwrap.dedent("""
    CREATE TABLE Admission_C (
        Institution_ID VARCHAR(50) NOT NULL,
        Academic_Year VARCHAR(10) NOT NULL,
        
        -- Dữ liệu C1 (Applicants/Admitted/Enrolled)
        Total_Applicants INTEGER,                               -- Tổng hồ sơ ứng tuyển [cite: 219]
        Total_Admitted INTEGER,                                 -- Tổng số được chấp nhận [cite: 219]
        Total_Enrolled INTEGER,                                 -- Tổng số nhập học [cite: 219]
        Acceptance_Rate FLOAT,                                  -- Tính toán: Total_Admitted / Total_Applicants
        
        -- Phân tách theo khu vực (In-State/Out-of-State/International)
        Applicants_In_State INTEGER,
        Admitted_In_State INTEGER,
        Enrolled_In_State INTEGER,
        Applicants_Out_of_State INTEGER,
        Admitted_Out_of_State INTEGER,
        Enrolled_Out_of_State INTEGER,
        Applicants_International INTEGER,
        Admitted_International INTEGER,
        Enrolled_International INTEGER,
        
        -- Dữ liệu C9 (Test Scores - 25th / 75th Percentile)
        SAT_Comp_25th INTEGER,
        SAT_Comp_75th INTEGER,
        ACT_Comp_25th INTEGER,
        ACT_Comp_75th INTEGER,
        
        -- Dữ liệu C10 (Học sinh trong Top)
        Rank_Top_10th_Percent FLOAT,                            -- % trong top 10% [cite: 343]
        
        -- Dữ liệu C2 (Waitlist)
        Waitlist_Offered INTEGER,                               -- Số lượng ứng viên được đưa vào Waitlist [cite: 232]
        Waitlist_Admitted INTEGER,                              -- Số lượng ứng viên được nhận từ Waitlist [cite: 232]

        PRIMARY KEY (Institution_ID, Academic_Year),
        FOREIGN KEY (Institution_ID) REFERENCES Institution_Master(Institution_ID)
    );
    """)
    sql_statements.append(admission_table)

    # --- 4. Bảng DETAIL 3: Admission_Factors_C7 (Yếu tố xét tuyển) ---
    # Sử dụng Enum/Lookup Table hoặc lưu trữ dạng VARCHAR/TEXT
    admission_factors_table = textwrap.dedent("""
    CREATE TABLE Admission_Factors_C7 (
        Institution_ID VARCHAR(50) NOT NULL,
        Academic_Year VARCHAR(10) NOT NULL,
        
        -- Các yếu tố Học thuật (Academic)
        Rigor_Secondary_Record VARCHAR(20),     -- Độ khó của hồ sơ cấp 3 [cite: 271]
        Academic_GPA VARCHAR(20),               -- GPA [cite: 271]
        Standardized_Test_Scores VARCHAR(20),   -- Điểm thi chuẩn hóa [cite: 271]
        Application_Essay VARCHAR(20),          -- Bài luận [cite: 271]
        Recommendation VARCHAR(20),             -- Thư giới thiệu [cite: 271]
        
        -- Các yếu tố Phi Học thuật (Nonacademic)
        Extracurricular_Activities VARCHAR(20), -- Ngoại khóa [cite: 271]
        Talent_Ability VARCHAR(20),             -- Tài năng/Kỹ năng [cite: 271]
        Character_Qualities VARCHAR(20),        -- Phẩm chất cá nhân [cite: 271]
        First_Generation VARCHAR(20),           -- Thế hệ đầu tiên học đại học [cite: 271]
        Alumni_Relation VARCHAR(20),            -- Quan hệ cựu sinh viên [cite: 271]

        PRIMARY KEY (Institution_ID, Academic_Year),
        FOREIGN KEY (Institution_ID) REFERENCES Institution_Master(Institution_ID)
    );
    """)
    sql_statements.append(admission_factors_table)

    # --- 5. Bảng DETAIL 4: FinancialAid_H (Hỗ trợ tài chính & Chi phí) ---
    financial_aid_table = textwrap.dedent("""
    CREATE TABLE FinancialAid_H (
        Institution_ID VARCHAR(50) NOT NULL,
        Academic_Year VARCHAR(10) NOT NULL,

        -- Dữ liệu G1 (Chi phí)
        Tuition_FullTime_1stYear MONEY,             -- Học phí năm nhất [cite: 700]
        Tuition_FullTime_UG MONEY,                  -- Học phí Undergraduate [cite: 700]
        Required_Fees MONEY,                        -- Các loại phí bắt buộc [cite: 704]
        Food_Housing_OnCampus MONEY,                -- Ăn và ở tại ký túc xá [cite: 704]
        
        -- Dữ liệu H2 (Hỗ trợ tài chính)
        FT_First_Time_Need_Met INTEGER,             -- Số SV năm nhất được đáp ứng nhu cầu tài chính [cite: 791]
        Pct_Need_Met_Avg FLOAT,                     -- % nhu cầu được đáp ứng trung bình [cite: 791]
        Avg_Grant_Award_NeedBased MONEY,            -- Học bổng/Trợ cấp TB theo nhu cầu [cite: 791]
        
        -- Dữ liệu H5 (Vay nợ)
        Loan_Borrowers_Pct FLOAT,                   -- % SV tốt nghiệp vay nợ (Any Loan Program) [cite: 821]
        Loan_Borrowers_Avg_Cumulative MONEY,        -- Số tiền vay nợ tích lũy trung bình [cite: 821]

        PRIMARY KEY (Institution_ID, Academic_Year),
        FOREIGN KEY (Institution_ID) REFERENCES Institution_Master(Institution_ID)
    );
    """)
    sql_statements.append(financial_aid_table)
    
    return sql_statements

def create_tables():
    """Kết nối DB và thực thi lệnh tạo bảng."""
    sql_commands = generate_cds_schema_sql()
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("Đang kết nối tới Database...")
        for command in sql_commands:
            cur.execute(command)
        
        conn.commit()
        print("✅ Đã tạo Schema thành công!")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    create_tables()