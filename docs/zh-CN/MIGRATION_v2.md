# 迁移指南：v1.x → v2.0.0

## 🎉 v2.0.0 重大更新

项目已完全重构，基于 PHP 官方的 [php-windows-builder](https://github.com/php/php-windows-builder) 实现。

## 主要变化

### ✅ 新增功能

1. **PHP 官方构建器集成**
   - 自动处理依赖库
   - 自动配置环境
   - 更可靠的构建流程

2. **扩展构建支持**
   - 原生支持任意 PECL 和第三方扩展
   - JSON 配置管理
   - 自动运行扩展测试
   - 灵活的版本映射

3. **新的 GitHub Actions 工作流**
   - `build-official.yml` - 基于官方构建器（推荐）
   - `build.yml` - 传统构建方式（保留）

### ⚠️ 变化点

| 方面 | v1.x | v2.0.0 |
|------|------|--------|
| 依赖库下载 | 手动下载/指定路径 | 自动处理 |
| 扩展支持 | 需手动修改脚本 | JSON 配置 |
| 构建工具 | 批处理脚本 | PHP 官方工具 |
| 推荐方式 | 本地构建 | GitHub Actions |

## 迁移步骤

### GitHub Actions 用户

#### 步骤 1：切换到新工作流

1. 进入 **Actions** 标签
2. 选择 **Build PHP for Windows (Official Builder)**（新工作流）
3. 不再使用旧的 "Build PHP for Windows" 工作流

#### 步骤 2：使用新的参数格式

**v1.x 参数：**
```
版本类型: stable
稳定版版本号: 8.4.14
构建类型: Release
线程安全: FALSE
```

**v2.0.0 参数：**
```
版本类型: stable
稳定版版本号: 8.4.14
架构: x64
线程安全: nts  ← 注意：改为 nts/ts
构建扩展: false  ← 新增
```

#### 步骤 3：添加扩展（可选）

**新功能：** 现在可以在构建 PHP 时同时构建扩展！

```yaml
构建扩展: true
扩展配置 JSON: [{"name":"xdebug","url":"https://github.com/xdebug/xdebug","ref":"3.4.0","args":"--enable-xdebug"}]
```

详见：[扩展构建指南](EXTENSIONS_GUIDE.md)

### 本地构建用户

**好消息：** 无需迁移！

所有旧的批处理脚本继续可用：
- `build_all.bat`
- `build_deps.bat`
- `download_php.bat`
- `setup.bat`

但推荐尝试 GitHub Actions 官方构建器，更简单更可靠。

## 常见问题

### Q1: 旧的工作流还能用吗？

**A:** 可以，但不推荐。

- `build.yml`（旧工作流）继续保留
- 但存在依赖库路径问题（已知问题）
- 推荐使用 `build-official.yml`（新工作流）

### Q2: 依赖库在哪里？

**A:** 不需要手动下载！

- v1.x：需要手动下载 deps-8.4-vs17-x64.zip
- v2.0.0：PHP 官方构建器自动处理

### Q3: 如何构建扩展？

**A:** 使用新的 JSON 配置：

```json
[
  {
    "name": "xdebug",
    "url": "https://github.com/xdebug/xdebug",
    "ref": "3.4.0",
    "args": "--enable-xdebug"
  }
]
```

复制到 GitHub Actions 的"扩展配置 JSON"输入框。

完整指南：[EXTENSIONS_GUIDE.md](EXTENSIONS_GUIDE.md)

### Q4: 线程安全参数变了？

**A:** 是的，更符合行业标准：

- v1.x: `FALSE` / `TRUE`
- v2.0.0: `nts` / `ts`

| 旧参数 | 新参数 | 说明 |
|--------|--------|------|
| `FALSE` | `nts` | Non-Thread-Safe |
| `TRUE` | `ts` | Thread-Safe |

### Q5: 为什么要切换到官方构建器？

**A:** 多个优势：

1. **更可靠** - PHP 官方维护
2. **更简单** - 自动处理依赖
3. **更强大** - 原生支持扩展
4. **更新快** - 跟随 PHP 官方更新

### Q6: 本地构建方式会废弃吗？

**A:** 不会！

- 批处理脚本继续保留
- 适合需要高度定制的场景
- 但推荐新用户使用 GitHub Actions

### Q7: 扩展版本如何管理？

**A:** 两种方式：

**方式 1：直接指定（简单）**
```json
{"name":"xdebug","ref":"3.4.0"}
```

**方式 2：版本映射（高级）**

创建 `extensions-versions.json`：
```json
{
  "xdebug": {
    "8.4": "3.4.0",
    "8.3": "3.3.2",
    "8.2": "3.3.2"
  }
}
```

然后使用脚本自动选择版本。

### Q8: 构建速度如何？

**A:** 更快！

- PHP 官方构建器经过优化
- 自动并行构建
- GitHub Actions 提供高性能环境

### Q9: 如何查看构建日志？

**A:** 在 GitHub Actions 中：

1. 进入 **Actions** 标签
2. 点击对应的工作流运行
3. 查看各个步骤的详细日志
4. 展开 "Build PHP" 或 "Build Extension" 步骤

### Q10: 出错怎么办？

**A:** 检查清单：

1. ✅ 确认使用 `build-official.yml` 工作流
2. ✅ 检查 PHP 版本号/tag 是否正确
3. ✅ 验证扩展 JSON 格式
4. ✅ 确认扩展版本与 PHP 版本兼容
5. ✅ 查看 Actions 日志了解详细错误

仍有问题？[提交 Issue](https://github.com/ServBay/PHP-Windows-Portable/issues)

## 推荐配置

### 生产环境

```yaml
版本类型: stable
稳定版版本号: 8.4.14
架构: x64
线程安全: nts
构建扩展: true
扩展配置: [常用扩展]
创建 Release: true
```

### 开发环境

```yaml
版本类型: development
开发版 commit hash: (最新)
开发版版本号: 8.6.0-dev-latest
架构: x64
线程安全: nts
构建扩展: true
扩展配置: [开发调试扩展]
创建 Release: false
```

## 参考资源

- [README.md](README.md) - 完整文档
- [EXTENSIONS_GUIDE.md](EXTENSIONS_GUIDE.md) - 扩展构建指南
- [extensions.example.json](extensions.example.json) - 扩展配置示例
- [README_OLD.md](README_OLD.md) - v1.x 文档（参考）
- [php-windows-builder](https://github.com/php/php-windows-builder) - PHP 官方工具

## 反馈

有问题或建议？欢迎：
- [提交 Issue](https://github.com/ServBay/PHP-Windows-Portable/issues)
- [提交 Pull Request](https://github.com/ServBay/PHP-Windows-Portable/pulls)

---

🚀 欢迎使用 v2.0.0！享受更简单、更强大的 PHP 构建体验！
