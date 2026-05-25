"""Curated emoji set powering the icon picker on /categories.

Hand-picked to cover what people actually need for personal expense
categorisation — sectioned the way phone keyboards do it (Smileys,
People, Animals & Nature, Food & Drink, Activity, Travel & Places,
Objects, Symbols). Flags are intentionally omitted (rarely useful as a
category badge, and they bloat the picker by 250+).

Glyphs were chosen for stable cross-OS rendering — we stick to Unicode
≤ 13 and skip multi-codepoint ZWJ sequences (families, gendered
professions, skin tones) that render inconsistently on Windows.

Order within a section is rough thematic clustering, not Unicode order,
so the user finds related glyphs without scrolling far.

Each emoji also carries a search string built from the Unicode CLDR name
plus a small set of curated synonyms — that's how the search box on
/categories matches "car" → 🚗 even though the official name is
"AUTOMOBILE".
"""
from __future__ import annotations

import unicodedata
from typing import List, Tuple


# Each section is (display_name, slug, [emojis...])
# Slug is used as the anchor id and tab key.
EMOJI_SECTIONS: List[Tuple[str, str, List[str]]] = [
    ("Smileys", "smileys", [
        "😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "🙂",
        "🙃", "😉", "😌", "😍", "🥰", "😘", "😗", "😙", "😚", "😋",
        "😛", "😝", "😜", "🤪", "🤨", "🧐", "🤓", "😎", "🥳", "🤩",
        "😏", "😒", "😞", "😔", "😟", "😕", "🙁", "☹️", "😣", "😖",
        "😫", "😩", "🥺", "😢", "😭", "😤", "😠", "😡", "🤬", "🤯",
        "😳", "🥵", "🥶", "😱", "😨", "😰", "😥", "😓", "🤗", "🤔",
        "🤭", "🤫", "🤥", "😶", "😐", "😑", "😬", "🙄", "😯", "😦",
        "😧", "😮", "😲", "🥱", "😴", "🤤", "😪", "😵", "🤐", "🥴",
        "🤢", "🤮", "🤧", "😷", "🤒", "🤕", "🤑", "🤠", "😈", "👿",
        "👹", "👺", "🤡", "💩", "👻", "💀", "☠️", "👽", "👾", "🤖",
    ]),

    ("People", "people", [
        "👶", "👦", "👧", "🧒", "👨", "👩", "🧑", "👴", "👵", "🧓",
        "👮", "👷", "💂", "🕵️", "👨‍⚕️", "👩‍⚕️", "👨‍🍳", "👩‍🍳",
        "👨‍🏫", "👩‍🏫", "👨‍💻", "👩‍💻", "👨‍💼", "👩‍💼", "👨‍🔧", "👩‍🔧",
        "👨‍🚒", "👩‍🚒", "👨‍✈️", "👩‍✈️",
        "🤴", "👸", "🤵", "👰", "🤰", "🤱",
        "🙇", "💁", "🙅", "🙆", "🙋", "🤦", "🤷", "🙎", "🙍",
        "💇", "💆", "🧖", "💅", "🤳",
        "💃", "🕺", "👯", "🧗", "🚶", "🏃",
        "🤝", "👍", "👎", "👌", "✌️", "🤞", "🤟", "🤘", "🤙",
        "👈", "👉", "👆", "👇", "☝️", "👋", "🤚", "🖐️", "🖖",
        "👏", "🙌", "👐", "🤲", "🙏", "✍️",
        "💪", "🦵", "🦶", "👂", "👃", "🧠", "🦷", "🦴",
        "👀", "👁️", "👅", "👄", "💋",
    ]),

    ("Animals & Nature", "animals", [
        "🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐨", "🐯",
        "🦁", "🐮", "🐷", "🐽", "🐸", "🐵", "🐒", "🐔", "🐧", "🐦",
        "🐤", "🐣", "🐥", "🦆", "🦅", "🦉", "🦇", "🐺", "🐗", "🐴",
        "🦄", "🐝", "🐛", "🦋", "🐌", "🐞", "🐜", "🦗", "🕷️", "🕸️",
        "🦂", "🐢", "🐍", "🦎", "🐙", "🦑", "🦐", "🦞", "🦀", "🐡",
        "🐠", "🐟", "🐬", "🐳", "🐋", "🦈", "🐊", "🐅", "🐆", "🦓",
        "🦍", "🦧", "🐘", "🦛", "🦏", "🐪", "🐫", "🦒", "🦘", "🐃",
        "🐂", "🐄", "🐎", "🐖", "🐏", "🐑", "🦙", "🐐", "🦌", "🐕",
        "🐩", "🐈", "🐓", "🦃", "🦚", "🦜", "🐇", "🦝", "🐁", "🐀",
        "🐿️", "🦔", "🐾", "🐉", "🐲",
        "🌵", "🎄", "🌲", "🌳", "🌴", "🌱", "🌿", "☘️", "🍀", "🎋",
        "🍃", "🍂", "🍁", "🍄", "🌾", "💐", "🌷", "🌹", "🥀", "🌺",
        "🌸", "🌼", "🌻", "🌞", "🌝", "🌛", "🌜", "🌚", "🌕", "🌙",
        "🌎", "🌍", "🌏", "💫", "⭐", "🌟", "✨", "⚡", "🔥", "🌈",
        "☀️", "⛅", "☁️", "🌧️", "⛈️", "🌨️", "❄️", "☃️", "⛄",
        "💨", "💧", "💦", "☔", "🌊",
    ]),

    ("Food & Drink", "food", [
        "🍏", "🍎", "🍐", "🍊", "🍋", "🍌", "🍉", "🍇", "🍓", "🍈",
        "🍒", "🍑", "🥭", "🍍", "🥥", "🥝", "🍅", "🍆", "🥑", "🥦",
        "🥬", "🥒", "🌶️", "🫑", "🌽", "🥕", "🧄", "🧅", "🥔", "🍠",
        "🥐", "🥯", "🍞", "🥖", "🥨", "🧀", "🥚", "🍳", "🧈", "🥞",
        "🧇", "🥓", "🥩", "🍗", "🍖", "🦴", "🌭", "🍔", "🍟", "🍕",
        "🫓", "🥪", "🥙", "🧆", "🌮", "🌯", "🥗", "🥘", "🥫", "🍝",
        "🍜", "🍲", "🍛", "🍣", "🍱", "🥟", "🦪", "🍤", "🍙", "🍚",
        "🍘", "🍥", "🥠", "🥮", "🍢", "🍡", "🍧", "🍨", "🍦", "🥧",
        "🧁", "🍰", "🎂", "🍮", "🍭", "🍬", "🍫", "🍿", "🍩", "🍪",
        "🌰", "🥜", "🍯", "🥛", "🍼", "☕", "🍵", "🧃", "🥤", "🍶",
        "🍺", "🍻", "🥂", "🍷", "🥃", "🍸", "🍹", "🍾", "🥄", "🍴",
        "🍽️", "🥣", "🥡", "🥢", "🧂",
    ]),

    ("Activity", "activity", [
        "⚽", "🏀", "🏈", "⚾", "🥎", "🎾", "🏐", "🏉", "🥏", "🎱",
        "🏓", "🏸", "🏒", "🏑", "🥍", "🏏", "🥅", "⛳", "🏹", "🎣",
        "🥊", "🥋", "🎽", "🛹", "🛼", "🛷", "⛸️", "🎿", "⛷️", "🏂",
        "🪂", "🏋️", "🤼", "🤸", "⛹️", "🤺", "🤾", "🏌️", "🏇", "🧘",
        "🏄", "🏊", "🤽", "🚣", "🚴", "🚵", "🏆", "🥇", "🥈", "🥉",
        "🏅", "🎖️", "🏵️", "🎗️", "🎫", "🎟️", "🎪", "🎭", "🩰", "🎨",
        "🎬", "🎤", "🎧", "🎼", "🎹", "🥁", "🎷", "🎺", "🎸", "🎻",
        "🎲", "♟️", "🎯", "🎳", "🎮", "🎰", "🧩", "🎉", "🎊", "🎈",
        "🎁", "🎀", "🎂", "🎃", "🎄", "🎆", "🎇", "🧨", "🪔", "🎏",
        "🎐", "🧧", "🏮", "🎎",
    ]),

    ("Travel & Places", "travel", [
        "🚗", "🚕", "🚙", "🚌", "🚎", "🏎️", "🚓", "🚑", "🚒", "🚐",
        "🚚", "🚛", "🚜", "🛴", "🚲", "🛵", "🏍️", "🛺", "🚨", "🚔",
        "🚍", "🚘", "🚖", "🚡", "🚠", "🚟", "🚃", "🚋", "🚞", "🚝",
        "🚄", "🚅", "🚈", "🚂", "🚆", "🚇", "🚊", "🚉", "✈️", "🛫",
        "🛬", "🛩️", "💺", "🛰️", "🚀", "🛸", "🚁", "🛶", "⛵", "🚤",
        "🛥️", "🛳️", "⛴️", "🚢", "⚓", "⛽", "🚧", "🚦", "🚥", "🚏",
        "🗺️", "🗿", "🗽", "🗼", "🏰", "🏯", "🏟️", "🎡", "🎢", "🎠",
        "⛲", "⛱️", "🏖️", "🏝️", "🏜️", "🌋", "⛰️", "🏔️", "🗻", "🏕️",
        "⛺", "🛖", "🏠", "🏡", "🏘️", "🏚️", "🏗️", "🏭", "🏢", "🏬",
        "🏣", "🏤", "🏥", "🏦", "🏨", "🏪", "🏫", "🏩", "💒", "🏛️",
        "⛪", "🕌", "🕍", "🛕", "🕋", "⛩️", "🛤️", "🛣️", "🌅", "🌄",
        "🌠", "🌇", "🌆", "🏙️", "🌃", "🌌", "🌉", "🌁",
    ]),

    ("Objects", "objects", [
        "⌚", "📱", "📲", "💻", "⌨️", "🖥️", "🖨️", "🖱️", "🕹️", "💽",
        "💾", "💿", "📀", "📼", "📷", "📸", "📹", "🎥", "📽️", "🎞️",
        "📞", "☎️", "📟", "📠", "📺", "📻", "🎙️", "🎚️", "🎛️", "🧭",
        "⏱️", "⏲️", "⏰", "🕰️", "⌛", "⏳", "📡", "🔋", "🔌", "💡",
        "🔦", "🕯️", "🧯", "🛢️", "💸", "💵", "💴", "💶", "💷", "💰",
        "💳", "💎", "⚖️", "🧰", "🔧", "🔨", "⚒️", "🛠️", "⛏️", "🔩",
        "⚙️", "🧱", "⛓️", "🧲", "🔫", "💣", "🧨", "🪓", "🔪", "🗡️",
        "⚔️", "🛡️", "🚬", "⚰️", "⚱️", "🏺", "🔮", "📿", "🧿", "💈",
        "⚗️", "🔭", "🔬", "🕳️", "🩹", "🩺", "💊", "💉", "🧬", "🦠",
        "🧫", "🧪", "🌡️", "🧹", "🧺", "🧻", "🚽", "🚰", "🚿", "🛁",
        "🧼", "🧴", "🛎️", "🔑", "🗝️", "🚪", "🛋️", "🛏️", "🧸", "🖼️",
        "🛍️", "🛒", "🎁", "✉️", "📩", "📨", "📧", "💌", "📥", "📤",
        "📦", "🏷️", "📪", "📫", "📬", "📭", "📮", "📜", "📃", "📄",
        "📑", "🧾", "📊", "📈", "📉", "🗒️", "🗓️", "📆", "📅", "🗑️",
        "📇", "🗃️", "🗳️", "🗄️", "📋", "📁", "📂", "🗂️", "🗞️", "📰",
        "📓", "📔", "📒", "📕", "📗", "📘", "📙", "📚", "📖", "🔖",
        "🧷", "🔗", "📎", "📐", "📏", "🧮", "📌", "📍", "✂️", "🖊️",
        "🖋️", "✒️", "🖌️", "🖍️", "📝", "✏️", "🔍", "🔎", "🔏", "🔐",
        "🔒", "🔓",
    ]),

    ("Symbols", "symbols", [
        "❤️", "🧡", "💛", "💚", "💙", "💜", "🤎", "🖤", "🤍", "💔",
        "❣️", "💕", "💞", "💓", "💗", "💖", "💘", "💝", "💟",
        "☮️", "✝️", "☪️", "🕉️", "☸️", "✡️", "🔯", "🕎", "☯️", "☦️",
        "🛐", "⛎",
        "♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓",
        "🆔", "⚛️", "🉑", "☢️", "☣️", "📴", "📳",
        "❌", "⭕", "🛑", "⛔", "📛", "🚫", "💯", "💢", "♨️", "🚷",
        "🚯", "🚳", "🚱", "🔞", "📵", "🚭", "❗", "❕", "❓", "❔",
        "‼️", "⁉️", "⚠️", "🚸", "🔱", "⚜️", "🔰", "♻️", "✅", "🈯",
        "💹", "❇️", "✳️", "❎", "🌐", "💠", "🌀", "💤", "🏧", "🚾",
        "♿", "🅿️", "🛂", "🛃", "🛄", "🛅", "🚹", "🚺", "🚻", "🚮",
        "🎦", "📶", "ℹ️", "🔣", "🆖", "🆗", "🆙", "🆒", "🆕", "🆓",
        "▶️", "⏸️", "⏹️", "⏺️", "⏭️", "⏮️", "⏩", "⏪", "◀️", "🔼",
        "🔽", "➡️", "⬅️", "⬆️", "⬇️", "↗️", "↘️", "↙️", "↖️", "↕️",
        "↔️", "↪️", "↩️", "⤴️", "⤵️", "🔀", "🔁", "🔂", "🔄", "🔃",
        "🎵", "🎶", "➕", "➖", "➗", "✖️", "♾️", "💲", "💱", "©️",
        "®️", "™️",
    ]),
]


