# PHP 版本号映射说明

本文档说明 GitHub Actions 工作流中的版本号处理逻辑。

[中文文档](VERSION_MAPPING.md) | [English Documentation](../../VERSION_MAPPING.md)

## 版本号类型

工作流处理三种版本号：

| 版本号 | 用途 | 示例 |
|--------|------|------|
| **php-version** | 用户输入的版本标识，用于包命名 | `8.4.14`, `8.5.0beta2`, `8.6.0-dev-20251105` |
| **php-source** | Git checkout 的引用 | `php-8.4.14`, `php-8.5.0beta2`, `<commit>`, `master` |
| **php-build-version** | 传给官方构建器的版本号 | `8.4.14`, `8.5`, `master` |

## 映射规则

### 稳定版 (stable)

```yaml
用户输入: 8.4.14
├─ php-version: 8.4.14          # 用于包命名
├─ php-source: php-8.4.14       # Git tag (添加 php- 前缀)
└─ php-build-version: 8.4.14    # 构建器版本号
```

**示例：**
```yaml
版本类型: stable
稳定版版本号: 8.4.14
```

**结果：**
- 下载源码：`git checkout php-8.4.14`
- 构建命令：使用 PHP 8.4.14 配置
- 输出包名：`php-8.4.14-stable-nts-Win-x64.zip`

### 测试版 (testing)

```yaml
用户输入: php-8.5.0beta2
├─ php-version: 8.5.0beta2      # 用于包命名 (去除 php- 前缀)
├─ php-source: php-8.5.0beta2   # Git tag (保持原样)
└─ php-build-version: 8.5       # 提取主版本号
```

**示例：**
```yaml
版本类型: testing
测试版标签: php-8.5.0beta2
```

**结果：**
- 下载源码：`git checkout php-8.5.0beta2`
- 构建命令：使用 PHP 8.5 配置
- 输出包名：`php-8.5.0beta2-test-nts-Win-x64.zip`

### 开发版 (development)

#### 指定 Commit

```yaml
用户输入:
  - commit: 1cf63a93801e02d9f75dde59b849dcfa632b9237
  - version: 8.6.0-dev-20251105

结果:
├─ php-version: 8.6.0-dev-20251105    # 用于包命名
├─ php-source: 1cf63a93801e02d9f...    # Git commit hash
└─ php-build-version: master          # 统一使用 master 配置
```

**示例：**
```yaml
版本类型: development
开发版 commit hash: 1cf63a93801e02d9f75dde59b849dcfa632b9237
开发版版本号: 8.6.0-dev-20251105
```

**结果：**
- 下载源码：`git checkout 1cf63a93801e02d9f75dde59b849dcfa632b9237`
- 构建命令：使用 master 配置
- 输出包名：`php-8.6.0-dev-20251105-dev-nts-Win-x64.zip`

#### 不指定 Commit（使用最新代码）

```yaml
用户输入:
  - commit: (留空)
  - version: 8.6.0-dev-latest

结果:
├─ php-version: 8.6.0-dev-latest    # 用于包命名
├─ php-source: master               # Git 分支
└─ php-build-version: master        # 统一使用 master 配置
```

**示例：**
```yaml
版本类型: development
开发版 commit hash: (留空)
开发版版本号: 8.6.0-dev-latest
```

**结果：**
- 下载源码：`git checkout master`
- 构建命令：使用 master 配置
- 输出包名：`php-8.6.0-dev-latest-dev-nts-Win-x64.zip`

## 为什么需要 php-build-version？

### 问题

PHP 官方构建器 (php-windows-builder) 需要识别 PHP 版本来确定使用哪个 Visual Studio 版本：

```
PHP 7.0-7.1  → VS 2015 (vc14)
PHP 7.2-8.3  → VS 2017/2019 (vs16)
PHP 8.4+     → VS 2022 (vs17)
```

但是：
- 官方构建器不认识 `8.6.0-dev-20251105` 这样的自定义版本号
- 官方构建器只支持配置文件中定义的版本号
- `master` 是特殊值，总是使用最新的 VS 配置

### 解决方案

引入 `php-build-version`：
- **稳定版**: 使用完整版本号（如 `8.4.14`）
- **测试版**: 提取主版本号（如 `8.5`）
- **开发版**: 统一使用 `master`

这样既保留了用户自定义的版本标识（用于包命名），又能让官方构建器正确识别版本。

## 版本号提取逻辑

### Bash 脚本实现

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
    # 提取主版本号: 8.5.0beta2 -> 8.5
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
    # 开发版统一使用 master
    PHP_BUILD_VERSION="master"
    ;;
esac
```

## 使用建议

### 生产环境

```yaml
版本类型: stable
稳定版版本号: 8.4.14  ← 使用最新稳定版
```

### 测试预发布功能

```yaml
版本类型: testing
测试版标签: php-8.5.0RC4  ← 使用 RC 版本
```

### 测试最新开发代码

```yaml
版本类型: development
开发版 commit hash: (留空)  ← 使用 master 最新代码
开发版版本号: 8.6.0-dev-latest
```

### 构建特定历史版本

```yaml
版本类型: development
开发版 commit hash: 1cf63a93801e02d9f75dde59b849dcfa632b9237
开发版版本号: 8.6.0-dev-20251105
```

## 调试技巧

### 查看版本映射结果

在 GitHub Actions 日志的 "Determine PHP Version and Source" 步骤中，会输出：

```
PHP Version: 8.6.0-dev-20251105
PHP Source: 1cf63a93801e02d9f75dde59b849dcfa632b9237
PHP Build Version: master
Version Type: development
```

检查这些值是否符合预期。

### 常见错误

#### 错误 1：构建器版本不支持

```
Error: The property '8.6' cannot be found on this object.
```

**原因：** 官方构建器不认识 `8.6` 版本号。

**解决：** 已修复，开发版统一使用 `master`。

#### 错误 2：Git checkout 失败

```
Error: The process 'git.exe' failed with exit code 1
```

**原因：** Git 引用不存在。

**检查：**
1. 稳定版是否添加了 `php-` 前缀？
2. 测试版 tag 是否存在？
3. 开发版 commit hash 是否正确？

## 相关文件

- `.github/workflows/build.yml` - 工作流定义
- `README.md` - 使用指南
- `EXTENSIONS_GUIDE.md` - 扩展构建指南

---

如有疑问，请参考 [README.md](../../README.md) 或提交 [Issue](https://github.com/ServBay/PHP-Windows-Portable/issues)。
