import os

if __name__ == '__main__':
    dic = "/home/raoxue/Desktop/openssl-1.0.1f/ssl"
    # sdic="/home/raoxue/Desktop/llvmref/wget_ll"
    # dic=sys.argv[1]
    abspath = os.path.abspath(dic)
    dicpath = os.listdir(dic)
    for file in dicpath:
        filename = os.path.basename(file)
        print(filename)
        if filename.endswith(".xml"):
            # command = "cd " + abspath + ";python3 main.py " + filename
            # os.system(command)
            llfile = filename[:-4] + ".ll"
            instument_name=filename[:-4]+"_instrument.ll"
            instrument_command = "cd "+dic+";opt -S -load libinstrumentpass.so -process -xml-filename " \
                                           ""+filename+" < " + llfile + " > "+instument_name
            print(instrument_command)
            os.system(instrument_command)