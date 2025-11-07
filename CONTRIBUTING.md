# Contributing Guide

[中文文档](docs/zh-CN/CONTRIBUTING.md) | [Documentation](CONTRIBUTING.md)

Thank you for your interest in the PHP-Windows-Portable project!

## How to Contribute

### Reporting Issues

If you find a bug or have a feature suggestion, please:

1. Check the [Issues](../../issues) page to ensure the issue hasn't already been reported
2. Create a new Issue including:
   - Clear title and description
   - Steps to reproduce the issue
   - Expected behavior and actual behavior
   - Your environment information (Windows version, Visual Studio version, PHP version, etc.)

### Submitting Code

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Code Standards

- Batch scripts should:
  - Use meaningful variable names
  - Include appropriate error handling
  - Add comments explaining complex logic
  - Maintain consistency with existing code style

- Documentation should:
  - Use clear English (or Chinese in docs/zh-CN/)
  - Include example code
  - Stay up-to-date

- GitHub Actions workflows should:
  - Follow official builder patterns
  - Include proper error handling
  - Have clear step descriptions
  - Use environment variables appropriately

### Testing

Before submitting a PR, please ensure:

1. Your code successfully compiles PHP
2. No existing functionality is broken
3. Necessary documentation is added
4. Extension configurations are tested (if applicable)

## Development Environment Setup

1. Clone the repository
2. Run `setup.bat` to configure environment (for local builds)
3. Prepare dependencies (or use GitHub Actions)
4. Test the build process

## Version Management

- Main branch (`main`) contains stable versions
- Development branch (`develop`) for daily development
- Feature branches (`feature/*`) for new feature development
- Fix branches (`fix/*`) for bug fixes

## Commit Message Guidelines

Use clear commit messages:

```
<type>: <short description>

<detailed description>

<related issue>
```

Types include:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation update
- `style`: Code formatting (no functionality impact)
- `refactor`: Refactoring
- `test`: Test-related
- `chore`: Build process or auxiliary tool changes

Example:
```
feat: Add PHP 8.4 support

- Update dependency versions
- Add new configuration options
- Update documentation

Closes #123
```

## Extension Contributions

When contributing extension configurations:

1. Verify the extension builds successfully with multiple PHP versions
2. Include proper version compatibility information
3. Specify all required dependency libraries in `libs` field
4. Test with both Thread-Safe and Non-Thread-Safe builds
5. Add documentation to EXTENSIONS_GUIDE.md if needed

Example extension configuration:
```json
{
  "name": "extension_name",
  "url": "https://github.com/org/extension",
  "ref": "1.0.0",
  "args": "--enable-extension",
  "libs": "openssl zlib"
}
```

## Documentation Guidelines

- Use English for main documentation
- Provide Chinese translations in docs/zh-CN/
- Include multilingual navigation links at the top
- Keep cross-references up-to-date
- Use clear examples and code snippets

## Contact

If you have questions, please:

- Create an Issue
- Participate in Discussions

Thank you for your contribution!
