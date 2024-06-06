
from typing import Callable, Any

from .util import Function, Functions, Equation, HtmlTagBasic, HtmlDoc, notin


class CssOperator:
    op = ''
    opfunc = None

    def __init__(self, opstr: str, opfunc: Callable[[str, str, str, HtmlTagBasic], list(HtmlTagBasic)]):
        super().__init__(opstr, opfunc)

    def eval(self, e: str, attr: str, val: str, htmltag: HtmlTagBasic) -> [HtmlTagBasic]:
        return self.opfunc(e, attr, val, htmltag)


class CssOperators(dict):  # S. 133 "Attribute Selectors"
    def __init__(self):
        super().__init__()
        self.registerall()

    def eval(self, op: str, e: str, attr: str, val: str, html: HtmlTagBasic) -> [HtmlTagBasic]:
        return self[op].eval(e, attr, val, html)

    @staticmethod
    def any(e: str, attr: str, val: str, html: HtmlTagBasic) -> [HtmlTagBasic]:
        if html is None:
            return []

        eall = e.split(' ')
        htmlall = html + html.children_tags
        matches = [HtmlTagBasic]
        # Test all tags
        for tag in htmlall:
            # Test, if the element e is same than in definition
            for etest in eall:
                if tag is etest:
                    # Test, if attr is included
                    attributes = tag.attrs
                    for attribute in attributes:
                        if HtmlTagBasic.attr_key(attribute) is attr:
                            matches += tag
                    break

        return matches

    @staticmethod
    def exact(e: str, attr: str, val: str, html: HtmlTagBasic) -> [HtmlTagBasic]:
        htmlany = CssOperators.any(e, attr, val, html)

        matches = [HtmlTagBasic]
        for htmltag in htmlany:
            for attribute in htmltag.attrs:
                if HtmlTagBasic.attr_key(attribute) is not attr:
                    continue
                else:
                    if HtmlTagBasic.attr_val(attribute) is val:
                        matches += htmltag
                    else:
                        break

        return matches

    @staticmethod
    def beginswith(e: str, attr: str, val: str, html: HtmlTagBasic) -> [HtmlTagBasic]:
        eall = CssOperators.any(e, attr, val, html)
        matches = [HtmlTagBasic]

        for htmltag in eall:
            attribute = htmltag.findattr(attr)
            if HtmlTagBasic.attr_val(attribute).startswith(val):
                matches += htmltag

        return matches

    @staticmethod
    def eitherorbegin(e: str, attr: str, val: str, html: HtmlTagBasic) -> [HtmlTagBasic]:
        matches = CssOperators.exact(e, attr, val, html)

        htmlbeginsall = notin(matches, html + html.children_tags)
        for htmltag in htmlbeginsall:
            attribute = htmltag.findattr(attr)
            if HtmlTagBasic.attr_val(attribute).startswith(val):
                matches += htmltag

        return matches

    @staticmethod
    def haswithin(e: str, attr: str, val: str, html: HtmlTagBasic) -> [HtmlTagBasic]:
        eall = CssOperators.any(e, attr, val, html)
        matches = [HtmlTagBasic]

        for htmltag in eall:
            attribute = htmltag.findattr(attr)
            if HtmlTagBasic.attr_val(attribute).__contains__(' ' + val + ' '):
                matches += htmltag

        return matches

    @staticmethod
    def endswith(e: str, attr: str, val: str, html: HtmlTagBasic) -> [HtmlTagBasic]:
        eall = CssOperators.any(e, attr, val, html)
        matches = [HtmlTagBasic]

        for htmltag in eall:
            attribute = htmltag.findattr(attr)
            if HtmlTagBasic.attr_val(attribute).endswith(val):
                matches += htmltag

        return matches

    @staticmethod
    def anywherewithin(e: str, attr: str, val: str, html: HtmlTagBasic) -> [HtmlTagBasic]:
        eall = CssOperators.any(e, attr, val, html)
        matches = [HtmlTagBasic]

        for htmltag in eall:
            attribute = htmltag.findattr(attr)
            if HtmlTagBasic.attr_val(attribute).__contains__(val):
                matches += htmltag

        return matches

    def register(self, operator: CssOperator):
        self[operator.op] = operator

    def registerall(self):
        self.register(CssOperator('any', CssOperators.any))
        self.register(CssOperator('=', CssOperators.exact))
        self.register(CssOperator('|=', CssOperators.eitherorbegin))
        self.register(CssOperator('~=', CssOperators.haswithin))
        self.register(CssOperator('^=', CssOperators.beginswith))
        self.register(CssOperator('$=', CssOperators.endswith))
        self.register(CssOperator('*=', CssOperators.anywherewithin))


css_operators = CssOperators()


class CssFunction(Function):
    def __init__(self, funcstr: str, func: Callable[..., Any]):
        super().__init__(funcstr, func)


