# 🚀 Quick Start - Deploy to GCP

Hướng dẫn nhanh deploy CDS Analytics lên GCP trong 5 bước.

## ⚡ Quick Steps

### 1️⃣ Setup GCP Resources (5 phút)

```bash
# Chạy script setup tự động
chmod +x scripts/setup-gcp.sh
./scripts/setup-gcp.sh YOUR_PROJECT_ID us-central1
```

**Lưu lại:**
- `DB_PASSWORD` từ output
- `CONNECTION_NAME` từ output
- File `key.json` (đã được tạo)

### 2️⃣ Cấu hình GitHub Secrets (3 phút)

Vào: **GitHub Repo** → **Settings** → **Secrets and variables** → **Actions**

Thêm 4 secrets:

| Secret Name | Value |
|------------|-------|
| `GCP_PROJECT_ID` | `YOUR_PROJECT_ID` |
| `GCP_SA_KEY` | Nội dung file `key.json` |
| `DATABASE_URL` | `postgresql://postgres:PASSWORD@/cds_db?host=/cloudsql/CONNECTION_NAME` |
| `CLOUD_SQL_INSTANCE` | `PROJECT_ID:REGION:cds-db` |

### 3️⃣ Setup Database (2 phút)

```bash
# Download Cloud SQL Proxy
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.amd64
chmod +x cloud-sql-proxy

# Chạy proxy (terminal 1)
./cloud-sql-proxy CONNECTION_NAME

# Terminal 2: Setup database
export DATABASE_URL="postgresql://postgres:PASSWORD@127.0.0.1:5432/cds_db"
source venv/bin/activate
python data_pipeline/scripts/create_db.py
```

### 4️⃣ Deploy (Tự động)

```bash
# Push code lên GitHub
git add .
git commit -m "Ready for deployment"
git push origin main
```

GitHub Actions sẽ tự động:
- ✅ Build Docker images
- ✅ Push lên Artifact Registry
- ✅ Deploy lên Cloud Run

### 5️⃣ Kiểm tra

1. Vào **GitHub** → **Actions** → Xem workflow status
2. Nếu thành công, lấy URLs từ workflow output
3. Truy cập Frontend URL để test

## 📝 Notes

- ⚠️ **KHÔNG commit** file `key.json`
- ✅ Database password: Lưu ở nơi an toàn
- ✅ URLs sẽ có format: `https://cds-backend-xxxxx.run.app`

## 🔗 Xem chi tiết

Xem file `DEPLOYMENT.md` để biết thêm chi tiết và troubleshooting.

---

**Total time: ~10 phút** ⏱️

