
from abc import ABC, abstractmethod
import operator
import os.path
import re
import sys
import shutil
import tempfile
import urllib.request
from typing import Any, AnyStr, Callable


def hex_to_int(hex: str) -> int:
    return int(hex, 16)


def int_to_hex(integer: int) -> str:
    return str(hex(integer))


def ifnonot(o: Any) -> str:
    if o is not None:
        return str(o)
    return str()


def percent(p: str) -> float:
    if len(p) is 0:
        return 1.0
    elif p[len(p)-1] is '%':
        return int(p[:len(p)-2])/100
    else:
        return 1.0


def op_to_func_numeric(opstr: str) -> Callable[[Any, Any], Any] | None:
    if opstr.find('/'):
        return operator.__truediv__
    elif opstr.find('*'):
        return operator.__mul__
    elif opstr.find('+'):
        return operator.__add__
    elif opstr.find('-'):
        return operator.__sub__
    return None


def intersection(l1: list, l2: list) -> list:
    match = list()
    for e in l1:
        if e in l2:
            match += e
    return match


def notin(l1: list, l2: list) -> list:
    intersec = intersection(l1, l2)
    both = l1 + l2
    match = list()
    for idx, e in enumerate(both):
        if e not in intersec:
            match += e
            continue
    return match


class PathBasic(str):
    prefix: str

    def __init__(self, pathstr: str, prefix: str = str()):
        super().__init__(pathstr)
        self.prefix = prefix

    def __str__(self):
        return str(super())


class DirectoryPath(PathBasic):
    path: str

    def __add__(self, other):
        if sys.platform is 'win32' or 'win64':
            return self + '\\' + other
        return self + '/' + other

    @staticmethod
    def parse(pathstr: str) -> dict:
        dct = dict()
        if sys.platform is 'win32' or 'win64':
            pos_prefix_end = pathstr.find(':\\')
            if pos_prefix_end > -1:
                dct['prefix'] = pathstr[:pos_prefix_end-1]
                dct['path'] = pathstr[pos_prefix_end+2:]
            elif pathstr.startswith('\\\\'): # e.g. \\wsl.localhost\Ubuntu
                pos_prefix_start = pathstr.find('\\\\')
                pos_prefix_end = pathstr.find('\\', pos_prefix_start)
                dct['prefix'] = pathstr[:pos_prefix_end+1]
                if len(pathstr) > pos_prefix_end+2: # e.g. \\wsl.localhost\Ubuntu
                    dct['path'] = pathstr[pos_prefix_end+2]
                else: # e.g. \\wsl.localhost\
                    dct['path'] = str()
            else:  # Generic path without prefix, e.g. Home, Network, etc.
                dct['prefix'] = str()
                dct['path'] = pathstr
        else:
            pos_prefix_end = pathstr.find('://')
            if pos_prefix_end > -1:
                dct['prefix'] = pathstr[:pos_prefix_end-1]
                dct['path'] = pathstr[pos_prefix_end+3:]
            elif pathstr.startswith('/'):
                dct['prefix'] = '/'
                dct['path'] = pathstr
            elif pathstr.startswith('~'):
                dct['prefix'] = '~/'
                dct['path'] = pathstr
            else:
                dct['prefix'] = str()
                dct['path'] = pathstr
        return dct

    def __init__(self, pathstr: str):
        super().__init__(pathstr)
        dct = self.parse(pathstr)
        self.prefix = dct['prefix']
        self.path = dct['path']

    def __str__(self):
        return str(super())


class FilePath(DirectoryPath):
    filename: str
    directory: super()

    @staticmethod
    def parse(pathstr: str) -> dict:
        dct = dict()
        if sys.platform is 'win32' or 'win64':
            pos_filename_start = pathstr.rfind('\\')
            dct['filename'] = pathstr[pos_filename_start+1:]
        else:
            pos_filename_start = pathstr.rfind('/')
            dct['filename'] = pathstr[pos_filename_start+1:]
        return dct

    def __init__(self, pathstr: str):
        super().__init__(pathstr)
        dct = self.parse(pathstr)
        self.filename = dct['filename']

    def __str__(self):
        return str(self.directory + self.filename)

    def read(self) -> AnyStr:
        with open(str(self.directory + self.filename), 'r') as f:
            return f.read()


