// ------------- Meme Generator (梗图生成) -------------

function Generator({ onPointGain, goBack }) {
  const [mode, setMode] = React.useState('text'); // text | template | image
  const [input, setInput] = React.useState('');
  const [style, setStyle] = React.useState('yy');
  const [generating, setGenerating] = React.useState(false);
  const [results, setResults] = React.useState([]);
  const [activeIdx, setActiveIdx] = React.useState(0);
  const [selectedTpl, setSelectedTpl] = React.useState(GEN_TEMPLATES[0]);

  async function generate() {
    if (!input.trim()) return;
    setGenerating(true);
    setResults([]);

    let lines = [];
    try {
      const styleMap = { cold: '冷漠系（像话都懒得说）', crazy: '癫狂系（发疯文学）', yy: '阴阳系（阴阳怪气）', cute: '可爱系（软萌撒娇）' };
      const prompt = `用户的吐槽是：「${input}」
请生成3个不同的梗图文案（风格：${styleMap[style]}）。每个文案最多15字，可用emoji。
只输出3行，不要编号，不要解释：`;
      const r = await window.claude.complete(prompt);
      lines = (r || '').split('\n').map(l => l.trim().replace(/^[-·0-9.、)】"]+\s*/, '').replace(/["]/g, '')).filter(Boolean).slice(0, 3);
    } catch (e) {}
    if (lines.length < 3) lines = ['那咋了 🫠', '班味浓郁 建议冷冻', '家人们 谁懂啊 💀'];

    // fake progressive load
    await new Promise(r => setTimeout(r, 300));
    const picked = [...GEN_TEMPLATES].sort(() => Math.random() - 0.5).slice(0, 3);
    setResults(lines.slice(0, 3).map((text, i) => ({ text, template: picked[i] })));
    setActiveIdx(0);
    setGenerating(false);
    onPointGain(15);
  }

  const modes = [
    { key: 'text', label: '一句话生梗', icon: '✍️' },
    { key: 'template', label: '模板填空', icon: '🧩' },
    { key: 'image', label: '图片改梗', icon: '🖼️' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#FAFAFB' }}>
      <div style={{ padding: '8px 20px 4px', display: 'flex', alignItems: 'center', gap: 10 }}>
        <button onClick={goBack} style={{
          width: 36, height: 36, borderRadius: '50%', background: '#F0F0F0',
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16,
        }}>‹</button>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 22, fontWeight: 800, lineHeight: 1.1 }}>造梗 ✨</div>
          <div style={{ fontSize: 11, color: '#888', marginTop: 2 }}>一句话，出梗图</div>
        </div>
      </div>

      {/* mode tabs */}
      <div style={{ display: 'flex', gap: 8, padding: '10px 16px 6px' }}>
        {modes.map(m => (
          <button key={m.key} onClick={() => setMode(m.key)} style={{
            flex: 1, padding: '8px 4px', fontSize: 12, fontWeight: 600,
            borderRadius: 12,
            background: mode === m.key ? '#1A1A1A' : '#F0F0F0',
            color: mode === m.key ? '#fff' : '#666',
            transition: 'all 0.2s',
          }}>{m.icon} {m.label}</button>
        ))}
      </div>

      <div className="no-scroll" style={{ flex: 1, overflowY: 'auto', padding: '8px 16px 20px' }}>
        {mode === 'text' && (
          <>
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="老板周五晚上6点在群里说加班…"
              style={{
                width: '100%', minHeight: 80, padding: 14,
                border: '2px solid #EDEDED', borderRadius: 16,
                fontSize: 14, fontFamily: 'inherit', outline: 'none',
                resize: 'none', lineHeight: 1.5,
              }}
            />
            <div style={{ fontSize: 11, color: '#888', margin: '10px 2px 6px', fontWeight: 600 }}>选个风格</div>
            <div className="no-scroll" style={{ display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 4 }}>
              {GEN_STYLES.map(s => (
                <button key={s.key} onClick={() => setStyle(s.key)} style={{
                  flexShrink: 0, padding: '7px 14px', borderRadius: 999, fontSize: 12, fontWeight: 600,
                  background: style === s.key ? '#1A1A1A' : '#F0F0F0',
                  color: style === s.key ? '#fff' : '#666',
                }}>{s.label}</button>
              ))}
            </div>

            {/* generate button */}
            <button onClick={generate} disabled={!input.trim() || generating} style={{
              width: '100%', padding: '14px', marginTop: 16,
              borderRadius: 16, fontSize: 15, fontWeight: 800,
              background: input.trim() && !generating
                ? 'linear-gradient(135deg, #7B5EA7, #5A3E8A)' : '#DDD',
              color: '#fff',
              boxShadow: input.trim() && !generating ? 'var(--shadow-purple)' : 'none',
            }}>
              {generating ? '梗图出炉中…' : '✨ 生成梗图'}
            </button>

            {/* results */}
            {generating && <GenSkeleton/>}
            {results.length > 0 && !generating && (
              <GenResults results={results} activeIdx={activeIdx} setActiveIdx={setActiveIdx}
                          originalInput={input} onRegen={generate}/>
            )}
          </>
        )}

        {mode === 'template' && (
          <TemplateMode selectedTpl={selectedTpl} setSelectedTpl={setSelectedTpl} onGen={generate}
                        input={input} setInput={setInput} generating={generating}
                        results={results} activeIdx={activeIdx} setActiveIdx={setActiveIdx}/>
        )}

        {mode === 'image' && (
          <ImageMode/>
        )}
      </div>
    </div>
  );
}

