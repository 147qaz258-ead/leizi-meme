// ------------- Plaza / Feed (刷梗广场) -------------

function Plaza({ onPointGain, onOpenGen }) {
  const [filter, setFilter] = React.useState('all');
  const [posts, setPosts] = React.useState(SEED_POSTS);
  const [detailPost, setDetailPost] = React.useState(null);
  const [showSheet, setShowSheet] = React.useState(false);

  const filters = [
    { key: 'all', label: '全部' },
    { key: '🔥 今日热梗', label: '🔥 今日热梗' },
    { key: '🌱 冷门好梗', label: '🌱 冷门好梗' },
    { key: '💀 考古老梗', label: '💀 考古老梗' },
  ];

  const visible = filter === 'all' ? posts : posts.filter(p => p.tag === filter);

  function laugh(id) {
    setPosts(ps => ps.map(p => p.id === id
      ? { ...p, stats: { ...p.stats, laugh: p.stats.laugh + 1 }, laughed: true }
      : p));
    onPointGain(2);
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#FAFAFB', position: 'relative' }}>
      {/* header */}
      <div style={{ padding: '8px 20px 10px', background: '#FAFAFB', position: 'sticky', top: 0, zIndex: 5 }}>
        <div style={{ fontSize: 28, fontWeight: 800, letterSpacing: '-0.3px' }}>广场 🔥</div>
        <div style={{ fontSize: 12, color: '#888', marginTop: 2 }}>刷的是梗，评的也是梗</div>
        {/* filter chips */}
        <div className="no-scroll" style={{
          display: 'flex', gap: 8, overflowX: 'auto',
          marginTop: 12, paddingBottom: 4,
        }}>
          {filters.map(f => (
            <button key={f.key} onClick={() => setFilter(f.key)} style={{
              flexShrink: 0,
              padding: '7px 14px', borderRadius: 999, fontSize: 12, fontWeight: 600,
              background: filter === f.key ? '#1A1A1A' : '#F0F0F0',
              color: filter === f.key ? '#fff' : '#888',
              transition: 'all 0.2s',
            }}>{f.label}</button>
          ))}
        </div>
      </div>

      {/* feed */}
      <div className="no-scroll" style={{
        flex: 1, overflowY: 'auto',
        padding: '4px 16px 120px',
        display: 'flex', flexDirection: 'column', gap: 14,
      }}>
        {visible.map(p => (
          <PostCard key={p.id} post={p} onLaugh={() => laugh(p.id)} onOpenDetail={() => setDetailPost(p)}/>
        ))}
      </div>

      {/* floating CTA */}
      <div style={{
        position: 'absolute', right: 16, bottom: 20, zIndex: 8,
      }}>
        <RotatingCTA text="发梗 · 发梗 · 发梗 · " centerEmoji="+" size={96}
                     onClick={() => setShowSheet(true)}/>
      </div>

      {showSheet && <PostSheet onClose={() => setShowSheet(false)} onGen={() => { setShowSheet(false); onOpenGen(); }}/>}
      {detailPost && <PostDetail post={detailPost} onClose={() => setDetailPost(null)} onPointGain={onPointGain}/>}
    </div>
  );
}

function PostCard({ post, onLaugh, onOpenDetail }) {
  return (
    <div className="pop-in" style={{
      background: '#fff', borderRadius: 20, overflow: 'hidden',
      boxShadow: 'var(--shadow-card)',
    }}>
      {/* header */}
      <div style={{ padding: '12px 14px', display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 36, height: 36, borderRadius: '50%',
          background: post.bg, display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 20,
        }}>{post.avatar}</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ fontSize: 13, fontWeight: 700 }}>@{post.author}</div>
            <LevelTag level={post.level}/>
          </div>
          <div style={{ fontSize: 11, color: '#888', marginTop: 2, display: 'flex', gap: 6 }}>
            <Badge accent={post.accent}>{post.tag}</Badge>
            <span>· {post.time}</span>
          </div>
        </div>
      </div>

      {/* meme image */}
      <MemePlaceholder label={post.memeLabel} aspect="1/1" bg={post.bg}/>

      {/* caption */}
      <div style={{ padding: '12px 16px 10px', fontSize: 14, lineHeight: 1.55, whiteSpace: 'pre-line' }}>
        {post.caption}
      </div>

      {/* actions */}
      <div style={{ display: 'flex', borderTop: '1px solid #F0F0F0' }}>
        <ActionBtn icon="😂" label={post.stats.laugh} active={post.laughed} onClick={onLaugh}/>
        <ActionBtn icon="💬" label="用梗评" onClick={onOpenDetail}/>
        <ActionBtn icon="🎨" label="二创"/>
        <ActionBtn icon="♡" label={post.stats.shares}/>
      </div>
    </div>
  );
}

