# HSMT/Code/processors/vlxd.py

VLXD_KEYWORDS = [
    # vật liệu nền
    "xi măng",
    "cement",
    "cát",
    "đá",
    "gravel",
    "sand",
    "bê tông",
    "concrete",

    # vật liệu xây
    "gạch",
    "brick",
    "block",

    # thép xây dựng
    "thép xây dựng",
    "rebar",
    "thép cuộn",
    "thép cây",

    # vật liệu hoàn thiện
    "sơn xây dựng",
    "vữa",
    "vữa xây",
    "vật liệu xây dựng"
]


def is_vlxd(text: str) -> bool:
    """
    Kiểm tra có phải vật liệu xây dựng hay không
    """
    if not text:
        return False

    text = text.lower()

    for k in VLXD_KEYWORDS:
        if k in text:
            return True

    return False
