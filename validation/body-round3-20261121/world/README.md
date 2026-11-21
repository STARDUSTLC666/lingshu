# World command reanchor public evidence slice

Final production head: `bd208a379e44497e9f35fdc145838abb19e6d313` (PR #1482).
The final implementation uses unrounded endpoint displacement for directional
commands and zero physical velocity for explicit stay. `intermediate/` is the
superseded attempt that used the rounded public velocity. Its original oracle
shared that assumption and is not final correctness proof.

`public-index.json` binds every retained file to its original and public byte
length/SHA256, states projections, and records verification checks. It does not
index itself or this explanatory README to avoid self-reference. JSON redaction
changes string tokens only, including dictionary keys, and checks identical
non-string tokens. Explicit metadata projections preserve retained numeric
values exactly with Decimal parsing. XML structure, text after path redaction,
and numeric attributes are verified after serialization.

Absolute paths become `<repo>`, `<audit-evidence>`, `<validation-venv>`,
`<no-contact-repo>`, `<user-home>` and related placeholders. Helpers are retained
for audit and can be rerun with explicit source/repository/output arguments;
standalone probe path placeholders must be configured for the target checkout.
No brain/baseline source tree, archive, database, cache, complete third-party
production snapshot, aggregate issue dump, or third-party issue/comment body is
included. Dedup evidence contains selected metadata, URLs, counts and body hashes.
The separate environment-change hypothesis is withheld from this command fix.

The full Windows gate is included only after its process has ended. Its code
input was frozen at 6d1048f6; the subsequent bd208a commit added two documentation
files. The original end-of-run head and any source-drift observations remain
unchanged; this slice does not relabel an entire-tree change as identical source.
The original Windows run has one failed pre-existing symlink-capability
assertion: this Windows host can create a real symlink, while that guard assumes
success implies POSIX. The unchanged test hash and independent capability probe
are retained. Original exit codes and failure/skip counts are not rewritten.
