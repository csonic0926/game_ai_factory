#!/usr/bin/env python3
"""twin_db.py — CRUD/query CLI for a game's story-world database.

The database is the file set under <STORY_ROOT>/story_world/:
  seed_entities.json   canonical entities (entities: [{id, name, type, summary, why_included}])
  seeds/*.json         grouped seed records (each file: named lists of records, most with "id")
  changelog.jsonl      append-only mutation log written by this tool

Design rules:
  - storage stays as git-versioned JSON; this tool is the maintained access path
    (workers query instead of copying world facts through handoff files)
  - every mutation appends one changelog line; --chapter stamps write-backs
  - validate reports; it exits non-zero only on hard errors (unparseable JSON,
    duplicate ids), warnings (dangling relation refs) are listed but pass

Usage examples:
  twin_db.py --root <STORY_ROOT> list --type place
  twin_db.py --root <STORY_ROOT> get portal_gacha
  twin_db.py --root <STORY_ROOT> search 渡口 --limit 8
  twin_db.py --root <STORY_ROOT> add-entity --json '{"id":"place_pier_gate","name":"渡口正門","type":"place","summary":"...","why_included":"..."}' --chapter ENTRY_LANDING
  twin_db.py --root <STORY_ROOT> add-fact --statement "..." --source "chapter:ENTRY_LANDING"
  twin_db.py --root <STORY_ROOT> add-relation --from place_south_pier --to place_village --type threshold --why "..."
  twin_db.py --root <STORY_ROOT> add-record --file seeds/geography.json --list locations --json '{...}'
  twin_db.py --root <STORY_ROOT> writeback --chapter CH2 --manifest ch2_writeback.json
  twin_db.py --root <STORY_ROOT> validate
"""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path


def resolve_root(root: str) -> Path:
    p = Path(root)
    if (p / "story_world").is_dir():
        p = p / "story_world"
    if not (p / "seed_entities.json").is_file():
        sys.exit(f"error: {p} has no seed_entities.json (pass <STORY_ROOT> or the story_world dir)")
    return p


