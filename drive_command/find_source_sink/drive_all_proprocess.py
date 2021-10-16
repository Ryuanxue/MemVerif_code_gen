import os
import sys

if __name__ == '__main__':
    dic = "/home/raoxue/Desktop/openssl-1.0.1f/ssl"
    #sdic="/home/raoxue/Desktop/llvmref/wget_ll"
    #dic=sys.argv[1]
    abspath = os.path.abspath(dic)
    dicpath = os.listdir(dic)
    for file in dicpath:
        filename = os.path.basename(file)
        print(filename)
        if filename.endswith(".ll"):
            xmlfile = dic+"/"+filename[:-3] + ".xml"

            if os.path.exists(xmlfile):
                print("fffff")
                os.system("cd " + abspath)
                os.remove(xmlfile)
            """
            generate xml file accoreding to process
            """
            command = "cd " + abspath + ";opt-10 -load libpprocesspass.so -process " + filename + " -xmlfile " + xmlfile
            os.system(command)
