// ------------- Seeded data -------------

// 12 meme posts for 广场
const SEED_POSTS = [
  {
    id: 'p1', author: '班味十足', avatar: '😮‍💨', level: '🥇 黄金梗师',
    tag: '🔥 今日热梗', time: '12m前',
    caption: '老板周五六点在群里说"辛苦大家"的时候，我',
    memeLabel: '狗头保命.jpg\n[表情包：柴犬歪头]',
    bg: '#FDE6D9', accent: 'red',
    stats: { laugh: 234, comments: 18, shares: 41 },
    template: '狗头保命',
  },
  {
    id: 'p2', author: '那咋了本了', avatar: '🫠', level: '💠 钻石梗王',
    tag: '🔥 今日热梗', time: '1h前',
    caption: '妈：你看看人家孩子\n我：那咋了',
    memeLabel: '那咋了.jpg\n[东北老大爷表情]',
    bg: '#E8F4FD', accent: 'blue',
    stats: { laugh: 1820, comments: 103, shares: 289 },
    template: '那咋了',
  },
  {
    id: 'p3', author: 'city不city', avatar: '🧳', level: '🥇 黄金梗师',
    tag: '🔥 今日热梗', time: '3h前',
    caption: '上海？city不city啊？\n————友情提醒：浦东很city，地铁13号线不太city',
    memeLabel: '[金发外国美女 戴墨镜 比耶]',
    bg: '#E5F7EC', accent: 'green',
    stats: { laugh: 892, comments: 56, shares: 134 },
    template: 'city不city',
  },
  {
    id: 'p4', author: '孤勇者本者', avatar: '⚔️', level: '💎 铂金梗将',
    tag: '💀 考古老梗', time: '5h前',
    caption: '谁说站在光里的才算英雄\n————周一早八赶地铁的打工人',
    memeLabel: '[黑白剪影 打工人背影]',
    bg: '#EEE9F8', accent: 'purple',
    stats: { laugh: 567, comments: 28, shares: 88 },
    template: '孤勇者',
  },
  {
    id: 'p5', author: '职场MBTI', avatar: '📋', level: '🥈 白银梗手',
    tag: '🌱 冷门好梗', time: '6h前',
    caption: '领导：这个你先做着\n我（I人）：好的 🙂\n我（内心）：这啥玩意儿',
    memeLabel: '[I人表面平静内心咆哮]',
    bg: '#FCF0E0', accent: 'amber',
    stats: { laugh: 421, comments: 35, shares: 52 },
    template: '表里不一',
  },
  {
    id: 'p6', author: '早八怨种', avatar: '🥲', level: '🥇 黄金梗师',
    tag: '🔥 今日热梗', time: '8h前',
    caption: '闹钟响的那一刻\n我的灵魂：已离开躯壳',
    memeLabel: '[悲伤蛙 Pepe 躺平]',
    bg: '#E5F7EC', accent: 'green',
    stats: { laugh: 733, comments: 49, shares: 95 },
    template: '悲伤蛙',
  },
  {
    id: 'p7', author: '发疯文学家', avatar: '🤪', level: '💠 钻石梗王',
    tag: '🔥 今日热梗', time: '10h前',
    caption: '啊啊啊啊啊我不想上班啊啊啊谁懂啊家人们',
    memeLabel: '[猫猫崩溃 爪子抱头]',
    bg: '#FDE6D9', accent: 'red',
    stats: { laugh: 2340, comments: 187, shares: 412 },
    template: '发疯文学',
  },
  {
    id: 'p8', author: '特种兵旅游', avatar: '🎒', level: '🥇 黄金梗师',
    tag: '🌱 冷门好梗', time: '12h前',
    caption: '48小时6个城市12个景点\n回来请了3天病假',
    memeLabel: '[地图 + 红色路线 + 大哭]',
    bg: '#E8F4FD', accent: 'blue',
    stats: { laugh: 389, comments: 22, shares: 41 },
    template: '特种兵',
  },
  {
    id: 'p9', author: '吗喽打工', avatar: '🐒', level: '🥈 白银梗手',
    tag: '🔥 今日热梗', time: '14h前',
    caption: '一只吗喽站在工位上\n它没有明天，只有KPI',
    memeLabel: '[猴子戴领带 电脑前]',
    bg: '#FCF0E0', accent: 'amber',
    stats: { laugh: 612, comments: 44, shares: 73 },
    template: '吗喽',
  },
  {
    id: 'p10', author: '哈基米', avatar: '🍯', level: '🥇 黄金梗师',
    tag: '🔥 今日热梗', time: '18h前',
    caption: '哈基米～哈基米～\n南北绿豆～豆豆冰',
    memeLabel: '[可爱水豚 戴花]',
    bg: '#EEE9F8', accent: 'purple',
    stats: { laugh: 1045, comments: 78, shares: 201 },
    template: '哈基米',
  },
  {
    id: 'p11', author: 'class is class', avatar: '🎓', level: '🥈 白银梗手',
    tag: '💀 考古老梗', time: '1d前',
    caption: 'Why？\n别问 问就是 class is class',
    memeLabel: '[学生崩溃 撕书]',
    bg: '#FDE6D9', accent: 'red',
    stats: { laugh: 287, comments: 15, shares: 34 },
    template: 'class is class',
  },
  {
    id: 'p12', author: '主理人', avatar: '☕', level: '💎 铂金梗将',
    tag: '🌱 冷门好梗', time: '1d前',
    caption: '我不是老板，我是主理人\n（店里就我一个人）',
    memeLabel: '[咖啡师独自站柜台]',
    bg: '#E5F7EC', accent: 'green',
    stats: { laugh: 498, comments: 37, shares: 61 },
    template: '主理人',
  },
];

