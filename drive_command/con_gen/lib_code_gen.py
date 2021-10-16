import copy
import os
import subprocess
from xml.dom.minidom import parse

from pycparser import parse_file, c_ast, c_generator, c_parser
from con_gen.deal_return import deal_return, global_return_sta, get_last_linenum, global_return_decl

genxml_dealed_file = []

dir_ast = {}
global_dic = {}
Ismodifyloclavarible = []
fun_loop = {}
globalv_list = []  # store global varible
fun_decl_dic = {}
global_funname = []
generator = c_generator.CGenerator()


def get_c_filename(curele):
    """
    获得基本块中的c文件名
    :param curele:基本块
    :return: string(c文件名）
    """
    startline = get_first_lineinfo(curele)  # 取第一行
    rindex = startline.rfind(":")
    rslash = startline.rfind("/")
    temp_cfile = startline[rslash + 1:rindex]
    return temp_cfile


def get_project_path(ele):
    startline = get_first_lineinfo(ele)  # 取第一行
    rslash = startline.rfind("/")
    temp_path = startline[:rslash]
    return temp_path


def find_loop(sta, funname):
    for s in sta:
        if s is None:
            continue
        else:
            if type(s) == c_ast.For or type(s) == c_ast.While or type(s) == c_ast.DoWhile:
                startline = int(str(s.coord).split(":")[1])
                last_num = -1
                linenum_list = []
                get_last_linenum(s, last_num, linenum_list)
                lastline = linenum_list[0]
                list2 = list(range(startline, lastline))
                tempdic = {}
                tempkeyname = str(startline) + ":" + str(lastline)
                tempdic[tempkeyname] = s
                if funname in fun_loop.keys():
                    flag = True
                    for loop in fun_loop[funname]:
                        loopkeylist = list(loop.keys())[0].split(":")
                        start_line = int(loopkeylist[0])
                        end_line = int(loopkeylist[1])
                        list1 = list(range(start_line, end_line))
                        if len(list2) > len(list1):
                            if list1[0] in list2:
                                fun_loop[funname].append(tempdic)
                                fun_loop[funname].remove(loop)
                                flag = False
                                break
                        else:
                            if list2[0] in list1:
                                flag = False
                                break
                    if flag:
                        fun_loop[funname].append(tempdic)
                else:
                    fun_loop[funname] = []
                    fun_loop[funname].append(tempdic)


def getfundef():
    s = r'''
    void f(int a){

    }
    '''
    parser = c_parser.CParser()
    s_ast = parser.parse(s)
    return s_ast


def gen_final_startpart(line_ast, outfile, genfunname, param_list, gotolabel, labeldefine, return_val):
    """
    根据存放ast的列表，进行代码移动操作，形参实参传递，生成最终的代码（适用于start_part）
    :param line_ast: 存放对应于c语句的ast列表（倒序）
    :param outfile: 生成函数的函数名
    :return:
    """
    """反向插入"""

    temp_ast = []
    for i in line_ast:
        key_funname = list(i.keys())[0]
        ast_list = i[key_funname]
        print(key_funname)
        # for ii in ast_list:
        #     # print(generator.visit(ii))
        #     if type(ii) == 'int':
        #         continue
        #     else:
        #         print(generator.visit(ii))
        #     print(ii)

    for st in line_ast:
        key_funname = list(st.keys())[0]
        ast_list = st[key_funname]
        if st == line_ast[0]:
            nextfunname = key_funname
            for t in ast_list:
                temp_ast.append(t)
        else:
            rdic = []
            depth = 0
            last_ast = ast_list[-1]
            linenum = ast_list[0]
            isincludefuncall1(last_ast, nextfunname, rdic, depth, linenum,
                              last_ast)  # 只是为了判断如果有需要展开的函数调用的话，返回dic
            if len(rdic) > 0:
                """进行声明和赋值语句的插入，插在何处是一个问题"""
                move_code_startpart(rdic, nextfunname, temp_ast, ast_list)
                temp_ast.clear()
                for t in ast_list:
                    if t == ast_list[0]:
                        continue
                    else:
                        temp_ast.append(t)
            nextfunname = key_funname

    fundef = getfundef()
    fundef.ext[0].decl.name = genfunname
    fundef.ext[0].decl.type.type.declname = genfunname
    funparam = fundef.ext[0].decl.type.args.params
    funparam.pop()
    temp_param = []
    temp_name = []
    for p in param_list:
        if p.name in temp_name:
            continue
        else:
            temp_name.append(p.name)
            temp_param.append(p)
    for p in temp_param:
        if p.init != None:
            vardecl = c_ast.Decl(quals='', name=p.name, type=p.type, storage='', funcspec='', init=None, bitsize=None)
            funparam.append(vardecl)
            continue
        funparam.append(p)
    temp_ret_name = []
    for p in return_val:
        if p.name in temp_ret_name:
            continue
        else:
            funparam.append(p)
            temp_ret_name.append(p.name)
    fundef.ext[0].body.block_items = []

    for ele in temp_ast:
        fundef.ext[0].body.block_items.append(ele)
    for ele in gotolabel:
        if ele in labeldefine:
            continue
        else:
            labelst = c_ast.Label(name=ele, stmt=c_ast.FuncCall(name=c_ast.ID(name="printf"), args=c_ast.ExprList(
                exprs=[c_ast.Constant(type="string", value='"##\\n"')])))
            fundef.ext[0].body.block_items.append(labelst)
    c_file = open(outfile, "w")
    # print(fundef)
    c_file.write(generator.visit(fundef))
    c_file.close()
    # print(generator.visit(fundef))


def modif_ret(tempsta, nextfunname, ret_name):
    for l in tempsta:
        if type(l) == c_ast.FuncCall and l.name.name == nextfunname:
            if type(tempsta) == c_ast.Assignment:
                tempsta.rvalue = c_ast.ID(name=ret_name)
        else:
            modif_ret(l, nextfunname, ret_name)


def get_actual_parm(c, rdic):
    if c.args is not None:
        # print("%%%%")
        for id in c.args.exprs:
            idname = generator.visit(id)
            rdic.append(idname)


def is_have_funcall(nextfunname, stmt, linenum, funlist):
    """
    一条简单语句对应的ast中是否包含被调用函数
    :param nextfunname: called函数的函数名
    :param stmt: 简单c语句对应的ast
    :param linenum: called函数所在的行号
    :param funlist: 返回列表，返回ture与called函数ast
    :return:
    """
    if stmt is None:
        return False
    # print("havecall.....")
    # print(stmt)
    # print(generator.visit(stmt))

    curlinenum = str(stmt.coord)
    print(curlinenum)
    # print(curlinenum)
    # if str(linenum) in curlinenum:
    # print("line ......")
    stype = type(stmt)
    # print(stmt)
    if stype == c_ast.FuncCall:
        if str(linenum) in curlinenum or curlinenum is None:
            tempfunname = stmt.name
            funname = generator.visit(tempfunname)
            if funname == nextfunname:
                funlist.append("true")
                funlist.append(stmt)
                print("function....")
                print(stmt)
                return True

    for s in stmt:
        if s is None:
            continue
        curlinenum = str(s.coord)
        # print(curlinenum)
        # if str(linenum) in curlinenum:
        # print("line ......")
        stype = type(s)
        # print(s)
        if stype == c_ast.FuncCall:
            if str(linenum) in curlinenum or curlinenum is None:
                tempfunname = s.name
                funname = generator.visit(tempfunname)
                if funname == nextfunname:
                    funlist.append("true")
                    funlist.append(s)
                    print("function....")
                    # print(s)
                    return True
                else:
                    is_have_funcall(nextfunname, s, linenum, funlist)
            else:
                is_have_funcall(nextfunname, s, linenum, funlist)
        else:
            is_have_funcall(nextfunname, s, linenum, funlist)


def find_ID(st, l):
    """

    :param st:
    :param l:
    :return:
    """
    for i in st:
        if (i == None):
            break
        elif type(i) == c_ast.ID:
            idname = i.name
            if type(st) == c_ast.StructRef:
                if st.field.name == idname:
                    continue
                else:
                    if i.name in globalv_list and i.name not in l:
                        l.append(i.name)
            if i.name in globalv_list and i.name not in l:
                l.append(i.name)
            find_ID(i, l)
        else:
            find_ID(i, l)


def storeFunllDecl(fun, funname):
    """
    将函数的参数列表中的变量对应的ast存放在fun_decl_dic中
    :param fun: c_ast.FuncDef（函数对应的ast）
    :param funname: 字符串（函数名）
    :return: 将参数列表添加到fun_decl_dic中
    """
    fun_decl_dic[funname] = []
    if type(fun.decl.type) == c_ast.FuncDecl and fun.decl.type.args != None:
        for i in fun.decl.type.args.params:
            fun_decl_dic[funname].append(i)


def modifyid(st, funname, fun_global_list, localval):
    """
    SSA处理，递归修改每一条语句对应的ast中的变量名和label为"_" + funname + "_" + oldname + "_"的形式
    :param st: ast节点（对应c语言中语句的ast节点或子节点）
    :param funname:字符串（函数名）
    :param fun_global_list:列表（包含funname函数中所使用到的全局变量的变量名）
    :param localval:list （存放局部变量的声明）
    :return:无
    """
    # if type(st)==c_ast.Decl:
    #     if st.name not in localval:
    #         localval.append(st.name)

    if type(st) == c_ast.If:
        for i in st:
            if type(i) == c_ast.Label:
                oldname = i.name
                newname = "_" + funname + "_" + oldname + "_"
                i.name = newname
                modifyid(i.stmt, funname, fun_global_list, localval)
            elif type(i) == c_ast.Goto:
                oldname = i.name
                newname = "_" + funname + "_" + oldname + "_"
                i.name = newname
    for i in st:
        # print(st)
        # if type(st)==c_ast.Decl and type(i) == c_ast.FuncDecl :
        #     modifyid(i.args.params, funname, fun_global_list, localval)
        #     continue
        if (i == None):
            continue

        elif type(i) == c_ast.Label:
            if type(st) == c_ast.If:
                continue
            oldname = i.name
            newname = "_" + funname + "_" + oldname + "_"
            i.name = newname
            modifyid(i.stmt, funname, fun_global_list, localval)

        elif type(i) == c_ast.Goto:
            if type(st) == c_ast.If:
                continue
            oldname = i.name
            newname = "_" + funname + "_" + oldname + "_"
            i.name = newname
        elif type(i) == c_ast.Decl:
            if i.name not in localval:
                localval.append(i.name)
            oldname = i.name
            newname = "_" + funname + "_" + oldname + "_"
            if oldname in fun_global_list:
                pass
            else:
                i.name = newname
            if type(i.type) == c_ast.PtrDecl:
                if type(i.type.type) == c_ast.FuncDecl:
                    if oldname in fun_global_list:
                        pass
                    else:
                        i.type.type.type.declname = newname
                    modifyid(i.type.type.args.params, funname, fun_global_list, localval)
                    continue
                elif type(i.type.type) == c_ast.PtrDecl:
                    if oldname in fun_global_list:
                        pass
                    else:
                        i.type.type.type.declname = newname
                else:
                    if oldname in fun_global_list:
                        pass
                    else:
                        i.type.type.declname = newname

            elif type(i.type) == c_ast.ArrayDecl:
                if type(i.type.type) == c_ast.PtrDecl:
                    if oldname in fun_global_list:
                        pass
                    else:
                        i.type.type.type.declname = newname
                else:
                    if oldname in fun_global_list:
                        pass
                    else:
                        i.type.type.declname = newname
            else:
                if oldname in fun_global_list:
                    pass
                else:
                    i.type.declname = newname
            if type(i.init) == c_ast.FuncCall:
                modifyid(i.init, funname, fun_global_list, localval)
                continue
                # print(generator.visit(i))
            elif type(i.init) == c_ast.ID:
                if type(i) == c_ast.FuncCall:
                    # print(st)
                    continue
                elif type(i) == c_ast.StructRef:
                    oldname = i.init.name
                    if oldname in localval:
                        if oldname == i.name.name:
                            if oldname in fun_global_list:
                                pass
                            else:
                                newname = "_" + funname + "_" + oldname + "_"
                                i.init.name = newname
                        elif oldname == i.field.name:
                            pass
                        pass
                else:
                    oldname = i.init.name
                    if oldname in localval:
                        newname = "_" + funname + "_" + oldname + "_"
                        if oldname in fun_global_list:
                            pass
                        else:
                            i.init.name = newname
                        continue
                    else:
                        continue
            elif type(i.init) == c_ast.StructRef:
                # print(i)
                tempnode = i.init
                if type(tempnode.name) == c_ast.StructRef:
                    modifyid(tempnode, funname, fun_global_list, localval)
                    continue
                # print(generator.visit(i))
                oldname = i.init.name.name
                if oldname in localval:
                    if oldname == i.init.name.name:
                        if oldname in fun_global_list:
                            pass
                        else:
                            newname = "_" + funname + "_" + oldname + "_"
                            i.init.name.name = newname
                    elif oldname == st.field.name:
                        pass
                    continue
            elif type(i.init) == c_ast.BinaryOp:
                modifyid(i.init.left, funname, fun_global_list, localval)
                modifyid(i.init.right, funname, fun_global_list, localval)
            elif type(i.init) == c_ast.UnaryOp:
                # print(i)
                # print(generator.visit(i))
                if type(i.init.expr) == c_ast.Constant:
                    continue
                elif type(i.init.expr) == c_ast.StructRef:
                    modifyid(i.init.expr, funname, fun_global_list, localval)
                    continue
                elif type(i.init.expr) == c_ast.ArrayRef:
                    modifyid(i.init.expr, funname, fun_global_list, localval)
                    continue
                elif type(i.init.expr) == c_ast.Cast:
                    modifyid(i.init.expr, funname, fun_global_list, localval)
                    continue
                elif type(i.init.expr) == c_ast.UnaryOp:
                    modifyid(i.init.expr, funname, fun_global_list, localval)
                    continue
                oldname = i.init.expr.name
                # print(oldname)
                if oldname in fun_global_list:
                    pass
                else:
                    if oldname in localval:
                        newname = "_" + funname + "_" + oldname + "_"
                        i.init.expr.name = newname
                    else:
                        pass
                continue
            elif type(i.init) == c_ast.Cast:
                modifyid(i.init, funname, fun_global_list, localval)
                continue
            elif type(i.init) == c_ast.ArrayRef:
                if type(i.init.name) == c_ast.StructRef:
                    modifyid(i.init.name, funname, fun_global_list, localval)
                    continue
                oldname = i.init.name.name
                if oldname in localval:
                    newname = "_" + funname + "_" + oldname + "_"
                    if oldname in fun_global_list:
                        pass
                    else:
                        i.init.name.name = newname
                    continue

            else:
                # print(i.init)
                # print(generator.visit(i.init))
                continue
        elif type(i) == c_ast.ID:
            if i.name in localval:
                # print(st)
                if type(st) == c_ast.FuncCall:
                    # print(st)
                    continue
                elif type(st) == c_ast.StructRef:
                    oldname = i.name
                    if oldname == st.name.name:
                        newname = "_" + funname + "_" + oldname + "_"
                        if oldname in fun_global_list:
                            pass
                        else:
                            i.name = newname
                    elif oldname == st.field.name:
                        pass
                    pass
                else:
                    oldname = i.name
                    newname = "_" + funname + "_" + oldname + "_"
                    if oldname in fun_global_list or oldname in global_funname:
                        pass
                    else:
                        i.name = newname
                    continue
            else:
                pass

        else:

            modifyid(i, funname, fun_global_list, localval)


