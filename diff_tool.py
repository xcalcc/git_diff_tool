#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import argparse
import sys
import time
import json
import linecache
import copy

# read file contents line by line.
def read_file(file_name):
    try:
        file_desc = open(file_name, 'r')

        text = file_desc.read().splitlines()
        file_desc.close()
        return text
    except IOError as error:
        print('Read input file Error: {0}'.format(error))
        sys.exit()


# git diff
def git_diff(path_args, commit_o, commit_n):
    if path_args and commit_o is None and commit_n is None:
        os.chdir(path_args)
        git_dir = "%s/.git" % (path_args)
        if os.path.isdir(git_dir):
            os.system(''' git log | grep "^commit " |awk '{print $2}' > git_commitID.txt ''')
        if not os.path.isdir(git_dir):
            print('There can not run git diff, please input the right path')

        if os.path.isfile("git_commitID.txt"):
            commitID_new = linecache.getline("git_commitID.txt", 1).strip('\n')
            commitID_old = linecache.getline("git_commitID.txt", 2).strip('\n')
        else:
            print('Read commitID failed: ')
            sys.exit()

        linecache.clearcache()

        os.system(''' git diff --unified=0 %s %s > git_diff_results.txt ''' % (commitID_old, commitID_new))

        git_diff_path = "%s/git_diff_results.txt" % (path_args)
        return git_diff_path

    if path_args and commit_o is not None and commit_n is not None:
        commitID_old = commit_o
        commitID_new = commit_n

        os.chdir(path_args)

        os.system(''' git diff --unified=0 %s %s > git_diff_results.txt ''' % (commitID_old, commitID_new))
        git_diff_path = "%s/git_diff_results.txt" % (path_args)
        return git_diff_path

# read the git_diff_results.txt and match the diff results to source file.
# def diff_map_code(git_diff_content, new_line_match, new_line_change, change_file_list,
#                  old_line_change, add_file_list, reduce_file_list):

