# Changelog

[中文文档](docs/zh-CN/CHANGELOG.md) | [Documentation](CHANGELOG.md)

## [2.0.0] - 2025-11-06

### 🎉 Major Update: Adopting PHP Official Build Tool

Project completely refactored based on PHP official [php-windows-builder](https://github.com/php/php-windows-builder).

#### Breaking Changes
- **✅ New GitHub Actions Official Builder Workflow** - Uses PHP officially maintained build tools
- **✅ Extension Building Support** - Native support for building and managing PHP extensions
- **✅ Extension Version Management** - Support specifying different extension versions by PHP version
- **✅ More Reliable Builds** - Based on official tools, automatically handles dependencies and environment
- **⚠️ Deprecated Manual Dependency Downloads** - Official builder automatically handles dependencies

#### New Files
- `.github/workflows/build.yml` - GitHub Actions workflow based on official builder (English version)
- `EXTENSIONS_GUIDE.md` - Complete extension building guide
- `extensions.default.json` - Default extensions configuration (8 popular extensions)
- `extensions.example.json` - Extension configuration examples

#### Documentation Updates
- `README.md` - Completely rewritten in English, recommends using official builder
- Multilingual support with docs/zh-CN/ for Chinese documentation
- `VERSION_MAPPING.md` - Explains version number mapping system
- Preserved old Chinese docs as reference

#### Build Architecture Comparison

**New Architecture (Recommended):**
```
User Input → PHP Official Builder → Extension Builder → Package & Release
```

**Old Architecture (Preserved):**
```
User Input → Manual Dependency Download → Batch Script Compile → Package & Release
```

#### Extension Features
- Support for any PECL and third-party extensions
- Flexible version configuration (JSON format)
- Automatic extension testing
- Matrix build support
- Default 8 popular extensions included

#### Default Extensions Included
- xdebug 3.4.0 - Debugger
- redis 6.1.0 - Redis client
- apcu 5.1.24 - APCu cache
- imagick 3.7.0 - Image processing
- memcache 8.2 - Memcache client
- memcached 3.3.0 - Memcached client
- mongodb 1.20.1 - MongoDB driver
- imap 1.0.2 - IMAP extension

#### Compatibility Notes
- Old batch scripts (build_all.bat, build_deps.bat, etc.) are preserved
- Local build approach still available
- Recommended for new projects to use official builder

## [1.2.1] - 2025-11-06

### Fixed
- **Path Issues Fixed** - Fixed PHP SDK and dependency library paths in GitHub Actions
  - PHP SDK now correctly extracted to D:\a\php\php-sdk-binary-tools-2.5.0
  - Dependencies now correctly downloaded to D:\a\php\deps
  - Added logic to automatically select dependency version based on PHP version

### Improved
- **Version Number Unified** - Default version unified to 8.4.4 across all documentation and configuration
  - Consistent with CHANGELOG v1.2
  - Uses current latest stable version as example

## [1.2] - 2025-11-06

### Major Updates
- **Complete GitHub Actions Refactoring** - Support automated builds for stable, testing, and development versions
  - Stable: Download from php.net (e.g., 8.4.4)
  - Testing: Download from GitHub tags (e.g., php-8.5.0beta2, php-8.5.0RC4)
  - Development: Download from GitHub commit (supports specific commit hash)

### Added
- **Version Type Selector** - Choose version type in GitHub Actions
- **Commit Hash Support** - Can build development version of specific commit
- **Automatic Release Function** - Automatically creates GitHub Release after build
- **SHA256 Checksum** - Automatically generates and includes checksum file
- **BUILD_INFO.md** - Document containing complete build information
- **GitHub Actions Guide** - Detailed usage guide for GitHub Actions

### Improved
- download_php.bat now supports three parameter formats:
  - Stable: `download_php.bat 8.4.4`
  - Testing: `download_php.bat php-8.5.0beta2`
  - Development: `download_php.bat 8.6.0-dev-20251105 . 1cf63a93801e02d9f75dde59b849dcfa632b9237`
- GitHub Actions workflow optimizations:
  - More detailed log output
  - Better error handling
  - Support for tar.gz and zip format extraction
  - Artifact retention extended to 90 days

### Documentation
- Added GitHub Actions usage guide
- Updated README with GA instructions
- Updated examples and usage instructions

## [1.1] - 2025-11-06

### Added
- **download_php.bat** - PHP source code download helper script
  - Automatically identifies version type (stable/development)
  - Supports downloading stable version from php.net
  - Supports downloading PHP 8.5.x from GitHub tags
  - Supports downloading PHP 8.6.x-dev from GitHub master
  - Automatic extraction and renaming to standard directory

- Development version PHP support
  - PHP 8.5.x: Fetch from GitHub releases/tags
  - PHP 8.6.x-dev: Fetch from GitHub master branch
  - Complete compilation process support

### Changed
- Updated PHP SDK version from 2.3.0 to 2.5.0
- Updated setup.bat to add development version options
- Updated GitHub Actions workflow to support development version downloads
- Updated documentation explaining development version compilation process

### Improved
- Enhanced version detection logic
- Improved error handling
- Updated all examples to use latest versions

## [1.0] - 2025-11-06

### Added
- Initial version release
- **build_all.bat** - PHP main compilation script
- **build_deps.bat** - Dependency library compilation script
- **setup.bat** - Environment quick setup script
- GitHub Actions CI/CD workflow
- Complete documentation system
  - README.md - Project description
  - CONTRIBUTING.md - Contributing guide
  - PROJECT_OVERVIEW.md - Project overview

### Features
- Support PHP 8.4.2 compilation
- Support Thread-Safe and Non-Thread-Safe builds
- Support Release and Debug builds
- 12+ dependency libraries support
- Compatible with Apache-Windows dependency libraries
- Environment variable configuration support