def find_fun_loop(fst, funname):
    """
    识别出函数中所有的loop，并记录每个loop的起始行号和结束行号
    :param fst: c_ast.FileAST(函数所在的c文件的翻译单元对应的ast)
    :param funname: 字符串（函数名）
    :return: 将识别出的loop添加到全局变量fun_loop字典中
    """
    for i in range(0, len(fst.ext)):
        st = fst.ext[i]
        if type(st) == c_ast.FuncDef and st.decl.name == funname:
            child = st.body
            for sta in child.block_items:
                statype = type(sta)
                if statype == c_ast.For or statype == c_ast.While or statype == c_ast.DoWhile:
                    startline = int(str(sta.coord).split(":")[1])
                    last_num = -1
                    line_list = []
                    get_last_linenum(sta, last_num, line_list)
                    lastline = line_list[0]
                    keyname = str(startline) + ":" + str(lastline)
                    tempdic = {keyname: sta}
                    fun_loop[funname] = []
                    fun_loop[funname].append(tempdic)
                elif statype == c_ast.If or statype == c_ast.Switch or statype == c_ast.Compound:
                    find_loop(sta, funname)
                else:
                    pass
            break


def move_code_endpart(line_ast):
    """
    移动代码，实参形参传递，返回值处理
    :param rdic: 列表（包含父节点，索引，called类型，实参列表）
    :param nextfunname: 被调用函数的函数名
    :param next_ast: 正序，被called函数的部分ast
    :param cur_ast: 正序：主调函数的部分ast
    :param rdic:
    :param nextfunname:
    :param next_ast:
    :param cur_ast:
    :return:
    """
    final_ast = []
    for st in line_ast:
        key_funname = list(st.keys())[0]
        if st == line_ast[0]:
            nextfunname = key_funname
        ast_list = st[key_funname]
        for t in ast_list:
            if st == line_ast[0]:
                final_ast.append(t)
            else:
                if t == ast_list[0]:
                    continue
                elif t == ast_list[1]:
                    rdic = []
                    depth = 0
                    linenum = ast_list[0]
                    isincludefuncall1(t, nextfunname, rdic, depth, linenum, t)
                    if len(rdic) > 0:
                        condtype = rdic[2]
                        ret_name = nextfunname + "_return_"
                        if condtype == 'basic':
                            t.rvalue = c_ast.ID(name=ret_name)
                        else:
                            modif_ret(t, nextfunname, ret_name)
                    final_ast.append(t)
                else:
                    final_ast.append(t)
                nextfunname = key_funname
    return final_ast


def move_code_startpart(rdic, nextfunname, next_ast, cur_ast):
    """
    移动代码，实参形参传递，返回值处理
    :param rdic: 列表（包含父节点，索引，called类型，实参列表）
    :param nextfunname: 被调用函数的函数名
    :param next_ast: 正序，被called函数的部分ast
    :param cur_ast: 正序：主调函数的部分ast
    :return:
    """
    n = 0
    parentnode = rdic[0]
    ind = rdic[1]
    condtype = rdic[2]
    rlist = rdic[3:]
    if parentnode == "null":
        tempast = []
        for decl in fun_decl_dic[nextfunname]:
            tempast.append(decl)
            lname = decl.name
            assign = c_ast.Assignment(op='=', lvalue=c_ast.ID(lname), rvalue=c_ast.ID(rlist[n]))
            tempast.append(assign)
            n = n + 1
        for ele in next_ast:
            tempast.append(ele)
        cur_ast.pop()
        for t in tempast:
            cur_ast.append(t)
        return cur_ast
    else:
        tempsta = parentnode[ind]
        for decl in fun_decl_dic[nextfunname]:
            parentnode.insert(ind, decl)
            ind = ind + 1
            lname = decl.name
            assign = c_ast.Assignment(op='=', lvalue=c_ast.ID(lname), rvalue=c_ast.ID(rlist[n]))
            parentnode.insert(ind, assign)
            ind = ind + 1
            n = n + 1

        for tele in next_ast:
            parentnode.insert(ind, tele)
            ind = ind + 1
        parentnode.remove(tempsta)
        return cur_ast


def re_move_code(rdic, nextfunname, temp_ast, re_po_flag):
    """
    将被调用函数的整个函数内联到主调函数中相应的位置（实参形参赋值，移动called函数的所有语句对应的ast）
    :param rdic: 列表（包含父节点，索引，called类型，实参列表）
    :param nextfunname: 被调用函数的函数名
    :param temp_ast: 对应于called函数的ast
    :return: 返回内联了called函数后的整个父节点
    """
    n = 0
    parentnode = rdic[0]
    print("parentnode")
    # for i in parentnode:
    #     print(generator.visit(i))
    ind = rdic[1]
    print(parentnode)
    print(ind)
    condtype = rdic[2]
    rlist = rdic[3:]
    ret_name = nextfunname + "_return_"
    tempsta = parentnode[ind]
    printst = c_ast.FuncCall(name=c_ast.ID(name="printf"),
                             args=c_ast.ExprList(exprs=[c_ast.Constant(type="string", value='"##\\n"')]))
    parentnode.insert(ind, printst)
    ind = ind + 1
    for decl in fun_decl_dic[nextfunname]:
        parentnode.insert(ind, decl)
        ind = ind + 1
        lname = decl.name
        assign = c_ast.Assignment(op='=', lvalue=c_ast.ID(lname), rvalue=c_ast.ID(rlist[n]))
        parentnode.insert(ind, assign)
        ind = ind + 1
        n = n + 1
    compoundst = c_ast.Compound(block_items=[])

    for tele in temp_ast:
        compoundst.block_items.append(tele)

    parentnode.insert(ind, compoundst)
    ind = ind + 1
    if re_po_flag == "positive":
        parentnode.pop(ind)
    else:
        if condtype == 'basic':
            print("tempsta...")
            print(generator.visit(tempsta))
            if type(tempsta) == c_ast.FuncCall:
                parentnode.remove(tempsta)
            else:
                tempsta.rvalue = c_ast.ID(name=ret_name)
        else:
            modif_ret(tempsta, nextfunname, ret_name)
    print("compundst......2")
    # print(compoundst)
    return compoundst.block_items


def find_called_fun(loopast, linenum, funname, rdic):
    '''
    在主调函数的loop对应的ast中查找是否包含被调called函数
    :param loopast: 主调函数中某一个语句对应的ast
    :param linenum: called函数所在的行号
    :param funname: 被掉clled函数的函数名
    :param rdic: 返回列表，返回的是实参列表相关
    :return:
    '''
    # 获得callend函数的被调用位置pos,被插入的父节点，如何进行插入
    typeloopast = type(loopast)
    if typeloopast == c_ast.For:
        forinit = loopast.init
        funlist = []
        is_have_funcall(funname, forinit, linenum, funlist)
        if len(funlist) > 0:
            print(forinit)

        forcond = loopast.cond
        funlist = []
        is_have_funcall(funname, forcond, linenum, funlist)
        if len(funlist) > 0:
            print(forcond)

        fornext = loopast.next
        funlist = []
        is_have_funcall(funname, fornext, linenum, funlist)
        if len(funlist) > 0:
            print(fornext)

        forstmt = loopast.stmt
        if type(forstmt) == c_ast.Compound:
            pass
        else:
            loopast.stmt = c_ast.Compound(block_items=forstmt)
        newforstmt = loopast.stmt
        for sta in newforstmt.block_items:
            depth = 1
            isincludefuncall1(sta, funname, rdic, depth, linenum, newforstmt.block_items)

    elif typeloopast == c_ast.While or c_ast.DoWhile:
        whstmt = loopast.stmt
        for sta in whstmt.block_items:
            depth = 1
            isincludefuncall1(sta, funname, rdic, depth, linenum, whstmt.block_items)


def deal_global_variable(ast):
    """ Simply use the c_generator module to emit a parsed AST.
    """
    """record all global variable in ast"""
    for func in ast.ext:
        if type(func) == c_ast.Decl and type(func.type) != c_ast.FuncDecl and func.name not in globalv_list:
            globalv_list.append(func.name)
    """record each function's global variable"""
    for fun in ast.ext:
        if type(fun) == c_ast.FuncDef:
            l = []
            fun111 = fun.body.block_items
            if fun111 is None:
                continue
            find_ID(fun111, l)
            global_dic[fun.decl.name] = l


def modifylocalvarible(ast, funname, fun_global_list, return_val):
    """
    在ast上将funname函数进行ssa操作
    :param ast: FileAST(funname所在的文件ast)
    :param funname: string（当前函数的函数名）
    :param fun_global_list:list(每个函数中使用到的全局变量)
    :param return_val:list（）存放为每个函数定义的返回值变量的ast语句
    :return:
    """
    for fun in ast.ext:
        if type(fun) == c_ast.FuncDef and fun.decl.name == funname:
            st = fun
            localval = []
            for s in st:
                modifyid(s, funname, fun_global_list, localval)
            storeFunllDecl(fun, funname)
            deal_return(fun, funname, return_val)
            break
            # print(fun)


