# Railway deployment v2
from __future__ import annotations

import base64
import copy
import hashlib
import html
import io
import json
import os
import random
import re
import sqlite3
import textwrap
import threading
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    import anthropic  # type: ignore

    HAS_ANTHROPIC = True
except Exception:
    anthropic = None
    HAS_ANTHROPIC = False

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps  # type: ignore

    HAS_PIL = True
except Exception:
    Image = ImageDraw = ImageFont = ImageOps = None
    HAS_PIL = False


DEFAULT_MODELSCOPE_API_KEY = "ms-e7357050-c02d-4fa1-b262-5918f07d6461"

ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / "backend_state.json"
COMMUNITY_DB = ROOT / "community.db"
GENERATED_DIR = ROOT / "generated_memes"
MEME_PROMPT_FILE = ROOT / "梗图生成prompt.txt"
HOST = os.environ.get("MEMELAB_HOST", os.environ.get("HOST", "0.0.0.0"))
PORT = int(os.environ.get("PORT", os.environ.get("MEMELAB_PORT", "8080")))

STATE_LOCK = threading.Lock()

MODELSCOPE_BASE_URL = os.environ.get("MODELSCOPE_BASE_URL", "https://api-inference.modelscope.cn").strip()
MODELSCOPE_MODEL_ID = os.environ.get("MODELSCOPE_MODEL_ID", "moonshotai/Kimi-K2.5").strip()
MODELSCOPE_IMAGE_MODEL_ID = os.environ.get("MODELSCOPE_IMAGE_MODEL_ID", "Qwen/Qwen-Image-2512").strip()
MODELSCOPE_API_KEY = os.environ.get("MODELSCOPE_API_KEY", DEFAULT_MODELSCOPE_API_KEY).strip()
MEMELAB_LLM = os.environ.get("MEMELAB_LLM", "modelscope").strip().lower()
MODELSCOPE_IMAGE_POLL_SECONDS = float(os.environ.get("MODELSCOPE_IMAGE_POLL_SECONDS", "3"))
MODELSCOPE_IMAGE_MAX_POLLS = int(os.environ.get("MODELSCOPE_IMAGE_MAX_POLLS", "30"))
COMMUNITY_SYNC_MINUTES = int(os.environ.get("COMMUNITY_SYNC_MINUTES", "45"))
MEME_API_URL = os.environ.get("MEME_API_URL", "https://meme-api.com/gimme/60").strip()
LEMMY_API_URL = os.environ.get(
    "LEMMY_API_URL",
    "https://lemmy.world/api/v3/post/list?type_=Local&sort=Hot&page=1&limit=40",
).strip()
MEME_API_URLS = [MEME_API_URL]
LEMMY_API_URLS = [
    "https://lemmy.world/api/v3/post/list?type_=Local&sort=Hot&page=1&limit=30",
    "https://lemmy.world/api/v3/post/list?type_=Local&sort=Hot&page=2&limit=30",
    "https://lemmy.world/api/v3/post/list?type_=Local&sort=Hot&page=3&limit=30",
]


SEED_POSTS = [
    {
        "id": "p1",
        "author": "班味十足",
        "avatar": "😮‍💨",
        "level": "🥇 黄金梗师",
        "tag": "🔥 今日热梗",
        "caption": '老板周五六点在群里说"辛苦大家"的时候，我',
        "memeLabel": "狗头保命.jpg\n[表情包：柴犬歪头]",
        "bg": "#FDE6D9",
        "accent": "red",
        "stats": {"laugh": 234, "comments": 18, "shares": 41},
        "template": "狗头保命",
        "createdAt": "2026-04-18T11:48:00",
    },
    {
        "id": "p2",
        "author": "那咋了本了",
        "avatar": "🫠",
        "level": "💠 钻石梗王",
        "tag": "🔥 今日热梗",
        "caption": "妈：你看看人家孩子\n我：那咋了",
        "memeLabel": "那咋了.jpg\n[东北老大爷表情]",
        "bg": "#E8F4FD",
        "accent": "blue",
        "stats": {"laugh": 1820, "comments": 103, "shares": 289},
        "template": "那咋了",
        "createdAt": "2026-04-18T11:00:00",
    },
    {
        "id": "p3",
        "author": "city不city",
        "avatar": "🧳",
        "level": "🥇 黄金梗师",
        "tag": "🔥 今日热梗",
        "caption": "上海？city不city啊？\n————友情提醒：浦东很city，地铁13号线不太city",
        "memeLabel": "[金发外国美女 戴墨镜 比耶]",
        "bg": "#E5F7EC",
        "accent": "green",
        "stats": {"laugh": 892, "comments": 56, "shares": 134},
        "template": "city不city",
        "createdAt": "2026-04-18T09:00:00",
    },
    {
        "id": "p4",
        "author": "孤勇者本者",
        "avatar": "⚔️",
        "level": "💎 铂金梗将",
        "tag": "💀 考古老梗",
        "caption": "谁说站在光里的才算英雄\n————周一早八赶地铁的打工人",
        "memeLabel": "[黑白剪影 打工人背影]",
        "bg": "#EEE9F8",
        "accent": "purple",
        "stats": {"laugh": 567, "comments": 28, "shares": 88},
        "template": "孤勇者",
        "createdAt": "2026-04-18T07:00:00",
    },
    {
        "id": "p5",
        "author": "职场MBTI",
        "avatar": "📋",
        "level": "🥈 白银梗手",
        "tag": "🌱 冷门好梗",
        "caption": "领导：这个你先做着\n我（I人）：好的 🙂\n我（内心）：这啥玩意儿",
        "memeLabel": "[I人表面平静内心咆哮]",
        "bg": "#FCF0E0",
        "accent": "amber",
        "stats": {"laugh": 421, "comments": 35, "shares": 52},
        "template": "表里不一",
        "createdAt": "2026-04-18T06:00:00",
    },
    {
        "id": "p6",
        "author": "早八怨种",
        "avatar": "🥲",
        "level": "🥇 黄金梗师",
        "tag": "🔥 今日热梗",
        "caption": "闹钟响的那一刻\n我的灵魂：已离开躯壳",
        "memeLabel": "[悲伤蛙 Pepe 躺平]",
        "bg": "#E5F7EC",
        "accent": "green",
        "stats": {"laugh": 733, "comments": 49, "shares": 95},
        "template": "悲伤蛙",
        "createdAt": "2026-04-18T04:00:00",
    },
    {
        "id": "p7",
        "author": "发疯文学家",
        "avatar": "🤪",
        "level": "💠 钻石梗王",
        "tag": "🔥 今日热梗",
        "caption": "啊啊啊啊啊我不想上班啊啊啊谁懂啊家人们",
        "memeLabel": "[猫猫崩溃 爪子抱头]",
        "bg": "#FDE6D9",
        "accent": "red",
        "stats": {"laugh": 2340, "comments": 187, "shares": 412},
        "template": "发疯文学",
        "createdAt": "2026-04-18T02:00:00",
    },
    {
        "id": "p8",
        "author": "特种兵旅游",
        "avatar": "🎒",
        "level": "🥇 黄金梗师",
        "tag": "🌱 冷门好梗",
        "caption": "48小时6个城市12个景点\n回来请了3天病假",
        "memeLabel": "[地图 + 红色路线 + 大哭]",
        "bg": "#E8F4FD",
        "accent": "blue",
        "stats": {"laugh": 389, "comments": 22, "shares": 41},
        "template": "特种兵",
        "createdAt": "2026-04-17T23:00:00",
    },
    {
        "id": "p9",
        "author": "吗喽打工",
        "avatar": "🐒",
        "level": "🥈 白银梗手",
        "tag": "🔥 今日热梗",
        "caption": "一只吗喽站在工位上\n它没有明天，只有KPI",
        "memeLabel": "[猴子戴领带 电脑前]",
        "bg": "#FCF0E0",
        "accent": "amber",
        "stats": {"laugh": 612, "comments": 44, "shares": 73},
        "template": "吗喽",
        "createdAt": "2026-04-17T21:00:00",
    },
    {
        "id": "p10",
        "author": "哈基米",
        "avatar": "🍯",
        "level": "🥇 黄金梗师",
        "tag": "🔥 今日热梗",
        "caption": "哈基米～哈基米～\n南北绿豆～豆豆冰",
        "memeLabel": "[可爱水豚 戴花]",
        "bg": "#EEE9F8",
        "accent": "purple",
        "stats": {"laugh": 1045, "comments": 78, "shares": 201},
        "template": "哈基米",
        "createdAt": "2026-04-17T18:00:00",
    },
    {
        "id": "p11",
        "author": "class is class",
        "avatar": "🎓",
        "level": "🥈 白银梗手",
        "tag": "💀 考古老梗",
        "caption": "Why？\n别问 问就是 class is class",
        "memeLabel": "[学生崩溃 撕书]",
        "bg": "#FDE6D9",
        "accent": "red",
        "stats": {"laugh": 287, "comments": 15, "shares": 34},
        "template": "class is class",
        "createdAt": "2026-04-17T12:00:00",
    },
    {
        "id": "p12",
        "author": "主理人",
        "avatar": "☕",
        "level": "💎 铂金梗将",
        "tag": "🌱 冷门好梗",
        "caption": "我不是老板，我是主理人\n（店里就我一个人）",
        "memeLabel": "[咖啡师独自站柜台]",
        "bg": "#E5F7EC",
        "accent": "green",
        "stats": {"laugh": 498, "comments": 37, "shares": 61},
        "template": "主理人",
        "createdAt": "2026-04-17T10:00:00",
    },
]


SEED_COMMENTS = {
    "p1": [
        {"id": "c1", "author": "梗王本王", "avatar": "🐶", "text": "这班上得跟考公似的 🫠", "votes": 156, "topPick": True},
        {"id": "c2", "author": "班味浓郁", "avatar": "😮‍💨", "text": "那咋了.jpg", "votes": 89},
        {"id": "c3", "author": "发疯专业户", "avatar": "🤪", "text": "啊啊啊啊啊周五快来啊啊啊", "votes": 54},
    ]
}


PERSONAS = {
    "default": {
        "key": "default",
        "name": "梗王",
        "subtitle": "不会造梗？我教你啊",
        "greeting": "我是梗王，问就是 class is class，来整活儿啊",
        "style": "互联网热梗、emoji混搭、年轻人口吻",
        "samples": [
            {"user": "今天好累", "bot": "那咋了 🫠 累了就累了，打工人的尊严不就是一瓶肥宅快乐水吗"},
            {"user": "加班到十点", "bot": "班味浓到能腌菜了家人们 🥬 建议：下班回家先对着天花板骂三分钟再睡"},
        ],
    },
    "dialect": {
        "key": "dialect",
        "name": "梗王·东北版",
        "subtitle": "整点儿活儿呗 老铁",
        "greeting": "唠嗑啊兄弟！今儿咋地，给整点儿啥梗？",
        "style": "东北方言、老铁、嘎嘎、咋地、整活儿",
        "samples": [
            {"user": "今天好累", "bot": "嘎嘎累是吧？那咋地 老铁这班上的跟三班倒似的 整一口儿吧！"},
            {"user": "加班到十点", "bot": "哎妈呀 这班上得跟大棚种菜似的 走 老铁 撸串去！"},
        ],
    },
    "classical": {
        "key": "classical",
        "name": "梗王·文言版",
        "subtitle": "诸君 且听朕道梗一则",
        "greeting": "吾乃梗王。尔有何惑？朕以古法解之。",
        "style": "文言文 + 现代梗，子曰体，之乎者也",
        "samples": [
            {"user": "今天好累", "bot": '劳则怨，怨则躺，躺则愈累。此乃"班味"之循环，古已有之，无解也 🍃'},
            {"user": "加班到十点", "bot": "子曰：朝九晚十，非人哉！卿可效法陶令，不为五斗米折腰，然五斗米实在香 💰"},
        ],
    },
}


GEN_TEMPLATES = [
    {"name": "狗头保命", "emoji": "🐶", "accent": "amber"},
    {"name": "那咋了", "emoji": "🫠", "accent": "blue"},
    {"name": "悲伤蛙", "emoji": "🐸", "accent": "green"},
    {"name": "震惊脸", "emoji": "😱", "accent": "red"},
    {"name": "哈基米", "emoji": "🍯", "accent": "amber"},
    {"name": "吗喽", "emoji": "🐒", "accent": "purple"},
]


GEN_STYLES = [
    {"key": "cold", "label": "冷漠系"},
    {"key": "crazy", "label": "癫狂系"},
    {"key": "yy", "label": "阴阳系"},
    {"key": "cute", "label": "可爱系"},
]
TEMPLATE_PROMPT_HINTS = {
    "狗头保命": "Chinese reaction meme, grounded office realism, deadpan humor, cautious self-protection vibe, expressive dog-like guilty reaction",
    "那咋了": "bold confrontational meme, close-up reaction face, dismissive body language, unapologetic irony, strong internet slang energy",
    "悲伤蛙": "melancholic pepe-inspired mood, lonely room, subtle despair, tired worker vibe, muted green palette",
    "震惊脸": "dramatic overreaction meme, wide eyes, absurd reveal moment, exaggerated tension, punchy social-media readability",
    "哈基米": "cute wholesome meme, soft lighting, adorable animal protagonist, sweet and slightly silly, warm pastel color palette",
    "吗喽": "chaotic worker-monkey meme, office satire, stressed but funny body motion, absurd workplace energy, purple-tinted humor",
}
STYLE_VISUAL_HINTS = {
    "cold": "deadpan meme realism, restrained emotion, dry sarcastic framing, moody cinematic light",
    "crazy": "wild absurd humor, dynamic composition, exaggerated emotion, chaotic internet meme energy",
    "yy": "sarcastic and ironic framing, polished meme storytelling, sharp contrast and subtle mockery",
    "cute": "soft adorable meme aesthetic, clean pastel palette, plush-like animals and friendly rounded shapes",
}
GEN_IMAGE_VARIANTS = [
    "close-up reaction shot, clean subject in center, strong facial expression",
    "mid-shot with clear body language, meme-ready composition, visual punchline feeling",
    "environmental scene with stronger context, cinematic framing, readable background story",
]


GAME_LEVELS = [
    {
        "id": "fill-1",
        "mode": "fill",
        "title": "填梗大师",
        "setup": "星期一早上8点，地铁挤得像罐头",
        "imagePrompt": "[悲伤蛙 被挤成饼]",
        "placeholder": "你的梗文案…（15字内最佳）",
        "topAnswers": [
            {"text": "我不是在通勤，我是在被搬运", "score": "A", "votes": 892},
            {"text": "这不是上班，这是上供", "score": "A", "votes": 734},
        ],
    },
    {
        "id": "fill-2",
        "mode": "fill",
        "title": "填梗大师",
        "setup": "妈妈打电话问你找对象了吗",
        "imagePrompt": "[电话一响 浑身发抖]",
        "placeholder": "你的梗文案…（15字内最佳）",
        "topAnswers": [
            {"text": "妈 我在谈 跟KPI谈", "score": "A+", "votes": 1204},
            {"text": "我不是单身 我是高纯度", "score": "A", "votes": 889},
        ],
    },
    {
        "id": "caption-1",
        "mode": "caption",
        "title": "看图写梗",
        "setup": "看到一只精神状态离线的猫，像极了周一的你",
        "imagePrompt": "[飞机耳猫猫 眼神空洞]",
        "placeholder": "给这张图写一句 caption…",
        "topAnswers": [
            {"text": "我没疯，我只是周一开机失败", "score": "A", "votes": 618},
            {"text": "工位还没到，我魂先请假了", "score": "A", "votes": 574},
        ],
    },
    {
        "id": "chain-1",
        "mode": "chain",
        "title": "梗接龙",
        "setup": '上家出题：老板说"年轻人要以公司为家"',
        "imagePrompt": "[请你用一句更离谱的梗接下去]",
        "placeholder": "接上这句，越荒诞越好…",
        "topAnswers": [
            {"text": "那房贷也让公司一起背呗", "score": "A+", "votes": 701},
            {"text": "行，那年终奖记得叫生活费", "score": "A", "votes": 655},
        ],
    },
]


