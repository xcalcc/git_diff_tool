#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import argparse
import sys
import json
import linecache

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

        git_diff_result = "%s/git_diff_results.txt" % (path_args)
        return git_diff_result

    if path_args and commit_o is not None and commit_n is not None:
        commitID_old = commit_o
        commitID_new = commit_n

        os.chdir(path_args)

        os.system(''' git diff --unified=0 %s %s > git_diff_results.txt ''' % (commitID_old, commitID_new))
        git_diff_result = "%s/git_diff_results.txt" % (path_args)
        return git_diff_result

# source file and line number match. return a dict of new source code line number map to old source code line number.
def code_map(git_diff_result, path_args):
    try:
        if os.path.exists(git_diff_result):
            git_diff_read = open(git_diff_result, 'r')
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
                    old_change_line = re.search(r'\-(\d+)', line_change.group(1))
                    if old_change_line is not None:
                        old_sln = int(old_change_line.group(1))
                    old_change = 1
            else:
                old_change_line = re.search(r'\-(\d+)\,0', line_change.group(1))
                if old_change_line is not None:
                    old_sln = int(old_change_line.group(1))
                old_change = 0

            print(new_change)
            print(old_change)
            if new_change > old_change:
                #current_add += (int(new_change) - int(old_change))
                count_add += (int(new_change) - int(old_change))
            if new_change < old_change:
                #current_reduce += (int(old_change) - int(new_change))
                count_reduce += (int(old_change) - int(new_change))
            print(count_add)
            print(count_reduce)

            # map line number , save data to dict.
            # if new_line_match is None:
            # new_line_match['%s' % change_file_name] = {}
            if count_add > 0:
                #sln_map = new_sln + current_add
                for i in range(new_sln, tln + 1):
                    print(i)
                    new_line_match['%s' % change_file][i] = i - count_add
            if count_reduce > 0:
                #sln_map = new_sln + current_reduce
                for i in range(old_sln, tln + 1):
                    new_line_match['%s' % change_file][i] = i + count_reduce
            print(new_line_match)

    # delete the change line number from all line number. just display match line.
    for f in change_file_list:
        for k in new_line_change:
            if k in new_line_match[f].keys():
                new_line_match[f].pop(k)

    print(new_line_match)

    with open('code_line_match', 'w') as f:
        f.write(str(new_line_match))
    #code_line_match_json = json.dumps(new_line_match, indent=1)
    #with open('code_line_match', 'w') as f:
    #    f.write(code_line_match_json)


if __name__ == "__main__":
    my_parser = argparse.ArgumentParser(description="Specify scenarios of diff !!!")
    my_parser.add_argument('-p',  action='store', dest='path', required=True)
    my_parser.add_argument('-t1', action='store', dest='commit_o')
    my_parser.add_argument('-t2', action='store', dest='commit_n')


    give_args = my_parser.parse_args()
    path_args = give_args.path
    commit_o  = give_args.commit_o
    commit_n  = give_args.commit_n

    git_diff_result = git_diff(path_args, commit_o, commit_n)
    code_map(git_diff_result, path_args)