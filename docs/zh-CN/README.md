# PHP-Windows-Portable

基于 PHP 官方的 [php-windows-builder](https://github.com/php/php-windows-builder)，使用 GitHub Actions 自动化构建 Windows 版 PHP。

**由 [ServBay 团队](https://www.servbay.com) 开发**

[中文文档](README.md) | [English Documentation](../../README.md)

## ✨ 特性

- 🚀 基于 PHP 官方构建工具 ([php-windows-builder](https://github.com/php/php-windows-builder))
- 📦 支持多个 PHP 版本（稳定版/测试版/开发版）
- 🔧 扩展构建和管理
- 🎯 灵活的版本和扩展配置
- 🔐 Thread-Safe 和 Non-Thread-Safe 构建
- 🌐 完整的 GitHub Actions 自动化
- ✅ 自动化测试和打包
- 📝 详细的构建信息和 SHA256 校验和

## 🎯 为什么使用这个项目？

本项目提供了一种**零配置**的 Windows PHP 构建方式：

- ✅ **无需本地环境设置** - 一切都在 GitHub Actions 上运行
- ✅ **官方 PHP 构建工具** - 基于 PHP 维护的构建器
- ✅ **扩展支持** - 自动构建流行扩展
- ✅ **完整测试** - 运行官方 PHP 测试
- ✅ **自动打包** - 创建可发布的构建产物

## 🚀 快速开始

### 第一步：Fork 此仓库

将此仓库 Fork 到你的 GitHub 账户。

### 第二步：进入 Actions 标签页

在你 Fork 的仓库中，进入 **Actions** 标签页。

### 第三步：运行工作流

1. 选择 **Build PHP for Windows** 工作流
2. 点击 **Run workflow**
3. 填写参数（参见下面的示例）
4. 点击 **Run workflow** 开始构建

## 📚 使用示例

### 示例 1：构建稳定版 PHP（使用默认扩展）

```yaml
版本类型: stable
版本号: 8.4.14
架构: x64
线程安全: nts
构建扩展: true
自定义扩展 JSON: (留空)
创建 GitHub Release: true
```

**包含的扩展：** xdebug, redis, apcu, imagick, memcache, memcached, mongodb, imap

### 示例 2：构建自定义扩展的 PHP

```yaml
版本类型: stable
版本号: 8.4.14
架构: x64
线程安全: nts
构建扩展: true
自定义扩展 JSON: [{"name":"swoole","url":"https://github.com/swoole/swoole-src","ref":"5.1.5","args":"--enable-swoole","libs":"openssl nghttp2"}]
创建 GitHub Release: true
```

### 示例 3：构建 PHP 8.5 测试版

```yaml
版本类型: testing
测试版标签: php-8.5.0RC4
架构: x64
线程安全: nts
构建扩展: true
创建 GitHub Release: true
```

### 示例 4：构建 PHP 8.6 开发版

```yaml
版本类型: development
开发版 Commit Hash: 1cf63a93801e02d9f75dde59b849dcfa632b9237
开发版版本号: 8.6.0-dev-20251105
架构: x64
线程安全: nts
构建扩展: false
创建 GitHub Release: true
```

## 📋 参数说明

### 版本配置

| 参数 | 说明 | 示例 |
|------|------|------|
| 版本类型 | stable/testing/development | `stable` |
| 稳定版版本号 | PHP 稳定版版本号 | `8.4.14` |
| 测试版标签 | GitHub 标签名 | `php-8.5.0RC4` |
| 开发版 Commit Hash | Git commit 哈希 | `1cf63a93...` |
| 开发版版本号 | 自定义版本标识 | `8.6.0-dev-20251105` |

### 构建配置

| 参数 | 说明 | 选项 |
|------|------|------|
| 架构 | CPU 架构 | `x64` / `x86` |
| 线程安全 | 线程安全模式 | `nts` / `ts` |

**推荐：** 使用 `nts` 以获得更好的性能（适用于 Nginx、IIS FastCGI）

### 扩展配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| 构建扩展 | 构建扩展 | `true` |
| 自定义扩展 JSON | 覆盖默认配置 | 见下文 |

#### 默认扩展（8 个）

- **xdebug 3.4.0** - 调试器
- **redis 6.1.0** - Redis 客户端
- **apcu 5.1.24** - APCu 缓存
- **imagick 3.7.0** - 图像处理
- **memcache 8.2** - Memcache 客户端
- **memcached 3.3.0** - Memcached 客户端
- **mongodb 1.20.1** - MongoDB 驱动
- **imap 1.0.2** - IMAP 扩展

#### 自定义扩展 JSON 格式

```json
[
  {
    "name": "扩展名称",
    "url": "https://github.com/owner/repo",
    "ref": "标签或分支",
    "args": "--enable-extension",
    "libs": "dep1 dep2"
  }
]
```

**另见：**
- [extensions.default.json](../../extensions.default.json) - 默认配置
- [extensions.example.json](../../extensions.example.json) - 更多示例
- [EXTENSIONS_GUIDE.md](EXTENSIONS_GUIDE.md) - 完整指南

### 发布选项

| 参数 | 说明 | 默认值 |
|------|------|--------|
| 创建 GitHub Release | 自动创建发布 | `true` |

## 📦 构建输出

### Artifacts（90 天保留期）

- `php-{version}-{type}-{TS/NTS}-Win-{arch}.zip` - PHP 构建包
- `php-{version}-{type}-{TS/NTS}-Win-{arch}.sha256` - 校验和
- `extension-{name}-{version}-{arch}-{TS/NTS}/` - 扩展构建包

### GitHub Release（永久保留）

自动创建发布，包含：
- 包含所有扩展的完整 PHP 包
- SHA256 校验和
- BUILD_INFO.md（构建信息）

## 🔍 SHA256 验证

**Windows PowerShell:**
```powershell
$hash = (Get-FileHash -Path "php-*.zip" -Algorithm SHA256).Hash
$expected = (Get-Content "php-*.sha256")
if ($hash -eq $expected) {
  Write-Host "✓ 验证通过"
} else {
  Write-Host "✗ 验证失败"
}
```

**Linux/macOS:**
```bash
sha256sum -c php-*.sha256
```

## 📚 文档

- [扩展指南](EXTENSIONS_GUIDE.md) - 如何配置扩展
- [PHP 8.6 说明](../../PHP_8.6_README.md) - PHP 8.6 特定信息
- [版本映射](VERSION_MAPPING.md) - 版本兼容性
- [迁移指南](MIGRATION_v2.md) - 从 v1.x 升级
- [更新日志](CHANGELOG.md) - 版本历史
- [贡献指南](CONTRIBUTING.md) - 如何贡献

## ❓ 常见问题

### Q: 应该使用哪种构建方式？

**A:** 本项目使用 GitHub Actions（官方构建器）- 唯一推荐的方法。

**优势：**
- ✅ 零设置 - 无需本地环境
- ✅ 可靠 - 基于官方维护的工具
- ✅ 完整 - 原生扩展支持
- ✅ 快速 - GitHub 的高性能环境

### Q: NTS 还是 TS？

**A:**
- **NTS (Non-Thread-Safe)** - 推荐
  - 适用于：Nginx + PHP-FPM、IIS FastCGI
  - 性能更好

- **TS (Thread-Safe)**
  - 适用于：Apache mod_php
  - 支持多线程

### Q: 如何构建特定扩展版本？

**A:** 在扩展 JSON 中指定 `ref` 字段：

```json
{
  "name": "xdebug",
  "url": "https://github.com/xdebug/xdebug",
  "ref": "3.4.0",
  "args": "--enable-xdebug"
}
```

在扩展的 GitHub releases/tags 页面查找版本。

### Q: 构建失败怎么办？

**A:** 故障排除步骤：
1. 检查 Actions 日志以了解具体错误
2. 验证 PHP 版本/标签是否正确
3. 验证扩展 JSON 格式是否有效
4. 检查扩展版本与 PHP 的兼容性

### Q: 支持哪些扩展？

**A:** 所有有源代码的 PECL 和第三方扩展。流行的有：
- Xdebug、Redis、Imagick、Swoole、MongoDB
- PDO 驱动、GD、ZIP、OpenSSL、cURL
- 更多：[EXTENSIONS_GUIDE.md](EXTENSIONS_GUIDE.md)

## 🏗️ 技术架构

### 工作流概览

```
用户输入 → 准备 → 构建 PHP → 构建扩展 → 打包 → 发布
        (解析)  (官方)    (官方)      (ZIP+SHA256) (GitHub)
```

### 基于 PHP 官方构建器

使用 [php-windows-builder](https://github.com/php/php-windows-builder)：
- 自动依赖下载
- 自动 Visual Studio 配置
- 内置测试运行器
- PGO 优化支持

## 🔗 相关资源

- [ServBay - 现代化开发环境](https://www.servbay.com)
- [PHP 官方网站](https://www.php.net/)
- [PHP Windows Builder](https://github.com/php/php-windows-builder)
- [PHP SDK Binary Tools](https://github.com/php/php-sdk-binary-tools)
- [PHP Windows 文档](https://wiki.php.net/internals/windows)
- [PECL 扩展](https://pecl.php.net/)

## 📄 许可证

本项目使用与 PHP 相同的许可证。

## 🤝 贡献

欢迎提交 Issues 和 Pull Requests！

特别欢迎：
- 添加更多流行扩展配置
- 完善文档
- 报告 bug 和问题

参见：[CONTRIBUTING.md](CONTRIBUTING.md)

## 🙏 致谢

本项目由 [ServBay 团队](https://www.servbay.com) 开发和维护。

特别感谢：
- PHP 开发团队的 [php-windows-builder](https://github.com/php/php-windows-builder)
- 所有贡献者的支持

---

💡 **提示**：本项目专为 GitHub Actions 设计 - 简单、快速、可靠！
