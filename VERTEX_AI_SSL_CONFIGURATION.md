# Vertex AI SSL Certificate Configuration

This document explains how to configure SSL certificates for on-premise Vertex AI deployments to resolve certificate verification errors.

## Common SSL Certificate Errors

When connecting to on-premise Vertex AI endpoints, you may encounter SSL certificate verification errors such as:

```
SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1000)'))
```

This typically occurs when:
- Using self-signed certificates (common in development)
- Corporate certificate authorities not in system trust store
- Proxy servers with certificate inspection
- Outdated certificate bundles

## SSL Configuration Options

### Environment Variables

Add these variables to your `.env` file:

```bash
# SSL Certificate Verification (default: true)
VERTEXAI_SSL_VERIFY=true

# Path to CA certificate file (fixes certificate verification errors)
VERTEXAI_SSL_CA_CERT_PATH=/path/to/ca.crt
```

### Configuration Parameters

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `VERTEXAI_SSL_VERIFY` | Enable/disable SSL certificate verification | `true` | `false` |
| `VERTEXAI_SSL_CA_CERT_PATH` | Path to CA certificate bundle | `None` | `/etc/ssl/certs/ca-bundle.crt` |

## Solutions by Scenario

### **For Your SSL Certificate Error**

You need the **CA certificate** to verify your server's SSL certificate:

```bash
# This fixes SSL certificate verification errors
VERTEXAI_SSL_CA_CERT_PATH=/path/to/ca.crt
```

### 1. Development Environment (Quick Fix)

**⚠️ Warning: This is insecure and should only be used in development!**

```bash
# Disable SSL verification completely
VERTEXAI_SSL_VERIFY=false
```

### 2. Production Environment (Secure)

#### Option A: Get CA Certificate from IT Department
Contact your IT department for the corporate CA certificate bundle.

#### Option B: Extract CA Certificate
```bash
openssl s_client -showcerts -connect your-endpoint:443 < /dev/null 2>/dev/null | openssl x509 -outform PEM > ca-cert.pem
```

Then configure it:
```bash
VERTEXAI_SSL_CA_CERT_PATH=/path/to/ca-cert.pem
```

#### Option C: System-wide Certificate Configuration
```bash
export REQUESTS_CA_BUNDLE=/path/to/ca-cert.pem
export CURL_CA_BUNDLE=/path/to/ca-cert.pem
```

### 3. Corporate Environment

Contact your IT department for:
- Corporate CA certificate bundle
- Proxy configuration details
- Firewall exceptions for your endpoint

## Automatic SSL Error Handling

The application includes automatic SSL error handling:

1. **Detection**: Automatically detects SSL certificate verification errors
2. **Logging**: Provides detailed error information and troubleshooting guidance
3. **Retry**: Automatically retries with SSL verification disabled (if enabled)
4. **Fallback**: Graceful fallback to non-SSL mode when possible

### Error Handling Flow

```
1. Try connection with SSL verification enabled
   ↓ (if SSL error)
2. Log detailed SSL error information
   ↓
3. If ssl_verify=true, retry with SSL disabled
   ↓ (if still fails)
4. Provide troubleshooting guidance
```

## Testing SSL Configuration

Use the provided debug script to test your SSL configuration:

```bash
python test_ssl_debug.py
```

This script will:
- Test direct SSL connection to your endpoint
- Test HTTP requests with different SSL options
- Test Vertex AI initialization with SSL configurations
- Provide comprehensive troubleshooting guidance

## Troubleshooting Guide

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Certificate verify failed | Self-signed or untrusted CA | Add CA certificate to trust store |
| Unable to get local issuer certificate | Missing CA certificate | Set `VERTEXAI_SSL_CA_CERT_PATH` |
| Certificate hostname mismatch | Certificate doesn't match endpoint hostname | Check endpoint URL or get correct certificate |
| Proxy intercepting connections | Corporate proxy with certificate inspection | Configure proxy settings or get proxy CA |

### Debug Information

When SSL errors occur, the application logs detailed information:

```
VERTEXAI_SSL_ERROR [On-Premise]: SSL certificate verification failed
VERTEXAI_SSL_ERROR [On-Premise]: This is common with self-signed or corporate certificates
VERTEXAI_SSL_DEBUG [On-Premise]: SSL configuration:
VERTEXAI_SSL_DEBUG [On-Premise]: ssl_verify=true
VERTEXAI_SSL_DEBUG [On-Premise]: ssl_ca_cert_path=/path/to/ca.crt
```

### Manual Certificate Extraction

If you need to extract the certificate from your endpoint:

```bash
# Extract server certificate
echo -n | openssl s_client -connect your-endpoint:443 -servername your-endpoint 2>/dev/null | openssl x509 -text

# Extract certificate chain
openssl s_client -showcerts -connect your-endpoint:443 -servername your-endpoint < /dev/null 2>/dev/null

# Save certificate to file
echo -n | openssl s_client -connect your-endpoint:443 -servername your-endpoint 2>/dev/null | openssl x509 -outform PEM > server-cert.pem
```

## Security Considerations

### Development vs Production

| Environment | SSL Verification | Security Level | Recommendation |
|-------------|------------------|----------------|----------------|
| Development | Can be disabled | Low | `VERTEXAI_SSL_VERIFY=false` |
| Staging | Should be enabled | Medium | Use proper CA certificates |
| Production | Must be enabled | High | Use validated certificates only |

### Best Practices

1. **Never disable SSL verification in production**
2. **Use proper CA certificates from trusted authorities**
3. **Regularly update certificate bundles**
4. **Monitor certificate expiration dates**
5. **Use client certificates for additional security**

## Example Configurations

### Development Setup
```bash
# .env file
VERTEXAI_ENDPOINT_URL=https://dev-vertex-api.company.com
VERTEXAI_PROJECT_ID=dev-project
VERTEXAI_API_TRANSPORT=rest
VERTEXAI_SSL_VERIFY=false  # Only for development!
```

### Production Setup
```bash
# .env file
VERTEXAI_ENDPOINT_URL=https://vertex-api.company.com
VERTEXAI_PROJECT_ID=prod-project
VERTEXAI_API_TRANSPORT=rest
VERTEXAI_SSL_VERIFY=true
VERTEXAI_SSL_CA_CERT_PATH=/etc/ssl/certs/company-ca.crt
```

### Quick Setup Guide

**For SSL certificate verification errors, you only need:**
```bash
VERTEXAI_SSL_CA_CERT_PATH=/path/to/your-ca.crt
```

## Support

If you continue to experience SSL certificate issues:

1. Run the debug script: `python test_ssl_debug.py`
2. Check the application logs for detailed error information
3. Contact your IT department for certificate assistance
4. Verify network connectivity and proxy settings 