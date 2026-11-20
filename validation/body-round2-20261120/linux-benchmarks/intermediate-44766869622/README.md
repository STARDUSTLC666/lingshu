# Intermediate Linux benchmark run: measurement checks pass, inventory defect

- Run: `44766869622`, repository `STARDUSTLC666/lingshu`.
- Evidence-driver metadata head: `f769b3ac33eb5221ad66f6a4384aa6429b26e597`.
- Actual measured source: `5226860c1d70bc7fc6619cf79aff10c4f9a2a234`.
- Exact baseline: `d74848fb33dbff1d719959df19d1266a1ac60f44`.

All three jobs concluded SUCCESS; all original job logs, whole-run log ZIP,
artifact ZIPs, extracted original files and API snapshots are retained. Artifact
ZIP SHA-256 values match the immutable GitHub artifact API digest.

Independent checks passed for all three artifacts: four benchmark source hashes,
all declared input Git blobs, all ten command exit codes and both stream hashes,
fixed correctness oracles and expected baseline failures, all 27 reconstructed
named-mutant source hashes, exact targeted XML assertion failures and no XML
errors/skips, and exact fixed/baseline guard counts. This is a scoped benchmark
workflow, not a complete repository/brain gate.

**Metadata defect:** each original inner `artifact-index.json` has exactly one
stale member, `driver.log`. The driver computes that inventory while the outer
shell is still teeing its output; printing the final validation summary then
changes `driver.log`. Every other listed member matches its declared length and
SHA-256. The original artifact index and original log bytes were not edited.

This run is retained as intermediate evidence. It must not be described as an
index-clean final benchmark seal. The parent task is correcting the evidence
driver and repeating the same measured source in a new run. Post-download
outer hashes are independent of this stale inner inventory entry.
