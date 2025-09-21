#!/bin/sh

# 如果任何命令執行失敗，立即中止腳本
set -e

# --- 1. 等待 MinIO 服務就緒 ---
# 透過迴圈設定 mc alias，直到成功為止，代表 MinIO 已可連線
echo "正在等待 MinIO 服務啟動..."
until mc alias set local http://${MINIO_HOST:-minio}:${MINIO_PORT:-9000} "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}"; do
    echo "MinIO 尚未就緒，2 秒後重試..."
    sleep 2
done
echo "成功連接到 MinIO 服務！"
echo "------------------------------------"

# --- 2. 檢查並建立 Bucket ---
# 檢查指定的 bucket 是否已經存在
# 我們將 mc ls 的輸出重新導向到 /dev/null，因為我們只關心它的成功/失敗狀態碼
echo "正在檢查 Bucket '${MINIO_BUCKET_NAME}' 是否存在..."
if mc ls "local/${MINIO_BUCKET_NAME}" >/dev/null 2>&1; then
    # 如果 mc ls 成功 (exit code 0)，代表 bucket 已存在
    echo "Bucket '${MINIO_BUCKET_NAME}' 已經存在，無需建立。"
else
    # 如果 mc ls 失敗 (exit code 1)，代表 bucket 不存在
    echo "Bucket '${MINIO_BUCKET_NAME}' 不存在，現在開始建立..."
    mc mb "local/${MINIO_BUCKET_NAME}"
    echo "Bucket '${MINIO_BUCKET_NAME}' 建立成功！"
fi
echo "------------------------------------"


# --- 3. 設定 Bucket 存取策略 ---
# 無論 bucket 是新建的還是已存在的，都確保其存取策略符合預期
echo "正在設定 Bucket '${MINIO_BUCKET_NAME}' 的存取策略為 private..."
mc anonymous set private "local/${MINIO_BUCKET_NAME}"
echo "策略設定完成。"
echo "------------------------------------"


echo "MinIO 初始化腳本執行完畢！"

