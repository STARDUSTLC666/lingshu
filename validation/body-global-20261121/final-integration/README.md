# Final integration freeze

Head: 0f7427549406ad125d7efc95da5ceece052e616d
Tree: 0f33bd5642db088a459aebd6750cc1c68715f10e
Branch: validation/global-final-20261121

This new checkout starts from the clean total13 guard commit513ce31 and merges
the existing perception#1433, controlled noise#1431 and extended acceptance
workflow histories. It preserves main23ba01e, repaired odd-r CNN, and the shared
M5.5 partition implementation. Production module count remains95.

Final acceptance: **165 passed /0 skipped /0 failed**,32.19seconds. Canonical
pixel→classification→World3D→core memory now reports color4/4 and object4/4;
clean0/4 divergence and degraded7/8 divergence. All existing domain guards were
retained. Strict manifest64/64; time lint23registered/0new/0stale.

Prior acceptance.xml failed during collection because original noise guard used
a cwd namespace import after product pathguard initialization. The same failure
was reproduced with explicit PYTHONPATH. The standalone existing#1431 integration
replaced only the test loader and corresponding mutant module alias with an
explicit canonical benchmark file load. Benchmark and four assertions remain
unchanged. Pixel-first/noise collection passed after the correction. Original
failed reports are retained and not counted as final passes.

This is synthetic RGB recognition and controlled oracle-derived noise acceptance.
It does not prove real-camera multi-object accuracy. Parent supervises complete
Linux/Windows gates, installed-wheel and real brain validation on this frozen head.
No source changes after freeze; no remote writes by this child.
