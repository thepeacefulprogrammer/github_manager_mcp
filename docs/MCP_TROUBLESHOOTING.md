# GitHub Project Manager MCP Server - Troubleshooting Guide

## Quick Setup Verification

### 1. Check MCP Server Configuration
Verify your `~/.cursor/mcp.json` contains:

```json
{
  "mcpServers": {
    "github-project-manager": {
      "command": "/home/randy/workspace/personal/github_manager_mcp/venv/bin/python",
      "args": [
        "/home/randy/workspace/personal/github_manager_mcp/src/github_project_manager_mcp/mcp_server_fastmcp.py",
        "--debug"
      ],
      "cwd": "/home/randy/workspace/personal/github_manager_mcp",
      "env": {
        "PYTHONPATH": "/home/randy/workspace/personal/github_manager_mcp/src:/home/randy/workspace/personal/github_manager_mcp"
      },
      "disabled": false
    }
  }
}
```

### 2. Test Server Manually
```bash
cd /home/randy/workspace/personal/github_manager_mcp
PYTHONPATH="/home/randy/workspace/personal/github_manager_mcp/src:/home/randy/workspace/personal/github_manager_mcp" \
/home/randy/workspace/personal/github_manager_mcp/venv/bin/python \
/home/randy/workspace/personal/github_manager_mcp/src/github_project_manager_mcp/mcp_server_fastmcp.py --help
```

## Common Issues and Solutions

### Issue 1: "Server not recognized in Cursor"
**Symptoms**: MCP server doesn't appear in Cursor's tool list

**Solutions**:
1. **Restart Cursor completely** (close all windows, restart application)
2. Check that `~/.cursor/mcp.json` is valid JSON (use `jq . ~/.cursor/mcp.json`)
3. Verify the Python path is correct: `ls -la /home/randy/workspace/personal/github_manager_mcp/venv/bin/python`
4. Check server logs in `logs/mcp_server_*.log`

### Issue 2: "Import errors when starting server"
**Symptoms**: Server fails to start with module import errors

**Solutions**:
1. Ensure virtual environment is activated and dependencies installed:
   ```bash
   cd /home/randy/workspace/personal/github_manager_mcp
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Verify PYTHONPATH includes both src directories
3. Check that all required modules exist in the expected locations

### Issue 3: "GitHub authentication errors"
**Symptoms**: Tools work but GitHub API calls fail

**Solutions**:
1. Set GitHub token in environment:
   ```bash
   export GITHUB_TOKEN="your_token_here"
   ```
2. Or create `.env` file in project root:
   ```
   GITHUB_TOKEN=your_token_here
   ```
3. Verify token has required permissions for GitHub Projects v2

### Issue 4: "Server starts but tools don't work"
**Symptoms**: Server appears in Cursor but tool calls fail

**Solutions**:
1. Check server logs for detailed error messages
2. Verify FastMCP version compatibility: `pip show fastmcp`
3. Test individual tools manually using the test_connection tool first
4. Ensure GitHub client is properly initialized (check logs for "GitHub client initialized successfully")

### Issue 5: "Logging to stdout breaks MCP protocol"
**Symptoms**: Server appears to start but Cursor can't communicate with it

**Solutions**:
1. **CRITICAL**: Ensure all logging goes to stderr, never stdout
2. Check that logging configuration uses `StreamHandler(sys.stderr)`
3. Verify no print statements or other stdout output in the code

## Debugging Steps

### 1. Enable Debug Logging
The server is configured with `--debug` flag by default. Check logs in:
```
/home/randy/workspace/personal/github_manager_mcp/logs/mcp_server_*.log
```

### 2. Test Server Isolation
Run the server in isolation to check for startup issues:
```bash
cd /home/randy/workspace/personal/github_manager_mcp
python src/github_project_manager_mcp/mcp_server_fastmcp.py --debug
```

### 3. Verify Dependencies
```bash
cd /home/randy/workspace/personal/github_manager_mcp
pip list | grep -E "(fastmcp|mcp|httpx|pydantic)"
```

### 4. Check Cursor MCP Status
In Cursor, you can check MCP server status through:
- Command Palette → "MCP: Show Server Status"
- Look for "github-project-manager" in the list

## Expected Behavior

### Successful Startup Logs
You should see these key messages in the logs:
```
INFO - Successfully imported FastMCP
INFO - Successfully imported project handlers
INFO - FastMCP server created successfully
INFO - All MCP tools registered successfully with FastMCP
INFO - GitHubProjectManagerMCPFastServer initialization complete
```

### Available Tools
When working correctly, Cursor should show these tools:
- `test_connection` - Basic connectivity test
- `create_project` - Create GitHub Projects v2 project
- `list_projects` - List projects for user/organization

## Getting Help

If issues persist:
1. Check the main project logs in `logs/` directory
2. Compare with the working legal-case-prep-mcp configuration
3. Verify all file paths are absolute and correct for your system
4. Ensure virtual environment is properly isolated and activated

## Success Indicators

✅ Server starts without import errors
✅ Logs show "GitHubProjectManagerMCPFastServer initialization complete"
✅ Cursor recognizes the server in MCP tool list
✅ `test_connection` tool responds successfully
✅ GitHub tools work with proper authentication
