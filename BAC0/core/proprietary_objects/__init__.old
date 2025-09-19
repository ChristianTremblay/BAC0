from typing import Any as Optional

from bacpypes3.errors import InvalidTag
from bacpypes3.primitivedata import Tag, TagClass, TagList, TagNumber, Unsigned


class OptionalUnsigned(Unsigned):
    """
    This is a special case where a vendor will send NULL values for Unsigned
    """

    @classmethod
    def decode(cls, tag_list: TagList) -> Optional[Unsigned]:
        """Decode an unsigned element from a tag list."""

        tag: Optional[Tag] = tag_list.pop()
        if not tag:
            raise InvalidTag("unsigned application tag expected")
        if tag.tag_class == TagClass.application:
            if cls._context is not None:
                raise InvalidTag(f"unsigned context tag {cls._context} expected")
            if tag.tag_number != TagNumber.unsigned:
                if tag.tag_number == TagNumber.null:
                    return None
                else:
                    raise InvalidTag(
                        f"unsigned application tag expected, got {tag.tag_number}"
                    )
        elif tag.tag_class == TagClass.context:
            if cls._context is None:
                raise InvalidTag("unsigned application tag expected")
            if tag.tag_number != cls._context:
                raise InvalidTag("mismatched context")
        else:
            raise InvalidTag("unexpected opening/closing tag")
        if len(tag.tag_data) < 1:
            raise InvalidTag("invalid tag length")

        # get the data
        value = 0
        for c in tag.tag_data:
            value = (value << 8) + c

        # return an instance of this thing
        return cls(value)
