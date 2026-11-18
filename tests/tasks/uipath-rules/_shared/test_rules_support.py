"""Builds a decisionTable element for policy_check tests (mirrors uipath-rules' test helper)."""
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

import policy_check as pc

NS = pc.rc.DMN_NS


def table(hit_policy, rows):
    xml = [f'<decisionTable xmlns="{NS}" hitPolicy="{hit_policy}">']
    xml += [f"<input><inputExpression><text>{name}</text></inputExpression></input>" for name in pc.INPUTS]
    xml += [f'<output name="{pc.OUTPUT}"/>']
    for cells, value in rows:
        xml.append("<rule>")
        xml += [f"<inputEntry><text>{escape(cell)}</text></inputEntry>" for cell in cells]
        xml.append(f'<outputEntry><text>"{value}"</text></outputEntry></rule>')
    xml.append("</decisionTable>")
    return ET.fromstring("".join(xml))
