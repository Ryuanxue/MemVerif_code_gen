"""
first need to compile .c file to .ll file
clang -g -s  -emit-llvm -fno-discard-value-names hello.c -o hello.ll
input:
1.filename:xxx.ll
2.range of line number of a function
3.function name
4.varible name of array or pointer
"""
import re
import subprocess
import sys

arg1=sys.argv[1] #filename
arg2=sys.argv[2] #range of line number and c filename format with c_filename-startline-endline
arg3=sys.argv[3] #varible name of array or pointer
arg4=sys.argv[4] #function name

arg2split=arg2.split("-")
c_filename=arg2split[0]
startline=arg2split[1]
endline=arg2split[2]
# print(arg2split)
"""
two:run SVF tool to get aliase result
wpa --ander --print-all-pts CWE126_Buffer_Overread__char_alloca_loop_01.ll 
"""
svfcommand="wpa --ander --print-all-pts "+arg1+" >temp.txt"
(status,output)=subprocess.getstatusoutput(svfcommand)
if status==0:
    file1=open("temp.txt","r",encoding="utf-8")
    pre=False
    preline=""

    """
    getting all line satisfy "##<" and point to not empty
    """
    aliase_result=[]
    for line in file1.readlines():
        if line.startswith("##<"):
            pre=True
            preline=line
        elif pre:
            if "{empty}" in line:
                pre = False
                continue
            else:
                aliase_result.append(preline)
                aliase_result.append(line)
                pre = False

        else:
            continue

    """
    judge whether two varible is aliase
    find the aliase of input "data"
    """
    # for i in aliase_result:
    #     print(i)
    result_len=len(aliase_result)
    aliasename=""
    for i in range(0,result_len,2):
        # pass
        strname=re.findall(r'[<](.*?)[>]',aliase_result[i])[0]
        # print(strname)
        if strname==arg3:
            flindex=aliase_result[i].index("fl:")
            flname=aliase_result[i][flindex+4:-3]
            lnindex=aliase_result[i].index("ln:")
            linenum=aliase_result[i][lnindex+4:flindex-1]
            print(flname)
            print(c_filename)
            print(int(linenum))
            if flname==c_filename and int(startline)-1<int(linenum) and int(linenum)<int(endline):
                print(aliase_result[i])
                nextline=aliase_result[i+1]
                next_split=nextline.split("PointsTo:")
                ptr=re.sub('\s|\t|\n','',next_split[0])[3:]
                ptrto=re.sub('\s|\t|\n', '', next_split[1])[1:-1]
                if int(ptr)+1!=int(ptrto):
                    pointsTo=int(ptrto)
                    print(pointsTo)
                    for j in range(0,result_len,2):
                        rnextline = aliase_result[j + 1]
                        rnext_split = rnextline.split("PointsTo:")
                        # ptr = re.sub('\s|\t|\n', '', next_split[0])[3:]
                        rptrto = re.sub('\s|\t|\n', '', rnext_split[1])[1:-1]
                        ptrname=re.findall(r'[<](.*?)[>]',aliase_result[j])[0]
                        if int(rptrto)==pointsTo and ptrname and ptrname!=arg3 and not ptrname.startswith("arrayidx"):
                            aliasename=ptrname
                            # print(re.findall(r'[<](.*?)[>]',aliase_result[j])[0])
                            # print(aliase_result[j])
                            break
                        # print(rptrto)
                    break
print(aliasename)
file = open("aliase.txt", "w", encoding="utf-8")
file.write(aliasename)
file.close()


def getaliase(arg1,arg2,arg3,arg4):
    # arg1 = sys.argv[1]  # filename
    # arg2 = sys.argv[2]  # range of line number and c filename format with c_filename-startline-endline
    # arg3 = sys.argv[3]  # varible name of array or pointer
    # arg4 = sys.argv[4]  # function name

    arg2split = arg2.split("-")
    c_filename = arg2split[0]
    startline = arg2split[1]
    endline = arg2split[2]
    # print(arg2split)
    """
    two:run SVF tool to get aliase result
    wpa --ander --print-all-pts CWE126_Buffer_Overread__char_alloca_loop_01.ll 
    """
    svfcommand = "wpa --ander --print-all-pts " + arg1 + " >temp.txt"
    (status, output) = subprocess.getstatusoutput(svfcommand)
    if status == 0:
        file1 = open("temp.txt", "r", encoding="utf-8")
        pre = False
        preline = ""

        """
        getting all line satisfy "##<" and point to not empty
        """
        aliase_result = []
        for line in file1.readlines():
            if line.startswith("##<"):
                pre = True
                preline = line
            elif pre:
                if "{empty}" in line:
                    pre = False
                    continue
                else:
                    aliase_result.append(preline)
                    aliase_result.append(line)
                    pre = False

            else:
                continue

        """
        judge whether two varible is aliase
        find the aliase of input "data"
        """
        # for i in aliase_result:
        #     print(i)
        result_len = len(aliase_result)
        aliasename = ""
        for i in range(0, result_len, 2):
            # pass
            strname = re.findall(r'[<](.*?)[>]', aliase_result[i])[0]
            # print(strname)
            if strname == arg3:
                flindex = aliase_result[i].index("fl:")
                flname = aliase_result[i][flindex + 4:-3]
                lnindex = aliase_result[i].index("ln:")
                linenum = aliase_result[i][lnindex + 4:flindex - 1]
                print(flname)
                print(c_filename)
                print(int(linenum))
                if flname == c_filename and int(startline) - 1 < int(linenum) and int(linenum) < int(endline):
                    print(aliase_result[i])
                    nextline = aliase_result[i + 1]
                    next_split = nextline.split("PointsTo:")
                    ptr = re.sub('\s|\t|\n', '', next_split[0])[3:]
                    ptrto = re.sub('\s|\t|\n', '', next_split[1])[1:-1]
                    if int(ptr) + 1 != int(ptrto):
                        pointsTo = int(ptrto)
                        print(pointsTo)
                        for j in range(0, result_len, 2):
                            rnextline = aliase_result[j + 1]
                            rnext_split = rnextline.split("PointsTo:")
                            # ptr = re.sub('\s|\t|\n', '', next_split[0])[3:]
                            rptrto = re.sub('\s|\t|\n', '', rnext_split[1])[1:-1]
                            ptrname = re.findall(r'[<](.*?)[>]', aliase_result[j])[0]
                            if int(rptrto) == pointsTo and ptrname and ptrname != arg3 and not ptrname.startswith(
                                    "arrayidx"):
                                aliasename = ptrname
                                # print(re.findall(r'[<](.*?)[>]',aliase_result[j])[0])
                                # print(aliase_result[j])
                                break
                            # print(rptrto)
                        break
"""
run constom llvm pass to get bound
"""
llvm_opt_command="opt -load libdummypass.so -dummypass "+arg1+" -fun-name " +arg4+ " -var-name " +aliasename
print(llvm_opt_command)
subprocess.getstatusoutput(llvm_opt_command)
if status==0:
    file = open("temp.txt", "r", encoding="utf-8")
    line=file.readlines()
    print(line)
    file.close()

    for i in aliase_result:
        print(i)




