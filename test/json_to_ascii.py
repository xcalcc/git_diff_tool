#!/usr/bin/env python3

import json
import re
import sys
import os

inputfile   = sys.argv[1]
current_dir = os.getcwd()
inputname   = os.path.basename(inputfile)
inputname   = re.sub('\.v', '', inputname)
inputname   = re.sub('deduplicate_', '',inputname)
outputfile  = "%s/%s-simp.v" % (current_dir, inputname)

def convert():
    with open(inputfile, "r") as input_file:
        input_file_data = json.load(input_file)

        fid_path = {}
        for fp in input_file_data["files"]:
            fid_path[fp["fid"]] = fp["path"]

        for key in input_file_data["issues"]:
            # file_name_match = re.sub(r'@.*', '', key["k"])
            # if file_name_match is not None:
            #     file_name = file_name_match

            fid       = key["fid"]
            if fid in fid_path.keys():
                file_name = fid_path[fid]

            sln       = key["sln"]
            fid_sln   = [str(fid), str(sln)]
            fid_sln   = ':'.join(fid_sln)

            certainly = key["c"]
            rc        = key["rc"]
            vn        = key["vn"]
            fn        = key["fn"]

            RBC_check = re.search(r'CERT', key["k"])

            issue_path = []
            for key_path in key["paths"]:
                issue_fid = key_path["fid"]
                issue_sln = key_path["sln"]
                issue_scn = key_path["scn"]

                path = [str(issue_fid), str(issue_sln), str(issue_scn)]
                path = ':'.join(path)

                issue_path.append(path)

            if RBC_check is not None:
                output_data = "[%s],[%s],[Vul],[%s],[RBC],[1,0,0],[CERT],[%s],[%s],[%s],%s" \
                              % (file_name, fid_sln, certainly, rc, vn, fn, issue_path)
            else:
                output_data = "[%s],[%s],[Vul],[%s],[%s],[1,0,0],[%s],[%s],%s" \
                              % (file_name, fid_sln, certainly, rc, vn, fn, issue_path)
            output_file.write(output_data+'\n')

if __name__ == "__main__":
    output_file = open(outputfile, 'w')
    convert()
    output_file.close()