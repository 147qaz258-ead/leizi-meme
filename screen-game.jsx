// ------------- Game (梗游戏 - 填梗大师) -------------

function GameScreen({ onPointGain, points }) {
  const [view, setView] = React.useState('menu'); // menu | playing | result
  const [currentLevel, setCurrentLevel] = React.useState(0);
  const [answer, setAnswer] = React.useState('');
  const [timeLeft, setTimeLeft] = React.useState(30);
  const [scoring, setScoring] = React.useState(false);
  const [result, setResult] = React.useState(null);

  React.useEffect(() => {
    if (view !== 'playing' || scoring) return;
    if (timeLeft <= 0) { submit(); return; }
    const t = setTimeout(() => setTimeLeft(v => v - 1), 1000);
    return () => clearTimeout(t);
  }, [view, timeLeft, scoring]);

  function startGame() {
    setAnswer('');
    setTimeLeft(30);
    setResult(null);
    setView('playing');
  }

  async function submit() {
    if (scoring) return;
    setScoring(true);
    const level = GAME_LEVELS[currentLevel];
    const userAns = answer.trim() || '（没写完）';
    let parsed = { grade: 'B', humor: 70, contrast: 70, fit: 70, comment: '还行，下次更好' };
    try {
      const prompt = `梗游戏评分。情境：「${level.setup}」，图是：${level.imagePrompt}。
用户填的梗文案是：「${userAns}」
请评分。严格返回一行JSON，格式：{"grade":"A+/A/B/C","humor":0-100,"contrast":0-100,"fit":0-100,"comment":"一句中文点评，不超过20字"}
只输出JSON：`;
      const r = await window.claude.complete(prompt);
      const m = (r || '').match(/\{[\s\S]*\}/);
      if (m) parsed = JSON.parse(m[0]);
    } catch (e) {}
    setResult({ ...parsed, userAns });
    setScoring(false);
    setView('result');
    onPointGain(parsed.grade?.startsWith('A') ? 15 : 5);
  }

  if (view === 'playing') return <PlayingView level={GAME_LEVELS[currentLevel]} timeLeft={timeLeft} answer={answer}
                                               setAnswer={setAnswer} onSubmit={submit} scoring={scoring}/>;
  if (view === 'result') return <ResultView level={GAME_LEVELS[currentLevel]} result={result}
                                              onNext={() => { setCurrentLevel((currentLevel + 1) % GAME_LEVELS.length); startGame(); }}
                                              onBack={() => setView('menu')}/>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#FAFAFB' }}>
      <div style={{ padding: '8px 20px 4px' }}>
        <div style={{ fontSize: 28, fontWeight: 800 }}>游戏 🎮</div>
        <div style={{ fontSize: 12, color: '#888', marginTop: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{
            background: '#F5F0E4', color: '#8B6914', padding: '2px 8px', borderRadius: 999,
            fontSize: 11, fontWeight: 700,
          }}>🥇 黄金梗师</span>
          <span>梗值 <strong style={{ color: 'var(--amber)' }}>{points}</strong></span>
        </div>
      </div>

      {/* level progress heatmap */}
      <div style={{ padding: '12px 16px 8px' }}>
        <div className="grad-border amber" style={{ padding: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700 }}>本周造梗活跃度</div>
              <div style={{ fontSize: 11, color: '#888', marginTop: 2 }}>再练3关升级 💠 铂金梗将</div>
            </div>
            <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--amber)', fontFamily: 'var(--font-num)' }}>
              {points}<span style={{ fontSize: 11, color: '#888', marginLeft: 3 }}>梗值</span>
            </div>
          </div>
          <Heatmap/>
        </div>
      </div>

      {/* level cards */}
      <div style={{ padding: '8px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
        <GameCard accent="purple" icon="✍️" title="填梗大师" desc="给图填文案，AI三维度打分"
                  meta="30秒 · AI打分" onClick={startGame} primary/>
        <GameCard accent="red" icon="🐱" title="看图写梗" desc="给你一张潜力图，写出最骚的caption"
                  meta="30秒 · 众评模式"/>
        <GameCard accent="green" icon="🔗" title="梗接龙" desc="接下一棒，组成荒诞故事链"
                  meta="多人异步"/>
      </div>

      {/* rotating CTA */}
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0 0 20px' }}>
        <RotatingCTA text="开始挑战 · 开始挑战 · " centerEmoji="⚡" size={130} onClick={startGame}/>
      </div>
    </div>
  );
}

function Heatmap() {
  // 7 cols x 4 rows
  const cells = Array.from({ length: 28 }).map((_, i) => {
    const v = Math.random();
    let c = '#F0F0F0';
    if (v > 0.9) c = '#B85C00';
    else if (v > 0.75) c = '#E07B00';
    else if (v > 0.55) c = '#F5A623';
    else if (v > 0.35) c = '#FAD9B0';
    return c;
  });
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(14, 1fr)', gap: 3 }}>
      {cells.concat(cells).map((c, i) => (
        <div key={i} style={{ aspectRatio: '1', background: c, borderRadius: 4 }}/>
      ))}
    </div>
  );
}

