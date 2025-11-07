# PHP Extensions Building Guide

This guide explains how to build PHP extensions using GitHub Actions.

[中文文档](docs/zh-CN/EXTENSIONS_GUIDE.md) | [Documentation](EXTENSIONS_GUIDE.md)

## Table of Contents
- [Quick Start](#quick-start)
- [Extension Configuration](#extension-configuration)
- [Common Extensions](#common-extensions)
- [Advanced Usage](#advanced-usage)
- [Extension Testing](#extension-testing)
- [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Build PHP Without Extensions

When running the workflow in GitHub Actions:
```
Version Type: stable
Stable Version: 8.4.14
Architecture: x64
Thread Safety: nts
Build Extensions: false  ← Uncheck
```

### 2. Build Single Extension

```
Version Type: stable
Stable Version: 8.4.14
Architecture: x64
Thread Safety: nts
Build Extensions: true  ← Check
Custom Extensions JSON: [{"name":"xdebug","url":"https://github.com/xdebug/xdebug","ref":"3.4.0","args":"--enable-xdebug"}]
```

### 3. Build Multiple Extensions

```json
[
  {
    "name": "xdebug",
    "url": "https://github.com/xdebug/xdebug",
    "ref": "3.4.0",
    "args": "--enable-xdebug"
  },
  {
    "name": "redis",
    "url": "https://github.com/phpredis/phpredis",
    "ref": "6.1.0",
    "args": "--enable-redis"
  }
]
```

### 4. Use Default Extensions

Leave the "Custom Extensions JSON" field empty to use the 8 default extensions:

```
Version Type: stable
Stable Version: 8.4.14
Architecture: x64
Thread Safety: nts
Build Extensions: true  ← Check
Custom Extensions JSON: (leave empty)  ← Use defaults
```

**Default extensions included:**
- xdebug 3.4.0 - Debugger
- redis 6.1.0 - Redis client
- apcu 5.1.24 - APCu cache
- imagick 3.7.0 - Image processing
- memcache 8.2 - Memcache client
- memcached 3.3.0 - Memcached client
- mongodb 1.20.1 - MongoDB driver
- imap 1.0.2 - IMAP extension

## Extension Configuration

### JSON Format

Each extension object contains the following fields:

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `name` | ✅ | Extension name | `"xdebug"` |
| `url` | ✅ | Git repository URL | `"https://github.com/xdebug/xdebug"` |
| `ref` | ✅ | Git reference (tag/branch/commit) | `"3.4.0"` |
| `args` | ✅ | Build arguments | `"--enable-xdebug"` |
| `libs` | ❌ | Dependencies (space-separated) | `"openssl zlib"` |

### Configuration File Approach

Use `extensions.example.json` as a template:

```bash
cp extensions.example.json extensions.json
# Edit extensions.json with your required extensions
```

Then paste the file contents into the "Custom Extensions JSON" input field in GitHub Actions.

### Default Configuration

The repository includes [extensions.default.json](extensions.default.json) with 8 popular extensions pre-configured. This file is automatically used when you enable extension building without providing custom configuration.

## Common Extensions

### Xdebug (Debugger)

```json
{
  "name": "xdebug",
  "url": "https://github.com/xdebug/xdebug",
  "ref": "3.4.0",
  "args": "--enable-xdebug"
}
```

**Version Compatibility:**
- Xdebug 3.4.x → PHP 8.2, 8.3, 8.4
- Xdebug 3.3.x → PHP 8.1, 8.2, 8.3
- Xdebug 3.2.x → PHP 8.0, 8.1, 8.2

### Redis (Cache)

```json
{
  "name": "redis",
  "url": "https://github.com/phpredis/phpredis",
  "ref": "6.1.0",
  "args": "--enable-redis"
}
```

**Version Compatibility:**
- phpredis 6.x → PHP 8.0+
- phpredis 5.x → PHP 7.0+

### Imagick (Image Processing)

```json
{
  "name": "imagick",
  "url": "https://github.com/Imagick/imagick",
  "ref": "3.7.0",
  "args": "--with-imagick",
  "libs": "imagemagick"
}
```

**Note:** Requires ImageMagick dependency library.

### Swoole (Async Framework)

```json
{
  "name": "swoole",
  "url": "https://github.com/swoole/swoole-src",
  "ref": "5.1.5",
  "args": "--enable-swoole",
  "libs": "openssl nghttp2"
}
```

**Version Compatibility:**
- Swoole 5.x → PHP 8.0+
- Swoole 4.x → PHP 7.2+

### MongoDB

```json
{
  "name": "mongodb",
  "url": "https://github.com/mongodb/mongo-php-driver",
  "ref": "1.20.1",
  "args": "--with-mongodb",
  "libs": "openssl"
}
```

### YAML

```json
{
  "name": "yaml",
  "url": "https://github.com/php/pecl-file_formats-yaml",
  "ref": "2.2.4",
  "args": "--with-yaml",
  "libs": "libyaml"
}
```

### APCu (Cache)

```json
{
  "name": "apcu",
  "url": "https://github.com/krakjoe/apcu",
  "ref": "5.1.24",
  "args": "--enable-apcu"
}
```

### Memcache

```json
{
  "name": "memcache",
  "url": "https://github.com/websupport-sk/pecl-memcache",
  "ref": "8.2",
  "args": "--enable-memcache"
}
```

### Memcached

```json
{
  "name": "memcached",
  "url": "https://github.com/php-memcached-dev/php-memcached",
  "ref": "3.3.0",
  "args": "--enable-memcached",
  "libs": "libmemcached zlib"
}
```

### IMAP

```json
{
  "name": "imap",
  "url": "https://github.com/php/pecl-mail-imap",
  "ref": "1.0.2",
  "args": "--with-imap",
  "libs": "imap openssl"
}
```

## Advanced Usage

### Build Different Extension Versions by PHP Version

Create a version mapping configuration file `extensions-versions.json`:

```json
{
  "xdebug": {
    "8.4": "3.4.0",
    "8.3": "3.3.2",
    "8.2": "3.3.2",
    "8.1": "3.2.2"
  },
  "redis": {
    "8.4": "6.1.0",
    "8.3": "6.1.0",
    "8.2": "6.0.2",
    "8.1": "5.3.7"
  }
}
```

### Generate Extension Configuration with Script

Create `generate-extensions.sh`:

```bash
#!/bin/bash
PHP_VERSION=$1

case $PHP_VERSION in
  8.4)
    cat << EOF
[
  {"name":"xdebug","url":"https://github.com/xdebug/xdebug","ref":"3.4.0","args":"--enable-xdebug"},
  {"name":"redis","url":"https://github.com/phpredis/phpredis","ref":"6.1.0","args":"--enable-redis"}
]
EOF
    ;;
  8.3)
    cat << EOF
[
  {"name":"xdebug","url":"https://github.com/xdebug/xdebug","ref":"3.3.2","args":"--enable-xdebug"},
  {"name":"redis","url":"https://github.com/phpredis/phpredis","ref":"6.1.0","args":"--enable-redis"}
]
EOF
    ;;
esac
```

### Batch Build Multiple Configurations

Use matrix strategy to build multiple PHP versions and extension combinations:

```yaml
strategy:
  matrix:
    php-version: ['8.2', '8.3', '8.4']
    extension:
      - name: xdebug
        url: https://github.com/xdebug/xdebug
        ref: 3.4.0
      - name: redis
        url: https://github.com/phpredis/phpredis
        ref: 6.1.0
```

## Extension Testing

By default, extensions are tested after building. You can control this behavior:

### Disable Testing

Add to the workflow:
```yaml
run-tests: false
```

### Custom Test Parameters

```yaml
test-runner-args: '--show-diff'
test-workers: 4
```

## Troubleshooting

### Issue 1: Extension Build Failure

**Possible Causes:**
- Extension version incompatible with PHP version
- Missing dependency libraries
- Incorrect build arguments

**Solutions:**
1. Check extension's official documentation for compatibility
2. Ensure `libs` field includes all required dependencies
3. Review build logs for detailed errors

### Issue 2: Dependency Library Not Found

**Solution:**
Ensure correct dependency library names are specified in the `libs` field. Common dependencies:
- `openssl` - OpenSSL
- `zlib` - Zlib compression
- `nghttp2` - HTTP/2 library
- `libmemcached` - Memcached client
- `imagemagick` - ImageMagick image processing
- `imap` - IMAP library
- `libyaml` - YAML parser

### Issue 3: JSON Format Error

**Solution:**
Use a JSON validation tool (like jsonlint.com) to validate configuration:
```bash
# Validate with jq
cat extensions.json | jq .
```

### Issue 4: Extension Version Not Compatible

**Solution:**
Check the extension's documentation or releases page for PHP version compatibility. Some extensions have specific PHP version requirements:

**Example for Xdebug:**
- PHP 8.4 → Use Xdebug 3.4.x
- PHP 8.3 → Use Xdebug 3.3.x or 3.4.x
- PHP 8.2 → Use Xdebug 3.2.x or 3.3.x

## Extension Source URLs

### Official PECL Extensions

Most extensions have GitHub mirrors:
- https://github.com/php/pecl-{category}-{extension}
- Example: https://github.com/php/pecl-file_formats-yaml

### Third-Party Extensions

- Xdebug: https://github.com/xdebug/xdebug
- phpredis: https://github.com/phpredis/phpredis
- Swoole: https://github.com/swoole/swoole-src
- Imagick: https://github.com/Imagick/imagick
- MongoDB: https://github.com/mongodb/mongo-php-driver
- APCu: https://github.com/krakjoe/apcu
- Memcache: https://github.com/websupport-sk/pecl-memcache
- Memcached: https://github.com/php-memcached-dev/php-memcached

## Finding Extension Versions

### Method 1: GitHub Releases

Visit the extension's GitHub repository and check the Releases page.

### Method 2: PECL Website

Visit https://pecl.php.net/ and search for the extension.

### Method 3: Use API

```bash
# View all tags for an extension
curl -s https://api.github.com/repos/xdebug/xdebug/tags | jq '.[].name'

# View latest release
curl -s https://api.github.com/repos/xdebug/xdebug/releases/latest | jq '.tag_name'
```

## Related Resources

- [PHP Windows Builder Official Documentation](https://github.com/php/php-windows-builder)
- [PECL Extension List](https://pecl.php.net/)
- [PHP Extension Development Documentation](https://www.php.net/manual/en/internals2.php)
- [Windows PHP SDK](https://github.com/php/php-sdk-binary-tools)

## Contributing Extension Configurations

Pull requests are welcome to add more popular extension configurations!

Please ensure:
1. Extension builds successfully
2. Correct version compatibility information is specified
3. All required dependency libraries are included

---

📝 Need help? Ask in [Issues](https://github.com/ServBay/PHP-Windows-Portable/issues).
