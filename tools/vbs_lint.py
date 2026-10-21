#!/usr/bin/env python3
"""Light structural lint for the VBScript modules.

VBScript only runs on Windows, so this catches the common mistakes anywhere:
unbalanced blocks (If/End If, For/Next, Sub/End Sub ...), names defined twice
across modules (an error once the bundle is pasted into VPX), and non-ASCII
characters. The real test run is tests/run_tests.wsf under cscript.

    python3 tools/vbs_lint.py [files...]   # default: table/*.vbs tests/*.vbs
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

OPENERS = [
    (re.compile(r"^(public\s+|private\s+)?(default\s+)?sub\b", re.I), "sub"),
    (re.compile(r"^(public\s+|private\s+)?(default\s+)?function\b", re.I), "function"),
    (re.compile(r"^(public\s+|private\s+)?property\s+(get|let|set)\b", re.I), "property"),
    (re.compile(r"^class\b", re.I), "class"),
    (re.compile(r"^select\s+case\b", re.I), "select"),
    (re.compile(r"^with\b", re.I), "with"),
    (re.compile(r"^for\b", re.I), "for"),
    (re.compile(r"^do\b", re.I), "do"),
    (re.compile(r"^while\b", re.I), "while"),
]
CLOSERS = [
    (re.compile(r"^end\s+sub\b", re.I), "sub"),
    (re.compile(r"^end\s+function\b", re.I), "function"),
    (re.compile(r"^end\s+property\b", re.I), "property"),
    (re.compile(r"^end\s+class\b", re.I), "class"),
    (re.compile(r"^end\s+select\b", re.I), "select"),
    (re.compile(r"^end\s+with\b", re.I), "with"),
    (re.compile(r"^end\s+if\b", re.I), "if"),
    (re.compile(r"^next\b", re.I), "for"),
    (re.compile(r"^loop\b", re.I), "do"),
    (re.compile(r"^wend\b", re.I), "while"),
]
DEF_RE = re.compile(r"^(?:public\s+|private\s+)?(sub|function)\s+(\w+)", re.I)
GLOBAL_DIM_RE = re.compile(r"^(dim|const)\s+(.+)$", re.I)


def strip_line(line: str) -> str:
    """Remove string contents and comments."""
    out, in_str, i = [], False, 0
    while i < len(line):
        ch = line[i]
        if in_str:
            if ch == '"':
                if i + 1 < len(line) and line[i + 1] == '"':
                    i += 2
                    continue
                in_str = False
                out.append('"')
            i += 1
            continue
        if ch == '"':
            in_str = True
            out.append('"')
        elif ch == "'":
            break
        else:
            out.append(ch)
        i += 1
    s = "".join(out).strip()
    if re.match(r"^rem\b", s, re.I):
        return ""
    return s


def logical_lines(text: str):
    """Yield (line_no, statement) with continuations joined and ':' split."""
    buf, start = "", 0
    for n, raw in enumerate(text.splitlines(), 1):
        s = strip_line(raw)
        if not buf:
            start = n
        if s.endswith(" _") or s == "_":
            buf += s[:-1] + " "
            continue
        buf += s
        for stmt in buf.split(":"):
            stmt = stmt.strip()
            if stmt:
                yield start, stmt
        buf = ""


def lint_file(path: pathlib.Path, defs: dict, errors: list):
    text = path.read_text(encoding="utf-8")
    for n, line in enumerate(text.splitlines(), 1):
        if any(ord(c) > 127 for c in line):
            errors.append(f"{path.name}:{n}: non-ASCII character (VPX script editor may mangle it)")
    stack = []
    in_class = 0
    for n, stmt in logical_lines(text):
        low = stmt.lower()
        # Single-line If: "If x Then y"
        m = re.match(r"^if\b.*\bthen\b(.*)$", low)
        if m:
            if m.group(1).strip() == "":
                stack.append(("if", n))
            continue
        if re.match(r"^(else|elseif)\b", low) or re.match(r"^exit\b", low):
            continue
        closed = False
        for rx, kind in CLOSERS:
            if rx.match(stmt):
                if not stack:
                    errors.append(f"{path.name}:{n}: '{stmt}' with nothing open")
                else:
                    top, at = stack.pop()
                    if top != kind:
                        errors.append(f"{path.name}:{n}: '{stmt}' closes {top} opened at line {at}")
                if kind == "class":
                    in_class -= 1
                closed = True
                break
        if closed:
            continue
        for rx, kind in OPENERS:
            if rx.match(stmt):
                stack.append((kind, n))
                if kind == "class":
                    in_class += 1
                break
        # Global definitions (outside classes and procedures)
        depth_proc = any(k in ("sub", "function", "property") for k, _ in stack[:-1]) if stack else False
        md = DEF_RE.match(stmt)
        if md and in_class == 0 and not depth_proc:
            name = md.group(2).lower()
            defs.setdefault(name, []).append(f"{path.name}:{n}")
        mg = GLOBAL_DIM_RE.match(stmt)
        if mg and in_class == 0 and not stack:
            for part in mg.group(2).split(","):
                nm = re.match(r"\s*(\w+)", part)
                if nm:
                    defs.setdefault(nm.group(1).lower(), []).append(f"{path.name}:{n}")
    for kind, at in stack:
        errors.append(f"{path.name}:{at}: {kind} never closed")


def main(argv):
    if argv:
        files = [pathlib.Path(a) for a in argv]
        groups = [files]
    else:
        # Each group shares one global namespace, as it does at run time.
        t = ROOT / "table"
        cabinet = [t / f"{m}.vbs" for m in ("tt_config", "tt_money", "tt_rules", "tt_sound",
                                            "tt_feel", "tt_display", "tt_scores", "tt_table")]
        tests = [t / f"{m}.vbs" for m in ("tt_config", "tt_money", "tt_rules", "tt_scores")]
        tests += sorted((ROOT / "tests").glob("*.vbs"))
        groups = [cabinet, tests, [t / "ThreatTide_loader.vbs"]]
    errors = []
    for files in groups:
        defs = {}
        for f in files:
            lint_file(f, defs, errors)
        for name, where in defs.items():
            if len(where) > 1:
                errors.append(f"'{name}' defined more than once: {', '.join(where)}")
    for e in errors:
        print(e)
    print(f"vbs_lint: {len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