function ActionBtn({ icon, label, active, onClick }) {
  return (
    <button onClick={onClick} style={{
      flex: 1, padding: '10px 0',
      display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 5,
      fontSize: 12, color: active ? 'var(--red)' : '#666',
      fontWeight: active ? 700 : 500,
    }}>
      <span style={{ fontSize: 15 }}>{icon}</span>
      <span>{label}</span>
    </button>
  );
}

function PostDetail({ post, onClose, onPointGain }) {
  const [comments, setComments] = React.useState([
    { id: 'c1', author: '梗王本王', avatar: '🐶', text: '这班上得跟考公似的 🫠', votes: 156, topPick: true },
    { id: 'c2', author: '班味浓郁', avatar: '😮‍💨', text: '那咋了.jpg', votes: 89 },
    { id: 'c3', author: '发疯专业户', avatar: '🤪', text: '啊啊啊啊啊周五快来啊啊啊', votes: 54 },
  ]);
  const [aiSuggestions, setAiSuggestions] = React.useState([]);
  const [loadingAI, setLoadingAI] = React.useState(false);
  const [customComment, setCustomComment] = React.useState('');

  async function loadAISuggestions() {
    setLoadingAI(true);
    try {
      const prompt = `用户在梗社区看到一条梗帖：「${post.caption}」。
请给出3个"用梗回评"的短句，每句不超过20字，只用梗、emoji、年轻人口吻。直接输出3行，不要编号，不要解释：`;
      const r = await window.claude.complete(prompt);
      const lines = (r || '').split('\n').map(l => l.trim().replace(/^[-·0-9.、)】]+\s*/, '')).filter(Boolean).slice(0, 3);
      setAiSuggestions(lines.length ? lines : ['这不就我的日常.jpg', '那咋了 🫠 班味就这味儿', '家人们谁懂啊']);
    } catch (e) {
      setAiSuggestions(['这不就我的日常.jpg', '那咋了 🫠 班味就这味儿', '家人们谁懂啊']);
    }
    setLoadingAI(false);
  }

  function postComment(text) {
    if (!text.trim()) return;
    setComments(cs => [{ id: 'nc' + Date.now(), author: '我', avatar: '😎', text, votes: 0, justPosted: true }, ...cs]);
    setCustomComment('');
    onPointGain(10);
  }

  return (
    <div className="fade-in" style={{
      position: 'absolute', inset: 0, zIndex: 90, background: 'rgba(0,0,0,0.5)',
    }} onClick={onClose}>
      <div className="slide-up" onClick={e => e.stopPropagation()} style={{
        position: 'absolute', left: 0, right: 0, bottom: 0, top: 40,
        background: '#FAFAFB', borderRadius: '28px 28px 0 0',
        display: 'flex', flexDirection: 'column',
      }}>
        <div style={{ width: 40, height: 4, background: '#E0E0E0', borderRadius: 999, margin: '10px auto 4px' }}/>

        <div className="no-scroll" style={{ flex: 1, overflowY: 'auto', padding: '8px 16px 16px' }}>
          {/* original post mini */}
          <div style={{
            background: '#fff', borderRadius: 16, padding: 12,
            display: 'flex', gap: 10, alignItems: 'center',
            boxShadow: 'var(--shadow-card)',
          }}>
            <div style={{ width: 48, height: 48, flexShrink: 0, borderRadius: 10, overflow: 'hidden' }}>
              <MemePlaceholder label={post.avatar} aspect="1/1" bg={post.bg}/>
            </div>
            <div style={{ flex: 1, fontSize: 13, lineHeight: 1.4, whiteSpace: 'pre-line' }}>{post.caption}</div>
          </div>

          {/* banner */}
          <div style={{
            marginTop: 14, padding: '10px 14px',
            background: 'linear-gradient(90deg, #FFF7E6, #FFEDC2)',
            borderRadius: 14, fontSize: 12, fontWeight: 600, color: '#8B6914',
            display: 'flex', alignItems: 'center', gap: 8,
          }}>
            <span>⚠️</span>
            <span>评论区只收梗，不收人话。没灵感？让AI帮你想。</span>
          </div>

          {/* comments */}
          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#888', marginBottom: 10 }}>
              梗评 · {comments.length}
            </div>
            {comments.map(c => (
              <CommentCard key={c.id} comment={c}/>
            ))}
          </div>
        </div>

        {/* AI suggestions + input */}
        <div style={{ borderTop: '1px solid #EEE', background: '#fff', padding: '10px 16px 12px' }}>
          {aiSuggestions.length > 0 && (
            <div style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 11, color: 'var(--blue)', fontWeight: 700, marginBottom: 6 }}>
                🤖 AI 给你3个梗，选一个回？
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {aiSuggestions.map((s, i) => (
                  <button key={i} onClick={() => postComment(s)} className="pop-in" style={{
                    textAlign: 'left', padding: '8px 12px',
                    background: '#F0F6FF', border: '1px solid #D5E6FB',
                    borderRadius: 12, fontSize: 13, color: '#1A1A1A',
                  }}>{s}</button>
                ))}
              </div>
            </div>
          )}
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <button onClick={loadAISuggestions} disabled={loadingAI} style={{
              padding: '8px 12px', borderRadius: 999,
              background: loadingAI ? '#E0E0E0' : '#F0F6FF',
              color: 'var(--blue)', fontSize: 12, fontWeight: 700,
              flexShrink: 0,
            }}>{loadingAI ? 'AI想中…' : '🤖 AI帮我想'}</button>
            <input
              value={customComment}
              onChange={e => setCustomComment(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && postComment(customComment)}
              placeholder="自己来一个梗…"
              style={{
                flex: 1, padding: '8px 12px', border: '1px solid #E5E5E5',
                borderRadius: 999, fontSize: 13, outline: 'none',
              }}/>
            <button onClick={() => postComment(customComment)} style={{
              padding: '8px 14px', borderRadius: 999,
              background: customComment.trim() ? 'var(--purple)' : '#DDD',
              color: '#fff', fontSize: 13, fontWeight: 700,
              flexShrink: 0,
            }}>发</button>
          </div>
          <button onClick={onClose} style={{
            marginTop: 10, width: '100%', padding: 10, fontSize: 12, color: '#888',
          }}>关闭</button>
        </div>
      </div>
    </div>
  );
}

