/* Sonora — reproductor fijo con forma de onda.
   Un solo momento de movimiento por pantalla: la onda al reproducir. */
'use strict';

const SonoraPlayer = (() => {
  const audio = document.getElementById('elemento-audio');
  const panel = document.getElementById('reproductor');
  const btnPlay = document.getElementById('btn-play');
  const tiempoEl = document.getElementById('tiempo-audio');
  const metaEl = document.getElementById('reproductor-meta');
  const canvas = document.getElementById('onda');
  const ctx = canvas.getContext('2d');
  const selVelocidad = document.getElementById('sel-velocidad-player');
  const btnDescargar = document.getElementById('btn-descargar-audio');
  const btnCerrar = document.getElementById('btn-cerrar-reproductor');

  let urlActual = null;
  let nombreActual = 'audio';
  let formatoActual = 'mp3';
  let picos = null; // Float32Array de picos por columna, para dibujar la onda
  let reproduciendo = false;

  function formatoTiempo(segundos) {
    if (!Number.isFinite(segundos)) return '0:00';
    const s = Math.max(0, Math.floor(segundos));
    return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0');
  }

  function dibujarOnda(progreso) {
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    const columnas = 120;
    const anchoCol = w / columnas;
    for (let i = 0; i < columnas; i++) {
      const p = picos ? picos[Math.floor((i / columnas) * picos.length)] : 0.25 + 0.15 * Math.sin(i * 0.7);
      const alto = Math.max(3, p * (h - 8));
      const x = i * anchoCol + 1;
      const y = (h - alto) / 2;
      const tocado = progreso != null && (i / columnas) <= progreso;
      ctx.fillStyle = tocado ? '#FACC15' : '#39424E';
      ctx.fillRect(x, y, Math.max(2, anchoCol - 2), alto);
    }
  }

  async function calcularPicos(blob) {
    try {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) { picos = null; return; }
      const ac = new AC();
      const buf = await blob.arrayBuffer();
      const decoded = await ac.decodeAudioData(buf);
      const canal = decoded.getChannelData(0);
      const n = 240;
      const paso = Math.floor(canal.length / n) || 1;
      picos = new Float32Array(n);
      for (let i = 0; i < n; i++) {
        let max = 0;
        for (let j = i * paso; j < Math.min(canal.length, (i + 1) * paso); j += 4) {
          const v = Math.abs(canal[j]);
          if (v > max) max = v;
        }
        picos[i] = Math.min(1, max * 1.4);
      }
      await ac.close();
    } catch (_) {
      picos = null; // sin decodificación, la onda usa el patrón neutro
    }
    dibujarOnda(0);
  }

  function actualizarTiempo() {
    const dur = audio.duration || 0;
    tiempoEl.textContent = formatoTiempo(audio.currentTime) + ' / ' + formatoTiempo(dur);
    dibujarOnda(dur ? audio.currentTime / dur : 0);
  }

  function setPlayIcono() {
    btnPlay.textContent = reproduciendo ? '❚❚' : '▸';
    btnPlay.setAttribute('aria-label', reproduciendo ? 'Pausar' : 'Reproducir');
  }

  async function cargar(blob, meta, nombre, formato) {
    if (urlActual) URL.revokeObjectURL(urlActual);
    urlActual = URL.createObjectURL(blob);
    nombreActual = nombre || 'audio';
    formatoActual = formato || 'mp3';
    audio.src = urlActual;
    audio.playbackRate = Number(selVelocidad.value) || 1;
    metaEl.textContent = meta || 'Audio generado';
    panel.hidden = false;
    reproduciendo = false;
    setPlayIcono();
    await calcularPicos(blob);
    actualizarTiempo();
  }

  function reproducir() {
    if (!audio.src) return;
    audio.play().then(() => { reproduciendo = true; setPlayIcono(); }).catch(() => {
      SonoraApp.toast('No se pudo reproducir el audio.');
    });
  }
  function pausar() { audio.pause(); reproduciendo = false; setPlayIcono(); }
  function alternar() { if (reproduciendo) pausar(); else reproducir(); }
  function cerrar() { pausar(); panel.hidden = true; }

  function descargar() {
    if (!urlActual) return;
    const a = document.createElement('a');
    a.href = urlActual;
    a.download = nombreActual + '.' + formatoActual;
    document.body.appendChild(a);
    a.click();
    a.remove();
  }

  function buscarEnOnda(evento) {
    const rect = canvas.getBoundingClientRect();
    const x = (evento.clientX - rect.left) / rect.width;
    if (audio.duration) audio.currentTime = Math.max(0, Math.min(1, x)) * audio.duration;
    actualizarTiempo();
  }

  audio.addEventListener('timeupdate', actualizarTiempo);
  audio.addEventListener('loadedmetadata', actualizarTiempo);
  audio.addEventListener('ended', () => { reproduciendo = false; setPlayIcono(); dibujarOnda(0); });
  audio.addEventListener('pause', () => { if (reproduciendo) { reproduciendo = false; setPlayIcono(); } });
  btnPlay.addEventListener('click', alternar);
  btnDescargar.addEventListener('click', descargar);
  btnCerrar.addEventListener('click', cerrar);
  selVelocidad.addEventListener('change', () => { audio.playbackRate = Number(selVelocidad.value) || 1; });
  canvas.addEventListener('click', buscarEnOnda);
  document.addEventListener('visibilitychange', () => { if (document.hidden) pausar(); });

  dibujarOnda(0);

  return { cargar, reproducir, pausar, alternar, cerrar, formatoTiempo };
})();
