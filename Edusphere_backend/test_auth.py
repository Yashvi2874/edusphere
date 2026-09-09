"""
Password handling tests.

Run:  python test_auth.py

These check the properties that matter rather than the implementation: that a
stored password is never the password, that the right one works and the wrong
one does not, and that accounts created before hashing existed still work and
convert themselves on the next login.
"""
import json
import shutil
import tempfile
from pathlib import Path

from database import Database, hash_password, is_hashed, verify_password

passed = failed = 0


def check(condition, label, detail=""):
    global passed, failed
    print(("  PASS  " if condition else "  FAIL  ") + label + (("  - " + detail) if detail else ""))
    if condition:
        passed += 1
    else:
        failed += 1


tmp = tempfile.mkdtemp()
try:
    db = Database(db_path=tmp)
    users_file = Path(tmp) / "users.json"

    # --- hashing primitives ---
    h = hash_password("CorrectHorse123")
    check(h != "CorrectHorse123", "hash is not the password itself")
    check(is_hashed(h), "hash is recognisable as bcrypt", h[:7] + "...")
    check(verify_password("CorrectHorse123", h), "correct password verifies")
    check(not verify_password("wrong", h), "wrong password rejected")
    check(hash_password("same") != hash_password("same"),
          "same password hashes differently each time (salted)")

    # --- signup stores a hash, never the password ---
    db.create_user_with_auth("a@example.com", "Sup3rSecret!", "A")
    stored = json.loads(users_file.read_text(encoding="utf-8"))
    rec = [u for u in stored.values() if u.get("email") == "a@example.com"][0]
    check(rec["password"] != "Sup3rSecret!", "signup does not store the password")
    check(is_hashed(rec["password"]), "signup stores a bcrypt hash")
    check("Sup3rSecret!" not in users_file.read_text(encoding="utf-8"),
          "the password appears nowhere in users.json")

    # --- login ---
    check(db.authenticate_user("a@example.com", "Sup3rSecret!")["success"],
          "correct login succeeds")
    check(not db.authenticate_user("a@example.com", "nope")["success"],
          "wrong password fails")
    check(not db.authenticate_user("nobody@example.com", "Sup3rSecret!")["success"],
          "unknown email fails")

    # --- legacy plain-text account still works, and upgrades itself ---
    users = json.loads(users_file.read_text(encoding="utf-8"))
    users["legacy_user"] = {
        "email": "old@example.com",
        "password": "PlainTextOldPassword",   # as stored before hashing existed
        "name": "Old",
    }
    users_file.write_text(json.dumps(users), encoding="utf-8")

    check(db.authenticate_user("old@example.com", "PlainTextOldPassword")["success"],
          "legacy plain-text account can still log in")
    after = json.loads(users_file.read_text(encoding="utf-8"))["legacy_user"]["password"]
    check(is_hashed(after), "legacy password is upgraded to a hash on login")
    check(db.authenticate_user("old@example.com", "PlainTextOldPassword")["success"],
          "upgraded account still logs in afterwards")
    check(not db.authenticate_user("old@example.com", "PlainTextOldPasswor")["success"],
          "upgraded account rejects a near-miss password")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("\n" + str(passed) + " passed, " + str(failed) + " failed")
raise SystemExit(1 if failed else 0)
