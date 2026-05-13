"""
MCP Server: 知识图谱查询接口
运行方式：cline 自动启动，通过 MCP 协议通信
"""
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).parents[3] / "data" / "knowledge_base.db"


def handle_request(request: dict) -> dict:
    method = request.get("method", "")
    
    if method == "tools/list":
        return {
            "tools": [
                {
                    "name": "kg_query",
                    "description": "查询知识图谱中的疾病-症状关系",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "disease": {"type": "string", "description": "疾病名称"},
                            "max_depth": {"type": "integer", "description": "查询深度", "default": 3}
                        },
                        "required": ["disease"]
                    }
                },
                {
                    "name": "m_rule_lookup",
                    "description": "查询 M-rule 规则详情",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "rule_id": {"type": "string", "description": "规则 ID"}
                        },
                        "required": ["rule_id"]
                    }
                }
            ]
        }
    
    if method == "tools/call":
        tool_name = request.get("params", {}).get("name", "")
        arguments = request.get("params", {}).get("arguments", {})
        
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        
        try:
            if tool_name == "kg_query":
                cursor = conn.execute(
                    """SELECT * FROM pathways WHERE disease = ? LIMIT 50""",
                    (arguments["disease"],)
                )
                results = [dict(row) for row in cursor.fetchall()]
                return {"content": [{"type": "text", "text": json.dumps(results, ensure_ascii=False, indent=2)}]}
            
            elif tool_name == "m_rule_lookup":
                cursor = conn.execute(
                    """SELECT * FROM m_rules WHERE rule_id = ?""",
                    (arguments["rule_id"],)
                )
                result = cursor.fetchone()
                if result:
                    return {"content": [{"type": "text", "text": json.dumps(dict(result), ensure_ascii=False, indent=2)}]}
                return {"content": [{"type": "text", "text": f"Rule {arguments['rule_id']} not found"}]}
        finally:
            conn.close()
    
    return {"error": f"Unknown method: {method}"}


if __name__ == "__main__":
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = handle_request(request)
            print(json.dumps(response), flush=True)
        except json.JSONDecodeError as e:
            print(json.dumps({"error": str(e)}), flush=True)