## Relevant Files

- `src/github_project_manager_mcp/__init__.py` - Main package initialization and version info

- `src/github_project_manager_mcp/mcp_server_fastmcp.py` - FastMCP-based server implementation for proper Cursor IDE integration with comprehensive debugging, async patterns, and complete project management tools (test_connection, create_project, list_projects, delete_project, get_project_details)

- `src/github_project_manager_mcp/github_client.py` - GitHub GraphQL API client with async support and error handling
- `tests/unit/test_github_client.py` - Unit tests for GitHub API client with TDD approach
- `src/github_project_manager_mcp/handlers/project_handlers.py` - MCP tool handlers for project management operations including create_project, list_projects, delete_project, and get_project_details with repository validation, pagination support, GitHub API integration, safe deletion with confirmation, and detailed project information retrieval
- `tests/unit/handlers/test_project_handlers.py` - Unit tests for project handlers with comprehensive TDD test coverage for create_project, list_projects, delete_project, and get_project_details functionality
- `src/github_project_manager_mcp/handlers/prd_handlers.py` - MCP tool handlers for PRD management operations including add_prd_to_project with comprehensive PRD creation, structured descriptions, status/priority validation, and GitHub Projects v2 draft issue integration
- `tests/unit/handlers/test_prd_handlers.py` - Unit tests for PRD handlers with comprehensive TDD test coverage for add_prd_to_project functionality including validation, error handling, and API integration
- `src/github_project_manager_mcp/handlers/prd_handlers.test.py` - Unit tests for PRD handlers
- `src/github_project_manager_mcp/handlers/task_handlers.py` - MCP tool handlers for task management operations
- `src/github_project_manager_mcp/handlers/task_handlers.test.py` - Unit tests for task handlers
- `src/github_project_manager_mcp/handlers/subtask_handlers.py` - MCP tool handlers for subtask management operations
- `src/github_project_manager_mcp/handlers/subtask_handlers.test.py` - Unit tests for subtask handlers
- `src/github_project_manager_mcp/models/project.py` - Data models for project entities including Project, ProjectField, and related classes for GitHub Projects v2 API
- `tests/unit/test_project_model.py` - Unit tests for Project data models with comprehensive TDD test coverage
- `src/github_project_manager_mcp/models/prd.py` - Data models for PRD entities including PRD, PRDStatus, and PRDPriority classes for GitHub Projects v2 integration with comprehensive field mapping and validation
- `tests/unit/test_prd_model.py` - Unit tests for PRD data models with comprehensive TDD test coverage for all PRD functionality including validation, serialization, and GitHub item mapping
- `src/github_project_manager_mcp/models/task.py` - Data models for task entities
- `src/github_project_manager_mcp/models/subtask.py` - Data models for subtask entities
- `src/github_project_manager_mcp/models/__init__.py` - Models package initialization with Project model exports
- `src/github_project_manager_mcp/handlers/__init__.py` - Handlers package initialization with project handler exports
- `src/github_project_manager_mcp/utils/auth.py` - GitHub authentication utilities with token validation and management
- `tests/unit/test_auth.py` - Unit tests for authentication utilities with TDD approach
- `src/github_project_manager_mcp/utils/query_builder.py` - GraphQL query builder for Projects v2 API with pagination, field selection, and delete project mutations
- `tests/unit/test_query_builder.py` - Unit tests for GraphQL query builder with TDD approach
- `src/github_project_manager_mcp/utils/error_handling.py` - Error handling and retry logic with exponential backoff and circuit breaker patterns
- `tests/unit/test_error_handling.py` - Unit tests for error handling utilities with TDD approach
- `src/github_project_manager_mcp/utils/validation.py` - Input validation utilities
- `src/github_project_manager_mcp/utils/logging.py` - Logging configuration and utilities
- `src/github_project_manager_mcp/utils/__init__.py` - Utils package initialization
- `src/github_project_manager_mcp/utils/utils.test.py` - Unit tests for utility functions
- `requirements.txt` - Production dependencies
- `requirements-dev.txt` - Development dependencies including testing frameworks
- `setup.py` - Package setup and installation configuration
- `.env.example` - Environment configuration template
- `pyproject.toml` - Modern Python project configuration
- `.github/workflows/ci.yml` - GitHub Actions CI/CD pipeline for automated testing and code quality
- `.github/workflows/dependabot.yml` - Automated dependency update workflow
- `.github/dependabot.yml` - Dependabot configuration for dependency management
- `.pre-commit-config.yaml` - Pre-commit hooks configuration for code quality enforcement
- `docs/MCP_TROUBLESHOOTING.md` - Comprehensive troubleshooting guide for MCP server setup and common issues

### Notes

- Unit tests should be placed alongside the code files they are testing using pytest framework
- Use `pytest` to run tests. Running without arguments executes all tests found by pytest discovery
- GitHub GraphQL API will be used for efficient data operations
- **FastMCP** will be used instead of basic MCP for proper protocol compliance and Cursor integration
- Environment variables will handle GitHub authentication tokens securely
- **CRITICAL**: Logging must use stderr only, never stdout (breaks MCP JSON-RPC protocol)
- Virtual environment setup is essential for proper Cursor MCP integration