class Url(PathBasic):
    domain: str
    domain_prefix: str
    tld: str
    urlpath: str

    @staticmethod
    def parse(urlstr: str) -> dict:
        dct = dict()
        pos_prefix_end = urlstr.find('://')
        if pos_prefix_end < 0:
            pos_prefix_end = -3
        else:
            dct['prefix'] = urlstr[:pos_prefix_end-1]
        end_domain = re.findall('\\..*/', urlstr)
        if len(end_domain) is 0:
            end_domain = re.findall('\\..*', urlstr)
            dct['tld'] = end_domain[len(end_domain)-1]
            dct['urlpath'] = str()
        else:
            dct['tld'] = end_domain[len(end_domain)-1]
            pos_url_path = urlstr.find(dct['tld']) + len(dct['tld']) + 1
            dct['urlpath'] = urlstr[pos_url_path:]
        pos_tld = urlstr.find(dct['tld'])
        pos_domain_prefix = urlstr.rfind('.', pos_tld)
        if pos_domain_prefix > -1:  # There is a domain prefix
            dct['domain_prefix'] = urlstr[pos_prefix_end+3:pos_domain_prefix-1]
            dct['domain'] = urlstr[pos_domain_prefix:pos_tld+len(dct['tld'])-1]
        else:  # There is just a domain given, like example.com
            dct['domain'] = urlstr[pos_prefix_end+3:pos_tld+len(dct['tld'])-1]
            dct['domain_prefix'] = str()

        return dct

    class FetchBuffer(DirectoryPath):
        files = [FilePath]

        def __init__(self, pathstr: str):
            super().__init__(pathstr)
            self.files = []

        def add_file(self, filename) -> FilePath:
            file = FilePath(self + filename)
            if os.path.exists(self + filename) or self + filename in self.files:
                return self.files[self.files.index(self + filename)]
            self.files.append(file)
            return file

        def get_file(self, filename) -> FilePath:
            for file in self.files:
                if file.filename is filename:
                    return file
            return self.add_file(filename)

    def __init__(self, urlstr: str):
        super().__init__(urlstr)
        dct = self.parse(urlstr)
        self.domain = dct['domain']
        self.domain_prefix = dct['domain_prefix']
        self.prefix = dct['prefix']
        self.tld = dct['tld']
        self.urlpath = dct['urlpath']

    def __str__(self):
        prefix = self.prefix + '://' if len(self.prefix) > 0 else ''
        suffix = '/' + self.urlpath if len(self.urlpath) > 0 else ''
        return prefix + self.domain + suffix

    def filename(self):
        pos_filename_start = str('/' + self.urlpath).rfind('/') if len(self.urlpath) > 0 else 0
        return str() if len(self.urlpath) is 0 else str(self.urlpath[pos_filename_start:])

    def fetch(self, filename: str, fetch_buffer: FetchBuffer) -> FilePath:
        fetch_file = fetch_buffer.get_file(filename)
        with urllib.request.urlopen(self) as response:
            with tempfile.NamedTemporaryFile(dir=fetch_file.directory, delete=False) as tmp_file:
                shutil.copyfileobj(response, tmp_file)
        return fetch_file


class HtmlTagBasic(str):
    attrs = list(str)
    closing = False
    content_doc = ''

    parent_tag = None
    children_tags = list()

    def __init__(self, tag_str: str):
        dct = self.parse_tag(tag_str)
        self.join(dct['tagname'])
        self.attrs = dct['attrs']
        self.closing = dct['closing']

    def findattr(self, attrkey: str) -> str:
        for attr in self.attrs:
            if HtmlTagBasic.attr_key(attr) is attrkey:
                return attrkey
        return str()

    @staticmethod
    def parse_tag(tag_str: str):
        if tag_str.startswith('</'):
            dct = dict(closing=True)
            tag = tag_str[2:tag_str.find('>')-1].removeprefix(' ').removesuffix(' ')
        elif tag_str.startswith('<'):
            dct = dict(closing=False)
            tag = tag_str[1:tag_str.find('>')-1].removeprefix(' ').removesuffix(' ')
        else:
            return dict()

        attrs = tag.split(' ')
        dct['tagname'] = attrs[0]
        dct['attrs'] = attrs[1:]

        return dct

    @staticmethod
    def attr_key(attr: str) -> str:
        pos_equiv = attr.find('=')
        if pos_equiv is -1:
            return str()
        return attr[:pos_equiv-1]

    @staticmethod
    def attr_val(attr: str) -> str:
        pos_opening = attr.find('"')
        pos_closing = attr.find('"', pos_opening)
        if pos_opening is -1 or pos_closing is -1:
            return str()
        return attr[pos_opening+1:pos_closing-1]

    def scan_for_children(self):
        if len(self.children_tags) > 0:
            return

        self.children_tags = HtmlDoc(self.content_doc)

        for chld in self.children_tags:
            chld.parent_tag = self


