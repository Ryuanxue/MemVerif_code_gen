import os
import re
import subprocess
import sys

from xml.dom.minidom import parse

def getaliase(arg1,arg2,arg3,arg4):
    # arg1 = sys.argv[1]  # filename
    # arg2 = sys.argv[2]  # range of line number and c filename format with c_filename-startline-endline
    # arg3 = sys.argv[3]  # varible name of array or pointer
    # arg4 = sys.argv[4]  # a list of aliasename

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
        # aliasename = ""
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
                                arg4.append(ptrname)
                                # print(re.findall(r'[<](.*?)[>]',aliase_result[j])[0])
                                # print(aliase_result[j])
                                break
                            # print(rptrto)
                        break

if __name__ == '__main__':
    xmlfile = sys.argv[1][:-3]+".xml"
    if os.path.exists(xmlfile):
        os.remove(xmlfile)
    """
    generate xml file accoreding to process
    """
    command="opt -load libpprocesspass.so -process "+sys.argv[1]+" -xmlfile "+xmlfile
    os.system(command)

    if os.path.exists(xmlfile):
        pass
    else:
        exit()
    print("parse xml")
    doc=parse(xmlfile)
    root=doc.documentElement
    ovreadsrc=root.getElementsByTagName("ovreadsrc")
    for overread in ovreadsrc:
        print(overread.getAttribute("Type"))
        #call shell
        # sh. / get_bound.sh
        # CWE126_Buffer_Overread__char_alloca_loop_01.ll
        # CWE126_Buffer_Overread__char_alloca_loop_01.c - 24 - 50
        # data
        # CWE126_Buffer_Overread__char_alloca_loop_01_bad
        c_filename1=overread.getAttribute("c_filename")
        startline=overread.getAttribute("startline")
        endline=overread.getAttribute("endline")
        srcname=overread.getAttribute("srcname")
        #
        if c_filename1.startswith("./"):
            c_filename=c_filename1[2:]
        else:
            c_filename=c_filename1
        print(c_filename)
        srcline=overread.getAttribute("srcline")
        funname=overread.getAttribute("funname")
        Type=overread.getAttribute("Type")
        bound=overread.getAttribute("bound")
        print(bound)
        if bound!="0" and bound!='-1':
            print("fff")
            continue
        else:
            print(srcname+" false")
        print(srcname)
        """
        get all aliasename about one overread
        """
        # aliasename=[]
        # shcommand="sh ./get_bound.sh "+sys.argv[1]+" "+c_filename+"-"+startline+"-"+endline+\
        # " "+srcname+" "+funname
        # getboundcommand="python3 getbound.py "
        # print(shcommand)
        # os.system(shcommand)
        # arg2=c_filename+"-"+startline+"-"+endline
        # getaliase(sys.argv[1],arg2,srcname,aliasename)
        # if (len(aliasename)>0):
        #     print(aliasename)

        """
        instrument arrcording to bound or srcname
        """


    #     file = open("bound.txt", "r", encoding="utf-8")
    #     lines=file.readlines()
    #     file.close()
    #     bound=lines[0]
    #     overread.setAttribute("bound",bound)
    #
    # with open(xmlfile, 'w') as f:
    #     f.write(doc.toprettyxml(indent="  "))

    instrument_command = "opt -S -load libprintpass1.so -process < " + sys.argv[
        1] + " > output.ll"
    os.system(instrument_command)