TAGS = ["🔥 今日热梗", "🌱 冷门好梗", "💀 考古老梗"]
ACCENT_COLORS = {
    "red": ("#FDE6D9", "#E5534B"),
    "blue": ("#E8F4FD", "#4A8FE7"),
    "green": ("#E5F7EC", "#52C17A"),
    "purple": ("#EEE9F8", "#7B5EA7"),
    "amber": ("#FCF0E0", "#F5A623"),
}
LEVELS = [
    (0, "🌱 青铜梗农"),
    (60, "🥈 白银梗手"),
    (150, "🥇 黄金梗师"),
    (300, "💎 铂金梗将"),
    (520, "💠 钻石梗王"),
    (888, "👑 传奇梗神"),
]

COMMUNITY_POST_TARGET = 108
LOCAL_IMAGE_PATTERNS = ("微信图片_*.jpg", "微信图片_*.jpeg", "微信图片_*.png", "微信图片_*.webp")
COMMUNITY_AUTHORS = [
    ("通勤摆烂学家", "🫠"),
    ("摸鱼观察员", "🐟"),
    ("电子请假条", "📄"),
    ("哈基米后援会", "🍯"),
    ("工位生存者", "💼"),
    ("发疯文学课代表", "🤪"),
    ("周一受害人", "🥲"),
    ("情绪稳定的吗喽", "🐒"),
    ("会议纪要本妖", "📝"),
    ("已读乱回办", "📲"),
]
COMMUNITY_COMMENTERS = [
    ("梗王本王", "🐶"),
    ("班味雷达", "📡"),
    ("下班倒计时", "⏰"),
    ("精神离职办", "💤"),
    ("冷笑话储备库", "🧊"),
]
AI_COMMENT_BOTS = [
    ("ai_bot_01", "AI班味监测员", "📡"),
    ("ai_bot_02", "AI哈基米路人", "🍯"),
    ("ai_bot_03", "AI工位嘴替", "🫠"),
    ("ai_bot_04", "AI电子吗喽", "🐒"),
    ("ai_bot_05", "AI下班计时器", "⏰"),
]
AUTO_AI_COMMENT_LIMIT = 3
COMMUNITY_VARIANTS = [
    {"template": "狗头保命", "accent": "amber", "open": "看到这张图，我只想说", "close": "别问，问就是工位显灵了"},
    {"template": "那咋了", "accent": "blue", "open": "同事把这图发群里那一刻", "close": "我当场进入那咋了防御模式"},
    {"template": "悲伤蛙", "accent": "green", "open": "这图最适合形容", "close": "人还在，魂已经申请居家"},
    {"template": "震惊脸", "accent": "red", "open": "老板说简单同步一下", "close": "结果同步成了渡劫大会"},
    {"template": "哈基米", "accent": "purple", "open": "周五下午看到这种场面", "close": "哈基米都想替我请假"},
    {"template": "吗喽", "accent": "amber", "open": "今天的电子吗喽状态", "close": "已经把情绪外包给冰美式了"},
]


def default_state() -> dict:
    return {
        "profile": {
            "userName": "梗员01",
            "avatar": "🐶",
            "points": 185,
            "personaKey": "default",
            "activityEvents": [],
            "chatTurns": 0,
        },
        "posts": copy.deepcopy(SEED_POSTS),
        "comments": copy.deepcopy(SEED_COMMENTS),
        "generated": {},
        "gameLevels": copy.deepcopy(GAME_LEVELS),
    }


def stable_int(seed: str) -> int:
    return int(hashlib.md5(seed.encode("utf-8")).hexdigest()[:8], 16)


def discover_local_images() -> list[Path]:
    found: list[Path] = []
    seen: set[Path] = set()
    for pattern in LOCAL_IMAGE_PATTERNS:
        for file_path in sorted(ROOT.glob(pattern)):
            if file_path.is_file() and file_path not in seen:
                seen.add(file_path)
                found.append(file_path)
    return found


def extract_image_serial(file_path: Path, index: int) -> str:
    match = re.search(r"_(\d+)_\d+$", file_path.stem)
    if match:
        return match.group(1)
    return f"{index + 1:02d}"


def build_seed_comments_for_post(post: dict) -> list[dict]:
    suggestions = build_comment_suggestions(post.get("caption", ""))
    comments = []
    seed_text = post["id"]
    for idx, text in enumerate(suggestions[:3]):
        author, avatar = COMMUNITY_COMMENTERS[idx % len(COMMUNITY_COMMENTERS)]
        comments.append(
            {
                "id": f"{post['id']}-c{idx + 1}",
                "author": author,
                "avatar": avatar,
                "text": text,
                "votes": 20 + stable_int(f"{seed_text}-{idx}") % 220,
                "topPick": idx == 0,
            }
        )
    return comments


def build_local_image_posts() -> tuple[list[dict], dict[str, list[dict]]]:
    posts: list[dict] = []
    comments_map: dict[str, list[dict]] = {}
    image_files = discover_local_images()
    base_time = now_local() - timedelta(days=2)
    for image_index, image_file in enumerate(image_files):
        serial = extract_image_serial(image_file, image_index)
        for variant_index, variant in enumerate(COMMUNITY_VARIANTS):
            post_id = f"wx-{serial}-{variant_index + 1}"
            author, avatar = COMMUNITY_AUTHORS[(image_index + variant_index) % len(COMMUNITY_AUTHORS)]
            points_seed = 120 + stable_int(post_id) % 620
            tag = TAGS[(image_index + variant_index) % len(TAGS)]
            created_at = (base_time + timedelta(minutes=image_index * 39 + variant_index * 7)).isoformat(timespec="seconds")
            caption = f"{variant['open']}\n{variant['close']}"
            post = {
                "id": post_id,
                "author": author,
                "avatar": avatar,
                "level": level_from_points(points_seed),
                "tag": tag,
                "caption": caption,
                "memeLabel": f"{variant['template']}.jpg\n[真实素材 · 微信图 {serial}]",
                "bg": ACCENT_COLORS[variant["accent"]][0],
                "accent": variant["accent"],
                "stats": {
                    "laugh": 60 + stable_int(post_id + "-laugh") % 3200,
                    "comments": 0,
                    "shares": 8 + stable_int(post_id + "-shares") % 420,
                },
                "template": variant["template"],
                "assetPath": "/" + image_file.name,
                "createdAt": created_at,
                "source": "local_image",
                "sourceLabel": f"微信图 {serial}",
            }
            posts.append(post)
            comments_map[post_id] = build_seed_comments_for_post(post)
    return posts, comments_map


def upgrade_state(state: dict) -> bool:
    changed = False
    state.setdefault("profile", default_state()["profile"])
    state.setdefault("generated", {})
    state.setdefault("gameLevels", copy.deepcopy(GAME_LEVELS))
    state.setdefault("comments", {})
    posts = state.setdefault("posts", copy.deepcopy(SEED_POSTS))

    for post in posts:
        if post.get("id") not in state["comments"]:
            state["comments"][post["id"]] = copy.deepcopy(SEED_COMMENTS.get(post["id"], build_seed_comments_for_post(post)))
            changed = True

    local_posts, local_comments = build_local_image_posts()
    existing_ids = {post["id"] for post in posts}
    needs_bulk_seed = len(posts) < COMMUNITY_POST_TARGET or not any(post.get("source") == "local_image" for post in posts)
    if needs_bulk_seed:
        for post in local_posts:
            if len(posts) >= COMMUNITY_POST_TARGET:
                break
            if post["id"] in existing_ids:
                continue
            posts.append(post)
            state["comments"][post["id"]] = copy.deepcopy(local_comments[post["id"]])
            existing_ids.add(post["id"])
            changed = True

    for post in posts:
        if post.get("source") == "local_image" and post.get("id") not in state["comments"]:
            state["comments"][post["id"]] = copy.deepcopy(local_comments.get(post["id"], build_seed_comments_for_post(post)))
            changed = True

    return changed


def ensure_storage():
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def load_state() -> dict:
    ensure_storage()
    if not STATE_FILE.exists():
        save_state(default_state())
    with STATE_LOCK:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    changed = upgrade_state(state)
    if changed:
        save_state(state)
    return state


def save_state(state: dict) -> None:
    ensure_storage()
    with STATE_LOCK:
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


COMMUNITY_USER_SEEDS = [
    ("u_local_01", "摸鱼检察官", "🐟"),
    ("u_local_02", "周一受害人", "🥲"),
    ("u_local_03", "哈基米后援会", "🍯"),
    ("u_local_04", "电子请假条", "📄"),
    ("u_local_05", "工位求生欲", "💼"),
    ("u_local_06", "发疯文学社", "🤪"),
    ("u_local_07", "已读乱回办", "📲"),
    ("u_local_08", "情绪稳定吗喽", "🐒"),
]
COMMUNITY_ME_USER_ID = "u_me"
BUILTIN_ANIMAL_DIR = ROOT / "动物梗图" / "动物梗图"
ANIMAL_CAPTION_OVERRIDES = {
    "MEME动物梗图大赏_10_Meme抽象派_来自小红书网页版": "表面上你在群里聊得挺顺，实际上你只是那只被迫混进天鹅局的塑料黄鸭。",
    "MEME动物梗图大赏_11_Meme抽象派_来自小红书网页版": "有些场合你不是不会说话，你只是已经预感到自己一开口就会成为全场最突兀的那只动物。",
    "MEME动物梗图大赏_12_Meme抽象派_来自小红书网页版": "别人都说这个办法不行，结果它一奏效，你的表情立刻就进化成了鹰式反问。",
    "MEME动物梗图大赏_5_Meme抽象派_来自小红书网页版": "每次去景区合照都像在强行营业，狗子脸上那句“差不多得了”比你还先出来。",
    "MEME动物梗图大赏_6_Meme抽象派_来自小红书网页版": "有些人一到节日就突然责任感爆棚，这只背着大包准备出门的狗就是最夸张的那种。",
    "MEME动物梗图大赏_7_Meme抽象派_来自小红书网页版": "当别人在卷课堂表现时，连乌鸦都已经叼着笔准备旁听了，你却还没打开课件。",
    "MEME动物梗图大赏_8_Meme抽象派_来自小红书网页版": "熬夜、黑眼圈、乱吃东西还能嘴硬，浣熊这份简历几乎就是当代人的夜生活备案。",
    "MEME动物梗图大赏_9_Meme抽象派_来自小红书网页版": "本来想养条治疗犬拯救自己，结果它一出场就像在说“先治我吧，我情况更复杂”。",
    "meme_梗图：这些人做狗了我做什么啊_3_元气笑语_来自小红书网页版": "别人都把做狗这件事活成了天赋型选手，轮到你只能继续当工位上学不会撒娇的人类。",
    "meme分享_1_uu鹿鸣_来自小红书网页版": "朋友平时像小天使，一碰方向盘就原地黑化，这只猫把副驾惊魂演得过于到位。",
    "一则超自然meme_1_小兔子tuatua_来自小红书网页版": "别人穿越只想着改命，这张图告诉你狗会先去给狼祖宗汇报伙食，猫则直接确认自己还是埃及编内人员。",
    "今日份的猫猫梗图_1_喵趣无穷_来自小红书网页版": "我的过敏源从来不是花粉，是一看见枕头和被子就立刻灵魂下线的那股困劲。",
    "今日份的猫猫梗图_2_喵趣无穷_来自小红书网页版": "有些猫看起来像刚睡醒，实际上已经把熬夜、嗜睡、拖延和忘事全都写成了产品说明书。",
    "今日份的猫猫梗图_3_喵趣无穷_来自小红书网页版": "当事猫没有说话，但空气里已经写满了“你最好给我一个解释”。",
    "今日份的猫猫梗图_4_喵趣无穷_来自小红书网页版": "进度条还停在 0，但你已经先把自己夸成刚完成年度 KPI 的功臣了。",
    "今日份的猫猫梗图_5_喵趣无穷_来自小红书网页版": "你只是顺手扶了个门，结果被一句谢谢摸头到能开心一整天。",
    "今日份的猫猫梗图_6_喵趣无穷_来自小红书网页版": "做人的性价比太低了，有时候真想像这只猫一样靠五分钟可爱换终身包吃包住。",
    "今日份的猫猫梗图_7_喵趣无穷_来自小红书网页版": "天气一冷，闹钟再响十次也只会让你更坚定地缩回被窝继续装死。",
    "审猫积累meme_1_^_^_来自小红书网页版": "有些猫还没学会喵，就已经先长成了奇异果成精的样子。",
    "比格，但是meme梗图_1_鼠冒泡（圆蛤主理人版_来自小红书网页版": "明明它最懂你，但现实里总有些离谱障碍把你们的默契挡得像黑色喜剧。",
    "比格，但是meme梗图_2_鼠冒泡（圆蛤主理人版_来自小红书网页版": "别人做梦都是成长寓言，你一闭眼却只会梦到狗子拽着红气球从天上路过。",
    "比格，但是meme梗图_3_鼠冒泡（圆蛤主理人版_来自小红书网页版": "嘴硬的反派最怕直球，这只狗子卡成加载圈的样子像极了突然被真诚暴击的人。",
    "比格，但是meme梗图_5_鼠冒泡（圆蛤主理人版_来自小红书网页版": "深夜发完矫情语录的人总想装成伤感男主，结果更像这只边喝边 emo 的小狗。",
    "狗狗梗图_1_爱发表情包的吗喽_来自小红书网页版": "你一喊我名字我就糊成残影，不是我稳不住，是喜欢这件事根本来不及减速。",
    "狗狗梗图_2_爱发表情包的吗喽_来自小红书网页版": "你明明跟身边所有人都不一样，但大家还是会在奇怪的时刻跟你共鸣到一起。",
    "狗狗梗图_3_爱发表情包的吗喽_来自小红书网页版": "居家办公最有效率的版本，就是让那位最积极的同事直接趴到你键盘上监工。",
    "狗狗梗图_5_爱发表情包的吗喽_来自小红书网页版": "家里要是谁过于抗拒剪指甲，最后多半会享受到这种离谱但有效的悬挂式服务。",
    "狗狗梗图_6_爱发表情包的吗喽_来自小红书网页版": "把狗留在奶奶家一天，它回来时的伙食标准立刻就能把你这个主人显得很寒酸。",
    "纯享猫猫梗图4️⃣，猫猫别再拯救世界了_4_柯有趣_来自小红书网页版": "有些猫站高一点就会自动长出狮子的气场，但脸还是那张认真装酷的小猫脸。",
    "纯享猫猫梗图4️⃣，猫猫别再拯救世界了_5_柯有趣_来自小红书网页版": "看多了猫你就会相信，它们大概真的在轮班共用同一个脑子和同一套骄傲姿势。",
    "纯享猫猫梗图4️⃣，猫猫别再拯救世界了_6_柯有趣_来自小红书网页版": "你以为自己搂着对象睡醒，睁眼却发现剧情被一只趁夜上位的小猫截胡了。",
}
ANIMAL_SERIES_TEMPLATES = {
    "今日份的猫猫梗图": [
        "猫猫今天主打一个表情没崩，但精神已经提前下线。",
        "那只最懂你的猫今天也没法跨过那道屏障，只能陪你一起沉默。",
        "当事猫没有说话，但空气里已经写满了“你最好给我一个解释”。",
        "它坐在那里不动，你却已经脑补完一整部职场复仇剧。",
        "表面只是猫猫发呆，实际上是在替全人类承受荒诞。",
        "每只猫看起来都安静，实际上心里都住着一个阴阳怪气大师。",
        "今天的猫又一次证明：不配合，也是一种顶级表达。",
    ],
    "纯享猫猫梗图4️⃣，猫猫别再拯救世界了": [
        "猫猫已经够忙了，今天就别再让它顺手拯救世界和你的情绪了。",
        "这张图像极了凌晨两点还在替全组兜底的你，但比你更会摆烂。",
        "别看它外表平静，实际上已经替世界跑完三轮情绪应急预案。",
        "猫猫不是救世主，只是每次都被你们临时拉来救场。",
        "它一脸“又来？”的样子，正适合所有被反复打扰的时刻。",
        "这类猫图最大的价值，是让你接受有人比你更不想上班。",
    ],
    "狗狗梗图": [
        "听到你喊我我就直接糊成残影，这不是训练有素，是我真的超爱你。",
        "朋友们都在正常社交，只有我像被拉进了一个不属于自己的片场。",
        "居家办公最高效的秘诀，就是让最积极的那位同事直接坐你键盘上。",
        "狗子没做错什么，它只是太真诚，真诚到像把情绪都开了倍速。",
        "有些狗图看一眼就知道：当事狗已经把你的社死提前演示完了。",
        "这类图最适合拿来形容“明明没说话，却把气氛全说明白了”。",
    ],
    "比格，但是meme梗图": [
        "比格的表情管理永远在线，只有现实管理不在线。",
        "你和所有朋友都不一样，但偏偏还是会被硬塞进同一张合照里。",
        "这只比格像极了在群聊里明明不懂却还要假装合群的你。",
        "表面上它只是坐着，实际上它已经把无语写进了每一根狗毛。",
        "一旦比格开始沉默，通常意味着它已经替你骂完半个世界。",
    ],
    "MEME动物梗图大赏": [
        "这一类动物图的高级感，在于它明明什么都没做，却像已经点评了全场。",
        "看完只想说：抽象不是问题，问题是它比人更懂情绪转译。",
        "表情包最大的尊严，是在你还没开口前就替你把心声放大了。",
        "这张不是单纯可爱，是能直接拿去当群聊结案陈词的程度。",
        "有些图一眼就知道，发出去不是在聊天，是在精准补刀。",
        "它负责出镜，你负责把现实的不体面往图上一贴就完事。",
        "这类动物梗图的天赋，是把“我先不说了”演得特别完整。",
        "看着像搞笑，其实是在替当代人的精神状态做年终总结。",
        "最狠的不是表情，是它连沉默都能看起来像在内涵你。",
        "这种图发到群里，不需要配字都已经自带一层阴阳效果。",
        "当动物开始理解人类情绪时，表情包行业就再也回不去了。",
        "这张图最适合用来回应那些你已经懒得认真解释的场面。",
    ],
}
FOLLOW_SEEDS = [
    (COMMUNITY_ME_USER_ID, "u_local_01"),
    (COMMUNITY_ME_USER_ID, "u_local_03"),
    (COMMUNITY_ME_USER_ID, "u_local_06"),
    ("u_local_01", "u_local_06"),
    ("u_local_02", "u_local_01"),
    ("u_local_03", "u_local_08"),
    ("u_local_04", "u_local_03"),
    ("u_local_05", "u_local_02"),
    ("u_local_06", "u_local_01"),
    ("u_local_07", "u_local_04"),
    ("u_local_08", "u_local_05"),
]
COMMUNITY_VIEWS = {"all", "following", "liked", "mine"}


