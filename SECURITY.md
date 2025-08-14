# Security Policy

## Supported Versions

The following versions of FindersKeepers v2 are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 2.x.x   | :white_check_mark: |
| 1.x.x   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability in FindersKeepers v2, please report it responsibly:

### How to Report

1. **Create a Security Advisory**: Use GitHub's security advisory feature
2. **Email**: Contact the maintainer directly for critical issues
3. **Do NOT**: Create public issues for security vulnerabilities

### What to Include

When reporting a vulnerability, please include:

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Suggested fix (if available)
- Your contact information

### Response Timeline

- **Initial Response**: Within 24-48 hours
- **Status Update**: Weekly updates on progress
- **Resolution**: Target 30 days for critical issues, 90 days for others

### Disclosure Policy

- We will acknowledge your report within 48 hours
- We will provide regular updates on our progress
- We will notify you when the issue is resolved
- We will publicly disclose the issue after a fix is released
- We will credit you for the discovery (unless you prefer to remain anonymous)

## Security Features

FindersKeepers v2 implements several security measures:

- **Environment Variable Security**: All sensitive data stored in environment variables
- **Container Security**: Non-root containers with minimal privileges
- **Database Encryption**: Encrypted connections to all databases
- **API Authentication**: JWT-based authentication for API endpoints
- **Automated Security Scanning**: CodeQL, Bandit, and dependency scanning
- **Secret Detection**: Automated scanning for hardcoded secrets

## Security Best Practices

When deploying FindersKeepers v2:

1. **Use Strong Passwords**: Generate unique passwords for all services
2. **Secure Environment Files**: Set `.env` file permissions to 600
3. **Regular Updates**: Keep all dependencies and containers updated
4. **Network Security**: Use internal Docker networks where possible
5. **Monitoring**: Enable logging and monitoring for security events
6. **Backup Security**: Secure and encrypt backup files

## Vulnerability Disclosure

For detailed security information and recent security advisories, see our [Security Guide](./docs/SECURITY_GUIDE.md).

---

**Last Updated**: August 2025  
**Contact**: Create a security advisory or discussion on GitHub
