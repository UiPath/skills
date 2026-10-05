#!/usr/bin/env python3
"""Grade a connector icon (app/element/image.svg) for visibility on a surface.

Mirrors the dark-surface rules documented in the uipath-connector-builder
skill (references/overview.md §Icon), which mirror the periodic build check:

  --surface dark  (default) pipeline rules against Studio Web's #1F1F1F.
                  Instant pass on a prefers-color-scheme:dark rule,
                  currentColor, an embedded <image>, or a backdrop.
  --surface light the same per-shape contrast against #FFFFFF, with any
                  @media (prefers-color-scheme: dark) block ignored. Catches
                  a logo "fixed" by repainting it white (invisible on light).
  --forbid-backdrop  fail when a solid <rect> covers >=90% of the viewBox
                  (the skill says not to add a tile the brand doesn't use).

Exit 0 = visible, 1 = invisible / malformed. One line of reasoning on stdout.
"""
import argparse
import re
import sys
import xml.etree.ElementTree as ET

SHAPES = {"path", "circle", "ellipse", "rect", "polygon", "polyline", "line"}
MIN_CONTRAST = 1.5
NAMED = {
    "black": (0, 0, 0), "white": (255, 255, 255), "red": (255, 0, 0),
    "green": (0, 128, 0), "blue": (0, 0, 255), "gray": (128, 128, 128),
    "grey": (128, 128, 128), "navy": (0, 0, 128), "orange": (255, 165, 0),
    "yellow": (255, 255, 0), "silver": (192, 192, 192),
}
DARK_MEDIA = re.compile(r"@media[^{]*prefers-color-scheme\s*:\s*dark[^{]*\{", re.I)


def local(tag):
    return tag.rsplit("}", 1)[-1]


def strip_dark_media(css):
    out, i = [], 0
    for m in DARK_MEDIA.finditer(css):
        if m.start() < i:
            continue
        out.append(css[i:m.start()])
        depth, j = 1, m.end()
        while j < len(css) and depth:
            depth += {"{": 1, "}": -1}.get(css[j], 0)
            j += 1
        i = j
    out.append(css[i:])
    return "".join(out)


def parse_css(css):
    """Return {selector: {prop: value}} for flat rules (.class / element)."""
    rules = {}
    for sel, body in re.findall(r"([^{}@]+)\{([^{}]*)\}", css):
        props = parse_decls(body)
        for s in sel.split(","):
            rules.setdefault(s.strip(), {}).update(props)
    return rules


def parse_decls(text):
    props = {}
    for decl in (text or "").split(";"):
        if ":" in decl:
            k, v = decl.split(":", 1)
            props[k.strip().lower()] = v.strip()
    return props


def parse_color(v):
    v = (v or "").strip().lower()
    if v in NAMED:
        return NAMED[v]
    m = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", v)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return tuple(int(h[k:k + 2], 16) for k in (0, 2, 4))
    m = re.fullmatch(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+).*\)", v)
    if m:
        return tuple(int(x) for x in m.groups())
    return None


def luminance(rgb):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def own_props(el, rules):
    """Resolution order (low→high): element rule, class rule, attribute, style."""
    props = {}
    props.update(rules.get(local(el.tag), {}))
    for cls in (el.get("class") or "").split():
        props.update(rules.get("." + cls, {}))
    for k in ("fill", "stroke", "opacity", "fill-opacity", "stroke-opacity"):
        if el.get(k) is not None:
            props[k] = el.get(k)
    props.update(parse_decls(el.get("style")))
    return props


def viewbox_area(root):
    vb = (root.get("viewBox") or "").replace(",", " ").split()
    try:
        if len(vb) == 4:
            return float(vb[2]) * float(vb[3])
        return float(root.get("width")) * float(root.get("height"))
    except (TypeError, ValueError):
        return None


def is_backdrop(el, props, area):
    if local(el.tag) != "rect" or not area:
        return False
    fill = props.get("fill", "black")
    if fill in ("none", "transparent"):
        return False
    try:
        w = float(el.get("width", "0").rstrip("%"))
        h = float(el.get("height", "0").rstrip("%"))
    except ValueError:
        return False
    if el.get("width", "").endswith("%"):
        return w * h >= 0.9 * 100 * 100
    return w * h >= 0.9 * area


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("svg")
    ap.add_argument("--surface", choices=("dark", "light"), default="dark")
    ap.add_argument("--forbid-backdrop", action="store_true")
    a = ap.parse_args()

    try:
        raw = open(a.svg, encoding="utf-8").read()
    except OSError as e:
        print(f"FAIL: cannot read {a.svg}: {e}")
        return 1
    if not raw.strip():
        print("FAIL: empty file")
        return 1
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        print(f"FAIL: not valid XML: {e}")
        return 1
    if local(root.tag) != "svg":
        print("FAIL: root element is not <svg>")
        return 1

    css = "".join(s.text or "" for s in root.iter() if local(s.tag) == "style")
    if a.surface == "light":
        css = strip_dark_media(css)
    rules = parse_css(css)
    surface = (0x1F, 0x1F, 0x1F) if a.surface == "dark" else (255, 255, 255)
    area = viewbox_area(root)

    shapes, has_image, has_current = [], False, "currentcolor" in raw.lower()

    def walk(el, inherited):
        nonlocal has_image
        props = dict(inherited)
        props.update(own_props(el, rules))
        if local(el.tag) == "image":
            has_image = True
        if local(el.tag) in SHAPES:
            shapes.append((el, props))
        for child in el:
            if local(child.tag) not in ("defs", "style", "clipPath", "mask", "symbol"):
                walk(child, {k: v for k, v in props.items() if k != "opacity"})

    walk(root, {})

    if a.forbid_backdrop:
        for el, props in shapes:
            if is_backdrop(el, props, area):
                print("FAIL: icon has a full-bleed backdrop <rect> the brand does not use")
                return 1

    if not shapes and not has_image:
        print("FAIL: no drawable shapes")
        return 1

    if a.surface == "dark":
        if re.search(r"prefers-color-scheme\s*:\s*dark", raw, re.I):
            print("PASS: has a prefers-color-scheme: dark rule")
            return 0
        if has_current:
            print("PASS: uses currentColor")
            return 0
        if has_image:
            print("PASS: embeds an <image> bitmap")
            return 0
        for el, props in shapes:
            if is_backdrop(el, props, area):
                print("PASS: solid backdrop rect covers the viewBox")
                return 0
    elif has_current or has_image:
        print("PASS: currentColor / <image> ink is host-resolved")
        return 0

    best = 0.0
    for el, props in shapes:
        try:
            if float(props.get("opacity", "1")) <= 0.5:
                continue
        except ValueError:
            pass
        fill, stroke = props.get("fill"), props.get("stroke")
        if fill is None and stroke is None:
            fill = "black"
        for paint, op_key in ((fill, "fill-opacity"), (stroke, "stroke-opacity")):
            if not paint or paint == "none" or paint.startswith("url("):
                continue
            try:
                if float(props.get(op_key, "1")) <= 0.5:
                    continue
            except ValueError:
                pass
            rgb = parse_color(paint)
            if rgb:
                best = max(best, contrast(rgb, surface))

    hex_surface = "#%02X%02X%02X" % surface
    if best >= MIN_CONTRAST:
        print(f"PASS: best ink contrast {best:.2f}:1 on {hex_surface}")
        return 0
    print(f"FAIL: best ink contrast {best:.2f}:1 on {hex_surface} (< {MIN_CONTRAST}:1)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
