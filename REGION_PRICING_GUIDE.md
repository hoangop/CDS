# 🌏 Region & Pricing Guide - Việt Nam

## 📍 Region Selection

### **Singapore (asia-southeast1)** - ✅ **KHUYẾN NGHỊ**

**Ưu điểm:**
- ✅ **Latency thấp**: ~30-50ms từ Việt Nam (vs ~200ms từ US)
- ✅ **Gần người dùng**: Tốt cho frontend/API phục vụ người dùng Việt Nam
- ✅ **Compliance**: Tuân thủ quy định dữ liệu khu vực châu Á
- ✅ **Timezone**: Gần với Việt Nam (UTC+8)

**Nhược điểm:**
- ⚠️ **Pricing cao hơn**: ~10-15% so với US regions
- ⚠️ **Ít services hơn**: Một số services mới có thể chưa có

### **US Central (us-central1)** - ⚠️ **KHÔNG KHUYẾN NGHỊ**

**Ưu điểm:**
- ✅ **Pricing rẻ nhất**: Thường rẻ hơn 10-15%
- ✅ **Services đầy đủ**: Tất cả services mới nhất
- ✅ **Documentation**: Nhiều examples và tutorials

**Nhược điểm:**
- ❌ **Latency cao**: ~200-250ms từ Việt Nam
- ❌ **Timezone khác**: UTC-6 (chênh 13-14 giờ)
- ❌ **Trải nghiệm người dùng kém**: Load chậm hơn

## 💰 Cloud SQL Pricing Comparison

### **Tier 1: Shared Core (Development/Testing)**

| Tier | vCPU | RAM | Giá/tháng (Singapore) | Giá/tháng (US) | Phù hợp |
|------|------|-----|----------------------|----------------|---------|
| `db-f1-micro` | 0.2 | 0.6 GB | ~$7-8 | ~$7 | Dev/Test nhỏ |
| `db-g1-small` | 0.5 | 1.7 GB | ~$25-30 | ~$25 | Dev/Test vừa |

**Đặc điểm:**
- ✅ Rẻ nhất
- ✅ Đủ cho development và testing
- ⚠️ Performance hạn chế
- ⚠️ Không đảm bảo SLA cao

### **Tier 2: Dedicated Core (Production)**

| Tier | vCPU | RAM | Giá/tháng (Singapore) | Giá/tháng (US) | Phù hợp |
|------|------|-----|----------------------|----------------|---------|
| `db-n1-standard-1` | 1 | 3.75 GB | ~$50-60 | ~$50 | Production nhỏ |
| `db-n1-standard-2` | 2 | 7.5 GB | ~$100-120 | ~$100 | Production vừa |
| `db-n1-standard-4` | 4 | 15 GB | ~$200-240 | ~$200 | Production lớn |

**Đặc điểm:**
- ✅ Performance tốt
- ✅ SLA cao (99.95%)
- ✅ Đảm bảo resources
- ⚠️ Đắt hơn Tier 1

## 📊 So sánh chi phí ước tính

### **Scenario 1: Development/Testing**

**Singapore:**
- Cloud SQL (db-f1-micro): ~$8/tháng
- Cloud Run (Backend): ~$5-10/tháng (tùy traffic)
- Cloud Run (Frontend): ~$5-10/tháng
- **Tổng: ~$18-28/tháng**

**US Central:**
- Cloud SQL (db-f1-micro): ~$7/tháng
- Cloud Run (Backend): ~$4-8/tháng
- Cloud Run (Frontend): ~$4-8/tháng
- **Tổng: ~$15-23/tháng**

**Tiết kiệm: ~$3-5/tháng** (nhưng latency cao hơn 4-5 lần)

### **Scenario 2: Production**

**Singapore:**
- Cloud SQL (db-n1-standard-1): ~$55/tháng
- Cloud Run (Backend): ~$20-50/tháng
- Cloud Run (Frontend): ~$20-50/tháng
- **Tổng: ~$95-155/tháng**

**US Central:**
- Cloud SQL (db-n1-standard-1): ~$50/tháng
- Cloud Run (Backend): ~$18-45/tháng
- Cloud Run (Frontend): ~$18-45/tháng
- **Tổng: ~$86-140/tháng**

**Tiết kiệm: ~$9-15/tháng** (nhưng UX kém hơn đáng kể)

## 🎯 Khuyến nghị

### **Cho Development/Testing:**
- ✅ **Singapore (asia-southeast1)**
- ✅ **Tier: db-f1-micro** ($8/tháng)
- **Lý do**: Latency thấp, dễ test, chênh lệch giá nhỏ

### **Cho Production:**
- ✅ **Singapore (asia-southeast1)**
- ✅ **Tier: db-n1-standard-1** ($55/tháng) hoặc **db-n1-standard-2** ($110/tháng)
- **Lý do**: 
  - UX tốt hơn (latency thấp)
  - Chênh lệch giá không đáng kể so với lợi ích
  - Compliance tốt hơn

### **Khi nào dùng US:**
- ⚠️ Chỉ khi budget rất hạn chế
- ⚠️ Người dùng chủ yếu ở US/Europe
- ⚠️ Không quan trọng latency

## 📝 Lưu ý

1. **Free Tier**: 
   - Cloud SQL: Không có free tier
   - Cloud Run: 2 triệu requests/tháng miễn phí
   - Artifact Registry: 0.5 GB storage miễn phí

2. **Pricing có thể thay đổi**: Kiểm tra [GCP Pricing Calculator](https://cloud.google.com/products/calculator)

3. **Traffic costs**: 
   - Egress (outbound) từ Singapore về Việt Nam: ~$0.12/GB
   - Egress từ US về Việt Nam: ~$0.12/GB (nhưng nhiều data hơn do latency)

## 🔧 Cách chọn region trong script

```bash
# Singapore (khuyến nghị)
./scripts/setup-gcp.sh YOUR_PROJECT_ID asia-southeast1

# US Central (nếu muốn rẻ hơn)
./scripts/setup-gcp.sh YOUR_PROJECT_ID us-central1
```

## 📈 Monitoring Costs

```bash
# Xem billing
gcloud billing accounts list

# Xem costs theo service
gcloud billing projects describe YOUR_PROJECT_ID
```

---

**Kết luận**: Với người dùng ở Việt Nam, **Singapore (asia-southeast1)** là lựa chọn tốt nhất dù có đắt hơn một chút, vì latency thấp sẽ cải thiện đáng kể trải nghiệm người dùng.

