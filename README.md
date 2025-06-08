# GitHub Manager MCP Server

An open-source Model Context Protocol (MCP) server that provides seamless GitHub project management capabilities for AI assistants and applications.

## 🚀 Overview

The GitHub Manager MCP Server enables AI assistants to interact with GitHub repositories, issues, pull requests, and project management features through a standardized protocol. This server bridges the gap between AI applications and GitHub's powerful project management ecosystem.

## ✨ Features

- **Repository Management**: Create, clone, and manage GitHub repositories
- **Issue Tracking**: Create, update, close, and search issues
- **Pull Request Management**: Create, review, merge, and manage pull requests
- **Project Boards**: Interact with GitHub Projects (v2) for advanced project management
- **Team Collaboration**: Manage assignees, reviewers, and team permissions
- **Webhook Integration**: Real-time notifications and event handling
- **Search & Analytics**: Advanced repository and code search capabilities
- **Branch Management**: Create, merge, and delete branches
- **Release Management**: Create and manage releases and tags

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- GitHub Personal Access Token with appropriate permissions
- Git installed on your system

### Quick Start

1. **Clone the repository**
   ```bash
   git clone git@github.com:thepeacefulprogrammer/github_manager_mcp.git
   cd github_manager_mcp
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your GitHub token
   ```

4. **Run the server**
   ```bash
   python -m github_manager_mcp
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_API_URL=https://api.github.com
MCP_SERVER_PORT=3000
LOG_LEVEL=INFO
```

### GitHub Token Permissions

Your GitHub Personal Access Token should have the following scopes:
- `repo` - Full repository access
- `project` - Project management access
- `admin:org` - Organization administration (if managing organization repos)
- `user` - User profile access

## 📋 Usage

### MCP Client Integration

```python
from mcp import Client

# Connect to the GitHub Manager MCP Server
client = Client("http://localhost:3000")

# Example: Create a new issue
response = client.call("create_issue", {
    "repository": "owner/repo-name",
    "title": "Bug: Application crashes on startup",
    "body": "Detailed description of the issue...",
    "labels": ["bug", "high-priority"],
    "assignees": ["username"]
})
```

### Available MCP Tools

#### Repository Management
- `create_repository` - Create a new repository
- `get_repository` - Get repository information
- `list_repositories` - List user/organization repositories
- `fork_repository` - Fork a repository

#### Issue Management
- `create_issue` - Create a new issue
- `update_issue` - Update existing issue
- `close_issue` - Close an issue
- `list_issues` - List repository issues
- `search_issues` - Search issues across repositories

#### Pull Request Management
- `create_pull_request` - Create a new pull request
- `update_pull_request` - Update existing pull request
- `merge_pull_request` - Merge a pull request
- `list_pull_requests` - List repository pull requests

#### Project Management
- `create_project` - Create a new project board
- `update_project` - Update project settings
- `add_item_to_project` - Add issues/PRs to project
- `move_project_item` - Move items between columns

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │────│  GitHub Manager │────│   GitHub API    │
│   (AI Agent)    │    │    MCP Server   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   Local Storage │
                       │   (Cache/Logs)  │
                       └─────────────────┘
```

## 🧪 Development

### Setting up Development Environment

1. **Fork and clone the repository**
   ```bash
   git fork git@github.com:thepeacefulprogrammer/github_manager_mcp.git
   cd github_manager_mcp
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Run tests**
   ```bash
   pytest tests/
   ```

5. **Code formatting**
   ```bash
   black .
   isort .
   flake8 .
   ```

### Project Structure

```
github_manager_mcp/
├── src/
│   ├── github_manager_mcp/
│   │   ├── __init__.py
│   │   ├── server.py          # Main MCP server implementation
│   │   ├── github_client.py   # GitHub API client wrapper
│   │   ├── handlers/          # MCP tool handlers
│   │   └── utils/             # Utility functions
├── tests/                     # Test suite
├── docs/                      # Documentation
├── examples/                  # Usage examples
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
└── README.md
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to your branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Standards

- Follow PEP 8 style guidelines
- Write comprehensive tests for all new features
- Include docstrings for all public methods
- Update documentation for any API changes

## 📚 Documentation

- [API Reference](docs/api-reference.md)
- [Configuration Guide](docs/configuration.md)
- [Examples](examples/)
- [Troubleshooting](docs/troubleshooting.md)

## 🔒 Security

- Never commit GitHub tokens or sensitive information
- Use environment variables for all configuration
- Follow GitHub's API rate limiting guidelines
- Report security vulnerabilities privately to maintainers

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Model Context Protocol](https://github.com/modelcontextprotocol) for the MCP specification
- [GitHub REST API](https://docs.github.com/en/rest) for comprehensive project management capabilities
- The open-source community for inspiration and contributions

## 📞 Support

- 🐛 [Report Bug](https://github.com/thepeacefulprogrammer/github_manager_mcp/issues)
- 💡 [Request Feature](https://github.com/thepeacefulprogrammer/github_manager_mcp/issues)
- 💬 [Discussions](https://github.com/thepeacefulprogrammer/github_manager_mcp/discussions)
- 📧 Email: [your-email@example.com]

---

<div align="center">
  
**⭐ If this project helps you, please give it a star! ⭐**

Made with ❤️ by [The Peaceful Programmer](https://github.com/thepeacefulprogrammer)

</div> 