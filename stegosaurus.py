import sys

if sys.version_info.major!=3:
    print("This is a Python 3 program.")
    print("Please use a Python 3 interpreter.")
    exit()

def getCommandArgs():
    has_inp = False
    has_h = False
    has_cpp = False
    ou = dict()
    ou["debug"] = False
    ou["hf"] = False
    for x in sys.argv[1:]:
        if x=="debug=true":
            ou["debug"] = True
        elif x=="hf=true":
            ou["hf"] = True
        else:
            if has_inp==False:
                has_inp = True
                ou["inp"] = x
            elif has_h==False:
                has_h = True
                ou["h"] = x
            elif has_cpp==False:
                has_cpp = True
                ou["cpp"] = x
            else:
                print("Too many arguments passed to program.")
                exit()
    if has_inp==False:
        print("Not enough arguments passed to program.")
        exit()
    if ou["inp"][len(ou["inp"])-5:]!=".steg":
        print("This program can only take .steg files as input.")
        exit()
    if has_h and has_cpp:
        return ou
    if has_h and (has_cpp==False):
        print("Arguments passed to program could not be parsed.")
        exit()
    stem = ou["inp"][:len(ou["inp"])-5] #removes the .steg
    ou["h"] = stem+".h"
    ou["cpp"] = stem+".cpp"
    return ou

def loadfile(filename):
    infile = open(filename,"rb")
    data = infile.read()
    infile.close()
    return list(data)

def savefile(filename,data):
    bdata = bytes(data)
    outfile = open(filename,"wb")
    outfile.truncate(0)
    outfile.seek(0,0)
    outfile.write(bdata)
    outfile.close()

def removeComments(indata):
    in_double_quote = False
    in_single_quote = False
    in_comment = False
    in_block_comment = False
    i = 0
    while True:
        if i>=len(indata):
            return
        if in_double_quote:
            if indata[i:i+2]==[92,34]: # [\,"]
                i += 2
                continue
            if indata[i]==34: # "
                i += 1
                in_double_quote = False
                continue
            i += 1
            continue
        if in_single_quote:
            if indata[i:i+2]==[92,39]: # [\,']
                i += 2
                continue
            if indata[i]==39: # ''
                i += 1
                in_single_quote = False
                continue
            i += 1
            continue
        if in_comment:
            if indata[i]==10: # return
                in_comment = False
            else:
                indata[i] = 32 # space
            i += 1
            continue
        if in_block_comment:
            if indata[i:i+2]==[42,47]: # [*,/]
                indata[i] = 32
                indata[i+1] = 32
                i += 2
                in_block_comment = False
            elif indata[i]==10:
                i += 1
            else:
                indata[i] = 32
                i += 1
            continue
        # not in a special area
        if indata[i]==34:
            in_double_quote = True
            i += 1
            continue
        if indata[i]==39:
            in_single_quote = True
            i += 1
            continue
        if indata[i:i+2]==[47,47]:
            indata[i] = 32
            indata[i+1] = 32
            in_comment = True
            i += 2
            continue
        if indata[i:i+2]==[47,42]: # [/,*]
            indata[i] = 32
            indata[i+1] = 32
            in_block_comment = True
            i += 2
            continue
        i += 1

def makeLines(indata):
    ou = []
    k = []
    for x in indata:
        if x==10:
            ou.append(k)
            k = []
        else:
            k.append(x)
    ou.append(k)
    return ou

def removeNonprintChars(indata):
    ou = []
    for line in indata:
        k = []
        for c in line:
            if c<32:
                if c==9:
                    k.append(c)
            else:
                k.append(c)
        ou.append(k)
    return ou

def countIndents(indata):
    ou = []
    for line in indata:
        i = 0
        while True:
            if i>=len(line):
                break
            if (line[i]!=32) and (line[i]!=9):
                break
            i += 1
        k = [i,bytes(line[i:]).decode("UTF-8")] # turns it into [int,str]
        ou.append(k)
    return ou

def chopLine_template(line):
    t = False
    m = ""
    for c in line[1]:
        if c=="<":
            t = True
        elif t==">":
            t = False
        elif t:
            m = m+c
    m = m.split(",")
    y = []
    for c in m:
        t = c.split(" ")
        i = len(t)-1
        while True:
            if t[i]=="":
                if i==0:
                    break
                else:
                    i -= 1
                    continue
            else:
                break
        if t[i]!="":
            y.append(t[i])
    # now y has the parameter names
    m = "<"
    for i in range(len(y)):
        if y!=0:
            m = m+","
        m = m+y[i]
    m = m+">"
    return [line[0],"template",[line[1][8:],m]]

