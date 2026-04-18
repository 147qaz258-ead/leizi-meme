// ------------- Meme King Home Chat (梗王首页) -------------

function MemeKingHome({ persona, setPersona, onPointGain, points, level }) {
  const [messages, setMessages] = React.useState([
    { role: 'bot', text: persona.greeting, id: 'init' },
  ]);
  const [input, setInput] = React.useState('');
  const [typing, setTyping] = React.useState(false);
  const [showPersonaSwitch, setShowPersonaSwitch] = React.useState(false);
  const scrollRef = React.useRef(null);

  // Reset on persona change
  React.useEffect(() => {
    setMessages([{ role: 'bot', text: persona.greeting, id: 'p-' + persona.key }]);
  }, [persona.key]);

  React.useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, typing]);

  async function send(text) {
    if (!text.trim()) return;
    const uid = 'u' + Date.now();
    setMessages(m => [...m, { role: 'user', text, id: uid }]);
    setInput('');
    setTyping(true);

    let reply = '';
    try {
      const samples = persona.samples.map(s => `用户：${s.user}\n梗王：${s.bot}`).join('\n\n');
      const prompt = `你现在扮演"梗王"，一个只会用中文互联网梗和emoji回答问题的AI NPC。性格：${persona.style}。
回复要求：
1. 只用梗、emoji、段子回答，不要规劝、不要客服口吻
2. 可以结合"那咋了"、"class is class"、"city不city"、"班味"、"孤勇者"、"哈基米"、"吗喽"、"主理人"、"发疯文学"等中文热梗
3. 控制在40字以内，一句到两句
4. 可以怼用户、反问、丢奇怪的梗

参考样例：
${samples}

用户说：${text}
梗王（只回复一句梗，不要解释）：`;
      reply = await window.claude.complete(prompt);
      reply = (reply || '').trim().replace(/^梗王[：:]\s*/, '');
    } catch (e) {
      reply = '这梗我给你扬了 💀 AI抽风了，你换一个试试？';
    }
    setTyping(false);
    setMessages(m => [...m, { role: 'bot', text: reply || '那咋了 🫠', id: 'b' + Date.now() }]);
    onPointGain(5);
  }

  const quickReplies = ['今天好累', '老板又PUA我', '帮我想一个周五下班的梗', '给我一个哈基米版本的早安'];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#FAFAFB' }}>
      {/* header */}
      <div style={{ padding: '8px 20px 12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ fontSize: 32, fontWeight: 900, letterSpacing: '-0.5px', lineHeight: 1.15 }}>
              吾乃{persona.name}
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
              {persona.subtitle}
            </div>
          </div>
          <button
            onClick={() => setShowPersonaSwitch(true)}
            style={{
              width: 40, height: 40, borderRadius: '50%',
              background: '#F0F0F0', display: 'flex',
              alignItems: 'center', justifyContent: 'center',
              fontSize: 18,
            }}>🎭</button>
        </div>
      </div>

      {/* doge avatar + stats row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '4px 20px 12px' }}>
        <div className="bob" style={{ flexShrink: 0 }}>
          <DogeAvatar size={88} expression="smirk"/>
        </div>
        <div className="grad-border" style={{ flex: 1, padding: '12px 14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: 11, color: '#888', fontWeight: 600 }}>今日梗值</div>
              <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--purple)', fontFamily: 'var(--font-num)' }}>
                +{points}
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 11, color: '#888', fontWeight: 600 }}>当前段位</div>
              <div style={{ fontSize: 13, fontWeight: 700, marginTop: 2 }}>{level}</div>
            </div>
          </div>
        </div>
      </div>

      {/* message list */}
      <div ref={scrollRef} className="no-scroll" style={{
        flex: 1, overflowY: 'auto',
        padding: '8px 16px 16px',
        display: 'flex', flexDirection: 'column', gap: 12,
      }}>
        {messages.map((m, i) => (
          <MessageBubble key={m.id} msg={m} />
        ))}
        {typing && (
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8 }}>
            <div style={{ width: 32, height: 32, flexShrink: 0 }}>
              <DogeAvatar size={32} />
            </div>
            <div style={{
              background: 'var(--purple-light)', padding: '12px 16px',
              borderRadius: '16px 16px 16px 4px',
              display: 'flex', gap: 4, alignItems: 'center',
            }}>
              <span className="typing-dot"/>
              <span className="typing-dot"/>
              <span className="typing-dot"/>
            </div>
          </div>
        )}

        {/* quick replies after init */}
        {messages.length === 1 && !typing && (
          <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ fontSize: 11, color: '#AAA', fontWeight: 600, letterSpacing: 0.3 }}>试试这么聊 👇</div>
            {quickReplies.map((q, i) => (
              <button key={i} onClick={() => send(q)} style={{
                textAlign: 'left', padding: '10px 14px',
                background: '#fff', border: '1px solid #EDEDED',
                borderRadius: 14, fontSize: 13, color: '#444',
              }}>{q}</button>
            ))}
          </div>
        )}
      </div>

      {/* input bar */}
      <div style={{ padding: '10px 16px 12px', background: '#FAFAFB', borderTop: '1px solid #EEE' }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          background: '#fff', border: '1px solid #E5E5E5',
          borderRadius: 999, padding: '6px 6px 6px 16px',
        }}>
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send(input)}
            placeholder="跟梗王唠两句…"
            style={{
              flex: 1, border: 'none', outline: 'none', fontSize: 14,
              background: 'transparent', fontFamily: 'inherit',
            }}
          />
          <button onClick={() => send(input)} disabled={!input.trim()} style={{
            height: 32, padding: '0 14px', borderRadius: 999,
            background: input.trim() ? 'var(--purple)' : '#DDD',
            color: '#fff', fontSize: 13, fontWeight: 700,
            transition: 'all 0.2s',
          }}>发送</button>
        </div>
      </div>

      {showPersonaSwitch && (
        <PersonaSheet current={persona} onPick={p => { setPersona(p); setShowPersonaSwitch(false); }}
                      onClose={() => setShowPersonaSwitch(false)}/>
      )}
    </div>
  );
}

