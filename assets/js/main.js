// Main JavaScript utilities for interactive app demos & studio hub

function copyToClipboard(text, btnElement) {
  navigator.clipboard.writeText(text).then(() => {
    const original = btnElement.innerText;
    btnElement.innerText = "Copied! ✓";
    btnElement.style.color = "#00f0dc";
    setTimeout(() => {
      btnElement.innerText = original;
      btnElement.style.color = "";
    }, 2000);
  });
}

// -------------------------------------------------------------
// Interactive Studio Hub Tab Switcher
// -------------------------------------------------------------
function switchStudioTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });
  document.querySelectorAll('.tab-panel').forEach(panel => {
    panel.classList.toggle('active', panel.id === tabId);
  });

  if (tabId === 'tab-piano' && window.webPianoInstance) {
    window.webPianoInstance.draw();
  }
  if (tabId === 'tab-swarm' && !window.webSwarmInstance) {
    window.webSwarmInstance = new WebSwarmDemo('studioSwarmCanvas');
  }
  if (tabId === 'tab-art') {
    generateStudioArt();
  }
}

// -------------------------------------------------------------
// Interactive Category Filtering & Search
// -------------------------------------------------------------
function filterApps(category, btn) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');

  const cards = document.querySelectorAll('.app-card');
  cards.forEach(card => {
    const cardCat = card.dataset.category || 'all';
    if (category === 'all' || cardCat.includes(category)) {
      card.style.display = 'flex';
    } else {
      card.style.display = 'none';
    }
  });
}

function searchApps(query) {
  const q = query.toLowerCase().trim();
  const cards = document.querySelectorAll('.app-card');
  cards.forEach(card => {
    const text = card.innerText.toLowerCase();
    if (!q || text.includes(q)) {
      card.style.display = 'flex';
    } else {
      card.style.display = 'none';
    }
  });
}

// -------------------------------------------------------------
// 4-7-8 Mindful Breathing Pacer Logic
// -------------------------------------------------------------
let breathInterval = null;
function initBreathingPacer() {
  const circle = document.getElementById('studioBreathCircle');
  const text = document.getElementById('studioBreathText');
  const timer = document.getElementById('studioBreathTimer');
  if (!circle || !text || !timer) return;

  let state = 'Inhale'; // 'Inhale' (4s), 'Hold' (7s), 'Exhale' (8s)
  let count = 4;

  function tick() {
    timer.innerText = `${count}s`;
    if (count > 1) {
      count--;
    } else {
      if (state === 'Inhale') {
        state = 'Hold';
        count = 7;
        text.innerText = 'HOLD BREATH';
        circle.style.transform = 'scale(1.4)';
        circle.style.borderColor = '#f59e0b';
      } else if (state === 'Hold') {
        state = 'Exhale';
        count = 8;
        text.innerText = 'EXHALE SLOWLY';
        circle.style.transform = 'scale(0.85)';
        circle.style.borderColor = '#3b82f6';
      } else {
        state = 'Inhale';
        count = 4;
        text.innerText = 'INHALE DEEP';
        circle.style.transform = 'scale(1.4)';
        circle.style.borderColor = '#00f0dc';
      }
    }
  }

  if (breathInterval) clearInterval(breathInterval);
  text.innerText = 'INHALE DEEP';
  circle.style.transform = 'scale(1.4)';
  circle.style.borderColor = '#00f0dc';
  breathInterval = setInterval(tick, 1000);
}

