
from .cacao import Cacao, Stack, cacao
from .util import HtmlTagBasic


class HtmlSourceEnvironment(Cacao.Environment):
    def __init__(self):
        super().__init__()
        tagtmpl = Cacao.Template('html', '<###starttag{} ###classes{}>###htmlbody{}</#starttag{}>')
        self.templates['html'] = tagtmpl

        scantmpl = Cacao.Template('scan', '###pre{}<###starttag{} ###classes{}>###htmlbody{}</#starttag{}>###post{}')
        self.templates['scan'] = scantmpl

        scanchldtmpl = Cacao.Template('scan_child', '###pre{}###htmltag{}###post{}')
        self.templates['scan_child'] = scanchldtmpl

        until_tmpl = Cacao.Template('until', '###until{}<')
        self.templates['until'] = until_tmpl


cacao_html = HtmlSourceEnvironment()


class HtmlTag(HtmlTagBasic):
    tagname = ''
    tagname_cairo = ''
    classes = ''
    content = ''
    childs = []

    pre_tag = ''
    post_tag =''

    def __init__(self, tagname: str, classes: str, content: str, pre: str = '', post: str = ''):
        super().__init__(content)
        self.tagname = tagname
        self.tagname_cairo = str()
        self.classes = classes
        self.content = content
        self.children = self.scan_for_children(content)
        self.pre_tag = pre
        self.post_tag = post

    def __iter__(self):
        return self.childs

    def has_child_tags(self):
        return len(self.children) > 1

    def scan_for_children(self, html_tag_str: str, varstack: Stack = Stack()):
        # Read pre and post for the first child
        cacao_html.templates.scan_child.transform(html_tag_str, varstack)
        html_tag_list = list()
        if len(varstack.html_tag) is 0:
            html_tag = HtmlTag('', '', html_tag_str)
            html_tag_list.append(html_tag)
            return html_tag_list
        # Create html tag
        cacao_html.templates.html.transform(varstack.html_tag, varstack)
        varstack.until = str()
        cacao_html.templates.until.transform(varstack.post, varstack)
        html_tag = HtmlTag(varstack.starttag, varstack.classes, varstack.htmlbody, varstack.pre, varstack.until)
        html_tag_list.append(html_tag)

        while len(varstack.post) > 0:
            # Find out, if a tag will follow
            varstack.until = str()
            cacao_html.templates.until.transform(varstack.post, varstack)
            if len(varstack.until) is 0:
                html_tag = HtmlTag('', '', varstack.post)
                html_tag_list.append(html_tag)
                varstack.post = str()
            else:
                # Scan for more children
                html_chlds = self.scan_for_children(varstack.post)
                html_tag_list.append(html_chlds)

        return html_tag_list

    @staticmethod
    def fromSource(html_tag_str: str):
        # Create a new Stack for reading the tags
        varstack = Stack()
        # Read the most outer tag to environment
        cacao_html.templates.scan.transform(html_tag_str, varstack)
        # Create a html tag with the values from stack
        return HtmlTag(varstack.starttag, varstack.classes, varstack.htmlbody, varstack.pre, varstack.post)

    def html(self):

        return self


def html(html_str):
