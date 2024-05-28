import os.path

from .pycairo.cairo import Context, Format, ImageSurface, TeeSurface, SVGSurface, Surface
from .html import HtmlTag, cacao_html, Stack
from .province_css import CssSurfaceModifier, Color, Font, FontSlant, FontWeight, AlignmentDefinition
from .cacao.py.util import genid


class HtmlSurface(TeeSurface):
    def __init__(self, font_family: str, width: float, height: float):
        self.svg = SVGSurface('./html.svg', width, height)
        super().__init__(self.svg)
        self.ctx = Context(self)
        self.regions = dict()
        self.font = Font(font_family)
        self.css = CssSurfaceModifier(self, self.ctx)

    def make_region(self, width: float, height: float, x: float = 0.0, y: float = 0.0, idnum: str = genid()) -> Surface:
        surface = self.create_for_rectangle(x, y, width, height)
        self.regions[idnum] = surface
        return surface

    def find_surface_id(self, surface: Surface):
        for key in self.regions.keys():
            if self.regions[key] is surface:
                return key
        return ''

    def create_area(self, width: float, height: float, x: float = 0.0, y: float = 0.0) -> Context:
        surface = self.make_region(width, height, x, y)
        self.ctx.set_source_surface(surface, x, y)
        return self.ctx

    def set_main_surface(self):
        self.ctx.set_source_surface(self, 0.0, 0.0)

    def regiondict(self):
        return self.regions

    def tag_open(self, name, attributes=''):
        self.ctx.tag_begin(name, attributes)

    def tag_close(self, name):
        self.ctx.tag_end(name)

    def save(self):
        self.ctx.save()

    def make_text(self, text):
        self.ctx.show_text(text)

    @staticmethod
    def align(context: Context, alignment: AlignmentDefinition) -> str:
        tagname = genid()
        context.tag_begin(tagname, '')
        # Make alignment things from CSS
        context.tag_end(tagname)
        return tagname

    def alignment_area(self, width: float, height: float, alignment: AlignmentDefinition) -> dict:
        current_point = self.ctx.get_current_point()
        regionid = genid()
        surface = self.make_region(width, height, current_point[0], current_point[1], regionid)
        context = Context(surface)
        self.regions[regionid] = dict(regionid=regionid, tag_align=self.align(context, alignment), context=context)
        return self.regions[regionid]

    def do_tag_children(self, html_tag_children: [HtmlTag]):
        for chld in html_tag_children.childs:
            if len(chld.pre_tag) > 0:
                self.make_text(chld.pre_tag)
            self.do_tag(chld)
            if len(chld.post_tag) > 0:
                self.make_text(chld.post_tag)

    def do_tag_content(self, html_tag: HtmlTag):
        pass

    def do_tag_with_children(self, html_tag: HtmlTag):
        # First do all children pre the content tag
        html_pre_children = html_tag.scan_for_children(html_tag.pre_tag)
        self.do_tag_children(html_pre_children)

        # Now do the content of the tag
        self.do_tag_content(html_tag)

        # Finally do all past the tag
        html_post_children = html_tag.scan_for_children(html_tag.post_tag)
        self.do_tag_children(html_post_children)

    def do_tag(self, html_tag: HtmlTag):
        # Open a new cairo tag
        tagname = html_tag.tagname
        tagname_cairo = tagname + '_' + genid()
        self.tag_open(tagname_cairo)

        # Fill the cairo tag with content
        if tagname is '':
            self.make_text(html_tag.content)
        elif html_tag.has_child_tags():
            self.do_tag_children(html_tag.children)
        elif html_tag.has_child_tags():
            self.do_tag_with_children(html_tag)
        else:
            self.do_tag_content(html_tag)

        # Close the cairo tag and save the cairo tagname
        self.tag_close(tagname_cairo)
        html_tag.tagname_cairo = tagname_cairo

        # Return the cairo tagname
        return tagname_cairo

    def html(self, html_tag: HtmlTag):
        if len(html_tag.childs) is 0:
            # Do processing, no childs
            self.do_tag(html_tag)


class TextSurface(Surface):
    def __init__(self, context: Context):
        super().__init__()
        self.ctx = context

    def make_text(self, text: str, font: Font = None):
        if font is not None:
            font_options = self.ctx.get_font_options()
            font_face = self.ctx.get_font_face()
            self.set_font(font)
            self.ctx.show_text(text)
            self.ctx.set_font_options(font_options)
            self.ctx.set_font_face(font_face)
        else:
            self.ctx.show_text(text)
        self.ctx.save()

    def set_font(self, font: Font):
        self.ctx.set_font_size(font.fontsize)
        self.ctx.select_font_face(font.family, font.italic, font.bold)
        self.ctx.set_font_options(font)


class Image:
    png = None
    img = None
    data = None

    @staticmethod
    def from_png(path: str):
        if not os.path.isfile(path):
            return None
        return ImageSurface.create_from_png(path)

    def __init__(self, path: str, width: int, height: int):
        format = Format.ARGB32
        format.stride_for_width(width)
        self.png = self.from_png(path)
        self.img = self.png.create_similar_image(format, width, height)
        self.data = self.img.get_data()

    def create_for_rectangle(self, x: int, y: int):
        return self.img.create_for_rectangle(x, y, self.img.get_width(), self.png.get_height())