def parse_to_ast(ele, return_val):
    """
    根据ele中的文件路径信息，获得对应文件的ast
    :param ele: 基本块（基本块中包含行号等信息）
    :param return_val: list(用于存放在deal_return函数中定义的返回值变量ast语句）
    :return:
    """
    # relabel_list = ele.get("label")[2:-2]
    # relabellist_list = relabel_list.split("\n")
    # print(ele.get_name())
    funname = getfunnmae(ele)
    startline = get_first_lineinfo(ele)  # 取第一行
    rindex = startline.rfind(":")
    rslash = startline.rfind("/")
    filename = startline[rslash + 1:rindex]
    pathname1 = startline[:rindex]
    fpath = startline[:rslash]
    fake_include = "../../utils/fake_libc_include"
    abs_fake_include = os.path.abspath(fake_include)
    if filename in dir_ast.keys():
        tempast = dir_ast[filename]
        if funname in Ismodifyloclavarible:
            if funname in global_return_decl.keys():
                return_val.append(global_return_decl[funname])
            pass
        else:
            fun_global_list = global_dic[funname]
            modifylocalvarible(tempast, funname, fun_global_list, return_val)
            find_fun_loop(tempast, funname)
            Ismodifyloclavarible.append(funname)
    else:
        command1 = "cd " + fpath + ";gcc -E " + pathname1 + " -I../crypto -I.. -I../include -I" + abs_fake_include + " " \
                                                                                                                     "-DOPENSSL_THREADS -D_REENTRANT -DDSO_DLFCN -DHAVE_DLFCN_H -m64 -DL_ENDIAN " \
                                                                                                                     "-DTERMIO -DOPENSSL_IA32_SSE2 -DOPENSSL_BN_ASM_MONT -DOPENSSL_BN_ASM_MONT5 -DOPENSSL_BN_ASM_GF2m -DSHA1_ASM" \
                                                                                                                     "-DSHA256_ASM -DSHA512_ASM -DMD5_ASM -DAES_ASM -DVPAES_ASM -DBSAES_ASM -DWHIRLPOOL_ASM -DGHASH_ASM >>fun1"

        (status, output) = subprocess.getstatusoutput(command1)
        if status == 0:
            # print(fpath + '/fun1')
            tempast = parse_file(fpath + '/fun1', use_cpp=True)

            """
            获取ele所在的c文件名
            判断此文件是否是路径中的最后一个c文件名
            调用entry_createxml()
            """
            # if is_gen_xml:
            #     entry_createxml(tempast, False, None)
            deal_global_variable(tempast)
            # 对两个函数进行ssa修改
            fun2_global_list = global_dic[funname]

            modifylocalvarible(tempast, funname, fun2_global_list, return_val)
            find_fun_loop(tempast, funname)
            Ismodifyloclavarible.append(funname)
            dir_ast[filename] = tempast
            os.remove(fpath + '/fun1')
    retast = copy.deepcopy(tempast)
    return retast


def notloop_move(linenum, next_ast, ele, re_po_flag, return_val):
    """
    不是loop类型的移动，将所有called函数内联到主调函数中相应的位置
    :param linenum: called函数在主调函数中的行号
    :param next_ast: 对应于主调函数的ast
    :param ele: called函数中的一个基本块节点
    :dfa_srcvarname:list(use to store src's varname)
    :is_srcpart:bool(use to judge whether block belong to srcpart(oppsite is sinkpart))
    :dfa_srcline:int (represent the linenume that src in)
    :return:
    """
    tempast = parse_to_ast(ele, return_val)
    funname = getfunnmae(ele)
    for ext1 in tempast.ext:
        if type(ext1) == c_ast.FuncDef and ext1.decl.name == funname:
            next_ast1 = ext1.body.block_items
            for i in next_ast:
                rdic = []
                depth = 1
                isincludefuncall1(i, funname, rdic, depth, linenum, next_ast)
                if len(rdic) > 0:
                    compundst = re_move_code(rdic, funname, next_ast1, re_po_flag)
                    return compundst


def get_bb_last_num(bbnode, funname):
    """
    :param bbnode: 一个基本块
    :param funname: called函数
    :return: clled函数所在的行号
    """
    bblabel = bbnode.get("label")[2:-2]
    bblabel_list = bblabel.split("\n")
    bblabel_linenum = 0
    callinst = bblabel_list[-2]
    lineinfo = bblabel_list[-3]
    if 'call' in callinst and funname in callinst:
        ind = lineinfo.index(":")
        bblabel_linenum = int(lineinfo[ind + 1:-2])
    return bblabel_linenum


def split_path_start(blocknamelist, split_pathlist):
    """
    将路径列表拆分成倒序和正序，以_end为标识
    :param blocknamelist: 基本块名字列表
    :param split_pathlist: 包含倒序的子区间
    :return:
    """
    newblocknamelist = []
    for bb in blocknamelist:
        newblocknamelist.append(bb)
    end = len(blocknamelist) - 1
    print(end)
    start = end
    newblocknamelist.reverse()
    for p in newblocknamelist:
        print(p)
        if p.endswith("_start"):
            templist = [start + 1, end]
            split_pathlist.append(templist)
            end = start
            start = start - 1
        elif p.endswith("_end"):
            templist = [start + 1, end]
            split_pathlist.append(templist)
            break
        else:
            start = start - 1
    split_pathlist.reverse()


def split_path_end(blocknamelist, split_pathlist):
    """
    将路径列表拆分成倒序和正序，以_end为标识
    :param blocknamelist: 基本块名字列表
    :param split_pathlist: 包含倒序的子区间
    :return:
    """
    start = 0
    end = start
    for p in blocknamelist:
        # print(p)
        if p.endswith("_end"):
            templist = [start, end]
            split_pathlist.append(templist)
            end = end + 1
            start = end
        elif p.endswith("_start"):
            templist = [start, end]
            split_pathlist.append(templist)
            break
        else:
            end = end + 1


def deal_recur(list3, prefunname, param_list, return_val):
    firstele = list3[0]
    firsfunname = getfunnmae(firstele)
    if firsfunname != prefunname:
        print("recur continue....")
        for ele in list3:
            print(ele.get_name())
    else:
        tempast = parse_to_ast(firstele, return_val)
        funname = getfunnmae(firstele)
        for ext1 in tempast.ext:
            if type(ext1) == c_ast.FuncDef and ext1.decl.name == funname:
                # deal_return(ext1, funname)
                funast = copy.deepcopy(ext1)

                for i in funast.decl.type.args.params:
                    param_list.append(i)

                """
                在funbody中找到dfa_srcline且memcpy
                得到memcpyast
                传递memcpyast获得varname
                """
                return funast.body


def loop_move_part_positive_order(partlist, pathlist, callerast, re_po_flag, return_val):
    """
    将整个路径分成end部分与start部分，此函数顺序移动，，处理的是start部分，将所有被调用函数移动到loop中
    :param partlist: 正序部分的块名字的list（start部分）
    :param pathlist: 路径，包含所有基本块
    :param callerast:
    :return:
    """
    blocknamelist = []
    for i in pathlist:
        bbname = i.get_name()
        blocknamelist.append(bbname)
    print(partlist)
    part = partlist[0]
    start1 = part[0]
    callerele = pathlist[start1]
    callerfunname = getfunnmae(callerele)
    if type(callerast) == c_ast.Compound:
        next_ast = callerast.block_items
    else:
        next_ast = callerast.stmt.block_items

    for t in partlist:
        if t == partlist[-1]:
            break
        startind = t[0]
        endind = t[1]
        part_path1 = pathlist[startind:endind + 1]
        next_ele1 = pathlist[endind + 1]
        calledfunname = getfunnmae(next_ele1)
        templist = []
        get_bb_linenum(part_path1, calledfunname, templist, blocknamelist)
        if len(templist) > 0:
            linenum = templist[0]
            print("lineum.....1")
            print(calledfunname)
            print(linenum)
            calledele = pathlist[endind + 1]
            next_ast = notloop_move(linenum, next_ast, calledele, re_po_flag, return_val)


def deal_end_part(pathlist, startline, ret_list, param_list, callerast, gotolabel, labeldefine,
                  return_val):
    """
    对最终路径的endpart部分进行处理（将每条路径根据end和start标识分成不同的区间，endpart部分包含第一区间到end与start之间的区间）
    :param pathlist: 列表（包含第一区间到end与start之间的区间的一条子路径）
    :param startline: int,source的行号
    :param endline: int,sink的行号
    :param ret_list: list,返回list，第一个元素为拆分end与start区间的索引，第二个元素为整个endpart段的所有ast组成的列表（已经处理好移动关系）
    :return:无
    """
    line_ast = []
    bblocklist = []
    for i in pathlist:
        bbname = i.get_name()
        bblocklist.append(bbname)
        print(bbname)
    split_path = []
    split_path_end(bblocklist, split_path)
    for part in split_path:
        start = part[0]
        end = part[-1]
        partpath = pathlist[start:end + 1]
        startele = partpath[0]
        callerfunname = getfunnmae(startele)
        ast = parse_to_ast(startele, return_val)
        tempast = []
        fun_ast_map = {callerfunname: tempast}
        # if part==split_path[0] and callerast is not None:
        #     tempast.append(callerast)
        varlist = []
        for ext1 in ast.ext:
            if type(ext1) == c_ast.FuncDef and ext1.decl.name == callerfunname:
                # deal_return(ext1, callerfunname)
                funast = copy.deepcopy(ext1)
                break
        bodyast = funast.body
        inc_linenum = []
        split_flag = False
        for ele in partpath:
            if ele.get_name().endswith("_end"):
                labelname = callerfunname + "_label_"
                labelst = c_ast.Label(name=labelname,
                                      stmt=c_ast.FuncCall(name=c_ast.ID(name="printf"), args=c_ast.ExprList(
                                          exprs=[c_ast.Constant(type="string", value='"##\\n"')])))
                tempast.append(labelst)
                labeldefine.append(labelname)
                break
            if split_flag:
                break
            bbname = ele.get_name()
            lineinfo_list1 = get_lineinfo_sort(ele)
            if part != split_path[0] and ele == partpath[0]:
                lineinfo_list = [get_last_lineinfo(ele)]
                nnlabel = ele.get("label")[2:-2]
                labellist = nnlabel.split("\n")
                for i in labellist:
                    print(i)
                print(lineinfo_list[0])
                linenum = get_per_linenum(lineinfo_list[0])
                print("linenum.....943")
                print(linenum)
                if len(tempast) == 0:
                    tempast.append(linenum)
                else:
                    tempast.insert(0, linenum)
            else:
                lineinfo_list = lineinfo_list1

            for line in lineinfo_list:
                linenum = get_per_linenum(line)
                if part == split_path[-1]:
                    if ele != partpath[0]:
                        pre_inc_linenum = inc_linenum[0]
                        print("pre_inc_linenum......957")
                        print(pre_inc_linenum)
                        if linenum > pre_inc_linenum:
                            ind = partpath.index(ele)
                            splitindex = start + ind
                            inc_line = pre_inc_linenum
                            split_flag = True
                            break
                if len(inc_linenum) > 0 and linenum <= inc_linenum[0]:
                    continue
                if part == split_path[0] and linenum < startline:
                    continue
                findflag = [False]
                recurfindline(bodyast, linenum, bbname, bblocklist, varlist, tempast, inc_linenum, gotolabel,
                              labeldefine, findflag)
                if findflag[0] is False:
                    find_in_return(linenum, tempast, callerfunname, varlist, inc_linenum)
        for va in varlist:
            flg = False
            finddecl(funast.decl, va, param_list, flg)
            if flg is False:
                finddecl(funast.body, va, param_list, flg)

        line_ast.append(fun_ast_map)
    print("line ast....976")
    for t in line_ast:
        print(t)
    final_ast = move_code_endpart(line_ast)
    ret_list.append(splitindex)
    ret_list.append(final_ast)
    ret_list.append(inc_line)


def find_loopid(st, varlist):
    """
    在loop（loop的ast）中找到使用的变量
    :param st:c_ast类型的ast(loop)
    :param varlist:列表（用于存放找到的string类型的变量）
    :return:无
    """
    if type(st) == c_ast.Decl:
        if st.init is not None:
            findid(st.init, varlist)
        else:
            return
    if type(st) == c_ast.ID:
        idname = st.name
        if idname in varlist:
            pass
        else:
            varlist.append(idname)
    else:
        for i in st:
            if i is None:
                continue
            elif type(i) == c_ast.Decl:
                if i.init is not None:
                    findid(st.init, varlist)
                else:
                    continue
            elif type(i) == c_ast.ID and type(st) != c_ast.FuncCall:
                idname = i.name
                if idname in varlist:
                    continue
                else:
                    varlist.append(idname)
            else:
                findid(i, varlist)


