FROM node:18-alpine AS deps

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Cấu hình npm với retry và timeout để xử lý lỗi mạng
RUN npm config set fetch-retries 5 && \
    npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 120000 && \
    npm config set registry https://registry.npmjs.org/

# Install dependencies với retry logic
# Nếu có package-lock.json thì dùng npm ci, không thì dùng npm install
RUN if [ -f package-lock.json ]; then \
      npm ci --legacy-peer-deps || (npm cache clean --force && npm ci --legacy-peer-deps); \
    else \
      npm install --legacy-peer-deps || (npm cache clean --force && npm install --legacy-peer-deps); \
    fi

FROM node:18-alpine AS builder

WORKDIR /app

# Copy dependencies từ stage trước
COPY --from=deps /app/node_modules ./node_modules

# Copy package files và source
COPY package.json package-lock.json* ./
COPY . .

# Build Next.js app
RUN npm run build

FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Copy built application từ standalone output
# Next.js standalone đã bao gồm tất cả dependencies và cấu trúc cần thiết
# Public folder (nếu có) đã được Next.js copy vào .next/standalone/public tự động
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Server.js nằm trong root của standalone folder
CMD ["node", "server.js"]