def load(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def log_change(root: Path, op: str, target: str, chapter: str | None, note: str = ""):
    entry = {
        "date": datetime.date.today().isoformat(),
        "op": op,
        "target": target,
        "chapter": chapter,
        "note": note,
    }
    with open(root / "changelog.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def seed_files(root: Path):
    return sorted((root / "seeds").glob("*.json")) if (root / "seeds").is_dir() else []


def record_lists(doc):
    """Yield (list_key, records) for every top-level list of dicts in a seed doc."""
    for key, val in doc.items():
        if isinstance(val, list) and val and isinstance(val[0], dict):
            yield key, val
        elif isinstance(val, dict):
            for sub, subval in val.items():
                if isinstance(subval, list) and subval and isinstance(subval[0], dict):
                    yield f"{key}.{sub}", subval


def all_known_ids(root: Path):
    ids = {}
    ents = load(root / "seed_entities.json")
    for e in ents.get("entities", []):
        if "id" in e:
            ids.setdefault(e["id"], []).append("seed_entities.json#entities")
    for sf in seed_files(root):
        doc = load(sf)
        for key, records in record_lists(doc):
            for r in records:
                if "id" in r:
                    ids.setdefault(r["id"], []).append(f"seeds/{sf.name}#{key}")
    return ids


def ref_tokens(value: str):
    """Split a relation endpoint like 'place_th_1f / place_th_2f' or
    'law_avatar（化身法則）' into bare id tokens."""
    tokens = []
    for part in re.split(r"[/、,]", value):
        part = part.strip()
        part = re.split(r"[（(\s]", part)[0].strip()
        if part:
            tokens.append(part)
    return tokens


def parse_json_arg(raw: str):
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"error: --json is not valid JSON: {e}")
    if not isinstance(obj, dict):
        sys.exit("error: --json must be a JSON object")
    return obj


# ---------------------------------------------------------------- commands

def cmd_list(root, args):
    ents = load(root / "seed_entities.json")["entities"]
    for e in ents:
        if args.type and e.get("type") != args.type:
            continue
        print(f"{e.get('id','?'):32} {e.get('type','?'):20} {e.get('name','')}")


def cmd_get(root, args):
    hits = []
    ents = load(root / "seed_entities.json")
    for e in ents.get("entities", []):
        if e.get("id") == args.id:
            hits.append(("seed_entities.json#entities", e))
    for sf in seed_files(root):
        for key, records in record_lists(load(sf)):
            for r in records:
                if r.get("id") == args.id:
                    hits.append((f"seeds/{sf.name}#{key}", r))
    if not hits:
        sys.exit(f"not found: {args.id}")
    for where, rec in hits:
        print(f"--- {where}")
        print(json.dumps(rec, ensure_ascii=False, indent=2))


def cmd_search(root, args):
    needle = args.keyword.lower()
    shown = 0
    files = [root / "seed_entities.json"] + seed_files(root)
    for path in files:
        doc = load(path)
        rel = path.name if path.parent == root else f"seeds/{path.name}"
        for key, records in record_lists(doc):
            for r in records:
                blob = json.dumps(r, ensure_ascii=False).lower()
                if needle in blob:
                    print(f"--- {rel}#{key}")
                    print(json.dumps(r, ensure_ascii=False, indent=2))
                    shown += 1
                    if shown >= args.limit:
                        print(f"(limit {args.limit} reached — refine the keyword)")
                        return
    if shown == 0:
        print(f"no records match: {args.keyword}")


def cmd_add_entity(root, args):
    path = root / "seed_entities.json"
    doc = load(path)
    if args.json:
        entity = parse_json_arg(args.json)
    else:
        if not (args.id and args.name and args.type and args.summary):
            sys.exit("error: give --json or all of --id --name --type --summary")
        entity = {"id": args.id, "name": args.name, "type": args.type,
                  "summary": args.summary,
                  "why_included": args.why or ""}
    missing = [k for k in ("id", "name", "type", "summary") if not entity.get(k)]
    if missing:
        sys.exit(f"error: entity missing required fields: {missing}")
    if any(e.get("id") == entity["id"] for e in doc["entities"]):
        sys.exit(f"error: entity id already exists: {entity['id']} (use update-entity)")
    if args.chapter and "source" not in entity:
        entity["source"] = f"chapter:{args.chapter}"
    doc["entities"].append(entity)
    save(path, doc)
    log_change(root, "add-entity", entity["id"], args.chapter, entity.get("name", ""))
    print(f"added entity {entity['id']}")


def cmd_update_entity(root, args):
    path = root / "seed_entities.json"
    doc = load(path)
    patch = parse_json_arg(args.json)
    for e in doc["entities"]:
        if e.get("id") == args.id:
            e.update(patch)
            save(path, doc)
            log_change(root, "update-entity", args.id, args.chapter,
                       "fields: " + ", ".join(patch.keys()))
            print(f"updated entity {args.id}")
            return
    sys.exit(f"not found: {args.id}")


def _target_list(root, file_arg, list_key):
    path = root / file_arg
    if not path.is_file():
        sys.exit(f"error: no such file: {path}")
    doc = load(path)
    node = doc
    for part in list_key.split("."):
        if not isinstance(node, dict) or part not in node:
            sys.exit(f"error: {file_arg} has no list '{list_key}'")
        node = node[part]
    if not isinstance(node, list):
        sys.exit(f"error: {file_arg}#{list_key} is not a list")
    return path, doc, node


def cmd_add_record(root, args):
    path, doc, records = _target_list(root, args.file, args.list)
    rec = parse_json_arg(args.json)
    rid = rec.get("id")
    if rid and any(r.get("id") == rid for r in records):
        sys.exit(f"error: id already exists in {args.file}#{args.list}: {rid}")
    if records and "id" in records[0] and not rid:
        sys.exit(f"error: records in {args.file}#{args.list} carry ids — give the new record an id")
    if args.chapter and "source" not in rec:
        rec["source"] = f"chapter:{args.chapter}"
    records.append(rec)
    save(path, doc)
    log_change(root, "add-record", f"{args.file}#{args.list}:{rid or '(no id)'}", args.chapter)
    print(f"added record to {args.file}#{args.list}")


def cmd_update_record(root, args):
    path, doc, records = _target_list(root, args.file, args.list)
    patch = parse_json_arg(args.json)
    for r in records:
        if r.get("id") == args.id:
            r.update(patch)
            save(path, doc)
            log_change(root, "update-record", f"{args.file}#{args.list}:{args.id}",
                       args.chapter, "fields: " + ", ".join(patch.keys()))
            print(f"updated {args.file}#{args.list}:{args.id}")
            return
    sys.exit(f"not found in {args.file}#{args.list}: {args.id}")


def _next_id(records, prefix):
    nums = []
    for r in records:
        m = re.fullmatch(prefix + r"_?(\d+)", str(r.get("id", "")))
        if m:
            nums.append(int(m.group(1)))
    return f"{prefix}_{(max(nums) + 1) if nums else 1:02d}"


def cmd_add_fact(root, args):
    path, doc, facts = _target_list(root, "seeds/facts.json", "facts")
    fid = args.id or _next_id(facts, "fact")
    if any(f.get("id") == fid for f in facts):
        sys.exit(f"error: fact id exists: {fid}")
    source = args.source or (f"chapter:{args.chapter}" if args.chapter else "")
    if not source:
        sys.exit("error: give --source or --chapter (facts must be source-tagged)")
    facts.append({"id": fid, "statement": args.statement, "source": source})
    save(path, doc)
    log_change(root, "add-fact", fid, args.chapter, args.statement[:60])
    print(f"added fact {fid}")


def cmd_add_relation(root, args):
    path, doc, rels = _target_list(root, "seeds/relations.json", "relations")
    rid = args.id or _next_id(rels, "rel")
    if any(r.get("id") == rid for r in rels):
        sys.exit(f"error: relation id exists: {rid} (pass --id)")
    known = all_known_ids(root)
    for endpoint in (args.from_, args.to):
        for tok in ref_tokens(endpoint):
            if tok not in known:
                print(f"warning: endpoint id not found in db: {tok}")
    rec = {"id": rid, "from": args.from_, "to": args.to,
           "type": args.type, "why_matters": args.why}
    if args.chapter:
        rec["source"] = f"chapter:{args.chapter}"
    rels.append(rec)
    save(path, doc)
    log_change(root, "add-relation", rid, args.chapter, f"{args.from_} -> {args.to}")
    print(f"added relation {rid}")


def cmd_writeback(root, args):
    """Batch write-back at chapter close. Manifest shape:
    {"entities": [...], "facts": [{statement, source?}...],
     "relations": [{from, to, type, why_matters}...],
     "records": [{"file": "seeds/x.json", "list": "key", "item": {...}}...]}
    """
    manifest = load(Path(args.manifest))
    n = 0
    for e in manifest.get("entities", []):
        ns = argparse.Namespace(json=json.dumps(e, ensure_ascii=False), id=None, name=None,
                                type=None, summary=None, why=None, chapter=args.chapter)
        cmd_add_entity(root, ns)
        n += 1
    for f in manifest.get("facts", []):
        ns = argparse.Namespace(id=f.get("id"), statement=f["statement"],
                                source=f.get("source"), chapter=args.chapter)
        cmd_add_fact(root, ns)
        n += 1
    for r in manifest.get("relations", []):
        ns = argparse.Namespace(id=r.get("id"), from_=r["from"], to=r["to"],
                                type=r.get("type", ""), why=r.get("why_matters", ""),
                                chapter=args.chapter)
        cmd_add_relation(root, ns)
        n += 1
    for rec in manifest.get("records", []):
        ns = argparse.Namespace(file=rec["file"], list=rec["list"],
                                json=json.dumps(rec["item"], ensure_ascii=False),
                                chapter=args.chapter)
        cmd_add_record(root, ns)
        n += 1
    log_change(root, "writeback", args.manifest, args.chapter, f"{n} records")
    print(f"writeback complete: {n} records from {args.manifest}")


def cmd_validate(root, args):
    errors, warnings = [], []
    try:
        ids = all_known_ids(root)
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: unparseable JSON: {e}")
    for rid, places in ids.items():
        primary = [p for p in places if p.startswith("seed_entities")]
        if len(primary) > 1:
            errors.append(f"duplicate entity id: {rid}")
    rel_path = root / "seeds" / "relations.json"
    if rel_path.is_file():
        for r in load(rel_path).get("relations", []):
            for side in ("from", "to"):
                for tok in ref_tokens(str(r.get(side, ""))):
                    if tok not in ids:
                        warnings.append(f"relation {r.get('id','?')}: dangling {side} ref '{tok}'")
    for sf in seed_files(root):
        for key, records in record_lists(load(sf)):
            with_id = [r for r in records if "id" in r]
            if with_id and len(with_id) != len(records):
                warnings.append(f"seeds/{sf.name}#{key}: {len(records)-len(with_id)} records missing id")
            seen = set()
            for r in with_id:
                if r["id"] in seen:
                    errors.append(f"seeds/{sf.name}#{key}: duplicate id {r['id']}")
                seen.add(r["id"])
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print(f"validate: {len(errors)} errors, {len(warnings)} warnings "
          f"({len(ids)} distinct record ids)")
    sys.exit(1 if errors else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, help="<STORY_ROOT> or the story_world dir")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list");   p.add_argument("--type")
    p = sub.add_parser("get");    p.add_argument("id")
    p = sub.add_parser("search"); p.add_argument("keyword"); p.add_argument("--limit", type=int, default=10)

    p = sub.add_parser("add-entity")
    p.add_argument("--json"); p.add_argument("--id"); p.add_argument("--name")
    p.add_argument("--type"); p.add_argument("--summary"); p.add_argument("--why")
    p.add_argument("--chapter")

    p = sub.add_parser("update-entity")
    p.add_argument("id"); p.add_argument("--json", required=True); p.add_argument("--chapter")

    p = sub.add_parser("add-record")
    p.add_argument("--file", required=True); p.add_argument("--list", required=True)
    p.add_argument("--json", required=True); p.add_argument("--chapter")

    p = sub.add_parser("update-record")
    p.add_argument("--file", required=True); p.add_argument("--list", required=True)
    p.add_argument("--id", required=True); p.add_argument("--json", required=True)
    p.add_argument("--chapter")

    p = sub.add_parser("add-fact")
    p.add_argument("--statement", required=True); p.add_argument("--source")
    p.add_argument("--id"); p.add_argument("--chapter")

    p = sub.add_parser("add-relation")
    p.add_argument("--from", dest="from_", required=True); p.add_argument("--to", required=True)
    p.add_argument("--type", required=True); p.add_argument("--why", required=True)
    p.add_argument("--id"); p.add_argument("--chapter")

    p = sub.add_parser("writeback")
    p.add_argument("--chapter", required=True); p.add_argument("--manifest", required=True)

    sub.add_parser("validate")

    args = ap.parse_args()
    root = resolve_root(args.root)
    {
        "list": cmd_list, "get": cmd_get, "search": cmd_search,
        "add-entity": cmd_add_entity, "update-entity": cmd_update_entity,
        "add-record": cmd_add_record, "update-record": cmd_update_record,
        "add-fact": cmd_add_fact, "add-relation": cmd_add_relation,
        "writeback": cmd_writeback, "validate": cmd_validate,
    }[args.cmd](root, args)


if __name__ == "__main__":
    main()