def findid(st, varlist):
    """
    找出st（ast节点）中使用到的变量
    :param st:c_ast类型的ast节点
    :param varlist:列表（用于存放为找到的tring类型的变量面）
    :return:无
    """
    if type(st) == c_ast.ID:
        idname = st.name
        if idname in varlist:
            return
        elif idname.endswith("_return_"):
            return
        else:
            varlist.append(idname)
            return
    for i in st:
        if (i == None):
            break
        elif type(i) == c_ast.ID and type(st) != c_ast.FuncCall:
            idname = i.name
            if idname in varlist:
                continue
            elif idname.endswith("_return_"):
                continue
            else:
                varlist.append(idname)
        else:
            findid(i, varlist)


def recurfindline(bodyast, line, blockname, blocknamelist, varlist, tempast, inc_linenum, gotolabel, labeldefine,
                  findflag):
    """
    根据给定行号，递归的在函数体中找到行号对应的最大的ast
    :param bodyast: c_ast类型的节点，初始的时候为函数体对应的bodyast，之后为每条c语句对应的ast
    :param line: int,行号
    :param blockname: string,基本块的name
    :param blocknamelist: list列表，基本块name对应的列表
    :param varlist: list列表（元素为string便令名，表示应该放到生成函数的参数列表中的变量）
    :param tempast:list列表（用于存放找到的对于与行号的ast）
    :param inc_linenum: 列表（拥有唯一的元素，表示已经处理过的ast中的最大的行号）
    :return: 将找到的ast添加到tempast之后
    """
    # print(str(bodyast.coord)+"11")
    if bodyast.coord is not None:
        stcoord = str(bodyast.coord)
        index1 = stcoord.index(":")
        rindex1 = stcoord.rindex(":")
        templine = int(stcoord[index1 + 1:rindex1])
        if templine > line:
            return
    if str(line) in str(bodyast.coord):
        print(str(bodyast.coord))
        print("find##2")
        index = blockname.index('BB')
        funn = 'BB' + blockname[:index] + '_start'
        lastnum = -1
        get_last_linenum(bodyast, lastnum, inc_linenum)
        if funn in blocknamelist:
            pass
        elif type(bodyast) == c_ast.Decl:
            pass
        else:
            findid(bodyast, varlist)
        find_goto_balel(bodyast, gotolabel, labeldefine)
        tempast.append(bodyast)
        findflag[0] = True
        return
    # print("linenum:" + str(line))
    for c in bodyast:
        if type(c) == c_ast.Compound or type(c) == c_ast.For or type(c) == c_ast.While or type(
                c) == c_ast.DoWhile or type(c) == c_ast.Label or type(c) \
                == c_ast.Switch or type(c) == c_ast.Case or type(c) == c_ast.Default or type(c) == c_ast.If:
            if str(line) in str(c.coord):
                print(str(c.coord))
                print("find##1")
                index = blockname.index('BB')
                funn = 'BB' + blockname[:index] + '_start'
                lastnum = -1
                get_last_linenum(c, lastnum, inc_linenum)
                # 判断何时需要将声明记录到para_list
                if funn in blocknamelist:
                    pass
                elif type(c) == c_ast.Decl:
                    pass
                else:
                    findid(c, varlist)
                find_goto_balel(c, gotolabel, labeldefine)
                tempast.append(c)
                findflag[0] = True
                return
            else:
                recurfindline(c, line, blockname, blocknamelist, varlist, tempast, inc_linenum, gotolabel, labeldefine,
                              findflag)
        else:
            if str(line) in str(c.coord):
                print(str(c.coord))
                print("find###")
                index = blockname.index('BB')
                funn = 'BB' + blockname[:index] + '_start'
                lastnum = -1
                get_last_linenum(c, lastnum, inc_linenum)
                # 判断何时需要将声明记录到para_list
                if funn in blocknamelist:
                    pass
                elif type(c) == c_ast.Decl:
                    pass
                else:
                    findid(c, varlist)
                find_goto_balel(c, gotolabel, labeldefine)
                tempast.append(c)
                findflag[0] = True
                if type(c) == c_ast.Decl:
                    pass
                else:
                    return
            else:
                continue


def judge_ishaveend(blocknamelist):
    """
    判断路径中是否有end类型的节点
    :param blocknamelist:列表（元素为string类型，代表基本块的函数名）
    :return:bool值
    """
    end_flag = False
    for b in blocknamelist:
        if b.endswith("_end"):
            end_flag = True
            break
    return end_flag


def judge_isend_start(bblist):
    """
    判断路径中是否存在end节点与start节点只相差一个基本块的子区间
    :param bblist: 列表（元素为string类型，代表基本块的函数名）
    :return: 列表（列表可能为空，可能包含找到的子区间）
    """
    ret_list = []
    split_pathlist = []
    split_path_pos(bblist, split_pathlist)
    for part in split_pathlist:
        if part == split_pathlist[0]:
            continue
        start = part[0]
        end = part[1]
        if bblist[start - 1].endswith("_end") and bblist[end].endswith("_start"):
            ret_list.append(part)
            break
    return ret_list


def judge_ishave_min_end_start(bblist):
    """
    判断路径中是否存在end节点与start节点只相差一个基本块的子区间
    :param bblist: 列表（元素为string类型，代表基本块的函数名）
    :return: 列表（列表可能为空，可能包含找到的子区间）
    """
    ret_list = []
    split_pathlist = []
    split_path_pos(bblist, split_pathlist)
    for part in split_pathlist:
        if part == split_pathlist[0]:
            continue
        start = part[0]
        end = part[1]
        if start + 1 == end:
            if bblist[start - 1].endswith("_end") and bblist[end].endswith("_start"):
                ret_list.append(part)
                break
    return ret_list


def judge_recur(pathlist, subpart):
    """
    判断路径的类型是否为递归
    :param pathlist: 列表（路径：包含所有最终路径的基本块）
    :param subpart: 列表（其元素为end与start之间只相差一个元素的子区间的起始索引与终止索引）
    :return:bool值
    """
    recur_flag = False
    start = subpart[0]

    preele = pathlist[start - 1]
    startele = pathlist[start]
    prefunname = getfunnmae(preele)
    startfunname = getfunnmae(startele)
    if prefunname == startfunname:
        recur_flag = True
    return recur_flag


def find_goto_balel(st, gotolabel, labeldefine):
    if type(st) == c_ast.Goto and st.name not in gotolabel:
        gotolabel.append(st.name)
        return
    elif type(st) == c_ast.Label and st.name not in labeldefine:
        labeldefine.append(st.name)
        find_goto_balel(st.stmt, gotolabel, labeldefine)
        return
    elif type(st) == c_ast.If or type(st) == c_ast.For or type(st) == c_ast.While or type(st) == c_ast.DoWhile \
            or type(st) == c_ast.Compound or type(st) == c_ast.Switch or type(st) == c_ast.Case or type(
        st) == c_ast.Default:
        for t in st:
            find_goto_balel(t, gotolabel, labeldefine)
    else:
        pass


def deal_reverse_loop(pathlist, param_list, gotolabel, labeldefine, return_val):
    """
    对于路径中有end节点的情况，判断路径中的endpart部分是否有loop，如果有loop，进行代码移动操作,
    并根据loop所在的位置对路径进行拆分，返回5种不同种类的拆分情况
    :param pathlist:列表（包含end节点的路径，元素是一些pydot 节点）
    :param param_list:列表（用来存放生成函数的参数）
    :return: retlist列表（元素为种类，拆分后的列表）
    """
    print("deal_reverse_loop start...")
    blocknamelist = []
    for pp in pathlist:
        ppname = pp.get_name()
        blocknamelist.append(ppname)
    endlist = []
    split_path_end(blocknamelist, endlist)
    isloop = False
    split_flag = False
    is_first_part = False
    if len(endlist) > 0:  # endlist不为空
        endlist.reverse()  # 逆转endlist
        len_endlist = len(endlist)
        for part in endlist:
            index_part = endlist.index(part)
            len_sub_endlist = len_endlist - index_part
            print("part....")
            print(part)
            '''解析c文件获取ast'''
            varlist = []
            if part == endlist[-1]:
                break
            start = part[0]
            end = part[1]
            partpath = pathlist[start: end + 1]
            called_ele = pathlist[start - 1]
            called_funname = getfunnmae(called_ele)
            # 判断callend函数所在的基本块和行号
            ret_list = []
            get_bb_linenum_inloop(partpath, called_funname, ret_list, blocknamelist)
            if len(ret_list) > 0:
                linenum = ret_list[0]
                """将loop所在的part拆分成两部分"""
                splitindex = ret_list[1]
                curele = pathlist[splitindex]
                # 判断called函数的行号是否在loop中
                loop_list = []
                tempast = parse_to_ast(curele, return_val)
                curfunname = getfunnmae(curele)
                isloop = judge_line_inloop(curfunname, linenum, loop_list)
                if isloop:
                    """
                    获得正在处理的元素索引
                    获得正在处理的元素在子区间的索引
                    判断子区间中剩余的其他元素是否在大loop中"""
                    print("haveloop.......")
                    # print(loop_list)

                    """
                    获得c文件名，将函数信息，文件添加到相应的列表中
                    """
                    print(generator.visit(loop_list[0]))
                    find_loopid(loop_list[0], varlist)
                    if part == endlist[0]:
                        is_first_part = True
                    subpart_ele_index = ret_list[2]
                    loop_range = loop_list[1]
                    loop_start = int(loop_range[0])
                    loop_end = int(loop_range[1])
                    int_loop_range = list(range(loop_start, loop_end + 1))
                    bbele = pathlist[start - 2]  # 上一个区间中的元素
                    move_flag = "reverse"
                    find_goto_balel(loop_list[0], gotolabel, labeldefine)
                    next_ast = loop_move(loop_list[0], linenum, bbele, move_flag, return_val)
                    # print("next_ast.....")
                    # for st in next_ast:
                    #     print(generator.visit(st))
                    if part == endlist[-2]:
                        pass
                    else:
                        curind = endlist.index(part)
                        tunc_list = endlist[curind + 1:]

                        # 非loop移动
                        for t in tunc_list:
                            print("tunc_list large than one...")
                            if t == tunc_list[-1]:
                                break
                            print("tunc list...")
                            print(tunc_list)
                            startind = t[0]
                            endind = t[1]
                            part_path1 = pathlist[startind:endind + 1]
                            pre_ele1 = pathlist[startind - 1]
                            funname = getfunnmae(pre_ele1)
                            print(funname)
                            templist = []
                            get_bb_linenum(part_path1, funname, templist, blocknamelist)
                            if len(templist) > 0:
                                linenum = templist[0]
                                bbele = pathlist[startind - 2]

                                mvflag = "reverse"

                                next_ast = notloop_move(linenum, next_ast, bbele, mvflag, return_val)
                    new_start = start + subpart_ele_index + 1
                    newpart_pathlist = pathlist[new_start:end + 1]

                    print("paele_linenum....")
                    for paele in newpart_pathlist:
                        if paele.get_name().endswith("_start") or paele.get_name().endswith("_end"):
                            continue
                        paele_linenum = getlinenum(paele)
                        print(paele_linenum)
                        print(int_loop_range)
                        if int(paele_linenum) in int_loop_range:
                            continue
                        else:
                            ret_index = blocknamelist.index(paele.get_name())
                            split_flag = True
                            break
                    if split_flag is False:
                        ret_index = end + 1

                    for ext1 in tempast.ext:
                        if type(ext1) == c_ast.FuncDef and ext1.decl.name == curfunname:
                            for va in varlist:
                                flg = False
                                finddecl(ext1.decl, va, param_list, flg)
                                if flg == False:
                                    finddecl(ext1.body, va, param_list, flg)
                    break
    retlist = []
    if isloop:
        if is_first_part and split_flag is False:
            """说明倒序且逆序，需要在下一个段中找到被调用的行号"""
            retlist.append("one")
            retlist.append(pathlist[ret_index:])
            retlist.append(loop_list[0])
        elif is_first_part and split_flag:
            """按照剩余部分当成startpart处理"""
            retlist.append("two")
            retlist.append(pathlist[ret_index:])
            retlist.append(loop_list[0])
        elif is_first_part is False and split_flag:
            """剩余部分可以分为endpart和start部分进行处理"""
            retlist.append("three")
            retlist.append(pathlist[ret_index:])
            retlist.append(loop_list[0])
        elif is_first_part is False and split_flag is False:
            retlist.append("four")
    else:
        retlist.append("five")
        retlist.append(pathlist)
    return retlist


