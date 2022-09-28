#!/bin/bash

SHELL_PATH=`realpath $0`
SHELL_DIR=`dirname ${SHELL_PATH}`
SIMP_PATH=${SHELL_DIR}/simpv
CONVERT_TOOL=${SHELL_DIR}/json_to_ascii.py
CURRENT_PATH=`pwd`

if [ $# -eq 0 ] || [ $# -ge 3 ]; then
	echo "convert.sh usage:  convert.sh <-i> json.v"
	echo "when add -i option, script will ignore deduplicate process, convert orignal JSON file to ASCII"
	exit 1
fi

# When no -i option, script will deduplicate JSON file , and then convert it to ASCII file
if [ $# -eq 1 ]; then
	TARGET_FILE=`basename $1`
	
	if [ -f ${SIMP_PATH} ] && [ -f ${CONVERT_TOOL} ]; then
		if [ -f $1 ]; then
			python3 ${SIMP_PATH} $1
			if [ -f deduplicate_${TARGET_FILE} ]; then
				python3 ${CONVERT_TOOL} deduplicate_${TARGET_FILE}
				if [ "$?" -eq 0 ]; then
					echo " "
					echo "Convert JSON file to ASCII file successfully under the path: ${CURRENT_PATH}"
					echo " "
				else
					echo " "
					echo "Convert JSON file to ASCII file failed, please check [json_to_ascii.py]"
					echo " "
				fi
			else
				echo " "
				echo "There has no generate deduplicate v file, please check [XVSA scan results] or [deduplicate_${TARGET_FILE} file]"
				echo " "
			fi
		else
			echo " "
			echo "There has no JSON file as input to deduplicate script, please input JSON file."
		fi
	else
		echo " "
		echo "There has no python script [simpv], please check it."
		echo " "
	fi
fi	


# With -i option, script will ignore deduplicate process, convert original JSON file to ASCII file.
if [ $# -eq 2 ]; then
	
	case $1 in
		-i)	
			TARGET_NAME=`basename $2`
			TARGET_NAME="${TARGET_NAME%.*}"
			cp $2 ${TARGET_NAME}-original.v
			TARGET_FILE=${TARGET_NAME}-original.v
			;;
		*)
			if [ "$2" = "-i" ]; then
				TARGET_NAME=`basename $1`
				TARGET_NAME="${TARGET_NAME%.*}"
				cp $1 ${TARGET_NAME}-original.v
				TARGET_FILE=${TARGET_NAME}-original.v
			else
				echo "Please input the right option [-i]"
				exit
			fi
			;;
	esac	

    if [ -f ${CONVERT_TOOL} ]; then
        if [ -f ${TARGET_FILE} ]; then
            python3 ${CONVERT_TOOL} ${TARGET_FILE}
            if [ "$?" -eq 0 ]; then
                echo " "
                echo "Convert original JSON file to ASCII file successfully under the path: ${CURRENT_PATH}"
                echo " "
            else
                echo " "
                echo "Convert JSON file to ASCII file failed, please check [json_to_ascii.py]"
                echo " "
            fi
			rm ${TARGET_FILE}
        else
            echo " "
            echo "There has no JSON file as input to deduplicate script, please input JSON file."
        fi
    else
        echo " "
        echo "There has no python script [${CONVERT_TOOL}], please check it."
        echo " "
    fi
 
fi