# source file and line number match. return a dict of new source code line number map to old source code line number.
def code_map(git_diff_path, path_args):
    try:
        if os.path.exists(git_diff_path):
            git_diff_read = open(git_diff_path, 'r')
            git_diff_content = git_diff_read.readlines()
            git_diff_read.close()
    except IOError as error:
        print('Read git_diff_results.txt failed, please check this file.')
        sys.exit()


    # length of git_diff_results.txt
    git_diff_len = len(git_diff_content)
    diff_list        = {}
    new_line_match   = {}
    change_file_list = []
    add_file_list    = []
    reduce_file_list = []


    for line_no,content in enumerate(git_diff_content):
        git_diff_diff = re.search(r'diff --git (.*)', content)
        if git_diff_diff is not None:
            git_diff_reduce = re.search(r'^a/(.*) (.*)', git_diff_diff.group(1))
            git_diff_add = re.search(r'^b/(.*)', git_diff_reduce.group(2))

            # count total line number of diff source file
            # "tln" is total line number
            git_diff_null = "\/dev\/null"
            if git_diff_reduce is not None:
                git_diff_reduce_file = re.sub(r'^a/', "", git_diff_reduce.group(1))

                if git_diff_null in git_diff_reduce.group(1):
                    new_file = re.sub(r'^b/', "", git_diff_add.group(1))
                    new_file_path = "%s/%s" % (path_args, new_file)
                    add_file_list.append(new_file_path)

            if git_diff_add is not None:
                git_diff_add_file = re.sub(r'^b/', "", git_diff_add.group(1))

                git_diff_target = "%s/%s" % (path_args, git_diff_add_file)
                if os.path.isfile(git_diff_target):
                    tln = 0
                    for count, line in enumerate(open(git_diff_target, 'r')):
                        tln += 1

                if git_diff_add_file == git_diff_reduce_file:
                    change_file = "%s/%s" % (path_args, git_diff_add_file)
                    change_file_list.append(change_file)
                    new_line_match['%s' % change_file] = {}

                    count_add = 0
                    count_reduce = 0
                    current_add = 0
                    current_reduce = 0
                    new_line_change = []
                    old_line_change = []

                if git_diff_null in git_diff_add.group(1):
                    reduce_file = re.sub(r'^a/', "", git_diff_reduce.group(1))
                    reduce_file_path = "%s/%s" % (path_args, reduce_file)
                    reduce_file_list.append(reduce_file_path)

        line_change = re.search(r'@@ (\-.*) (\+.*) @@', content)
        if line_change is not None:
            new_line_change_check = re.search(r',0', line_change.group(2))
            old_line_change_check = re.search(r',0', line_change.group(1))

            if new_line_change_check is None:
                new_change_line = re.search(r'\+(\d+)\,(\d+)', line_change.group(2))
                if new_change_line is not None:
                    new_sln = int(new_change_line.group(1))
                    new_change = int(new_change_line.group(2))
                    for i in range(new_change):
                        new_line_change.append(new_sln + i)
                else:
                    new_change_line = re.search(r'\+(\d+)', line_change.group(2))
                    if new_change_line is not None:
                        new_sln = int(new_change_line.group(1))
                    new_line_change.append(new_sln)
                    new_change = 1
            else:
                new_change_line = re.search(r'\+(\d+)\,0', line_change.group(2))
                if new_change_line is not None:
                    new_sln = int(new_change_line.group(1))
                new_change = 0

            if old_line_change_check is None:
                old_change_line = re.search(r'\-(\d+)\,(\d+)', line_change.group(1))
                if old_change_line is not None:
                    old_sln = int(old_change_line.group(1))
                    old_change = int(old_change_line.group(2))
                    for i in range(old_change):
                        old_line_change.append(old_sln + i)
                else:
                    old_change_line = re.search(r'\+(\d+)', line_change.group(1))
                    if old_change_line is not None:
                        old_sln = int(old_change_line.group(1))
                    old_change = 1
            else:
                old_change_line = re.search(r'\-(\d+)\,0', line_change.group(1))
                if old_change_line is not None:
                    old_sln = int(old_change_line.group(1))
                old_change = 0


            if new_change > old_change:
                current_add += (int(new_change) - int(old_change))
                count_add += (int(new_change) - int(old_change))
            if new_change < old_change:
                current_reduce += (int(old_change) - int(new_change))
                count_reduce += (int(old_change) - int(new_change))

            # map line number , save data to dict.
            # if new_line_match is None:
            # new_line_match['%s' % change_file_name] = {}
            if count_add > 0:
                sln_map = new_sln + current_add
                for i in range(sln_map, tln + 1):
                    new_line_match['%s' % change_file][i] = i - count_add
            if count_reduce > 0:
                sln_map = new_sln + current_reduce
                for i in range(sln_map, tln + 1):
                    new_line_match['%s' % change_file][i] = i + count_reduce
            '''
            else:
                if count_add > 0:
                    sln_map = new_sln + count_add
                    for i in range(sln_map, tln + 1):
                        new_line_match[i] = i - count_add
                if count_reduce > 0:
                    sln_map = new_sln + count_reduce
                    for i in range(sln_map, tln + 1):
                        new_line_match[i] = i + count_reduce
            '''

    # delete the change line number from all line number. just display match line.
    for f in change_file_list:
        for k in new_line_change:
            if k in new_line_match[f].keys():
                new_line_match[f].pop(k)

    print(new_line_match)

    print(new_line_change)
    #print(old_line_change)
    #print(add_file_list)
    #print(reduce_file_list)
    print(change_file_list)




    # need fill this logic in the next step,, to support mutiple files modified in one commit.
    #if len(diff_list) > 1:
    #    diff_map_code(git_diff_content, new_line_match, new_line_change, change_file_list,
    #                  old_line_change, add_file_list, reduce_file_list)

    return new_line_match, change_file_list


