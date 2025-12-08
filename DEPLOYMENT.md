# 🚀 Deployment Guide - CDS Analytics to GCP

Hướng dẫn deploy ứng dụng CDS Analytics lên Google Cloud Platform (GCP) với CI/CD tự động qua GitHub Actions.

## 📋 Prerequisites

1. **GCP Account** với billing enabled
2. **GitHub Repository** đã sync code
3. **gcloud CLI** đã cài đặt và authenticated
4. **Docker** đã cài đặt (cho local testing)

## 🔧 Bước 1: Setup GCP Project

### 1.1. Tạo GCP Project (nếu chưa có)

```bash
# Login vào GCP
gcloud auth login

# Tạo project mới
gcloud projects create YOUR_PROJECT_ID --name="CDS Analytics"

# Set project
gcloud config set project YOUR_PROJECT_ID
```

### 1.2. Chạy script setup tự động

```bash
# Make script executable
chmod +x scripts/setup-gcp.sh

# Chạy setup (thay YOUR_PROJECT_ID bằng project ID của bạn)
./scripts/setup-gcp.sh YOUR_PROJECT_ID us-central1
```

Script này sẽ tự động:
- ✅ Enable các APIs cần thiết
- ✅ Tạo Artifact Registry repository
- ✅ Tạo Cloud SQL instance (PostgreSQL)
- ✅ Tạo Service Account cho GitHub Actions
- ✅ Grant các permissions cần thiết
- ✅ Tạo và download service account key

### 1.3. Lưu thông tin quan trọng

Sau khi chạy script, bạn sẽ nhận được:
- **DB_PASSWORD**: Mật khẩu database (lưu lại cẩn thận!)
- **CONNECTION_NAME**: Cloud SQL connection name
- **key.json**: Service account key file

⚠️ **Lưu ý**: Thêm `key.json` vào `.gitignore` để không commit lên GitHub!

## 🔐 Bước 2: Cấu hình GitHub Secrets

Vào GitHub repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Thêm các secrets sau:

### 2.1. GCP_PROJECT_ID
```
YOUR_PROJECT_ID
```

### 2.2. GCP_SA_KEY
Copy toàn bộ nội dung file `key.json` (từ bước 1.2):
```json
{
  "type": "service_account",
  "project_id": "...",
  ...
}
```

### 2.3. DATABASE_URL
Format cho Cloud SQL:
```
postgresql://postgres:YOUR_DB_PASSWORD@/cds_db?host=/cloudsql/PROJECT_ID:REGION:cds-db
```

Ví dụ:
```
postgresql://postgres:MySecurePassword123@/cds_db?host=/cloudsql/my-project:us-central1:cds-db
```

### 2.4. CLOUD_SQL_INSTANCE
Format:
```
PROJECT_ID:REGION:INSTANCE_NAME
```

Ví dụ:
```
my-project:us-central1:cds-db
```

## 🗄️ Bước 3: Setup Database

### 3.1. Kết nối tới Cloud SQL

Có 2 cách:

**Cách 1: Cloud SQL Proxy (Recommended)**
```bash
# Download Cloud SQL Proxy
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.amd64
chmod +x cloud-sql-proxy

# Chạy proxy (thay CONNECTION_NAME)
./cloud-sql-proxy CONNECTION_NAME
```

Sau đó kết nối như local:
```bash
psql -h 127.0.0.1 -U postgres -d cds_db
```

**Cách 2: gcloud sql connect**
```bash
gcloud sql connect cds-db --user=postgres --database=cds_db
```

### 3.2. Chạy migrations

```bash
# Activate venv
source venv/bin/activate

# Update DATABASE_URL trong environment
export DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@127.0.0.1:5432/cds_db"

# Chạy create_db.py (nếu dùng Cloud SQL Proxy)
python data_pipeline/scripts/create_db.py
```

Hoặc nếu dùng Cloud SQL trực tiếp, cần update `create_db.py` để dùng connection string phù hợp.

## 🚀 Bước 4: Deploy qua GitHub Actions

### 4.1. Push code lên GitHub

```bash
git add .
git commit -m "Add CI/CD configuration for GCP deployment"
git push origin main
```

### 4.2. Trigger deployment

GitHub Actions sẽ tự động chạy khi:
- ✅ Push code lên branch `main`
- ✅ Tạo Pull Request vào `main`
- ✅ Manual trigger từ GitHub Actions tab

### 4.3. Kiểm tra deployment

1. Vào GitHub repository → **Actions** tab
2. Xem workflow run status
3. Nếu thành công, bạn sẽ thấy URLs của Backend và Frontend

## 📍 Bước 5: Truy cập ứng dụng

Sau khi deploy thành công, bạn sẽ có:

- **Backend API**: `https://cds-backend-xxxxx.run.app`
- **Frontend**: `https://cds-frontend-xxxxx.run.app`
- **API Docs**: `https://cds-backend-xxxxx.run.app/docs`

## 🔄 Bước 6: Import dữ liệu (Production)

### 6.1. Setup Cloud SQL Proxy

```bash
./cloud-sql-proxy CONNECTION_NAME
```

### 6.2. Import dữ liệu

```bash
# Set DATABASE_URL
export DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@127.0.0.1:5432/cds_db"

# Chạy import script
python data_pipeline/scripts/process_direct_pdf_to_db.py
```

## 🛠️ Troubleshooting

### Lỗi: Permission denied
```bash
# Kiểm tra service account permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID
```

### Lỗi: Database connection failed
- Kiểm tra Cloud SQL instance đang chạy
- Verify DATABASE_URL format
- Kiểm tra Cloud SQL instance connection trong Cloud Run

### Lỗi: Image push failed
```bash
# Kiểm tra Artifact Registry repository
gcloud artifacts repositories list
```

### Xem logs
```bash
# Backend logs
gcloud run services logs read cds-backend --region us-central1

# Frontend logs
gcloud run services logs read cds-frontend --region us-central1
```

## 📊 Monitoring & Maintenance

### Xem metrics
- Vào **Cloud Console** → **Cloud Run** → Chọn service
- Xem metrics: Requests, Latency, Errors

### Scale services
```bash
# Update min instances
gcloud run services update cds-backend \
  --min-instances 1 \
  --region us-central1
```

### Update environment variables
```bash
gcloud run services update cds-backend \
  --set-env-vars KEY=VALUE \
  --region us-central1
```

## 🔒 Security Best Practices

1. ✅ **Never commit** `key.json` hoặc secrets
2. ✅ Sử dụng **Secret Manager** cho sensitive data
3. ✅ Enable **Cloud SQL private IP** (recommended)
4. ✅ Setup **Cloud Armor** cho DDoS protection
5. ✅ Enable **Cloud Run authentication** nếu cần

## 📚 Tài liệu tham khảo

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Artifact Registry](https://cloud.google.com/artifact-registry/docs)

## ✅ Checklist Deployment

- [ ] GCP Project created
- [ ] APIs enabled
- [ ] Cloud SQL instance created
- [ ] Artifact Registry repository created
- [ ] Service Account created và key downloaded
- [ ] GitHub Secrets configured
- [ ] Database schema created
- [ ] Code pushed to GitHub
- [ ] GitHub Actions workflow successful
- [ ] Backend URL accessible
- [ ] Frontend URL accessible
- [ ] Data imported to production database

---

**Happy Deploying! 🚀**

