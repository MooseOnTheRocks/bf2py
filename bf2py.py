# bf2py.py

"""Brainfuck to python optimizing compiler.

Command line:
bf2py.py file [--datasize | -d] [--cellsize | -c]
"""

# TO-DO:
#   - Implement debug mode.
#   - Shorten while loops with only simple statements to one line.

import argparse
import os
import sys

def compile(*, source, datasize, cellsize):
    code = ""
    indent = [0]
    
    data = "D"
    ptr = "p"
    write = "W"
    read = "R"
    mask = "M"
    
    def nl():
        return '\n' + " " * indent[-1]
    
    code += f"import sys" + nl()
    code += f"{data}=[0]*{datasize}" + nl()
    code += f"{ptr}=0" + nl()
    code += f"def {write}(x):print(chr(x),end='')" + nl()
    code += f"def {read}():c=sys.stdin.read(1);{data}[{ptr}]=ord(c)if len(c)==1else 0" + nl()
    
    if cellsize == 8:
        code += f"{mask}=0xff" + nl()
    elif cellsize == 16:
        code += f"{mask}=0xffff" + nl()
    elif cellsize == 32:
        code += f"{mask}=0xffffffff" + nl()
    
    dptr = 0
    dval = 0
    last = "\0"
    empty = [0]
    
    for c in source:
        if not c in "><+-.,[]": continue
        
        if not c in "><" and last in "><" and dptr:
            code += f"{ptr}{'-' if dptr < 0 else '+'}={abs(dptr)};"
            dptr = 0
            empty = False
        elif not c in "+-" and last in "+-" and dval:
            if cellsize == 0:
                code += f"{data}[{ptr}]{'-' if dval < 0 else '+'}={abs(dval)};"
            else:
                code += f"{data}[{ptr}]=({data}[{ptr}]{'-' if dval < 0 else '+'}{abs(dval)})&{mask};"
            dval = 0
            empty = False
        
        last = c
        
        if c == '>':
            dptr += 1
        elif c == '<':
            dptr -= 1
        elif c == '+':
            dval += 1
        elif c == '-':
            dval -= 1
        elif c == ".":
            code += f"{write}({data}[{ptr}]);"
            empty = False
        elif c == ",":
            code += f"{read}();"
            empty = False
        elif c == "[":
            if not empty:
                code += nl()
            indent.append(len(indent))
            code += f"while {data}[{ptr}]!=0:" + nl()
            empty = True
        elif c == "]":
            indent.pop()
            if empty:
                code += "pass"
            code += nl()
            empty = False
            assert len(indent) > 0, "Unmatched ']'"
    
    assert len(indent) == 1 and indent[0] == 0, "Unmatched '['"
    
    return '\n'.join(filter(None, map(lambda line: line.rstrip(), code.split('\n'))))

if __name__ == "__main__":
    cli_parser = argparse.ArgumentParser()
    cli_parser.add_argument("file",
                            help="Brianfuck file to be compiled.")
    cli_parser.add_argument("-d", "--datasize",
                            help="Specify the number of cells available to the BF runtime (0 for unbounded).",
                            type=int,
                            default=30_000)
    cli_parser.add_argument("-c", "--cellsize",
                            help="Specify the size of each cell (in bytes) available in the BF runtime (0 for unbounded). Will wrap on over/under-flow.",
                            type=int,
                            choices=[0, 8, 16, 32],
                            default=8)
    
    args = cli_parser.parse_args()
    file_in = args.file
    assert os.path.isfile(file_in), "Source file required."
    datasize = args.datasize
    assert datasize >= 1, "Datasize must be at least 1 or 0 (unbounded)."
    cellsize = args.cellsize
    
    with open(file_in) as file:
        source = file.read()
    
    file_out_name = os.path.basename(file_in)
    if file_out_name[-2:] == ".b":
        file_out_name = file_out_name[:-2]
    file_out_name += '.py'
    file_out = os.path.join(os.path.dirname(file_in), file_out_name)
    
    code = compile(source=source, datasize=datasize, cellsize=cellsize)
    with open(file_out, "w") as file:
        file.write(code)