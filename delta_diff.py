#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
import sys
import time
import json
import copy
import re


# This function is used for dealing with Changes to the line number caused by the modification of the source file.
def line_change_check(line_change, symbol, line_change_check, line_change_list):
    if line_change_check is None:
        new_change_line = re.search(r'{0}(\d+)\,(\d+)'.format(symbol), line_change)
        if new_change_line is not None:
            sln = int(new_change_line.group(1))
            ln_change = int(new_change_line.group(2))
            for i in range(ln_change):
                line_change_list.append(sln + i)
        else:
            new_change_line = re.search(r'{0}(\d+)'.format(symbol), line_change)
            if new_change_line is not None:
                sln = int(new_change_line.group(1))
                line_change_list.append(sln)
            ln_change = 1
    else:
        new_change_line = re.search(r'{0}(\d+)\,0'.format(symbol), line_change)
        if new_change_line is not None:
            sln = int(new_change_line.group(1))
        ln_change = 0

    return ln_change, sln, line_change_list

# This function is used for calculate line number change when source code changed based on git diff results.
def line_no_calculate(content, tln, new_line_match, change_file,
                      count_add, count_reduce, new_line_change, old_line_change):
    # This cover code line match , will calculate line number after code modify.
    line_change = re.search(r'@@ (\-.*) (\+.*) @@', content)
    if line_change is not None:
        new_line_change_check = re.search(r',0', line_change.group(2))
        old_line_change_check = re.search(r',0', line_change.group(1))

        new_change, new_sln, new_line_change = line_change_check(line_change.group(2), '\+',
                                                                 new_line_change_check, new_line_change)
        old_change, old_sln, old_line_change = line_change_check(line_change.group(1), '\-',
                                                                 old_line_change_check, old_line_change)

        # judge add line or delete line and calculate line number
        if new_change > old_change:
            count_add += (int(new_change) - int(old_change))
        if new_change < old_change:
            count_reduce += (int(old_change) - int(new_change))

        if tln:
            if count_add > 0:
                for i in range(new_sln, tln + 1):
                    new_line_match['%s' % change_file][i] = i - count_add
            if count_reduce > 0:
                for i in range(old_sln, tln + 1):
                    new_line_match['%s' % change_file][i] = i + count_reduce

    return new_line_match, new_line_change, count_add, count_reduce

# source file and line number match. return a dict of new source code line number map to old source code line number.
# This function just be used in product flow , for inner flow it's not need
def code_map(git_diff_result, new_v):
    try:
        if os.path.exists(git_diff_result):
            with open(git_diff_result, 'r') as git_diff_read:
                git_diff_content = git_diff_read.readlines()
    except IOError as error:
        print('Read git_diff_results.txt failed, please check this file.')
        sys.exit()

    with open(new_v, "r") as new_v_file:
        new_v_data = json.load(new_v_file)

    # length of git_diff_results.txt
    new_line_match   = {}
    change_file_list = []
    add_file_list    = []
    reduce_file_list = []
    new_line_change = []
    old_line_change = []

    # This loop be used read git_diff_results.txt and output code_line_match.
    count_add = 0
    count_reduce = 0
    for line_no,content in enumerate(git_diff_content):
        git_diff_diff = re.search(r'diff --git (.*)', content)
        if git_diff_diff is not None:
            git_diff_reduce = re.search(r'^a/(.*) (.*)', git_diff_diff.group(1))
            git_diff_add = re.search(r'^b/(.*)', git_diff_reduce.group(2))

            # count total line number of diff source file
            # "tln" is total line number
            # in git diff results, it use "/dev/null" as a mark when add or delete file.
            # This cover delete file in this git push
            git_diff_null = "\/dev\/null"
            if git_diff_reduce is not None:
                git_diff_reduce_file = re.sub(r'^a/', "", git_diff_reduce.group(1))
                tln=None
                if git_diff_null in git_diff_reduce.group(1):
                    new_file = re.sub(r'^b/', "", git_diff_add.group(1))
                    add_file_list.append(new_file)

            # This cover add new file in this git push
            if git_diff_add is not None:
                git_diff_add_file = re.sub(r'^b/', "", git_diff_add.group(1))
                tln=None
                if git_diff_null in git_diff_add.group(1):
                    reduce_file = re.sub(r'^a/', "", git_diff_reduce.group(1))
                    reduce_file_list.append(reduce_file)

            # This cover modify file in this git push
            if git_diff_add_file == git_diff_reduce_file:
                change_file = git_diff_add_file
                change_file_list.append(change_file)
                new_line_match['%s' % change_file] = {}

                for i in new_v_data["issues"]:
                    for k in i["issueTraceInfos"]:
                        for j in k["issueTraces"]:
                            if j["scanFilePath"]:
                                if git_diff_add_file in j["scanFilePath"]:
                                    tln = j["scanFileNoOfLines"]
                            else:
                                tln=None

        new_line_match, new_line_change, \
        count_add, count_reduce = line_no_calculate(content, tln, new_line_match, change_file, count_add, count_reduce,
                                                    new_line_change, old_line_change)
    # delete the change line number from all line number. just display match line.
    for f in change_file_list:
        for k in new_line_change:
            if k in new_line_match[f].keys():
                new_line_match[f].pop(k)

    # write code line match results to a file ,as function json_map input.
    with open('code_line_match', 'w') as f:
        f.write(str(new_line_match))

