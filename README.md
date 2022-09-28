# repo_diff.py & delta_doff.py

## 1. Perequisite
* Need user environment can run "git log & git diff"

## 2. Introduce **repo_diff.py**
- 1. This tool need 'git log' to get User's commit info. Need specify commitID.
- 2. This tool run 'git diff' to get the diff results to file <git_diff_results.txt>.
- 3. This tool read <git_diff_results.txt> and output code line map results to file <code_line_match>
- 4. This tool will get the code line map . 
- 5. This tool will diff the results based on code line map & fid map.
- 6. This tool will output the results to Json file follow core team Json format.

## 2. Introduce **delta_diff.py**
- 1. This tool input the file <code_line_match> and baseline.v & previous.v .
- 2. This tool will output delta scan and diff results to add_results.v / same_results.v / reduce_results.v .
- 3. This tool will count new/fix issue depend on group by "issueKey" / "k" .

## 3. Usage for Inner Gerrit + Jenkins + Delta flow
```shell script
- 1. **repo_diff.py**: <*This tool will be used in inner Gerrit+Jenkins+delta flow*>
* python3 diff_tool.py -p <git path> -t1 <baseline_commitID> -t2 <previous_commitID>
* python3 delta_diff.py -m <code_line_match> -f1 <baseline.v> -f2 <previous.v>

- <git path> : That means where can run 'git log' & 'git diff' command.
- <baseline_commitID> : Specify commit ID as baseline when git diff.
- <previous_commitID> : Specify commit ID as previous when git diff.
- <baseline.v> : Specify json file from core as delta diff baseline v.
- <previous.v> : Specify json file from core as delta diff previous v.
```

## 4. Usage for Product flow
```shell script
- 2. **delta_diff.py**: <*This tool will be used in product scenarios*>
* python3 delta_diff.py -g <git_diff_results.txt> -f1 <baseline.v from MW> -f2 <previous.v from MW>

- <git_diff_results.txt> : Specify git_diff_results.txt as input.
- <baseline.v from MW> : Specify json file from MW as delta diff baseline v .
- <previous.v from MW> : Specify json file from MW as delta diff previous v .
```

## 5. Function & Logic in **repo_diff.py**

### 1). git_diff() : This function is used to run "git diff" in specified path.  
        It will produce "git_commitID.txt" & "git_diff_results.txt". "git_diff_results.txt" will be used in the next function to get code line  
        map info.

### 2). code_map() : This function is used to analysis "git_diff_results.txt" to get code line map info & some files changed info.   
        These data will be used in the next function.
        a). new_line_match : This is a two layer dictionary that be used to store file name and related line number map.  
            structure : {filename1:{new_line1 : old_line1, new_line2 : old_lin2}, filename2:{new_line1 : old_line1, new_line2 : old_line2}, ...}
        b). change_file_list : This is a list to store the file name that be modified in this commit.
        c). add_file_list    : This is a list to store the new file that be added in this commit.
        d). reduce_file_list : This is a list to store the reduce file that be deleted in this commit.
          
        *Note: **This tool will output <code_line_match>**

## 6. Function & Logic in **delta_diff.py**

### 1). json_convert() : This function is used to convert json file from MW to standard format in core json format.  
                         So the diff logic need not be modified ,can support different scenarios in inner and product.

### 2). json_map() : This function is used to read old & new .v file , read the data from the previous functions.  
        In this function it will produce "add_results.v" to store new add issues in the latest scan results. "reduce_results.v" to store be fixed issues in this commit.
        These two file format are following core .v file format. It should be used by MW components.
        *Logic: In this function, it will read old & new .v , new_line_match , change_file_list , add_file_list , reduce_file_list .  
                a). If one issue in new .v & old .v is same , it will be stored in the list "same_results"
                b). If one issue from new .v is different from old .v , it will be mapped code line , after line map , if it is same with old .v issue,  
                    it will be stored in the list "same_results", if not , it will be stored in the list "add_results"
                c). If one issue from old .v is different from new .v , it will be mapped code line , after line map , if it is same with new .v issue,  
                    it will be stored in the list "same_results", if not , it will be stored in the list "reduce_results"
                    
                d). After the code map and diff step , it will read the list of "same_results", "add_results" and "reduce_results".  
                    And then translate these 3 list to json format and write to json file "same_results.v", "add_results.v" and "reduce_resuls.v".
                    
        **group issue check&display function :   
                a). In this function, it will read all "k" value and count the number of it from old & new .v file.   
                b). And then read all "k" value and count the number of it from "add_results.v" & "reduce_results.v".  
                c). Based on the previous 2 step data , it can get the situation of add results or reduce results in related group.  
                    For example, it will produce the results about add results in related group as below:  
                    --> "In this scan results the group of [b@AOB@main@5] has [1] defects, this commit leads to [1] add results."  
                        "In this scan results the group of [b@UIV@main@a] has [1] defects, this commit leads to [1] add results."

