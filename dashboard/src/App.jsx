import React, { useState, useEffect, useRef } from 'react';
import { createChart, ColorType } from 'lightweight-charts';
import { motion } from 'framer-motion';
import {
  TrendingUp, TrendingDown, Activity, Shield, Zap, Info,
  Target, BarChart2, Percent, AlertTriangle
} from 'lucide-react';

// ── helpers ──────────────────────────────────────────────────────────────────
const fmt = (n, d = 2) => (typeof n === 'number' ? n.toFixed(d) : '—');
const pct  = (n)        => fmt(n * 100, 1) + '%';

const consensusClass = (v) => v > 0.2 ? 'buy' : v < -0.2 ? 'sell' : 'neutral';
const consensusLabel = (v) => {
  if (v > 0.5) return 'Strong Buy';
  if (v > 0.2) return 'Buy';
  if (v < -0.5) return 'Strong Sell';
  if (v < -0.2) return 'Sell';
  return 'Neutral';
};
const signalColor  = (s) => s === 1 ? 'var(--accent-emerald)' : s === -1 ? 'var(--accent-rose)' : 'var(--text-secondary)';
const signalLabel  = (s) => s === 1 ? 'BUY' : s === -1 ? 'SELL' : 'HOLD';
const confColor    = (c) => c > 0.6 ? 'var(--accent-emerald)' : c > 0.3 ? 'var(--accent-gold)' : 'var(--text-secondary)';

// ── sub-components ────────────────────────────────────────────────────────────

/** Pill badge for indicator state */
const Pill = ({ label, color }) => (
  <span className="pill" style={{ background: `${color}22`, color }}>{label}</span>
);

/** Price-target row */
const TargetRow = ({ label, price, prob, color }) => (
  <div className="target-row">
    <span className="target-label" style={{ color }}>{label}</span>
    <span className="target-price">₹{fmt(price, 0)}</span>
    <span className="target-prob">{pct(prob)} prob</span>
    <div className="target-bar-wrap">
      <div className="target-bar" style={{ width: pct(prob), background: color }} />
    </div>
  </div>
);

/** Hit-ratio ring-like display */
const HitRing = ({ label, value }) => {
  const pctVal = Math.round(value * 100);
  const color  = pctVal >= 60 ? 'var(--accent-emerald)' : pctVal >= 50 ? 'var(--accent-gold)' : 'var(--accent-rose)';
  return (
    <div className="hit-ring">
      <div className="hit-ring-value" style={{ color }}>{pctVal}%</div>
      <div className="hit-ring-label">{label}</div>
    </div>
  );
};