function GameCard({ accent, icon, title, desc, meta, onClick, primary }) {
  const bgColors = {
    purple: '#EEE6FA', red: '#FDE6E4', green: '#DFF4E7',
  };
  return (
    <button onClick={onClick} className={`grad-border ${accent}`} style={{
      padding: '14px 16px', textAlign: 'left', display: 'flex', alignItems: 'center', gap: 12,
    }}>
      <div style={{
        width: 48, height: 48, borderRadius: '50%', background: bgColors[accent],
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 24, flexShrink: 0,
      }}>{icon}</div>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{ fontSize: 15, fontWeight: 700 }}>{title}</div>
          {primary && <span style={{ fontSize: 9, fontWeight: 700, color: '#fff', background: 'var(--red)', padding: '2px 6px', borderRadius: 999 }}>HOT</span>}
        </div>
        <div style={{ fontSize: 12, color: '#666', marginTop: 3 }}>{desc}</div>
        <div style={{ fontSize: 10, color: '#AAA', marginTop: 4 }}>{meta}</div>
      </div>
      <span style={{ color: '#BBB', fontSize: 20 }}>›</span>
    </button>
  );
}

function PlayingView({ level, timeLeft, answer, setAnswer, onSubmit, scoring }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#FAFAFB', padding: '10px 16px 16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
        <div style={{ fontSize: 14, fontWeight: 700 }}>✍️ 填梗大师 · 第 {level.id} 关</div>
        <div style={{
          fontSize: 20, fontWeight: 800, color: timeLeft <= 10 ? 'var(--red)' : 'var(--text-primary)',
          fontFamily: 'var(--font-num)',
        }}>⏱ {timeLeft}s</div>
      </div>

      {/* setup */}
      <div style={{
        background: 'linear-gradient(135deg, #FFF7E6, #FDE6D9)',
        padding: '12px 16px', borderRadius: 14,
        fontSize: 13, lineHeight: 1.5, marginBottom: 10,
      }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: '#8B6914', marginBottom: 4 }}>情境</div>
        {level.setup}
      </div>

      {/* meme image */}
      <div style={{ flex: 1, minHeight: 0, marginBottom: 10 }}>
        <div style={{ height: '100%', borderRadius: 16, overflow: 'hidden' }}>
          <MemePlaceholder label={level.imagePrompt + '\n（给图填一句文案）'} aspect="auto" bg="#F5F3EE"/>
        </div>
      </div>

      {/* input */}
      <textarea
        value={answer}
        onChange={e => setAnswer(e.target.value)}
        placeholder="你的梗文案…（15字内最佳）"
        maxLength={30}
        style={{
          width: '100%', padding: 12, border: '2px solid #EDEDED', borderRadius: 14,
          fontSize: 14, fontFamily: 'inherit', outline: 'none', resize: 'none',
          minHeight: 60,
        }}
      />
      <button onClick={onSubmit} disabled={scoring} style={{
        marginTop: 10, padding: '14px', borderRadius: 14,
        background: scoring ? '#DDD' : 'linear-gradient(135deg, #7B5EA7, #5A3E8A)',
        color: '#fff', fontSize: 15, fontWeight: 800,
        boxShadow: 'var(--shadow-purple)',
      }}>{scoring ? '梗王评审中…' : '提交给AI评审 🎯'}</button>
    </div>
  );
}

