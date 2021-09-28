#!/bin/bash
(cd ../../; python2 ./generator.pyc hs_climate_analysis utf-8)
markdown2 --extras tables,fenced-code-blocks,strike,target-blank-links doc/log14186.md > release/log14186.html
(cd release; zip -r 14186_hs_climate_analysis.hslz *)