function GenSkeleton() {
  return (
    <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
      <div style={{ fontSize: 13, color: 'var(--purple)', fontWeight: 700 }}>
        <span className="bob" style={{ display: 'inline-block' }}>✨</span> 梗王画梗中…
      </div>
      <div className="skeleton" style={{ width: '80%', aspectRatio: '1/1', borderRadius: 16 }}/>
      <div className="skeleton" style={{ width: '60%', height: 12, borderRadius: 6 }}/>
    </div>
  );
}

function GenResults({ results, activeIdx, setActiveIdx, originalInput, onRegen }) {
  const cur = results[activeIdx];
  return (
    <div style={{ marginTop: 16 }}>
      <div style={{ fontSize: 12, color: '#888', marginBottom: 8, display: 'flex', justifyContent: 'space-between' }}>
        <span>左右滑查看 ({activeIdx + 1}/{results.length})</span>
        <button onClick={onRegen} style={{ color: 'var(--purple)', fontSize: 12, fontWeight: 700 }}>
          🎲 再抽一组
        </button>
      </div>
      <div className="pop-in" style={{
        background: '#fff', borderRadius: 20, padding: 12,
        boxShadow: 'var(--shadow-card)',
      }}>
        <div style={{ position: 'relative', borderRadius: 12, overflow: 'hidden' }}>
          <MemePlaceholder label={`${cur.template.name}\n${cur.template.emoji}`} aspect="1/1" />
          <div style={{
            position: 'absolute', left: 0, right: 0, bottom: 0,
            padding: '20px 16px 14px',
            background: 'linear-gradient(transparent, rgba(0,0,0,0.7))',
            color: '#fff', fontSize: 18, fontWeight: 800,
            textAlign: 'center', textShadow: '0 2px 6px rgba(0,0,0,0.5)',
            lineHeight: 1.3,
          }}>{cur.text}</div>
          <div style={{
            position: 'absolute', top: 8, right: 8,
            background: 'rgba(0,0,0,0.6)', color: '#fff',
            fontSize: 10, padding: '3px 8px', borderRadius: 999,
            fontWeight: 600,
          }}>造梗局·段位水印</div>
        </div>
      </div>

      {/* pagination dots */}
      <div style={{ display: 'flex', gap: 6, justifyContent: 'center', marginTop: 10 }}>
        {results.map((_, i) => (
          <button key={i} onClick={() => setActiveIdx(i)} style={{
            width: i === activeIdx ? 24 : 8, height: 8, borderRadius: 999,
            background: i === activeIdx ? 'var(--purple)' : '#DDD',
            transition: 'all 0.2s',
          }}/>
        ))}
      </div>

      {/* thumbnails */}
      <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
        {results.map((r, i) => (
          <button key={i} onClick={() => setActiveIdx(i)} style={{
            flex: 1, padding: 8, borderRadius: 12,
            background: '#fff',
            border: i === activeIdx ? '2px solid var(--purple)' : '2px solid #EEE',
            fontSize: 11, lineHeight: 1.3, textAlign: 'left',
            color: '#444', fontWeight: 500,
          }}>
            <div style={{ fontSize: 18, marginBottom: 4 }}>{r.template.emoji}</div>
            {r.text.slice(0, 14)}{r.text.length > 14 ? '…' : ''}
          </button>
        ))}
      </div>

      {/* CTAs */}
      <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
        <ExitBtn icon="🚀" label="发到广场" accent="red"/>
        <ExitBtn icon="💬" label="给梗王看" accent="purple"/>
        <ExitBtn icon="📥" label="保存/分享" accent="blue"/>
      </div>
    </div>
  );
}

