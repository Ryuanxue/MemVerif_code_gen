import os

if __name__ == '__main__':
    dic = "/home/raoxue/Desktop/openssl-1.0.1f/ssl"
    abspath = os.path.abspath(dic)
    dicpath = os.listdir(dic)

    for file in dicpath:
        filename = os.path.basename(file)
        if filename.endswith(".ll"):
            if "_instrument" not in filename:
                command="cd "+dic+";opt-10 -load libfindsinkpass.so -find-sink "+filename+" -xmlfile sink.xml"
                os.system(command)

