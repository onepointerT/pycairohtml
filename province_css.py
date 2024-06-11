
import os.path
from enum import Enum
from .html import HtmlTag
from .util import hex_to_int, int_to_hex, ifnonot
from .utilcss import HtmlTagBasic, css_functions, css_operators, css_selectors
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

    def to_colorcode(self):
        r = int_to_hex(int(self.red))
        g = int_to_hex(int(self.green))
        b = int_to_hex(int(self.blue))
        return ColorCode('#' + r + g + b)


class ColorCode:
    code = str()

    def __init__(self, color_code: str = '#ffffff'):
        self.code = color_code
        if color_code[0] is not '#' or len(color_code) is not 7:
            raise TypeError("'{0}' is not a color code.".format(color_code))

    def to_rgba(self):
        r = hex_to_int(self.code[1:2])
        g = hex_to_int(self.code[3:4])
        b = hex_to_int(self.code[5:6])
        return Color(r, g, b, 1.0)


class Colors(Enum):
    default_black = Color(27.0, 25.0, 23.0, 0.8)


class Font(FontOptions):
    class Style:
        normal = 0,
        italic = 1,
        bold = 2,
        underlined = 3,
        italicbold = 4,
        italicunderlined = 5,
        boldunderlined = 6,
        italicboldunderlined = 7


    class Family:
        serif = 0,
        sans = 1,
        sansserif = 2,
        monospace = 3,
        cursive = 4

    name: ''
    family: Family.serif
    italic: FontSlant.NORMAL
    bold: FontWeight.NORMAL
    fontsize: 13.0
    color: Colors.default_black

    def __init__(self, font_name: str, font_family: Family, font_size: float = 13.0):
        super().__init__()
        self.name = font_name
        self.family = font_family
        self.fontsize = font_size

    def set_italic(self, slant: FontSlant):
        self.italic = slant

    def set_bold(self, weight: FontWeight):
        self.bold = weight

    def set_color(self, color: Color = Colors.default_black):
        self.color = color
        self.set_custom_palette_color(0, color.r(), color.g(), color.b(), color.a())

    def copy(self):
        font = Font(self.name, self.family, self.fontsize)
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

    def as_color(self) -> Color | None:
        if self[0] is not '#' or len(self) < 7:
            return None
        r = self[1:2]
        g = self[3:4]
        b = self[5:6]
        return Color(hex_to_int(r), hex_to_int(g), hex_to_int(b), 1.0)


    def as_pixel(self) -> Pixel | None:
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


class CssAttributes(list):

    def __init__(self):
        super().__init__()

    def find(self, attribute_key: str) -> CssAttribute | None:
        for attr in self:
            if attr is attribute_key:
                return attr
        return None

    def add(self, css_attribute: CssAttribute):
        self.append(css_attribute)


class CssBorderWidthProperty(Enum):
    medium = 0,
    thin = 1,
    thick = 2,
    length = 3,
    initial = 4,
    inherit = 5


class CssBorderStyleProperty(Enum):
    none = 0,
    hidden = 1,
    dotted = 2,
    dashed = 3,
    solid = 4,
    double = 5,
    groove = 6,
    ridge = 7,
    inset = 8,
    outset = 9,
    initial = 10,
    inherit = 11


class CssTextAlignProperty(Enum):
    left = 0,
    right = 1,
    center = 2,
    justify = 3,
    initial = 4,
    inherit = 5,


class CssBorderWidth([int, int, int, int]):
    def __init__(self, toppx: int = 0, bottompx: int = 0, leftpx: int = 0, rightpx: int = 0):
        super().__init__([toppx, bottompx, leftpx, rightpx])

    @staticmethod
    def new(topbottompx: int = 0, leftrightpx: int = 0):
        return CssBorderWidth(topbottompx, topbottompx, leftrightpx, leftrightpx)

    @staticmethod
    def new(allpx: int = 0):
        return CssBorderWidth(allpx, allpx, allpx, allpx)
    @staticmethod
    def new(toppx: int = 0, bottompx: int = 0, leftpx: int = 0, rightpx: int = 0):
        return CssBorderWidth(toppx, bottompx, leftpx, rightpx)

    @staticmethod
    def new(width: CssBorderWidthProperty = CssBorderWidthProperty.inherit):
        return CssBorderWidth.new(1, 1) # TODO


class CssBorder:
    px = Pixel
    style = CssBorderStyleProperty
    color_code = ColorCode

    def __init__(self, pixel: int = 0, style: CssBorderStyleProperty = CssBorderStyleProperty.hidden,
                 color: ColorCode = Colors.default_black.value.to_colorcode()):
        self.px = pixel
        self.style = style
        self.color_code = color


