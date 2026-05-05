from flask import Flask, request, jsonify, render_template_string
import os
import requests as req
import json

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")

SYSTEM_PROMPT = """You are an expert NLP and sentiment analysis engine. Analyze the given text and return ONLY a valid JSON object — no preamble, no explanation, no markdown.

If the input is unintelligible (random characters, gibberish, keyboard mashing, meaningless symbols), return:
{"error": "unintelligible", "message": "Input does not appear to be meaningful text."}

Otherwise, analyze and return this exact JSON structure:
{
  "valid": true,
  "sentiment": {
    "label": "Positive" | "Negative" | "Neutral" | "Mixed",
    "score": <float 0.0-1.0>,
    "summary": "<one sentence summary of overall sentiment>"
  },
  "emotions": [
    {"name": "<emotion>", "score": <float 0.0-1.0>, "present": <true|false>}
  ],
  "attitude": {
    "tone": "<primary tone e.g. Sarcastic, Aggressive, Passive, Assertive, Empathetic, Formal, Casual, Hostile, Enthusiastic, Anxious>",
    "secondary_tone": "<secondary tone or null>",
    "behavioral_state": "<e.g. Defensive, Open, Evasive, Confrontational, Cooperative>",
    "emotional_state": "<overall emotional state of the sender>",
    "description": "<2-3 sentence interpretation of the sender's attitude and behavior>"
  },
  "statistics": {
    "word_count": <int>,
    "sentence_count": <int>,
    "avg_sentence_length": <float>,
    "subjectivity": <float 0.0-1.0>,
    "intensity": <float 0.0-1.0>,
    "confidence": <float 0.0-1.0>
  },
  "key_phrases": ["<phrase1>", "<phrase2>", "<phrase3>"],
  "overall_summary": "<3-4 sentence expert summary of the sender's attitude, emotional state, and behavioral signals>"
}

Emotions to always include (set present: true/false and score accordingly):
joy, anger, fear, sadness, surprise, disgust, trust, anticipation, sarcasm, anxiety

Scores must be honest and calibrated — not all 1.0. Return ONLY the JSON.
"""

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>SentimentIQ — Emotion Intelligence</title>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet"/>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg: #07080f;
      --surface: #0f1020;
      --card: #161b35;
      --border: #2a2f5a;
      --text: #f0f2ff;
      --muted: #ffffff;
      --radius: 20px;
    }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: 'Outfit', sans-serif;
      min-height: 100vh;
      overflow-x: hidden;
    }

    /* Animated background */
    .bg-orbs {
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 0;
      overflow: hidden;
    }
    .orb {
      position: absolute;
      border-radius: 50%;
      filter: blur(80px);
      opacity: 0.18;
      animation: float 12s ease-in-out infinite;
    }
    .orb1 { width: 500px; height: 500px; background: #ff3cac; top: -100px; left: -100px; animation-delay: 0s; }
    .orb2 { width: 400px; height: 400px; background: #784ba0; top: 30%; right: -80px; animation-delay: -4s; }
    .orb3 { width: 350px; height: 350px; background: #2b86c5; bottom: 10%; left: 20%; animation-delay: -8s; }
    .orb4 { width: 300px; height: 300px; background: #ffb347; bottom: -60px; right: 30%; animation-delay: -2s; }

    @keyframes float {
      0%, 100% { transform: translateY(0) scale(1); }
      50% { transform: translateY(-40px) scale(1.05); }
    }

    .page { position: relative; z-index: 1; max-width: 860px; margin: 0 auto; padding: 48px 20px 80px; }

    /* Hero header */
    header { text-align: center; margin-bottom: 52px; }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(255,60,172,0.12);
      border: 1px solid rgba(255,60,172,0.3);
      border-radius: 100px;
      padding: 6px 16px;
      font-size: 0.72rem;
      font-weight: 600;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: #ff3cac;
      margin-bottom: 20px;
    }
    .badge-dot { width: 6px; height: 6px; border-radius: 50%; background: #ff3cac; animation: pulse 1.5s ease-in-out infinite; }
    @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(0.8)} }

    header h1 {
      font-size: clamp(3rem, 8vw, 5.5rem);
      font-weight: 900;
      letter-spacing: -0.04em;
      line-height: 0.95;
      margin-bottom: 18px;
    }

    .gradient-text {
      background: linear-gradient(135deg, #ff3cac 0%, #784ba0 40%, #2b86c5 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    header p {
      color: #ffffff;
      font-size: 1rem;
      font-weight: 400;
      line-height: 1.6;
      max-width: 480px;
      margin: 0 auto;
    }

    /* Input section */
    .input-shell {
      background: linear-gradient(135deg, rgba(255,60,172,0.15), rgba(43,134,197,0.15));
      border-radius: 24px;
      padding: 2px;
      margin-bottom: 28px;
    }

    .input-inner {
      background: var(--surface);
      border-radius: 22px;
      padding: 28px;
    }

    .input-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 14px;
    }

    .input-label {
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: #ffffff;
    }

    .char-count {
      font-size: 0.72rem;
      color: #ffffff;
      font-weight: 400;
    }

    textarea {
      width: 100%;
      background: rgba(255,255,255,0.04);
      border: 1.5px solid var(--border);
      border-radius: 14px;
      color: var(--text);
      font-family: 'Outfit', sans-serif;
      font-size: 1rem;
      font-weight: 300;
      padding: 18px 20px;
      resize: vertical;
      min-height: 140px;
      outline: none;
      transition: border-color 0.3s, box-shadow 0.3s;
      line-height: 1.65;
    }

    textarea:focus {
      border-color: #ff3cac;
      box-shadow: 0 0 0 4px rgba(255,60,172,0.1);
    }
    textarea::placeholder { color: #ffffff; }

    .input-actions {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      margin-top: 16px;
      gap: 12px;
    }

    .hint { font-size: 0.72rem; color: #ffffff; margin-right: auto; }
    .hint kbd {
      background: var(--border);
      border-radius: 4px;
      padding: 1px 5px;
      font-family: inherit;
      font-size: 0.68rem;
    }

    #analyzeBtn {
      background: linear-gradient(135deg, #ff3cac, #784ba0, #2b86c5);
      background-size: 200% 200%;
      animation: gradientShift 4s ease infinite;
      color: #fff;
      border: none;
      border-radius: 14px;
      font-family: 'Outfit', sans-serif;
      font-size: 0.95rem;
      font-weight: 700;
      letter-spacing: 0.04em;
      padding: 14px 36px;
      cursor: pointer;
      transition: transform 0.15s, box-shadow 0.3s;
      box-shadow: 0 4px 24px rgba(255,60,172,0.35);
    }

    @keyframes gradientShift {
      0% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
      100% { background-position: 0% 50%; }
    }

    #analyzeBtn:hover { transform: translateY(-2px); box-shadow: 0 8px 32px rgba(255,60,172,0.5); }
    #analyzeBtn:active { transform: scale(0.97); }
    #analyzeBtn:disabled { opacity: 0.45; cursor: not-allowed; transform: none; }

    .spinner {
      display: inline-block;
      width: 14px; height: 14px;
      border: 2px solid rgba(255,255,255,0.3);
      border-top-color: #fff;
      border-radius: 50%;
      animation: spin 0.6s linear infinite;
      vertical-align: middle;
      margin-right: 8px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    /* Results */
    #results { display: none; animation: fadeUp 0.5s ease; }
    #results.visible { display: block; }
    @keyframes fadeUp { from { opacity:0; transform:translateY(20px); } to { opacity:1; transform:translateY(0); } }

    .error-box {
      background: rgba(255,80,80,0.1);
      border: 1px solid rgba(255,80,80,0.3);
      border-radius: var(--radius);
      padding: 18px 22px;
      color: #ff6b6b;
      font-size: 0.9rem;
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    /* Section label */
    .section-label {
      font-size: 0.68rem;
      font-weight: 700;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: #ffffff;
      margin-bottom: 12px;
      padding-left: 4px;
    }

    /* Cards */
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
    @media (max-width: 600px) { .grid-2 { grid-template-columns: 1fr; } }

    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 24px;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .card:hover { transform: translateY(-2px); box-shadow: 0 8px 32px rgba(0,0,0,0.3); }

    .card-label {
      font-size: 0.65rem;
      font-weight: 700;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: #ffffff;
      margin-bottom: 18px;
    }

    /* Sentiment card */
    .sent-hero {
      display: flex;
      align-items: center;
      gap: 16px;
      margin-bottom: 14px;
    }

    .sent-icon {
      width: 60px; height: 60px;
      border-radius: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.8rem;
      flex-shrink: 0;
    }

    .sent-label {
      font-size: 1.9rem;
      font-weight: 800;
      letter-spacing: -0.02em;
    }

    .sent-pill {
      display: inline-block;
      font-size: 0.72rem;
      font-weight: 600;
      padding: 4px 12px;
      border-radius: 100px;
      margin-top: 4px;
    }

    .sent-summary { font-size: 0.82rem; color: #ffffff; line-height: 1.55; font-weight: 400; }

    /* Emotion bars */
    .emotion-row { margin-bottom: 11px; }
    .emotion-meta { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }
    .emotion-name {
      font-size: 0.78rem;
      font-weight: 600;
      text-transform: capitalize;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .emotion-score { font-size: 0.72rem; color: #ffffff; }
    .bar-track {
      height: 7px;
      background: rgba(255,255,255,0.06);
      border-radius: 4px;
      overflow: hidden;
    }
    .bar-fill {
      height: 100%;
      border-radius: 4px;
      transition: width 1s cubic-bezier(0.4,0,0.2,1);
    }
    .emotion-row.dim .emotion-name { color: var(--muted); }
    .emotion-row.dim .bar-fill { opacity: 0.3; }

    /* Attitude tags */
    .tags-wrap { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
    .tag {
      display: inline-block;
      border-radius: 8px;
      font-size: 0.75rem;
      font-weight: 600;
      padding: 5px 12px;
      letter-spacing: 0.02em;
    }
    .tag-primary { background: rgba(255,60,172,0.15); color: #ff3cac; border: 1px solid rgba(255,60,172,0.25); }
    .tag-secondary { background: rgba(120,75,160,0.15); color: #a78bfa; border: 1px solid rgba(120,75,160,0.25); }
    .tag-behavior { background: rgba(43,134,197,0.15); color: #60c4ff; border: 1px solid rgba(43,134,197,0.25); }
    .tag-state { background: rgba(255,179,71,0.12); color: #ffb347; border: 1px solid rgba(255,179,71,0.25); }

    .attitude-desc {
      font-size: 0.83rem;
      color: #ffffff;
      line-height: 1.65;
      font-weight: 400;
    }

    /* Stats */
    .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 18px; }
    .stat-item { }
    .stat-val {
      font-size: 1.8rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      background: linear-gradient(135deg, #fff, #a0a8d0);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .stat-label { font-size: 0.65rem; color: #ffffff; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 2px; font-weight: 600; }

    .meter-row { margin-bottom: 12px; }
    .meter-meta { display: flex; justify-content: space-between; margin-bottom: 5px; }
    .meter-name { font-size: 0.75rem; color: #ffffff; font-weight: 500; }
    .meter-val { font-size: 0.75rem; font-weight: 700; }
    .meter-track { height: 6px; background: rgba(255,255,255,0.06); border-radius: 4px; overflow: hidden; }
    .meter-fill { height: 100%; border-radius: 4px; }

    /* Key phrases */
    .phrase-tag {
      display: inline-block;
      background: rgba(255,255,255,0.05);
      border: 1px solid var(--border);
      border-radius: 8px;
      font-size: 0.8rem;
      font-weight: 500;
      padding: 6px 14px;
      margin: 0 8px 10px 0;
      color: var(--text);
      transition: background 0.2s, border-color 0.2s;
    }
    .phrase-tag:hover { background: rgba(255,60,172,0.1); border-color: rgba(255,60,172,0.3); }

    /* Summary card */
    .summary-shell {
      background: linear-gradient(135deg, rgba(255,60,172,0.12), rgba(43,134,197,0.12));
      border-radius: 22px;
      padding: 2px;
      margin-top: 16px;
    }
    .summary-inner {
      background: var(--card);
      border-radius: 20px;
      padding: 26px;
    }
    .summary-title {
      font-size: 0.65rem;
      font-weight: 700;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: #ffffff;
      margin-bottom: 14px;
    }
    .summary-text {
      font-size: 0.95rem;
      line-height: 1.8;
      color: #ffffff;
      font-weight: 300;
    }

    .chart-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 24px;
      margin-bottom: 16px;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .chart-card:hover { transform: translateY(-2px); box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
    .chart-wrap { position: relative; height: 260px; }
    .chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
    @media (max-width: 600px) { .chart-grid { grid-template-columns: 1fr; } }

    footer {
      text-align: center;
      margin-top: 52px;
      color: #ffffff;
      font-size: 0.72rem;
      font-weight: 500;
      letter-spacing: 0.1em;
      text-transform: uppercase;
    }
  </style>
</head>
<body>
  <div class="bg-orbs">
    <div class="orb orb1"></div>
    <div class="orb orb2"></div>
    <div class="orb orb3"></div>
    <div class="orb orb4"></div>
  </div>

  <div class="page">
    <header>
      <div class="badge"><span class="badge-dot"></span>AI-Powered Analysis</div>
      <h1><span class="gradient-text">Sentiment</span><br>Intelligence</h1>
      <p>Decode the emotion, attitude & psychological state behind any text — instantly.</p>
    </header>

    <div class="input-shell">
      <div class="input-inner">
        <div class="input-top">
          <div class="input-label">Your Text</div>
          <span class="char-count" id="charCount">0 characters</span>
        </div>
        <textarea id="inputText" placeholder="Paste a message, review, tweet, essay, email — anything..."></textarea>
        <div class="input-actions">
          <span class="hint">Press <kbd>ctrl</kbd> + <kbd>Enter</kbd> to analyze</span>
          <button id="analyzeBtn" onclick="analyze()">Analyze Now →</button>
        </div>
      </div>
    </div>

    <div id="results">
      <div id="errorBox" class="error-box" style="display:none;">
        <span>⚠</span><span id="errorMsg"></span>
      </div>

      <div id="analysisOutput" style="display:none;">

        <div class="grid-2">
          <!-- Sentiment -->
          <div class="card" id="sentimentCard">
            <div class="card-label">Overall Sentiment</div>
            <div class="sent-hero">
              <div class="sent-icon" id="sentIcon"></div>
              <div>
                <div class="sent-label" id="sentimentLabel"></div>
                <div id="sentimentPill"></div>
              </div>
            </div>
            <div class="sent-summary" id="sentimentSummary"></div>
          </div>

          <!-- Emotions -->
          <div class="card">
            <div class="card-label">Emotion Breakdown</div>
            <div id="emotionBars"></div>
          </div>
        </div>

        <div class="grid-2">
          <!-- Attitude -->
          <div class="card">
            <div class="card-label">Attitude & Tone</div>
            <div class="tags-wrap" id="attitudeTags"></div>
            <div class="attitude-desc" id="attitudeDesc"></div>
          </div>

          <!-- Stats -->
          <div class="card">
            <div class="card-label">Text Statistics</div>
            <div class="stats-grid" id="statsGrid"></div>
            <div id="meters"></div>
          </div>
        </div>

        <!-- Charts -->
        <div class="chart-grid">
          <div class="chart-card">
            <div class="card-label">Emotion Radar</div>
            <div class="chart-wrap"><canvas id="radarChart"></canvas></div>
          </div>
          <div class="chart-card">
            <div class="card-label">Sentiment Breakdown</div>
            <div class="chart-wrap"><canvas id="donutChart"></canvas></div>
          </div>
        </div>

        <!-- Key phrases -->
        <div class="card" style="margin-bottom:0;">
          <div class="card-label">Key Phrases</div>
          <div id="keyPhrases"></div>
        </div>

        <!-- Summary -->
        <div class="summary-shell">
          <div class="summary-inner">
            <div class="summary-title">✦ Expert Analysis Summary</div>
            <div class="summary-text" id="overallSummary"></div>
          </div>
        </div>

      </div>
    </div>

    <footer>Sentiment_IQ </footer>
  </div>

  <script>
    const textarea = document.getElementById('inputText');
    const charCount = document.getElementById('charCount');
    textarea.addEventListener('input', () => {
      charCount.textContent = textarea.value.length + ' characters';
    });

    const sentConfig = {
      Positive: { color: '#00e57b', bg: 'rgba(0,229,123,0.12)', border: 'rgba(0,229,123,0.25)', icon: '😊', iconBg: 'rgba(0,229,123,0.15)' },
      Negative: { color: '#ff4d6a', bg: 'rgba(255,77,106,0.12)', border: 'rgba(255,77,106,0.25)', icon: '😤', iconBg: 'rgba(255,77,106,0.15)' },
      Neutral:  { color: '#60c4ff', bg: 'rgba(96,196,255,0.12)', border: 'rgba(96,196,255,0.25)', icon: '😐', iconBg: 'rgba(96,196,255,0.15)' },
      Mixed:    { color: '#ffb347', bg: 'rgba(255,179,71,0.12)', border: 'rgba(255,179,71,0.25)', icon: '🤔', iconBg: 'rgba(255,179,71,0.15)' },
    };

    const emotionColors = [
      'linear-gradient(90deg,#ff3cac,#ff6b9d)',
      'linear-gradient(90deg,#ff6b35,#ff9f1c)',
      'linear-gradient(90deg,#784ba0,#a78bfa)',
      'linear-gradient(90deg,#2b86c5,#60c4ff)',
      'linear-gradient(90deg,#00e57b,#00c9a7)',
      'linear-gradient(90deg,#ff4d6a,#ff8c69)',
      'linear-gradient(90deg,#ffb347,#ffd700)',
      'linear-gradient(90deg,#00c9a7,#4ecdc4)',
      'linear-gradient(90deg,#c471ed,#f64f59)',
      'linear-gradient(90deg,#60c4ff,#a78bfa)',
    ];

    const emotionEmoji = {
      joy:'😄', anger:'😠', fear:'😨', sadness:'😢',
      surprise:'😲', disgust:'🤢', trust:'🤝',
      anticipation:'⏳', sarcasm:'😏', anxiety:'😰'
    };

    async function analyze() {
      const text = textarea.value.trim();
      if (!text) return;

      const btn = document.getElementById('analyzeBtn');
      const results = document.getElementById('results');
      const errorBox = document.getElementById('errorBox');
      const output = document.getElementById('analysisOutput');

      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span>Analyzing...';
      results.classList.add('visible');
      errorBox.style.display = 'none';
      output.style.display = 'none';

      try {
        const res = await fetch('/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text })
        });
        const data = await res.json();

        if (data.error) {
          errorBox.style.display = 'flex';
          document.getElementById('errorMsg').textContent = data.message || data.error;
        } else {
          renderResults(data);
          output.style.display = 'block';
        }
      } catch(e) {
        errorBox.style.display = 'flex';
        document.getElementById('errorMsg').textContent = 'Network error. Is the server running?';
      }

      btn.disabled = false;
      btn.textContent = 'Analyze Now →';
    }


    let radarChartInst = null;
    let donutChartInst = null;

    function renderCharts(d) {
      const emotions = [...d.emotions].sort((a,b) => b.score - a.score);
      const labels = emotions.map(e => e.name.charAt(0).toUpperCase() + e.name.slice(1));
      const scores = emotions.map(e => Math.round(e.score * 100));

      // Destroy old charts
      if (radarChartInst) radarChartInst.destroy();
      if (donutChartInst) donutChartInst.destroy();

      // Radar chart
      const radarCtx = document.getElementById('radarChart').getContext('2d');
      radarChartInst = new Chart(radarCtx, {
        type: 'radar',
        data: {
          labels,
          datasets: [{
            label: 'Emotion Intensity',
            data: scores,
            backgroundColor: 'rgba(255,60,172,0.15)',
            borderColor: '#ff3cac',
            borderWidth: 2,
            pointBackgroundColor: '#ff3cac',
            pointBorderColor: '#fff',
            pointBorderWidth: 1.5,
            pointRadius: 4,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            r: {
              min: 0, max: 100,
              ticks: { display: false, stepSize: 25 },
              grid: { color: 'rgba(255,255,255,0.08)' },
              angleLines: { color: 'rgba(255,255,255,0.08)' },
              pointLabels: {
                color: '#ffffff',
                font: { family: 'Outfit', size: 11, weight: '600' }
              }
            }
          },
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: '#161b35',
              borderColor: '#2a2f5a',
              borderWidth: 1,
              titleColor: '#fff',
              bodyColor: '#fff',
              callbacks: { label: ctx => ` ${ctx.raw}%` }
            }
          }
        }
      });

      // Donut — sentiment + subjectivity + intensity
      const sl = d.sentiment.label;
      const sentScore = Math.round(d.sentiment.score * 100);
      const subj = Math.round(d.statistics.subjectivity * 100);
      const intens = Math.round(d.statistics.intensity * 100);
      const conf = Math.round(d.statistics.confidence * 100);

      const donutCtx = document.getElementById('donutChart').getContext('2d');
      donutChartInst = new Chart(donutCtx, {
        type: 'doughnut',
        data: {
          labels: ['Sentiment', 'Subjectivity', 'Intensity', 'Confidence'],
          datasets: [{
            data: [sentScore, subj, intens, conf],
            backgroundColor: [
              'rgba(255,60,172,0.85)',
              'rgba(120,75,160,0.85)',
              'rgba(43,134,197,0.85)',
              'rgba(0,229,123,0.85)',
            ],
            borderColor: '#07080f',
            borderWidth: 3,
            hoverOffset: 8,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '62%',
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                color: '#ffffff',
                font: { family: 'Outfit', size: 11, weight: '600' },
                padding: 14,
                boxWidth: 12,
                boxHeight: 12,
              }
            },
            tooltip: {
              backgroundColor: '#161b35',
              borderColor: '#2a2f5a',
              borderWidth: 1,
              titleColor: '#fff',
              bodyColor: '#fff',
              callbacks: { label: ctx => ` ${ctx.label}: ${ctx.raw}%` }
            }
          }
        }
      });
    }

    function renderResults(d) {
      // Sentiment
      const sl = d.sentiment.label;
      const cfg = sentConfig[sl] || sentConfig.Neutral;
      const pct = Math.round(d.sentiment.score * 100);

      document.getElementById('sentIcon').textContent = cfg.icon;
      document.getElementById('sentIcon').style.background = cfg.iconBg;
      document.getElementById('sentimentLabel').textContent = sl;
      document.getElementById('sentimentLabel').style.color = cfg.color;
      document.getElementById('sentimentPill').innerHTML =
        `<span class="sent-pill" style="background:${cfg.bg};color:${cfg.color};border:1px solid ${cfg.border}">${pct}% confidence</span>`;
      document.getElementById('sentimentSummary').textContent = d.sentiment.summary;

      // Emotions
      const emotionBars = document.getElementById('emotionBars');
      emotionBars.innerHTML = '';
      const sorted = [...d.emotions].sort((a,b) => b.score - a.score);
      sorted.forEach((em, i) => {
        const p = Math.round(em.score * 100);
        const emoji = emotionEmoji[em.name] || '•';
        const grad = emotionColors[i % emotionColors.length];
        emotionBars.innerHTML += `
          <div class="emotion-row ${em.present ? '' : 'dim'}">
            <div class="emotion-meta">
              <span class="emotion-name">${emoji} ${em.name}</span>
              <span class="emotion-score">${p}%</span>
            </div>
            <div class="bar-track">
              <div class="bar-fill" style="width:${p}%;background:${grad}"></div>
            </div>
          </div>`;
      });

      // Attitude
      const att = d.attitude;
      document.getElementById('attitudeTags').innerHTML =
        `<span class="tag tag-primary">${att.tone}</span>` +
        (att.secondary_tone ? `<span class="tag tag-secondary">${att.secondary_tone}</span>` : '') +
        (att.behavioral_state ? `<span class="tag tag-behavior">${att.behavioral_state}</span>` : '') +
        (att.emotional_state ? `<span class="tag tag-state">${att.emotional_state}</span>` : '');
      document.getElementById('attitudeDesc').textContent = att.description;

      // Stats
      const s = d.statistics;
      document.getElementById('statsGrid').innerHTML = `
        <div class="stat-item"><div class="stat-val">${s.word_count}</div><div class="stat-label">Words</div></div>
        <div class="stat-item"><div class="stat-val">${s.sentence_count}</div><div class="stat-label">Sentences</div></div>
        <div class="stat-item"><div class="stat-val">${s.avg_sentence_length.toFixed(1)}</div><div class="stat-label">Avg Length</div></div>
        <div class="stat-item"><div class="stat-val">${Math.round(s.confidence*100)}%</div><div class="stat-label">Confidence</div></div>
      `;

      const meters = [
        { name: 'Subjectivity', val: s.subjectivity, color: 'linear-gradient(90deg,#ff3cac,#784ba0)', textColor: '#ff3cac' },
        { name: 'Intensity',    val: s.intensity,    color: 'linear-gradient(90deg,#ff6b35,#ffb347)', textColor: '#ffb347' },
      ];
      document.getElementById('meters').innerHTML = meters.map(m => `
        <div class="meter-row">
          <div class="meter-meta">
            <span class="meter-name">${m.name}</span>
            <span class="meter-val" style="color:${m.textColor}">${Math.round(m.val*100)}%</span>
          </div>
          <div class="meter-track">
            <div class="meter-fill" style="width:${Math.round(m.val*100)}%;background:${m.color}"></div>
          </div>
        </div>`).join('');

      // Key phrases
      document.getElementById('keyPhrases').innerHTML =
        (d.key_phrases || []).map(p => `<span class="phrase-tag">${p}</span>`).join('');

      // Summary
      document.getElementById('overallSummary').textContent = d.overall_summary;

      // Charts
      renderCharts(d);
    }

    textarea.addEventListener('keydown', e => {
      if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) analyze();
    });
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"error": "empty", "message": "Please enter some text to analyze."}), 400

    if len(text) < 3:
        return jsonify({"error": "unintelligible", "message": "Input is too short to analyze meaningfully."}), 422

    try:
        response = req.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze this text:\n\n{text}"}
                ],
                "max_tokens": 1024,
                "temperature": 0.2,
            },
            timeout=30,
        )

        if response.status_code != 200:
            try:
                err = response.json().get("error", {})
                msg = err.get("message", response.text)
            except Exception:
                msg = response.text
            return jsonify({"error": f"[{response.status_code}] {msg}"}), response.status_code

        raw = response.json()["choices"][0]["message"]["content"].strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)

        if result.get("error") == "unintelligible":
            return jsonify(result), 422

        return jsonify(result)

    except json.JSONDecodeError:
        return jsonify({"error": "parse_error", "message": "Could not parse analysis response. Try again."}), 500
    except req.exceptions.Timeout:
        return jsonify({"error": "timeout", "message": "Request timed out. Try again."}), 504
    except Exception as e:
        return jsonify({"error": "server_error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))