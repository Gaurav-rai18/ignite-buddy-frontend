"""`trainee-kb`: administer the knowledge base.
   trainee-kb ingest ./ignite_docs --space ignite          (pdf, pptx, docx, md, txt; incremental)
   trainee-kb ingest ./handbook.pdf --space general --reset
   trainee-kb list | delete --space general --source handbook.pdf | query "what is the leave policy"
"""
import argparse
import os
import sys

from .store import SPACES


def main(argv=None):
    ap = argparse.ArgumentParser(prog="trainee-kb")
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("ingest"); i.add_argument("path"); i.add_argument("--space", choices=SPACES, required=True)
    i.add_argument("--reset", action="store_true", help="delete everything in the space first")
    sub.add_parser("list")
    d = sub.add_parser("delete"); d.add_argument("--space", choices=SPACES, required=True); d.add_argument("--source", required=True)
    q = sub.add_parser("query"); q.add_argument("text"); q.add_argument("--space", choices=SPACES)
    a = ap.parse_args(argv)

    from .store import get_kb
    kb = get_kb()
    if a.cmd == "ingest":
        from .ingest import ingest_path
        if not os.path.exists(a.path):
            sys.exit(f"{a.path} does not exist")
        r = ingest_path(kb, a.space, a.path, a.reset)
        print(f"\n{r['files']} files, {r['chunks']} chunks, {len(r['skipped'])} unsupported skipped, {len(r['errors'])} errors")
    elif a.cmd == "list":
        for sp, st in kb.stats().items():
            print(f"[{sp}] {st['chunks']} chunks")
            for s in st["sources"]:
                print(f"   {s}")
    elif a.cmd == "delete":
        kb.delete_source(a.space, a.source)
        print("deleted")
    else:
        for sp in ([a.space] if a.space else SPACES):
            for h in kb.query(sp, a.text, 5):
                print(f"[{sp}] {h.score:.2f}  {h.source} p.{h.page}: {h.text[:120]}")


if __name__ == "__main__":
    main()