def total_count() -> int:
    """Total emojis exposed by the picker."""
    return sum(len(items) for _, _, items in EMOJI_SECTIONS)


# Common search aliases for emojis whose Unicode name is too obscure for
# typed search ("car" doesn't match "AUTOMOBILE"). Only add an entry if
# the official name fails an obvious-search test. Keep terms space-
# separated and lowercase.
_CUSTOM_KEYWORDS: dict[str, str] = {
    # Food & drink
    "🛒": "cart shopping trolley grocery",
    "🥖": "bread baguette",
    "🥐": "croissant pastry",
    "🥨": "pretzel",
    "🥯": "bagel",
    "🍞": "bread loaf",
    "🥞": "pancakes breakfast",
    "🧇": "waffle breakfast",
    "🧀": "cheese",
    "🥩": "steak meat beef",
    "🥓": "bacon",
    "🍳": "egg breakfast fried",
    "🥚": "egg",
    "🧈": "butter",
    "🌭": "hot dog hotdog",
    "🍔": "burger hamburger",
    "🍟": "fries chips",
    "🍕": "pizza",
    "🥪": "sandwich",
    "🥙": "kebab wrap",
    "🌮": "taco mexican",
    "🌯": "burrito wrap",
    "🥗": "salad",
    "🥘": "curry pan dal",
    "🍝": "pasta spaghetti noodles",
    "🍜": "ramen noodles soup",
    "🍲": "stew pot soup",
    "🍛": "curry rice thali biryani indian",
    "🍣": "sushi",
    "🍱": "bento japanese lunch",
    "🥟": "dumpling samosa momos",
    "🍤": "shrimp prawn",
    "🍙": "rice ball onigiri",
    "🍚": "rice",
    "🍦": "ice cream cone soft serve",
    "🍨": "ice cream",
    "🍧": "shaved ice golakhi gola",
    "🧁": "cupcake muffin",
    "🍰": "cake slice",
    "🎂": "cake birthday",
    "🍭": "lollipop candy",
    "🍬": "candy sweet",
    "🍫": "chocolate bar",
    "🍿": "popcorn munch movie snack",
    "🍩": "donut doughnut",
    "🍪": "cookie biscuit",
    "🥜": "peanuts nuts",
    "🍯": "honey jar",
    "🥛": "milk dairy lassi glass",
    "🍼": "baby bottle milk",
    "☕": "coffee cafe espresso tea hot",
    "🍵": "tea green matcha cup",
    "🧃": "juice box drink",
    "🥤": "soda cup drink soft",
    "🧋": "bubble tea boba",
    "🍶": "sake bottle",
    "🍺": "beer mug",
    "🍻": "beer cheers clinking",
    "🥂": "champagne clinking lavish celebrate party glasses",
    "🍷": "wine glass",
    "🥃": "whiskey tumbler",
    "🍸": "cocktail martini",
    "🍹": "cocktail tropical drink beverage",
    "🍾": "champagne bottle pop celebrate",
    "🫓": "flatbread paratha kulcha naan roti",

    # Travel
    "🚗": "car automobile drive",
    "🚕": "taxi cab",
    "🚙": "suv jeep car",
    "🚌": "bus",
    "🏎️": "race car formula",
    "🚓": "police car cop",
    "🚑": "ambulance medical",
    "🚒": "fire truck",
    "🚚": "truck delivery lorry",
    "🚛": "lorry semi truck",
    "🛴": "scooter kick",
    "🚲": "bicycle bike cycle",
    "🛵": "scooter motor moped",
    "🏍️": "motorcycle motorbike bike",
    "🛺": "rickshaw auto tuktuk",
    "🚖": "taxi cab uber ola",
    "🚇": "metro subway underground",
    "🚆": "train",
    "🚄": "bullet train high speed",
    "✈️": "airplane plane flight travel",
    "🛫": "takeoff flight",
    "🛬": "landing flight",
    "🚀": "rocket launch",
    "⚓": "anchor",
    "⛽": "fuel gas petrol diesel pump",
    "🅿️": "parking",
    "🛣️": "highway road toll",
    "🚦": "traffic light",
    "🏨": "hotel building accommodation",
    "🏡": "home house",
    "🏠": "home house rent",
    "🏖️": "beach holiday vacation",
    "🏝️": "island holiday tropical",
    "⛺": "tent camping",
    "🗻": "mountain fuji",
    "🏔️": "mountain snow",

    # Objects / bills / shopping
    "📱": "phone mobile cell smartphone",
    "💻": "laptop computer pc",
    "🖥️": "desktop computer monitor",
    "⌨️": "keyboard",
    "🖨️": "printer",
    "🖱️": "mouse",
    "🎧": "headphones audio music",
    "📷": "camera photo",
    "📺": "tv television netflix hotstar",
    "📻": "radio music",
    "💡": "light bulb electricity power idea",
    "🔌": "plug socket electric",
    "🔋": "battery",
    "🔦": "torch flashlight",
    "🚿": "shower water",
    "🛁": "bathtub bath",
    "🚽": "toilet",
    "🧼": "soap",
    "🧴": "lotion shampoo care",
    "🛏️": "bed sleep",
    "🛋️": "sofa couch furniture",
    "🚪": "door",
    "🔑": "key lock",
    "🔒": "lock secure",
    "🔧": "wrench tool repair maintenance",
    "🔨": "hammer tool",
    "🛠️": "tools repair",
    "🧹": "broom cleaning",
    "🧺": "laundry basket",
    "🧻": "toilet paper roll",
    "💊": "pill medicine pharmacy tablet",
    "💉": "syringe injection vaccine",
    "🩺": "stethoscope doctor",
    "🏥": "hospital medical",
    "🦷": "tooth dentist dental",
    "🛡️": "shield insurance protect",
    "💰": "money bag rich rupees",
    "💵": "dollar cash bill note",
    "💴": "yen cash",
    "💶": "euro cash",
    "💷": "pound cash",
    "💳": "credit card debit payment",
    "🪙": "coin money",
    "💸": "money fly cash spent",
    "📈": "chart growth invest stock up",
    "📉": "chart decline loss",
    "📊": "chart bar analytics",
    "🐷": "savings piggy bank pig",
    "🛍️": "shopping bag retail",
    "🎁": "gift present birthday",
    "🎀": "ribbon bow gift",
    "🎈": "balloon party",
    "🎉": "party celebrate",
    "🎊": "confetti party",
    "🪔": "diya lamp diwali festival",
    "🪅": "pinata",
    "💼": "briefcase business work salary office",
    "👔": "necktie shirt formal office",
    "👕": "shirt t-shirt clothes",
    "👖": "jeans pants trousers",
    "👗": "dress",
    "👟": "shoes sneakers",
    "👞": "shoe formal",
    "👠": "heel formal",
    "👜": "handbag bag purse",
    "👛": "purse pocket billo wallet",
    "💄": "lipstick makeup",
    "💍": "ring jewellery",
    "💎": "diamond gem luxury",
    "🧸": "teddy toy kid",
    "📚": "books study education tuition",
    "🏫": "school education",
    "🎓": "graduation degree education",
    "📷": "camera photo",
    "🎬": "movie cinema clapper netflix",
    "🎮": "game gaming console",
    "🎵": "music note",
    "🎼": "music",
    "🏷️": "tag label",

    # Animals (common pet/family terms)
    "🐶": "dog puppy pet billo",
    "🐱": "cat kitty pet",
    "🐴": "horse",
    "🐮": "cow",
    "🐷": "pig",
    "🐔": "chicken",
    "🐝": "bee honey",
    "🦋": "butterfly",
    "🐢": "turtle",
    "🐠": "fish",

    # Activity
    "🏋️": "gym workout weights",
    "🧘": "yoga meditate",
    "🏃": "run running jog",
    "🚶": "walking walk ghoomna outing",
    "🚴": "cycling biking",
    "⚽": "football soccer",
    "🏀": "basketball",
    "🏏": "cricket bat",
    "🎾": "tennis",

    # Symbols often used for finances
    "💲": "dollar money currency",
    "💱": "exchange currency forex",
    "🔁": "repeat subscription recurring",
    "🔄": "refresh cycle",
    "♻️": "recycle reuse",
    "✅": "tick check done ok",
    "❌": "cross wrong cancel",
    "⚠️": "warning caution alert",
    "💯": "100 hundred",

    # People (common occupation/role searches)
    "👨‍⚕️": "doctor medical",
    "👨‍🍳": "chef cook",
    "👨‍💻": "developer programmer it computer",
    "👨‍💼": "office worker business",
    "👨‍🏫": "teacher tutor",
    "👨‍🔧": "mechanic technician repair",
    "👨‍🚒": "firefighter fire",
    "👨‍✈️": "pilot",
    "👶": "baby kid child",
    "🤰": "pregnant",
}


