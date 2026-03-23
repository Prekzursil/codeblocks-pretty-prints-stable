# Profile seed template

This directory is expected to contain the curated Code::Blocks profile seed
produced by the overlay/migration lane.

The installer skeleton expects the seed to be normalized for the edition-owned
install path and to carry only the intentional settings we want to preserve.

Typical seed inputs from the current good profile:

- `default.conf`
- `default.cbKeyBinder20.conf`
- `codesnippets.ini`
- optional editor/tweak files that remain stable across installs

The install-time normalization step should rewrite any old install root
references to the final edition-owned path.


