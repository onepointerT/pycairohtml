
from abc import ABC, abstractmethod
import os.path
from typing import Callable


def hex_to_int(hex: str) -> int:
    return int(hex, 16)


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

    def scan_for_children(self):
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

    def


class Operator:
    op = ''
    opfunc = None

    def __init__(self, opstr: str, opfunc: Callable[[str, str], bool]):
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

    def __init__(self, funcstr: str, func: Callable[[[str]], list] = None):
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
    def register(self, funcstr: str, func: Callable[[[str]], list] = None):
        func = Function(funcstr, func)
        self[func.funcname] = func

    def call(self, funcname: str, parameters: list(str)) -> list:
        if self[funcname] is None:
            return list(str)

        return self[funcname].call(parameters)
