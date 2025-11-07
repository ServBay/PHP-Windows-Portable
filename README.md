# PHP-Windows-Portable

Automated PHP compilation for Windows using GitHub Actions, built on PHP's official [php-windows-builder](https://github.com/php/php-windows-builder).

**Developed by [ServBay Team](https://www.servbay.com)**

[中文文档](docs/zh-CN/README.md) | [Documentation](README.md)

## ✨ Features

- 🚀 Based on PHP official build tool ([php-windows-builder](https://github.com/php/php-windows-builder))
- 📦 Support multiple PHP versions (stable/testing/development)
- 🔧 Extension building and management
- 🎯 Flexible version and extension configuration
- 🔐 Thread-Safe and Non-Thread-Safe builds
- 🌐 Complete GitHub Actions automation
- ✅ Automated testing and packaging
- 📝 Detailed build information and SHA256 checksums

## 🎯 Why Use This Project?

This project provides a **zero-configuration** way to build PHP for Windows:

- ✅ **No local environment setup needed** - Everything runs on GitHub Actions
- ✅ **Official PHP build tools** - Based on PHP's maintained builder
- ✅ **Extension support** - Build popular extensions automatically
- ✅ **Complete testing** - Runs official PHP tests
- ✅ **Automatic packaging** - Creates release-ready artifacts

## 🚀 Quick Start

### Step 1: Fork this Repository

Fork this repository to your GitHub account.

### Step 2: Go to Actions Tab

Navigate to the **Actions** tab in your forked repository.

### Step 3: Run the Workflow

1. Select **Build PHP for Windows** workflow
2. Click **Run workflow**
3. Fill in the parameters (see examples below)
4. Click **Run workflow** to start

## 📚 Usage Examples

### Example 1: Build Stable PHP with Default Extensions

```yaml
Version Type: stable
Version Number: 8.4.14
Architecture: x64
Thread Safety: nts
Build Extensions: true
Custom Extensions JSON: (leave empty)
Create GitHub Release: true
```

**Included extensions:** xdebug, redis, apcu, imagick, memcache, memcached, mongodb, imap

### Example 2: Build PHP with Custom Extensions

```yaml
Version Type: stable
Version Number: 8.4.14
Architecture: x64
Thread Safety: nts
Build Extensions: true
Custom Extensions JSON: [{"name":"swoole","url":"https://github.com/swoole/swoole-src","ref":"5.1.5","args":"--enable-swoole","libs":"openssl nghttp2"}]
Create GitHub Release: true
```

### Example 3: Build PHP 8.5 Testing Version

```yaml
Version Type: testing
Testing Tag: php-8.5.0RC4
Architecture: x64
Thread Safety: nts
Build Extensions: true
Create GitHub Release: true
```

### Example 4: Build PHP 8.6 Development Version

```yaml
Version Type: development
Dev Commit Hash: 1cf63a93801e02d9f75dde59b849dcfa632b9237
Dev Version: 8.6.0-dev-20251105
Architecture: x64
Thread Safety: nts
Build Extensions: false
Create GitHub Release: true
```

## 📋 Parameters Reference

### Version Configuration

| Parameter | Description | Example |
|-----------|-------------|---------|
| Version Type | stable/testing/development | `stable` |
| Stable Version | PHP stable version | `8.4.14` |
| Testing Tag | GitHub tag name | `php-8.5.0RC4` |
| Dev Commit Hash | Git commit hash | `1cf63a93...` |
| Dev Version | Custom version ID | `8.6.0-dev-20251105` |

### Build Configuration

| Parameter | Description | Options |
|-----------|-------------|---------|
| Architecture | CPU architecture | `x64` / `x86` |
| Thread Safety | Thread safety mode | `nts` / `ts` |

**Recommendation:** Use `nts` for better performance (for Nginx, IIS FastCGI)

### Extension Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| Build Extensions | Build extensions | `true` |
| Custom Extensions JSON | Override defaults | See below |

#### Default Extensions (8 extensions)

- **xdebug 3.4.0** - Debugger
- **redis 6.1.0** - Redis client
- **apcu 5.1.24** - APCu cache
- **imagick 3.7.0** - Image processing
- **memcache 8.2** - Memcache client
- **memcached 3.3.0** - Memcached client
- **mongodb 1.20.1** - MongoDB driver
- **imap 1.0.2** - IMAP extension

#### Custom Extension JSON Format

```json
[
  {
    "name": "extension-name",
    "url": "https://github.com/owner/repo",
    "ref": "tag-or-branch",
    "args": "--enable-extension",
    "libs": "dep1 dep2"
  }
]
```

**See also:**
- [extensions.default.json](extensions.default.json) - Default configuration
- [extensions.example.json](extensions.example.json) - More examples
- [EXTENSIONS_GUIDE.md](EXTENSIONS_GUIDE.md) - Complete guide

### Release Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| Create GitHub Release | Auto-create release | `true` |

## 📦 Build Output

### Artifacts (90-day retention)

- `php-{version}-{type}-{TS/NTS}-Win-{arch}.zip` - PHP build
- `php-{version}-{type}-{TS/NTS}-Win-{arch}.sha256` - Checksum
- `extension-{name}-{version}-{arch}-{TS/NTS}/` - Extension builds

### GitHub Release (Permanent)

Automatically creates release with:
- Complete PHP package with all extensions
- SHA256 checksum
- BUILD_INFO.md (build information)

## 🔍 SHA256 Verification

**Windows PowerShell:**
```powershell
$hash = (Get-FileHash -Path "php-*.zip" -Algorithm SHA256).Hash
$expected = (Get-Content "php-*.sha256")
if ($hash -eq $expected) {
  Write-Host "✓ Verification passed"
} else {
  Write-Host "✗ Verification failed"
}
```

**Linux/macOS:**
```bash
sha256sum -c php-*.sha256
```

## 📚 Documentation

- [Extensions Guide](EXTENSIONS_GUIDE.md) - How to configure extensions
- [PHP 8.6 README](PHP_8.6_README.md) - PHP 8.6 specific information
- [Version Mapping](VERSION_MAPPING.md) - Version compatibility
- [Migration Guide](docs/zh-CN/MIGRATION_v2.md) - Upgrading from v1.x
- [Changelog](CHANGELOG.md) - Version history
- [Contributing](CONTRIBUTING.md) - How to contribute

## ❓ FAQ

### Q: Which build method should I use?

**A:** This project uses GitHub Actions (official builder) - the only recommended method.

**Advantages:**
- ✅ Zero setup - No local environment needed
- ✅ Reliable - Based on officially maintained tools
- ✅ Complete - Native extension support
- ✅ Fast - GitHub's high-performance environment

### Q: NTS or TS?

**A:**
- **NTS (Non-Thread-Safe)** - Recommended
  - For: Nginx + PHP-FPM, IIS FastCGI
  - Better performance

- **TS (Thread-Safe)**
  - For: Apache mod_php
  - Supports multithreading

### Q: How do I build specific extension versions?

**A:** Specify the `ref` field in extension JSON:

```json
{
  "name": "xdebug",
  "url": "https://github.com/xdebug/xdebug",
  "ref": "3.4.0",
  "args": "--enable-xdebug"
}
```

Find extension versions on their GitHub releases/tags page.

### Q: Build failed, what to do?

**A:** Troubleshooting steps:
1. Check Actions logs for specific errors
2. Verify PHP version/tag is correct
3. Verify extension JSON format is valid
4. Check extension compatibility with PHP version

### Q: What extensions are supported?

**A:** All PECL and third-party extensions with source code. Popular ones:
- Xdebug, Redis, Imagick, Swoole, MongoDB
- PDO drivers, GD, ZIP, OpenSSL, cURL
- More: [EXTENSIONS_GUIDE.md](EXTENSIONS_GUIDE.md)

## 🏗️ Technical Architecture

### Workflow Overview

```
User Input → Prepare → Build PHP → Build Extensions → Package → Release
          (Parse)    (Official)  (Official)       (ZIP+SHA256) (GitHub)
```

### Based on PHP Official Builder

Uses [php-windows-builder](https://github.com/php/php-windows-builder):
- Automatic dependency download
- Automatic Visual Studio configuration
- Built-in test runner
- PGO optimization support

## 🔗 Related Resources

- [ServBay - Modern Development Environment](https://www.servbay.com)
- [PHP Official Website](https://www.php.net/)
- [PHP Windows Builder](https://github.com/php/php-windows-builder)
- [PHP SDK Binary Tools](https://github.com/php/php-sdk-binary-tools)
- [PHP Windows Documentation](https://wiki.php.net/internals/windows)
- [PECL Extensions](https://pecl.php.net/)

## 📄 License

This project uses the same license as PHP.

## 🤝 Contributing

Issues and Pull Requests are welcome!

Especially welcome:
- Add more popular extension configurations
- Improve documentation
- Report bugs and issues

See: [CONTRIBUTING.md](CONTRIBUTING.md)

## 🙏 Acknowledgments

This project is developed and maintained by the [ServBay Team](https://www.servbay.com).

Special thanks to:
- PHP development team for [php-windows-builder](https://github.com/php/php-windows-builder)
- All contributors for their support

---

💡 **Tip**: This project is designed for GitHub Actions - simple, fast, and reliable!
