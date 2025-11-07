# 更新日志

[中文文档](CHANGELOG.md) | [English Documentation](../../CHANGELOG.md)

## [2.0.0] - 2025-11-06

### 🎉 重大更新：采用 PHP 官方构建工具

项目完全重构，基于 PHP 官方的 [php-windows-builder](https://github.com/php/php-windows-builder) 实现。

#### 重大变更
- **✅ 新增 GitHub Actions 官方构建器工作流** - 使用 PHP 官方维护的构建工具
- **✅ 扩展构建支持** - 原生支持构建和管理 PHP 扩展
- **✅ 扩展版本管理** - 支持根据 PHP 版本指定不同的扩展版本
- **✅ 更可靠的构建** - 基于官方工具，自动处理依赖和环境
- **⚠️ 废弃手动依赖库下载** - 官方构建器自动处理依赖

#### 新增文件
- `.github/workflows/build.yml` - 基于官方构建器的 GitHub Actions 工作流（英文版）
- `EXTENSIONS_GUIDE.md` - 扩展构建完整指南
- `extensions.default.json` - 默认扩展配置（8 个流行扩展）
- `extensions.example.json` - 扩展配置示例

#### 文档更新
- `README.md` - 完全重写为英文，推荐使用官方构建器
- 多语言支持，中文文档位于 docs/zh-CN/
- `VERSION_MAPPING.md` - 说明版本号映射系统
- 保留旧的中文文档作为参考

#### 构建架构对比

**新架构（推荐）：**
```
用户输入 → PHP 官方构建器 → 扩展构建器 → 打包发布
```

**旧架构（保留）：**
```
用户输入 → 手动下载依赖 → 批处理脚本编译 → 打包发布
```

#### 扩展功能
- 支持任意 PECL 和第三方扩展
- 灵活的版本配置（JSON 格式）
- 自动运行扩展测试
- 矩阵构建支持
- 包含 8 个默认流行扩展

#### 默认包含的扩展
- xdebug 3.4.0 - 调试器
- redis 6.1.0 - Redis 客户端
- apcu 5.1.24 - APCu 缓存
- imagick 3.7.0 - 图像处理
- memcache 8.2 - Memcache 客户端
- memcached 3.3.0 - Memcached 客户端
- mongodb 1.20.1 - MongoDB 驱动
- imap 1.0.2 - IMAP 扩展

#### 兼容性说明
- 旧的批处理脚本（build_all.bat, build_deps.bat 等）继续保留
- 本地构建方式仍然可用
- 推荐新项目使用官方构建器

## [1.2.1] - 2025-11-06

### 修复
- **路径问题修复** - 修复 GitHub Actions 中 PHP SDK 和依赖库路径问题
  - PHP SDK 现在正确解压到 D:\a\php\php-sdk-binary-tools-2.5.0
  - 依赖库现在正确下载到 D:\a\php\deps
  - 添加基于 PHP 版本自动选择依赖库版本的逻辑

### 改进
- **版本号统一** - 所有文档和配置中的默认版本统一为 8.4.4
  - 与 CHANGELOG v1.2 保持一致
  - 使用当前最新稳定版作为示例

## [1.2] - 2025-11-06

### 重大更新
- **GitHub Actions 完整重构** - 支持稳定版、测试版、开发版的自动化构建
  - 稳定版：从 php.net 下载（如 8.4.4）
  - 测试版：从 GitHub tags 下载（如 php-8.5.0beta2、php-8.5.0RC4）
  - 开发版：从 GitHub commit 下载（支持指定 commit hash）

### 新增
- **版本类型选择器** - 在 GitHub Actions 中可选择版本类型
- **Commit hash 支持** - 可以构建特定 commit 的开发版
- **自动发布功能** - 构建完成后自动创建 GitHub Release
- **SHA256 校验和** - 自动生成并附带校验文件
- **BUILD_INFO.md** - 包含完整构建信息的文档
- **GITHUB_ACTIONS_GUIDE.md** - GitHub Actions 详细使用指南

### 改进
- download_php.bat 现在支持三种参数格式：
  - 稳定版：`download_php.bat 8.4.4`
  - 测试版：`download_php.bat php-8.5.0beta2`
  - 开发版：`download_php.bat 8.6.0-dev-20251105 . 1cf63a93801e02d9f75dde59b849dcfa632b9237`
- GitHub Actions 工作流优化：
  - 更详细的日志输出
  - 更好的错误处理
  - 支持 tar.gz 和 zip 格式解压
  - Artifacts 保留期延长至 90 天

### 文档
- 新增 GitHub Actions 使用指南
- 更新 README 添加 GA 说明
- 更新示例和用法说明

## [1.1] - 2025-11-06

### 新增
- **download_php.bat** - PHP 源码下载辅助脚本
  - 自动识别版本类型（稳定版/开发版）
  - 支持从 php.net 下载稳定版
  - 支持从 GitHub tags 下载 PHP 8.5.x
  - 支持从 GitHub master 下载 PHP 8.6.x-dev
  - 自动解压并重命名到标准目录

- 开发版 PHP 支持
  - PHP 8.5.x：从 GitHub releases/tags 获取
  - PHP 8.6.x-dev：从 GitHub master 分支获取
  - 完整的编译流程支持

### 更改
- 更新 PHP SDK 版本从 2.3.0 到 2.5.0
- 更新 setup.bat 添加开发版选项
- 更新 GitHub Actions 工作流支持开发版下载
- 更新文档说明开发版编译流程

### 改进
- 增强版本检测逻辑
- 改进错误处理
- 更新所有示例使用最新版本

## [1.0] - 2025-11-06

### 新增
- 初始版本发布
- **build_all.bat** - PHP 主编译脚本
- **build_deps.bat** - 依赖库编译脚本
- **setup.bat** - 环境快速设置脚本
- GitHub Actions CI/CD 工作流
- 完整的文档系统
  - README.md - 项目说明
  - CONTRIBUTING.md - 贡献指南
  - PROJECT_OVERVIEW.md - 项目概览

### 特性
- 支持 PHP 8.4.2 编译
- 支持 Thread-Safe 和 Non-Thread-Safe 构建
- 支持 Release 和 Debug 构建
- 12+ 依赖库支持
- 与 Apache-Windows 依赖库兼容
- 环境变量配置支持