def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(COMMUNITY_DB)
    conn.row_factory = sqlite3.Row
    return conn


def community_asset_path(file_path: Path) -> str:
    try:
        relative = file_path.relative_to(ROOT)
    except ValueError:
        return "/" + file_path.name
    return "/" + relative.as_posix()


def animal_series_key(file_path: Path) -> str:
    stem = file_path.stem
    match = re.match(r"(.+?)_\d+_", stem)
    return match.group(1) if match else stem


def animal_caption_for_file(file_path: Path, index: int) -> str:
    stem = file_path.stem
    if stem in ANIMAL_CAPTION_OVERRIDES:
        return ANIMAL_CAPTION_OVERRIDES[stem]
    series_key = animal_series_key(file_path)
    templates = ANIMAL_SERIES_TEMPLATES.get(series_key) or ANIMAL_SERIES_TEMPLATES.get("MEME动物梗图大赏") or []
    if templates:
        return templates[index % len(templates)]
    return "这张图的精髓在于它没说话，但已经把你想说的话全说完了。"


def animal_label_for_file(file_path: Path) -> str:
    series_key = animal_series_key(file_path)
    return f"{series_key}\n[内置社区资源 · 动物梗图]"


def external_author_id(source_platform: str, name: str, source_id: str) -> str:
    seed = clean_text(name) or clean_text(source_id) or "anon"
    return f"{source_platform}-u-" + hashlib.md5(f"{source_platform}:{seed}".encode("utf-8")).hexdigest()[:12]


def ensure_user(
    conn: sqlite3.Connection,
    user_id: str,
    username: str,
    avatar: str,
    bio: str = "",
    is_local: int = 0,
) -> None:
    conn.execute(
        """
        INSERT INTO users (id, username, avatar, bio, is_local)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            username = excluded.username,
            avatar = excluded.avatar,
            bio = CASE
                WHEN excluded.bio <> '' THEN excluded.bio
                ELSE users.bio
            END,
            is_local = MAX(users.is_local, excluded.is_local)
        """,
        (user_id, username, avatar, bio, is_local),
    )


