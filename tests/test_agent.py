from barberian.agent import handle_message


def test_add_mcp():
    result = handle_message("add GitHub MCP")
    assert result["ok"] is True
    assert result["type"] == "mcp"
    assert result["name"] == "github"


def test_add_skill():
    result = handle_message("add research skill")
    assert result["ok"] is True
    assert result["type"] == "skill"
    assert result["name"] == "research"


def test_list_integrations():
    handle_message("add GitHub MCP")
    result = handle_message("list MCP")
    assert result["ok"] is True
    assert "github" in result["items"]
