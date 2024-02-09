from enum import Enum
import re

from .tag import Tag, TagType
from .tag import Doctype, Normal, SelfClosing, Comment, Content


def parse(html: str) -> Tag:
    root_tag = ParseTag(tag_name="ROOT")
    for section in split_html_into_sections(html):
        try:
            root_tag.add(section)
        except ParseError as e:
            print(root_tag)
            print("Current Section:", section)
            raise e
    if root_tag.content:
        previous_content = root_tag.content[-1]
        if isinstance(previous_content, ParseTag):
            if not previous_content.closed:
                raise ParseWarning("Last tag was not closed")
    root_tag.closed = True

    return root_tag.convert()


def split_html_into_sections(html: str) -> list[str]:
    return re.split(r'(?<=>)|(?=<)', html)


class TagSection(Enum):
    OPENING = "opening"
    CONTENT = "content"
    CLOSING = "closing"

    DOCTYPE = "doctype"
    COMMENT = "comment"
    SELF_CLOSING = "self closing"


_tag_name = r'[A-Za-z0-9]+'
_attr_name = r'[^\s\"\'>/=]+'
_attr_value = r'[^\s\"\'=<>`]+|\'[^\']*\'|"[^"]*"'
_attributes = fr'(?:\s+(?:{_attr_name})\s*=\s*(?:{_attr_value}))*'

regex_patterns = {
    TagSection.OPENING: fr'<({_tag_name})({_attributes})\s*>',
    TagSection.CLOSING: fr'</({_tag_name})\s*>',

    TagSection.DOCTYPE: r'<!DOCTYPE\s+html\s*(.*?)\s*>',
    TagSection.COMMENT: r'<!--\s*(.*?)\s*-->',
    TagSection.SELF_CLOSING: fr'<({_tag_name})({_attributes})\s*/>'
}

void_elements = ['area', 'base', 'br', 'col', 'embed', 'hr',
                 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr']


def identify_section(section: str) -> tuple[TagSection | None, list[str]]:
    if re.match(r'^\s*$', section):
        return None, []
    else:
        for section_type, pattern in regex_patterns.items():
            match = re.match(pattern, section, re.IGNORECASE)
            if match:
                return section_type, list(match.groups())
        return TagSection.CONTENT, [section]


class ParseTag:
    def __init__(self, tag_name: str | None = None, attributes: str | None = None) -> None:
        if tag_name == None:
            raise ParseError("Tag name was not specified")
        self.tag_name = tag_name
        self.attributes = attributes
        self.closed = tag_name in void_elements
        self.type = TagType.SELF_CLOSING if tag_name in void_elements else TagType.NORMAL
        self.content: list[ParseTag | Tag | str] = []

    def add(self, section: str) -> None:
        if self.closed:
            raise ParseError("Current tag is already closed")
        section_type, matched_groups = identify_section(section)

        if not section_type:
            return
        if section_type == TagSection.OPENING:
            self.handle_opening_tag(matched_groups)
        elif section_type == TagSection.CLOSING:
            self.handle_closing_tag(matched_groups)
        elif section_type == TagSection.DOCTYPE:
            self.handle_other_tags(Doctype(matched_groups[0]))
        elif section_type == TagSection.COMMENT:
            self.handle_other_tags(Comment(matched_groups[0]))
        elif section_type == TagSection.CONTENT:
            self.handle_other_tags(Content(matched_groups[0]))
        else:
            raise ParseError("Could not classify tag")

    def handle_opening_tag(self, matched_groups: list[str]) -> None:
        tag_name, attributes = matched_groups
        tag_name = tag_name.lower()
        if self.tag_name:
            if self.content:
                previous_content = self.content[-1]
                if isinstance(previous_content, ParseTag):
                    if not previous_content.closed:
                        previous_content.handle_opening_tag(matched_groups)
                        return
            self.content.append(ParseTag(tag_name, attributes))
        else:
            self.tag_name = tag_name
            self.attributes = attributes

    def handle_closing_tag(self, matched_groups: list[str]) -> None:
        closing_tag_name = matched_groups[0].lower()
        if self.tag_name:
            if self.content:
                previous_content = self.content[-1]
                if isinstance(previous_content, ParseTag):
                    if not previous_content.closed:
                        previous_content.handle_closing_tag(matched_groups)
                        return
            if self.tag_name == closing_tag_name:
                self.closed = True
            else:
                raise ParseError(
                    f"Mismatched closing tag </{matched_groups[0]}>")
        else:
            raise ParseError("Encountered closing tag before opening tag")

    def handle_other_tags(self, tag: Tag) -> None:
        if self.tag_name:
            if self.content:
                previous_content = self.content[-1]
                if isinstance(previous_content, ParseTag):
                    if not previous_content.closed:
                        previous_content.handle_other_tags(tag)
                        return
            self.content.append(tag)
        else:
            raise ParseError(f"Encountered {type(tag)} before opening tag")

    def convert(self) -> Tag:
        if self.type == TagType.SELF_CLOSING:
            return SelfClosing(self)
        elif self.type == TagType.NORMAL:
            return Normal(self)
        else:
            raise ParseError

    def __repr__(self, level: int = 0, only_child: bool = False) -> str:
        out = []
        out.append(f"{'  '*level*(1-only_child)}<{self.tag_name}{self.attributes or ''}>")
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
            if self.closed:
                out.append(f"{'  '*level}</{self.tag_name}>")
            return '\n'.join(out)
        else:
            return ''.join(out) + f"</{self.tag_name}>"


class ParseError(Exception):
    pass


class ParseWarning(Warning):
    pass
