import os.path
from enum import Enum
from os import path
from .html import HtmlTag
from .util import hex_to_int
from ..pycairo.cairo import FontSlant, FontWeight, FontOptions, LineCap, LineJoin, Context, Surface


class Color:
    def __init__(self, red: float, green: float, blue: float, alpha: float):
        self.red = red
        self.green = green
        self.blue = blue
        self.alpha = alpha

    def r(self): return self.red
    def g(self): return self.green
    def b(self): return self.blue
    def a(self): return self.alpha


class Colors(Enum):
    default_black = Color(27.0, 25.0, 23.0, 0.8)


class Font(FontOptions):
    family: ''
    italic: FontSlant.NORMAL
    bold: FontWeight.NORMAL
    fontsize: 13.0
    color: Colors.default_black

    def __init__(self, font_family: str, fontsize: float = 13.0):
        super().__init__()
        self.family = font_family
        self.fontsize = fontsize

    def set_italic(self, slant: FontSlant):
        self.italic = slant

    def set_bold(self, weight: FontWeight):
        self.bold = weight

    def set_color(self, color: Color = Colors.default_black):
        self.color = color
        self.set_custom_palette_color(0, color.r(), color.g(), color.b(), color.a())

    def copy(self):
        font = Font(self.family, self.fontsize)
        font.set_italic(self.italic)
        font.set_bold(self.bold)
        font.set_color(self.color)
        return font


class LineDefinition:
    line_cap: LineCap.SQUARE
    line_join: LineJoin.BEVEL
    color: Colors.default_black
    width: 8.2

    def __init__(self, width: float = 8.2, color: Color = Colors.default_black,
                 line_cap: LineCap = LineCap.SQUARE, line_join: LineJoin = LineJoin.BEVEL):
        self.width = width
        self.color = color
        self.line_cap = line_cap
        self.line_join = line_join


class AlignmentDefinition:
    span_hpx: 0.0  # Horizontal, where 0.0 is flex and every other value is a fixed span
    span_vpx: 0.0  # Vertical, where 0.0 is flex and every other value is a fixed span
    linebreaks: 0.0  # 0.0 means: make a new line, whenever a line is full
    hspace: 1.0
    vspace: 1.0
    lspace: 1.0

    def __init__(self, hspace: float = 1.0, vspace: float = 1.0, linebreaks: float = 0.0,
                 span_hpx: float = 0.0, span_vpx: float = 0.0, lspace: float = 0.0):
        self.span_hpx = span_hpx
        self.span_vpx = span_vpx
        self.linebreaks = linebreaks
        self.hspace = hspace
        self.vspace = vspace
        self.lspace = lspace


class Pixel(float):
    def __init__(self, px: float):
        super().__init__(px)


class CssValue(str):
    def __init__(self, value: str):
        super().__init__(value)

    def as_color(self) -> Color:
        if self[0] is not '#' or len(self) < 7:
            return None
        r = self[1:2]
        g = self[3:4]
        b = self[5:6]
        return Color(hex_to_int(r), hex_to_int(g), hex_to_int(b), 1.0)


    def as_pixel(self) -> Pixel:
        if self.__reversed__()[:1] is not 'xp':
            return None
        return Pixel(float(str(self.__reversed__()[2:]).__reversed__().__str__()))

    def as_int(self) -> int:
        return int(float(self))


class CssPair(str):
    value: ''
    values: [CssValue]

    @staticmethod
    def value_tokens(value):
        values = value.split(' ')
        lst = [CssValue]
        for value in values:
            cssval = CssValue(value)
            lst.append(cssval)
        return lst

    def __init__(self, key: str, value: str):
        super().__init__(key)
        self.value = value
        self.values = self.value_tokens(value)


class CssAttribute(CssPair):
    def __init__(self, key: str, value: str):
        super().__init__(key, value)

    @staticmethod
    def parse(lane: str):
        pos_key_end = lane.find(':')
        pos_value_end = lane.find(';', pos_key_end)
        key = lane[:pos_key_end-1]
        value = lane[pos_key_end+2:pos_value_end-1]
        return CssAttribute(key, value)