// ── main ──────────────────────────────────────────────────────────────────────
const App = () => {
  const [data, setData]                 = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [loading, setLoading]           = useState(true);
  const [indexType, setIndexType]       = useState('50'); // '50' or '500'
  const chartContainerRef               = useRef();
  const chartRef                        = useRef();

  useEffect(() => {
    setLoading(true);
    const fileName = indexType === '50' ? 'summary.json' : 'summary_500.json';
    fetch(fileName)
      .then(r => r.json())
      .then(json => { 
        setData(json); 
        setSelectedStock(json[0]); 
        setLoading(false); 
      })
      .catch(err => {
        console.error('Error loading data:', err);
        setLoading(false);
      });
  }, [indexType]);

  // ── chart ──────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!selectedStock || !chartContainerRef.current) return;
    let chart  = chartRef.current;
    let series = chartContainerRef.current._series;

    if (!chart) {
      chart = createChart(chartContainerRef.current, {
        layout: { background: { type: ColorType.Solid, color: 'transparent' }, textColor: '#a0a0a0', fontFamily: 'Outfit, sans-serif' },
        grid:   { vertLines: { color: 'rgba(255,255,255,0.05)' }, horzLines: { color: 'rgba(255,255,255,0.05)' } },
        width:  chartContainerRef.current.clientWidth,
        height: chartContainerRef.current.clientHeight,
        timeScale: { borderColor: 'rgba(255,255,255,0.1)' },
      });
      series = chart.addCandlestickSeries({
        upColor: '#10b981', downColor: '#f43f5e', borderVisible: false,
        wickUpColor: '#10b981', wickDownColor: '#f43f5e',
      });
      chartRef.current = chart;
      chartContainerRef.current._series = series;
      window.addEventListener('resize', () => chart.applyOptions({ width: chartContainerRef.current?.clientWidth }));
    }

    series.setData(selectedStock.history.map(d => ({
      time: d.time, open: d.open, high: d.high, low: d.low, close: d.close,
    })));
    chart.timeScale().fitContent();
  }, [selectedStock]);

  if (loading) return (
    <div style={{ display:'flex', height:'100vh', alignItems:'center', justifyContent:'center', background:'#0a0a0a' }}>
      <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
        style={{ width:32, height:32, border:'2px solid #d4af37', borderTopColor:'transparent', borderRadius:'50%' }} />
    </div>
  );

  const s  = selectedStock;
  const pr = s?.prediction  || {};
  const hr = s?.hit_ratio   || {};
  const ind = s?.indicators || {};

  // ── indicator cards config ─────────────────────────────────────────────────
  const indicatorCards = [
    { name: 'RSI (14)',       value: fmt(ind.rsi, 1),
      meaning: ind.rsi > 70 ? 'Overbought' : ind.rsi < 30 ? 'Oversold' : 'Neutral',
      color:   ind.rsi > 70 ? 'var(--accent-rose)' : ind.rsi < 30 ? 'var(--accent-emerald)' : 'var(--text-secondary)',
      desc: 'Measures momentum; >70 overbought, <30 oversold.' },

    { name: 'MACD Hist',      value: fmt(ind.macd, 3),
      meaning: ind.macd > 0 ? 'Bullish momentum' : 'Bearish momentum',
      color:   ind.macd > 0 ? 'var(--accent-emerald)' : 'var(--accent-rose)',
      desc: 'Histogram shows divergence between fast and slow EMA.' },

    { name: 'ADX (14)',       value: fmt(ind.adx, 1),
      meaning: ind.adx > 25 ? 'Strong trend' : 'Weak / no trend',
      color:   ind.adx > 25 ? 'var(--accent-gold)' : 'var(--text-secondary)',
      desc: 'Trend strength 0-100; >25 confirms directional move.' },

    { name: 'BB Position',   value: pct(ind.bb_pos),
      meaning: ind.bb_pos > 0.8 ? 'Near upper band' : ind.bb_pos < 0.2 ? 'Near lower band' : 'Mid-range',
      color:   ind.bb_pos > 0.8 ? 'var(--accent-rose)' : ind.bb_pos < 0.2 ? 'var(--accent-emerald)' : 'var(--text-secondary)',
      desc: 'Price position within Bollinger Bands (20,2). >80% = extended up.' },

    { name: 'ATR (14)',       value: `₹${fmt(ind.atr, 1)}`,
      meaning: ind.atr > ind.atr * 1.5 ? 'High volatility' : 'Normal volatility',
      color:   'var(--text-secondary)',
      desc: 'Average True Range — daily expected price swing in rupees.' },

    { name: 'SuperTrend',    value: ind.supertrend > 0 ? 'BUY' : 'SELL',
      meaning: ind.supertrend > 0 ? 'Price above band' : 'Price below band',
      color:   ind.supertrend > 0 ? 'var(--accent-emerald)' : 'var(--accent-rose)',
      desc: 'ATR-based trailing stop; flips on breakout/breakdown.' },

    { name: 'Volume Surge',  value: `${fmt(ind.volume_surge, 2)}x`,
      meaning: ind.volume_surge > 1.5 ? 'Unusual volume' : 'Normal volume',
      color:   ind.volume_surge > 1.5 ? 'var(--accent-gold)' : 'var(--text-secondary)',
      desc: 'Current volume vs 20-day average. >1.5× = institutional interest.' },

    { name: 'Z-Score',       value: fmt(ind.zscore, 2),
      meaning: Math.abs(ind.zscore) > 2 ? 'Statistically extreme' : 'Within normal range',
      color:   Math.abs(ind.zscore) > 2 ? 'var(--accent-rose)' : 'var(--text-secondary)',
      desc: 'Standard deviations from 20-day mean price. |z|>2 = mean-reversion alert.' },
  ];

  return (
    <div className="app-shell">
      {/* ── sidebar ────────────────────────────────────────────────────────── */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1>NIFTY {indexType} INSIGHTS</h1>
          <p style={{ fontSize:'0.75rem', color:'var(--text-secondary)', marginTop:4 }}>
            Institutional Grade Analytics
          </p>
        </div>
        
        <div className="index-tabs">
          <div 
            className={`index-tab ${indexType === '50' ? 'active' : ''}`}
            onClick={() => setIndexType('50')}
          >
            Nifty 50
          </div>
          <div 
            className={`index-tab ${indexType === '500' ? 'active' : ''}`}
            onClick={() => setIndexType('500')}
          >
            Nifty 500
          </div>
        </div>

        <div className="stock-list">
          {data.map(stock => (
            <motion.div
              key={stock.symbol}
              whileHover={{ x: 4 }}
              onClick={() => setSelectedStock(stock)}
              className={`stock-item ${s?.symbol === stock.symbol ? 'active' : ''}`}
            >
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                <span className="symbol">{stock.symbol}</span>
                <span className={`consensus ${consensusClass(stock.consensus)}`}>
                  {consensusLabel(stock.consensus)}
                </span>
              </div>
              <div style={{ display:'flex', justifyContent:'space-between', fontSize:'0.82rem', marginTop:4 }}>
                <span style={{ color:'var(--text-secondary)' }}>₹{fmt(stock.price)}</span>
                <span style={{ color: stock.change >= 0 ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                  {stock.change >= 0 ? '+' : ''}{fmt(stock.change)}
                </span>
              </div>
            </motion.div>
          ))}
        </div>
      </aside>

      {/* ── main ───────────────────────────────────────────────────────────── */}
      <main className="main-content">
        <motion.div initial={{ opacity:0, y:10 }} animate={{ opacity:1, y:0 }} transition={{ duration:0.3 }}
          style={{ display:'flex', flexDirection:'column', gap:24, width:'100%' }}>

          {/* header stats */}
          <div className="header-stats">
            <div className="glass-panel stat-card">
              <div className="stat-label"><Activity size={14} style={{ display:'inline', marginRight:6 }} />Last Price</div>
              <div className="stat-value">₹{s?.price?.toLocaleString()}</div>
              <div style={{ fontSize:'0.8rem', marginTop:4, color: s?.change >= 0 ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                {s?.change >= 0 ? '▲' : '▼'} {fmt(Math.abs(s?.change))}
              </div>
            </div>
            <div className="glass-panel stat-card">
              <div className="stat-label"><Zap size={14} style={{ display:'inline', marginRight:6 }} />RSI (14)</div>
              <div className="stat-value" style={{ color: ind.rsi > 70 ? 'var(--accent-rose)' : ind.rsi < 30 ? 'var(--accent-emerald)' : 'inherit' }}>
                {fmt(ind.rsi, 1)}
              </div>
              <div style={{ fontSize:'0.78rem', color:'var(--text-secondary)', marginTop:4 }}>
                {ind.rsi > 70 ? 'Overbought zone' : ind.rsi < 30 ? 'Oversold zone' : 'Neutral zone'}
              </div>
            </div>
            <div className="glass-panel stat-card">
              <div className="stat-label"><Shield size={14} style={{ display:'inline', marginRight:6 }} />Consensus</div>
              <div className={`stat-value consensus ${consensusClass(s?.consensus)}`} style={{ background:'transparent', padding:0, fontSize:'1.25rem' }}>
                {consensusLabel(s?.consensus)}
              </div>
              <div style={{ fontSize:'0.78rem', color:'var(--text-secondary)', marginTop:4 }}>
                Score: {fmt(s?.consensus, 3)}
              </div>
            </div>
            <div className="glass-panel stat-card">
              <div className="stat-label"><Info size={14} style={{ display:'inline', marginRight:6 }} />Industry</div>
              <div className="stat-value" style={{ fontSize:'1rem' }}>{s?.industry}</div>
              <div style={{ fontSize:'0.78rem', color:'var(--text-secondary)', marginTop:4 }}>{s?.company}</div>
            </div>
          </div>

          {/* candlestick chart */}
          <div className="glass-panel p-4" style={{ height:480 }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:12 }}>
              <span style={{ fontWeight:600, color:'var(--accent-gold)' }}>Historical Performance — 100 Days</span>
              <span style={{ fontSize:'0.82rem', color:'var(--text-secondary)' }}>OHLC Candlestick</span>
            </div>
            <div ref={chartContainerRef} style={{ width:'100%', height:'calc(100% - 40px)' }} />
          </div>

          {/* ── Consensus Prediction Panel ──────────────────────────────────── */}
          <div className="glass-panel p-6">
            <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:20 }}>
              <Target size={20} color="var(--accent-gold)" />
              <h2 style={{ margin:0, fontSize:'1.15rem', fontWeight:700 }}>Consensus Prediction</h2>
              <span style={{ marginLeft:'auto', fontSize:'0.78rem', color:'var(--text-secondary)' }}>
                Weighted vote of 400+ indicators
              </span>
            </div>

            <div className="prediction-grid">
              {/* ── signal block ── */}
              <div className="pred-signal-block glass-panel">
                <div style={{ fontSize:'0.8rem', color:'var(--text-secondary)', marginBottom:8 }}>Signal</div>
                <div style={{ fontSize:'2.8rem', fontWeight:800, color: signalColor(pr.signal), lineHeight:1 }}>
                  {signalLabel(pr.signal)}
                </div>
                <div style={{ fontSize:'0.85rem', color: confColor(pr.confidence), marginTop:8 }}>
                  {pr.confidence_level?.toUpperCase()} confidence · {fmt(pr.confidence * 100, 1)}%
                </div>

                {/* bullish/bearish bar */}
                <div style={{ marginTop:16 }}>
                  <div style={{ display:'flex', justifyContent:'space-between', fontSize:'0.75rem', marginBottom:4 }}>
                    <span style={{ color:'var(--accent-emerald)' }}>▲ Bullish {fmt(pr.bullish_pct, 1)}%</span>
                    <span style={{ color:'var(--accent-rose)'    }}>▼ Bearish {fmt(pr.bearish_pct, 1)}%</span>
                  </div>
                  <div className="consensus-bar-track">
                    <div className="consensus-bar-fill" style={{ width: `${pr.bullish_pct}%` }} />
                  </div>
                </div>

                <div style={{ marginTop:12, fontSize:'0.78rem', color:'var(--text-secondary)' }}>
                  Expected move: ±{fmt(pr.expected_move_pct, 2)}%
                </div>
              </div>

              {/* ── price targets ── */}
              <div className="pred-targets-block glass-panel">
                <div style={{ fontSize:'0.8rem', color:'var(--text-secondary)', marginBottom:12 }}>
                  {pr.direction === 'LONG' ? '📈 Long Targets' : '📉 Short Targets'}
                </div>
                <TargetRow label="T1"   price={pr.target_1}  prob={pr.prob_target_1} color="var(--accent-emerald)" />
                <TargetRow label="T2"   price={pr.target_2}  prob={pr.prob_target_2} color="var(--accent-gold)"    />
                <TargetRow label="T3"   price={pr.target_3}  prob={pr.prob_target_3} color="var(--accent-rose)"    />
                <div className="stop-loss-row">
                  <AlertTriangle size={14} color="var(--accent-rose)" />
                  <span>Stop Loss</span>
                  <span style={{ color:'var(--accent-rose)', fontWeight:700 }}>₹{fmt(pr.stop_loss, 0)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* ── Hit Ratio Backtester ────────────────────────────────────────── */}
          <div className="glass-panel p-6">
            <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:20 }}>
              <BarChart2 size={20} color="var(--accent-gold)" />
              <h2 style={{ margin:0, fontSize:'1.15rem', fontWeight:700 }}>Hit Ratio Backtester</h2>
              <span style={{ marginLeft:'auto', fontSize:'0.78rem', color:'var(--text-secondary)' }}>
                Historical prediction accuracy
              </span>
            </div>

            <div className="hit-ratio-grid">
              <HitRing label="5-Day Overall"   value={hr.overall_5d  ?? 0.5} />
              <HitRing label="10-Day Overall"  value={hr.overall_10d ?? 0.5} />
              <HitRing label="High Conf 5D"    value={hr.high_conf_5d ?? 0.5} />
              <HitRing label="Buy Hit Rate"    value={hr.buy_hit_5d  ?? 0.5} />
              <HitRing label="Sell Hit Rate"   value={hr.sell_hit_5d ?? 0.5} />

              {/* stats summary */}
              <div className="hit-ring">
                <div className="hit-ring-value" style={{ fontSize:'1.1rem', color:'var(--accent-gold)' }}>
                  {hr.win_count_5d}/{hr.signal_count_5d}
                </div>
                <div className="hit-ring-label">Wins / Signals</div>
              </div>
            </div>

            {/* ── Target Analytics (New) ── */}
            <div style={{ marginTop: 24, borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: 20 }}>
              <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                <Target size={14} color="var(--accent-gold)" /> Target vs SL Analytics (10-Day Window)
              </div>
              <div className="target-analytics-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 16 }}>
                <div className="target-stat-card glass-panel" style={{ padding: '12px', textAlign: 'center' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: 4 }}>Target 1 Hits</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--accent-emerald)' }}>{pct(hr.t1_hit_rate)}</div>
                  <div className="mini-progress" style={{ height: 4, background: 'rgba(255,255,255,0.05)', borderRadius: 2, marginTop: 8 }}>
                    <div style={{ height: '100%', width: pct(hr.t1_hit_rate), background: 'var(--accent-emerald)', borderRadius: 2 }} />
                  </div>
                </div>
                <div className="target-stat-card glass-panel" style={{ padding: '12px', textAlign: 'center' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: 4 }}>Target 2 Hits</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--accent-gold)' }}>{pct(hr.t2_hit_rate)}</div>
                  <div className="mini-progress" style={{ height: 4, background: 'rgba(255,255,255,0.05)', borderRadius: 2, marginTop: 8 }}>
                    <div style={{ height: '100%', width: pct(hr.t2_hit_rate), background: 'var(--accent-gold)', borderRadius: 2 }} />
                  </div>
                </div>
                <div className="target-stat-card glass-panel" style={{ padding: '12px', textAlign: 'center' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: 4 }}>Target 3 Hits</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--accent-rose)' }}>{pct(hr.t3_hit_rate)}</div>
                  <div className="mini-progress" style={{ height: 4, background: 'rgba(255,255,255,0.05)', borderRadius: 2, marginTop: 8 }}>
                    <div style={{ height: '100%', width: pct(hr.t3_hit_rate), background: 'var(--accent-rose)', borderRadius: 2 }} />
                  </div>
                </div>
                <div className="target-stat-card glass-panel" style={{ padding: '12px', textAlign: 'center', border: '1px solid rgba(244, 63, 94, 0.2)' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: 4 }}>SL Hit Rate</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--accent-rose)' }}>{pct(hr.sl_hit_rate)}</div>
                  <div className="mini-progress" style={{ height: 4, background: 'rgba(255,255,255,0.05)', borderRadius: 2, marginTop: 8 }}>
                    <div style={{ height: '100%', width: pct(hr.sl_hit_rate), background: 'var(--accent-rose)', borderRadius: 2 }} />
                  </div>
                </div>
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: 12, fontStyle: 'italic' }}>
                * Analyzed {hr.total_signals} historical signals for {s?.symbol}. Target hit rates measured before SL hit.
              </div>
            </div>

            <div style={{ marginTop:16, padding:'12px 16px', background:'rgba(255,255,255,0.02)', borderRadius:10, fontSize:'0.82rem', color:'var(--text-secondary)' }}>
              Avg directional return on signal:&nbsp;
              <span style={{ color: hr.avg_directional_return >= 0 ? 'var(--accent-emerald)' : 'var(--accent-rose)', fontWeight:700 }}>
                {hr.avg_directional_return >= 0 ? '+' : ''}{fmt(hr.avg_directional_return, 3)}%
              </span>
            </div>
          </div>

          {/* ── Technical Indicator Analysis ────────────────────────────────── */}
          <div className="glass-panel p-6">
            <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:20 }}>
              <Percent size={20} color="var(--accent-gold)" />
              <h2 style={{ margin:0, fontSize:'1.15rem', fontWeight:700 }}>Technical Indicator Analysis</h2>
            </div>
            <div className="indicator-details-grid">
              {indicatorCards.map((ind, i) => (
                <motion.div key={ind.name}
                  initial={{ opacity:0, y:10 }} animate={{ opacity:1, y:0 }}
                  transition={{ delay: i * 0.04 }}
                  className="indicator-card"
                >
                  <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:4 }}>
                    <span className="ind-name">{ind.name}</span>
                    <Pill label={ind.meaning} color={ind.color} />
                  </div>
                  <div className="ind-value">{ind.value}</div>
                  <p className="ind-desc">{ind.desc}</p>
                </motion.div>
              ))}
            </div>
          </div>

        </motion.div>
      </main>
    </div>
  );
};

export default App;