# This function is used for convert view data to core v format .
def view_to_v(old_v_data, target):
    files = []
    issues = []
    tmp_files = []
    for issue_k in old_v_data["issues"]:
        for f in issue_k["issueTraceInfos"]:
            for p in f["issueTraces"]:
                if p["relativePath"]:
                    if p["relativePath"] not in tmp_files:
                        tmp_files.append(p["relativePath"])
                else:
                    if "null" not in tmp_files:
                        tmp_files.append("null")

    for i in range(len(tmp_files)):
        f_fid = {}
        f_fid["fid"]  = i+1
        f_fid["path"] = tmp_files[i]
        files.append(f_fid)

    for issue_k in old_v_data["issues"]:
        issue = {}
        for f_name in files:
            if issue_k["relativePath"]:
                if issue_k["relativePath"] in f_name["path"]:
                    issue["fid"] = f_name["fid"]
            else:
                for tmp_f_name in files:
                    if tmp_f_name["path"] == "null":
                        issue["fid"] = tmp_f_name["fid"]
        issue["k"]   = issue_k["issueKey"]
        issue["sln"] = issue_k["lineNo"]
        issue["scn"] = issue_k["columnNo"]
        issue["rs"]  = issue_k["ruleSet"]
        issue["rc"]  = issue_k["vulnerable"]
        issue["ec"]  = issue_k["checksum"]
        issue["c"]   = issue_k["certainty"]
        issue["ic"]  = issue_k["complexity"]
        issue["vn"]  = issue_k["variableName"]
        issue["fn"]  = issue_k["functionName"]
        issue["m"]   = issue_k["message"]
        issue["id"]  = issue_k["id"]

        issue_path = {}
        for f in issue_k["issueTraceInfos"]:
            paths = []
            for p in f["issueTraces"]:
                for f_name in files:
                    if p["relativePath"] and f_name["path"]:
                        if p["relativePath"] in f_name["path"]:
                            issue_path["fid"] = f_name["fid"]
                issue_path["sln"] = p["lineNo"]
                issue_path["scn"] = p["columnNo"]
                issue_path["m"]   = p["message"]
                issue_path["vn"]  = p["variableName"]
                issue_path["fn"]  = p["functionName"]
                issue_path["id"]  = p["id"]
                issue_path["checksum"] = p["checksum"]

                paths.append(copy.deepcopy(issue_path))
            issue["paths"] = copy.deepcopy(paths)
            issues.append(copy.deepcopy(issue))

    # write data to baseline.v
    target_data = {
        "files": files,
        "issues": issues,
        "rulesets": [{"rs":"BUILTIN", "rv":"1"}, {"rs":"CERT", "rv":"1"}],
        "v": 1,
        "id":"@@scanTaskId@@",
        "s":"@@status@@",
        "m":"@@message@@",
        "eng":"Xcalibyte",
        "ev":"1",
        "er":"b4084f1ce6fd0a66187e7113d828d0c89f07f15e(develop)",
        "x1":"yv#@EHZ*qhlm.8#@GZIT*zyr.m35#@EHZ*zfgsvm.8#@EHZ*xvigx.8#@EHZ*avil_tolyzo.9#cehz@cuz@wfnnb~x",
        "x2":"SLNV,FHVI.cx4",
        "ss": 1588221147214383,
        "se": 1588221147265190,
        "usr": 56000,
        "sys": 0,
        "rss": 44084
    }

    v_format = json.dumps(target_data, indent=1)
    with open("{0}".format(target), 'w') as v_target:
        v_target.write(v_format)
    #return target