def gen_code_entry(pathlist, startline, endline, outfile, genfunname, return_val, srcinfo):
    """
    代码生成的入口,将路径分成不同种类，每种不同的路径调用不同的接口进行处理
    1.路径当中没有end节点，source所在的深度为0，直接调用deal_start进行处理
    2.对于有end节点的路径，首先判断end节点与start节点之间只相差一个基本块，
    只相差一个基本块可分为下面几种类型：
        （1）递归:调用deal_recur
        （2）source节点和sink节点在相同的函数中，调用loop_same_source_sink
        （3）不合理的路径（排除）
    end节点和start节点之间相差多个基本块可分为下面几种类型：
        （1）深度为0的区间当中包含loop，此loop调用source和sink所在函数（对应“one”）:处理loop，然后移动代码
        （2）深度为0的区间当中包含loop，此loop调用source所在函数但没有调用sink所在函数（对应“two”）：处理loop，
        剩余部分按照startpart进行处理（调用deal_startpart）
        （3）调用source所在的函数的代码块在一个loop中，但是这个函数所在的区间不是深度为0的（对应“three”）:处理loop，
        剩余部分分成endpart和startpart进行处理
        （4）source所在点没有被任何loop代码块调用，sink点有可能loop，也可能没有(对应“five”)：
        直接将路径分成endpart和startpart进行处理
    :param pathlist: 列表（路径：包含所有最终路径的基本块）
    :param startline: int整数（source行号）
    :param endline: int整数（sink行号）
    :param outfile: string字符串（生成函数存放的路径名）
    :param genfunname:string字符串（生成函数的函数名）
    :srcinfo: None或者list[src_file,src_line]
    :return:无
    """
    split_pathlist = []
    bblist = []
    param_list = []
    gotolabel = []
    labeldefine = []

    for bb in pathlist:
        bbname = bb.get_name()
        bblist.append(bbname)
    split_path_pos(bblist, split_pathlist)
    """
    1.首先判断一条路径是否拥有end节点
    """
    end_flag = judge_ishaveend(bblist)
    if end_flag:
        """
        路径当中包含end节点
        2.判断路径中是否包含end节点与start节点之间只包含一个元素的区间
        """
        end_start_part = judge_ishave_min_end_start(bblist)
        if len(end_start_part) > 0:
            """
            拥有end节点与start节点之间只包含一个元素的区间  
            4.判断路径是否是递归
            """
            recur_flag = judge_recur(pathlist, end_start_part[0])  ##first
            if recur_flag:
                """递归类型处理"""
                start = end_start_part[0][0]
                preele = pathlist[start - 1]
                prefunname = getfunnmae(preele)
                re_po_flag = "positive"
                """
                目前只支持在src所在的函数为递归函数
                """

                recurast = deal_recur(pathlist, prefunname, param_list, return_val)
                callerast = recurast
                sub_split_path = []
                split_path_start(bblist, sub_split_path)
                flag = "reverse"
                print(split_pathlist)
                templist = sub_split_path[1:]
                loop_move_part_positive_order(templist, pathlist, callerast, flag, return_val)
                fundef = getfundef()
                fundef.ext[0].decl.name = genfunname
                fundef.ext[0].decl.type.type.declname = genfunname
                funparam = fundef.ext[0].decl.type.args.params
                funparam.pop()
                temp_param = []
                temp_name = []
                for p in param_list:
                    if p.name in temp_name:
                        continue
                    else:
                        temp_param.append(p)
                        temp_name.append(p.name)
                for p in temp_param:
                    if p.init != None:
                        vardecl = c_ast.Decl(quals='', name=p.name, type=p.type, storage='', funcspec='', init=None,
                                             bitsize=None)
                        funparam.append(vardecl)
                        continue
                    funparam.append(p)
                temp_ret_name = []
                for p in return_val:
                    if p.name in temp_ret_name:
                        continue
                    else:
                        funparam.append(p)
                        temp_ret_name.append(p.name)

                fundef.ext[0].body.block_items = []
                fundef.ext[0].body.block_items.append(callerast)
                for ele in gotolabel:
                    if ele in labeldefine:
                        continue
                    else:
                        labelst = c_ast.Label(name=ele,
                                              stmt=c_ast.FuncCall(name=c_ast.ID(name="printf"), args=c_ast.ExprList(
                                                  exprs=[c_ast.Constant(type="string", value='"##\\n"')])))
                        fundef.ext[0].body.block_items.append(labelst)
                c_file = open(outfile, "w")
                c_file.write(generator.visit(fundef))
                c_file.close()


            else:
                """
                3.判断路径是否应该被排除
                5.判断路径是否是同一个source同一个sink
                """
                print("minmum part call deal_reverse_loop..")
                rloop_list = deal_reverse_loop(pathlist, param_list, gotolabel, labeldefine, return_val)
                if len(rloop_list) > 2:
                    print("ninmum part...")
                    print(generator.visit(rloop_list[2]))
                if rloop_list[0] == "one":
                    """is_first_part and split_flag is False"""
                    subpathlist = rloop_list[1]
                    callerast = rloop_list[2]
                    sub_split_path = []
                    split_path_start(bblist, sub_split_path)
                    flag = "reverse"
                    print(split_pathlist)
                    templist = sub_split_path[1:]
                    loop_move_part_positive_order(templist, pathlist, callerast, flag, return_val)

                    fundef = getfundef()
                    fundef.ext[0].decl.name = genfunname
                    fundef.ext[0].decl.type.type.declname = genfunname
                    funparam = fundef.ext[0].decl.type.args.params
                    funparam.pop()
                    temp_param = []
                    temp_name = []
                    for p in param_list:
                        if p.name in temp_name:
                            continue
                        else:
                            temp_param.append(p)
                            temp_name.append(p.name)
                    for p in temp_param:
                        if p.init != None:
                            vardecl = c_ast.Decl(quals='', name=p.name, type=p.type, storage='', funcspec='', init=None,
                                                 bitsize=None)
                            funparam.append(vardecl)
                            continue
                        funparam.append(p)
                    temp_ret_name = []
                    for p in return_val:
                        if p.name in temp_name:
                            continue
                        else:
                            funparam.append(p)
                            temp_ret_name.append(p.name)

                    fundef.ext[0].body.block_items = []
                    fundef.ext[0].body.block_items.append(callerast)
                    for ele in gotolabel:
                        if ele in labeldefine:
                            continue
                        else:
                            labelst = c_ast.Label(name=ele,
                                                  stmt=c_ast.FuncCall(name=c_ast.ID(name="printf"), args=c_ast.ExprList(
                                                      exprs=[c_ast.Constant(type="string", value='"##\\n"')])))
                            fundef.ext[0].body.block_items.append(labelst)
                    c_file = open(outfile, "w")
                    c_file.write(generator.visit(fundef))
                    c_file.close()
                else:
                    return
        else:
            """
            判断有没有大loop
            分段进行处理
            """
            endstart_part = judge_isend_start(bblist)
            e_start = endstart_part[0][0]
            e_end = endstart_part[0][1]
            e_start_ele = pathlist[e_start - 1]
            e_end_ele = pathlist[e_end]
            e_start_funname = getfunnmae(e_start_ele)
            e_end_funname = getfunnmae(e_end_ele)
            if e_start_funname == e_end_funname:
                """source和sink同一个函数中，且这个函数被一个loop调用"""
                print("source and sink in a loop...")
                rloop_list = deal_reverse_loop(pathlist, param_list, gotolabel, labeldefine, return_val)
                if len(rloop_list) > 2:
                    print(generator.visit(rloop_list[2]))
                if rloop_list[0] == "one":
                    """is_first_part and split_flag is False"""

                    subpathlist = rloop_list[1]
                    callerast = rloop_list[2]
                    sub_split_path = []
                    split_path_start(bblist, sub_split_path)
                    flag = "reverse"
                    print(split_pathlist)
                    templist = sub_split_path[1:]
                    loop_move_part_positive_order(templist, pathlist, callerast, flag, return_val)

                    fundef = getfundef()
                    fundef.ext[0].decl.name = genfunname
                    fundef.ext[0].decl.type.type.declname = genfunname
                    funparam = fundef.ext[0].decl.type.args.params
                    funparam.pop()
                    temp_param = []
                    for p in param_list:
                        if p in temp_param:
                            continue
                        else:
                            temp_param.append(p)
                    for p in temp_param:
                        if p.init != None:
                            vardecl = c_ast.Decl(quals='', name=p.name, type=p.type, storage='', funcspec='', init=None,
                                                 bitsize=None)
                            funparam.append(vardecl)
                            continue
                        funparam.append(p)
                    temp_ret_name = []
                    for p in return_val:
                        if p.name in temp_ret_name:
                            continue
                        else:
                            funparam.append(p)
                            temp_ret_name.append(p.name)

                    fundef.ext[0].body.block_items = []
                    fundef.ext[0].body.block_items.append(callerast)
                    for ele in gotolabel:
                        if ele in labeldefine:
                            continue
                        else:
                            labelst = c_ast.Label(name=ele,
                                                  stmt=c_ast.FuncCall(name=c_ast.ID(name="printf"), args=c_ast.ExprList(
                                                      exprs=[c_ast.Constant(type="string", value='"##\\n"')])))
                            fundef.ext[0].body.block_items.append(labelst)
                    c_file = open(outfile, "w")
                    c_file.write(generator.visit(fundef))
                    c_file.close()
            else:
                print("ordinary source and sink....")
                rloop_list = deal_reverse_loop(pathlist, param_list, gotolabel, labeldefine, return_val)
                # if len(rloop_list) > 2:
                #     print(generator.visit(rloop_list[2]))
                if rloop_list[0] == "one":
                    """is_first_part and split_flag is False"""

                    subpathlist = rloop_list[1]
                    callerast = rloop_list[2]
                    sub_split_path = []
                    split_path_start(bblist, sub_split_path)
                    flag = "reverse"
                    print(split_pathlist)
                    loop_move_part_positive_order(sub_split_path, pathlist, callerast, flag, return_val)

                    fundef = getfundef()
                    fundef.ext[0].decl.name = genfunname
                    fundef.ext[0].decl.type.type.declname = genfunname
                    funparam = fundef.ext[0].decl.type.args.params
                    funparam.pop()
                    temp_param = []
                    temp_name = []
                    for p in param_list:
                        if p.name in temp_name:
                            continue
                        else:
                            temp_param.append(p)
                            temp_name.append(p.name)
                    for p in temp_param:
                        if p.init != None:
                            vardecl = c_ast.Decl(quals='', name=p.name, type=p.type, storage='', funcspec='', init=None,
                                                 bitsize=None)
                            funparam.append(vardecl)
                            continue
                        funparam.append(p)
                    temp_return_name = []
                    for p in return_val:
                        if p.name in temp_return_name:
                            continue
                        else:
                            funparam.append(p)
                            temp_return_name.append(p.name)

                    fundef.ext[0].body.block_items = []
                    fundef.ext[0].body.block_items.append(callerast)
                    for ele in gotolabel:
                        if ele in labeldefine:
                            continue
                        else:
                            labelst = c_ast.Label(name=ele,
                                                  stmt=c_ast.FuncCall(name=c_ast.ID(name="printf"), args=c_ast.ExprList(
                                                      exprs=[c_ast.Constant(type="string", value='"##\\n"')])))
                            fundef.ext[0].body.block_items.append(labelst)
                    c_file = open(outfile, "w")
                    c_file.write(generator.visit(fundef))
                    c_file.close()
                elif rloop_list[0] == "two":
                    """is_first_part and split_flag"""

                    startpathlist = rloop_list[1]
                    startlinenum = 0
                    callerast = rloop_list[2]
                    dealed_ast = [callerast]
                    line_ast = []
                    deal_start_part(bblist, startpathlist, startlinenum, endline, dealed_ast, line_ast, param_list,
                                    None, gotolabel, labeldefine, return_val)
                    line_ast.reverse()
                    gen_final_startpart(line_ast, outfile, genfunname, param_list, gotolabel, labeldefine, return_val)
                elif rloop_list[0] == "three":
                    """is_first_part is False and split_flag"""

                    subpathlist = rloop_list[1]
                    callerast = rloop_list[2]
                    subbblist = []
                    starline = 0
                    for i in subpathlist:
                        bbname = i.get_name()
                        subbblist.append(bbname)
                    split_endlist = []
                    split_path_end(subbblist, split_endlist)
                    start = split_endlist[0][0]
                    end = split_endlist[-1][-1]
                    endpathlist = subpathlist[start:end + 1]
                    dep_list = []
                    deal_end_part(endpathlist, starline, dep_list, param_list, callerast, gotolabel, labeldefine,
                                  return_val)
                    if len(dep_list) > 0:
                        split_index = dep_list[0]
                        startpathlist = subpathlist[split_index:]
                        startlinenum = 0
                        endpart_astlist = dep_list[1]
                        endpart_astlist.insert(0, callerast)
                        line_ast = []
                        inc_line = dep_list[2]
                        deal_start_part(bblist, startpathlist, startlinenum, endline, endpart_astlist, line_ast,
                                        param_list,
                                        inc_line, gotolabel, labeldefine, return_val)
                        print("line ast...")
                        for t in line_ast:
                            print(t)
                        line_ast.reverse()
                        gen_final_startpart(line_ast, outfile, genfunname, param_list, gotolabel, labeldefine,
                                            return_val)
                elif rloop_list[0] == "four":
                    print("continue.....four")
                elif rloop_list[0] == "five":
                    """没有loop的情况，分为endpart,和startpart处理"""
                    print("five....1457")

                    split_endlist = []
                    split_path_end(bblist, split_endlist)
                    start = split_endlist[0][0]
                    end = split_endlist[-1][-1]
                    endpathlist = pathlist[start:end + 1]
                    dep_list = []
                    deal_end_part(endpathlist, startline, dep_list, param_list, None, gotolabel, labeldefine,
                                  return_val)
                    if len(dep_list) > 0:
                        split_index = dep_list[0]
                        startpathlist = pathlist[split_index:]
                        print("startpathlist....")
                        for ele in startpathlist:
                            print(ele.get_name())
                        startlinenum = 0
                        endpart_astlist = dep_list[1]
                        print("endpart+astlist....1470")
                        for t in endpart_astlist:
                            print(t)
                        line_ast = []
                        inc_line = dep_list[2]
                        deal_start_part(bblist, startpathlist, startlinenum, endline, endpart_astlist, line_ast,
                                        param_list,
                                        inc_line, gotolabel, labeldefine, return_val)
                        line_ast.reverse()
                        gen_final_startpart(line_ast, outfile, genfunname, param_list, gotolabel, labeldefine,
                                            return_val)
    else:
        """
        路径当中没有包含end节点
        """
        dealed_ast = []
        line_ast = []
        deal_start_part(bblist, pathlist, startline, endline, dealed_ast, line_ast, param_list, None, gotolabel,
                        labeldefine, return_val)
        line_ast.reverse()
        gen_final_startpart(line_ast, outfile, genfunname, param_list, gotolabel, labeldefine, return_val)

    print("srcname in code_gen...")