// -------------------------------------------------------------
// Wallpaper Generator in Studio Hub
// -------------------------------------------------------------
function generateStudioArt() {
  const canvas = document.getElementById('studioArtCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  canvas.width = canvas.clientWidth;
  canvas.height = canvas.clientHeight;

  const palettes = [
    ['#07090e', '#00f0dc', '#3b82f6', '#a855f7'],
    ['#051510', '#10b981', '#34d399', '#f59e0b'],
    ['#150510', '#f43f5e', '#ec4899', '#fbbf24']
  ];
  const p = palettes[Math.floor(Math.random() * palettes.length)];

  ctx.fillStyle = p[0];
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  for (let i = 0; i < 40; i++) {
    ctx.strokeStyle = p[1 + Math.floor(Math.random() * (p.length - 1))];
    ctx.lineWidth = 1 + Math.random() * 2.5;
    ctx.beginPath();
    ctx.moveTo(Math.random() * canvas.width, Math.random() * canvas.height);
    ctx.lineTo(Math.random() * canvas.width, Math.random() * canvas.height);
    ctx.stroke();
  }

  for (let i = 0; i < 8; i++) {
    ctx.fillStyle = p[1 + Math.floor(Math.random() * (p.length - 1))] + '22';
    ctx.beginPath();
    ctx.arc(Math.random() * canvas.width, Math.random() * canvas.height, 30 + Math.random() * 90, 0, Math.PI * 2);
    ctx.fill();
  }
}

// -------------------------------------------------------------
// Interactive Web Synthesizer for Piano Demo (Web Audio API)
// -------------------------------------------------------------
class WebPianoDemo {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.audioCtx = null;
    this.activeNotes = new Set();
    this.initAudio();
    this.initKeyboard();
    this.draw();
  }

  initAudio() {
    window.addEventListener('click', () => {
      if (!this.audioCtx) {
        this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
    }, { once: true });
  }

  playNote(freq) {
    if (!this.audioCtx) {
      this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    const osc = this.audioCtx.createOscillator();
    const gain = this.audioCtx.createGain();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(freq, this.audioCtx.currentTime);
    gain.gain.setValueAtTime(0.4, this.audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + 1.2);
    osc.connect(gain);
    gain.connect(this.audioCtx.destination);
    osc.start();
    osc.stop(this.audioCtx.currentTime + 1.2);
  }

  initKeyboard() {
    const notes = [
      { name: 'C', freq: 261.63, key: 'A', isBlack: false },
      { name: 'C#', freq: 277.18, key: 'W', isBlack: true },
      { name: 'D', freq: 293.66, key: 'S', isBlack: false },
      { name: 'D#', freq: 311.13, key: 'E', isBlack: true },
      { name: 'E', freq: 329.63, key: 'D', isBlack: false },
      { name: 'F', freq: 349.23, key: 'F', isBlack: false },
      { name: 'F#', freq: 369.99, key: 'T', isBlack: true },
      { name: 'G', freq: 392.00, key: 'G', isBlack: false },
      { name: 'G#', freq: 415.30, key: 'Y', isBlack: true },
      { name: 'A', freq: 440.00, key: 'H', isBlack: false },
      { name: 'A#', freq: 466.16, key: 'U', isBlack: true },
      { name: 'B', freq: 493.88, key: 'J', isBlack: false },
      { name: 'C2', freq: 523.25, key: 'K', isBlack: false },
    ];
    this.notes = notes;

    window.addEventListener('keydown', (e) => {
      const k = e.key.toUpperCase();
      const n = this.notes.find(x => x.key === k);
      if (n && !this.activeNotes.has(n.name)) {
        this.activeNotes.add(n.name);
        this.playNote(n.freq);
        this.draw();
      }
    });

    window.addEventListener('keyup', (e) => {
      const k = e.key.toUpperCase();
      const n = this.notes.find(x => x.key === k);
      if (n) {
        this.activeNotes.delete(n.name);
        this.draw();
      }
    });
  }

  draw() {
    if (!this.canvas) return;
    const w = this.canvas.width = this.canvas.clientWidth;
    const h = this.canvas.height = this.canvas.clientHeight || 180;
    this.ctx.clearRect(0, 0, w, h);

    const whiteKeys = this.notes.filter(n => !n.isBlack);
    const keyWidth = w / whiteKeys.length;

    whiteKeys.forEach((note, i) => {
      const isPressed = this.activeNotes.has(note.name);
      this.ctx.fillStyle = isPressed ? '#00f0dc' : '#ffffff';
      this.ctx.fillRect(i * keyWidth + 2, 10, keyWidth - 4, h - 20);
      this.ctx.strokeStyle = '#1a1e29';
      this.ctx.strokeRect(i * keyWidth + 2, 10, keyWidth - 4, h - 20);

      this.ctx.fillStyle = '#111827';
      this.ctx.font = 'bold 13px sans-serif';
      this.ctx.textAlign = 'center';
      this.ctx.fillText(`${note.name} (${note.key})`, i * keyWidth + keyWidth / 2, h - 24);
    });
  }
}

// -------------------------------------------------------------
// Interactive Swarm Simulation for Day 3 Web Demo
// -------------------------------------------------------------
class WebSwarmDemo {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.agents = [];
    this.foods = [];
    this.init();
  }

  init() {
    this.canvas.width = this.canvas.clientWidth;
    this.canvas.height = this.canvas.clientHeight || 300;

    for (let i = 0; i < 40; i++) {
      this.agents.push({
        x: Math.random() * this.canvas.width,
        y: Math.random() * this.canvas.height,
        vx: (Math.random() - 0.5) * 2.5,
        vy: (Math.random() - 0.5) * 2.5,
        energy: 80 + Math.random() * 40,
        radius: 4,
        color: '#00f0dc'
      });
    }

    for (let i = 0; i < 8; i++) {
      this.foods.push({
        x: Math.random() * this.canvas.width,
        y: Math.random() * this.canvas.height
      });
    }

    this.canvas.addEventListener('click', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      this.foods.push({ x: e.clientX - rect.left, y: e.clientY - rect.top });
    });

    this.loop();
  }

  loop() {
    this.update();
    this.render();
    requestAnimationFrame(() => this.loop());
  }

  update() {
    const w = this.canvas.width;
    const h = this.canvas.height;

    this.agents.forEach(a => {
      let nearest = null;
      let minDist = 120;
      this.foods.forEach((f, idx) => {
        const dx = f.x - a.x;
        const dy = f.y - a.y;
        const dist = Math.hypot(dx, dy);
        if (dist < minDist) {
          minDist = dist;
          nearest = { f, idx, dx, dy, dist };
        }
      });

      if (nearest) {
        a.vx += (nearest.dx / nearest.dist) * 0.15;
        a.vy += (nearest.dy / nearest.dist) * 0.15;
        if (nearest.dist < 10) {
          this.foods.splice(nearest.idx, 1);
          a.energy += 30;
          this.foods.push({ x: Math.random() * w, y: Math.random() * h });
        }
      }

      a.x += a.vx;
      a.y += a.vy;

      if (a.x < 0 || a.x > w) a.vx *= -1;
      if (a.y < 0 || a.y > h) a.vy *= -1;
    });
  }

  render() {
    this.ctx.fillStyle = '#07090e';
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    // Draw Foods
    this.ctx.fillStyle = '#10b981';
    this.foods.forEach(f => {
      this.ctx.beginPath();
      this.ctx.arc(f.x, f.y, 6, 0, Math.PI * 2);
      this.ctx.fill();
    });

    // Draw Agents
    this.agents.forEach(a => {
      this.ctx.fillStyle = a.color;
      this.ctx.beginPath();
      this.ctx.arc(a.x, a.y, a.radius, 0, Math.PI * 2);
      this.ctx.fill();
    });
  }
}

window.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('studioBreathCircle')) {
    initBreathingPacer();
  }
  if (document.getElementById('studioPianoCanvas')) {
    window.webPianoInstance = new WebPianoDemo('studioPianoCanvas');
  }
});
