#!/bin/bash
# ============================================================
# MySQL SSL Certificate Generation Script
# ============================================================
# Usage: ./generate-ssl-certs.sh
# Output: ssl/ directory with CA, server, and client certificates
# ============================================================

set -e

SSL_DIR="$(dirname "$0")/ssl"
DAYS_VALID=3650  # 10 years
KEY_SIZE=4096

echo "=== MySQL SSL Certificate Generator ==="
echo "Output directory: $SSL_DIR"

# Create SSL directory
mkdir -p "$SSL_DIR"
cd "$SSL_DIR"

# Clean existing certificates
rm -f *.pem *.key *.csr

echo ""
echo "=== Step 1: Generate CA Certificate ==="
openssl genrsa -out ca-key.pem $KEY_SIZE
openssl req -new -x509 -nodes -days $DAYS_VALID \
    -key ca-key.pem \
    -out ca.pem \
    -subj "/C=US/ST=State/L=City/O=InventorySystem/CN=MySQL-CA"

echo ""
echo "=== Step 2: Generate Server Certificate ==="
openssl genrsa -out server-key.pem $KEY_SIZE
openssl req -new -key server-key.pem -out server-req.pem \
    -subj "/C=US/ST=State/L=City/O=InventorySystem/CN=mysql-server"
openssl x509 -req -in server-req.pem -days $DAYS_VALID \
    -CA ca.pem -CAkey ca-key.pem -CAcreateserial \
    -out server-cert.pem

echo ""
echo "=== Step 3: Generate Client Certificate ==="
openssl genrsa -out client-key.pem $KEY_SIZE
openssl req -new -key client-key.pem -out client-req.pem \
    -subj "/C=US/ST=State/L=City/O=InventorySystem/CN=mysql-client"
openssl x509 -req -in client-req.pem -days $DAYS_VALID \
    -CA ca.pem -CAkey ca-key.pem -CAcreateserial \
    -out client-cert.pem

echo ""
echo "=== Step 4: Set Permissions ==="
chmod 600 *-key.pem
chmod 644 *.pem

# Clean up CSR files
rm -f *.csr *.srl server-req.pem client-req.pem

echo ""
echo "=== Certificates Generated Successfully ==="
echo ""
echo "Files created:"
ls -la "$SSL_DIR"
echo ""
echo "To enable SSL in MySQL, update docker/mysql/conf.d/security.cnf:"
echo "  require_secure_transport = ON"
echo "  ssl_ca = /etc/mysql/ssl/ca.pem"
echo "  ssl_cert = /etc/mysql/ssl/server-cert.pem"
echo "  ssl_key = /etc/mysql/ssl/server-key.pem"
echo ""
echo "For Django connection, add to DATABASE_URL or settings:"
echo "  'OPTIONS': {"
echo "      'ssl': {"
echo "          'ca': '/path/to/ca.pem',"
echo "          'cert': '/path/to/client-cert.pem',"
echo "          'key': '/path/to/client-key.pem',"
echo "      }"
echo "  }"