# json results map and diff.
def json_map(old_v, new_v, new_line_match, change_file_list):
    # old .v json results load as diff baseline
    with open(old_v, "r") as old_v_file:
        old_v_data = json.load(old_v_file)

    old_v_files    = old_v_data["files"]
    old_v_issues   = old_v_data["issues"]

    # new .v json results load as diff baseline and write the data to diff results(three json files.)
    with open(new_v, "r") as new_v_file:
        new_v_data = json.load(new_v_file)

    new_v_files    = new_v_data["files"]
    new_v_issues   = new_v_data["issues"]
    new_v_rulesets = new_v_data["rulesets"]
    new_v_v        = new_v_data["v"]
    new_v_id       = new_v_data["id"]
    new_v_s        = new_v_data["s"]
    new_v_m        = new_v_data["m"]
    new_v_eng      = new_v_data["eng"]
    new_v_ev       = new_v_data["ev"]
    new_v_er       = new_v_data["er"]
    new_v_x1       = new_v_data["x1"]
    new_v_x2       = new_v_data["x2"]
    new_v_ss       = new_v_data["ss"]
    new_v_se       = new_v_data["se"]
    new_v_usr      = new_v_data["usr"]
    new_v_sys      = new_v_data["sys"]
    new_v_rss      = new_v_data["rss"]

    # add_files      = []  # This list store the add fid & path that only in new results , it will be diff further.
    # reduce_files   = []  # This list store the reduce fid & path that only in new results , it will be diff further.
    diff_new_issues= []  # This list store the different issues from new results , it will be diff further.
    diff_old_issues= []  # This list store the different issues from old results , it will be diff further.

    same_results   = []  # This list store the same issues, and will be write to same results Json file.
    add_results    = []  # This list store the add issues, and will be write to different results Json file.
    reduce_results = []  # This list store the reduce issues, and will be write to different results Json file.

    ### 1. simple json diff, get the same issues.
    ### fid diff will be used add/delete file when commit to git repo.
    # diff new with old, get same & add results.
    # map fid to file name to avoid file name and fid mismatch scenarios.
    # add this fid & file name match can reduce the function that check add_file_list & reduce_file_list.
    for new_issue in new_v_issues:
        for fid_path in new_v_files:
            if fid_path["fid"] == new_issue["fid"]:
                new_issue["fid"] = fid_path["path"]
            for new_issue_fid in new_issue["paths"]:
                if fid_path["fid"] == new_issue_fid["fid"]:
                    new_issue_fid["fid"] = fid_path["path"]

    for old_issue in old_v_issues:
        for fid_path in old_v_files:
            if fid_path["fid"] == old_issue["fid"]:
                old_issue["fid"] = fid_path["path"]
            for old_issue_fid in old_issue["paths"]:
                if fid_path["fid"] == old_issue_fid["fid"]:
                    old_issue_fid["fid"] = fid_path["path"]

    for new_issue in new_v_issues:
        if new_issue in old_v_issues:
            same_results.append(new_issue)
        else:
            diff_new_issues.append(new_issue)

    for old_issue in old_v_issues:
        if old_issue not in new_v_issues:
            diff_old_issues.append(old_issue)


    ### 2. map resuts and diff them further.
    ### if diff_files is empty, it need not map & diff fid, just need map & diff line number and other 'k,vn,fn' value.
    # diff & map new with old , get the same & add results.
    #if len_add_files == 0:
    for diff_issue in diff_new_issues:
        tmp_list = copy.deepcopy(diff_issue)
        # judge file whether need be matched , recursive match all sln which need be matched .
        if tmp_list["fid"] in new_line_match.keys():
            if tmp_list["sln"] in new_line_match[tmp_list["fid"]].keys():
                tmp_list["sln"] = new_line_match[tmp_list["fid"]][tmp_list["sln"]]
                for diff_path in tmp_list["paths"]:
                    if diff_path["fid"] in new_line_match.keys():
                        if diff_path["sln"] in new_line_match[diff_path["fid"]].keys():
                            diff_path["sln"] = new_line_match[diff_path["fid"]][diff_path["sln"]]
        if tmp_list in old_v_issues:
            same_results.append(diff_issue)
        else:
            add_results.append(diff_issue)

    # diff & map old with new , get the same & reduce results.
    old_line_match = {}
    for f in new_line_match.keys():
        old_line_match[f] = dict(zip(new_line_match[f].values(), new_line_match[f].keys()))
    print(old_line_match)
    for diff_issue in diff_old_issues:
        tmp_list = copy.deepcopy(diff_issue)
        # judge file whether need be matched , recursive match all sln which need be matched .
        if tmp_list["fid"] in old_line_match.keys():
            if tmp_list["sln"] in old_line_match[tmp_list["fid"]].keys():
                tmp_list["sln"] = old_line_match[tmp_list["fid"]][tmp_list["sln"]]
                for diff_path in tmp_list["paths"]:
                    if diff_path["fid"] in old_line_match.keys():
                        if diff_path["sln"] in old_line_match[diff_path["fid"]].keys():
                            diff_path["sln"] = old_line_match[diff_path["fid"]][diff_path["sln"]]
        #if diff_issue in new_v_issues:
        #    if tmp_list not in same_results:
        #        same_results.append(tmp_list)
        #else:
        if tmp_list not in new_v_issues:
            reduce_results.append(diff_issue)

    #print(old_v_issues)
    #print(new_v_issues)
    #print(diff_old_issues)
    #print(same_results)
    #print(add_results)
    #print(reduce_results)

    ### 3. write the same & diff results to json file.
    if same_results:
        # revert file name to fid for producing normal .v file
        for issue in same_results:
            for fid_path in new_v_files:
                if fid_path["path"] == issue["fid"]:
                    issue["fid"] = fid_path["fid"]
                for issue_fid in issue["paths"]:
                    if fid_path["path"] == issue_fid["fid"]:
                        issue_fid["fid"] = fid_path["fid"]

        same_results_dict = {
            "files": new_v_files,
            "issues": same_results,
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

        same_json_format = json.dumps(same_results_dict, indent=1)
        with open('same_results.v', 'w') as same_json_target:
            same_json_target.write(same_json_format)

    if add_results:
        # revert file name to fid for producing normal .v file
        for issue in same_results:
            for fid_path in new_v_files:
                if fid_path["path"] == issue["fid"]:
                    issue["fid"] = fid_path["fid"]
                for issue_fid in issue["paths"]:
                    if fid_path["path"] == issue_fid["fid"]:
                        issue_fid["fid"] = fid_path["fid"]

        add_results_dict = {
            "files": new_v_files,
            "issues": add_results,
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

        add_json_format = json.dumps(add_results_dict, indent=1)
        with open('add_results.v', 'w') as add_json_target:
            add_json_target.write(add_json_format)

    if reduce_results:
        # revert file name to fid for producing normal .v file
        for issue in same_results:
            for fid_path in new_v_files:
                if fid_path["path"] == issue["fid"]:
                    issue["fid"] = fid_path["fid"]
                for issue_fid in issue["paths"]:
                    if fid_path["path"] == issue_fid["fid"]:
                        issue_fid["fid"] = fid_path["fid"]

        reduce_results_dict = {
            "files": new_v_files,
            "issues": reduce_results,
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

        reduce_json_format = json.dumps(reduce_results_dict, indent=1)
        with open('reduce_results.v', 'w') as reduce_json_target:
            reduce_json_target.write(reduce_json_format)

    # count "k" & number of it in old & new .v file
    old_k_list = {}
    new_k_list = {}
    for k in old_v_data["issues"]:
        if k["k"] not in old_k_list.keys():
            old_k_list[k["k"]] = 1
        else:
            old_k_list[k["k"]] += 1

    for k in new_v_data["issues"]:
        if k["k"] not in new_k_list.keys():
            new_k_list[k["k"]] = 1
        else:
            new_k_list[k["k"]] += 1

    # count "k" & number of it in add & reduce results .v file
    add_k_list    = {}
    reduce_k_list = {}
    if os.path.isfile("add_results.v"):
        with open("add_results.v", "r") as add_file:
            add_result = json.load(add_file)

        for k in add_result["issues"]:
            if k["k"] not in add_k_list.keys():
                add_k_list[k["k"]] = 1
            else:
                add_k_list[k["k"]] += 1

    if os.path.isfile("reduce_results.v"):
        with open("reduce_results.v", "r") as reduce_file:
            reduce_result = json.load(reduce_file)

        for k in reduce_result["issues"]:
            if k["k"] not in reduce_k_list:
                reduce_k_list[k["k"]] = 1
            else:
                reduce_k_list[k["k"]] += 1

    if add_k_list:
        for k in add_k_list.keys():
            print("In this scan results the group of [%s] has [%s] defects, this commit leads to [%s] add results."
                  % (k, new_k_list[k] ,add_k_list[k]))

    if reduce_k_list:
        for k in reduce_k_list.keys():
            print("In this scan results the group of [%s] has [%s] defects, this commit fixed [%s] reduce results"
                  % (k, old_k_list[k], reduce_k_list[k]))


'''
    file_fid  = {}
    match_fid = []
    match_sln = {}

    for key in new_v_data["files"]:
        file_fid[key["path"]] = key["fid"]

    for change_file in change_file_list:
        if change_file in file_fid:
            match_fid.append(file_fid[change_file])
'''



# compare the new results with the baseline file, output compare results to nightly file.
def compare_baseline(target):
    time_mark = time.strftime("%Y%m%d%H%M%S", time.localtime())
    time_2 = time.strftime("%Y%m%d", time.localtime())

    file1 = '/home/jun/xc5/projectscan/C_project/%s/results_review/TP_baseline' % (target)
    file2 = '/home/jun/xc5/projectscan/C_project/%s/results_review/FP_baseline' % (target)

    file_dir = '/home/jun/xc5/projectscan/C_project/lua/results_review'

    for target_dir in os.scandir(file_dir):
        if time_2 in str(target_dir):
            data = target_dir.name
            file3 = '%s/%s/%s/xvsa-xfa-dummy-simp.v' % (file_dir, data, target)

    TP_file = read_file(file1)
    FP_file = read_file(file2)

    # nightly_results = read_file('/home/jun/xc5/projectscan/C_project/lua/results_review/data_20200303123321/lua/xvsa-xfa-dummy-simp.v')
    nightly_results = read_file(file3)

    for issue in TP_file:
        if issue not in nightly_results:
            FN_target  = 'FN_results_%s.txt' % (time_mark)
            FN_results = open(FN_target, 'a')
            FN_results.write(issue)
            FN_results.write('\n')
            FN_results.close()

    for issue in FP_file:
        if issue in nightly_results:
            FP_target  = 'FP_results_%s.txt' % (time_mark)
            FP_results = open(FP_target, 'a')
            FP_results.write(issue)
            FP_results.write('\n')
            FP_results.close()

    for issue in nightly_results:
        if issue not in FP_file and issue not in TP_file:
            ADD_target  = 'ADD_results_%s.txt' % (time_mark)
            ADD_results = open('ADD_results.txt', 'a')
            ADD_results.write(issue)
            ADD_results.write('\n')
            ADD_results.close()

if __name__ == "__main__":
    my_parser = argparse.ArgumentParser(description="Specify scenarios of diff & old/new scan results !!!")
    my_parser.add_argument('-p',  action='store', dest='path')
    my_parser.add_argument('-t1', action='store', dest='commit_o')
    my_parser.add_argument('-t2', action='store', dest='commit_n')
    my_parser.add_argument('-f1', action='store', dest='old_v', required=True)
    my_parser.add_argument('-f2', action='store', dest='new_v', required=True)

    my_parser.add_argument('-d', '--debug', dest = 'debug', action = 'store_true',
                        help = 'debug mode')

    give_args = my_parser.parse_args()
    old_v = give_args.old_v
    new_v = give_args.new_v
    path_args = give_args.path
    commit_o  = give_args.commit_o
    commit_n  = give_args.commit_n

    git_diff_path = git_diff(path_args, commit_o, commit_n)

    new_line_match, change_file_list = code_map(git_diff_path, path_args)
    json_map(old_v, new_v, new_line_match, change_file_list)

'''
    if path_args is not None:
        git_diff_path = git_diff(path_args)
    if commit_o is not None and \
            commit_n is not None:
        git_diff_path = git_diff(commit_o, commit_n)
'''