class CssFunctions(dict): # S. 137ff "Structural Pseudo Classes"
    def __init__(self):
        super().__init__()
        self.registerall()

    def register(self, funcstr: str, func: Callable[..., Any] = None):
        func = CssFunction(funcstr, func)
        self[func.funcname] = func

    def register(self, func_css: CssFunction):
        self[func_css.funcname] = func_css

    @staticmethod
    def root(html: HtmlTagBasic) -> HtmlTagBasic:
        while html.parent_tag is not None:
            html = html.parent_tag
        return html

    @staticmethod
    def nthchild(n: str, html: HtmlTagBasic) -> HtmlTagBasic | None:
        nint = int(n)
        html.scan_for_children()

        for idx, chld in enumerate(html.children_tags):
            if idx is nint:
                return chld

        return None

    @staticmethod
    def nthlastchild(n: str, html: HtmlTagBasic) -> HtmlTagBasic | None:
        nint = int(n)
        html.scan_for_children()

        for idx, chld in enumerate(html.children_tags.reverse()):
            if idx is nint:
                return chld

        return None

    @staticmethod
    def onlyoftype(e: str, html: HtmlTagBasic) -> [HtmlTagBasic]:
        matches = list(HtmlTagBasic)
        html.scan_for_children()

        for htmlelem in html + html.children_tags:
            if e is str(htmlelem.tag):
                matches += htmlelem

        return matches

    @staticmethod
    def nthoftype(e: str, n: str, html: HtmlTagBasic) -> HtmlTagBasic | None:
        matches = CssFunctions.onlyoftype(e, html)
        nint = int(n)

        for idx, chld in enumerate(matches):
            if idx is nint:
                return chld

        return None

    @staticmethod
    def nthlastoftype(e: str, n: str, html: HtmlTagBasic) -> HtmlTagBasic | None:
        matches = CssFunctions.onlyoftype(e, html)
        nint = int(n)

        for idx, chld in enumerate(matches.reverse()):
            if idx is nint:
                return chld

        return None

    @staticmethod
    def fistchild(html: HtmlTagBasic) -> HtmlTagBasic | None:
        return CssFunctions.nthchild("1", html)

    @staticmethod
    def lastchild(html: HtmlTagBasic) -> HtmlTagBasic | None:
        return CssFunctions.nthlastchild("1", html)

    @staticmethod
    def firstoftype(e: str, html: HtmlTagBasic) -> HtmlTagBasic | None:
        return CssFunctions.nthoftype(e, "1", html)

    @staticmethod
    def lastoftype(e: str, html: HtmlTagBasic) -> HtmlTagBasic | None:
        return CssFunctions.nthlastoftype(e, "1", html)

    @staticmethod
    def onlychild(html: HtmlTagBasic) -> HtmlTagBasic | None:
        return len(html.parent_tag.children_tags) is 1

    @staticmethod
    def empty(e: str, html: HtmlTagBasic) -> HtmlTagBasic | None:
        html.scan_for_children()
        if str(html) is e and len(html.content_doc) is 0 \
            or (html.content_doc.startswith('<!-- ') and html.content_doc.endswith(' -->')):
            return html
        elif str(html) is ('br' or 'input' or '!DOCTYPE' or 'meta'):  # Match empty and void elements
            return html

        return None

    @staticmethod
    def lang(e: str, l: str, html: HtmlTagBasic) -> HtmlTagBasic | None:
        matches = CssOperators.exact(e, 'lang', l, html)
        if len(matches) > 0:
            return matches[0]
        return None

    @staticmethod
    def no(e: str, expression: str, html: HtmlTagBasic) -> [HtmlTagBasic]:
        if expression.__contains__(']['):
            expression.strip('][')
            pos_eq = expression.find('=')
            if pos_eq is -1:
                htmltags = css_operators.eval('any', e, expression, '', html)
            elif expression[pos_eq] is 0:
                htmltags = css_operators.eval('any', e, expression, '', html)
            else:
                val = expression[pos_eq+1:]
                if expression[pos_eq-1].isalpha():
                    attr = expression[:pos_eq-1]
                    htmltags = css_operators.eval('=', e, attr, val, html)
                else:
                    attr = expression[:pos_eq-2]
                    htmltags = css_operators.eval(expression[pos_eq-1:pos_eq], e, attr, val, html)

            return notin(html + html.children_tags, htmltags)
        else:
            matches = [HtmlTagBasic]
            htmltags = html + html.children_tags
            for htmltag in htmltags:
                if str(htmltag) is not expression:
                    matches += htmltag
            return matches

    def registerall(self):
        self.register(CssFunction('root', CssFunctions.root))
        self.register(CssFunction('nth-child', CssFunctions.nthchild))
        self.register(CssFunction('nth-last-child', CssFunctions.nthlastchild))
        self.register(CssFunction('nth-of-type', CssFunctions.nthoftype))
        self.register(CssFunction('nth-last-of-type', CssFunctions.nthlastoftype))
        self.register(CssFunction('first-child', CssFunctions.fistchild))
        self.register(CssFunction('last-child', CssFunctions.lastchild))
        self.register(CssFunction('first-of-type', CssFunctions.firstoftype))
        self.register(CssFunction('last-of-type', CssFunctions.lastoftype))
        self.register(CssFunction('only-child', CssFunctions.onlychild))
        self.register(CssFunction('only-of-type', CssFunctions.onlyoftype))
        self.register(CssFunction('empty', CssFunctions.empty))
        self.register(CssFunction('not', CssFunctions.no))


css_functions = CssFunctions
