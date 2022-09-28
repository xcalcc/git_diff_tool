#!/bin/bash

test_target="test_same_issue test_new_issue test_fix_issue test_move_issue"
for target in ${test_target}
do
	cd ${target} && mkdir test
	cd test  
	rm *.v code_line_match
	python3 ../../../delta_diff_m.py -g ../../${target}/git_diff_results.txt -f1 ../../${target}/baseline.view -f2 ../../${target}/previous.view

	bash ../../convert.sh -i baseline.v
	bash ../../convert.sh -i previous.v
	cd ../../
done


