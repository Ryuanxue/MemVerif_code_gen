import os
from xml.dom.minidom import parse

if __name__ == '__main__':
    """
    partion into three kinds,have bound,pointer,have name.
    """
    dic = "/home/raoxue/Desktop/openssl-1.0.1f/ssl"
    # sdic="/home/raoxue/Desktop/llvmref/wget_ll"
    # dic=sys.argv[1]
    sum_result=[]
    bound_result=[]
    pointer_result=[]
    srcname_result=[]
    abspath = os.path.abspath(dic)
    dicpath = os.listdir(dic)
    for file in dicpath:
        filename = os.path.basename(file)
        # print(filename)
        if filename.endswith(".xml"):
            doc = parse(dic+"/"+filename)
            root = doc.documentElement
            ovreadsrc = root.getElementsByTagName("ovreadsrc")
            for overread in ovreadsrc:
                bound=overread.getAttribute("bound")
                srcname=overread.getAttribute("srcname")
                c_filename=overread.getAttribute("c_filename")
                srcline=overread.getAttribute("srcline")
                str = c_filename + "_" + srcline + "_" + bound + "_" + srcname
                sum_result.append(str)
                if(int(bound)!=0):
                    bound_result.append(str)
                if(srcname=="struct"):
                    pointer_result.append(str)
                if(len(srcname)>0 and srcname!="struct"):
                    srcname_result.append(str)
                if (srcname=="struct" and int(bound)>0):
                    print(str)


    print("###############")
    for i in pointer_result:
        print(i)
    print(len(pointer_result))
    print("############")

    for i in srcname_result:
        print(i)
    print(len(srcname_result))
    print("############")

    for i in bound_result:
        print(i)
    print(len(bound_result))
    print("############")
    print(len(sum_result))


