"""
SQLite 通用连接与 CRUD 封装。

依赖:
    - 仅 Python 标准库 sqlite3

用法:
    with Database("data/knowledge_base.db") as db:
        db.execute("SELECT * FROM nodes")
"""

import sqlite3
from pathlib import Path
from typing import Any, Generator, Optional


class Database:
    """SQLite 数据库通用连接管理。"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """建立连接（如已连接则返回现有连接）。"""
        if self.conn is None:
            # 确保父目录存在
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA foreign_keys=ON")
        return self.conn

    def close(self):
        """关闭连接。"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """执行单条 SQL。"""
        return self.connect().execute(sql, params)

    def executemany(self, sql: str, params_list: list[tuple]) -> sqlite3.Cursor:
        """批量执行 SQL。"""
        return self.connect().executemany(sql, params_list)

    def fetchone(self, sql: str, params: tuple = ()) -> Optional[dict]:
        """查询单行，返回 dict。"""
        row = self.execute(sql, params).fetchone()
        return dict(row) if row else None

    def fetchall(self, sql: str, params: tuple = ()) -> list[dict]:
        """查询多行，返回 list[dict]。"""
        rows = self.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def init_schema(self, schema_path: str) -> int:
        """执行 schema.sql 建表，返回执行的语句数。

        Args:
            schema_path: schema.sql 文件路径（支持项目相对路径和绝对路径）。

        Returns:
            成功执行的 SQL 语句数。
        """
        schema_file = Path(schema_path)
        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        sql = schema_file.read_text(encoding="utf-8")
        count = 0
        for statement in sql.split(";"):
            stmt = statement.strip()
            if stmt:
                self.execute(stmt)
                count += 1
        return count

    def __enter__(self) -> "Database":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.close()