def chopLine_namespace(line):
    return [line[0],"namespace",[line[1][9:]]]

def chopLine_datastructure(line):
    y = line[1].split(" ")
    u = []
    for x in y:
        if x!="":
            u.append(x)
    m = ""
    for i in range(2,len(u)):
        if i!=2:
            m = m+" "
        m = m+u[i]
    return [line[0],u[0],[u[1],m]]

def chopLine_struct(line):
    return chopLine_datastructure(line)

def chopLine_class(line):
    return chopLine_datastructure(line)

def chopLine_func(line):
    i = 0
    while True:
        if line[1][i]=="(":
            break
        else:
            i += 1
    i -= 1
    while True:
        if line[1][i]!=" ":
            break
        else:
            i -= 1
    while True:
        if line[1][i]==" ":
            break
        else:
            i -= 1
    s1 = line[1][:4]
    s2 = line[1][4:i]
    s3 = line[1][i:]
    return [line[0],s1,[s2,s3]]

def chopLine_private(line):
    return [line[0],"private",[]]

def chopLine_public(line):
    return [line[0],"public",[]]

def chopLine_if(line):
    return [line[0],"if",[line[1][2:]]]

def chopLine_elif(line):
    return [line[0],"elif",[line[1][4:]]]

def chopLine_else(line):
    return [line[0],"else",[]]

def chopLine_for(line):
    return [line[0],"for",[line[1][3:]]]

def chopLine_while(line):
    return [line[0],"while",[line[1][5:]]]

def chopLine_try(line):
    return [line[0],"try",[]]

def chopLine_catch(line):
    return [line[0],"catch",[line[1][5:]]]

def chopLine_hash(line):
    return [line[0],"#",[line[1][1:]]]

def chopLine_honly(line):
    return [line[0],"honly",[]]

def chopLine_cpponly(line):
    return [line[0],"cpponly",[]]

def chopLine_debug(line):
    return [line[0],"debug",[]]

def chopLine_include(line):
    return [line[0],"include",[]]

def chopLine_default(line):
    return [line[0],"?",[line[1]]]

def chopAllLines(indata):
    chops = {
            "template ":chopLine_template, "namespace ":chopLine_namespace,
            "struct ":chopLine_struct, "class ":chopLine_class, "func ":chopLine_func,
            "private ":chopLine_private, "public ":chopLine_public,
            "if ":chopLine_if, "elif ":chopLine_elif, "else ":chopLine_else,
            "for ":chopLine_for, "while ":chopLine_while,
            "try ":chopLine_try, "catch ":chopLine_catch, "#":chopLine_hash,
            "honly ":chopLine_honly, "cpponly ":chopLine_cpponly, "debug ":chopLine_debug, "include ":chopLine_include
            }
    dar = {
            "private":chopLine_private, "public":chopLine_public, "else":chopLine_else,
            "try":chopLine_try, "honly":chopLine_honly, "cpponly":chopLine_cpponly, "debug":chopLine_debug, "include":chopLine_include
            }
    ou = []
    for linenum in range(len(indata)):
        line = indata[linenum]
        ta = False
        try:
            for x in dar:
                if line[1]==x:
                    ou.append(dar[x](line))
                    ta = True
                    break
            if ta==False:
                for x in chops:
                    if line[1][:len(x)]==x:
                        ou.append(chops[x](line))
                        ta = True
                        break
            if ta==False:
                ou.append(chopLine_default(line))
        except:
            print("Source code syntax error.")
            print("Line: "+str(linenum+1))
            exit()
    return ou

def inject_debugger(indata,inp):
    in_func = False
    func_level = 0
    ou = []
    ou.append([0,"honly",[]])
    ou.append([1,"#",["include \"STEGOSAURUSTRACEBACKDEBUGGER.h\""]])
    for linenum in range(len(indata)):
        line = indata[linenum]
        if line[1]=="?":
            if line[2][0]=="":
                continue
        if line[0]<=func_level:
            in_func = False
        if in_func:
            if (line[1]=="?") or (line[1]=="for") or (line[1]=="while") or (line[1]=="if") or (line[1]=="try"):
                ou.append([line[0],"?",["STEGOSAURUSTRACEBACKDEBUGGER::steg_spot = "+str(linenum+1)]])
            ou.append(line)
        else:
            if line[1]=="func":
                in_func = True
                func_level = line[0]
                ou.append(line)
                ou.append([line[0]+1,"?",["STEGOSAURUSTRACEBACKDEBUGGER::coin MY_DEBUGGING_COIN_NODE(\""+inp+" : "+line[2][0]+line[2][1]+"\")"]])
            else:
                ou.append(line)
    return ou

