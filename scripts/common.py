"""daily-agent-briefing 公共工具。纯标准库,零第三方依赖(代理常死,别引 pip)。"""
import os
import sys
import urllib.request

# Windows 下 Python 默认 stdout 是 GBK,终端是 UTF-8,中文会乱码。统一改成 UTF-8。
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001  重定向/无 encoding 时忽略
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SOURCES_FILE = os.path.join(ROOT, "sources.yaml")
DATA_DIR = os.path.join(ROOT, "data", "raw")
BASELINE_FILE = os.path.join(ROOT, "data", "baseline.json")
LATEST_DELTA_FILE = os.path.join(ROOT, "data", "latest_delta.json")

# 系统全局代理(127.0.0.1:10809)经常半死:urllib 会读注册表代理,SSL 握手超时;
# curl --noproxy 直连却是通的。所以这里显式装一个「不走任何代理」的 opener,全部直连。
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))


def load_sources():
    """读 sources.yaml,返回 {"sources": [...], "repost_domains": [...]}。"""
    text = open(SOURCES_FILE, encoding="utf-8").read()
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {"sources": []}
    except ImportError:
        return _parse_flat_yaml(text)


def _parse_flat_yaml(text):
    """PyYAML 不可用时的降级解析,只支持本文件受控的扁平格式。"""
    sources = []
    repost_domains = []
    mode = None  # None | "sources" | "repost"
    current = None
    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("sources:"):
            mode = "sources"
            continue
        if stripped.startswith("repost_domains:"):
            mode = "repost"
            continue
        indent = len(line) - len(stripped)
        if mode == "repost":
            if stripped.startswith("- "):
                repost_domains.append(_coerce(stripped[2:].strip()))
            continue
        if mode == "sources":
            if stripped.startswith("- "):
                if current is not None:
                    sources.append(current)
                current = {}
                _add_kv(current, stripped[2:])
            elif current is not None and indent > 0:
                _add_kv(current, stripped)
    if current is not None:
        sources.append(current)
    return {"sources": sources, "repost_domains": repost_domains}


def _add_kv(d, text):
    if ":" not in text:
        return
    k, v = text.split(":", 1)
    d[k.strip()] = _coerce(v.strip())


def _coerce(v):
    if v == "true":
        return True
    if v == "false":
        return False
    if v.isdigit():
        return int(v)
    return v


def _decode(data):
    """先按 utf-8 解,失败(国内 GBK 站)再按 gbk 解,避免中文乱码丢字。"""
    for enc in ("utf-8", "gbk"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", "ignore")


def fetch_url(url, timeout=25):
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (daily-agent-briefing/0.1)"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return _decode(r.read())


def fetch_json(url, timeout=25):
    """GET 一个返回 JSON 的接口(GitHub API 等),返回解析后的对象。"""
    import json
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (daily-agent-briefing/0.1)",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(_decode(r.read()))