def get_last_lineinfo(no):
    """
    获得节点中最后一行以“/home”开头的行信息
    :param no:Node节点
    :return:列表（包含最后一行行信息）
    """
    pathline = []
    nnlabel = no.get("label")[2:-2]
    if nnlabel.endswith("_start") or nnlabel.endswith("_end"):
        pass
    labellist = nnlabel.split("\n")
    for l in labellist:
        if l.startswith('BB'):
            # print(l)
            if "/home/" in l:
                index = l.index('/home/')
                l1 = l[index:]
                pathline.append(l1)
        elif "/home/" in l:
            pathline.append(l)
    return pathline[-1]


def get_lineinfo(no):
    """
    将所有以“/home”开始的行信息添加到列表中（保证列表中的信息不重复）
    :param no:Node节点
    :return:列表（包含不重复的行信息，顺序添加）
    """
    pathline = []
    nnlabel = no.get("label")[2:-2]
    if nnlabel.endswith("_start") or nnlabel.endswith("_end"):
        pass
    labellist = nnlabel.split("\n")
    for l in labellist:
        if l.startswith('BB'):
            # print(l)
            if "/home/" in l:
                index = l.index('/home/')
                l1 = l[index:]
                pathline.append(l1)
        elif "/home/" in l and l not in pathline:
            pathline.append(l)
    return pathline


def get_lineinfo_sort(no):
    """
    将所有以“/home”开始的行信息添加到列表中（升序添加不重复）
    :param no:Node节点
    :return:列表（包含不重复且升序的行信息）
    :param no:
    :return:
    """
    pathline = []
    nnlabel = no.get("label")[2:-2]
    if nnlabel.endswith("_start") or nnlabel.endswith("_end"):
        pass
    linenum = -1
    labellist = nnlabel.split("\n")
    for l in labellist:
        if l.startswith('BB'):
            # print(l)
            if "/home/" in l:
                index = l.index('/home/')
                l1 = l[index:]
                ind = l1.index(":")
                real_linenum = l1[ind + 1:-2]
                if int(real_linenum) < linenum:
                    continue
                pathline.append(l1)
                linenum = int(real_linenum)
            else:
                continue
        elif "/home/" in l and l not in pathline:
            ind = l.index(":")
            real_linenum = l[ind + 1:-2]
            # print(real_linenum)
            if int(real_linenum) < linenum:
                print("continue linenum.....")
            else:
                pathline.append(l)
                linenum = int(real_linenum)
    return pathline


def finddecl(child, va, parm_list, flg):
    """
    在函数的参数列表或是函数体中找到变量va的声明语句对应的ast
    :param child: Node，准确的说是函数的的参数声明fun.decl或是函数体fun.body对应的ast
    :param va: string（变量名，代表在代码生成过程中使用但没有声明的变量）
    :param parm_list: 列表（元素是声明语句对应的ast，代表va列表中相应变量的声明语句）
    :param flg: bool值,用于判断变量名va的声明语句是否已经存在于parm_list中
    :return:无
    """
    if type(child) == c_ast.ParamList:
        for c in child.params:
            if c.name == va:
                if c in parm_list:
                    flg = True
                    break
                parm_list.append(c)
                flg = True
                break
    else:
        for c in child:
            if type(c) == c_ast.FuncDecl:
                finddecl(c.args, va, parm_list, flg)
            elif type(c) == c_ast.Compound or type(c) == c_ast.For or type(c) == c_ast.While or type(
                    c) == c_ast.DoWhile or type(c) \
                    == c_ast.Switch or type(c) == c_ast.Case or type(c) == c_ast.Default or type(c) == c_ast.If:
                finddecl(c, va, parm_list, flg)
            else:
                if type(c) == c_ast.Decl:
                    if c.name == va:
                        if c in parm_list:
                            flg = True
                            break
                        parm_list.append(c)
                        flg = True
                        break

    # if child is None:
    #     return
    # for c in child:
    #     if c is None:
    #         break
    #     elif type(c) == c_ast.Decl:
    #         if c.name == va:
    #             if c in parm_list:
    #                 flg = True
    #                 break
    #             parm_list.append(c)
    #             flg = True
    #             break
    #         else:
    #             finddecl(c, va, parm_list, flg)
    #     else:
    #         finddecl(c, va, parm_list, flg)


def find_in_return(linenum, tempast, funname, varlist, inc_linenum):
    if funname in global_return_sta.keys():
        tempdic = global_return_sta[funname]
        if linenum in tempdic.keys():
            returnsta = tempdic[linenum][0]
            findid(returnsta, varlist)
            tempast.append(returnsta)
            if len(inc_linenum) > 0:
                inc_linenum[0] = tempdic[linenum][1]
            else:
                inc_linenum.append(tempdic[linenum][1])


def deal_start_part(blocknamelist, pathlist, startline, endline, dealed_ast, line_ast, param_list, inc_line, gotolabel,
                    labeldefine, return_val):
    """
    处理最终路径列表中的startpart部分（包括本身路径单重没有_end节点的情况，将路径拆分出startpart的情况）
    :param blocknamelist: 列表（包含所有未拆分情况下的基本块name）
    :param pathlist:列表（包含拆分果果startpart部分的节点）
    :param startline:int（source行号）
    :param endline:int（sink行号）
    :param dealed_ast:列表（其元素为已经处理过后所返回的ast语句）
    :param line_ast:列表（用于存放最终遍历到的所有ast）
    :param param_list:列表（用于存放需要放在生成函数的参数列表里的ast变量语句）
    :param inc_line:
    :return:
    """
    bblocklist = []
    for i in pathlist:
        bbname = i.get_name()
        bblocklist.append(bbname)
    split_path = []
    split_path_pos(bblocklist, split_path)
    for part in split_path:
        start = part[0]
        end = part[-1]
        partpath = pathlist[start:end + 1]
        startele = partpath[0]
        callerfunname = getfunnmae(startele)
        ast = parse_to_ast(startele, return_val)

        tempast = []
        fun_ast_map = {callerfunname: tempast}
        if part == split_path[0]:
            if len(dealed_ast) > 0:
                for t in dealed_ast:
                    tempast.append(t)
        varlist = []
        for ext1 in ast.ext:
            if type(ext1) == c_ast.FuncDef and ext1.decl.name == callerfunname:
                funast = copy.deepcopy(ext1)
                break
        bodyast = funast.body

        print("findast....")
        print(funast)
        inc_linenum = []
        if part == split_path[0] and inc_line is not None:
            inc_linenum.append(inc_line)

        if part == split_path[-1]:
            for ele in partpath:
                bbname = ele.get_name()
                lineinfo_list = get_lineinfo_sort(ele)
                if len(lineinfo_list) == 0:
                    continue
                for line in lineinfo_list:
                    linenum = get_per_linenum(line)
                    if len(inc_linenum) > 0 and linenum <= inc_linenum[0]:
                        continue
                    if part == split_path[0] and linenum < startline:
                        continue
                    if part == split_path[-1] and linenum > endline:
                        break
                    findflag = [False]
                    recurfindline(bodyast, linenum, bbname, bblocklist, varlist, tempast, inc_linenum, gotolabel,
                                  labeldefine, findflag)
                    if findflag[0] is False:
                        find_in_return(linenum, tempast, callerfunname, varlist, inc_linenum)
            line_ast.append(fun_ast_map)
        else:
            called_ele = pathlist[end + 1]
            called_funname = getfunnmae(called_ele)
            # 判断callend函数所在的基本块和行号
            ret_list = []
            get_bb_linenum_inloop(partpath, called_funname, ret_list, bblocklist)
            if len(ret_list) > 0:
                called_linenum = ret_list[0]
                """将loop所在的part拆分成两部分"""
                splitindex = ret_list[1]
                curele = pathlist[splitindex]
                # 判断called函数的行号是否在loop中
                loop_list = []
                curfunname = getfunnmae(curele)
                isloop = judge_line_inloop(curfunname, called_linenum, loop_list)
                if isloop:
                    loop_range = loop_list[1]
                    loopast = loop_list[0]
                    find_goto_balel(loopast, gotolabel, labeldefine)
                    funn = 'BB' + callerfunname + '_start'
                    if funn in blocknamelist:
                        pass
                    else:
                        find_loopid(loopast, varlist)
                    loop_start = loop_range[0]
                    loop_end = loop_range[1]
                    int_loop_range = range(loop_start, loop_end + 1)
                    is_inloop = False
                    for ele in partpath:
                        bbname = ele.get_name()
                        lineinfo_list = get_lineinfo_sort(ele)
                        if len(lineinfo_list) == 0:
                            continue
                        for line in lineinfo_list:
                            linenum = get_per_linenum(line)
                            if linenum in int_loop_range:
                                is_inloop = True
                                break
                            else:
                                if len(inc_linenum) > 0 and linenum <= inc_linenum[0]:
                                    continue
                                if part == split_path[0] and linenum < startline:
                                    continue
                                if part == split_path[-1] and linenum > endline:
                                    break
                                findflag = [False]
                                recurfindline(bodyast, linenum, bbname, bblocklist, varlist, tempast, inc_linenum,
                                              gotolabel, labeldefine, findflag)
                                if findflag[0] is False:
                                    find_in_return(linenum, tempast, callerfunname, varlist, inc_linenum)
                        if is_inloop:
                            tempast.append(loopast)
                            break
                    move_flag = "reverse"
                    next_ast = loop_move(loopast, called_linenum, called_ele, move_flag, return_val)
                    if part == split_path[-2]:
                        pass
                    else:
                        curind = split_path.index(part)
                        tunc_list = split_path[curind + 1:]
                        # 非loop移动
                        for t in tunc_list:
                            if t == tunc_list[-1]:
                                break
                            print("tunc list...")
                            print(tunc_list)
                            startind = t[0]
                            endind = t[1]
                            part_path1 = pathlist[startind:endind + 1]
                            next_ele = pathlist[endind + 1]
                            funname = getfunnmae(next_ele)
                            print(funname)
                            templist = []
                            get_bb_linenum(part_path1, funname, templist, bblocklist)
                            if len(templist) > 0:
                                linenum = templist[0]
                                mvflag = "reverse"
                                next_ast = notloop_move(linenum, next_ast, next_ele, mvflag, return_val)
                    line_ast.append(fun_ast_map)
                    break
                else:  # 没有loop
                    for ele in partpath:
                        bbname = ele.get_name()
                        lineinfo_list = get_lineinfo_sort(ele)
                        if part != split_path[-1] and ele == partpath[-2]:
                            lineinfo_list1 = [get_last_lineinfo(ele)]
                            linenum = get_per_linenum(lineinfo_list1[0])
                            if len(tempast) == 0:
                                tempast.append(linenum)
                            else:
                                tempast.insert(0, linenum)
                        if len(lineinfo_list) == 0:
                            continue
                        for line in lineinfo_list:
                            linenum = get_per_linenum(line)
                            if len(inc_linenum) > 0 and linenum <= inc_linenum[0]:
                                continue
                            if part == split_path[0] and linenum < startline:
                                continue
                            if part == split_path[-1] and linenum > endline:
                                break
                            findflag = [False]
                            recurfindline(bodyast, linenum, bbname, bblocklist, varlist, tempast, inc_linenum,
                                          gotolabel, labeldefine, findflag)
                            if findflag[0] is False:
                                find_in_return(linenum, tempast, callerfunname, varlist, inc_linenum)
                    line_ast.append(fun_ast_map)
        for va in varlist:
            flg = False
            finddecl(funast.decl.type.args, va, param_list, flg)
            if flg == False:
                finddecl(funast.body, va, param_list, flg)