# This function is used to convert json file from MW to json format follow core format.
# This function just be used in product flow , for inner flow it's not need
def json_convert(old_v, new_v):
    # This logic is used to read baseline.view and convert it to baseline.v
    with open(old_v, "r") as old_v_file:
        old_v_data = json.load(old_v_file)

    view_to_v(old_v_data, 'baseline.v')

    # convert previous.view to previous.v
    with open(new_v, "r") as new_v_file:
        new_v_data = json.load(new_v_file)

    view_to_v(new_v_data, 'previous.v')

# This function is used for map fid to file name to avoid fid change in different scan results.
def fid_name_map(v_issues, v_files):
    for issue in v_issues:
        if "fid" in issue.keys():
            for fid_path in v_files:
                if fid_path["fid"] == issue["fid"]:
                    issue["fid"] = fid_path["path"]
                for issue_fid in issue["paths"]:
                    if fid_path["fid"] == issue_fid["fid"]:
                        issue_fid["fid"] = fid_path["path"]
    return v_issues

# This function is used for diff results based on code line match results.
def issue_map_diff(diff_issue, line_match_results):
    tmp_list = copy.deepcopy(diff_issue)
    if 'k' in tmp_list.keys():
        tmp_list.pop('k')
    if 'id' in tmp_list.keys():
        tmp_list.pop('id')
    if 'ic' in tmp_list.keys():
        tmp_list.pop('ic')
    for t_list in tmp_list['paths']:
        if 'id' in t_list.keys():
            t_list.pop('id')
        if 'checksum' in t_list.keys():
            t_list.pop('checksum')
    # judge file whether need be matched , recursive match all sln which need be matched .
    for file_key in line_match_results.keys():
        if tmp_list["fid"].find(file_key) != -1:
            if tmp_list["sln"] in line_match_results[file_key].keys():
                tmp_list["sln"] = line_match_results[file_key][tmp_list["sln"]]
    for diff_path in tmp_list["paths"]:
        for file_key in line_match_results.keys():
            if diff_path["fid"].find(file_key) != -1:
                if diff_path["sln"] in line_match_results[file_key].keys():
                    diff_path["sln"] = line_match_results[file_key][diff_path["sln"]]
    return tmp_list

# This function is used for delete "k", "id" , "checksum" avoid impact diff flow.
def value_pop(v_issues):
    for old_issue in v_issues:
        if 'k' in old_issue.keys():
            old_issue.pop('k')
        if 'id' in old_issue.keys():
            old_issue.pop('id')
        if 'ic' in old_issue.keys():
            old_issue.pop('ic')
        for o_issue in old_issue["paths"]:
            if 'id' in o_issue.keys():
                o_issue.pop('id')
            if 'checksum' in o_issue.keys():
                o_issue.pop('checksum')

