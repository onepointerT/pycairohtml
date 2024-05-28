
from enum import Enum
from .html import HtmlTag
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