def remove_empty_lines(indata):
    ou = []
    for line in indata:
        if line[1]=="?":
            if line[2][0]=="":
                continue
        ou.append(line)
    return ou

def addString(ou,s):
    w = s.encode("UTF-8")
    for x in w:
        ou.append(x)

def addReturn(ou):
    ou.append(10)

def addSemicolon(ou):
    ou.append(59)

def isTemplateFunc(s):
    if len(s)==0:
        return [False]
    t = False
    for x in s:
        if x[1]=="template":
            t = True
            m = x
        elif x[1]=="struct":
            t = False
        elif x[1]=="class":
            t = False
    if t:
        return [True,m]
    return [False]

def isFuncInTemplate(s):
    if len(s)==0:
        return [False]
    t = 0
    for x in s:
        if t==0:
            if x[1]=="template":
                t = 1
                m = x
        elif t==1:
            if (x[1]=="struct") or (x[1]=="class"):
                return [True,m,x]
    return [False]

def isMethod(s):
    if len(s)==0:
        return [False]
    for x in s:
        if (x[1]=="class") or (x[1]=="struct"):
            return [True,x]
    return [False]

def isDataMember(s):
    if len(s)<2:
        return False
    t = 0
    for x in s:
        if t==0:
            if (x[1]=="class") or (x[1]=="struct"):
                t = 1
        else:
            if x[1]=="func":
                return False
    if t==0:
        return False
    return True

def isInclude(s):
    for x in s:
        if x[1]=="include":
            return True
    return False

def closeBlock(ou,b,ish):
    if (b=="template") or (b=="private") or (b=="public") or (b=="honly") or (b=="cpponly") or (b=="debug") or (b=="include"):
        return
    if (b=="namespace") or (b=="func") or (b=="if") or (b=="elif") or (b=="else") or (b=="for") or (b=="while") or (b=="try") or (b=="catch"):
        addString(ou,"}")
        addReturn(ou)
        return
    if (b=="class") or (b=="struct"):
        if ish:
            addString(ou,"};")
            addReturn(ou)
        return
    raise "internal error"

