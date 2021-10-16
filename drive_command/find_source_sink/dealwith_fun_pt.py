import os

if __name__ == '__main__':
    # dic = "/home/raoxue/Desktop/openssl-1.0.1f/ssl"
    # dic="/home/raoxue/Desktop/libdwarf-20161021/dwarf-20161021/libdwarf"
    dic = "/home/raoxue/Desktop/libdwarf-20161021/dwarf-20161021/dwarfdump"

    # sdic="/home/raoxue/Desktop/llvmref/wget_ll"
    # dic=sys.argv[1]
    abspath = os.path.abspath(dic)
    dicpath = os.listdir(dic)
    for file in dicpath:
        basename = os.path.basename(file)
        if basename.endswith(".ll"):
            cmd="cd "+dic+";opt -S -load libdw_fun_ptpass.so -de-fun-pt "+basename
            os.system(cmd)
