"""Post-tool Hook: 检查修改的文件是否有跨层导入违规"""
import re
import sys
from pathlib import Path

LAYER_DEPENDENCIES = {
    "infrastructure": set(),
    "knowledge_graph": {"infrastructure"},
    "extraction": {"infrastructure", "knowledge_graph"},
    "reasoning": {"infrastructure", "knowledge_graph", "extraction", "retrieval"},
    "retrieval": {"infrastructure", "knowledge_graph"},
    "generation": {"infrastructure", "retrieval", "reasoning"},
}

def check_file(filepath: Path) -> list[str]:
    content = filepath.read_text(encoding="utf-8")
    violations = []
    imports = re.findall(r"^\s*from\s+src\.(\w+)", content, re.MULTILINE)
    imports += re.findall(r"^\s*import\s+src\.(\w+)", content, re.MULTILINE)
    
    for part in filepath.parts:
        if part in LAYER_DEPENDENCIES:
            current_layer = part
            allowed = LAYER_DEPENDENCIES[current_layer]
            for dep in imports:
                if dep != current_layer and dep not in allowed:
                    violations.append(
                        f"❌ {filepath}: 禁止 {current_layer} 导入 {dep}"
                    )
            break
    return violations

if __name__ == "__main__":
    changed_files = sys.argv[1:] if len(sys.argv) > 1 else []
    all_violations = []
    for f in changed_files:
        p = Path(f)
        if p.suffix == ".py":
            all_violations.extend(check_file(p))
    
    if all_violations:
        print("\n".join(all_violations))
        print("⚠️  请在提交前修复以上导入违规")
        sys.exit(1)
    else:
        print("✅ 导入检查通过")