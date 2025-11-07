# 贡献指南

[中文文档](CONTRIBUTING.md) | [English Documentation](../../CONTRIBUTING.md)

感谢您对 PHP-Windows-Portable 项目的关注！

## 如何贡献

### 报告问题

如果您发现了 bug 或有功能建议，请：

1. 检查 [Issues](../../issues) 页面，确保问题尚未被报告
2. 创建新的 Issue，包含：
   - 清晰的标题和描述
   - 重现问题的步骤
   - 预期行为和实际行为
   - 您的环境信息（Windows 版本、Visual Studio 版本、PHP 版本等）

### 提交代码

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

### 代码规范

- 批处理脚本应该：
  - 使用有意义的变量名
  - 包含适当的错误处理
  - 添加注释说明复杂逻辑
  - 保持与现有代码风格一致

- 文档应该：
  - 主文档使用英文（在 docs/zh-CN/ 中提供中文翻译）
  - 包含示例代码
  - 保持更新

- GitHub Actions 工作流应该：
  - 遵循官方构建器模式
  - 包含适当的错误处理
  - 具有清晰的步骤描述
  - 适当使用环境变量

### 测试

在提交 PR 之前，请确保：

1. 您的代码能够成功编译 PHP
2. 没有破坏现有功能
3. 添加了必要的文档
4. 扩展配置已测试（如适用）

## 开发环境设置

1. 克隆仓库
2. 运行 `setup.bat` 配置环境（用于本地构建）
3. 准备依赖库（或使用 GitHub Actions）
4. 测试编译流程

## 版本管理

- 主分支 (`main`) 包含稳定版本
- 开发分支 (`develop`) 用于日常开发
- 功能分支 (`feature/*`) 用于新功能开发
- 修复分支 (`fix/*`) 用于 bug 修复

## 提交信息规范

使用清晰的提交信息：

```
<类型>: <简短描述>

<详细描述>

<相关 Issue>
```

类型包括：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

示例：
```
feat: 添加 PHP 8.4 支持

- 更新依赖库版本
- 添加新的配置选项
- 更新文档

Closes #123
```

## 扩展贡献

贡献扩展配置时：

1. 验证扩展可在多个 PHP 版本上成功构建
2. 包含正确的版本兼容性信息
3. 在 `libs` 字段中指定所有必需的依赖库
4. 使用 Thread-Safe 和 Non-Thread-Safe 构建进行测试
5. 如需要，将文档添加到 EXTENSIONS_GUIDE.md

扩展配置示例：
```json
{
  "name": "extension_name",
  "url": "https://github.com/org/extension",
  "ref": "1.0.0",
  "args": "--enable-extension",
  "libs": "openssl zlib"
}
```

## 文档指南

- 主文档使用英文
- 在 docs/zh-CN/ 中提供中文翻译
- 在顶部包含多语言导航链接
- 保持交叉引用最新
- 使用清晰的示例和代码片段

## 联系方式

如有疑问，请通过以下方式联系：

- 创建 Issue
- 参与讨论

再次感谢您的贡献！
