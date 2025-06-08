# GitHub Project Manager MCP Server

An open-source Model Context Protocol (MCP) server that provides automated GitHub project management capabilities for AI assistants and applications, specifically designed to integrate with PRD-driven development workflows.

## 🚀 Overview

The GitHub Project Manager MCP Server enables AI assistants to automate GitHub Projects v2 management through a structured workflow hierarchy (Project → PRDs → Tasks → Subtasks). This server bridges the gap between AI-driven development workflows and GitHub's project management ecosystem, allowing AI agents like Claude/Cursor to automatically update project status as work progresses.

## ✨ Features

- **Automated Project Management**: AI agents can create and manage GitHub Projects v2 boards automatically
- **PRD-Driven Workflow**: Supports hierarchical project structure with PRDs as top-level planning documents
- **Task & Subtask Management**: Create, update, and track tasks and subtasks within PRDs
- **Status Column Management**: Support for workflow status columns (Backlog, This Sprint, Up Next, In Progress, Done)
- **Seamless AI Integration**: Designed specifically for AI agent automation of project management tasks
- **Real-time Updates**: Automatically update GitHub Projects as development work progresses
- **Progress Tracking**: Query project health and progress through AI agents

## 🎯 Use Case

This MCP server is designed for developers who:
- Use PRD-driven development workflows
- Want AI agents to automatically manage their GitHub project status
- Follow structured task breakdown methodologies (PRD → Tasks → Subtasks)
- Prefer automation over manual project management
- Work with AI assistants like Claude Desktop or Cursor

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- GitHub Personal Access Token with appropriate permissions
- Access to GitHub Projects v2

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
   python -m github_project_manager_mcp
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
- `project` - Project management access
- `repo` - Repository access (for Projects v2)
- `user` - User profile access

## 📋 Usage

### MCP Client Integration

```python
from mcp import Client

# Connect to the GitHub Project Manager MCP Server
client = Client("http://localhost:3000")

# Example: Create a new project
response = client.call("create_project", {
    "name": "Q1 2024 Features",
    "description": "Major feature development for Q1",
    "repository": "owner/repo-name"
})

# Example: Add a PRD to the project
response = client.call("add_prd_to_project", {
    "project_id": "project_123",
    "prd_title": "User Authentication System",
    "prd_description": "Implement secure user authentication",
    "status": "This Sprint"
})
```

### Available MCP Tools

#### Project Management
- `create_project` - Create a new GitHub Project v2 board
- `list_projects` - List all available projects
- `get_project_details` - Get detailed project information
- `archive_project` - Archive a completed project

#### PRD Management
- `add_prd_to_project` - Add a new PRD to a project
- `list_prds` - List PRDs within a project
- `update_prd_status` - Update PRD status and details
- `move_prd_to_column` - Move PRD between status columns

#### Task Management
- `create_task` - Create a new task under a PRD
- `list_tasks` - List tasks within a PRD or project
- `update_task` - Update task details and status
- `move_task_to_column` - Move task between status columns

#### Subtask Management
- `add_subtask` - Add subtask to a task
- `list_subtasks` - List subtasks within a task
- `complete_subtask` - Mark subtask as complete
- `get_task_progress` - Get completion status of task and subtasks

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI Agent      │────│  GitHub Project │────│   GitHub API    │
│ (Claude/Cursor) │    │   Manager MCP   │    │   Projects v2   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   PRD Workflow  │
                       │   Integration   │
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
│   ├── github_project_manager_mcp/
│   │   ├── __init__.py
│   │   ├── server.py          # Main MCP server implementation
│   │   ├── github_client.py   # GitHub GraphQL API client
│   │   ├── handlers/          # MCP tool handlers
│   │   │   ├── project_handlers.py
│   │   │   ├── prd_handlers.py
│   │   │   ├── task_handlers.py
│   │   │   └── subtask_handlers.py
│   │   ├── models/            # Data models
│   │   └── utils/             # Utility functions
├── tasks/                     # PRD and task files
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

## 📚 Roadmap

- [x] Create comprehensive PRD for GitHub Project Manager
- [ ] Generate detailed task breakdown from PRD
- [ ] Implement core MCP server infrastructure
- [ ] Develop GitHub GraphQL API integration
- [ ] Create project management handlers
- [ ] Implement PRD management capabilities
- [ ] Add task and subtask management
- [ ] Integrate with AI workflow automation
- [ ] Add comprehensive testing suite
- [ ] Create documentation and examples

## 🎯 Vision

Our goal is to create the most seamless integration between AI-driven development workflows and GitHub project management, enabling developers to focus on building great software while AI agents handle the administrative overhead of project tracking and status updates.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 💬 Community

* GitHub Discussions

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
