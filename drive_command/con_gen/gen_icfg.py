import os
from xml.dom.minidom import Document

import pydot


def isend(node_name, edges):
    Flag = True
    for e in edges:
        fromnode = e.get_source()
        if fromnode == node_name:
            Flag = False
            break
    return Flag


Dir = "../../meta_data/cfg_dot"
path = os.path.abspath(Dir)
path_list = os.listdir(path)
# 将所有的以dot结尾的文件添加入fn_list列表中
fn_list = []
fun_entry_end = {}

doc = Document()
root = doc.createElement("root")
doc.appendChild(root)

for file in path_list:
    filename = os.path.basename(file)
    if filename.endswith(".dot"):
        funname=filename[:-4]
        print(funname)
        funnode=doc.createElement("fun")
        funnode.setAttribute("name",funname)
        root.appendChild(funnode)
        fn_list.append(filename)

filename="../../meta_data/_funname_.xml"
with open(filename, 'w') as f:
        f.write(doc.toprettyxml(indent=' '))
        f.close()

# 用于存放所有的节点和所有的边，最后这些节点和边被添加到图中
Nodes = []
Edges = []
m = 0

"""
we must record the entry point and end point of each function.
1.if the source of edges is call statement,omit and jump the edge.
2.get the sorce of edge relative node.
3.get the destination of edge relative node.
4.add a edge from the souce node to the called function's start node.
5.add a edge from the called function's end node to the destination node.

"""

"""
1.只解析一次文件
2.在第一次循环的时候添加end节点，同时判断将哪一个节点指向end节点
3.将end节点添加到fun_entry_end字典中
4.在第一次循环的时候将所有的节点以及边添加到Node和Edge中

"""
for f in fn_list:
    (filedot,) = pydot.graph_from_dot_file(str(Dir + "/" + f))
    nodes = filedot.get_nodes()
    edges = filedot.get_edges()

    funid = f[0:-4]  # """函数名”“”
    fun_entry_end[funid] = []
    """找到函数的入口节点和出口节点添加进入fun_entry_end字典中"""
    end_label = funid + "_end"
    end_name = "BB" + end_label
    endnode = pydot.Node(end_name, label='"{' + end_label + '}"')
    Nodes.append(endnode)
    for n in nodes:
        node_name = n.get_name()
        if node_name.endswith("_start"):
            fun_entry_end[funid].append(n)
        if isend(node_name, edges):
            edge = pydot.Edge(n, endnode)
            Edges.append(edge)
    fun_entry_end[funid].append(endnode)

for f in fn_list:

    # fnodes=[] #单个函数的node
    # if m==10:
    #     break
    print(f)
    (filedot,) = pydot.graph_from_dot_file(str(Dir + "/" + f))
    nodes = filedot.get_nodes()
    edges = filedot.get_edges()
    for ele in nodes:
        # fnodes.append(ele)
        Nodes.append(ele)  # 所有函数的node

        nodelabel = ele.get("label")[2:-2]

        if "call " in nodelabel:
            labellist = nodelabel.split("\n")
            endline = labellist[-2]
            print(endline)
            if "call" not in endline:
                continue
            if "@" not in endline:
                continue
            start_num = endline.index("@")
            end_num = endline.index("(")
            funname = endline[start_num + 1:end_num]
            if funname.startswith("llvm"):
                continue
            else:
                if funname in fun_entry_end.keys():
                    edge1 = pydot.Edge(ele, fun_entry_end[funname][0])
                    edge2 = pydot.Edge(fun_entry_end[funname][1], ele)
                    Edges.append(edge1)
                    Edges.append(edge2)

    for e in edges:
        Edges.append(e)
        # src = e.get_source()
        # dest = e.get_destination()
        #
        # srcnode = filedot.get_node(src)[0]
        # destnode = filedot.get_node(dest)[0]
        # nodelabel = srcnode.get("label")[2:-2]
        #
        # if "call " in nodelabel:
        #     labellist = nodelabel.split("\n")
        #     endline = labellist[-2]
        #     print(endline)
        #     if "call" not in endline:
        #         Edges.append(e)
        #         continue
        #
        #     if "@" not in endline:
        #         Edges.append(e)
        #         continue
        #     start_num = endline.index("@")
        #     end_num = endline.index("(")
        #     funname = endline[start_num + 1:end_num]
        #     if funname.startswith("llvm"):
        #         Edges.append(e)
        #     else:
        #         if funname in fun_entry_end.keys():
        #             edge1 = pydot.Edge(srcnode, fun_entry_end[funname][0])
        #             edge2 = pydot.Edge(fun_entry_end[funname][1], destnode)
        #             Edges.append(edge1)
        #             Edges.append(edge2)
        #             Edges.append(e)
        #         else:
        #             Edges.append(e)
        # else:
        #     Edges.append(e)

    m = m + 1

"""重新创建了一个图，将所有的节点和边添加到图中"""
g = pydot.Dot(graph_name='icfg graph', graph_type='digraph')
for n in Nodes:
    g.add_node(n)
j = 0
for e in Edges:
    g.add_edge(e)
    j = j + 1
print(j)
g.write("../../meta_data/_icfg.dot")