class HtmlDoc(list(HtmlTagBasic)):
    doc = ''

    def __init__(self, filepath: str = str()):
        if os.path.isfile(filepath):
            with open(filepath, 'r') as f:
                file = f.read()
                super().__init__(HtmlDoc.scan_for_tags(file))
                self.doc = file
        elif len(filepath) > 0:
            super().__init__(HtmlDoc.scan_for_tags(filepath))
        else:
            super().__init__()

    def __iter__(self):
        return self

    @staticmethod
    def parse_tag_lane(tag_str: str) -> HtmlTagBasic:
        pos_closing_tag = tag_str.find('>')

        if pos_closing_tag is -1:
            raise TypeError

        return HtmlTagBasic(tag_str.removeprefix(' ')[:pos_closing_tag-1])

    @staticmethod
    def count_ident(lane: str) -> int:
        return (len(lane.removeprefix(' ')) - len(lane)) * (-1)

    @staticmethod
    def scan_for_tags(html_source_str: str) -> [HtmlTagBasic]:
        lanes = html_source_str.splitlines(keepends=True)
        tags = [HtmlTagBasic]

        newtag = True
        closing_tag_reached = False
        prefix_ident = 0
        tag_content = str()
        for idx, lane in enumerate(lanes):
            if newtag:
                tag_content = str()
                newtag = False
                closing_tag_reached = False

            lane_nows = lane.removeprefix(' ').removesuffix(' ')
            if lane_nows.startswith('</') and HtmlDoc.count_ident(lane) is prefix_ident:
                closing_tag = lane_nows[2:lane_nows.find('>')]
                tag_content += lane_nows[lane_nows.find('>'):]
                newtag = True
                closing_tag_reached = True
            elif lane_nows.startswith('<'):
                opening_tag = lane_nows[1:lane_nows.find('>')]
                tag_content += lane_nows[lane_nows.find('>'):]
                closing_tag_reached = False
                prefix_ident = HtmlDoc.count_ident(lane)
            else:
                tag_content += lane_nows

            if not newtag and closing_tag_reached:
                tag = HtmlTagBasic(opening_tag)
                tag.content_doc = tag_content
                newtag = True
                tags += tag

        return tags



class Equation:
    operand1 = ''
    operand2 = ''
    op = ''

    def __init__(self, op1: str, op2: str, op: str):
        self.operand1 = op1
        self.operand2 = op2
        self.op = op


class Operator:
    op = ''
    opfunc = None

    def __init__(self, opstr: str, opfunc: Callable[[str, str, ...], bool]):
        self.op = opstr
        self.opfunc = opfunc

    def iop(self, operand1: str, operand2: str) -> bool:
        return self.__iop__(operand1, operand2)

    def __iop__(self, operand1: str, operand2: str) -> bool:
        return self.opfunc(operand1, operand2)

    def eq(self, equation: Equation) -> bool:
        return self.iop(equation.operand1, equation.operand2)


class Operators(dict):
    def register(self, operator: Operator):
        self[operator.op] = operator

    def eq(self, equation: Equation) -> bool:
        if self[equation.op] is None:
            return False
        return self[equation.op].eq(equation)


class Function:
    funcname = ''
    parameters = list(str)
    func = None

    def __init__(self, funcstr: str, func: Callable[..., Any] = None):
        funcattrs = self.parse(funcstr)
        self.funcname = funcattrs['funcname']
        self.parameters = funcattrs['parameters']
        self.func = func

    def call(self, parameters: list(str)) -> list:
        return self.func(parameters)

    @staticmethod
    def parse(funcstr: str) -> dict:
        pos_opening_bracket = funcstr.find('(')
        pos_closing_bracket = funcstr.rfind(')')

        if pos_opening_bracket is -1 or pos_closing_bracket is -1:
            return dict(funcname=funcstr)

        parameters_str = funcstr[pos_opening_bracket+1:pos_closing_bracket-1]
        parameters = Function.parse_parameters(parameters_str)

        return dict(funcname=funcstr[:pos_opening_bracket-1], parameters=parameters)

    @staticmethod
    def parse_parameters(parameters_str: str) -> list(str):
        if parameters_str.__contains__(','):
            tokens = parameters_str.split(',')
        else:
            tokens = [parameters_str]

        for idx, token in tokens:
            if token.startswith(' '):
                tokens[idx] = token.removeprefix(' ')

        return tokens


class Functions(dict):
    def register(self, funcstr: str, func: Callable[..., Any] = None):
        func = Function(funcstr, func)
        self[func.funcname] = func

    def call(self, funcname: str, parameters: list(str)) -> list:
        if self[funcname] is None:
            return list(str)

        return self[funcname].call(parameters)
