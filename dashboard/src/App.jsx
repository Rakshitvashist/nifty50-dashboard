import React, { useState, useEffect, useRef } from 'react';
import { createChart, ColorType } from 'lightweight-charts';
import { motion, AnimatePresence } from 'framer-motion';
import { TrendingUp, TrendingDown, Activity, Shield, Zap, Info } from 'lucide-react';

const App = () => {
  const [data, setData] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [loading, setLoading] = useState(true);
  const chartContainerRef = useRef();
  const chartRef = useRef();

  useEffect(() => {
    fetch('summary.json')
      .then(res => res.json())
      .then(json => {
        setData(json);
        setSelectedStock(json[0]);
        setLoading(false);
      })
      .catch(err => console.error("Error loading data:", err));
  }, []);

  useEffect(() => {
    if (!selectedStock || !chartContainerRef.current) return;

    let chart = chartRef.current;
    let series = chartContainerRef.current.series;

    // Initialize chart only once
    if (!chart) {
      chart = createChart(chartContainerRef.current, {
        layout: {
          background: { type: ColorType.Solid, color: 'transparent' },
          textColor: '#a0a0a0',
          fontFamily: 'Outfit, sans-serif',
        },
        grid: {
          vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
          horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
        },
        width: chartContainerRef.current.clientWidth,
        height: chartContainerRef.current.clientHeight,
        timeScale: {
          borderColor: 'rgba(255, 255, 255, 0.1)',
        },
      });

      series = chart.addCandlestickSeries({
        upColor: '#10b981',
        downColor: '#f43f5e',
        borderVisible: false,
        wickUpColor: '#10b981',
        wickDownColor: '#f43f5e',
      });

      chartRef.current = chart;
      chartContainerRef.current.series = series;

      const handleResize = () => {
        if (chartContainerRef.current) {
          chart.applyOptions({ width: chartContainerRef.current.clientWidth });
        }
      };
      window.addEventListener('resize', handleResize);
    }

    const formattedData = selectedStock.history.map(item => ({
      time: item.time,
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close,
    }));

    // Update data without destroying the chart
    series.setData(formattedData);
    chart.timeScale().fitContent();

  }, [selectedStock]);

  if (loading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-black">
        <motion.div 
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
          className="w-8 h-8 border-2 border-gold rounded-full border-t-transparent"
        />
      </div>
    );
  }

  const getConsensusClass = (val) => {
    if (val > 0.2) return 'buy';
    if (val < -0.2) return 'sell';
    return 'neutral';
  };

  const getConsensusLabel = (val) => {
    if (val > 0.5) return 'Strong Buy';
    if (val > 0.2) return 'Buy';
    if (val < -0.5) return 'Strong Sell';
    if (val < -0.2) return 'Sell';
    return 'Neutral';
  };

  return (
    <div className="flex w-full h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1>NIFTY 50 INSIGHTS</h1>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Institutional Grade Analytics</p>
        </div>
        <div className="stock-list">
          {data.map(stock => (
            <motion.div
              key={stock.symbol}
              whileHover={{ x: 4 }}
              onClick={() => setSelectedStock(stock)}
              className={`stock-item ${selectedStock?.symbol === stock.symbol ? 'active' : ''}`}
            >
              <div className="flex justify-between items-center">
                <span className="symbol">{stock.symbol}</span>
                <span className={`consensus ${getConsensusClass(stock.consensus)}`}>
                  {getConsensusLabel(stock.consensus)}
                </span>
              </div>
              <div className="flex justify-between items-center mt-1" style={{ fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>{stock.price.toFixed(2)}</span>
                <span style={{ color: stock.change >= 0 ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                  {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)}
                </span>
              </div>
            </motion.div>
          ))}
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <motion.div
          initial={{ opacity: 0.5, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="w-full flex flex-col gap-6"
        >
            {/* Header Stats */}
            <div className="header-stats">
              <div className="glass-panel stat-card">
                <div className="stat-label flex items-center gap-2"><Activity size={14} /> Last Price</div>
                <div className="stat-value">₹{selectedStock?.price.toLocaleString()}</div>
              </div>
              <div className="glass-panel stat-card">
                <div className="stat-label flex items-center gap-2"><Zap size={14} /> RSI (14)</div>
                <div className="stat-value" style={{ color: selectedStock?.indicators.rsi > 70 ? 'var(--accent-rose)' : selectedStock?.indicators.rsi < 30 ? 'var(--accent-emerald)' : 'inherit' }}>
                  {selectedStock?.indicators.rsi.toFixed(1)}
                </div>
              </div>
              <div className="glass-panel stat-card">
                <div className="stat-label flex items-center gap-2"><Shield size={14} /> Consensus</div>
                <div className={`stat-value consensus ${getConsensusClass(selectedStock?.consensus)}`} style={{ background: 'transparent', padding: 0, fontSize: '1.25rem' }}>
                  {getConsensusLabel(selectedStock?.consensus)}
                </div>
              </div>
              <div className="glass-panel stat-card">
                <div className="stat-label flex items-center gap-2"><Info size={14} /> Industry</div>
                <div className="stat-value" style={{ fontSize: '1.1rem' }}>{selectedStock?.industry}</div>
              </div>
            </div>

            {/* Chart Area */}
            <div className="glass-panel chart-container p-4" style={{ height: '500px' }}>
              <div className="flex justify-between items-center mb-4">
                <span style={{ fontWeight: 600, color: 'var(--accent-gold)' }}>Historical performance (100 Days)</span>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>OHLC Candlestick Engine</span>
              </div>
              <div ref={chartContainerRef} style={{ width: '100%', height: 'calc(100% - 40px)' }} />
            </div>

            {/* Indicator Details */}
            <div className="indicator-grid">
               <div className="glass-panel p-6 flex flex-col items-center justify-center gap-2">
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Trend Direction</span>
                  {selectedStock?.consensus > 0 ? <TrendingUp color="#10b981" size={32} /> : <TrendingDown color="#f43f5e" size={32} />}
                  <span style={{ fontWeight: 600 }}>{selectedStock?.consensus > 0 ? 'Bullish' : 'Bearish'}</span>
               </div>
               <div className="glass-panel p-6 flex flex-col items-center justify-center gap-2">
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>MACD Histogram</span>
                  <div style={{ height: '40px', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <div style={{ 
                      width: '60%', 
                      height: '8px', 
                      background: 'rgba(255,255,255,0.1)', 
                      borderRadius: '4px',
                      position: 'relative'
                    }}>
                      <div style={{ 
                        position: 'absolute',
                        left: '50%',
                        width: Math.abs(selectedStock?.indicators.macd * 10) + '%',
                        height: '100%',
                        background: selectedStock?.indicators.macd > 0 ? 'var(--accent-emerald)' : 'var(--accent-rose)',
                        transform: selectedStock?.indicators.macd > 0 ? '' : 'translateX(-100%)',
                        borderRadius: '4px'
                      }} />
                    </div>
                  </div>
                  <span style={{ fontWeight: 600 }}>{selectedStock?.indicators.macd.toFixed(4)}</span>
               </div>
            </div>
          </motion.div>
      </main>
      
      <style>{`
        .flex { display: flex; }
        .flex-col { flex-direction: column; }
        .justify-between { justify-content: space-between; }
        .items-center { align-items: center; }
        .gap-2 { gap: 8px; }
        .gap-6 { gap: 24px; }
        .p-4 { padding: 16px; }
        .p-6 { padding: 24px; }
        .mt-1 { margin-top: 4px; }
        .mb-4 { margin-bottom: 16px; }
        .w-full { width: 100%; }
        .h-screen { height: 100vh; }
        .overflow-hidden { overflow: hidden; }
      `}</style>
    </div>
  );
};

export default App;