function ExitBtn({ icon, label, accent }) {
  const colors = { red: 'var(--red)', purple: 'var(--purple)', blue: 'var(--blue)' };
  return (
    <button style={{
      flex: 1, padding: '12px 6px',
      background: '#fff', borderRadius: 14,
      border: '1px solid #EEE',
      fontSize: 12, fontWeight: 700, color: colors[accent],
      display: 'flex', flexDirection: 'column', gap: 4,
      alignItems: 'center',
    }}>
      <span style={{ fontSize: 20 }}>{icon}</span>
      {label}
    </button>
  );
}

function TemplateMode({ selectedTpl, setSelectedTpl, onGen, input, setInput, generating, results, activeIdx, setActiveIdx }) {
  return (
    <>
      <div style={{ fontSize: 11, color: '#888', margin: '2px 2px 8px', fontWeight: 600 }}>选一个模板</div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
        {GEN_TEMPLATES.map(t => (
          <button key={t.name} onClick={() => setSelectedTpl(t)} className={selectedTpl.name === t.name ? 'grad-border' : ''} style={{
            padding: 10, borderRadius: 14,
            background: '#fff',
            border: selectedTpl.name === t.name ? 'none' : '1px solid #EEE',
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4,
          }}>
            <div style={{ fontSize: 26 }}>{t.emoji}</div>
            <div style={{ fontSize: 11, fontWeight: 600 }}>{t.name}</div>
          </button>
        ))}
      </div>
      <div style={{ fontSize: 11, color: '#888', margin: '14px 2px 6px', fontWeight: 600 }}>描述下场景，AI自动填词</div>
      <textarea
        value={input}
        onChange={e => setInput(e.target.value)}
        placeholder={`用 ${selectedTpl.name} 做一个关于…`}
        style={{
          width: '100%', minHeight: 70, padding: 12,
          border: '2px solid #EDEDED', borderRadius: 14,
          fontSize: 13, fontFamily: 'inherit', outline: 'none', resize: 'none',
        }}
      />
      <button onClick={onGen} disabled={!input.trim() || generating} style={{
        width: '100%', padding: 14, marginTop: 12,
        borderRadius: 14, fontSize: 14, fontWeight: 800,
        background: input.trim() && !generating
          ? 'linear-gradient(135deg, #4A8FE7, #2E6FCC)' : '#DDD',
        color: '#fff',
      }}>{generating ? '生成中…' : '✨ 用这个模板生成'}</button>
      {generating && <GenSkeleton/>}
      {results.length > 0 && !generating && (
        <GenResults results={results} activeIdx={activeIdx} setActiveIdx={setActiveIdx} originalInput={input} onRegen={onGen}/>
      )}
    </>
  );
}

function ImageMode() {
  return (
    <div style={{
      border: '2px dashed #DDD', borderRadius: 16,
      padding: '40px 20px', textAlign: 'center',
      background: '#fff',
    }}>
      <div style={{ fontSize: 48, marginBottom: 10 }}>📤</div>
      <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 4 }}>上传照片，AI改成梗图</div>
      <div style={{ fontSize: 12, color: '#888', marginBottom: 16, lineHeight: 1.5 }}>
        识别图里的元素和情绪，推荐梗文案
      </div>
      <button style={{
        padding: '10px 24px', borderRadius: 999,
        background: '#1A1A1A', color: '#fff', fontSize: 13, fontWeight: 700,
      }}>从相册选图</button>
      <div style={{ fontSize: 11, color: '#AAA', marginTop: 16 }}>（demo：功能占位）</div>
    </div>
  );
}

Object.assign(window, { Generator });
