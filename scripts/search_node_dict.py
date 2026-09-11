#!/usr/bin/env python3
"""Cross-platform node-dictionary lookup (macOS/Linux/Windows) - Python twin of
search_node_dict.ps1. Searches BOTH dictionaries:
    references/node_dictionary_merged.json  (1665 library nodes)
    references/node_dict_extras.json        (PIE-verified Actor/Component members, special K2Nodes, patterns)

Usage:
    python3 search_node_dict.py -q spawn                 # substring search, all fields
    python3 search_node_dict.py -q MakeTransform --exact # exact display_name / dsl_type_id
    python3 search_node_dict.py -q "Math|"               # browse a category
    python3 search_node_dict.py -q transform --max 40    # more results

Output mirrors the ps1 version (MAIN/EXTRA tags, pins, defaults, notes, sources).
Namespace law applies: dictionary display_name/category are PALETTE names, NOT tool
type_ids - verify candidates with find_node_types before create_node (G16).
"""
import argparse
import json
import os
import sys

STOPWORDS = {"str", "ref", "bool", "int", "float", "num", "obj", "optional", "empty",
             "all", "none", "true", "false", "eg", "ie", "etc", "and", "or", "the",
             "with", "for", "use", "default", "if"}


def skill_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def format_pins(pins):
    if not pins:
        return "(none)"
    parts = []
    for p in pins:
        if p.get("type") == "exec":
            continue
        d = p.get("default")
        s = ""
        if d is not None and str(d) != "":
            s = "=" + str(d)
        parts.append("{}:{}{}".format(p.get("name"), p.get("type"), s))
    return " ".join(parts) if parts else "(exec only)"


def test_match(field, q, exact):
    if field is None or field == "":
        return -1
    f = str(field)
    if exact:
        return 0 if f.lower() == q.lower() else -1
    if f.lower() == q.lower():
        return 0
    if q.lower() in f.lower():
        return 1
    return -1


def get_rank(node, key, q, exact):
    display = node.get("display_name")
    idv = node.get("dsl_type_id")
    best = -1
    for r in (test_match(display, q, exact), test_match(idv, q, exact)):
        if r >= 0 and (best < 0 or r < best):
            best = r
    if best >= 0:
        return best
    if exact:
        return -1
    cat = str(node.get("category") or "")
    if q.lower() in cat.lower():
        return 2
    fn = str(node.get("function_name") or "")
    if q.lower() in fn.lower():
        return 3
    if q.lower() in key.lower():
        return 3
    return -1


def load(path):
    if not os.path.exists(path):
        return None
    # utf-8-sig transparently strips a BOM if present (main dict has one; PS tolerated it, Python does not)
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser(description="Cross-platform node dictionary search")
    ap.add_argument("-q", "--query", required=True, help="search string")
    ap.add_argument("--exact", action="store_true", help="exact display_name/dsl_type_id match")
    ap.add_argument("--max", type=int, default=15, help="max results (0 = all)")
    args = ap.parse_args()

    q = args.query
    sd = skill_dir()
    hits = []

    main_obj = load(os.path.join(sd, "references", "node_dictionary_merged.json"))
    if main_obj:
        for key, n in main_obj.get("nodes", {}).items():
            rank = get_rank(n, key, q, args.exact)
            if rank >= 0:
                cat = n.get("category") or ""
                disp = n.get("display_name") or ""
                nid = "{}|{}".format(cat, disp) if (cat and disp) else (disp or key)
                hits.append((rank, "MAIN ", nid, n))

    extra_obj = load(os.path.join(sd, "references", "node_dict_extras.json"))
    if extra_obj:
        for key, n in extra_obj.get("nodes", {}).items():
            rank = get_rank(n, key, q, args.exact)
            if rank >= 0:
                hits.append((rank, "EXTRA", n.get("dsl_type_id", key), n))

    hits.sort(key=lambda h: h[0])
    shown = hits if args.max <= 0 else hits[: args.max]

    if not shown:
        print("0 hits for '{}'. Try a shorter substring (e.g. 'Spawn' not 'SpawnActorFromClass'), "
              "drop --exact, or browse a category ('Math|').".format(q))
        return

    for rank, src, nid, n in shown:
        owner = ""
        fo = n.get("function_owner")
        if fo:
            owner = "  ({})".format(str(fo).replace("/Script/Engine.", ""))
        elif n.get("ue_class"):
            owner = "  ({})".format(n["ue_class"])
        print("[{}] {}{}".format(src.strip(), nid, owner))
        print("  in : {}".format(format_pins(n.get("inputs"))))
        if n.get("outputs"):
            print("  out: {}".format(format_pins(n.get("outputs"))))
        if n.get("notes"):
            print("  ! {}".format(n["notes"]))
        if src.strip() == "EXTRA" and n.get("source"):
            print("  src: {}".format(n["source"]))
        print("")

    total = len(hits)
    shown_n = len(shown)
    if total > shown_n:
        print("({} of {} hits shown - raise --max to see more)".format(shown_n, total))
    else:
        print("({} hit(s))".format(total))


if __name__ == "__main__":
    sys.exit(main())
