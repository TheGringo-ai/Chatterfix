# Contributing to ChatterFix

Thank you for your interest in contributing to ChatterFix! This document provides guidelines for contributing to the project.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Community](#community)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive experience for everyone. We expect all contributors to:

- Be respectful and considerate
- Welcome newcomers and help them learn
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards others

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Personal attacks or trolling
- Publishing others' private information
- Disruptive or unprofessional conduct

Report violations to: conduct@chatterfix.com

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ (for mobile app)
- Git
- Google Cloud account (for Firebase/Firestore)

### Quick Setup

```bash
# Fork the repository on GitHub

# Clone your fork
git clone https://github.com/YOUR-USERNAME/Chatterfix.git
cd Chatterfix

# Add upstream remote
git remote add upstream https://github.com/TheGringo-ai/Chatterfix.git

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Run the application
python3 main.py
```

---

## How to Contribute

### Reporting Bugs

Before creating a bug report:
1. Check the [issue tracker](https://github.com/TheGringo-ai/Chatterfix/issues) for existing reports
2. Ensure you're on the latest version
3. Collect information about the bug

**Create a bug report with:**
- Clear, descriptive title
- Steps to reproduce
- Expected vs actual behavior
- Screenshots if applicable
- Environment details (OS, browser, Python version)

### Suggesting Features

We welcome feature suggestions! Please:
1. Check if the feature already exists or is planned
2. Clearly describe the feature and its benefits
3. Consider how it fits ChatterFix's "technician-first" philosophy
4. Be open to feedback and discussion

### Contributing Code

1. **Find an issue** to work on, or create one for discussion
2. **Comment on the issue** to express your intent
3. **Fork and create a branch** for your work
4. **Write your code** following our standards
5. **Write tests** for your changes
6. **Submit a pull request**

---

## Development Setup

### Environment Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific tests
pytest tests/test_imports.py -v
```

### Code Quality

```bash
# Format code
black app/

# Sort imports
isort app/ --profile=black

# Lint code
flake8 app/

# Type checking
mypy app/ --ignore-missing-imports

# Security scan
bandit -r app/
```

### Running Locally

```bash
# Start the server
python3 main.py

# Or with hot reload
uvicorn main:app --reload --port 8000
```

---

## Coding Standards

### Python Style

- **Formatter:** Black (88 character line length)
- **Imports:** isort with Black profile
- **Linting:** Flake8, Pylint
- **Type Hints:** Encouraged for all functions
- **Docstrings:** Required for public functions

```python
# Good example
async def create_work_order(
    title: str,
    description: str,
    priority: str = "Medium",
) -> dict:
    """
    Create a new work order in the system.

    Args:
        title: The work order title
        description: Detailed description of the issue
        priority: Priority level (Low, Medium, High, Critical)

    Returns:
        dict: The created work order with ID
    """
    # Implementation
    pass
```

### Commit Messages

Follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(ai): add voice command for inventory lookup
fix(auth): resolve session cookie not being set
docs(readme): update installation instructions
```

### Branch Naming

```
feature/short-description
fix/issue-number-description
docs/what-you-updated
```

---

## Pull Request Process

### Before Submitting

1. **Sync with upstream:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks:**
   ```bash
   pre-commit run --all-files
   pytest
   ```

3. **Update documentation** if needed

### PR Template

Your PR should include:

```markdown
## Summary
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How did you test these changes?

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-reviewed my code
- [ ] Added comments for complex logic
- [ ] Updated documentation
- [ ] Added tests for new features
- [ ] All tests pass
- [ ] No new warnings
```

### Review Process

1. **Automated checks** run on all PRs
2. **Code review** by maintainers
3. **Address feedback** promptly
4. **Merge** after approval

### After Merge

- Delete your branch
- Update your fork
- Celebrate your contribution! 🎉

---

## What We're Looking For

### High Priority

- Bug fixes
- Performance improvements
- Accessibility improvements
- Documentation improvements
- Test coverage

### Feature Areas

- Voice command enhancements
- Mobile app improvements
- AI assistant capabilities
- Integration with external systems
- Offline functionality

### Good First Issues

Look for issues labeled `good first issue` - these are great for newcomers!

---

## Community

### Getting Help

- **GitHub Discussions:** Ask questions and share ideas
- **GitHub Issues:** Report bugs and request features
- **Email:** support@chatterfix.com

### Recognition

Contributors are recognized in:
- Our contributors list
- Release notes
- Project documentation

---

## License

By contributing, you agree that your contributions will be licensed under the same [dual license](LICENSE) as the project.

---

## Thank You!

Your contributions help make ChatterFix better for maintenance technicians everywhere. We appreciate your time and effort!

---

*© 2024 Fred Taylor. All Rights Reserved.*
