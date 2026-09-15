from barberian.mcp_client import MCPClient


def test_mcp_client_builds_json_rpc_requests():
    client = MCPClient("https://mcp.example.test")
    request = client.request_payload("tools/list", {})
    assert request["jsonrpc"] == "2.0"
    assert request["method"] == "tools/list"
    assert request["params"] == {}
    assert request["id"] == 1