def getfunnmae(ele):
    """
    获取此基本块所属函数的函数名
    :param ele:Node（基本块）
    :return:string(函数名）
    """
    elename = ele.get_name()
    if elename.endswith("_start"):
        funname = elename[2:-6]
    elif elename.endswith("_end"):
        funname = elename[2:-4]
    else:
        inde = elename.index("BB")
        funname = elename[:inde]
    return funname


def get_classifypath_key(pathlist):
    """
    获取每条路径的key值，key值是在本函数中进行构造的。
    :param pathlist: 列表（一条路径，其元素是一系列的基本块）
    :return: string(key值）
    """
    p1 = pathlist[0]
    prefunname = getfunnmae(p1)
    prebbname = p1.get_name()
    k = 1
    key = prefunname + "_" + str(k)
    for i in range(1, len(pathlist)):
        curp = pathlist[i]
        curfunname = getfunnmae(curp)
        curbbname = curp.get_name()
        if prebbname.endswith("_start") or prebbname.endswith("_end"):
            k = k + 1
            key = key + "_" + curfunname + "_" + str(k)
            prebbname = curbbname
        else:
            prebbname = curbbname
    return key


def get_first_lineinfo(ele):
    """
    获取基本块中第一条语句的行信息（以绝对路径显示的）
    :param ele: Node（基本块节点）
    :return: string（行信息）
    """
    relabel_list = ele.get("label")[2:-2]
    relabellist_list = relabel_list.split("\n")
    relist1_linenum = 0
    for l in relabellist_list:
        if "/home/" in l:
            if l.startswith('BB'):
                index = l.index('/home/')
                l1 = l[index:]
                return l1
            else:
                return l


def getlinenum(ele):
    """
    获取基本块中第一条语句的行号
    :param ele: Node（基本块节点）
    :return: string型的行号
    """
    relabel_list = ele.get("label")[2:-2]
    relabellist_list = relabel_list.split("\n")
    relist1_linenum = 0
    for l in relabellist_list:
        if "/home/" in l:
            if l.startswith('BB'):
                # print(l)
                index = l.index('/home/')
                l1 = l[index:]
                ind = l1.index(":")
                relist1_linenum = l1[ind + 1:-2]
                break
            else:
                ind = l.index(":")
                relist1_linenum = l[ind + 1:-2]
                break
    return relist1_linenum


def get_per_linenum(lineinfo):
    """
    根据行信息获取行号
    :param lineinfo: 字符串（以绝对路径显示的一条行信息，包含路径名，文件名，行号等）
    :return: int整数（代表行号）
    """
    if lineinfo.startswith('BB'):
        index = lineinfo.index('/home/')
        l1 = lineinfo[index:]
        ind = l1.index(":")
        relist1_linenum = int(l1[ind + 1:-2])
    else:
        ind = lineinfo.index(":")
        relist1_linenum = int(lineinfo[ind + 1:-2])
    return relist1_linenum


def part_sort(templist):
    """
    对路径的子区间进行升序处理
    :param templist: 列表（代表路径的一个子区间，元素是一些基本块）
    :return: 列表（升序后的路径子区间）
    """
    sort_templist = []
    for temp_ele in templist:
        tname = temp_ele.get_name()
        temp_linenum = getlinenum(temp_ele)
        if temp_ele == templist[0]:
            sort_templist.append(temp_ele)
            continue
        elif tname.endswith("_start") or tname.endswith("_end"):
            sort_templist.append(temp_ele)
        elif temp_linenum == 0:
            continue
        else:
            if len(sort_templist) == 0:
                sort_templist.append(temp_ele)
            else:
                ret_temp = sort_templist[-1]
                ret_linenmu = getlinenum(ret_temp)
                if temp_linenum > ret_linenmu:
                    sort_templist.append(temp_ele)
                elif temp_linenum == ret_linenmu:
                    sort_templist.append(temp_ele)
                    continue
                else:
                    for rev in sort_templist[::-1]:
                        rev_linenum = getlinenum(rev)
                        if rev == sort_templist[0] and rev_linenum > temp_linenum:
                            sort_templist.insert(0, temp_ele)
                            break

                        elif rev_linenum < temp_linenum:
                            rev_ind = sort_templist.index(rev)
                            sort_templist.insert(rev_ind + 1, temp_ele)
                            break
                        elif rev_linenum == temp_linenum:
                            rev_ind = sort_templist.index(rev)
                            sort_templist.insert(rev_ind + 1, temp_ele)
                            break
                        elif rev_linenum > temp_linenum:
                            continue
    return sort_templist


def sort_deup1(pa):
    """
    对一条路径按照行号进行升序操作，将路径根据end或start划分成不同的子区间，
    调用sort_part对每一个子区间进行升序，在保证每个子区间都是升序的情况下，
    整条路径自然是升序的。
    :param pa:列表（代表一条路径，元素是一些基本块）
    :return:列表（升序后的路径）
    """
    sort_pa = []
    split_list = []
    pabblist = []
    for p in pa:
        pname = p.get_name()
        pabblist.append(pname)
    split_path_pos(pabblist, split_list)
    split_len = len(split_list)
    for i in range(0, split_len):
        part = split_list[i]
        start = part[0]
        end = part[1]
        per_part = pa[start:end + 1]
        sort_list = part_sort(per_part)
        for ele in sort_list:
            # print(ele)
            sort_pa.append(ele)
    return sort_pa


def merge_two_list_part(list1, list2):
    """
    合并两条路径，两条路径所属的子区间相同，且已经做好升序排列
    :param list1: 列表（包含某一个路径子区间的基本块）
    :param list2: 列表（包含某一个路径子区间的基本块）
    :return:列表（合并后的子区间路径）
    """
    templist = []
    start_end = list1[-1]
    start_end_name = start_end.get_name()
    flag = False
    if start_end_name.endswith("_end") or start_end_name.endswith("_start"):
        templist1 = list1[0:-1]
        templist2 = list2[0:-1]
        flag = True
    else:
        templist1 = list1
        templist2 = list2
    lenlist1 = len(templist1)
    lenlist2 = len(templist2)
    pt1 = 0
    pt2 = 0
    while (1):
        if pt1 == lenlist1 and pt2 != lenlist2:
            for i in range(pt2, lenlist2):
                tempe = list2[i]
                templist.append(tempe)
            break
        elif pt1 == lenlist1 and pt2 == lenlist2:
            break
        elif pt1 < lenlist1 and pt2 == lenlist2:
            for i in range(pt1, lenlist1):
                tempe = list1[i]
                templist.append(tempe)
            break

        e1 = templist1[pt1]
        e2 = templist2[pt2]
        e1line = getlinenum(e1)
        e2line = getlinenum(e2)

        if e1line == e2line:
            templist.append(e1)
            pt1 = pt1 + 1
            pt2 = pt2 + 1
            continue
        elif e1line < e2line:
            templist.append(e1)
            pt1 = pt1 + 1
            continue
        else:
            templist.append(e2)
            pt2 = pt2 + 1
            continue
    if flag:
        templist.append(start_end)
    return templist


def merge_two_list(list1, list2):
    """
    合并两条路径，两条路径的key值相同，将路径划分成不同的子区间，调用merge_two_list_part合并子区间，
    在保证每个子区间都合并好之后两条路径也就完成了合并
    :param list1: 列表（一条路径，包含基本块）
    :param list2: 列表（一条路径，包含基本块）
    :return:列表（合并后的路径）
    """
    split_list1 = []
    split_list2 = []
    bblist1 = []
    bblist2 = []
    for l in list1:
        bname = l.get_name()
        bblist1.append(bname)
    for l in list2:
        bname = l.get_name()
        bblist2.append(bname)
    split_path_pos(bblist1, split_list1)
    split_path_pos(bblist2, split_list2)
    part_len = len(split_list2)
    merge_list = []
    for i in range(0, part_len):
        list1_part = split_list1[i]
        list2_part = split_list2[i]
        list1_start = list1_part[0]
        list1_end = list1_part[1]
        list2_start = list2_part[0]
        list2_end = list2_part[1]
        part_list1 = list1[list1_start:list1_end + 1]
        part_list2 = list2[list2_start:list2_end + 1]
        templist = merge_two_list_part(part_list1, part_list2)
        for te in templist:
            merge_list.append(te)
    return merge_list


def split_path_pos(pathlist, split_pathlist):
    """
    将路径按照end标识和start标识拆分为不同的区间
    :param pathlist: 列表（包含所有基本块的名字）
    :param split_pathlist: 列表（其元素为不同的区间，每个区间是一个列表，包含起始索引和终止索引）
    :return:无
    """
    start = 0
    end = start
    for p in pathlist:
        if p.endswith("_end"):
            templist = [start, end]
            split_pathlist.append(templist)
            end = end + 1
            start = end
        elif p.endswith("_start"):
            templist = [start, end]
            split_pathlist.append(templist)
            end = end + 1
            start = end
        else:
            end = end + 1
        if p == pathlist[-1]:
            templist = [start, end - 1]
            split_pathlist.append(templist)


def loop_move(loopast, linenum, ele, re_po_flat, return_val):
    """
    loopast是loop所在的区间（不论是不是（正倒序都可以）），将相邻的called函数移动到loop中相应的位置
    :param loopast: 对应与主调函数中loop的ast
    :param linenum: called函数所在的行号
    :param ele: called函数中的一个基本块
    :return: ext1.body.block_items
    """
    tempast = parse_to_ast(ele, return_val)
    funname = getfunnmae(ele)
    for ext1 in tempast.ext:
        if type(ext1) == c_ast.FuncDef and ext1.decl.name == funname:
            # deal_return(ext1, funname)
            next_ast = ext1.body.block_items
            rdic = []
            find_called_fun(loopast, linenum, funname, rdic)
            if len(rdic) > 0:
                compoundst = re_move_code(rdic, funname, next_ast, re_po_flat)
                # print("compoundst....1")
                # print(compoundst)
                return compoundst
            break


def judge_line_inloop(funname, startlinenum, ret_list):
    """
    判断called函数调用的行号是否在一个loop中
    :param funname:主调函数的函数名
    :param startlinenum: called函数所在行号
    :param ret_list: 返回列表，返回loop对应的ast
    :return:bool值
    """
    isloop = False
    if funname in fun_loop.keys():
        for loop in fun_loop[funname]:
            loopkey = list(loop.keys())[0].split(":")
            start = int(loopkey[0])
            end = int(loopkey[1])
            templist = list(range(start, end))
            if int(startlinenum) in templist:
                onlyloopast = copy.deepcopy(loop[list(loop.keys())[0]])
                loop_list = [start, end]
                ret_list.append(onlyloopast)
                ret_list.append(loop_list)
                isloop = True
                break
    return isloop


