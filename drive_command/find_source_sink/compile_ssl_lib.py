import os

if __name__ == '__main__':
    dic = "/home/raoxue/Desktop/openssl-1.0.1f/ssl"
    abspath = os.path.abspath(dic)
    dicpath = os.listdir(dic)
    ll_file=[]
    final_ll_file=[]
    os.system("cd "+dic+";rm *.s;rm *.out")
    for file in dicpath:
        filename = os.path.basename(file)
        if filename.endswith(".ll"):
            ll_file.append(filename)
    for fname in ll_file:
        base=fname[:-3]
        if base+"_instrument.ll" in ll_file:
            continue
        else:
            final_ll_file.append(fname)
    for f in final_ll_file:
        base=f[:-3]
        s_name=base+".bc"
        out_name=base+".o"
        ll_to_s_command="cd "+dic+";llvm-as "+f+" -o "+s_name
        os.system(ll_to_s_command)
        s_to_out_commmand="cd "+dic+";clang -c "+s_name+" -o "+out_name
        os.system(s_to_out_commmand)

    os.system("cd "+dic+";ar r libssl.a *.o")
