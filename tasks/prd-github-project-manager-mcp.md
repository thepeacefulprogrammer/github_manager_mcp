# Product Requirements Document: GitHub Project Manager MCP Server

## Introduction/Overview

The GitHub Project Manager MCP Server is a Model Context Protocol server that enables AI agents (like Claude/Cursor) to automate GitHub project management through a structured workflow. This server bridges the gap between the user's established PRD-driven development workflow and GitHub's project management capabilities, allowing AI agents to automatically update project status as work progresses.

The system implements a hierarchical project structure (Project → PRDs → Tasks → Subtasks) that mirrors the user's current development methodology while integrating with GitHub Projects v2 for visualization and tracking.

## Goals

1. **Automate GitHub Project Updates**: Enable AI agents to automatically update GitHub project status as PRD workflow progresses
2. **Maintain Workflow Consistency**: Preserve the user's established PRD → Tasks → Subtasks development methodology
3. **Provide Progress Visibility**: Offer clear progress tracking through GitHub Projects with status columns
4. **Seamless Integration**: Work directly with Cursor/Claude to eliminate manual project management overhead
5. **Self-Contained Operation**: Function as a standalone MCP server that can be launched by Cursor without external dependencies

## User Stories

1. **As a developer**, I want to create a new project in GitHub so that I can organize multiple PRDs under a single initiative
2. **As a developer**, I want to add PRDs to my project so that I can track major feature development efforts
3. **As a developer**, I want the AI agent to automatically create tasks from my PRD so that I don't have to manually set up project tracking
4. **As a developer**, I want the AI agent to update task status as we complete subtasks so that my GitHub project stays current without manual intervention
5. **As a developer**, I want to see progress through status columns (Backlog, This Sprint, Up Next, In Progress, Done) so that I can quickly assess project health
6. **As a developer**, I want to query my project status through the AI agent so that I can get updates without leaving my development environment
7. **As a developer**, I want to move PRDs and tasks between status columns so that I can manage my project flow

## Functional Requirements

### Project Management
1. The system must allow creation of new GitHub Projects v2 boards ✅ **COMPLETED**
2. The system must allow listing of existing GitHub Projects ✅ **COMPLETED**
3. The system must allow retrieval of project details and current status ✅ **COMPLETED**
4. The system must support project deletion and archiving ✅ **COMPLETED (deletion)**
5. The system must allow updating project metadata including name, description, and visibility ✅ **COMPLETED**

### PRD Management
5. The system must allow adding PRDs as high-level items to a GitHub Project ✅ **COMPLETED**
6. The system must allow listing all PRDs within a project ⏳ **NEXT PRIORITY**
7. The system must allow updating PRD status and details ⏳ **PLANNED**
8. The system must support moving PRDs between status columns ⏳ **PLANNED**
9. The system must allow retrieval of tasks associated with a specific PRD ⏳ **PLANNED**
10. The system must support deletion of PRDs from projects ✅ **COMPLETED**

### Task Management
11. The system must allow creation of tasks under a specific PRD
12. The system must allow listing all tasks within a PRD or project
13. The system must allow updating task status, assignee, and details
14. The system must support moving tasks between status columns
15. The system must allow retrieval of subtasks associated with a specific task

### Subtask Management
16. The system must allow creation of subtasks under a specific task
17. The system must allow listing all subtasks within a task
18. The system must allow marking subtasks as complete/incomplete
19. The system must automatically update parent task status when all subtasks are complete
20. The system must automatically update parent PRD status when all tasks are complete

### Status Management
21. The system must support the following status columns: Backlog, This Sprint, Up Next, In Progress, Done
22. The system must allow moving items between status columns
23. The system must track status change history
24. The system must support bulk status updates

### Integration Features
25. The system must provide MCP tool interfaces for all CRUD operations
26. The system must support AI agent automation of status updates during workflow execution
27. The system must provide query capabilities for project health and progress reporting
28. The system must handle GitHub API authentication and rate limiting

## Non-Goals (Out of Scope)

1. **Git Operations**: Will not handle commits, branches, or pull requests (existing tools handle this)
2. **Code Integration**: Will not analyze or modify source code directly
3. **GitHub Issues Integration**: Will not sync with or manage GitHub Issues (separate from Projects v2)
4. **Time Tracking**: Will not include detailed time tracking or estimation features
5. **Advanced Reporting**: Will not include complex analytics or reporting dashboards
6. **Multi-User Collaboration**: Initial version focuses on single-user workflow automation
7. **External Tool Integration**: Will not integrate with tools outside GitHub ecosystem

## Current Implementation Status