### Current Priority

🎉 **MCP SERVER IS FULLY OPERATIONAL WITH GITHUB API!** 🎉

**MAJOR MILESTONE ACHIEVED**: We now have a complete working MCP server with:
- ✅ `test_connection` - Verified working
- ✅ `list_projects` - **WORKING WITH REAL GITHUB DATA** (found 3 projects for thepeacefulprogrammer)
- ✅ `create_project` - **SUCCESSFULLY CREATED REAL GITHUB PROJECT** (MCP Test Project: PVT_kwHOAGo2TM4A7C1T)
- ✅ `update_project` - **COMPLETE PROJECT METADATA MANAGEMENT** (title, description, visibility, README updates with comprehensive validation)
- ✅ `delete_project` - **IMPLEMENTED WITH SAFETY CHECKS** (requires explicit confirmation, prevents accidental deletions)
- ✅ `get_project_details` - **COMPREHENSIVE PROJECT INFORMATION RETRIEVAL** (detailed project metadata, descriptions, and status)
- ✅ `add_prd_to_project` - **FULLY FUNCTIONAL WITH COMPREHENSIVE PRD CREATION** (creates draft issues with structured descriptions, acceptance criteria, technical requirements, business value)
- ✅ `delete_prd_from_project` - **FULLY FUNCTIONAL PRD CLEANUP TOOL** (safely deletes PRDs from projects with confirmation, proper GraphQL API integration)
- ✅ GitHub Authentication - Working with .env token
- ✅ GraphQL API - Successfully calling GitHub Projects v2 API

**CURRENT FOCUS**: **PROJECT-LEVEL CRUD OPERATIONS COMPLETED!** 
- ✅ Project Create, Read, Update, Delete - **ALL COMPLETED**
- 🎯 **NEXT PRIORITY**: PRD-level CRUD completion (list_prds, update_prd)

**DEVELOPMENT STRATEGY**: **HIERARCHICAL CRUD COMPLETION**
Following a systematic approach to ensure solid foundations:
1. ✅ **Complete Project Level CRUD** (100% - ALL OPERATIONS COMPLETED!)
2. 📋 **Complete PRD Level CRUD** (50% - list_prds, update_prd remaining) 
3. 📝 **Complete Task Level CRUD** (0% - all operations needed)
4. ✅ **Complete Subtask Level CRUD** (0% - all operations needed)
5. 🔄 **Implement Status Management & Workflow Automation**

**NEXT TASK**: Implement `list_prds` to continue PRD-level CRUD completion, followed by `update_prd`.

## Tasks

- [x] 1.0 Set up Core MCP Server Infrastructure
  - [x] 1.1 Create project directory structure with src/github_project_manager_mcp layout
  - [x] 1.2 Set up pyproject.toml with project metadata, dependencies, and build configuration
  - [x] 1.3 Create requirements.txt with core dependencies (mcp, httpx, python-dotenv)
  - [x] 1.4 Create requirements-dev.txt with development dependencies (pytest, black, isort, flake8)
  - [x] 1.5 Create .env.example template with GITHUB_TOKEN and other configuration variables
  - [x] 1.6 Initialize main package with __init__.py and version information
  - [x] 1.7 Set up pytest configuration and test directory structure
  - [x] 1.8 Create basic logging configuration module
  - [x] 1.9 Set up CI/CD workflow files for automated testing

- [x] 1.5 Implement FastMCP Server Integration (COMPLETED)
  - [x] 1.5.1 Update requirements.txt to include fastmcp>=0.1.0 and remove conflicting mcp dependencies
  - [x] 1.5.2 Create FastMCP-based server implementation at src/github_project_manager_mcp/mcp_server_fastmcp.py
  - [x] 1.5.3 Implement proper logging setup with stderr-only output (critical for MCP protocol)
  - [x] 1.5.4 Add comprehensive startup debugging and environment tracking
  - [x] 1.5.5 Create basic test_connection tool to verify MCP server functionality
  - [x] 1.5.6 Register all GitHub project management tools with FastMCP
  - [x] 1.5.7 Add async initialization patterns for GitHub client and heavy components
  - [x] 1.5.8 Create logs directory and file-based logging system
  - [x] 1.5.9 Test FastMCP server locally before Cursor integration

- [x] 1.6 Configure Cursor MCP Integration (COMPLETED)
  - [x] 1.6.1 Create virtual environment setup script for project isolation
  - [x] 1.6.2 Update ~/.cursor/mcp.json with github-project-manager-mcp server configuration
  - [x] 1.6.3 Configure proper command path using project's virtual environment Python
  - [x] 1.6.4 Set PYTHONPATH environment variable for proper module imports
  - [x] 1.6.5 Add working directory and environment variable configuration
  - [x] 1.6.6 Test MCP server recognition in Cursor IDE
  - [x] 1.6.7 Verify all tools show up correctly in Cursor's MCP tool list
  - [x] 1.6.8 Create troubleshooting documentation for common MCP setup issues