function MessageBubble({ msg }) {
  const isBot = msg.role === 'bot';
  return (
    <div className="pop-in" style={{
      display: 'flex', gap: 8, alignItems: 'flex-end',
      justifyContent: isBot ? 'flex-start' : 'flex-end',
    }}>
      {isBot && (
        <div style={{ width: 32, height: 32, flexShrink: 0 }}>
          <DogeAvatar size={32} />
        </div>
      )}
      <div style={{
        maxWidth: '75%', padding: '10px 14px',
        fontSize: 15, lineHeight: 1.5,
        background: isBot ? 'var(--purple-light)' : '#1A1A1A',
        color: isBot ? '#1A1A1A' : '#fff',
        borderRadius: isBot ? '16px 16px 16px 4px' : '16px 16px 4px 16px',
        whiteSpace: 'pre-line',
        wordBreak: 'break-word',
      }}>{msg.text}</div>
    </div>
  );
}

function PersonaSheet({ current, onPick, onClose }) {
  return (
    <div style={{
      position: 'absolute', inset: 0, zIndex: 100,
      background: 'rgba(0,0,0,0.4)',
    }} onClick={onClose} className="fade-in">
      <div className="slide-up" onClick={e => e.stopPropagation()} style={{
        position: 'absolute', left: 0, right: 0, bottom: 0,
        background: '#fff', borderRadius: '28px 28px 0 0',
        padding: '12px 20px 32px',
      }}>
        <div style={{ width: 40, height: 4, background: '#E0E0E0', borderRadius: 999, margin: '4px auto 16px' }}/>
        <div style={{ fontSize: 18, fontWeight: 800, marginBottom: 4 }}>梗王换人格</div>
        <div style={{ fontSize: 12, color: '#888', marginBottom: 16 }}>选一个梗王版本来跟你唠</div>
        {Object.values(PERSONAS).map(p => (
          <button key={p.key} onClick={() => onPick(p)} style={{
            display: 'flex', alignItems: 'center', gap: 12,
            width: '100%', padding: '12px 14px',
            background: current.key === p.key ? '#F0EBFA' : '#F7F7F8',
            border: current.key === p.key ? '2px solid var(--purple)' : '2px solid transparent',
            borderRadius: 16, marginBottom: 8, textAlign: 'left',
          }}>
            <div style={{
              width: 40, height: 40, borderRadius: '50%',
              background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 22,
            }}>
              {p.key === 'default' ? '👑' : p.key === 'dialect' ? '🧊' : '📜'}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 15, fontWeight: 700 }}>{p.name}</div>
              <div style={{ fontSize: 12, color: '#888', marginTop: 2 }}>{p.subtitle}</div>
            </div>
            {current.key === p.key && <span style={{ color: 'var(--purple)', fontSize: 18 }}>✓</span>}
          </button>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, { MemeKingHome });