### ✅ **COMPLETED - Project Level CRUD (100%)**
- ✅ **Create**: `create_project` - Fully functional with repository association
- ✅ **Read**: `list_projects`, `get_project_details` - Complete with pagination and filtering
- ✅ **Update**: `update_project` - **COMPLETED** with comprehensive metadata management
- ✅ **Delete**: `delete_project` - Implemented with safety confirmation

### 🚧 **IN PROGRESS - PRD Level CRUD (50%)**
- ✅ **Create**: `add_prd_to_project` - Fully functional with comprehensive metadata
- ❌ **Read**: `list_prds` - Planned next after project CRUD completion
- ❌ **Update**: `update_prd` - Planned for status and detail management
- ✅ **Delete**: `delete_prd_from_project` - Implemented with safety confirmation

### 📋 **PLANNED - Task Level CRUD (0%)**
- ❌ **Create**: `create_task` - Will link to parent PRDs
- ❌ **Read**: `list_tasks` - Will support PRD and project filtering
- ❌ **Update**: `update_task` - Will handle status and assignment changes
- ❌ **Delete**: `delete_task` - Will include cascade considerations

### 📝 **PLANNED - Subtask Level CRUD (0%)**
- ❌ **Create**: `create_subtask` - Will implement as checklist items
- ❌ **Read**: `list_subtasks` - Will support task-specific queries
- ❌ **Update**: `update_subtask` - Will handle completion status
- ❌ **Delete**: `delete_subtask` - Will update parent task progress

## Design Considerations

### CRUD-First Development Approach
The implementation follows a hierarchical CRUD completion strategy:
1. **Complete Project Level CRUD** (current focus)
2. **Complete PRD Level CRUD**
3. **Complete Task Level CRUD**
4. **Complete Subtask Level CRUD**
5. **Implement Status Management and Workflow Automation**

This approach ensures solid foundations at each level before building dependent functionality.

### Update Project Requirements
The `update_project` functionality must support:
- **Project Name Updates**: Ability to rename projects while preserving relationships
- **Description Updates**: Modify project descriptions and documentation
- **Visibility Changes**: Update project visibility settings (if supported by GitHub API)
- **Metadata Updates**: Update project fields and custom properties
- **Validation**: Ensure updates don't break existing PRD/Task relationships
- **Audit Trail**: Track update history for debugging and rollback capabilities

### GitHub Projects v2 Structure
- Utilize GitHub Projects v2 as the underlying data store
- Map PRDs to high-level project items with custom fields
- Map Tasks to project items linked to PRD items
- Map Subtasks to checklist items within task items

### Status Column Configuration
- **Backlog**: Items planned but not yet prioritized
- **This Sprint**: Items committed for current development cycle
- **Up Next**: Items ready to begin work
- **In Progress**: Items currently being worked on
- **Done**: Completed items

### MCP Server Architecture
- Implement as standalone Python-based MCP server
- Use GitHub GraphQL API for efficient data operations
- Support both stdio and HTTP transport protocols
- Include comprehensive error handling and logging

## Technical Considerations

### Dependencies
- GitHub GraphQL API access
- Python MCP SDK
- GitHub authentication (Personal Access Token or GitHub App)
- OAuth flow support for secure authentication

### Performance Requirements
- Handle projects with up to 100 PRDs
- Support up to 50 tasks per PRD
- Support up to 20 subtasks per task
- Respond to MCP calls within 2 seconds for standard operations

### Security Requirements
- Secure storage of GitHub authentication tokens
- Proper scope management for GitHub API access
- Input validation for all user-provided data
- Rate limiting compliance with GitHub API

### Integration Points
- Must work with Cursor AI environment
- Must integrate with existing PRD workflow tools
- Must support the user's task management rules and protocols

## Success Metrics

1. **Automation Efficiency**: 90% reduction in manual GitHub project management tasks
2. **Workflow Compliance**: 100% of PRD workflow steps automatically reflected in GitHub Projects
3. **Update Accuracy**: 99% accuracy in status updates reflecting actual work progress
4. **Response Time**: Sub-2-second response times for standard MCP operations
5. **User Adoption**: Daily use of the MCP server for project management activities

## Open Questions

1. **GitHub Authentication**: Should we use Personal Access Tokens, GitHub Apps, or support both authentication methods?
2. **Project Templates**: Should we support project templates for common project structures?
3. **Notifications**: Should the system support notifications when status changes occur?
4. **Backup/Export**: Should we include functionality to export project data for backup purposes?
5. **Concurrent Access**: How should we handle potential conflicts if the user manually updates GitHub Projects while the AI agent is working?
6. **Custom Fields**: Should we support additional custom fields beyond the basic PRD/Task/Subtask structure?
