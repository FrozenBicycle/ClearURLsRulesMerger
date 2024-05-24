import json
import logging
from copy import deepcopy
from hashlib import sha256
from http.client import HTTPResponse
from pathlib import Path
from sys import argv, exit
from typing import LiteralString
from urllib.request import urlopen

# public rules
PUBLIC_RULES_URL: LiteralString = "https://github.com/ClearURLs/Rules/raw/master/data.min.json"
# local rules
LOCAL_RULES_PATH: LiteralString = "./data/data.json"
MERGED_PATH: LiteralString = "./data/data.merged.json"


# type aliases
type Value = str | bool | list[str] | Rules
type Node = Value | dict[str, "Node"]
type Rules = dict[str, Node]


# constants
PRIMITIVES = (str, bool)
COMPOSITES = (list, dict)


def merge_values(public: Value, local: Value) -> Value:
    """merge two basic values or lists"""
    if isinstance(public, PRIMITIVES) or isinstance(local, PRIMITIVES):
        # Basic values conflict. Local values are used
        return local
    
    if isinstance(public, list) and isinstance(local, list):
        # Merge the list, keeping the original order
        return list(dict.fromkeys(public + local))
    
    raise TypeError(f"Unsupported value types: {type(public)}, {type(local)}")


def merge_nodes(public: Node, local: Node) -> Node:
    if isinstance(public, dict) and isinstance(local, dict):
        # merge dict nodes
        merged: Node = deepcopy(public)
        for key, local_value in local.items():
            if key in merged:
                public_value = merged[key]
                merged[key] = merge_nodes(public_value, local_value)
            else:
                merged[key] = deepcopy(local_value)
        return merged
    else:
        # merge basic values or lists
        return merge_values(public, local) # type: ignore


def merge_rules(public: Rules, local: Rules) -> Rules:
    merged: Rules = {}
    all_keys: set[str] = set(public.keys()) | set(local.keys())

    for key in all_keys:
        public_node: Node | None = public.get(key)
        local_node: Node | None = local.get(key)

        if public_node is None:
            merged[key] = deepcopy(local_node) # type: ignore
            
        elif local_node is None:
            merged[key] = deepcopy(public_node)
        
        else:
            merged[key] = merge_nodes(public_node, local_node)
    return merged
    
    
def fetch_public_rules(json_url: LiteralString) -> Rules:
    # download public ClearURLs rules
    with urlopen(json_url) as response:
        response: HTTPResponse = response
        return json.load(response)


def fetch_local_rules(path: Path) -> Rules:
    # read local rules file
    with path.open("rb") as file:
        return json.load(file)
    
    
def save_binary(path: Path, data: bytes) -> None:
    with path.open("wb") as file:
        file.write(data)


def gen_hash(data: bytes) -> bytes:
    """generate hash of data with SHA256, return the hexdigest"""
    return sha256(data).hexdigest().encode("ascii")


def is_path_valid(path: Path, existence_needed: bool) -> tuple[bool, str]:
    # path don't need to exist
    if not existence_needed:
        if path.parent.exists() and path.parent.is_dir():
            return True, ""
        return False, "The parent of the target path does not exist" \
            ", or is not a directory"
    
    # path must exist and be a file
    if not path.exists():
        return False, "File not found"
    
    if not path.is_file():
        return False, "Target is not a file"

    if path.suffix.lower() != ".json":
        return False, "File extension is not '.json'"
    
    return True, ""


def dump_rules(rules: Rules) -> bytes:
    return json \
        .dumps(rules, indent=None, ensure_ascii=True) \
        .encode("ascii")


def gen_hash_path(json_path: Path) -> Path:
    return json_path.with_suffix(".hash")


def config_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
        format="[%(asctime)s %(levelname)s] %(message)s",
    )


def main(argv: list[str]) -> int:
    global PUBLIC_RULES_URL, LOCAL_RULES_PATH
    
    config_logging()
    
    # parse command line arguments, set I/O paths
    SRC: Path = Path(argv[1] if len(argv) > 1 else LOCAL_RULES_PATH)
    DEST: Path = Path(argv[2] if len(argv) > 2 else MERGED_PATH)
    
    logging.info(f"Merging rules from [{SRC}] to [{DEST}]")
    
    # paths validation
    valid, reason = is_path_valid(SRC, True)
    valid2, reason2 = is_path_valid(DEST, False)
    
    assert valid and valid2, \
        f"Input path [{SRC}] with problem: {reason}\n" \
            f"Output path [{DEST}] with problem: {reason2}"
    
    # download the latest public ClearURLs rules
    pulic: Rules = fetch_public_rules(PUBLIC_RULES_URL)
    logging.info("public rules fetched.")
    
    # load local rules file
    local: Rules = fetch_local_rules(SRC)
    logging.info("local rules fetched.")
    
    # merge rules
    merged: Rules = merge_rules(pulic, local)
    logging.info("rules merged.")
    
    # create hash of merged rules
    data: bytes = dump_rules(merged)
    _hash: bytes = gen_hash(data)
    HASH_DEST: Path = gen_hash_path(DEST)
    
    logging.info(f"rules size: {len(data) / 1024:.0f} kB")
    
    # save merged rules and hash to file
    save_binary(DEST, data)
    save_binary(HASH_DEST, _hash)
    logging.info(f"rules and hash saved, program exit.")
    
    return 0
    

if __name__ == "__main__":
    exit(main(argv))