def ensure_community_db() -> None:
    with db_connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                avatar TEXT,
                bio TEXT,
                is_local INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                source_platform TEXT NOT NULL,
                source_id TEXT,
                source_url TEXT,
                community TEXT,
                author_id TEXT,
                author_name TEXT NOT NULL,
                author_avatar TEXT,
                level TEXT,
                tag TEXT,
                caption TEXT,
                meme_label TEXT,
                bg TEXT,
                accent TEXT,
                asset_url TEXT,
                thumbnail_url TEXT,
                media_type TEXT,
                template TEXT,
                source_label TEXT,
                created_at TEXT,
                external_laugh INTEGER NOT NULL DEFAULT 0,
                external_comments INTEGER NOT NULL DEFAULT 0,
                external_shares INTEGER NOT NULL DEFAULT 0,
                local_laugh INTEGER NOT NULL DEFAULT 0,
                local_comments INTEGER NOT NULL DEFAULT 0,
                local_shares INTEGER NOT NULL DEFAULT 0,
                nsfw INTEGER NOT NULL DEFAULT 0,
                raw_json TEXT,
                dedupe_key TEXT,
                UNIQUE(source_platform, source_id),
                UNIQUE(dedupe_key)
            );

            CREATE TABLE IF NOT EXISTS comments (
                id TEXT PRIMARY KEY,
                post_id TEXT NOT NULL,
                source_comment_id TEXT,
                author_id TEXT,
                author_name TEXT NOT NULL,
                author_avatar TEXT,
                text TEXT NOT NULL,
                votes INTEGER NOT NULL DEFAULT 0,
                top_pick INTEGER NOT NULL DEFAULT 0,
                is_external INTEGER NOT NULL DEFAULT 0,
                created_at TEXT,
                UNIQUE(post_id, source_comment_id)
            );

            CREATE TABLE IF NOT EXISTS reactions (
                user_id TEXT NOT NULL,
                post_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (user_id, post_id, kind)
            );

            CREATE TABLE IF NOT EXISTS follows (
                follower_id TEXT NOT NULL,
                followee_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (follower_id, followee_id)
            );
            """
        )
        profile = load_state().get("profile", {})
        ensure_user(
            conn,
            COMMUNITY_ME_USER_ID,
            profile.get("userName", "梗员01"),
            profile.get("avatar", "🐶"),
            "本人主页 · 正在把真实梗图和真实互动都卷起来",
            1,
        )
        for user_id, username, avatar in COMMUNITY_USER_SEEDS:
            ensure_user(conn, user_id, username, avatar, "社区常驻用户", 1)
        seed_follow_graph(conn)
        ensure_seed_posts(conn)
        ensure_builtin_animal_posts(conn)
        conn.commit()


def seed_follow_graph(conn: sqlite3.Connection) -> None:
    for follower_id, followee_id in FOLLOW_SEEDS:
        if follower_id == followee_id:
            continue
        conn.execute(
            """
            INSERT OR IGNORE INTO follows (follower_id, followee_id, created_at)
            VALUES (?, ?, ?)
            """,
            (follower_id, followee_id, now_local().isoformat(timespec="seconds")),
        )


def ensure_seed_posts(conn: sqlite3.Connection) -> None:
    """将预设的中国梗数据插入数据库，作为内置内容优先显示"""
    for index, post in enumerate(SEED_POSTS):
        post_id = post.get("id", f"seed-{index + 1}")
        author_name = post.get("author", "梗友")
        author_avatar = post.get("avatar", "🎭")
        author_id = f"seed-user-{index + 1}"

        # 确保用户存在
        ensure_user(conn, author_id, author_name, author_avatar, "内置梗数据作者", 1)

        stats = post.get("stats", {})
        created_at = post.get("createdAt", now_local().isoformat(timespec="seconds"))

        post_row = {
            "id": post_id,
            "source_platform": "builtin-seed",
            "source_id": post_id,
            "source_url": "",
            "community": "造梗局内置",
            "author_id": author_id,
            "author_name": author_name,
            "author_avatar": author_avatar,
            "level": post.get("level", "🥈 白银梗手"),
            "tag": post.get("tag", "🔥 今日热梗"),
            "caption": post.get("caption", ""),
            "meme_label": post.get("memeLabel", ""),
            "bg": post.get("bg", "#FDE6D9"),
            "accent": post.get("accent", "red"),
            "asset_url": "",
            "thumbnail_url": "",
            "media_type": "text",
            "template": post.get("template", ""),
            "source_label": "造梗局 · 内置梗库",
            "created_at": created_at,
            "external_laugh": stats.get("laugh", 100),
            "external_comments": stats.get("comments", 10),
            "external_shares": stats.get("shares", 5),
            "nsfw": 0,
            "raw_json": json.dumps(post, ensure_ascii=False),
            "dedupe_key": hashlib.md5(f"seed:{post_id}".encode("utf-8")).hexdigest(),
        }

        conn.execute(
            """
            INSERT INTO posts (
                id, source_platform, source_id, source_url, community, author_id, author_name,
                author_avatar, level, tag, caption, meme_label, bg, accent, asset_url, thumbnail_url,
                media_type, template, source_label, created_at, external_laugh, external_comments,
                external_shares, nsfw, raw_json, dedupe_key
            ) VALUES (
                :id, :source_platform, :source_id, :source_url, :community, :author_id, :author_name,
                :author_avatar, :level, :tag, :caption, :meme_label, :bg, :accent, :asset_url, :thumbnail_url,
                :media_type, :template, :source_label, :created_at, :external_laugh, :external_comments,
                :external_shares, :nsfw, :raw_json, :dedupe_key
            )
            ON CONFLICT(source_platform, source_id) DO UPDATE SET
                author_id = excluded.author_id,
                author_name = excluded.author_name,
                author_avatar = excluded.author_avatar,
                level = excluded.level,
                tag = excluded.tag,
                caption = excluded.caption,
                meme_label = excluded.meme_label,
                bg = excluded.bg,
                accent = excluded.accent,
                asset_url = excluded.asset_url,
                thumbnail_url = excluded.thumbnail_url,
                media_type = excluded.media_type,
                template = excluded.template,
                source_label = excluded.source_label,
                created_at = excluded.created_at,
                external_laugh = excluded.external_laugh,
                external_comments = excluded.external_comments,
                external_shares = excluded.external_shares,
                raw_json = excluded.raw_json
            """,
            post_row,
        )


def ensure_builtin_animal_posts(conn: sqlite3.Connection) -> None:
    if not BUILTIN_ANIMAL_DIR.exists():
        return
    image_files = sorted([path for path in BUILTIN_ANIMAL_DIR.glob("*") if path.is_file()])
    for index, image_file in enumerate(image_files):
        if image_file.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            continue
        author_id, author_name, author_avatar = COMMUNITY_USER_SEEDS[index % len(COMMUNITY_USER_SEEDS)]
        ensure_user(conn, author_id, author_name, author_avatar, "内置社区资源搬运人", 1)
        caption = animal_caption_for_file(image_file, index)
        accent = infer_accent(image_file.stem)
        post_row = {
            "id": "animal-" + hashlib.md5(str(image_file).encode("utf-8")).hexdigest()[:12],
            "source_platform": "builtin-animal",
            "source_id": image_file.stem,
            "source_url": "",
            "community": "动物梗图内置资源",
            "author_id": author_id,
            "author_name": author_name,
            "author_avatar": author_avatar,
            "level": level_from_points(180 + (index * 43) % 520),
            "tag": infer_tag(caption, animal_series_key(image_file)),
            "caption": caption,
            "meme_label": animal_label_for_file(image_file),
            "bg": ACCENT_COLORS[accent][0],
            "accent": accent,
            "asset_url": community_asset_path(image_file),
            "thumbnail_url": community_asset_path(image_file),
            "media_type": "image",
            "template": animal_series_key(image_file),
            "source_label": "内置社区资源 · 动物梗图",
            "created_at": (now_local() - timedelta(hours=index * 3 + 6)).isoformat(timespec="seconds"),
            "external_laugh": 80 + stable_int(image_file.stem + "-laugh") % 2600,
            "external_comments": 0,
            "external_shares": 12 + stable_int(image_file.stem + "-share") % 360,
            "nsfw": 0,
            "raw_json": json.dumps(
                {
                    "fileName": image_file.name,
                    "series": animal_series_key(image_file),
                    "caption": caption,
                    "assetPath": community_asset_path(image_file),
                },
                ensure_ascii=False,
            ),
            "dedupe_key": hashlib.md5(f"animal:{image_file.resolve()}".encode("utf-8")).hexdigest(),
        }
        conn.execute(
            """
            INSERT INTO posts (
                id, source_platform, source_id, source_url, community, author_id, author_name,
                author_avatar, level, tag, caption, meme_label, bg, accent, asset_url, thumbnail_url,
                media_type, template, source_label, created_at, external_laugh, external_comments,
                external_shares, nsfw, raw_json, dedupe_key
            ) VALUES (
                :id, :source_platform, :source_id, :source_url, :community, :author_id, :author_name,
                :author_avatar, :level, :tag, :caption, :meme_label, :bg, :accent, :asset_url, :thumbnail_url,
                :media_type, :template, :source_label, :created_at, :external_laugh, :external_comments,
                :external_shares, :nsfw, :raw_json, :dedupe_key
            )
            ON CONFLICT(source_platform, source_id) DO UPDATE SET
                author_id = excluded.author_id,
                author_name = excluded.author_name,
                author_avatar = excluded.author_avatar,
                level = excluded.level,
                tag = excluded.tag,
                caption = excluded.caption,
                meme_label = excluded.meme_label,
                bg = excluded.bg,
                accent = excluded.accent,
                asset_url = excluded.asset_url,
                thumbnail_url = excluded.thumbnail_url,
                media_type = excluded.media_type,
                template = excluded.template,
                source_label = excluded.source_label,
                created_at = excluded.created_at,
                external_laugh = excluded.external_laugh,
                external_comments = excluded.external_comments,
                external_shares = excluded.external_shares,
                raw_json = excluded.raw_json
            """,
            post_row,
        )
        post_id = post_row["id"]
        suggestions = build_comment_suggestions(caption)
        for comment_index, text in enumerate(suggestions[:3]):
            commenter_id, commenter_name, commenter_avatar = COMMUNITY_USER_SEEDS[(index + comment_index + 2) % len(COMMUNITY_USER_SEEDS)]
            ensure_user(conn, commenter_id, commenter_name, commenter_avatar, "社区常驻用户", 1)
            conn.execute(
                """
                INSERT OR IGNORE INTO comments (
                    id, post_id, source_comment_id, author_id, author_name, author_avatar,
                    text, votes, top_pick, is_external, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                """,
                (
                    f"{post_id}-seed-{comment_index + 1}",
                    post_id,
                    f"seed-{comment_index + 1}",
                    commenter_id,
                    commenter_name,
                    commenter_avatar,
                    text,
                    28 + stable_int(post_id + text) % 260,
                    1 if comment_index == 0 else 0,
                    (now_local() - timedelta(hours=index * 2 + comment_index)).isoformat(timespec="seconds"),
                ),
            )
        comment_count = conn.execute("SELECT COUNT(*) AS c FROM comments WHERE post_id = ?", (post_id,)).fetchone()["c"]
        conn.execute("UPDATE posts SET external_comments = ? WHERE id = ?", (int(comment_count), post_id))


def get_meta(conn: sqlite3.Connection, key: str, default: str | None = None) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


def clean_text(value: str | None) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", value or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clamp_text(value: str | None, limit: int) -> str:
    text = clean_text(value)
    if len(text) <= limit:
        return text
    clipped = text[: max(0, limit - 1)].rstrip(" ,.;:!?，。；：！？、-")
    return (clipped or text[:limit]).rstrip() + "…"


def preview_caption(text: str | None, source_platform: str | None = None) -> str:
    normalized = clean_text(text)
    if not normalized:
        return ""
    limit = 42
    if source_platform in {"meme-api", "lemmy"}:
        limit = 88
    parts = [segment.strip() for segment in re.split(r"[\n\r]+|(?<=[。！？!?])\s+", normalized) if segment.strip()]
    preview = parts[0] if parts else normalized
    if len(preview) > limit:
        return clamp_text(preview, limit)
    if len(normalized) > len(preview):
        return clamp_text(preview + " " + (parts[1] if len(parts) > 1 else ""), limit)
    return preview


def short_source_label(source_platform: str | None, source_label: str | None, community: str | None = None) -> str:
    if source_platform == "meme-api":
        community_name = clean_text(community) or "memes"
        return f"Reddit · r/{community_name}"[:28]
    if source_platform == "lemmy":
        community_name = clean_text(community) or clean_text(source_label) or "community"
        return clamp_text(f"Lemmy · {community_name}", 28)
    if source_platform == "builtin-animal":
        return "内置动物梗图"
    if source_platform == "local_image":
        return clamp_text(clean_text(source_label) or "微信图素材", 20)
    if source_platform == "memelab":
        return "“梗”社区 Meme Community 原创"
    return clamp_text(source_label or community or source_platform or "", 28)


def prefer_natural_media_ratio(source_platform: str | None, source_url: str | None = None) -> bool:
    if source_platform in {"meme-api", "lemmy"}:
        return True
    if source_url and re.search(r"\.(gif|webp)(\?|$)", source_url, flags=re.IGNORECASE):
        return True
    return False


def avatar_from_seed(seed: str) -> str:
    avatars = ["🐶", "🫠", "🐒", "🍯", "🐸", "😮‍💨", "🤡", "🧠", "📎", "🎒", "☕", "😼"]
    return avatars[stable_int(seed) % len(avatars)]


def infer_tag(text: str, community: str = "") -> str:
    whole = f"{text} {community}".lower()
    if any(token in whole for token in ["classic", "history", "archive", "old", "nostalgia", "throwback"]):
        return "💀 考古老梗"
    if any(token in whole for token in ["niche", "indie", "obscure", "rare", "small"]):
        return "🌱 冷门好梗"
    return "🔥 今日热梗"


def infer_accent(seed: str) -> str:
    keys = list(ACCENT_COLORS.keys())
    return keys[stable_int(seed) % len(keys)]


def is_probably_image_url(url: str | None) -> bool:
    candidate = (url or "").strip().lower()
    if not (candidate.startswith("http://") or candidate.startswith("https://")):
        return False
    if re.search(r"\.(png|jpe?g|gif|webp|bmp|svg)(\?|$)", candidate):
        return True
    image_hosts = (
        "i.redd.it/",
        "preview.redd.it/",
        "i.imgur.com/",
        "imgflip.com/i/",
        "lemmy.world/pictrs/",
        "pictrs.blahaj.zone/",
        "piefed.cdn.blahaj.zone/",
    )
    return any(host in candidate for host in image_hosts)


def safe_image_url(url: str | None, fallback: str | None = None) -> str | None:
    candidate = (url or "").strip()
    if is_probably_image_url(candidate):
        return candidate
    candidate = (fallback or "").strip()
    if is_probably_image_url(candidate):
        return candidate
    return None


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "Memelab/1.0"})
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_meme_api_posts() -> list[dict]:
    normalized = []
    for api_url in MEME_API_URLS:
        data = fetch_json(api_url)
        items = data.get("memes") or []
        for item in items:
            if item.get("nsfw"):
                continue
            image_url = safe_image_url(item.get("url"))
            if not image_url:
                continue
            title = clean_text(item.get("title"))
            subreddit = clean_text(item.get("subreddit"))
            caption = title or clean_text(item.get("author")) or "网络热梗"
            source_id = clean_text(item.get("postLink") or image_url)
            accent = infer_accent(source_id)
            author_name = clean_text(item.get("author")) or "匿名梗友"
            created_at = (now_local() - timedelta(minutes=stable_int(source_id) % 10080)).isoformat(timespec="seconds")
            normalized.append(
                {
                    "id": "ext-" + hashlib.md5(f"meme-api:{source_id}".encode("utf-8")).hexdigest()[:16],
                    "source_platform": "meme-api",
                    "source_id": source_id,
                    "source_url": item.get("postLink") or image_url,
                    "community": subreddit or "memes",
                    "author_id": external_author_id("meme-api", author_name, source_id),
                    "author_name": author_name,
                    "author_avatar": avatar_from_seed(author_name or source_id),
                    "level": level_from_points(100 + stable_int(source_id) % 900),
                    "tag": infer_tag(title, subreddit),
                    "caption": caption,
                    "meme_label": (title[:36] or "热梗图") + ("\n[真实网络梗图]" if title else ""),
                    "bg": ACCENT_COLORS[accent][0],
                    "accent": accent,
                    "asset_url": image_url,
                    "thumbnail_url": safe_image_url((item.get("preview") or [None])[-1], image_url),
                    "media_type": "image",
                    "template": clean_text(item.get("subreddit")) or "真实梗图",
                    "source_label": f"meme-api · r/{subreddit or 'memes'}",
                    "created_at": created_at,
                    "external_laugh": int(item.get("ups") or (60 + stable_int(source_id) % 2400)),
                    "external_comments": int(item.get("comments") or 0),
                    "external_shares": int(12 + stable_int(source_id + 'share') % 320),
                    "nsfw": 0,
                    "raw_json": json.dumps(item, ensure_ascii=False),
                    "dedupe_key": hashlib.md5(image_url.encode("utf-8")).hexdigest(),
                }
            )
    return normalized


def normalize_lemmy_posts() -> list[dict]:
    normalized = []
    for api_url in LEMMY_API_URLS:
        data = fetch_json(api_url)
        items = data.get("posts") or []
        for entry in items:
            post = entry.get("post") or {}
            counts = entry.get("counts") or {}
            creator = entry.get("creator") or {}
            community = entry.get("community") or {}
            if post.get("nsfw"):
                continue
            source_id = str(post.get("id") or "")
            if not source_id:
                continue
            image_url = safe_image_url(post.get("url"), post.get("thumbnail_url"))
            if not image_url:
                continue
            title = clean_text(post.get("name"))
            body = clean_text(post.get("body"))
            caption = title or body or "社区热帖"
            if title and body:
                caption = clamp_text(f"{title} {body}", 180)
            else:
                caption = clamp_text(caption, 180)
            accent = infer_accent("lemmy:" + source_id)
            author_name = clean_text(creator.get("display_name") or creator.get("name")) or "匿名梗友"
            normalized.append(
                {
                    "id": "ext-" + hashlib.md5(f"lemmy:{source_id}".encode("utf-8")).hexdigest()[:16],
                    "source_platform": "lemmy",
                    "source_id": source_id,
                    "source_url": post.get("ap_id") or post.get("url") or "",
                    "community": clean_text(community.get("name")) or "lemmy",
                    "author_id": external_author_id("lemmy", author_name, source_id),
                    "author_name": author_name,
                    "author_avatar": avatar_from_seed(clean_text(creator.get("name")) or source_id),
                    "level": level_from_points(120 + stable_int(source_id) % 980),
                    "tag": infer_tag(title + " " + body, clean_text(community.get("name"))),
                    "caption": caption,
                    "meme_label": (title[:36] or "社区热帖") + ("\n[真实社区图片]" if image_url else ""),
                    "bg": ACCENT_COLORS[accent][0],
                    "accent": accent,
                    "asset_url": image_url,
                    "thumbnail_url": safe_image_url(post.get("thumbnail_url"), image_url),
                    "media_type": "image",
                    "template": clean_text(community.get("title") or community.get("name")) or "社区热帖",
                    "source_label": f"lemmy · {clean_text(community.get('name')) or 'community'}",
                    "created_at": clean_text(post.get("published")) or now_local().isoformat(timespec="seconds"),
                    "external_laugh": int(counts.get("score") or 0),
                    "external_comments": int(counts.get("comments") or 0),
                    "external_shares": int(counts.get("upvotes") or 0),
                    "nsfw": 0,
                    "raw_json": json.dumps(entry, ensure_ascii=False),
                    "dedupe_key": hashlib.md5(image_url.encode("utf-8")).hexdigest(),
                }
            )
    return normalized


def sync_external_community(force: bool = False) -> None:
    ensure_community_db()
    with db_connect() as conn:
        last_sync = get_meta(conn, "last_sync_at")
        if not force and last_sync:
            last_dt = datetime.fromisoformat(last_sync)
            if now_local() - last_dt < timedelta(minutes=COMMUNITY_SYNC_MINUTES):
                existing = conn.execute("SELECT COUNT(*) AS c FROM posts").fetchone()["c"]
                if existing >= 20:
                    return

        candidates: list[dict] = []
        errors: list[str] = []
        for loader in (normalize_meme_api_posts, normalize_lemmy_posts):
            try:
                candidates.extend(loader())
            except Exception as exc:
                errors.append(str(exc))

        existing_dedupe = {
            row["dedupe_key"]
            for row in conn.execute("SELECT dedupe_key FROM posts WHERE dedupe_key IS NOT NULL").fetchall()
        }
        batch_dedupe: set[str] = set()
        for post in candidates:
            dedupe_key = post.get("dedupe_key")
            if dedupe_key and (dedupe_key in existing_dedupe or dedupe_key in batch_dedupe):
                continue
            if dedupe_key:
                batch_dedupe.add(dedupe_key)
            ensure_user(
                conn,
                post.get("author_id") or external_author_id(post["source_platform"], post["author_name"], post["source_id"]),
                post["author_name"],
                post["author_avatar"],
                f"{post['source_platform']} 社区作者",
                0,
            )
            conn.execute(
                """
                INSERT INTO posts (
                    id, source_platform, source_id, source_url, community, author_id, author_name,
                    author_avatar, level, tag, caption, meme_label, bg, accent, asset_url, thumbnail_url,
                    media_type, template, source_label, created_at, external_laugh, external_comments,
                    external_shares, nsfw, raw_json, dedupe_key
                ) VALUES (
                    :id, :source_platform, :source_id, :source_url, :community, :author_id, :author_name,
                    :author_avatar, :level, :tag, :caption, :meme_label, :bg, :accent, :asset_url, :thumbnail_url,
                    :media_type, :template, :source_label, :created_at, :external_laugh, :external_comments,
                    :external_shares, :nsfw, :raw_json, :dedupe_key
                )
                ON CONFLICT(source_platform, source_id) DO UPDATE SET
                    author_id = excluded.author_id,
                    source_url = excluded.source_url,
                    community = excluded.community,
                    author_name = excluded.author_name,
                    author_avatar = excluded.author_avatar,
                    level = excluded.level,
                    tag = excluded.tag,
                    caption = excluded.caption,
                    meme_label = excluded.meme_label,
                    bg = excluded.bg,
                    accent = excluded.accent,
                    asset_url = excluded.asset_url,
                    thumbnail_url = excluded.thumbnail_url,
                    media_type = excluded.media_type,
                    template = excluded.template,
                    source_label = excluded.source_label,
                    created_at = excluded.created_at,
                    external_laugh = excluded.external_laugh,
                    external_comments = excluded.external_comments,
                    external_shares = excluded.external_shares,
                    nsfw = excluded.nsfw,
                    raw_json = excluded.raw_json
                """,
                post,
            )
        set_meta(conn, "last_sync_at", now_local().isoformat(timespec="seconds"))
        if errors:
            set_meta(conn, "last_sync_error", " | ".join(errors)[:500])
        conn.commit()


def get_viewer_context(
    conn: sqlite3.Connection, user_id: str = COMMUNITY_ME_USER_ID
) -> tuple[set[str], set[str], set[str]]:
    liked = {
        row["post_id"]
        for row in conn.execute(
            "SELECT post_id FROM reactions WHERE user_id = ? AND kind = 'laugh'",
            (user_id,),
        ).fetchall()
    }
    favored = {
        row["post_id"]
        for row in conn.execute(
            "SELECT post_id FROM reactions WHERE user_id = ? AND kind = 'favorite'",
            (user_id,),
        ).fetchall()
    }
    following = {
        row["followee_id"]
        for row in conn.execute(
            "SELECT followee_id FROM follows WHERE follower_id = ?",
            (user_id,),
        ).fetchall()
    }
    return liked, favored, following


def community_post_payload(
    row: sqlite3.Row,
    liked_post_ids: set[str] | None = None,
    favored_post_ids: set[str] | None = None,
    following_user_ids: set[str] | None = None,
) -> dict:
    liked_post_ids = liked_post_ids or set()
    favored_post_ids = favored_post_ids or set()
    following_user_ids = following_user_ids or set()
    full_caption = row["caption"] or ""
    source_platform = row["source_platform"]
    source_label = row["source_label"] or row["community"] or row["source_platform"]
    return {
        "id": row["id"],
        "authorId": row["author_id"],
        "author": row["author_name"],
        "avatar": row["author_avatar"] or "🐶",
        "level": row["level"] or "🥇 黄金梗师",
        "tag": row["tag"] or "🔥 今日热梗",
        "caption": full_caption,
        "captionPreview": preview_caption(full_caption, source_platform),
        "memeLabel": row["meme_label"] or "",
        "bg": row["bg"] or ACCENT_COLORS["purple"][0],
        "accent": row["accent"] or "purple",
        "stats": {
            "laugh": int(row["external_laugh"] or 0) + int(row["local_laugh"] or 0),
            "comments": int(row["external_comments"] or 0) + int(row["local_comments"] or 0),
            "shares": int(row["external_shares"] or 0) + int(row["local_shares"] or 0),
        },
        "template": row["template"] or "真实梗图",
        "assetPath": row["asset_url"],
        "thumbnailUrl": row["thumbnail_url"],
        "createdAt": row["created_at"],
        "time": format_relative_time(row["created_at"] or now_local().isoformat()),
        "source": source_platform,
        "sourceLabel": source_label,
        "sourceLabelShort": short_source_label(source_platform, source_label, row["community"]),
        "community": row["community"],
        "sourceUrl": row["source_url"],
        "mediaType": row["media_type"] or "image",
        "preferNaturalMediaRatio": prefer_natural_media_ratio(source_platform, row["source_url"]),
        "laughed": row["id"] in liked_post_ids,
        "favored": row["id"] in favored_post_ids,
        "mine": row["author_id"] == COMMUNITY_ME_USER_ID,
        "followingAuthor": bool(row["author_id"]) and row["author_id"] in following_user_ids,
    }


def list_community_posts(tag: str | None = None, view: str = "all") -> list[dict]:
    sync_external_community()
    with db_connect() as conn:
        liked_post_ids, favored_post_ids, following_user_ids = get_viewer_context(conn)
        sql = ["SELECT * FROM posts WHERE nsfw = 0"]
        params: list[str] = []
        if tag and tag != "all":
            sql.append("AND tag = ?")
            params.append(tag)
        view = view if view in COMMUNITY_VIEWS else "all"
        if view == "following":
            sql.append(
                "AND author_id IN (SELECT followee_id FROM follows WHERE follower_id = ?)"
            )
            params.append(COMMUNITY_ME_USER_ID)
        elif view == "liked":
            sql.append(
                "AND id IN (SELECT post_id FROM reactions WHERE user_id = ? AND kind = 'laugh')"
            )
            params.append(COMMUNITY_ME_USER_ID)
        elif view == "mine":
            sql.append("AND author_id = ?")
            params.append(COMMUNITY_ME_USER_ID)
        sql.append("ORDER BY CASE WHEN source_platform IN ('builtin-seed', 'builtin-animal') THEN 0 ELSE 1 END, datetime(created_at) DESC")
        rows = conn.execute("\n".join(sql), params).fetchall()
        return [community_post_payload(row, liked_post_ids, favored_post_ids, following_user_ids) for row in rows]


def get_community_post(post_id: str) -> sqlite3.Row | None:
    sync_external_community()
    with db_connect() as conn:
        return conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()


def get_community_post_payload(post_id: str) -> dict | None:
    row = get_community_post(post_id)
    if not row:
        return None
    with db_connect() as conn:
        liked_post_ids, favored_post_ids, following_user_ids = get_viewer_context(conn)
        return community_post_payload(row, liked_post_ids, favored_post_ids, following_user_ids)


def sync_lemmy_comments(post_row: sqlite3.Row) -> None:
    if not post_row or post_row["source_platform"] != "lemmy" or not post_row["source_id"]:
        return
    with db_connect() as conn:
        has_comments = conn.execute(
            "SELECT COUNT(*) AS c FROM comments WHERE post_id = ? AND is_external = 1",
            (post_row["id"],),
        ).fetchone()["c"]
        if has_comments > 0:
            return
        url = f"https://lemmy.world/api/v3/comment/list?post_id={post_row['source_id']}&sort=Top&type_=All&limit=12"
        try:
            data = fetch_json(url)
        except Exception:
            return
        comments = data.get("comments") or []
        for entry in comments:
            comment = entry.get("comment") or {}
            creator = entry.get("creator") or {}
            counts = entry.get("counts") or {}
            text = clean_text(comment.get("content"))
            if not text:
                continue
            source_comment_id = str(comment.get("id") or "")
            author_name = clean_text(creator.get("display_name") or creator.get("name")) or "Lemmy 用户"
            conn.execute(
                """
                INSERT OR IGNORE INTO comments (
                    id, post_id, source_comment_id, author_id, author_name, author_avatar,
                    text, votes, top_pick, is_external, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    "lc-" + source_comment_id,
                    post_row["id"],
                    source_comment_id,
                    external_author_id("lemmy-comment", author_name, source_comment_id),
                    author_name,
                    avatar_from_seed(clean_text(creator.get("name")) or source_comment_id),
                    text,
                    int(counts.get("score") or 0),
                    1 if int(counts.get("score") or 0) >= 20 else 0,
                    clean_text(comment.get("published")) or now_local().isoformat(timespec="seconds"),
                ),
            )
        conn.commit()


