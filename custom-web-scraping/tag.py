from __future__ import annotations
from enum import Enum
import re
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .parse import ParseTag


class TagType(Enum):
    DOCTYPE = "doctype"
    NORMAL = "normal"
    SELF_CLOSING = "self closing"
    COMMENT = "comment"


class Tag:
    def __init__(self, tag_name: str | None = "", attributes: dict[str, str] = {}, content: list['Tag' | str] = []):
        self.tag_name = tag_name
        self.attributes = attributes
        self.content = content

    def __repr__(self, level: int = -1, only_child: bool = False) -> str:
        out = []
        if self.tag_name != "ROOT":
            out.append(f"{'  '*level*(1-only_child)
                          }<{self.tag_name}{repr_attributes(self.attributes)}>")
        if len(self.content) > 1:
            for content in self.content:
                if isinstance(content, str):
                    out.append('  '*level + content)
                else:
                    out.append(content.__repr__(level+1))
        elif self.content:
            content = self.content[-1]
            if isinstance(content, str):
                out.append(content)
            else:
                out.append(content.__repr__(level, True))

        if len(self.content) > 1:
            if self.tag_name != "ROOT":
                out.append(f"{'  '*level}</{self.tag_name}>")
            return '\n'.join(out)
        else:
            return ''.join(out) + f"</{self.tag_name}>"


class Doctype(Tag):
    def __init__(self, legacy_string: str = ""):
        super().__init__()
        self.legacy_string = legacy_string

    def __repr__(self, level: int = -1, only_child: int = False) -> str:
        if self.legacy_string:
            return f"{'  '*level*(1-only_child)}<!DOCTYPE html {self.legacy_string}>"
        else:
            return f"{'  '*level*(1-only_child)}<!DOCTYPE html>"


_attr_pair = r'(?:[^\s\"\'>/=]+)\s*=\s*(?:[^\s\"\'=<>`]+|\'[^\']*\'|"[^"]*")'


def repr_attributes(attributes: dict[str, str]) -> str:
    out = []
    if not attributes:
        return ''
    for key, value in attributes.items():
        out.append(f"{key}={value}")
    return ' ' + ' '.join(out)


class Normal(Tag):
    def __init__(self, parse_tag: 'ParseTag'):
        attributes = {}

        if parse_tag.attributes:
            for attr_pair in re.findall(_attr_pair, parse_tag.attributes):
                key, value = attr_pair.split('=')
                attributes[key.strip()] = value.strip()

        content: list[str | Tag] = []
        for i in parse_tag.content:
            if isinstance(i, (str, Tag)):
                content.append(i)
            else:
                content.append(i.convert())

        super().__init__(parse_tag.tag_name, attributes, content)

    def __repr__(self, level: int = -1, only_child: bool = False) -> str:
        return super().__repr__(level, only_child)


class SelfClosing(Tag):
    def __init__(self, parse_tag: 'ParseTag'):
        assert not parse_tag.content
        attributes = {}

        if parse_tag.attributes:
            for attr_pair in re.findall(_attr_pair, parse_tag.attributes):
                key, value = attr_pair.split('=', 1)
                attributes[key.strip()] = value.strip()

        super().__init__(parse_tag.tag_name, attributes)

    def __repr__(self, level: int = -1, only_child: bool = False) -> str:
        return f"{'  '*level*(1-only_child)}<{self.tag_name}{repr_attributes(self.attributes)} />"


class Comment(Tag):
    def __init__(self, comment: str = "") -> None:
        super().__init__()
        self.comment = comment

    def __repr__(self, level: int = -1, only_child: bool = False) -> str:
        return f"{'  '*level*(1-only_child)}<!-- {self.comment} -->"


class Content(Tag):
    def __init__(self, text: str = "") -> None:
        super().__init__()
        self.text = text.strip()

    def __repr__(self, level: int = -1, only_child: bool = False) -> str:
        return f"{'  '*level*(1-only_child)}{self.text}"
