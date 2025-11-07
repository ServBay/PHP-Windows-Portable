# PHP 8.6 支持说明

## 概述

PHP 8.6 是当前的开发版本（master 分支），由于 PHP 8.6 引入了重大的内部 API 变更，许多 PECL 扩展需要补丁才能编译。

## 支持的扩展

对于 PHP 8.6，目前支持以下扩展：

### ✅ 完全支持

1. **redis (phpredis 6.2.0)**
   - 需要补丁：`patch/php8.5/phpredis-6.2.0-php8.5.patch` + `patch/php8.6/phpredis.patch`
   - 状态：编译成功

2. **imagick (3.8.0)**
   - 需要补丁：`patch/php8.4/imagick.patch` + `patch/php8.5/imagick.c.diff`
   - 状态：编译成功
   - 说明：使用 PHP 8.4 和 8.5 补丁即可在 8.6 上工作

3. **memcache (8.2)**
   - 需要补丁：`patch/php8.5/memcache.diff` + `patch/php8.6/memcache.patch`
   - 状态：编译成功

4. **memcached (3.4.0)**
   - 需要补丁：`patch/php8.5/memcached.diff` + `patch/php8.6/memcached.patch`
   - 状态：编译成功

5. **imap (1.0.3)**
   - 需要补丁：无需补丁
   - 状态：编译成功
   - 说明：PECL imap 1.0.3 原生支持 PHP 8.6

## 不支持的扩展

以下扩展在 PHP 8.6 中暂不支持（缺少必要的 PHP 8.6 补丁）：

### ❌ 缺少 PHP 8.6 补丁

1. **xdebug**
   - 原因：只有 PHP 8.5 补丁，缺少 PHP 8.6 补丁
   - 建议：等待 xdebug 官方支持 PHP 8.6

## PHP 8.6 主要 API 变更

### 1. Zval 操作函数变更
- `zval_dtor()` → `zval_ptr_dtor_nogc()`
- `ZVAL_IS_NULL()` → `Z_ISNULL_P()`
- `zval_is_true()` → `zend_is_true()`

### 2. 头文件路径变更
- `ext/standard/php_smart_string.h` → `Zend/zend_smart_string.h`

### 3. 异常处理变更
- `zend_exception_get_default()` → `zend_ce_exception`

## 补丁应用顺序

对于支持的扩展，补丁按以下顺序应用：

1. 先应用 PHP 8.5 补丁或 .diff 文件
2. 再应用 PHP 8.6 补丁

示例（redis）：
```bash
patch -p0 < patch/php8.5/phpredis-6.2.0-php8.5.patch
patch -p0 < patch/php8.6/phpredis.patch
```

## 使用建议

### 生产环境
- **不推荐**在生产环境使用 PHP 8.6
- PHP 8.6 是开发版本，API 可能继续变化
- 建议使用稳定版本（PHP 8.3 或 8.4）

### 开发测试
- 可以使用 PHP 8.6 进行兼容性测试
- 支持的扩展：redis, imagick, memcache, memcached, imap
- 如果项目依赖 xdebug，请使用 PHP 8.5 或更早版本

## 构建配置

### 自动选择
workflow 会自动检测 PHP 版本：
- PHP 8.6 (development) → 使用 `extensions.php8.6.json`（只包含支持的扩展）
- 其他版本 → 使用 `extensions.default.json`（完整扩展列表）

### 手动配置
如需自定义扩展列表，可以在触发 workflow 时提供 `extensions_json` 参数。

## 参考资料

- [PHP 8.6 补丁详情](../ServBay-Utility/runtime/patch/php8.6/README.md)
- [PHP 8.6 变更日志](https://www.php.net/ChangeLog-8.php#PHP_8_6)
- [PHP Internals](https://www.php.net/manual/en/internals2.php)

## 更新计划

我们会持续关注以下扩展的 PHP 8.6 支持情况：

- [x] redis - ✅ 已支持（使用 PHP 8.5 + 8.6 补丁）
- [x] imagick - ✅ 已支持（使用 PHP 8.4 + 8.5 补丁）
- [x] memcache - ✅ 已支持（使用 PHP 8.5 + 8.6 补丁）
- [x] memcached - ✅ 已支持（使用 PHP 8.5 + 8.6 补丁）
- [x] imap - ✅ 已支持（原生支持，无需补丁）
- [ ] xdebug - 等待官方支持或创建补丁

一旦 xdebug 有 PHP 8.6 补丁可用，我们会及时更新此项目。
