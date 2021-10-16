import os

if __name__ == '__main__':
    dic = "wget_ll"
    abspath = os.path.abspath(dic)
    dicpath = os.listdir(dic)
    for file in dicpath:
        filename=os.path.basename(file)
        print(filename)
        if filename.endswith(".ll"):
            command="cd "+abspath+";python3 main.py "+filename
            os.system(command)