def get_bb_linenum_inloop(part_path, called_funname, ret_list, bblocklist):
    """
    在区间中找被调用函数，并获取被调用函数的行号
    :param part_path: 子区间（包含一些基本块）
    :param called_funname: called函数的函数名
    :param ret_list: 返回值列表，包含行号和ccalled函数所在基本块在整个基本款列表中的索引
    :param bblocklist:基本块的name列表
    :return:无
    """
    """获取子区间中对called函数调用所在的行号"""
    n = 0
    for p in part_path:
        if p.get_name().endswith("_end") or p.get_name().endswith("_start"):
            n = n + 1
            continue
        else:
            linenum = get_bb_last_num(p, called_funname)
            if linenum > 0:
                ret_list.append(linenum)
                ind = bblocklist.index(p.get_name())
                ret_list.append(ind)
                break
            n = n + 1
    ret_list.append(n)


def get_bb_linenum(part_path, called_funname, ret_list, bblocklist):
    """
    在区间中找被调用函数，并获取被调用函数的行号
    :param part_path: 子区间（包含一些基本块）
    :param called_funname: called函数的函数名
    :param ret_list: 返回值列表，包含行号和ccalled函数所在基本块在整个基本款列表中的索引
    :param bblocklist:基本块的name列表
    :return:无
    """
    """获取子区间中对called函数调用所在的行号"""
    for n in part_path:
        if n.get_name().endswith("_end") or n.get_name().endswith("_start"):
            continue
        else:
            linenum = get_bb_last_num(n, called_funname)
            if linenum > 0:
                ret_list.append(linenum)
                ind = bblocklist.index(n.get_name())
                ret_list.append(ind)


def isincludefuncall1(l, nextfunname, rdic, depth, linenum, parent_node):
    """
    根据called函数名和行号判断对应于每一条语句的ast中是否包含被调用函数，
    如果存在，保存这条语句的父节点，当前语句的索引，类型，以及所找到函数的实参到rdic列表中
    :param l: c语句对应的ast
    :param nextfunname: 被调用函数的函数名
    :param rdic: 返回值列表（父节点，called函数所在的节点在父节点中的索引，called函数的类型（basic，ifcond），实参列表）
    :param depth: 递归深度
    :param linenum: 被调用函数所在的行号
    :param parent_node: 参数l的父节点
    :return:无
    """
    """为了得到每一种语句的父节点"""
    depth = depth + 1
    statetype = type(l)
    # print("include.....l")
    # print(generator.visit(l))
    if statetype == c_ast.If:
        cond = l.cond
        funlist = []
        is_have_funcall(nextfunname, cond, linenum, funlist)
        if len(funlist) > 0:
            funcall = funlist[1]
            if depth == 1:
                rdic.append('null')
                rdic.append('null')
                rdic.append("ifcond")
                get_actual_parm(funcall, rdic)
                return
            else:
                rdic.append(parent_node)
                ind = parent_node.index(l)
                rdic.append(ind)
                rdic.append('ifcond')
                get_actual_parm(funcall, rdic)
                return

        iftrue = l.iftrue
        # print(l)
        if iftrue is not None:
            if type(iftrue) == c_ast.Compound:
                pass
            else:
                l.iftrue = c_ast.Compound(block_items=[iftrue])
            if l.iftrue.block_items is None:
                pass
            else:
                for ele in l.iftrue.block_items:
                    eletype = type(ele)
                    if eletype == c_ast.If or eletype == c_ast.For or eletype == c_ast.While or eletype == c_ast.DoWhile or eletype == c_ast.Switch or eletype == c_ast.Compound:
                        isincludefuncall1(ele, nextfunname, rdic, depth, linenum, l.iftrue.block_items)
                    else:
                        funlist = []
                        is_have_funcall(nextfunname, ele, linenum, funlist)
                        if len(funlist) > 0:
                            funcall = funlist[1]
                            rdic.append(l.iftrue.block_items)
                            ind = l.iftrue.block_items.index(ele)
                            rdic.append(ind)
                            rdic.append('basic')
                            # print("parent and child.....")
                            # print(generator.visit(l.iftrue))
                            # print("parent and child.....")
                            # print(generator.visit(ele))
                            get_actual_parm(funcall, rdic)
                            return
        else:
            pass

        iffalse = l.iffalse
        if iffalse is None:
            pass
        else:
            iffalsetype = type(iffalse)
            if iffalsetype == c_ast.Compound:
                pass
            else:
                l.iffalse = c_ast.Compound(block_items=[iffalse])
            if l.iffalse.block_items is None:
                pass
            else:
                for ele in l.iffalse.block_items:
                    eletype = type(ele)
                    if eletype == c_ast.If or eletype == c_ast.For or eletype == c_ast.While or eletype == c_ast.DoWhile or eletype == c_ast.Switch or eletype == c_ast.Compound:
                        isincludefuncall1(ele, nextfunname, rdic, depth, linenum, l.iffalse.block_items)
                    else:
                        funlist = []
                        is_have_funcall(nextfunname, ele, linenum, funlist)
                        if len(funlist) > 0:
                            funcall = funlist[1]
                            rdic.append(l.iffalse.block_items)
                            ind = l.iffalse.block_items.index(ele)
                            rdic.append(ind)
                            rdic.append('basic')
                            # print("parent and child.....1")
                            # print(generator.visit(l.iffalse))
                            # print("parent and child.....1")
                            # print(generator.visit(ele))
                            get_actual_parm(funcall, rdic)
                            return

    elif statetype == c_ast.For:
        init = l.init
        funlist = []
        is_have_funcall(nextfunname, init, linenum, funlist)
        if len(funlist) > 0:
            funcall = funlist[1]
            if depth == 1:
                rdic.append('null')
                rdic.append('null')
                rdic.append("loopcond")
                get_actual_parm(funcall, rdic)
                return
            else:
                rdic.append(parent_node)
                ind = parent_node.index(l)
                rdic.append(ind)
                rdic.append('loopcond')
                get_actual_parm(funcall, rdic)
                return

        cond = l.cond
        funlist = []
        is_have_funcall(nextfunname, cond, linenum, funlist)
        if len(funlist) > 0:
            funcall = funlist[1]
            if depth == 1:
                rdic.append('null')
                rdic.append('null')
                rdic.append("loopcond")
                get_actual_parm(funcall, rdic)
                return
            else:
                rdic.append(parent_node)
                ind = parent_node.index(l)
                rdic.append(ind)
                rdic.append('loopcond')
                get_actual_parm(funcall, rdic)
                return

        next = l.next
        funlist = []
        is_have_funcall(nextfunname, next, linenum, funlist)
        if len(funlist) > 0:
            funcall = funlist[1]
            if depth == 1:
                rdic.append('null')
                rdic.append('null')
                rdic.append("loopcond")
                get_actual_parm(funcall, rdic)
                return
            else:
                rdic.append(parent_node)
                ind = parent_node.index(l)
                rdic.append(ind)
                rdic.append('loopcond')
                get_actual_parm(funcall, rdic)
                return

        stmt = l.stmt
        if type(stmt) == c_ast.Compound:
            pass
        else:
            l.stmt = c_ast.Compound(block_items=[stmt])
        for ele in l.stmt.block_items:
            eletype = type(ele)
            if eletype == c_ast.If or eletype == c_ast.For or eletype == c_ast.While or eletype == c_ast.DoWhile or eletype == c_ast.Switch or eletype == c_ast.Compound:
                isincludefuncall1(ele, nextfunname, rdic, depth, linenum, l.stmt.block_items)
            else:
                funlist = []
                is_have_funcall(nextfunname, ele, linenum, funlist)
                # funflagkey = list(fundic.keys())[0]
                if len(funlist) > 0:
                    funcall = funlist[1]
                    rdic.append(l.stmt.block_items)
                    ind = l.stmt.block_items.index(ele)
                    rdic.append(ind)
                    rdic.append("basic")
                    # print("parent and child.....2")
                    # print(generator.visit(l.stmt))
                    # print("parent and child.....2")
                    # print(generator.visit(ele))
                    get_actual_parm(funcall, rdic)
                    return

    elif statetype == c_ast.Compound:
        for ele in l.block_items:
            eletype = type(ele)
            if eletype == c_ast.If or eletype == c_ast.For or eletype == c_ast.While or eletype == c_ast.DoWhile or eletype == c_ast.Switch or eletype == c_ast.Compound:
                isincludefuncall1(ele, nextfunname, rdic, depth, linenum, l.block_items)
            else:
                funlist = []
                is_have_funcall(nextfunname, ele, linenum, funlist)
                if len(funlist) > 0:
                    funcall = funlist[1]
                    rdic.append(l.block_items)
                    ind = l.block_items.index(ele)
                    rdic.append(ind)
                    rdic.append("basic")
                    # print("parent and child.....3")
                    # print(generator.visit(l))
                    # print("parent and child.....3")
                    # print(generator.visit(ele))
                    get_actual_parm(funcall, rdic)
                    return
    elif statetype == c_ast.While or statetype == c_ast.DoWhile:
        cond = l.cond
        funlist = []
        is_have_funcall(nextfunname, cond, linenum, funlist)
        if len(funlist) > 0:
            funcall = funlist[1]
            if depth == 1:
                rdic.append('null')
                rdic.append('null')
                rdic.append("loopcond")
                get_actual_parm(funcall, rdic)
                return
            else:
                rdic.append(parent_node)
                ind = parent_node.index(l)
                rdic.append(ind)
                rdic.append('loopcond')
                get_actual_parm(funcall, rdic)
                return

        stmt = l.stmt
        if type(stmt) == c_ast.Compound:
            pass
        else:
            l.stmt = c_ast.Compound(block_items=[stmt])
        for ele in l.stmt.block_items:
            eletype = type(ele)
            if eletype == c_ast.If or eletype == c_ast.For or eletype == c_ast.While or eletype == c_ast.DoWhile or eletype == c_ast.Switch or eletype == c_ast.Compound:
                isincludefuncall1(ele, nextfunname, rdic, depth, linenum, l.stmt.block_items)
            else:
                funlist = []
                is_have_funcall(nextfunname, ele, linenum, funlist)
                if len(funlist) > 0:
                    funcall = funlist[1]
                    rdic.append(l.stmt.block_items)
                    ind = l.stmt.block_items.index(ele)
                    rdic.append(ind)
                    rdic.append("basic")
                    # print("parent and child.....4")
                    # print(generator.visit(l.stmt))
                    # print("parent and child.....4")
                    # print(generator.visit(ele))
                    get_actual_parm(funcall, rdic)
                    return

    elif statetype == c_ast.Switch:
        cond = l.cond
        funlist = []
        is_have_funcall(nextfunname, cond, linenum, funlist)
        if len(funlist) > 0:
            funcall = funlist[1]
            if depth == 1:
                rdic.append('null')
                rdic.append('null')
                rdic.append("ifcond")
                get_actual_parm(funcall, rdic)
                return
            else:
                rdic.append(parent_node)
                ind = parent_node.index(l)
                rdic.append(ind)
                rdic.append('ifcond')
                get_actual_parm(funcall, rdic)
                return

        stmt = l.stmt
        for ele in stmt.block_items:
            eletype = type(ele)
            if eletype == c_ast.Case or eletype == c_ast.Default:
                for caseele in ele.stmts:
                    eletype = type(caseele)
                    if eletype == c_ast.If or eletype == c_ast.For or eletype == c_ast.While or eletype == c_ast.DoWhile or eletype == c_ast.Switch or eletype == c_ast.Compound:
                        isincludefuncall1(caseele, nextfunname, rdic, depth, linenum, ele.stmts)
                    else:
                        funlist = []
                        is_have_funcall(nextfunname, caseele, linenum, funlist)
                        if len(funlist) > 0:
                            funcall = funlist[1]
                            rdic.append(ele.stmts)
                            ind = ele.stmts.index(caseele)
                            rdic.append(ind)
                            rdic.append('basic')
                            # print("parent and child.....5")
                            # print(generator.visit(ele))
                            # print("parent and child.....5")
                            # print(generator.visit(caseele))
                            get_actual_parm(funcall, rdic)
                            return
    else:
        funlist = []
        # print(l)
        is_have_funcall(nextfunname, l, linenum, funlist)
        # print("funlist.....")
        # print(funlist)
        if len(funlist) > 0:
            funcall = funlist[1]
            if depth == 1:
                rdic.append('null')
                rdic.append('null')
                rdic.append("basic")
                get_actual_parm(funcall, rdic)
                return
            else:
                # print("parentnode")
                # print(parent_node)
                rdic.append(parent_node)
                ind = parent_node.index(l)
                rdic.append(ind)
                rdic.append('basic')
                print("parent and child.....6")
                # for st in parent_node:
                #     print(generator.visit(st))
                print("parent and child.....6")
                # print(generator.visit(l))
                get_actual_parm(funcall, rdic)
                return