def _base_name(emoji: str) -> str:
    """Best-effort Unicode CLDR name for an emoji. Walks codepoints until
    one yields a name (handles variation selectors / ZWJ joiners), and
    lowercases the result for case-insensitive matching."""
    for ch in emoji:
        try:
            return unicodedata.name(ch).lower()
        except ValueError:
            continue
    return ""


def search_text(emoji: str) -> str:
    """Lowercase space-separated terms that match this emoji in search.

    Combines the official Unicode name (so "pizza" → 🍕 "for free") with
    any curated synonyms in _CUSTOM_KEYWORDS (so "car" → 🚗 even though
    Unicode calls it "AUTOMOBILE", or "biryani" → 🍛).
    """
    base = _base_name(emoji)
    extra = _CUSTOM_KEYWORDS.get(emoji, "")
    return f"{base} {extra}".strip()


def sections_with_search() -> List[Tuple[str, str, List[Tuple[str, str]]]]:
    """Sections enriched so each emoji is paired with its search string.

    Returned shape: ``[(display_name, slug, [(emoji, search_text), ...]), ...]``.
    Used by the template to set the ``data-search`` attribute on each
    button, which the picker JS filters against.
    """
    out: List[Tuple[str, str, List[Tuple[str, str]]]] = []
    for name, slug, items in EMOJI_SECTIONS:
        out.append((name, slug, [(em, search_text(em)) for em in items]))
    return out
