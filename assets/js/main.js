// Main JavaScript utilities for interactive app demos

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
    const w = this.canvas.width;
    const h = this.canvas.height;
    this.ctx.clearRect(0, 0, w, h);

    const whiteKeys = this.notes.filter(n => !n.isBlack);
    const keyWidth = w / whiteKeys.length;

    // Draw white keys
    whiteKeys.forEach((note, i) => {
      const isPressed = this.activeNotes.has(note.name);
      this.ctx.fillStyle = isPressed ? '#ffd700' : '#ffffff';
      this.ctx.fillRect(i * keyWidth + 2, 10, keyWidth - 4, h - 20);
      this.ctx.strokeStyle = '#1a1e29';
      this.ctx.strokeRect(i * keyWidth + 2, 10, keyWidth - 4, h - 20);

      this.ctx.fillStyle = '#111827';
      this.ctx.font = 'bold 14px sans-serif';
      this.ctx.textAlign = 'center';
      this.ctx.fillText(`${note.name} (${note.key})`, i * keyWidth + keyWidth / 2, h - 30);
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
    this.canvas.height = this.canvas.clientHeight;

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
      // Find nearest food
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
