# Current-head append publication audit

PASS. Independently checked 1636 manifested artifacts plus three detached metadata files, exact canonical blob coverage/hashes, JSON/XML parsing and private prefixes; 315 XML runs have matching JUnit index.

New PR1478 CI: 3 successful gate legs, each 5638 passed / 40 skipped / 98 subtests; 102 actual script groups and actual brain 23/23, plus title success. Raw job logs match original indexed ZIP entries; saved API job/run identities and workflow script source agree. Actual CI checkout was GitHub merge commit `6cfd83024a94b93bad714ca670c6921d8bc73866`; independently queried commit API confirms its tree equals current `41dc5e01fd710ffeab79aa4d566d8ed5ed5baf50` exactly.

Measured `bae2eaea9fb77e9e451f1b220d17f9096d06ee78` / historical `89c005b7fdd48f64c603d34c280a4d18a93956f7` evidence remains historical; new current core matches frozen combined source `5226860c1d70bc7fc6619cf79aff10c4f9a2a234`. Only search_skills AST changes during the merge; fresh-decay functions remain unchanged. Windows gate remains false with the original known failure. The helper was code-reviewed for repeat stability and not rerun.
