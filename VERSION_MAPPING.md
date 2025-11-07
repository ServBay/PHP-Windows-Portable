# PHP Version Number Mapping

This document explains the version number handling logic in the GitHub Actions workflow.

[中文文档](docs/zh-CN/VERSION_MAPPING.md) | [Documentation](VERSION_MAPPING.md)

## Version Number Types

The workflow handles three types of version numbers:

| Version Number | Purpose | Example |
|----------------|---------|---------|
| **php-version** | User input identifier, used for package naming | `8.4.14`, `8.5.0beta2`, `8.6.0-dev-20251105` |
| **php-source** | Git checkout reference | `php-8.4.14`, `php-8.5.0beta2`, `<commit>`, `master` |
| **php-build-version** | Version passed to official builder | `8.4.14`, `8.5`, `master` |

## Mapping Rules

### Stable Version (stable)

```yaml
User input: 8.4.14
├─ php-version: 8.4.14          # For package naming
├─ php-source: php-8.4.14       # Git tag (add php- prefix)
└─ php-build-version: 8.4.14    # Builder version number
```

**Example:**
```yaml
Version Type: stable
Stable Version: 8.4.14
```

**Result:**
- Download source: `git checkout php-8.4.14`
- Build command: Uses PHP 8.4.14 configuration
- Output package: `php-8.4.14-stable-nts-Win-x64.zip`

### Testing Version (testing)

```yaml
User input: php-8.5.0beta2
├─ php-version: 8.5.0beta2      # For package naming (strip php- prefix)
├─ php-source: php-8.5.0beta2   # Git tag (keep as-is)
└─ php-build-version: 8.5       # Extract major version
```

**Example:**
```yaml
Version Type: testing
Testing Tag: php-8.5.0beta2
```

**Result:**
- Download source: `git checkout php-8.5.0beta2`
- Build command: Uses PHP 8.5 configuration
- Output package: `php-8.5.0beta2-test-nts-Win-x64.zip`

### Development Version (development)

#### With Specific Commit

```yaml
User input:
  - commit: 1cf63a93801e02d9f75dde59b849dcfa632b9237
  - version: 8.6.0-dev-20251105

Result:
├─ php-version: 8.6.0-dev-20251105    # For package naming
├─ php-source: 1cf63a93801e02d9f...    # Git commit hash
└─ php-build-version: master          # Always use master config
```

**Example:**
```yaml
Version Type: development
Dev Commit Hash: 1cf63a93801e02d9f75dde59b849dcfa632b9237
Dev Version: 8.6.0-dev-20251105
```

**Result:**
- Download source: `git checkout 1cf63a93801e02d9f75dde59b849dcfa632b9237`
- Build command: Uses master configuration
- Output package: `php-8.6.0-dev-20251105-dev-nts-Win-x64.zip`

#### Without Specific Commit (Latest Code)

```yaml
User input:
  - commit: (leave empty)
  - version: 8.6.0-dev-latest

Result:
├─ php-version: 8.6.0-dev-latest    # For package naming
├─ php-source: master               # Git branch
└─ php-build-version: master        # Always use master config
```

**Example:**
```yaml
Version Type: development
Dev Commit Hash: (leave empty)
Dev Version: 8.6.0-dev-latest
```

**Result:**
- Download source: `git checkout master`
- Build command: Uses master configuration
- Output package: `php-8.6.0-dev-latest-dev-nts-Win-x64.zip`

## Why php-build-version?

### The Problem

The official PHP builder (php-windows-builder) needs to identify the PHP version to determine which Visual Studio version to use:

```
PHP 7.0-7.1  → VS 2015 (vc14)
PHP 7.2-8.3  → VS 2017/2019 (vs16)
PHP 8.4+     → VS 2022 (vs17)
```

However:
- The official builder doesn't recognize custom version identifiers like `8.6.0-dev-20251105`
- The official builder only supports version numbers defined in configuration files
- `master` is a special value that always uses the latest VS configuration

### The Solution

Introduce `php-build-version`:
- **Stable**: Use full version number (e.g., `8.4.14`)
- **Testing**: Extract major version (e.g., `8.5`)
- **Development**: Always use `master`

This preserves the user's custom version identifier (for package naming) while allowing the official builder to correctly recognize the version.

## Version Extraction Logic

### Bash Script Implementation

```bash
case "$VERSION_TYPE" in
  stable)
    PHP_VERSION="${{ github.event.inputs.stable_version }}"
    PHP_SOURCE="php-$PHP_VERSION"
    PHP_BUILD_VERSION="$PHP_VERSION"
    ;;
  testing)
    TAG="${{ github.event.inputs.testing_tag }}"
    PHP_VERSION="${TAG#php-}"
    PHP_SOURCE="$TAG"
    # Extract major version: 8.5.0beta2 -> 8.5
    PHP_BUILD_VERSION=$(echo "$PHP_VERSION" | cut -d'.' -f1,2)
    ;;
  development)
    COMMIT="${{ github.event.inputs.dev_commit }}"
    PHP_VERSION="${{ github.event.inputs.dev_version }}"
    if [ -n "$COMMIT" ]; then
      PHP_SOURCE="$COMMIT"
    else
      PHP_SOURCE="master"
    fi
    # Development always uses master
    PHP_BUILD_VERSION="master"
    ;;
esac
```

## Usage Recommendations

### Production Environment

```yaml
Version Type: stable
Stable Version: 8.4.14  ← Use latest stable
```

### Test Pre-release Features

```yaml
Version Type: testing
Testing Tag: php-8.5.0RC4  ← Use RC version
```

### Test Latest Development Code

```yaml
Version Type: development
Dev Commit Hash: (leave empty)  ← Use master latest
Dev Version: 8.6.0-dev-latest
```

### Build Specific Historical Version

```yaml
Version Type: development
Dev Commit Hash: 1cf63a93801e02d9f75dde59b849dcfa632b9237
Dev Version: 8.6.0-dev-20251105
```

## Debugging Tips

### View Version Mapping Results

In the GitHub Actions logs "Determine PHP Version and Source" step, you'll see:

```
PHP Version: 8.6.0-dev-20251105
PHP Source: 1cf63a93801e02d9f75dde59b849dcfa632b9237
PHP Build Version: master
Version Type: development
```

Check if these values match expectations.

### Common Errors

#### Error 1: Builder Version Not Supported

```
Error: The property '8.6' cannot be found on this object.
```

**Cause:** Official builder doesn't recognize `8.6` version number.

**Solution:** Fixed, development versions now use `master` uniformly.

#### Error 2: Git Checkout Failed

```
Error: The process 'git.exe' failed with exit code 1
```

**Cause:** Git reference doesn't exist.

**Check:**
1. Did stable version add `php-` prefix?
2. Does testing tag exist?
3. Is development commit hash correct?

## Related Files

- `.github/workflows/build.yml` - Workflow definition
- `README.md` - Usage guide
- `EXTENSIONS_GUIDE.md` - Extension building guide

---

Have questions? Refer to [README.md](README.md) or submit an [Issue](https://github.com/ServBay/PHP-Windows-Portable/issues).