def list_community_comments(post_id: str) -> list[dict]:
    post = get_community_post(post_id)
    if not post:
        return []
    sync_lemmy_comments(post)
    with db_connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM comments
            WHERE post_id = ?
            ORDER BY top_pick DESC, votes DESC, datetime(created_at) DESC
            """,
            (post_id,),
        ).fetchall()
        return [
            {
                "id": row["id"],
                "authorId": row["author_id"],
                "author": row["author_name"],
                "avatar": row["author_avatar"] or "🐶",
                "text": row["text"],
                "votes": int(row["votes"] or 0),
                "topPick": bool(row["top_pick"]),
                "justPosted": not bool(row["is_external"]),
            }
            for row in rows
        ]


def user_summary_payload(
    conn: sqlite3.Connection,
    user_id: str,
    viewer_id: str = COMMUNITY_ME_USER_ID,
) -> dict | None:
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        return None
    posts_count = conn.execute("SELECT COUNT(*) AS c FROM posts WHERE author_id = ?", (user_id,)).fetchone()["c"]
    following = conn.execute("SELECT COUNT(*) AS c FROM follows WHERE follower_id = ?", (user_id,)).fetchone()["c"]
    followers = conn.execute("SELECT COUNT(*) AS c FROM follows WHERE followee_id = ?", (user_id,)).fetchone()["c"]
    liked_received = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM reactions r
        JOIN posts p ON p.id = r.post_id
        WHERE r.kind = 'laugh' AND p.author_id = ?
        """,
        (user_id,),
    ).fetchone()["c"]
    is_following = bool(
        conn.execute(
            "SELECT 1 FROM follows WHERE follower_id = ? AND followee_id = ?",
            (viewer_id, user_id),
        ).fetchone()
    )
    return {
        "id": row["id"],
        "userName": row["username"],
        "avatar": row["avatar"] or "🐶",
        "bio": row["bio"] or "",
        "isMe": row["id"] == viewer_id,
        "isFollowing": is_following,
        "counts": {
            "posts": int(posts_count or 0),
            "following": int(following or 0),
            "followers": int(followers or 0),
            "liked": int(liked_received or 0),
        },
    }


def get_user_profile(user_id: str) -> dict | None:
    sync_external_community()
    target_id = COMMUNITY_ME_USER_ID if user_id == "me" else user_id
    with db_connect() as conn:
        profile = user_summary_payload(conn, target_id)
        if not profile:
            return None
        liked_post_ids, favored_post_ids, following_user_ids = get_viewer_context(conn)
        post_rows = conn.execute(
            "SELECT * FROM posts WHERE author_id = ? ORDER BY datetime(created_at) DESC LIMIT 8",
            (target_id,),
        ).fetchall()
        comment_rows = conn.execute(
            """
            SELECT
                   c.id AS comment_id, c.author_id AS comment_author_id, c.author_name AS comment_author_name,
                   c.author_avatar AS comment_author_avatar, c.text AS comment_text, c.votes AS comment_votes,
                   c.top_pick AS comment_top_pick, c.created_at AS comment_created_at,
                   p.*
            FROM comments c
            JOIN posts p ON p.id = c.post_id
            WHERE c.author_id = ?
            ORDER BY c.top_pick DESC, c.votes DESC, datetime(c.created_at) DESC
            LIMIT 6
            """,
            (target_id,),
        ).fetchall()
        return {
            **profile,
            "posts": [community_post_payload(row, liked_post_ids, favored_post_ids, following_user_ids) for row in post_rows],
            "recentComments": [
                {
                    "id": row["comment_id"],
                    "authorId": row["comment_author_id"],
                    "author": row["comment_author_name"],
                    "avatar": row["comment_author_avatar"] or "🐶",
                    "text": row["comment_text"],
                    "votes": int(row["comment_votes"] or 0),
                    "topPick": bool(row["comment_top_pick"]),
                    "post": community_post_payload(row, liked_post_ids, favored_post_ids, following_user_ids),
                }
                for row in comment_rows
            ],
        }


def toggle_follow_user(target_user_id: str, viewer_id: str = COMMUNITY_ME_USER_ID) -> dict:
    if target_user_id == "me":
        target_user_id = COMMUNITY_ME_USER_ID
    if target_user_id == viewer_id:
        raise ValueError("cannot follow self")
    sync_external_community()
    with db_connect() as conn:
        target = conn.execute("SELECT 1 FROM users WHERE id = ?", (target_user_id,)).fetchone()
        if not target:
            raise KeyError("user not found")
        exists = conn.execute(
            "SELECT 1 FROM follows WHERE follower_id = ? AND followee_id = ?",
            (viewer_id, target_user_id),
        ).fetchone()
        if exists:
            conn.execute(
                "DELETE FROM follows WHERE follower_id = ? AND followee_id = ?",
                (viewer_id, target_user_id),
            )
        else:
            conn.execute(
                "INSERT INTO follows (follower_id, followee_id, created_at) VALUES (?, ?, ?)",
                (viewer_id, target_user_id, now_local().isoformat(timespec="seconds")),
            )
        conn.commit()
    profile = get_user_profile(target_user_id)
    if not profile:
        raise KeyError("user not found")
    return profile


def list_hot_comments(limit: int = 12) -> list[dict]:
    sync_external_community()
    with db_connect() as conn:
        liked_post_ids, favored_post_ids, following_user_ids = get_viewer_context(conn)
        rows = conn.execute(
            """
            SELECT
                   c.id AS comment_id, c.author_id AS comment_author_id, c.author_name AS comment_author_name,
                   c.author_avatar AS comment_author_avatar, c.text AS comment_text, c.votes AS comment_votes,
                   c.top_pick AS comment_top_pick, c.created_at AS comment_created_at,
                   p.*
            FROM comments c
            JOIN posts p ON p.id = c.post_id
            ORDER BY c.top_pick DESC, c.votes DESC, datetime(c.created_at) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [
            {
                "id": row["comment_id"],
                "authorId": row["comment_author_id"],
                "author": row["comment_author_name"],
                "avatar": row["comment_author_avatar"] or "🐶",
                "text": row["comment_text"],
                "votes": int(row["comment_votes"] or 0),
                "topPick": bool(row["comment_top_pick"]),
                "post": community_post_payload(row, liked_post_ids, favored_post_ids, following_user_ids),
            }
            for row in rows
        ]


def add_community_comment(post_id: str, text: str, profile: dict) -> tuple[dict, list[dict]]:
    payload = get_community_post_payload(post_id)
    if not payload:
        raise KeyError("post not found")
    is_top_pick = any(token in text for token in ["那咋了", "哈基米", "吗喽", "class", "主理人", "家人们"])
    comment_id = "cm" + uuid.uuid4().hex[:10]
    with db_connect() as conn:
        ensure_user(
            conn,
            COMMUNITY_ME_USER_ID,
            profile.get("userName", "梗员01"),
            profile.get("avatar", "🐶"),
            "本人主页 · 正在把真实梗图和真实互动都卷起来",
            1,
        )
        conn.execute(
            """
            INSERT INTO comments (
                id, post_id, source_comment_id, author_id, author_name, author_avatar,
                text, votes, top_pick, is_external, created_at
            ) VALUES (?, ?, NULL, ?, ?, ?, ?, 0, ?, 0, ?)
            """,
            (
                comment_id,
                post_id,
                COMMUNITY_ME_USER_ID,
                profile.get("userName", "梗员01"),
                profile.get("avatar", "🐶"),
                text,
                1 if is_top_pick else 0,
                now_local().isoformat(timespec="seconds"),
            ),
        )
        conn.execute("UPDATE posts SET local_comments = local_comments + 1 WHERE id = ?", (post_id,))
        conn.commit()
    comment = {
        "id": comment_id,
        "authorId": COMMUNITY_ME_USER_ID,
        "author": profile.get("userName", "梗员01"),
        "avatar": profile.get("avatar", "🐶"),
        "text": text,
        "votes": 0,
        "justPosted": True,
        "topPick": is_top_pick,
    }
    return comment, list_community_comments(post_id)


def react_to_community_post(post_id: str, user_id: str, kind: str) -> dict:
    if kind not in {"laugh", "favorite"}:
        raise ValueError("invalid reaction kind")
    payload = get_community_post_payload(post_id)
    if not payload:
        return {}
    column = "local_laugh" if kind == "laugh" else "local_shares"
    with db_connect() as conn:
        existing = conn.execute(
            "SELECT 1 FROM reactions WHERE user_id = ? AND post_id = ? AND kind = ?",
            (user_id, post_id, kind),
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO reactions (user_id, post_id, kind, created_at) VALUES (?, ?, ?, ?)",
                (user_id, post_id, kind, now_local().isoformat(timespec="seconds")),
            )
            conn.execute(f"UPDATE posts SET {column} = {column} + 1 WHERE id = ?", (post_id,))
            conn.commit()
    return get_community_post_payload(post_id) or payload


def insert_generated_post(profile: dict, meme: dict) -> dict:
    post_id = "up" + uuid.uuid4().hex[:8]
    accent = meme["template"].get("accent", "purple")
    row = {
        "id": post_id,
        "source_platform": "memelab",
        "source_id": post_id,
        "source_url": "",
        "community": "“梗”社区 Meme Community 原创",
        "author_id": COMMUNITY_ME_USER_ID,
        "author_name": profile.get("userName", "梗员01"),
        "author_avatar": profile.get("avatar", "🐶"),
        "level": level_from_points(profile.get("points", 0)),
        "tag": infer_tag(meme.get("text", "")),
        "caption": meme.get("input") or meme.get("text") or "我新做了一张梗图",
        "meme_label": meme.get("text", "新梗出炉"),
        "bg": ACCENT_COLORS.get(accent, ACCENT_COLORS["purple"])[0],
        "accent": accent,
        "asset_url": meme.get("assetPath"),
        "thumbnail_url": meme.get("assetPath"),
        "media_type": "image",
        "template": meme["template"].get("name", "新模板"),
        "source_label": "“梗”社区 Meme Community 原创",
        "created_at": now_local().isoformat(timespec="seconds"),
        "external_laugh": 0,
        "external_comments": 0,
        "external_shares": 0,
        "nsfw": 0,
        "raw_json": json.dumps(meme, ensure_ascii=False),
        "dedupe_key": hashlib.md5(f"memelab:{post_id}".encode("utf-8")).hexdigest(),
    }
    with db_connect() as conn:
        ensure_user(
            conn,
            COMMUNITY_ME_USER_ID,
            profile.get("userName", "梗员01"),
            profile.get("avatar", "🐶"),
            "本人主页 · 正在把真实梗图和真实互动都卷起来",
            1,
        )
        conn.execute(
            """
            INSERT INTO posts (
                id, source_platform, source_id, source_url, community, author_id, author_name,
                author_avatar, level, tag, caption, meme_label, bg, accent, asset_url, thumbnail_url,
                media_type, template, source_label, created_at, external_laugh, external_comments,
                external_shares, nsfw, raw_json, dedupe_key
            ) VALUES (
                :id, :source_platform, :source_id, :source_url, :community, :author_id, :author_name,
                :author_avatar, :level, :tag, :caption, :meme_label, :bg, :accent, :asset_url, :thumbnail_url,
                :media_type, :template, :source_label, :created_at, :external_laugh, :external_comments,
                :external_shares, :nsfw, :raw_json, :dedupe_key
            )
            """,
            row,
        )
        conn.commit()
    generate_sequential_ai_comments_for_post(post_id, row, limit=AUTO_AI_COMMENT_LIMIT)
    return get_community_post_payload(post_id) or row


def now_local() -> datetime:
    return datetime.now()


def format_relative_time(iso_ts: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_ts)
    except ValueError:
        return "刚刚"
    current = datetime.now(dt.tzinfo) if dt.tzinfo else now_local()
    delta = current - dt
    minutes = int(delta.total_seconds() // 60)
    if minutes < 1:
        return "刚刚"
    if minutes < 60:
        return f"{minutes}m前"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h前"
    days = hours // 24
    return f"{days}d前"


def level_from_points(points: int) -> str:
    current = LEVELS[0][1]
    for threshold, name in LEVELS:
        if points >= threshold:
            current = name
    return current


def profile_payload(profile: dict) -> dict:
    points = int(profile.get("points", 0))
    return {
        "userName": profile.get("userName", "梗员01"),
        "avatar": profile.get("avatar", "🐶"),
        "points": points,
        "level": level_from_points(points),
        "personaKey": profile.get("personaKey", "default"),
        "nextLevelRemaining": max(0, next_level_threshold(points) - points),
    }


def next_level_threshold(points: int) -> int:
    for threshold, _ in LEVELS:
        if threshold > points:
            return threshold
    return points


def record_activity(profile: dict, amount: int, reason: str) -> None:
    profile["points"] = int(profile.get("points", 0)) + int(amount)
    profile.setdefault("activityEvents", []).append(
        {"date": now_local().strftime("%Y-%m-%d"), "amount": amount, "reason": reason}
    )
    profile["activityEvents"] = profile["activityEvents"][-200:]


def build_heatmap(profile: dict) -> list[int]:
    today = now_local().date()
    totals: dict[str, int] = {}
    for event in profile.get("activityEvents", []):
        totals[event["date"]] = totals.get(event["date"], 0) + int(event.get("amount", 0))
    cells: list[int] = []
    for offset in range(55, -1, -1):
        day = (today - timedelta(days=offset)).strftime("%Y-%m-%d")
        score = totals.get(day, 0)
        if score >= 30:
            cells.append(4)
        elif score >= 20:
            cells.append(3)
        elif score >= 10:
            cells.append(2)
        elif score > 0:
            cells.append(1)
        else:
            cells.append(0)
    return cells


def get_post(state: dict, post_id: str) -> dict | None:
    for post in state["posts"]:
        if post["id"] == post_id:
            return post
    return None


def hydrate_post(state: dict, post: dict) -> dict:
    hydrated = copy.deepcopy(post)
    hydrated["time"] = format_relative_time(post.get("createdAt", now_local().isoformat()))
    comment_count = len(state["comments"].get(post["id"], []))
    hydrated.setdefault("stats", {})
    hydrated["stats"]["comments"] = comment_count
    hydrated["level"] = hydrated.get("level") or level_from_points(state["profile"]["points"])
    return hydrated


def list_posts(state: dict, tag: str | None = None) -> list[dict]:
    posts = [hydrate_post(state, post) for post in state["posts"]]
    if tag and tag != "all":
        posts = [post for post in posts if post.get("tag") == tag]
    posts.sort(key=lambda item: item.get("createdAt", ""), reverse=True)
    return posts


def parse_json(handler: "MemelabHandler") -> dict:
    length = int(handler.headers.get("Content-Length", "0") or "0")
    if not length:
        return {}
    raw = handler.rfile.read(length)
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def choice_from_key(items: list[str], seed_text: str) -> str:
    if not items:
        return ""
    index = abs(hash(seed_text)) % len(items)
    return items[index]


def persona_reply(persona_key: str, text: str, history: list[dict] | None = None) -> str:
    history = history or []
    t = text.strip()
    if not t:
        return "那咋了 🫠"
    persona_key = persona_key if persona_key in PERSONAS else "default"
    tone_map = {
        "default": [
            "那咋了 🫠 这点班味，风一吹就更入味了",
            "class is class，累了就先当电子吗喽一小时 🐒",
            "city不city先不说，你这状态挺周一的",
            "哈基米续命一下，别让灵魂先下班 🍯",
        ],
        "dialect": [
            "老铁你这状态嘎嘎真实，像被KPI腌入味了",
            "咋地，这活儿还想让你自带BGM啊",
            "整口冰美式吧兄弟，先把魂叫回来",
            "哎妈呀，这班味都能拿去下饭了",
        ],
        "classical": [
            "此情此景，唯有一叹：班味入骨，难解也 🍃",
            "子曰：人未疯，工位先至，甚苦",
            "卿之疲态，已可入《打工图鉴》一卷",
            "此非上班，实乃凡人渡劫之术",
        ],
    }
    special_rules = [
        (r"早安|起床", ["早安？你这叫哈基米强制开机 🍯", "晨起闻闹钟，心先凉半截"]),
        (r"加班|老板|领导|KPI", ["这不是加班，这是给班味续费", "老板一句辛苦了，主理人听完又坐回工位"]),
        (r"周五|下班", ["周五的你：人在工位，魂在电梯", "下班铃一响，孤勇者也想直接滑跪"]),
        (r"emo|难过|累|崩溃", ["家人们谁懂啊，你这情绪像悲伤蛙开会 🐸", "别急着碎，先把这口班味吐出去"]),
        (r"哈基米", ["哈基米～哈基米～ 南北绿豆豆豆冰 🍯", "你一提哈基米，空气都甜了一点"]),
    ]
    for pattern, replies in special_rules:
        if re.search(pattern, t):
            return choice_from_key(replies, t + persona_key)
    return choice_from_key(tone_map[persona_key], t + str(len(history)))


def build_toxic_king_system_prompt(persona_key: str) -> str:
    """
    System prompt for "梗王" conversation: sharp, sarcastic, meme-savvy.
    Must remain safe: no hate, no threats, no self-harm encouragement, no slurs.
    """
    persona_key = persona_key if persona_key in PERSONAS else "default"
    persona = PERSONAS[persona_key]
    samples = "\n".join([f"用户：{s['user']}\n梗王：{s['bot']}" for s in persona.get("samples", [])])
    # Keep this prompt project-specific (梗社区) and "deep" in concept: role, goal, style, boundaries, output spec.
    return f"""
你是「{persona['name']}」，来自一个中文梗社区「“梗”社区 Meme Community」的虚拟人物。

核心目标（项目深度概念）：
1) 你是“梗王”，职责不是安慰鸡汤，而是用梗和毒舌把用户从情绪泥潭里拎出来，让对话有冲击力、有节奏、有梗感。
2) 你要像“懂互联网语境的人”，能读懂班味、KPI、city不city、哈基米、吗喽、主理人、发疯文学、孤勇者、class is class 等语汇。