class CssClass:
    class Name(str):
        def __init__(self, cls_str: str):
            super().__init__(cls_str)

        def __str__(self):
            return self[1:]

    classname: ''
    classnames: [Name]
    htmltag: ''
    attributes: [CssAttribute]

    @staticmethod
    def parse(cls_str: str):
        # Find all needed parameters
        pos_open_bracket = cls_str.find('{')
        pos_first_lane = cls_str.find('\n', pos_open_bracket) + 1
        pos_last_lane = cls_str.find('}', pos_first_lane) - 2
        lane_one = cls_str[:pos_open_bracket]
        lanes_attributes = cls_str[pos_first_lane:pos_last_lane]

        # Parse html tags, classnames and attributes
        cssclass = CssClass.parse_first_lane(lane_one)
        attrs = CssClass.parse_attributes(lanes_attributes)

        return dict(cssclass=cssclass, attrs=attrs)

    @staticmethod
    def parse_first_lane(cls_str: str) -> dict:
        # Find all needed parameters
        last_cls_name_start = cls_str.rfind(' .')
        first_html_tag = cls_str.find(' ', last_cls_name_start) + 1
        tokens = cls_str[:first_html_tag-2].split(' ')

        # Parse
        classnames = [CssClass.Name]
        for token in tokens:
            if token[0] is '.':
                classnames += CssClass.Name(token)
            else:
                break

        return dict(classes=cls_str[:first_html_tag-2], classnames=classnames, html_tags=cls_str[first_html_tag:])

    @staticmethod
    def parse_attributes(self, attr_str: str) -> [CssAttribute]:
        # Find all needed parameters
        attr_list = attr_str.split('\n')
        lst = [CssAttribute]

        # Parse
        for attr in attr_list:
            lst += CssAttribute.parse(attr)

        return lst

    def __init__(self, cls_str: str):
        parsed = self.parse(cls_str)
        self.classname = parsed['cssclass']['classes']
        self.classnames = parsed['cssclass']['classnames']
        self.htmltag = parsed['cssclass']['html_tags']
        self.attributes = parsed['attrs']


class CssFile:
    @staticmethod
    def parse(css_file: str):
        classes = [CssClass]
        lanes = css_file.split('\n')

        pos_last_dot = 0
        pos_last_closing_brace = 0
        for idx, lane in enumerate(lanes):
            if lane.startswith('.'):
                pos_last_dot = idx
            elif lane.startswith('}'):
                pos_last_closing_brace = idx
            elif pos_last_dot < pos_last_closing_brace:
                cls_str = str()
                cls_lanes = lanes[pos_last_dot:pos_last_closing_brace]
                for string in cls_lanes:
                    cls_str += string + '\n'

                classes += CssClass(cls_str)

        return classes

    def __init__(self, path: str):
        self.path = path
        self.classes = [CssClass]

        if os.path.isfile(path):
            with open(path, 'r') as f:
                self.classes = self.parse(f.read())


class CssSurfaceModifier:
    def __init__(self, surface: Surface, context: Context = None):
        self.surface = surface
        if context is None:
            self.ctx = Context(surface)
        else:
            self.ctx = context

    def set_rgb(self, color: Color):
        self.ctx.set_source_rgb(color.r(), color.g(), color.b())

    def set_rgba(self, color: Color):
        self.ctx.set_source_rgba(color.r(), color.g(), color.b(), color.a())

    def draw_line(self, hend: float, vend: float, linedef: LineDefinition = LineDefinition()):
        # Modify line width, if modifier
        lw = self.ctx.get_line_width()
        self.ctx.set_line_width(linedef.width)

        # Modify line fill, if modifier
        self.set_rgba(linedef.color)

        # Modify line modifier
        lcap = self.ctx.get_line_cap()
        ljoin = self.ctx.get_line_join()
        self.ctx.set_line_cap(linedef.line_cap)
        self.ctx.set_line_join(linedef.line_join)

        # Draw a line
        self.ctx.rel_line_to(hend, vend)

        # Reset the environment
        self.ctx.set_line_width(lw)
        self.ctx.set_line_cap(lcap)
        self.ctx.set_line_join(ljoin)


class TableModifier(CssSurfaceModifier):
    def __init__(self, surface: Surface, context: Context = None):
        super().__init__(surface, context)

    def draw_table(self, html_tag: HtmlTag):
        pass