- [x] 2.0 Implement GitHub GraphQL API Integration (COMPLETED)
  - [x] 2.1 Create GitHub client class with GraphQL endpoint configuration
  - [x] 2.2 Implement authentication handling using Personal Access Tokens
  - [x] 2.3 Create GraphQL query builder utilities for Projects v2 API
  - [x] 2.4 Implement error handling and retry logic for API calls
  - [x] 2.5 Add rate limiting compliance and request throttling
  - [x] 2.6 Create GraphQL mutations for project creation and updates
  - [x] 2.7 Implement pagination handling for large result sets
  - [x] 2.8 Add comprehensive unit tests for GitHub client functionality
  - [x] 2.9 Create integration tests with GitHub API (using test tokens)

- [ ] 3.0 Build Project Management Functionality (AFTER FastMCP Integration)
  - [x] 3.1 Create Project data model with fields for GitHub Projects v2 structure
  - [x] 3.2 Implement create_project MCP tool handler with name, description, and repository parameters
  - [x] 3.3 Implement list_projects MCP tool handler with filtering and pagination
  - [x] 3.4 Migrate existing MCP server implementation to use FastMCP architecture
  - [x] 3.5 Implement get_project_details MCP tool handler for retrieving project information
  - [x] 3.6 Implement delete_project MCP tool handler for removing test projects and cleanup
  - [x] 3.7 **COMPLETED**: Implement update_project MCP tool handler for project metadata management
    - [x] 3.7.1 Research GitHub Projects v2 updateProjectV2 GraphQL mutation capabilities
    - [x] 3.7.2 Create update_project_handler with parameter validation for name, description, visibility
    - [x] 3.7.3 Build GraphQL mutation for updateProjectV2 with proper field mapping
    - [x] 3.7.4 Add comprehensive error handling and validation logic
    - [x] 3.7.5 Register update_project tool in FastMCP server with proper parameter schema
    - [ ] 3.7.6 Test update_project with real GitHub API calls and various update scenarios
    - [x] 3.7.7 Add unit tests for update_project functionality with TDD approach
  - [ ] 3.8 Create status column configuration and management for projects
  - [ ] 3.9 Add project validation logic for required fields and constraints
  - [ ] 3.10 Implement project search and filtering capabilities
  - [ ] 3.11 Create comprehensive unit tests for all project management operations
  - [ ] 3.12 Add integration tests for project CRUD operations with GitHub API

- [ ] 4.0 Implement PRD and Task Management
  - [x] 4.1 Create PRD data model with custom fields for GitHub Projects v2 items
  - [x] 4.2 Implement add_prd_to_project MCP tool handler with title, description, and status - **FULLY WORKING AND TESTED**
  - [x] 4.2.1 Implement delete_prd_from_project MCP tool handler for cleanup operations - **FULLY WORKING AND TESTED**
  - [ ] 4.3 Implement list_prds MCP tool handler with project filtering
  - [ ] 4.4 Implement update_prd_status MCP tool handler for status and detail updates
  - [ ] 4.5 Create Task data model with relationship to parent PRD
  - [ ] 4.6 Implement create_task MCP tool handler with PRD association
  - [ ] 4.7 Implement list_tasks MCP tool handler with PRD and project filtering
  - [ ] 4.8 Implement update_task MCP tool handler for status and detail management
  - [ ] 4.9 Create Subtask data model with checklist item structure
  - [ ] 4.10 Implement add_subtask MCP tool handler with task association
  - [ ] 4.11 Implement list_subtasks MCP tool handler for task-specific queries
  - [ ] 4.12 Implement complete_subtask MCP tool handler with completion tracking
  - [ ] 4.13 Create hierarchical relationship management between PRDs, tasks, and subtasks
  - [ ] 4.14 Add validation logic for all PRD, task, and subtask operations
  - [ ] 4.15 Create comprehensive unit tests for PRD, task, and subtask functionality

- [ ] 5.0 Create Status Management and Workflow Automation
  - [ ] 5.1 Implement status column definitions (Backlog, This Sprint, Up Next, In Progress, Done)
  - [ ] 5.2 Create move_prd_to_column MCP tool handler for status transitions
  - [ ] 5.3 Create move_task_to_column MCP tool handler for task status management
  - [ ] 5.4 Implement automatic parent status updates when all children are complete
  - [ ] 5.5 Create get_task_progress MCP tool handler for completion percentage tracking
  - [ ] 5.6 Implement bulk status update operations for multiple items
  - [ ] 5.7 Create workflow automation logic for status change triggers
  - [ ] 5.8 Add status change history tracking and audit logging
  - [ ] 5.9 Implement project health and progress reporting queries
  - [ ] 5.10 Create validation rules for status transitions and workflow compliance
  - [ ] 5.11 Add comprehensive integration tests for complete workflow scenarios
  - [ ] 5.12 Create end-to-end tests simulating full PRD lifecycle automation
