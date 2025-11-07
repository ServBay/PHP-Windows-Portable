# PHP 扩展构建指南

本指南说明如何使用 GitHub Actions 构建 PHP 扩展。

[中文文档](EXTENSIONS_GUIDE.md) | [English Documentation](../../EXTENSIONS_GUIDE.md)

## 目录
- [快速开始](#快速开始)
- [扩展配置](#扩展配置)
- [常见扩展](#常见扩展)
- [高级用法](#高级用法)

## 快速开始

### 1. 不构建扩展（仅构建 PHP）

在 GitHub Actions 中运行工作流时：
```
版本类型: stable
稳定版版本号: 8.4.14
架构: x64
线程安全: nts
构建扩展: false  ← 不勾选
```

### 2. 构建单个扩展

```
版本类型: stable
稳定版版本号: 8.4.14
架构: x64
线程安全: nts
构建扩展: true  ← 勾选
扩展配置 JSON: [{"name":"xdebug","url":"https://github.com/xdebug/xdebug","ref":"3.4.0","args":"--enable-xdebug"}]
```

### 3. 构建多个扩展

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

### 4. 使用默认扩展

将"扩展配置 JSON"字段留空以使用 8 个默认扩展：

```
版本类型: stable
稳定版版本号: 8.4.14
架构: x64
线程安全: nts
构建扩展: true  ← 勾选
扩展配置 JSON: (留空)  ← 使用默认
```

**默认包含的扩展：**
- xdebug 3.4.0 - 调试器
- redis 6.1.0 - Redis 客户端
- apcu 5.1.24 - APCu 缓存
- imagick 3.7.0 - 图像处理
- memcache 8.2 - Memcache 客户端
- memcached 3.3.0 - Memcached 客户端
- mongodb 1.20.1 - MongoDB 驱动
- imap 1.0.2 - IMAP 扩展

## 扩展配置

### JSON 格式

每个扩展对象包含以下字段：

| 字段 | 必需 | 说明 | 示例 |
|------|------|------|------|
| `name` | ✅ | 扩展名称 | `"xdebug"` |
| `url` | ✅ | Git 仓库地址 | `"https://github.com/xdebug/xdebug"` |
| `ref` | ✅ | Git 引用（tag/branch/commit） | `"3.4.0"` |
| `args` | ✅ | 构建参数 | `"--enable-xdebug"` |
| `libs` | ❌ | 依赖库（空格分隔） | `"openssl zlib"` |

### 配置文件方式

推荐使用 `extensions.example.json` 作为模板：

```bash
cp extensions.example.json extensions.json
# 编辑 extensions.json 配置你需要的扩展
```

然后在 GitHub Actions 中粘贴文件内容到 `扩展配置 JSON` 输入框。

### 默认配置

仓库包含 [extensions.default.json](../../extensions.default.json)，预配置了 8 个流行扩展。当您启用扩展构建而不提供自定义配置时，会自动使用此文件。

## 常见扩展

### Xdebug（调试器）

```json
{
  "name": "xdebug",
  "url": "https://github.com/xdebug/xdebug",
  "ref": "3.4.0",
  "args": "--enable-xdebug"
}
```

**版本兼容性：**
- Xdebug 3.4.x → PHP 8.2, 8.3, 8.4
- Xdebug 3.3.x → PHP 8.1, 8.2, 8.3
- Xdebug 3.2.x → PHP 8.0, 8.1, 8.2

### Redis（缓存）

```json
{
  "name": "redis",
  "url": "https://github.com/phpredis/phpredis",
  "ref": "6.1.0",
  "args": "--enable-redis"
}
```

**版本兼容性：**
- phpredis 6.x → PHP 8.0+
- phpredis 5.x → PHP 7.0+

### Imagick（图像处理）

```json
{
  "name": "imagick",
  "url": "https://github.com/Imagick/imagick",
  "ref": "3.7.0",
  "args": "--with-imagick",
  "libs": "imagemagick"
}
```

**注意：** 需要 ImageMagick 依赖库。

### Swoole（异步框架）

```json
{
  "name": "swoole",
  "url": "https://github.com/swoole/swoole-src",
  "ref": "5.1.5",
  "args": "--enable-swoole",
  "libs": "openssl nghttp2"
}
```

**版本兼容性：**
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

### APCu（缓存）

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

## 高级用法

### 按 PHP 版本构建不同的扩展版本

创建版本映射配置文件 `extensions-versions.json`：

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

### 使用脚本生成扩展配置

创建 `generate-extensions.sh`：

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

### 批量构建多个配置

使用矩阵策略构建多个 PHP 版本和扩展组合：

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

## 扩展测试

默认情况下，扩展构建后会运行测试。可以通过配置控制：

### 禁用测试

在工作流中添加：
```yaml
run-tests: false
```

### 自定义测试参数

```yaml
test-runner-args: '--show-diff'
test-workers: 4
```

## 故障排除

### 问题 1：扩展构建失败

**可能原因：**
- 扩展版本与 PHP 版本不兼容
- 缺少依赖库
- 构建参数错误

**解决方法：**
1. 检查扩展的官方文档确认兼容性
2. 确保 `libs` 字段包含所有必需的依赖库
3. 查看构建日志了解详细错误

### 问题 2：找不到依赖库

**解决方法：**
确保在 `libs` 字段中指定了正确的依赖库名称。常见依赖库：
- `openssl` - OpenSSL
- `zlib` - Zlib 压缩库
- `nghttp2` - HTTP/2 库
- `libmemcached` - Memcached 客户端
- `imagemagick` - ImageMagick 图像处理
- `imap` - IMAP 库
- `libyaml` - YAML 解析器

### 问题 3：JSON 格式错误

**解决方法：**
使用 JSON 验证工具（如 jsonlint.com）验证配置：
```bash
# 使用 jq 验证
cat extensions.json | jq .
```

### 问题 4：扩展版本不兼容

**解决方法：**
检查扩展的文档或发布页面以了解 PHP 版本兼容性。某些扩展对 PHP 版本有特定要求：

**Xdebug 示例：**
- PHP 8.4 → 使用 Xdebug 3.4.x
- PHP 8.3 → 使用 Xdebug 3.3.x 或 3.4.x
- PHP 8.2 → 使用 Xdebug 3.2.x 或 3.3.x

## 扩展源码地址

### 官方 PECL 扩展

大多数扩展在 GitHub 上有镜像：
- https://github.com/php/pecl-{category}-{extension}
- 示例：https://github.com/php/pecl-file_formats-yaml

### 第三方扩展

- Xdebug: https://github.com/xdebug/xdebug
- phpredis: https://github.com/phpredis/phpredis
- Swoole: https://github.com/swoole/swoole-src
- Imagick: https://github.com/Imagick/imagick
- MongoDB: https://github.com/mongodb/mongo-php-driver
- APCu: https://github.com/krakjoe/apcu
- Memcache: https://github.com/websupport-sk/pecl-memcache
- Memcached: https://github.com/php-memcached-dev/php-memcached

## 扩展版本查找

### 方法 1：GitHub Releases

访问扩展的 GitHub 仓库，查看 Releases 页面。

### 方法 2：PECL 官网

访问 https://pecl.php.net/ 搜索扩展。

### 方法 3：使用 API

```bash
# 查看扩展的所有 tags
curl -s https://api.github.com/repos/xdebug/xdebug/tags | jq '.[].name'

# 查看最新 release
curl -s https://api.github.com/repos/xdebug/xdebug/releases/latest | jq '.tag_name'
```

## 相关资源

- [PHP Windows Builder 官方文档](https://github.com/php/php-windows-builder)
- [PECL 扩展列表](https://pecl.php.net/)
- [PHP 扩展开发文档](https://www.php.net/manual/en/internals2.php)
- [Windows PHP SDK](https://github.com/php/php-sdk-binary-tools)

## 贡献扩展配置

欢迎提交 Pull Request 添加更多常用扩展的配置！

请确保：
1. 测试过扩展可以成功构建
2. 指定了正确的版本兼容性信息
3. 包含了所有必需的依赖库

---

📝 需要帮助？请在 [Issues](https://github.com/ServBay/PHP-Windows-Portable/issues) 中提问。
