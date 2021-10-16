import os
from xml.dom.minidom import parse, Document

dic = "/home/raoxue/Desktop/openssl-1.0.1f/ssl"
abspath = os.path.abspath(dic)
dicpath = os.listdir(dic)
sorce_info = []
sink_info = []
doc = Document()
root = doc.createElement("root")
doc.appendChild(root)

for file in dicpath:
    filename = os.path.basename(file)
    if filename.endswith(".xml"):
        if filename == "sink.xml":
            continue
            # doc = parse(dic + "/" + filename)
            # root = doc.documentElement
            # ovreadsrc = root.getElementsByTagName("ovreadsrc")
            # for overread in ovreadsrc:
            #     c_filename = overread.getAttribute("c_filename")
            #     sinkline = overread.getAttribute("linenum")
            #     str1 = c_filename + "#" + sinkline + "#"
            #     sink_info.append(str1)

        else:
            doc1 = parse(dic + "/" + filename)
            root1 = doc1.documentElement
            ovreadsrc = root1.getElementsByTagName("ovreadsrc")
            for overread in ovreadsrc:
                root.appendChild(overread)

filename="source.xml"
with open(filename, 'w') as f:
        f.write(doc.toprettyxml(indent=' '))
        f.close()