# This function is used for write diff results to json format file, to add_results.v/same_results.v/reduce_results.v
def v_write(target_name, v_files, results, new_v_rulesets, new_v_v, new_v_id, new_v_s, new_v_m, new_v_eng,
            new_v_ev, new_v_er, new_v_x1, new_v_x2, new_v_ss, new_v_se, new_v_usr, new_v_sys, new_v_rss):
    # revert file name to fid for producing normal .v file
    for issue in results:
        if "fid" in issue.keys():
            for fid_path in v_files:
                if fid_path["path"] == issue["fid"]:
                    issue["fid"] = fid_path["fid"]
                for issue_fid in issue["paths"]:
                    if fid_path["path"] == issue_fid["fid"]:
                        issue_fid["fid"] = fid_path["fid"]

    results_dict = {
        "files": v_files,
        "issues": results,
        "rulesets": new_v_rulesets,
        "v": new_v_v,
        "id": new_v_id,
        "s": new_v_s,
        "m": new_v_m,
        "eng": new_v_eng,
        "ev": new_v_ev,
        "er": new_v_er,
        "x1": new_v_x1,
        "x2": new_v_x2,
        "ss": new_v_ss,
        "se": new_v_se,
        "usr": new_v_usr,
        "sys": new_v_sys,
        "rss": new_v_rss
    }

    json_format = json.dumps(results_dict, indent=1)
    with open('{0}'.format(target_name), 'w') as json_target:
        json_target.write(json_format)

