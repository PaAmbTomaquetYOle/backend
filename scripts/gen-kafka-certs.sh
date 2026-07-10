#!/usr/bin/env bash
# Starting point only — cert provisioning and secret storage strategy is
# devops's call (Erik / Ki-re), not prescribed here. This generates local,
# self-signed material good enough for the hackathon's docker-compose Kafka
# broker (SASL_SSL / SCRAM-SHA-512); it is not a production PKI setup.
set -euo pipefail

CERT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/certs"
KEYSTORE_PASSWORD="${KAFKA_SSL_KEYSTORE_PASSWORD:?Set KAFKA_SSL_KEYSTORE_PASSWORD before running}"
TRUSTSTORE_PASSWORD="${KAFKA_SSL_TRUSTSTORE_PASSWORD:?Set KAFKA_SSL_TRUSTSTORE_PASSWORD before running}"

mkdir -p "$CERT_DIR"
cd "$CERT_DIR"

echo "Generating CA..."
openssl req -new -x509 -keyout ca.key -out ca.pem -days 3650 -nodes \
  -subj "/CN=offboardme-kafka-ca" -passout pass:"$KEYSTORE_PASSWORD"

echo "Generating broker keypair + CSR..."
keytool -genkeypair -alias kafka -keyalg RSA -keysize 2048 -validity 3650 \
  -keystore kafka.keystore.p12 -storetype PKCS12 \
  -storepass "$KEYSTORE_PASSWORD" -keypass "$KEYSTORE_PASSWORD" \
  -dname "CN=kafka, OU=OffboardMe, O=OffboardMe" \
  -ext "SAN=DNS:kafka,DNS:localhost"

keytool -certreq -alias kafka -keystore kafka.keystore.p12 -storetype PKCS12 \
  -storepass "$KEYSTORE_PASSWORD" -file kafka.csr

echo "Signing broker cert with the CA..."
openssl x509 -req -CA ca.pem -CAkey ca.key -in kafka.csr -out kafka-signed.pem \
  -days 3650 -CAcreateserial -extfile <(printf "subjectAltName=DNS:kafka,DNS:localhost")

echo "Importing CA + signed cert into the broker keystore..."
keytool -importcert -alias ca -file ca.pem -keystore kafka.keystore.p12 \
  -storetype PKCS12 -storepass "$KEYSTORE_PASSWORD" -noprompt
keytool -importcert -alias kafka -file kafka-signed.pem -keystore kafka.keystore.p12 \
  -storetype PKCS12 -storepass "$KEYSTORE_PASSWORD" -noprompt

echo "Building broker truststore (trusts the CA)..."
keytool -importcert -alias ca -file ca.pem -keystore kafka.truststore.p12 \
  -storetype PKCS12 -storepass "$TRUSTSTORE_PASSWORD" -noprompt

rm -f kafka.csr kafka-signed.pem ca.srl

echo "Done. Wrote to $CERT_DIR:"
echo "  ca.pem                  — client-side CA (aiokafka/kafkajs KAFKA_SSL_CAFILE / KAFKA_SSL_CA)"
echo "  kafka.keystore.p12       — broker keystore (KAFKA_SSL_KEYSTORE_LOCATION)"
echo "  kafka.truststore.p12     — broker truststore (KAFKA_SSL_TRUSTSTORE_LOCATION)"
echo "Set KAFKA_SASL_USERNAME/KAFKA_SASL_PASSWORD in .env — kafka-setup bootstraps that SCRAM user on first start."