class CssAlignment(CssAttributes):
    margin = 0
    border_width = CssBorderWidth
    border_left = CssBorder
    border_right = CssBorder
    border_top = CssBorder
    border_bottom = CssBorder

    def __init__(self):
        super().__init__()
        self.border_width = CssBorderWidth()
        self.border_left = CssBorder()
        self.border_right = CssBorder()
        self.border_top = CssBorder()
        self.border_bottom = CssBorder()


class CssClass:
    class Name(str):
        def __init__(self, cls_str: str):
            super().__init__(cls_str)

        def __str__(self):
            return self[1:]

    classname: ''
    classnames: [Name]
    htmltag: HtmlTagBasic
    attributes: CssAttributes

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


class CssFont:
    style: Font.Style
    family: Font.Family
    name: str

    def __init__(self, font_style: Font.Style, font_family: Font.Family, font_name: str = 'arial'):
        self.style = font_style
        self.family = font_family
        self.name = font_name

    @staticmethod
    def new(css_attribute: CssAttribute):
        css_values = css_attribute.values

        italic = False
        bold = False
        underlined = False
        font_family = Font.Family.serif
        name_now = False
        font_name = 'arial'
        for value in css_values:
            if value.find('italic') > -1:
                italic = True
            if value.find('bold') > -1:
                bold = True
            if value.find('underlined') > -1:
                underlined = True

            if value.find('sans-serif') > -1:
                font_family = Font.Family.sansserif
                name_now = True
            elif value.find('sans') > -1:
                font_family = Font.Family.sans
                name_now = True
            elif value.find('monospace') > -1:
                font_family = Font.Family.monospace
                name_now = True
            elif value.find('cursive') > -1:
                font_family = Font.Family.cursive
                name_now = True
            if name_now:
                pos_comma = value.find(',')
                if pos_comma > -1:
                    font_name = value[:pos_comma-1]

        font_style = Font.Style.normal
        if underlined and bold and italic:
            font_style = Font.Style.italicboldunderlined
        elif underlined and bold:
            font_style = Font.Style.boldunderlined
        elif underlined and italic:
            font_style = Font.Style.italicunderlined
        elif bold and italic:
            font_style = Font.Style.italicbold
        elif bold:
            font_style = Font.Style.bold
        elif italic:
            font_style = Font.Style.italic
        elif underlined:
            font_style = Font.Style.underlined

        return CssFont(font_style, font_family, font_name)

    @staticmethod
    def new(css_class: CssClass):
        # Find font-style, font-family, font-size
        font_style = css_class.attributes.find('font-style')
        font_size = css_class.attributes.find('font-size')
        font_family = css_class.attributes.find('font-family')

        css_attribute_value = ifnonot(font_style) + ' ' + ifnonot(font_size) + ' ' + ifnonot(font_family)
        css_attribute = CssAttribute('font', css_attribute_value)
        return CssFont.new(css_attribute)


class CssAttributeSelector:
    funcname = ''
    eq = None
    def __init__(self, attr_str: str):
        attrs = self.parse(attr_str)
        self.funcname = attrs['funcname']
        self.eq = CssEquation(attrs['eqstr'])

    @staticmethod
    def parse(attr_str: str) -> dict:
        pos_left_bracket = attr_str.find('[')
        pos_right_bracket = attr_str.find(']')

        funcname = attr_str[:pos_left_bracket-1]
        eqstr = attr_str[pos_left_bracket+1:pos_right_bracket-1]

        return dict(funcname=funcname, eqstr=eqstr)


class CssSelector:
    attr = ''

    def __init__(self, cls_str: str):
        self.attr = self.parse(cls_str)

    def eval(self, html: HtmlTagBasic):
        return css_selectors.eval(self.attr, html)

    @staticmethod
    def parse(cls_str: str) -> str:
        pos_double_point = cls_str.find(':')

        reststr = cls_str[pos_double_point+1:]
        for idx, char in enumerate(reststr):
            if char.isalpha():
                continue
            else:
                return reststr[:idx-1]
        return str()


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


class Css:
    classes = [CssClass]
    attributes = [CssAttribute]

    def __init__(self):
        pass

    def append(self, css_file: CssFile):
        pass


class CssContext(Context):
    surface = None
    css = None
    
    def __init__(self, surface: Surface, css: Css):
        super().__init__(surface)
        self.surface = surface
        self.css = css


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
