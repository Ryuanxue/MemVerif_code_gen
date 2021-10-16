from __future__ import print_function
import sys


sys.path.extend(['.', '..'])
sys.path.append("../")

from pycparser import c_ast

global_return_sta = {}
global_return_decl={}


def get_last_linenum(c, last_num, inc_linenum):
    if c.coord is not None:
        templine = int(str(c.coord).split(":")[1])
        if templine > last_num:
            last_num = templine
            if len(inc_linenum) == 0:
                inc_linenum.append(last_num)
            else:
                inc_linenum[0] = last_num
    for child in c:
        if child is None:
            continue
        else:
            if child.coord is not None:
                templine = int(str(child.coord).split(":")[1])
                if templine > last_num:
                    last_num = templine
                    if len(inc_linenum) == 0:
                        inc_linenum.append(last_num)
                    else:
                        inc_linenum[0] = last_num
            # print("finally_last_num:" + str(last_num))
            get_last_linenum(child, last_num, inc_linenum)
    # return last_num

def find_return(st, ret_name, gotost, funnamne,pst):
    """
    在每一条语句（复合语句，简单语句，语句）中递归查找所有的return语句，修改成赋值语句并添加goto语句
    find all return statement and modify it and insert new statement
    :param st: 复合语句或者简单语句对应的ast
    :param ret_name: 返回值变量名
    :param gotost: goto语句对应的ast
    :return:
    """
    if type(st)==c_ast.Label:
        print("findlabel...")
        print(st)
    if type(st)==c_ast.Compound or type(st)==c_ast.If or type(st)==c_ast.For or type(st)==c_ast.While or type(st)==c_ast.DoWhile \
        or type(st)==c_ast.Switch or type(st)==c_ast.Case or type(st)==c_ast.Default or type(st)==c_ast.Label:
        for child in st:
            find_return(child,ret_name,gotost,funnamne,st)

    elif type(st) == c_ast.Return:
        assign = c_ast.Assignment(op='=', lvalue=c_ast.ID(name=ret_name), rvalue=st.expr)
        if type(st.expr) == c_ast.FuncCall:
            lineinfo = str(st.coord)
            index = lineinfo.index(":")
            rindex = lineinfo.rindex(":")
            linenum = int(lineinfo[index + 1:rindex])
            last_num = -1
            inc_linenum = []
            get_last_linenum(st, last_num, inc_linenum)
            global_return_sta[funnamne][linenum] = [assign, inc_linenum[0]]
        if type(pst) == c_ast.Compound:
            pst.block_items.remove(st)
            pst.block_items.append(assign)
            pst.block_items.append(gotost)
        elif type(pst) == c_ast.If and st == pst.iftrue:
            tempst = c_ast.Compound(block_items=[assign, gotost])
            pst.iftrue = tempst
        elif type(pst) == c_ast.If and st == pst.iffalse:
            tempst = c_ast.Compound(block_items=[assign, gotost])
            pst.iffalse = tempst
        elif type(pst) ==c_ast.Label:
            tempst = c_ast.Compound(block_items=[assign, gotost])
            pst.stmt = tempst
        else:
            if type(pst) == c_ast.Case or type(pst) == c_ast.Default:
                pst.stmts.remove(st)
                pst.stmts.append(assign)
                pst.stmts.append(gotost)



def deal_return(rast, funnamne, return_val):
    """
    进行return归一化操作，将函数中的return语句替换为赋值语句，并添加label
    :param rast: 对应于函数的ast
    :param funnamne: 函数名
    :return_val:list,存放为每个函数定义的返回值变量
    :return: 无
    """

    if funnamne == "ssl_add_clienthello_tlsext":
        print("funast....")
        print(rast)
    # rast is a funast
    print("return_name....")
    ret_name = funnamne + "_return_"
    labelname = funnamne + "_label_"
    gotost = c_ast.Goto(name=labelname)
    returntype = rast.decl.type.type
    if type(returntype) == c_ast.TypeDecl:
        returnname = returntype.type.names[0]
        temptype = c_ast.TypeDecl(declname=ret_name, quals=[], type=c_ast.IdentifierType(names=[returnname]))
    elif type(returntype) == c_ast.PtrDecl:
        returnname = returntype.type.type.names[0]
        temptype = c_ast.PtrDecl(quals=[], type=c_ast.TypeDecl(declname=ret_name, quals=[],
                                                               type=c_ast.IdentifierType(names=[returnname])))
    else:
        print(rast.decl)
        returnname = returntype.type.type.names[0]
    if returnname == 'void':
        pass
    else:
        global_return_sta[funnamne] = {}
        returnsta = c_ast.Decl(name=ret_name, quals=[], storage=[], funcspec=[], type=temptype, init=None,
                               bitsize=None)
        # rast.body.block_items.insert(0, returnsta)
        global_return_decl[funnamne]=returnsta
        return_val.append(returnsta)
        # deal_last_return(rast,ret_name)
        if type(rast.body.block_items[-1])==c_ast.Label and type(rast.body.block_items[-1].stmt)==c_ast.Return:
            find_return(rast.body.block_items[-1],ret_name,gotost,funnamne,None)
        for s in rast.body.block_items:
            if type(s)==c_ast.Label:
                print("labal....")
                print(s)
            if type(s) == c_ast.Return:
                assign = c_ast.Assignment(op='=', lvalue=c_ast.ID(name=ret_name), rvalue=s.expr)
                if type(s.expr) == c_ast.FuncCall:
                    lineinfo = str(s.coord)
                    index = lineinfo.index(":")
                    rindex = lineinfo.rindex(":")
                    linenum = int(lineinfo[index + 1:rindex])
                    last_num = -1
                    inc_linenum = []
                    get_last_linenum(s, last_num, inc_linenum)
                    global_return_sta[funnamne][linenum] = [assign, inc_linenum[0]]
                index=rast.body.block_items.index(s)
                rast.body.block_items.remove(s)
                rast.body.block_items.insert(index,assign)
                index=index+1
                rast.body.block_items.insert(index,gotost)
            else:
                find_return(s, ret_name, gotost, funnamne,None)
    """添加label"""
    labelname = funnamne + "_label_"
    labelst = c_ast.Label(name=labelname, stmt=c_ast.FuncCall(name=c_ast.ID(name="printf"), args=c_ast.ExprList(
        exprs=[c_ast.Constant(type="string", value='"##\\n"')])))
    rast.body.block_items.append(labelst)