def toString(indata,use_debug,ish):
    ou = []
    s = []
    skip_active = False
    skip_to = 0
    for line in indata:
        while True:
            if len(s)==0:
                break
            if s[-1][0]<line[0]:
                break
            closeBlock(ou,s[-1][1],ish)
            s.pop()
        if skip_active:
            if line[0]<=skip_to:
                skip_active = False
            else:
                continue
        if line[1]=="?":
            if isInclude(s):
                addString(ou,"#include ")
                addString(ou,line[2][0])
                addReturn(ou)
            elif (isDataMember(s)==False) or ish:
                addString(ou,line[2][0])
                addSemicolon(ou)
                addReturn(ou)
            continue
        if line[1]=="template":
            if ish:
                addString(ou,"template")
                addString(ou,line[2][0])
                addReturn(ou)
            s.append(line)
            continue
        if line[1]=="namespace":
            addString(ou,"namespace")
            addString(ou,line[2][0])
            addString(ou," {")
            addReturn(ou)
            s.append(line)
            continue
        if (line[1]=="struct") or (line[1]=="class"):
            if ish:
                addString(ou,line[1])
                addString(ou," ")
                addString(ou,line[2][0])
                addString(ou," ")
                addString(ou,line[2][1])
                addString(ou," {")
                addReturn(ou)
            s.append(line)
            continue
        if line[1]=="func":
            h = isTemplateFunc(s)
            if h[0]:
                addString(ou,"template")
                addString(ou,h[1][2][0])
                addString(ou," ")
            del(h)
            addString(ou,line[2][0])
            addString(ou," ")
            if ish:
                addString(ou,line[2][1])
                addSemicolon(ou)
                addReturn(ou)
                skip_active = True
                skip_to = line[0]
                continue
            else:
                g = isMethod(s)
                if g[0]:
                    h = isFuncInTemplate(s)
                    if h[0]:
                        addString(ou,h[2][2][0])
                        addString(ou,h[1][2][1])
                    else:
                        addString(ou,g[1][2][0])
                    addString(ou,"::")
                    del(h)
                del(g)
                addString(ou,line[2][1])
                addString(ou," {")
                addReturn(ou)
                s.append(line)
                continue
        if line[1]=="private":
            if ish:
                addString(ou,"private:")
                addReturn(ou)
            s.append(line)
            continue
        if line[1]=="public":
            if ish:
                addString(ou,"public:")
                addReturn(ou)
            s.append(line)
            continue
        if line[1]=="if":
            addString(ou,"if (")
            addString(ou,line[2][0])
            addString(ou,") {")
            addReturn(ou)
            s.append(line)
            continue
        if line[1]=="elif":
            addString(ou,"else if (")
            addString(ou,line[2][0])
            addString(ou,") {")
            addReturn(ou)
            s.append(line)
            continue
        if line[1]=="else":
            addString(ou,"else {")
            addReturn(ou)
            s.append(line)
            continue
        if line[1]=="for":
            addString(ou,"for (")
            addString(ou,line[2][0])
            addString(ou,") {")
            addReturn(ou)
            s.append(line)
            continue
        if line[1]=="while":
            addString(ou,"while (")
            addString(ou,line[2][0])
            addString(ou,") {")
            addReturn(ou)
            s.append(line)
            continue
        if line[1]=="try":
            addString(ou,"try {")
            addReturn(ou)
            s.append(line)
            continue
        if line[1]=="catch":
            addString(ou,"catch (")
            addString(ou,line[2][0])
            addString(ou,") {")
            addReturn(ou)
            s.append(line)
            continue
        if line[1]=="#":
            addString(ou,"#")
            addString(ou,line[2][0])
            addReturn(ou)
            continue
        if line[1]=="honly":
            if ish:
                s.append(line)
            else:
                skip_active = True
                skip_to = line[0]
            continue
        if line[1]=="cpponly":
            if ish:
                skip_active = True
                skip_to = line[0]
            else:
                s.append(line)
            continue
        if line[1]=="debug":
            if use_debug:
                s.append(line)
            else:
                skip_active = True
                skip_to = line[0]
            continue
        if line[1]=="include":
            if ish:
                s.append(line)
            else:
                skip_active = True
                skip_to = line[0]
            continue
        raise "internal error"
    while len(s)!=0:
        closeBlock(ou,s[-1][1],ish)
        s.pop()
    return ou

def makeHF_h_helper(c):
    u = ord(c)
    if u>=128:
        return c
    if (u>=48) and (u<=57):
        return c
    if (u>=65) and (u<=90):
        return c
    if (u>=97) and (u<=122):
        return c
    return "_"

def makeHF_h(inp,inpfilename):
    g_name = []
    for x in inpfilename:
        g_name.append(makeHF_h_helper(x))
    ou = []
    addString(ou,"#ifndef __STEGOSAURUS_INCLUDE_GUARD_")
    for x in g_name:
        addString(ou,x)
    addReturn(ou)
    addString(ou,"#define __STEGOSAURUS_INCLUDE_GUARD_")
    for x in g_name:
        addString(ou,x)
    addReturn(ou)
    addString(ou,"using namespace std;")
    addReturn(ou)
    ou = ou + inp
    addReturn(ou)
    addString(ou,"#endif")
    addReturn(ou)
    return ou

def makeHF_cpp(inp,hfilename):
    ou = []
    addString(ou,"#include \"")
    addString(ou,hfilename)
    addString(ou,"\"")
    addReturn(ou)
    addString(ou,"using namespace std;")
    addReturn(ou)
    ou = ou + inp
    return ou

def main():
    myargs = getCommandArgs()
    data = loadfile(myargs["inp"])
    removeComments(data)
    data = makeLines(data)
    data = removeNonprintChars(data)
    data = countIndents(data)
    data = chopAllLines(data)
    if myargs["debug"]:
        data = inject_debugger(data,myargs["inp"])
    else:
        data = remove_empty_lines(data)
    h = toString(data,myargs["debug"],True)
    cpp = toString(data,myargs["debug"],False)
    del(data)
    if myargs["hf"]:
        h = makeHF_h(h,myargs["inp"])
        cpp = makeHF_cpp(cpp,myargs["h"])
    savefile(myargs["h"],h)
    savefile(myargs["cpp"],cpp)

main()