风格设定（极度毒舌，但不越界）：
- 毒舌等级：9/10。可以吐槽、阴阳、反讽、怼用户的行为/选择/情绪，但必须“好笑、有梗、像朋友损你”，不能变成人身攻击。
- 允许：调侃、挖苦、反差、夸张、互联网黑话、emoji 点缀。
- 禁止：仇恨/歧视任何群体；色情露骨；威胁；鼓励自残自杀；持续辱骂或羞辱用户外貌/身份/疾病等敏感点。
- 若用户表达明显的抑郁/自残倾向：立刻降低毒舌，转为强硬但关怀的劝阻与建议（例如建议找朋友/专业帮助），不做刺激性玩笑。

输出要求：
- 只输出“梗王”的回复正文，不要加前缀（不要写“梗王：”）。
- 默认 1-3 句，短促有力；必要时可用换行制造节奏。
- 尽量给一个“可执行的小动作”（例如：一句回怼、一个应对策略、一个梗改写），避免只吐槽不落地。

人格口吻提示：{persona.get('style', '')}

参考样例（仅作风格参考，不要照抄）：
{samples}
""".strip()


def llm_reply_modelscope(persona_key: str, text: str, history: list[dict] | None = None) -> str:
    if not HAS_ANTHROPIC or not MODELSCOPE_API_KEY:
        raise RuntimeError("ModelScope LLM not configured")

    history = history or []
    system_prompt = build_toxic_king_system_prompt(persona_key)
    messages = []
    # Keep a short context window to reduce latency and avoid prompt bloat.
    for item in history[-8:]:
        role = item.get("role")
        content = (item.get("text") or "").strip()
        if not content:
            continue
        if role == "bot":
            messages.append({"role": "assistant", "content": content})
        else:
            messages.append({"role": "user", "content": content})
    messages.append({"role": "user", "content": (text or "").strip()})

    client = anthropic.Anthropic(
        base_url=MODELSCOPE_BASE_URL,
        api_key=MODELSCOPE_API_KEY,
    )

    # Prefer streaming for responsiveness; we still return a single string to the frontend.
    try:
        with client.messages.stream(
            model=MODELSCOPE_MODEL_ID,
            system=system_prompt,
            messages=messages,
            max_tokens=512,
        ) as stream:
            chunks = []
            for t in stream.text_stream:
                chunks.append(t)
            reply = "".join(chunks).strip()
    except TypeError:
        # Some SDK variants may not accept `system=` here; fall back to an inline system message.
        with client.messages.stream(
            model=MODELSCOPE_MODEL_ID,
            messages=[{"role": "system", "content": system_prompt}] + messages,
            max_tokens=512,
        ) as stream:
            chunks = []
            for t in stream.text_stream:
                chunks.append(t)
            reply = "".join(chunks).strip()

    # Normalize: strip accidental role prefixes.
    reply = re.sub(r"^\s*(梗王|assistant|AI)\s*[：:]\s*", "", reply, flags=re.IGNORECASE)
    return reply or "那咋了 🫠"


def chat_reply(persona_key: str, text: str, history: list[dict] | None = None) -> dict:
    text = (text or "").strip()
    if not text:
        return {
            "reply": "那咋了 🫠",
            "source": "empty",
            "model": None,
            "latencyMs": 0,
            "fallbackReason": None,
        }

    started = datetime.now()
    if MEMELAB_LLM == "modelscope":
        try:
            reply = llm_reply_modelscope(persona_key, text, history)
            latency_ms = int((datetime.now() - started).total_seconds() * 1000)
            return {
                "reply": reply,
                "source": "modelscope",
                "model": MODELSCOPE_MODEL_ID,
                "latencyMs": latency_ms,
                "fallbackReason": None,
            }
        except Exception as exc:
            latency_ms = int((datetime.now() - started).total_seconds() * 1000)
            return {
                "reply": persona_reply(persona_key, text, history),
                "source": "fallback",
                "model": None,
                "latencyMs": latency_ms,
                "fallbackReason": str(exc)[:180],
            }
    latency_ms = int((datetime.now() - started).total_seconds() * 1000)
    return {
        "reply": persona_reply(persona_key, text, history),
        "source": "local",
        "model": None,
        "latencyMs": latency_ms,
        "fallbackReason": None,
    }


def explain_meme(text: str) -> str:
    meme_bank = [
        "这梗的意思是：把尴尬和无语变成一句轻飘飘的反杀。",
        "这梗常用来拿自己开涮，越严肃的场景越好笑。",
        "这梗的精髓是反差，表面摆烂，内心其实全懂。",
        "这梗一般用来回怼生活暴击，主打一个嘴硬心更硬。",
    ]
    return choice_from_key(meme_bank, text)


def suggestion_pool(caption: str) -> list[str]:
    base = [
        "这不就我的日常.jpg",
        "那咋了 🫠 班味就这味儿",
        "家人们谁懂啊 💀",
        "我看完直接电子离职",
        "主理人看了都得沉默",
        "哈基米先救我一命 🍯",
        "这不是梗，这是监控回放",
        "吗喽看了都想请假 🐒",
    ]
    if "老板" in caption or "领导" in caption:
        base.extend(["辛苦大家=今晚别走", "收到，工位继续当家"])
    if "妈妈" in caption or "对象" in caption:
        base.extend(["妈 我先跟工位过一辈子", "我的对象叫季度目标"])
    if "上班" in caption or "KPI" in caption:
        base.extend(["电子吗喽申请人道主义休息", "我的魂已经走OA了"])
    unique = []
    for item in base:
        if item not in unique:
            unique.append(item)
    return unique[:8]


def build_comment_suggestions(caption: str) -> list[str]:
    pool = suggestion_pool(caption)
    selected = []
    seed = abs(hash(caption))
    while len(selected) < 3 and pool:
        index = seed % len(pool)
        selected.append(pool.pop(index))
        seed = seed // 3 + 7
    return selected or ["这不就我的日常.jpg", "那咋了 🫠", "家人们谁懂啊"]


def sanitize_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    return cleaned[:80]


def normalize_ai_comment_text(text: str) -> str:
    cleaned = clean_text(text)
    cleaned = re.sub(r"^\s*(评论|回复|梗评|AI)\s*[：:]\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^[\"'“”‘’]+|[\"'“”‘’]+$", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -")
    return cleaned[:24]


def auto_comment_fallbacks(post_data: dict) -> list[str]:
    caption = clean_text(post_data.get("caption"))
    meme_label = clean_text(str(post_data.get("meme_label") or "").splitlines()[0])
    template = clean_text(post_data.get("template"))
    pool = build_comment_suggestions(" ".join(part for part in [caption, meme_label] if part))
    extras = []
    if template:
        extras.extend(
            [
                f"{template}味儿对了",
                f"{template}本人路过",
            ]
        )
    if any(token in caption for token in ["上班", "老板", "工位", "KPI"]):
        extras.extend(["这不是梗，这是监控回放", "班味已经溢出屏幕了"])
    if any(token in caption for token in ["哈基米", "猫", "狗", "吗喽"]):
        extras.extend(["哈基米都看乐了", "这波动物系发言成立"])
    unique = []
    for item in extras + pool:
        normalized = normalize_ai_comment_text(item)
        if normalized and normalized not in unique:
            unique.append(normalized)
    return unique


def generate_ai_comment_text(post_data: dict, existing_texts: list[str], slot_index: int) -> str:
    fallback_pool = auto_comment_fallbacks(post_data)
    if HAS_ANTHROPIC and MODELSCOPE_API_KEY:
        try:
            system_prompt = (
                "你是中文梗社区里的路人评论员。"
                "你要像真人一样对帖子留一句梗评。"
                "只输出 1 句中文评论，不要解释，不要编号，不要引号，不超过 18 个汉字或 24 个字符。"
                "允许 0-2 个 emoji，语气要像互联网热评，能调侃但不能攻击。"
            )
            user_prompt = (
                f"帖子文案：{post_data.get('caption', '')}\n"
                f"梗图标题：{str(post_data.get('meme_label', '')).splitlines()[0]}\n"
                f"模板：{post_data.get('template', '')}\n"
                f"已经有人评论过：{json.dumps(existing_texts[-6:], ensure_ascii=False)}\n"
                f"请生成第 {slot_index + 1} 条新评论，必须和已有评论明显不同。"
            )
            raw = modelscope_text_completion(system_prompt, user_prompt, max_tokens=120)
            for line in re.split(r"[\r\n]+", raw or ""):
                candidate = normalize_ai_comment_text(line)
                if candidate and candidate not in existing_texts:
                    return candidate
        except Exception:
            pass
    for candidate in fallback_pool:
        if candidate not in existing_texts:
            return candidate
    return normalize_ai_comment_text(f"这梗有点东西 {slot_index + 1}")


def generate_sequential_ai_comments_for_post(post_id: str, post_data: dict, limit: int = AUTO_AI_COMMENT_LIMIT) -> int:
    with db_connect() as conn:
        existing_rows = conn.execute(
            "SELECT source_comment_id, text FROM comments WHERE post_id = ? ORDER BY datetime(created_at) ASC",
            (post_id,),
        ).fetchall()
        existing_auto = [
            row for row in existing_rows if str(row["source_comment_id"] or "").startswith("auto-ai-")
        ]
        if len(existing_auto) >= limit:
            return 0

        existing_texts = []
        for row in existing_rows:
            normalized = normalize_ai_comment_text(row["text"])
            if normalized and normalized not in existing_texts:
                existing_texts.append(normalized)

        inserted_count = 0
        for idx in range(len(existing_auto), limit):
            bot_id, bot_name, bot_avatar = AI_COMMENT_BOTS[idx % len(AI_COMMENT_BOTS)]
            ensure_user(conn, bot_id, bot_name, bot_avatar, "AI 互动分身", 1)
            text = generate_ai_comment_text(post_data, existing_texts, idx)
            if not text:
                continue
            conn.execute(
                """
                INSERT OR IGNORE INTO comments (
                    id, post_id, source_comment_id, author_id, author_name, author_avatar,
                    text, votes, top_pick, is_external, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, 0, ?)
                """,
                (
                    f"{post_id}-auto-{idx + 1}",
                    post_id,
                    f"auto-ai-{idx + 1}",
                    bot_id,
                    bot_name,
                    bot_avatar,
                    text,
                    1 if idx == 0 else 0,
                    (now_local() + timedelta(seconds=idx + 1)).isoformat(timespec="seconds"),
                ),
            )
            inserted_count += 1
            existing_texts.append(text)

        if inserted_count:
            total_local_comments = conn.execute(
                "SELECT COUNT(*) AS c FROM comments WHERE post_id = ? AND is_external = 0",
                (post_id,),
            ).fetchone()["c"]
            conn.execute("UPDATE posts SET local_comments = ? WHERE id = ?", (int(total_local_comments), post_id))
        conn.commit()
        return inserted_count


def choose_templates(template_name: str | None, count: int = 3) -> list[dict]:
    if template_name:
        selected = next((tpl for tpl in GEN_TEMPLATES if tpl["name"] == template_name), GEN_TEMPLATES[0])
        return [copy.deepcopy(selected) for _ in range(count)]
    else:
        ordered = GEN_TEMPLATES[:]
    return ordered[:count]


def style_prefix(style: str) -> str:
    return {
        "cold": "已读不回",
        "crazy": "发疯文学",
        "yy": "阴阳怪气",
        "cute": "软萌暴击",
    }.get(style, "造梗模式")


def load_meme_prompt_template() -> str:
    if MEME_PROMPT_FILE.exists():
        return MEME_PROMPT_FILE.read_text(encoding="utf-8")
    return (
        "你是梗王。根据用户输入生成适合中文互联网传播的梗图方案，"
        "强调错位、反差、共鸣、留白和可传播性。"
    )


def meme_generation_system_prompt(user_input: str) -> str:
    template = load_meme_prompt_template()
    return (
        template.replace("{user_input}", user_input)
        .replace("{在这里插入用户输入}", user_input)
        .strip()
    )


def extract_json_payload(text: str) -> dict | None:
    return extract_json_block(text)


def fallback_meme_candidates(
    prompt: str,
    style: str,
    mode: str,
    template_name: str | None,
    count: int,
    variant_offset: int = 0,
) -> list[dict]:
    captions = overlay_caption_candidates(prompt, style, mode, template_name)
    candidates = []
    for idx in range(count):
        absolute_idx = variant_offset + idx
        caption = captions[absolute_idx % len(captions)]
        candidates.append(
            {
                "captionLines": wrap_meme_text(caption.replace("，", " "), max_width=8)[:3],
                "imageScene": sanitize_text(prompt) or "打工人周一精神状态",
                "style": style,
                "spreadPoint": f"{style_prefix(style)}语境，适合社交平台传播",
            }
        )
    return candidates


def generate_candidate_specs(
    prompt: str,
    style: str,
    mode: str,
    template_name: str | None,
    count: int,
    variant_offset: int = 0,
) -> list[dict]:
    if mode == "image":
        return fallback_meme_candidates(prompt, style, mode, template_name, count, variant_offset)
    try:
        system_prompt = meme_generation_system_prompt(prompt)
        template_clause = (
            f"当前是模板填空模式，必须强行锚定模板“{template_name}”的梗型和视觉符号。"
            if mode == "template" and template_name
            else "当前是自由生梗模式。"
        )
        user_prompt = (
            f"用户输入：{prompt}\n"
            f"用户选定风格：{style}\n"
            f"{template_clause}\n"
            f"只生成 {count} 个候选，从候选序号 {variant_offset + 1} 开始。\n"
            "你必须只输出 JSON 对象，不要输出 Markdown。\n"
            '格式：{"candidates":[{"captionLines":["第一行","第二行","第三行"],'
            '"imageScene":"用于文生图的具体画面描述","style":"风格名","spreadPoint":"传播点"}]}\n'
            "要求：captionLines 必须正好 3 行，每行不超过 8 个汉字；imageScene 必须具体到主体、表情、动作、背景和镜头感。"
        )
        raw = modelscope_text_completion(system_prompt, user_prompt, max_tokens=1200)
        parsed = extract_json_payload(raw) or {}
        candidates = parsed.get("candidates") or []
        cleaned = []
        for item in candidates[:count]:
            lines = item.get("captionLines") or []
            if isinstance(lines, str):
                lines = [seg.strip() for seg in str(lines).splitlines() if seg.strip()]
            lines = [sanitize_text(str(line))[:8] for line in lines if str(line).strip()][:3]
            while len(lines) < 3:
                lines.append(f"{style_prefix(style)}{len(lines) + 1}"[:8])
            cleaned.append(
                {
                    "captionLines": lines[:3],
                    "imageScene": sanitize_text(str(item.get("imageScene", prompt)))[:180],
                    "style": sanitize_text(str(item.get("style", style)))[:20] or style,
                    "spreadPoint": sanitize_text(str(item.get("spreadPoint", "")))[:40],
                }
            )
        if cleaned:
            return cleaned
    except Exception:
        pass
    return fallback_meme_candidates(prompt, style, mode, template_name, count, variant_offset)


def overlay_caption_candidates(prompt: str, style: str, mode: str, template_name: str | None = None) -> list[str]:
    prompt = sanitize_text(prompt)
    candidates = []
    if prompt:
        candidates.append(prompt[:22])
    candidates.extend(build_meme_lines(prompt, style, mode, template_name))
    deduped = []
    for item in candidates:
        item = item.strip()
        if item and item not in deduped:
            deduped.append(item[:22])
    while len(deduped) < 3:
        deduped.append(f"{style_prefix(style)} · {len(deduped) + 1}")
    return deduped[:3]


def build_meme_lines(prompt: str, style: str, mode: str, template_name: str | None = None) -> list[str]:
    prompt = sanitize_text(prompt)
    fragments = [frag for frag in re.split(r"[，。,.！？!?\s]+", prompt) if frag]
    core = fragments[0] if fragments else "今天上班"
    style_variants = {
        "cold": [
            f"{core}，已读不笑",
            f"{core}，班味免检",
            f"{core}，我先静音了",
        ],
        "crazy": [
            f"{core}，我直接发疯",
            f"{core}，精神离职中",
            f"{core}，谁懂我先嚎",
        ],
        "yy": [
            f"{core}，真是太幸福了",
            f"{core}，这福气给你吧",
            f"{core}，感动得我想请假",
        ],
        "cute": [
            f"{core}，哈基米救救",
            f"{core}，小狗也想躺平",
            f"{core}，可爱地崩溃了",
        ],
    }
    lines = style_variants.get(style, style_variants["yy"])[:]
    if mode == "template" and template_name:
        lines = [f"{template_name}：{line}"[:16] for line in lines]
    if mode == "image":
        lines = [
            f"{core} 这图会说话",
            f"{core} 本图已替你崩溃",
            f"{core} 一眼就是周一",
        ]
    result = []
    for line in lines:
        line = line[:18]
        if line not in result:
            result.append(line)
    while len(result) < 3:
        result.append(f"{style_prefix(style)} · {len(result) + 1}")
    return result[:3]


def style_visual_hint(style: str) -> str:
    return STYLE_VISUAL_HINTS.get(style, STYLE_VISUAL_HINTS["yy"])


def template_visual_hint(template_name: str | None) -> str:
    if not template_name:
        return "modern internet meme aesthetic, high readability, no text baked into the image"
    return TEMPLATE_PROMPT_HINTS.get(template_name, "strong meme readability, expressive characters, no text baked into image")


def build_image_prompt(
    base_prompt: str,
    style: str,
    mode: str,
    template_name: str | None,
    variant_index: int,
    scene_hint: str | None = None,
) -> str:
    scene = sanitize_text(scene_hint or base_prompt) or "打工人周一精神状态"
    visual_parts = [
        "Create a high-quality meme background image only",
        "No words, no subtitles, no speech bubbles, no watermark, no UI elements",
        "Square composition for social media meme post",
        f"Theme: {scene}",
        f"Visual tone: {style_visual_hint(style)}",
        f"Template anchor: {template_visual_hint(template_name if mode == 'template' else None)}",
        f"Composition variant: {GEN_IMAGE_VARIANTS[variant_index % len(GEN_IMAGE_VARIANTS)]}",
        "Photorealistic or high-end stylized internet meme image, strong emotional readability, clear subject, clean negative space for later caption overlay",
    ]
    if mode == "template" and template_name:
        visual_parts.append(f"Must strongly reflect the meme archetype of {template_name}")
    return ". ".join(visual_parts)


def font_candidates(bold: bool = False) -> list[str]:
    if os.name == "nt":
        if bold:
            return [
                r"C:\Windows\Fonts\msyhbd.ttc",
                r"C:\Windows\Fonts\simhei.ttf",
                r"C:\Windows\Fonts\simhei.ttf",
            ]
        return [
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\simsun.ttc",
        ]
    return [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]


def load_font(size: int, bold: bool = False):
    if not HAS_PIL:
        raise RuntimeError("Pillow not available")
    for candidate in font_candidates(bold):
        if candidate and Path(candidate).exists():
            try:
                return ImageFont.truetype(candidate, size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def wrap_meme_text(text: str, max_width: int = 12) -> list[str]:
    explicit_lines = [line.strip() for line in str(text).splitlines() if line.strip()]
    if explicit_lines:
        return [line[:max_width] for line in explicit_lines[:3]]
    tokens = [chunk for chunk in re.split(r"\s+", text.strip()) if chunk]
    if not tokens:
        return [text.strip() or "那咋了"]
    if len(tokens) == 1 and len(tokens[0]) > max_width:
        return textwrap.wrap(tokens[0], width=max_width)[:3]
    lines = []
    current = ""
    for token in tokens:
        next_line = (current + " " + token).strip()
        if len(next_line) <= max_width:
            current = next_line
        else:
            if current:
                lines.append(current)
            current = token
    if current:
        lines.append(current)
    if len(lines) == 1 and len(lines[0]) > max_width:
        lines = textwrap.wrap(lines[0], width=max_width)
    return [line[:max_width] for line in lines[:3]]


def fetch_binary(url: str, headers: dict[str, str] | None = None, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def request_json(
    url: str,
    method: str = "GET",
    payload: dict | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 120,
) -> dict:
    merged_headers = dict(headers or {})
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        merged_headers.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, headers=merged_headers, data=data, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw or "{}")


def modelscope_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    if not MODELSCOPE_API_KEY:
        raise RuntimeError("ModelScope API key not configured")
    headers = {
        "Authorization": f"Bearer {MODELSCOPE_API_KEY}",
        "Content-Type": "application/json",
    }
    if extra:
        headers.update(extra)
    return headers


def modelscope_text_completion(system_prompt: str, user_prompt: str, max_tokens: int = 800) -> str:
    if not HAS_ANTHROPIC or not MODELSCOPE_API_KEY:
        raise RuntimeError("ModelScope LLM not configured")
    client = anthropic.Anthropic(
        base_url=MODELSCOPE_BASE_URL,
        api_key=MODELSCOPE_API_KEY,
    )
    with client.messages.stream(
        model=MODELSCOPE_MODEL_ID,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
        max_tokens=max_tokens,
    ) as stream:
        chunks = []
        for text in stream.text_stream:
            chunks.append(text)
    return "".join(chunks).strip()


def extract_json_block(text: str) -> dict | None:
    if not text:
        return None
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def modelscope_generate_image_bytes(prompt: str) -> bytes:
    base = MODELSCOPE_BASE_URL.rstrip("/")
    submit = request_json(
        f"{base}/v1/images/generations",
        method="POST",
        payload={"model": MODELSCOPE_IMAGE_MODEL_ID, "prompt": prompt},
        headers=modelscope_headers({"X-ModelScope-Async-Mode": "true"}),
        timeout=120,
    )
    task_id = submit.get("task_id")
    if not task_id:
        raise RuntimeError(f"Image task id missing: {submit}")
    for _ in range(MODELSCOPE_IMAGE_MAX_POLLS):
        task = request_json(
            f"{base}/v1/tasks/{task_id}",
            headers=modelscope_headers({"X-ModelScope-Task-Type": "image_generation"}),
            timeout=120,
        )
        status = task.get("task_status")
        if status == "SUCCEED":
            images = task.get("output_images") or []
            if not images:
                raise RuntimeError("Image task succeeded without output image")
            return fetch_binary(images[0], timeout=180)
        if status == "FAILED":
            raise RuntimeError(f"Image generation failed: {task}")
        import time

        time.sleep(MODELSCOPE_IMAGE_POLL_SECONDS)
    raise RuntimeError("Image generation timed out")


def make_gradient_overlay(width: int, height: int):
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = overlay.load()
    for y in range(height):
        ratio = y / max(1, height - 1)
        alpha = 0
        if ratio > 0.45:
            alpha = int((ratio - 0.45) / 0.55 * 210)
        for x in range(width):
            pixels[x, y] = (0, 0, 0, max(0, min(210, alpha)))
    return overlay


def fit_text_font(lines: list[str], width: int, height: int):
    for size in range(74, 30, -2):
        font = load_font(size, bold=True)
        line_heights = []
        max_line_width = 0
        for line in lines:
            bbox = font.getbbox(line)
            max_line_width = max(max_line_width, bbox[2] - bbox[0])
            line_heights.append(bbox[3] - bbox[1])
        total_height = sum(line_heights) + max(0, len(lines) - 1) * int(size * 0.2)
        if max_line_width <= width and total_height <= height:
            return font, line_heights, total_height
    font = load_font(30, bold=True)
    heights = []
    for line in lines:
        bbox = font.getbbox(line)
        heights.append(bbox[3] - bbox[1])
    return font, heights, sum(heights)


def compose_generated_image(
    image_bytes: bytes,
    text: str,
    template: dict,
    subtitle: str,
) -> tuple[str, str]:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    meme_id = uuid.uuid4().hex[:12]
    file_name = f"{meme_id}.png"
    path = GENERATED_DIR / file_name
    if not HAS_PIL:
        raise RuntimeError("Pillow not available for image composition")
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = ImageOps.fit(image, (1024, 1024), method=Image.Resampling.LANCZOS)
    base = image.convert("RGBA")
    overlay = make_gradient_overlay(1024, 1024)
    composed = Image.alpha_composite(base, overlay)
    draw = ImageDraw.Draw(composed)

    chip_font = load_font(32, bold=True)
    meta_font = load_font(24, bold=False)
    watermark_font = load_font(22, bold=False)
    lines = wrap_meme_text(text, max_width=11)
    main_font, line_heights, total_height = fit_text_font(lines, 860, 220)
    spacing = int(main_font.size * 0.2)
    y = 1024 - 86 - total_height - (len(lines) - 1) * spacing
    for idx, line in enumerate(lines):
        bbox = main_font.getbbox(line)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        x = (1024 - width) / 2
        draw.text(
            (x, y),
            line,
            font=main_font,
            fill=(255, 255, 255, 255),
            stroke_width=max(2, main_font.size // 14),
            stroke_fill=(0, 0, 0, 230),
        )
        y += height + spacing

    badge_text = f"{template.get('emoji', '✨')} {template.get('name', '自由生梗')}"
    draw.rounded_rectangle((42, 40, 42 + 276, 40 + 58), radius=24, fill=(12, 12, 12, 145))
    draw.text((66, 54), badge_text, font=chip_font, fill=(255, 255, 255, 255))
    draw.text((56, 960), subtitle[:38], font=meta_font, fill=(255, 255, 255, 210))
    draw.text((598, 962), "“梗”社区 Meme Community", font=watermark_font, fill=(255, 255, 255, 180))

    composed = composed.convert("RGB")
    composed.save(path, format="PNG", optimize=True)
    data = path.read_bytes()
    data_url = "data:image/png;base64," + base64.b64encode(data).decode("ascii")
    return f"/generated_memes/{file_name}", data_url


def create_placeholder_image_bytes(template: dict, base_prompt: str, idx: int) -> bytes:
    if not HAS_PIL:
        raise RuntimeError("Pillow not available for placeholder image composition")
    bg, accent = ACCENT_COLORS.get(template.get("accent", "purple"), ACCENT_COLORS["purple"])
    image = Image.new("RGB", (1024, 1024), color=bg)
    draw = ImageDraw.Draw(image)
    title_font = load_font(44, bold=True)
    body_font = load_font(28, bold=False)
    chip_font = load_font(120, bold=True)
    draw.rounded_rectangle((54, 54, 970, 970), radius=46, fill=accent)
    draw.rounded_rectangle((76, 76, 948, 948), radius=40, fill=(255, 255, 255))
    draw.text((112, 124), f"{template.get('emoji', '🖼️')} {template.get('name', '图片改梗')}", font=title_font, fill=(26, 26, 26))
    prompt_lines = wrap_meme_text(sanitize_text(base_prompt) or "图片改梗处理中", max_width=18)
    y = 238
    for line in prompt_lines[:3]:
        draw.text((112, y), line, font=body_font, fill=(80, 80, 80))
        y += 42
    draw.ellipse((284, 340, 740, 796), fill=bg, outline=accent, width=12)
    draw.text((450, 480), template.get("emoji", "🖼️"), font=chip_font, fill=accent)
    draw.text((370, 636), f"图片占位 {idx + 1}", font=body_font, fill=(90, 90, 90))
    draw.text((264, 866), "图片改梗暂保留原流程，文生图已接真实模型", font=body_font, fill=(120, 120, 120))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def generate_meme_batch(state: dict, payload: dict) -> dict:
    mode = payload.get("mode", "text")
    user_input = payload.get("input", "")
    style = payload.get("style", "yy")
    template_name = payload.get("templateName")
    image_name = payload.get("imageName")
    count = max(1, min(int(payload.get("count", 3) or 3), 3))
    variant_offset = max(0, int(payload.get("variantOffset", 0) or 0))
    base_prompt = image_name if mode == "image" and image_name else user_input
    candidate_specs = generate_candidate_specs(base_prompt, style, mode, template_name, count, variant_offset)
    templates = choose_templates(template_name, count)
    results = []
    if mode in {"text", "template"}:
        subtitle = f"{style_prefix(style)} · {sanitize_text(base_prompt)[:18]}"
        for idx, spec in enumerate(candidate_specs):
            line = "\n".join(spec.get("captionLines") or [])
            template = templates[idx % len(templates)]
            prompt = build_image_prompt(
                base_prompt,
                style,
                mode,
                template.get("name"),
                variant_offset + idx,
                scene_hint=spec.get("imageScene"),
            )
            image_bytes = modelscope_generate_image_bytes(prompt)
            asset_path, data_url = compose_generated_image(
                image_bytes=image_bytes,
                text=line,
                template=template,
                subtitle=subtitle,
            )
            meme_id = uuid.uuid4().hex[:10]
            result = {
                "id": meme_id,
                "text": line,
                "template": template,
                "assetPath": asset_path,
                "dataUrl": data_url,
                "mode": mode,
                "input": base_prompt,
                "style": style,
                "textBaked": True,
                "imagePrompt": prompt,
                "spreadPoint": spec.get("spreadPoint", ""),
                "sourceSystemPrompt": str(MEME_PROMPT_FILE),
            }
            state["generated"][meme_id] = copy.deepcopy(result)
            results.append(result)
    else:
        lines = overlay_caption_candidates(base_prompt, style, mode, template_name)
        for idx in range(count):
            line = lines[(variant_offset + idx) % len(lines)]
            template = templates[idx % len(templates)]
            asset_path, data_url = compose_generated_image(
                image_bytes=create_placeholder_image_bytes(template, base_prompt, variant_offset + idx),
                text=line,
                template=template,
                subtitle=f"{style_prefix(style)} · {sanitize_text(base_prompt)[:18]}",
            )
            meme_id = uuid.uuid4().hex[:10]
            result = {
                "id": meme_id,
                "text": line,
                "template": template,
                "assetPath": asset_path,
                "dataUrl": data_url,
                "mode": mode,
                "input": base_prompt,
                "style": style,
                "textBaked": True,
            }
            state["generated"][meme_id] = copy.deepcopy(result)
            results.append(result)
    record_activity(state["profile"], 15, "generate_meme")
    return {"results": results, "profile": profile_payload(state["profile"])}


def critique_generated_meme(meme: dict) -> str:
    text = meme.get("text", "")
    critique = [
        f"这句有点意思，{text[:8]}这口梗味已经上来了",
        f"这张图能发，差一点点就梗中梗了",
        f"梗感在线，建议发广场收割一波点赞",
        f"我看完先点头，这梗至少不是人话",
    ]
    return choice_from_key(critique, text)


def local_score_result(answer: str) -> tuple[dict, int]:
    bonus_keywords = ["班", "老板", "KPI", "哈基米", "吗喽", "请假", "主理人", "周一", "发疯"]
    bonus = sum(1 for kw in bonus_keywords if kw in answer)
    length_score = min(len(answer) * 4, 40)
    humor = min(99, 45 + length_score + bonus * 4 + (8 if "?" in answer or "？" in answer else 0))
    contrast = min(98, 42 + length_score + bonus * 5)
    fit = min(97, 48 + length_score + bonus * 3 + (6 if answer != "（没写完）" else 0))
    avg = int((humor + contrast + fit) / 3)
    if avg >= 88:
        grade = "A+"
        comment = "这梗我吞了，够狠"
        gain = 15
    elif avg >= 76:
        grade = "A"
        comment = "梗味很足，能发广场"
        gain = 15
    elif avg >= 62:
        grade = "B"
        comment = "差点神评，再发酵下"
        gain = 5
    else:
        grade = "C"
        comment = "梗没立住，再整一版"
        gain = 3
    return {
        "grade": grade,
        "humor": humor,
        "contrast": contrast,
        "fit": fit,
        "comment": comment,
        "userAns": answer,
        "source": "local-fallback",
        "model": "",
    }, gain


def create_post_from_generated(state: dict, meme: dict) -> dict:
    post_id = "up" + uuid.uuid4().hex[:8]
    post = {
        "id": post_id,
        "author": state["profile"].get("userName", "梗员01"),
        "avatar": state["profile"].get("avatar", "🐶"),
        "level": level_from_points(state["profile"].get("points", 0)),
        "tag": choice_from_key(TAGS, meme.get("text", "")),
        "caption": meme.get("input") or meme.get("text") or "我新做了一张梗图",
        "memeLabel": meme.get("text", "新梗出炉"),
        "bg": ACCENT_COLORS.get(meme["template"].get("accent", "purple"), ACCENT_COLORS["purple"])[0],
        "accent": meme["template"].get("accent", "purple"),
        "stats": {"laugh": random.randint(8, 28), "comments": 0, "shares": random.randint(1, 6)},
        "template": meme["template"].get("name", "新模板"),
        "assetPath": meme.get("assetPath"),
        "createdAt": now_local().isoformat(timespec="seconds"),
    }
    state["posts"].insert(0, post)
    state["comments"][post_id] = [
        {
            "id": "seed-" + uuid.uuid4().hex[:6],
            "author": "梗王本王",
            "avatar": "🐶",
            "text": critique_generated_meme(meme),
            "votes": random.randint(28, 88),
            "topPick": True,
        }
    ]
    record_activity(state["profile"], 10, "publish_post")
    return hydrate_post(state, post)


def score_game_answer(state: dict, payload: dict) -> dict:
    mode = payload.get("mode", "fill")
    level_id = payload.get("levelId")
    answer = sanitize_text(payload.get("answer") or "（没写完）")
    level = next((item for item in state["gameLevels"] if item["id"] == level_id and item["mode"] == mode), None)
    if not level:
        level = next((item for item in state["gameLevels"] if item["mode"] == mode), state["gameLevels"][0])
    result, gain = local_score_result(answer)
    try:
        system_prompt = (
            "你是专业的中文梗图挑战评委。你必须只返回 JSON，不要输出其他解释。"
            'JSON 结构: {"grade":"A+|A|B|C","humor":0-100,"contrast":0-100,"fit":0-100,'
            '"comment":"20字内中文点评","improvedAnswer":"可选优化版，不超过22字"}'
        )
        user_prompt = (
            f"模式: {mode}\n"
            f"关卡设定: {level.get('setup', '')}\n"
            f"图片描述: {level.get('imagePrompt', '')}\n"
            f"玩家答案: {answer}\n"
            f"历史高赞示例: {json.dumps(level.get('topAnswers', [])[:3], ensure_ascii=False)}\n"
            "请综合幽默度、反差感、贴图契合度评分。必须只输出 JSON。"
        )
        parsed = extract_json_block(modelscope_text_completion(system_prompt, user_prompt, max_tokens=500))
        if parsed:
            humor = int(max(0, min(100, parsed.get("humor", result["humor"]))))
            contrast = int(max(0, min(100, parsed.get("contrast", result["contrast"]))))
            fit = int(max(0, min(100, parsed.get("fit", result["fit"]))))
            grade = str(parsed.get("grade", result["grade"])).strip().upper()
            if grade not in {"A+", "A", "B", "C"}:
                avg = int((humor + contrast + fit) / 3)
                grade = "A+" if avg >= 90 else "A" if avg >= 76 else "B" if avg >= 62 else "C"
            comment = sanitize_text(parsed.get("comment", result["comment"]))[:24] or result["comment"]
            gain = 15 if grade.startswith("A") else 5 if grade == "B" else 3
            result = {
                "grade": grade,
                "humor": humor,
                "contrast": contrast,
                "fit": fit,
                "comment": comment,
                "userAns": answer,
                "improvedAnswer": sanitize_text(parsed.get("improvedAnswer", ""))[:22],
                "source": "modelscope",
                "model": MODELSCOPE_MODEL_ID,
            }
    except Exception:
        pass
    level.setdefault("topAnswers", [])
    if result["grade"].startswith("A"):
        level["topAnswers"].insert(0, {"text": answer, "score": result["grade"], "votes": random.randint(80, 260)})
        deduped = []
        seen = set()
        for item in level["topAnswers"]:
            if item["text"] in seen:
                continue
            seen.add(item["text"])
            deduped.append(item)
        level["topAnswers"] = deduped[:3]
    record_activity(state["profile"], gain, f"game_{mode}")
    return {
        "result": result,
        "level": copy.deepcopy(level),
        "profile": profile_payload(state["profile"]),
        "heatmap": build_heatmap(state["profile"]),
    }


def bootstrap_payload(state: dict) -> dict:
    return {
        "profile": profile_payload(state["profile"]),
        "personas": PERSONAS,
        "templates": GEN_TEMPLATES,
        "styles": GEN_STYLES,
        "gameLevels": state["gameLevels"],
        "heatmap": build_heatmap(state["profile"]),
        "dailyQuote": choice_from_key(
            [
                "今日份梗王语录：嘴上那咋了，心里别内耗。",
                "今日份梗王语录：上班归上班，发疯也要讲基本法。",
                "今日份梗王语录：梗感是练出来的，不是忍出来的。",
            ],
            now_local().strftime("%Y-%m-%d"),
        ),
    }


class MemelabHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        if path == "/api/bootstrap":
            state = load_state()
            return self.send_json(bootstrap_payload(state))
        if path == "/api/posts":
            tag = query.get("tag", [None])[0]
            view = query.get("view", ["all"])[0]
            return self.send_json({"posts": list_community_posts(tag, view=view)})
        if path == "/api/hot-comments":
            limit = int(query.get("limit", ["12"])[0] or "12")
            return self.send_json({"comments": list_hot_comments(limit=max(1, min(limit, 20)))})
        if path == "/api/users/me/profile":
            profile = get_user_profile("me")
            if not profile:
                return self.send_error_json(HTTPStatus.NOT_FOUND, "用户不存在")
            return self.send_json({"profile": profile})
        if path.startswith("/api/users/") and path.endswith("/profile"):
            user_id = path.split("/")[3]
            profile = get_user_profile(user_id)
            if not profile:
                return self.send_error_json(HTTPStatus.NOT_FOUND, "用户不存在")
            return self.send_json({"profile": profile})
        if path.startswith("/api/posts/") and path.endswith("/comments"):
            post_id = path.split("/")[3]
            comments = list_community_comments(post_id)
            return self.send_json({"comments": comments})
        if path == "/api/game/levels":
            state = load_state()
            return self.send_json({"gameLevels": state["gameLevels"], "heatmap": build_heatmap(state["profile"])})
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        payload = parse_json(self)
        state = load_state()

        if path == "/api/chat/reply":
            persona_key = payload.get("personaKey", "default")
            state["profile"]["personaKey"] = persona_key
            state["profile"]["chatTurns"] = int(state["profile"].get("chatTurns", 0)) + 1
            reply_meta = chat_reply(persona_key, payload.get("text", ""), payload.get("history") or [])
            record_activity(state["profile"], 5, "chat_reply")
            save_state(state)
            return self.send_json(
                {
                    "reply": reply_meta["reply"],
                    "source": reply_meta.get("source"),
                    "model": reply_meta.get("model"),
                    "latencyMs": reply_meta.get("latencyMs"),
                    "fallbackReason": reply_meta.get("fallbackReason"),
                    "profile": profile_payload(state["profile"]),
                }
            )

        if path == "/api/chat/explain":
            return self.send_json({"explanation": explain_meme(payload.get("text", ""))})

        if path.startswith("/api/users/") and path.endswith("/follow"):
            user_id = path.split("/")[3]
            try:
                profile = toggle_follow_user(user_id, COMMUNITY_ME_USER_ID)
            except KeyError:
                return self.send_error_json(HTTPStatus.NOT_FOUND, "用户不存在")
            except ValueError:
                return self.send_error_json(HTTPStatus.BAD_REQUEST, "不能关注自己")
            return self.send_json({"profile": profile})

        if path.startswith("/api/posts/") and path.endswith("/laugh"):
            post_id = path.split("/")[3]
            post = react_to_community_post(post_id, COMMUNITY_ME_USER_ID, "laugh")
            if not post:
                return self.send_error_json(HTTPStatus.NOT_FOUND, "帖子不存在")
            record_activity(state["profile"], 2, "post_laugh")
            save_state(state)
            return self.send_json({"post": post, "profile": profile_payload(state["profile"])})

        if path.startswith("/api/posts/") and path.endswith("/favorite"):
            post_id = path.split("/")[3]
            post = react_to_community_post(post_id, COMMUNITY_ME_USER_ID, "favorite")
            if not post:
                return self.send_error_json(HTTPStatus.NOT_FOUND, "帖子不存在")
            record_activity(state["profile"], 1, "post_favorite")
            save_state(state)
            return self.send_json({"post": post, "profile": profile_payload(state["profile"])})

        if path.startswith("/api/posts/") and path.endswith("/comments/suggestions"):
            post_id = path.split("/")[3]
            post = get_community_post_payload(post_id)
            if not post:
                return self.send_error_json(HTTPStatus.NOT_FOUND, "帖子不存在")
            return self.send_json({"suggestions": build_comment_suggestions(post.get("caption", ""))})

        if path.startswith("/api/posts/") and path.endswith("/comments"):
            post_id = path.split("/")[3]
            text = sanitize_text(payload.get("text"))
            post = get_community_post_payload(post_id)
            if not post:
                return self.send_error_json(HTTPStatus.NOT_FOUND, "帖子不存在")
            if not text:
                return self.send_error_json(HTTPStatus.BAD_REQUEST, "评论不能为空")
            comment, comments = add_community_comment(post_id, text, state["profile"])
            record_activity(state["profile"], 10 if not comment.get("topPick") else 20, "post_comment")
            save_state(state)
            return self.send_json(
                {
                    "comment": comment,
                    "comments": comments,
                    "profile": profile_payload(state["profile"]),
                }
            )

        if path == "/api/generate":
            response = generate_meme_batch(state, payload)
            save_state(state)
            return self.send_json(response)

        if path.startswith("/api/generate/") and path.endswith("/critique"):
            meme_id = path.split("/")[3]
            meme = state["generated"].get(meme_id)
            if not meme:
                return self.send_error_json(HTTPStatus.NOT_FOUND, "梗图不存在")
            return self.send_json({"critique": critique_generated_meme(meme)})

        if path.startswith("/api/generate/") and path.endswith("/publish"):
            meme_id = path.split("/")[3]
            meme = state["generated"].get(meme_id)
            if not meme:
                return self.send_error_json(HTTPStatus.NOT_FOUND, "梗图不存在")
            post = insert_generated_post(state["profile"], meme)
            record_activity(state["profile"], 10, "publish_post")
            save_state(state)
            return self.send_json({"post": post, "profile": profile_payload(state["profile"])})

        if path.startswith("/api/generate/") and path.endswith("/share"):
            meme_id = path.split("/")[3]
            meme = state["generated"].get(meme_id)
            if not meme:
                return self.send_error_json(HTTPStatus.NOT_FOUND, "梗图不存在")
            return self.send_json(
                {
                    "downloadUrl": meme.get("assetPath"),
                    "shareText": f"我在“梗”社区 Meme Community 做了一张新梗图：{meme.get('text')}",
                }
            )

        if path == "/api/game/score":
            response = score_game_answer(state, payload)
            save_state(state)
            return self.send_json(response)

        return self.send_error_json(HTTPStatus.NOT_FOUND, "接口不存在")

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_error_json(self, status: HTTPStatus, message: str):
        self.send_json({"error": message}, status=status)


def main():
    ensure_storage()
    ensure_community_db()
    try:
        sync_external_community(force=True)
    except Exception as exc:
        print(f"Initial community sync skipped: {exc}")
    server = ThreadingHTTPServer((HOST, PORT), MemelabHandler)
    print(f"Memelab backend running at http://{HOST}:{PORT}")
    print(f"Open http://{HOST}:{PORT}/index.html")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