function ResultView({ level, result, onNext, onBack }) {
  if (!result) return null;
  const gradeColors = {
    'A+': { bg: 'linear-gradient(135deg, #FFD700, #FF6B6B)', fg: '#fff' },
    'A': { bg: 'linear-gradient(135deg, #52C17A, #2E9E59)', fg: '#fff' },
    'B': { bg: 'linear-gradient(135deg, #4A8FE7, #2E6FCC)', fg: '#fff' },
    'C': { bg: 'linear-gradient(135deg, #AAA, #777)', fg: '#fff' },
  };
  const gc = gradeColors[result.grade] || gradeColors.B;
  const isGood = result.grade?.startsWith('A');

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#FAFAFB', padding: '14px 16px' }}>
      <div style={{ textAlign: 'center', marginBottom: 10 }}>
        <div className="pop-in" style={{
          display: 'inline-block', background: gc.bg, color: gc.fg,
          padding: '12px 32px', borderRadius: 999,
          fontSize: 28, fontWeight: 900,
          boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
        }}>{result.grade}</div>
        <div style={{ fontSize: 14, fontWeight: 700, marginTop: 10 }}>
          {isGood ? '🎉 梗中梗！' : '🫠 这梗王还得练'}
        </div>
      </div>

      {/* user answer */}
      <div style={{ background: '#fff', borderRadius: 14, padding: 14, boxShadow: 'var(--shadow-card)', marginBottom: 10 }}>
        <div style={{ fontSize: 10, color: '#888', fontWeight: 700, marginBottom: 4 }}>你写的</div>
        <div style={{ fontSize: 15, fontWeight: 700 }}>{result.userAns}</div>
      </div>

      {/* scores */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginBottom: 10 }}>
        <ScoreBar label="幽默度" value={result.humor} color="var(--red)"/>
        <ScoreBar label="反差度" value={result.contrast} color="var(--blue)"/>
        <ScoreBar label="契合度" value={result.fit} color="var(--green)"/>
      </div>

      {/* comment */}
      <div style={{
        background: '#F0EBFA', borderRadius: 14, padding: 12,
        display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 10,
      }}>
        <div style={{ flexShrink: 0 }}>
          <DogeAvatar size={36} expression="smirk"/>
        </div>
        <div>
          <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--purple)' }}>梗王点评</div>
          <div style={{ fontSize: 13, marginTop: 3 }}>{result.comment}</div>
        </div>
      </div>

      {/* top answers */}
      <div style={{ fontSize: 11, fontWeight: 700, color: '#888', margin: '4px 0 8px' }}>本关 TOP 答案</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {level.topAnswers.map((a, i) => (
          <div key={i} style={{
            background: '#fff', borderRadius: 12, padding: '10px 12px',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            fontSize: 12,
          }}>
            <span>{a.text}</span>
            <span style={{ color: 'var(--green)', fontWeight: 700 }}>{a.score} · {a.votes}👍</span>
          </div>
        ))}
      </div>

      <div style={{ flex: 1 }}/>

      <div style={{ display: 'flex', gap: 8 }}>
        <button onClick={onBack} style={{
          flex: 1, padding: 12, borderRadius: 12, background: '#F0F0F0', fontSize: 13, fontWeight: 700,
        }}>返回</button>
        <button onClick={onNext} style={{
          flex: 2, padding: 12, borderRadius: 12,
          background: 'var(--purple)', color: '#fff', fontSize: 13, fontWeight: 700,
        }}>下一关 ›</button>
      </div>
    </div>
  );
}

function ScoreBar({ label, value, color }) {
  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: '10px 10px 8px' }}>
      <div style={{ fontSize: 10, color: '#888', fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: 20, fontWeight: 800, color, fontFamily: 'var(--font-num)', marginTop: 2 }}>{value}</div>
      <div style={{ height: 4, background: '#F0F0F0', borderRadius: 2, marginTop: 4, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${value}%`, background: color, borderRadius: 2, transition: 'width 0.6s' }}/>
      </div>
    </div>
  );
}

Object.assign(window, { GameScreen });