# json results map and diff.
def json_map(old_v, new_v, match):
    # read code line match file as new_line_match
    #with open(match, "r") as match_file:
    # new_line_match = json.load(match_file)
    with open(match, 'r') as match_file:
        new_line_match = eval(match_file.read())

    # old .v json results load as diff baseline
    with open(old_v, "r") as old_v_file:
        old_v_data = json.load(old_v_file)

    old_v_files    = copy.deepcopy(old_v_data["files"])
    old_v_issues   = copy.deepcopy(old_v_data["issues"])

    # new .v json results load as diff baseline and write the data to diff results(three json files.)
    with open(new_v, "r") as new_v_file:
        new_v_data = json.load(new_v_file)

    new_v_files    = copy.deepcopy(new_v_data["files"])
    new_v_issues   = copy.deepcopy(new_v_data["issues"])
    new_v_rulesets = copy.deepcopy(new_v_data["rulesets"])
    new_v_v        = copy.deepcopy(new_v_data["v"])
    new_v_id       = copy.deepcopy(new_v_data["id"])
    new_v_s        = copy.deepcopy(new_v_data["s"])
    new_v_m        = copy.deepcopy(new_v_data["m"])
    new_v_eng      = copy.deepcopy(new_v_data["eng"])
    new_v_ev       = copy.deepcopy(new_v_data["ev"])
    new_v_er       = copy.deepcopy(new_v_data["er"])
    new_v_x1       = copy.deepcopy(new_v_data["x1"])
    new_v_x2       = copy.deepcopy(new_v_data["x2"])
    new_v_ss       = copy.deepcopy(new_v_data["ss"])
    new_v_se       = copy.deepcopy(new_v_data["se"])
    new_v_usr      = copy.deepcopy(new_v_data["usr"])
    new_v_sys      = copy.deepcopy(new_v_data["sys"])
    new_v_rss      = copy.deepcopy(new_v_data["rss"])

    # add_files    = []  # This list store the add fid & path that only in new results , it will be diff further.
    # reduce_files = []  # This list store the reduce fid & path that only in new results , it will be diff further.
    diff_new_issue = []  # This list store the different issues from new results , it will be diff further.
    diff_old_issue = []  # This list store the different issues from old results , it will be diff further.

    same_result    = []  # This list store the same issues, and will be write to same results Json file.
    add_results    = []  # This list store the add issues, and will be write to different results Json file.
    reduce_results = []  # This list store the reduce issues, and will be write to different results Json file.

    ### 1. simple json diff, get the same issues.
    ### fid diff will be used add/delete file when commit to git repo.
    # diff new with old, get same & add results.
    # map fid to file name to avoid file name and fid mismatch scenarios.
    # add this fid & file name match can reduce the function that check add_file_list & reduce_file_list.
    new_v_issues = fid_name_map(new_v_issues, new_v_files)
    old_v_issues = fid_name_map(old_v_issues, old_v_files)

    for new_issue in new_v_issues:
        if new_issue in old_v_issues:
            same_result.append(new_issue)
        else:
            diff_new_issue.append(new_issue)

    for old_issue in old_v_issues:
        if old_issue not in new_v_issues:
            diff_old_issue.append(old_issue)

    same_results    = copy.deepcopy(same_result)
    diff_new_issues = copy.deepcopy(diff_new_issue)
    diff_old_issues = copy.deepcopy(diff_old_issue)

    # call function to delete "k", "id" "checksum" in v file which will not need in diff flow.
    value_pop(new_v_issues)
    value_pop(old_v_issues)

    print(new_line_match)
    ### 2. map resuts and diff them further.
    ### if diff_files is empty, it need not map & diff fid, just need map & diff line number and other 'k,vn,fn' value.
    # diff & map new with old , get the same & add results.
    if len(diff_new_issues) !=0 and len(diff_old_issues) != 0:
        for diff_issue in diff_new_issues:
            tmp_list = issue_map_diff(diff_issue, new_line_match)
            if tmp_list in old_v_issues:
                same_results.append(diff_issue)
            else:
                add_results.append(diff_issue)

        # diff & map old with new , get the same & reduce results.
        # reverse new_line_match to get the dict of old line number match to new line number results.
        old_line_match = {}
        for f in new_line_match.keys():
            old_line_match[f] = dict(zip(new_line_match[f].values(), new_line_match[f].keys()))
        for diff_issue in diff_old_issues:
            tmp_list = issue_map_diff(diff_issue, old_line_match)
            if tmp_list not in new_v_issues:
                reduce_results.append(diff_issue)

    if len(diff_new_issues) == 0 and len(diff_old_issues) != 0:
        reduce_results = diff_old_issues

    if len(diff_old_issues) == 0 and len(diff_new_issues) != 0:
        add_results = diff_new_issues

    ### 3. write the same & diff results to json file.
    if same_results:
        # revert file name to fid for producing normal .v file
        v_write('same_results.v', new_v_files, same_results, new_v_rulesets, new_v_v, new_v_id, new_v_s, new_v_m,
                new_v_eng, new_v_ev, new_v_er, new_v_x1, new_v_x2, new_v_ss, new_v_se, new_v_usr, new_v_sys,new_v_rss)

    if add_results:
        # revert file name to fid for producing normal .v file
        v_write('add_results.v', new_v_files, add_results, new_v_rulesets, new_v_v, new_v_id, new_v_s, new_v_m,
                new_v_eng,new_v_ev, new_v_er, new_v_x1, new_v_x2, new_v_ss, new_v_se, new_v_usr, new_v_sys, new_v_rss)

    if reduce_results:
        # revert file name to fid for producing normal .v file
        v_write('reduce_results.v', old_v_files, reduce_results, new_v_rulesets, new_v_v, new_v_id, new_v_s, new_v_m,
                new_v_eng, new_v_ev, new_v_er, new_v_x1, new_v_x2, new_v_ss, new_v_se, new_v_usr, new_v_sys, new_v_rss)

    return same_results

# This function is used when count issueKey in new/fixed issues .Just count the issuekey appear add/reduce v files.
def issueKey_list(result, same_results):
    # k_list = {}
    group_list = []
    path_list = []
    tmp_value = {}
    all_issueKey = []
    group_issueKey = []

    if same_results:
        for s_result in same_results:
            all_issueKey.append(s_result["k"])
            if s_result["k"] not in group_issueKey:
                group_issueKey.append(s_result["k"])

    #if all_issueKey:
    for k in result["issues"]:
        all_issueKey.append(k["k"])
        if k["k"] not in group_issueKey:
            group_issueKey.append(k["k"])
            tmp_value["issueKey"] = k["k"]
            if 'id' in k.keys():
                tmp_value["id"] = k["id"]
            group_list.append(copy.deepcopy(tmp_value))

    for k in result["issues"]:
        if all_issueKey.count(k["k"]) > 1:
            if 'checksum' in k["paths"][0].keys():
                tmp_value["checksum"] = k["paths"][0]["checksum"]
            tmp_value["issueKey"] = k["k"]
            if 'id' in k.keys():
                tmp_value["id"] = k["id"]
            path_list.append(copy.deepcopy(tmp_value))

    # k_list["values"] = list
    return group_list, path_list

