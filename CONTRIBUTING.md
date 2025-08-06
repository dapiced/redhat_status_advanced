# Contributing to Red Hat Status Checker

Thank you for your interest in contributing to the Red Hat Status Checker! This document provides guidelines for contributing to this project.

## 📋 Code of Conduct

By participating in this project, you agree to abide by our code of conduct:
- Be respectful and inclusive
- Focus on constructive feedback
- Help maintain a welcoming environment for all contributors

## 🚀 Getting Started

### Prerequisites
- Python 3.6+
- Git
- Docker/Podman (optional, for container testing)

### Development Setup
1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/redhat_status_enhanced.git`
3. Create a virtual environment: `python3 -m venv .venv`
4. Activate virtual environment: `source .venv/bin/activate`
5. Install dependencies: `pip install -r requirements.txt`
6. Run tests: `python3 run_tests.py --all`

## 🔧 Development Guidelines

### Code Style
- Follow PEP 8 Python style guidelines
- Use type hints where appropriate
- Include docstrings for all public functions and classes
- Keep functions focused and modular

### Testing
- Write unit tests for new features
- Ensure all tests pass before submitting PR
- Include integration tests for API changes
- Test coverage should not decrease

### Commit Messages
- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, etc.)
- Reference issue numbers when applicable

## 📝 Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes with appropriate tests
3. Ensure all tests pass: `./run_tests_venv.sh --all`
4. Update documentation if needed
5. Submit a pull request with:
   - Clear description of changes
   - Reference to related issues
   - Screenshots/examples if UI changes

## 🧪 Testing

Run the comprehensive test suite:
```bash
# Run all tests
./run_tests_venv.sh --all

# Run specific test categories
python3 run_tests.py --flags        # CLI flag tests
python3 run_tests.py --examples     # Example command tests
./run_tests_venv.sh --containers    # Container tests
```

## 📁 Project Structure

```
redhat_status/
├── analytics/      # AI and analytics modules
├── config/         # Configuration management
├── core/           # Core functionality
├── database/       # Data persistence
├── notifications/  # Alert and notification systems
└── utils/          # Utility functions

tests/              # Comprehensive test suite
```

## 🐛 Bug Reports

When filing bug reports, please include:
- Python version and OS
- Steps to reproduce
- Expected vs actual behavior
- Error messages or logs
- Configuration details (sanitized)

## 💡 Feature Requests

For feature requests:
- Check existing issues first
- Provide clear use case description
- Consider implementation complexity
- Discuss breaking changes

## 📚 Documentation

- Update README.md for user-facing changes
- Add docstrings for new functions/classes
- Update CHANGELOG.md for version releases
- Include usage examples

## 🏷️ Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release tag
4. Update documentation

## 🤝 Questions?

- Open an issue for questions
- Check existing documentation
- Review closed issues for similar questions

Thank you for contributing to making Red Hat Status Checker better! 🎉