// 梗王人格
const PERSONAS = {
  default: {
    key: 'default',
    name: '梗王',
    subtitle: '不会造梗？我教你啊',
    greeting: '我是梗王，问就是 class is class，来整活儿啊',
    style: '互联网热梗、emoji混搭、年轻人口吻',
    samples: [
      { user: '今天好累', bot: '那咋了 🫠 累了就累了，打工人的尊严不就是一瓶肥宅快乐水吗' },
      { user: '加班到十点', bot: '班味浓到能腌菜了家人们 🥬 建议：下班回家先对着天花板骂三分钟再睡' },
    ],
  },
  dialect: {
    key: 'dialect',
    name: '梗王·东北版',
    subtitle: '整点儿活儿呗 老铁',
    greeting: '唠嗑啊兄弟！今儿咋地，给整点儿啥梗？',
    style: '东北方言、老铁、嘎嘎、咋地、整活儿',
    samples: [
      { user: '今天好累', bot: '嘎嘎累是吧？那咋地 老铁这班上的跟三班倒似的 整一口儿吧！' },
      { user: '加班到十点', bot: '哎妈呀 这班上得跟大棚种菜似的 走 老铁 撸串去！' },
    ],
  },
  classical: {
    key: 'classical',
    name: '梗王·文言版',
    subtitle: '诸君 且听朕道梗一则',
    greeting: '吾乃梗王。尔有何惑？朕以古法解之。',
    style: '文言文 + 现代梗，子曰体，之乎者也',
    samples: [
      { user: '今天好累', bot: '劳则怨，怨则躺，躺则愈累。此乃"班味"之循环，古已有之，无解也 🍃' },
      { user: '加班到十点', bot: '子曰：朝九晚十，非人哉！卿可效法陶令，不为五斗米折腰，然五斗米实在香 💰' },
    ],
  },
};

// 梗图生成 - 预设结果
const GEN_TEMPLATES = [
  { name: '狗头保命', emoji: '🐶', accent: 'amber' },
  { name: '那咋了', emoji: '🫠', accent: 'blue' },
  { name: '悲伤蛙', emoji: '🐸', accent: 'green' },
  { name: '震惊脸', emoji: '😱', accent: 'red' },
  { name: '哈基米', emoji: '🍯', accent: 'amber' },
  { name: '吗喽', emoji: '🐒', accent: 'purple' },
];

const GEN_STYLES = [
  { key: 'cold', label: '冷漠系' },
  { key: 'crazy', label: '癫狂系' },
  { key: 'yy', label: '阴阳系' },
  { key: 'cute', label: '可爱系' },
];

// 游戏关卡
const GAME_LEVELS = [
  {
    id: 1,
    setup: '星期一早上8点，地铁挤得像罐头',
    imagePrompt: '[悲伤蛙 被挤成饼]',
    topAnswers: [
      { text: '我不是在通勤，我是在被搬运', score: 'A', votes: 892 },
      { text: '这不是上班，这是上供', score: 'A', votes: 734 },
    ],
  },
  {
    id: 2,
    setup: '妈妈打电话问你找对象了吗',
    imagePrompt: '[电话一响 浑身发抖]',
    topAnswers: [
      { text: '妈 我在谈 跟KPI谈', score: 'A+', votes: 1204 },
      { text: '我不是单身 我是高纯度', score: 'A', votes: 889 },
    ],
  },
];

Object.assign(window, { SEED_POSTS, PERSONAS, GEN_TEMPLATES, GEN_STYLES, GAME_LEVELS });
