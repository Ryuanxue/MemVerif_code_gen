import sys

if __name__ == '__main__':
    if len(sys.argv)>1:
        inputfile=sys.argv[1]
    else:
        # inputfile = "/home/raoxue/Desktop/fuzztest/test.txt"
        inputfile="/home/raoxue/Desktop/FTS/openssl-1.0.1f/test.txt"
        # inputfile="/home/raoxue/Desktop/openssl-1.0.1f/ssl/test.txt"
    file=open(inputfile,"r",encoding="utf-8")
    presuff=[]
    result=[]
    for line in file.readlines():
        if 'filename' not in line:
            continue
        if line in result:
            continue
        else:
            index=line.find(",")
            preresult=line[:index]
            if preresult in presuff:
                continue
            else:
                presuff.append(preresult)
                result.append(line)
                print(line)

    print(len(result))