function CommentCard({ comment }) {
  return (
    <div className={comment.justPosted ? 'pop-in' : ''} style={{
      background: '#fff', borderRadius: 14, padding: 12, marginBottom: 8,
      position: 'relative',
      boxShadow: 'var(--shadow-card)',
    }}>
      {comment.topPick && (
        <div style={{
          position: 'absolute', top: -8, left: 12,
          background: 'linear-gradient(90deg, #FFD700, #FFA500)',
          color: '#fff', fontSize: 10, fontWeight: 800,
          padding: '3px 10px', borderRadius: 999,
          letterSpacing: '0.3px',
        }}>✨ 梗中梗</div>
      )}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
        <div style={{
          width: 32, height: 32, borderRadius: '50%', background: '#F5F5F5',
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16,
          flexShrink: 0,
        }}>{comment.avatar}</div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: '#666' }}>@{comment.author}</div>
          <div style={{ fontSize: 14, marginTop: 4, lineHeight: 1.5 }}>{comment.text}</div>
          <div style={{ fontSize: 11, color: '#AAA', marginTop: 6, display: 'flex', gap: 12 }}>
            <span>👍 {comment.votes}</span>
            <span>回复</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function PostSheet({ onClose, onGen }) {
  const opts = [
    { icon: '📷', title: '从相册上传', desc: '相册选图/短视频，加梗文' },
    { icon: '✨', title: '现做一张', desc: '跳到梗图生成，一键出梗图', primary: true },
    { icon: '🎨', title: '用模板二创', desc: '选广场上的梗模板填空' },
  ];
  return (
    <div className="fade-in" style={{
      position: 'absolute', inset: 0, zIndex: 100, background: 'rgba(0,0,0,0.4)',
    }} onClick={onClose}>
      <div className="slide-up" onClick={e => e.stopPropagation()} style={{
        position: 'absolute', left: 0, right: 0, bottom: 0,
        background: '#fff', borderRadius: '28px 28px 0 0',
        padding: '12px 16px 28px',
      }}>
        <div style={{ width: 40, height: 4, background: '#E0E0E0', borderRadius: 999, margin: '4px auto 12px' }}/>
        <div style={{ fontSize: 18, fontWeight: 800, marginBottom: 4, padding: '0 4px' }}>发个梗</div>
        <div style={{ fontSize: 12, color: '#888', marginBottom: 14, padding: '0 4px' }}>三种方式，随你整</div>
        {opts.map((o, i) => (
          <button key={i} onClick={o.primary ? onGen : onClose} style={{
            width: '100%', display: 'flex', alignItems: 'center', gap: 14,
            padding: '14px 14px', marginBottom: 8,
            background: o.primary ? 'linear-gradient(135deg, #F0EBFA, #E8E0F5)' : '#F7F7F8',
            borderRadius: 16, textAlign: 'left',
          }}>
            <div style={{
              width: 44, height: 44, borderRadius: '50%', background: '#fff',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 22, flexShrink: 0,
            }}>{o.icon}</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 15, fontWeight: 700 }}>{o.title}</div>
              <div style={{ fontSize: 12, color: '#888', marginTop: 2 }}>{o.desc}</div>
            </div>
            <span style={{ color: '#BBB' }}>›</span>
          </button>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, { Plaza });