# count "k" & number of it in add & reduce results .v file
def issueKey_count(same_results):
    # Just one "k" only appear in add_results.v ,it's a new issue.
    # Just one "k" only appear in reduce_results.v , it's a fixed issue.
    add_group_list = []
    add_path_list  = []
    reduce_group_list = []
    reduce_path_list  = []
    if os.path.isfile("add_results.v"):
        with open("add_results.v", "r") as add_file:
            add_result = json.load(add_file)
        # call function issueKey_list() to count "issueKey" in new issues.
        add_group_list, add_path_list = issueKey_list(add_result, same_results)

    if os.path.isfile("reduce_results.v"):
        with open("reduce_results.v", "r") as reduce_file:
            reduce_result = json.load(reduce_file)
        # call function issueKey_list() to count "issueKey" in reduce issues.
        reduce_group_list, reduce_path_list = issueKey_list(reduce_result, same_results)

    if add_group_list:
        print("New issue Group: %s" % len(add_group_list))
        for i in add_group_list:
            print("    issueKey: %s" % i['issueKey'])
            if 'id' in i.keys():
                print("    id: %s" % i['id'])

    if add_path_list:
        print("New issue Path: %s" % len(add_path_list))
        for i in add_path_list:
            print("    issueKey: %s" % i['issueKey'])
            if 'id' in i.keys():
                print("    id: %s" % i['id'])
            if 'checksum' in i.keys():
                print("    checksum: %s" % i["checksum"])

    if reduce_group_list:
        print("Fixed issue Group: %s" % len(reduce_group_list))
        for i in reduce_group_list:
            print("    issueKey: %s" % i['issueKey'])
            if 'id' in i.keys():
                print("    id: %s" % i['id'])

    if reduce_path_list:
        print("Fixed issue Path: %s" % len(reduce_path_list))
        for i in reduce_path_list:
            print("    issueKey: %s" % i['issueKey'])
            if 'id' in i.keys():
                print("    id: %s" % i['id'])
            if 'checksum' in i.keys():
                print("    checksum: %s" % i["checksum"])


if __name__ == "__main__":
    my_parser = argparse.ArgumentParser(description="Specify code line match file & old/new scan results !!!")
    my_parser.add_argument('-g',  action='store', dest='git_diff_result')
    my_parser.add_argument('-m',  action='store', dest='match')
    my_parser.add_argument('-f1', action='store', dest='old_v', required=True)
    my_parser.add_argument('-f2', action='store', dest='new_v', required=True)

    my_parser.add_argument('-d', '--debug', dest = 'debug', action = 'store_true', help = 'debug mode')

    give_args = my_parser.parse_args()
    old_v     = give_args.old_v
    new_v     = give_args.new_v
    match     = give_args.match
    git_diff_result = give_args.git_diff_result

    # This condition be used in inner Gerrit+Jenkins flow.
    # This function input is code_line_match.
    if match and git_diff_result is None:
        same_results = json_map(old_v, new_v, match)
        issueKey_count(same_results)

    # This condition be used in product flow.
    # This function input is git_diff_results.txt
    if git_diff_result and match is None:
        # 1. call function to read git_diff_results.txt and output code line match results to code_line_match
        code_map(git_diff_result, new_v)

        # 2. call function to read MW json file ,convert them to the same format with core json format
        match = os.path.abspath('code_line_match')
        json_convert(old_v, new_v)

        # 3. input code_line_match, baseline,v and previous.v output diff results to add/reduce/same results .v
        old_v = os.path.abspath('baseline.v')
        new_v = os.path.abspath('previous.v')
        same_results = json_map(old_v, new_v, match)

        # 4. call function to count new/fix issue based on group in UI .
        issueKey_count(same_results)
