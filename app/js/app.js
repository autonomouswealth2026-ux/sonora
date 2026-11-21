/* Sonora — router por hash, estado del backend y Estudio TTS.
   Pantallas: estudio, voces, voz-a-voz, doblaje, efectos, historial, ajustes. */
'use strict';

const SonoraApp = (() => {
  const RUTAS = ['estudio', 'voces', 'voz-a-voz', 'doblaje', 'efectos', 'historial', 'ajustes'];
  const $ = (id) => document.getElementById(id);

  /* Estado del backend: 'desconocido' | 'online' | 'offline' | 'cpu' */
  const estadoBackend = { estado: 'desconocido', latenciaMs: null, modelos: [], gpu: null, ultimoHealth: null };
  let ultimoFocoDialogo = null;

  /* ---------- utilidades ---------- */
  function toast(mensaje, accion) {
    const el = $('toast');
    el.textContent = '';
    el.append(mensaje);
    if (accion) {
      const b = document.createElement('button');
      b.className = 'btn btn-fantasma btn-pequeno';
      b.type = 'button';
      b.textContent = accion.texto;
      b.addEventListener('click', () => { accion.alHacer(); el.hidden = true; });
      el.append(b);
    }
    el.hidden = false;
    clearTimeout(toast._t);
    toast._t = setTimeout(() => { el.hidden = true; }, 4000);
  }

  function confirmar(titulo, texto, textoBoton, conCheckbox, textoCheckbox) {
    return new Promise((resolver) => {
      $('titulo-confirmar').textContent = titulo;
      $('texto-confirmar').textContent = texto;
      $('btn-confirmar-aceptar').textContent = textoBoton;
      const wrap = $('check-confirmar-wrap');
      wrap.hidden = !conCheckbox;
      if (conCheckbox) {
        $('texto-check-confirmar').textContent = textoCheckbox || 'Borrar también el audio';
        $('check-confirmar').checked = true;
      }
      const fondo = $('dialogo-confirmar');
      fondo.hidden = false;
      ultimoFocoDialogo = document.activeElement;
      $('btn-confirmar-aceptar').focus();
      const cerrar = (valor) => {
        fondo.hidden = true;
        $('btn-confirmar-aceptar').onclick = null;
        $('btn-confirmar-cancelar').onclick = null;
        if (ultimoFocoDialogo) ultimoFocoDialogo.focus();
        resolver(valor ? { checkbox: $('check-confirmar').checked } : null);
      };
      $('btn-confirmar-aceptar').onclick = () => cerrar(true);
      $('btn-confirmar-cancelar').onclick = () => cerrar(false);
    });
  }

  function abrirDialogo(id) {
    ultimoFocoDialogo = document.activeElement;
    $(id).hidden = false;
    const foco = $(id).querySelector('input, button, select, textarea, a');
    if (foco) foco.focus();
  }
  function cerrarDialogo(id) {
    $(id).hidden = true;
    if (ultimoFocoDialogo) ultimoFocoDialogo.focus();
  }

  function formatearFecha(ts) {
    const d = new Date(ts);
    const hoy = new Date();
    const mismoDia = d.toDateString() === hoy.toDateString();
    const hora = d.toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' });
    if (mismoDia) return 'hoy ' + hora;
    return d.toLocaleDateString('es', { day: 'numeric', month: 'short' }) + ' ' + hora;
  }

  /* ---------- router ---------- */
  function rutaActual() {
    const h = location.hash.replace(/^#\/?/, '');
    return RUTAS.includes(h) ? h : 'estudio';
  }
  function mostrarPantalla(ruta) {
    RUTAS.forEach((r) => { $('pantalla-' + r).hidden = r !== ruta; });
    document.querySelectorAll('[data-ruta]').forEach((a) => {
      a.classList.toggle('activo', a.dataset.ruta === ruta);
    });
    document.title = 'Sonora — ' + ({ estudio: 'Estudio', voces: 'Voice Lab', 'voz-a-voz': 'Voz a voz', doblaje: 'Doblaje', efectos: 'Efectos de sonido', historial: 'Historial', ajustes: 'Ajustes' }[ruta]);
    window.scrollTo({ top: 0 });
    if (ruta === 'historial') SonoraPantallas.renderHistorial();
    if (ruta === 'voces') SonoraPantallas.renderVoces();
    if (ruta === 'ajustes') SonoraPantallas.renderAjustes();
    if (ruta === 'voz-a-voz') SonoraPantallas.renderSelectoresVoz();
  }
  window.addEventListener('hashchange', () => mostrarPantalla(rutaActual()));

  /* ---------- estado del backend ---------- */
  function pintarEstadoBackend() {
    const btn = $('estado-backend');
    const texto = $('estado-backend-texto');
    const banner = $('banner-backend');
    const sinUrl = !SonoraApi.configurado();
    if (sinUrl) {
      btn.dataset.estado = 'offline';
      texto.textContent = 'Sin configurar';
      $('banner-backend-detalle').textContent = 'Pega la URL del backend en Ajustes para generar audio. El historial local y los ajustes siguen disponibles.';
      banner.hidden = false;
    } else if (estadoBackend.estado === 'online') {
      btn.dataset.estado = estadoBackend.gpu === false ? 'cpu' : 'online';
      const modelo = (estadoBackend.modelos && estadoBackend.modelos[0]) || 'Backend';
      texto.textContent = (estadoBackend.gpu === false ? 'CPU · ' : 'En línea · ') + modelo;
      banner.hidden = true;
    } else {
      btn.dataset.estado = 'offline';
      texto.textContent = 'Sin conexión';
      $('banner-backend-detalle').textContent = 'Solo funcionan el historial local y los ajustes. Arranca el notebook de Kaggle y pega la URL en Ajustes.';
      banner.hidden = false;
    }
    aplicarDegradado();
  }

  async function comprobarBackend(mostrarToast) {
    if (!SonoraApi.configurado()) { estadoBackend.estado = 'desconocido'; pintarEstadoBackend(); return false; }
    try {
      const h = await SonoraApi.health();
      const eraOffline = estadoBackend.estado !== 'online';
      estadoBackend.estado = 'online';
      estadoBackend.latenciaMs = h.latenciaMs;
      estadoBackend.modelos = h.models_loaded || h.modelos || [];
      estadoBackend.gpu = h.gpu;
      estadoBackend.ultimoHealth = h;
      pintarEstadoBackend();
      if (mostrarToast) toast('Backend en línea' + (estadoBackend.modelos[0] ? ' · ' + estadoBackend.modelos[0] + ' listo' : ''));
      else if (eraOffline) toast('Backend en línea' + (estadoBackend.modelos[0] ? ' · ' + estadoBackend.modelos[0] + ' listo' : ''));
      return true;
    } catch (err) {
      estadoBackend.estado = 'offline';
      estadoBackend.latenciaMs = null;
      pintarEstadoBackend();
      if (mostrarToast) toast(SonoraApi.mensajeEnEspanol(err));
      return false;
    }
  }

  /* Degradado: con backend apagado, los botones GPU se deshabilitan CON el motivo. */
  function aplicarDegradado() {
    const online = estadoBackend.estado === 'online';
    const cpu = online && estadoBackend.gpu === false;
    const motivos = {
      'btn-generar': null, // depende del modelo elegido, se resuelve en validarEstudio()
      'btn-clonar': 'Clonar voz necesita GPU.',
      'btn-disenar': 'Diseñar voces necesita GPU.',
      'btn-convertir': 'La conversión de voz necesita GPU.',
      'btn-doblaje': 'El doblaje necesita GPU.',
      'btn-sfx': 'Los efectos de sonido necesitan GPU.',
    };
    Object.entries(motivos).forEach(([id, motivo]) => {
      const btn = $(id);
      if (!btn || id === 'btn-generar') return;
      const motivoEl = $('motivo-' + id.replace('btn-', ''));
      if (!online) {
        btn.disabled = true;
        if (motivoEl) { motivoEl.textContent = motivo + ' Arranca el backend GPU.'; motivoEl.hidden = false; }
      } else {
        if (motivoEl) motivoEl.hidden = true;
        // el botón se reactiva; cada pantalla revalida sus propios requisitos
        btn.disabled = false;
      }
    });
    if (cpu) {
      // Solo Kokoro (CPU) puede generar; el resto sigue deshabilitado con motivo.
      ['btn-clonar', 'btn-disenar', 'btn-convertir', 'btn-doblaje', 'btn-sfx'].forEach((id) => {
        const btn = $(id);
        if (btn) btn.disabled = true;
      });
    }
    validarEstudio();
    SonoraPantallas.validarClonar();
    // M8: al reconectar no basta con re-habilitar los botones: cada
    // pantalla revalida sus requisitos (muestra, consentimiento, audio).
    if (SonoraPantallas.validarSts) SonoraPantallas.validarSts();
  }

  /* ---------- Estudio TTS ---------- */
  const MODELOS = {
    kokoro: { nombre: 'Kokoro-82M', gpu: false, soporta: { estabilidad: false, similitud: false, estilo: false, velocidad: true }, ayuda: 'Kokoro-82M es rápido y corre en CPU. Español limitado a 3 voces fijas. No usa estabilidad, similitud ni estilo.' },
    'qwen3-tts-1.7b': { nombre: 'Qwen3-TTS 1.7B', gpu: true, soporta: { estabilidad: true, similitud: false, estilo: true, velocidad: true }, ayuda: 'Qwen3-TTS 1.7B clona con 3 s de muestra y habla español nativo. Necesita GPU.' },
    'qwen3-tts-0.6b': { nombre: 'Qwen3-TTS 0.6B', gpu: true, soporta: { estabilidad: true, similitud: false, estilo: true, velocidad: true }, ayuda: 'Qwen3-TTS 0.6B es la versión ligera de clonación. Necesita GPU.' },
    'qwen3-tts-1.7b-customvoice': { nombre: 'Qwen3-TTS CustomVoice', gpu: true, soporta: { estabilidad: true, similitud: false, estilo: true, velocidad: true }, ayuda: 'Qwen3-TTS CustomVoice: 9 voces fijas con control por instrucciones (estabilidad y estilo sí tienen efecto). Necesita GPU.' },
  };
  const MAX_CARACTERES = 10000;
  let vozActiva = { id: 'ef_dora', name: 'ef_dora', source: 'fija', model: 'kokoro', language: 'es' };
  let generando = false;

  function numeroEspanol(n, decimales) {
    return n.toLocaleString('es', { minimumFractionDigits: decimales, maximumFractionDigits: decimales });
  }

  function pintarVozActiva() {
    $('voz-actual-nombre').textContent = vozActiva.name;
    $('voz-actual-avatar').textContent = (vozActiva.name || 'V').trim().charAt(0).toUpperCase();
    const origen = { fija: 'Fija', clonada: 'Clonada', disenada: 'Diseñada' }[vozActiva.source] || vozActiva.source;
    $('voz-actual-meta').textContent = origen + ' · ' + (MODELOS[vozActiva.model] ? MODELOS[vozActiva.model].nombre : vozActiva.model) + ' · ' + (vozActiva.language || 'es');
    // El modelo del selector sigue a la voz cuando la voz lo exige.
    // (Antes las voces fijas iban siempre a Kokoro, incluidas las 9
    // de Qwen CustomVoice, que con model=kokoro daban 400.)
    if (vozActiva.model && MODELOS[vozActiva.model]) $('sel-modelo').value = vozActiva.model;
    else if (vozActiva.source === 'fija') $('sel-modelo').value = 'kokoro';
    aplicarModelo();
  }

  function aplicarModelo() {
    const modelo = MODELOS[$('sel-modelo').value] || MODELOS['qwen3-tts-1.7b'];
    $('ayuda-modelo').textContent = modelo.ayuda;
    // B4: lo que hace cada slider depende de la VOZ, no solo del modelo
    // del selector. Kokoro: solo velocidad. Qwen CustomVoice: velocidad
    // + estabilidad/estilo (vía instruct). Voces clonadas/diseñadas
    // (Qwen Base): solo velocidad (remuestreo real en el backend).
    // Similitud NO la expone ningún motor: siempre deshabilitada, con
    // el motivo, nunca en silencio.
    const esCustom = (vozActiva.model || '').includes('customvoice');
    const soporta = {
      estabilidad: esCustom,
      similitud: false,
      estilo: esCustom,
    };
    const motivos = {
      estabilidad: esCustom ? '' : (vozActiva.source === 'fija' ? 'Kokoro no usa estabilidad.' : 'La clonación Qwen3-TTS no expone estabilidad.'),
      similitud: 'Ningún motor expone similitud: la clonación usa siempre la referencia completa.',
      estilo: esCustom ? '' : (vozActiva.source === 'fija' ? 'Kokoro no usa estilo.' : 'La clonación Qwen3-TTS no expone estilo.'),
    };
    const mapa = { estabilidad: 'slider-estabilidad', similitud: 'slider-similitud', estilo: 'slider-estilo' };
    Object.entries(mapa).forEach(([clave, id]) => {
      const slider = $(id);
      slider.disabled = !soporta[clave];
      if (!soporta[clave]) $('ayuda-' + clave).textContent = motivos[clave];
    });
    validarEstudio();
  }

  function validarEstudio() {
    const texto = $('texto-tts').value.trim();
    const btn = $('btn-generar');
    const motivo = $('motivo-generar');
    const modelo = MODELOS[$('sel-modelo').value] || MODELOS['qwen3-tts-1.7b'];
    if (generando) return;
    if (!texto) {
      btn.disabled = true;
      motivo.textContent = 'Escribe un texto para generar.';
      motivo.hidden = false;
      return;
    }
    if (!SonoraApi.configurado()) {
      btn.disabled = true;
      motivo.textContent = 'Backend sin configurar: pega la URL en Ajustes.';
      motivo.hidden = false;
      return;
    }
    if (estadoBackend.estado !== 'online') {
      btn.disabled = true;
      motivo.textContent = 'Backend sin conexión: arranca el notebook y pega la URL en Ajustes.';
      motivo.hidden = false;
      return;
    }
    if (modelo.gpu && estadoBackend.gpu === false) {
      btn.disabled = true;
      motivo.textContent = modelo.nombre + ' necesita GPU y el backend actual es solo CPU. Elige Kokoro-82M o arranca el backend GPU.';
      motivo.hidden = false;
      return;
    }
    btn.disabled = false;
    motivo.hidden = true;
  }

  function actualizarContadorTexto() {
    const n = $('texto-tts').value.length;
    $('contador-texto').textContent = numeroEspanol(n, 0) + ' / 10.000 caracteres';
    $('aviso-largo').hidden = n <= MAX_CARACTERES;
    const err = $('error-texto');
    if (n > MAX_CARACTERES) { err.textContent = 'Texto largo (' + numeroEspanol(n, 0) + ' caracteres): se generará por bloques de hasta 2.000 caracteres.'; err.hidden = false; }
    else err.hidden = true;
    validarEstudio();
  }

  function trocearTexto(texto) {
    // Bloques de hasta 2.000 caracteres cortados por frase, para narración estable.
    const frases = texto.match(/[^.!?]+[.!?]+["»)]?\s*|[^.!?]+$/g) || [texto];
    const bloques = [];
    let actual = '';
    frases.forEach((f) => {
      if ((actual + f).length > 2000 && actual) { bloques.push(actual.trim()); actual = f; }
      else actual += f;
    });
    if (actual.trim()) bloques.push(actual.trim());
    return bloques;
  }

  function mostrarProgresoGenerar(texto, porcentaje) {
    $('progreso-generar').textContent = texto;
    $('progreso-generar').hidden = false;
    $('barra-progreso').hidden = false;
    $('barra-progreso-relleno').style.width = Math.round(porcentaje) + '%';
  }
  function ocultarProgresoGenerar() {
    $('progreso-generar').hidden = true;
    $('barra-progreso').hidden = true;
    $('barra-progreso-relleno').style.width = '0';
  }

  // M1: concatena varios WAV PCM en uno válido (una sola cabecera).
  // Sin esto, new Blob([wav1, wav2]) deja cabeceras intermedias y el
  // WAV resultante es inválido. Si algún bloque no se puede parsear,
  // se vuelve a la concatenación simple.
  async function combinarWav(blobs) {
    try {
      const partes = [];
      let canales = 1, sr = 24000, bits = 16;
      for (const b of blobs) {
        const buf = await b.arrayBuffer();
        const v = new DataView(buf);
        if (v.getUint32(0) !== 0x52494646) throw new Error('no wav');
        canales = v.getUint16(22, true);
        sr = v.getUint32(24, true);
        bits = v.getUint16(34, true);
        const bytes = new Uint8Array(buf);
        let idx = 12;
        let datos = null;
        while (idx + 8 <= bytes.length) {
          const id = String.fromCharCode(...bytes.slice(idx, idx + 4));
          const tam = v.getUint32(idx + 4, true);
          if (id === 'data') { datos = bytes.slice(idx + 8, idx + 8 + tam); break; }
          idx += 8 + tam + (tam % 2);
        }
        if (!datos) throw new Error('sin data');
        partes.push(datos);
      }
      const total = partes.reduce((a, p) => a + p.length, 0);
      const out = new Uint8Array(44 + total);
      const w = new DataView(out.buffer);
      const esc = (o, t) => { for (let i = 0; i < t.length; i++) out[o + i] = t.charCodeAt(i); };
      esc(0, 'RIFF'); w.setUint32(4, 36 + total, true); esc(8, 'WAVE');
      esc(12, 'fmt '); w.setUint32(16, 16, true); w.setUint16(20, 1, true);
      w.setUint16(22, canales, true); w.setUint32(24, sr, true);
      w.setUint32(28, sr * canales * bits / 8, true);
      w.setUint16(32, canales * bits / 8, true); w.setUint16(34, bits, true);
      esc(36, 'data'); w.setUint32(40, total, true);
      let off = 44;
      partes.forEach((p) => { out.set(p, off); off += p.length; });
      return new Blob([out], { type: 'audio/wav' });
    } catch (_) {
      return new Blob(blobs, { type: 'audio/wav' });
    }
  }

  async function generar() {
    const texto = $('texto-tts').value.trim();
    if (!texto || generando) return;
    const modelo = $('sel-modelo').value;
    const formato = $('sel-formato').value;
    const cuerpoBase = {
      voice_id: vozActiva.id,
      model: modelo,
      language: vozActiva.language || 'es',
      speed: Number($('slider-velocidad').value),
      format: formato,
      // M9: el interruptor de Ajustes por fin se envía.
      normalize: SonoraStore.leerAjustes().normalizar !== false,
    };
    // A7: si hay reglas de pronunciación locales, pedir al backend
    // que las aplique (antes nunca se enviaba dictionary_id).
    const reglas = await SonoraStore.listarDiccionarioLocal();
    if (reglas.length) cuerpoBase.dictionary_id = 'local';
    // B4: solo se envían los sliders que la voz activa soporta de
    // verdad; similitud no se envía nunca (el backend la rechaza).
    const esCustom = (vozActiva.model || '').includes('customvoice');
    if (esCustom) {
      cuerpoBase.stability = Number($('slider-estabilidad').value);
      cuerpoBase.style_exaggeration = Number($('slider-estilo').value);
    }
    const bloques = trocearTexto(texto);
    generando = true;
    $('btn-generar').disabled = true;
    $('btn-generar').textContent = 'Generando… 0%';
    try {
      const audios = [];
      let duracionTotal = 0;
      let res = null;
      for (let i = 0; i < bloques.length; i++) {
        const pct = Math.round((i / bloques.length) * 100);
        mostrarProgresoGenerar('Sintetizando… bloque ' + (i + 1) + ' de ' + bloques.length + ' (' + pct + '%)', pct);
        $('btn-generar').textContent = 'Generando… ' + pct + '%';
        res = await SonoraApi.tts({ ...cuerpoBase, text: bloques[i] });
        audios.push(res.blob);
        if (res.durationSeconds) duracionTotal += res.durationSeconds;
      }
      mostrarProgresoGenerar('Sintetizando… 100%', 100);
      const combinado = (formato === 'wav' && audios.length > 1)
        ? await combinarWav(audios)
        : new Blob(audios, { type: formato === 'wav' ? 'audio/wav' : 'audio/mpeg' });
      const item = {
        id: SonoraStore.nuevoId('hist'),
        remoteId: res && res.generationId ? 'gen_' + res.generationId : null,
        createdAt: Date.now(),
        type: 'tts',
        text: texto.slice(0, 200),
        textoCompleto: texto,
        voice_id: vozActiva.id,
        voiceName: vozActiva.name,
        model: modelo,
        duration_s: duracionTotal || null,
        characters: texto.length,
        format: formato,
        audioBlob: combinado,
      };
      await SonoraStore.guardarHistorial(item);
      $('resultado-vacio').hidden = true;
      const resEl = $('resultado-audio');
      resEl.hidden = false;
      resEl.innerHTML = '';
      const tarjeta = document.createElement('div');
      tarjeta.className = 'tarjeta-audio';
      const meta = document.createElement('p');
      meta.innerHTML = '';
      meta.textContent = vozActiva.name + ' · ' + MODELOS[modelo].nombre + (duracionTotal ? ' · ' + SonoraPlayer.formatoTiempo(duracionTotal) : '') + ' · ' + formatearFecha(Date.now());
      tarjeta.append(meta);
      resEl.append(tarjeta);
      await SonoraPlayer.cargar(combinado, vozActiva.name + ' · ' + MODELOS[modelo].nombre, 'sonora-' + item.id.slice(0, 8), formato);
      toast('Audio generado y guardado en el Historial.');
    } catch (err) {
      toast(SonoraApi.mensajeEnEspanol(err));
    } finally {
      generando = false;
      $('btn-generar').textContent = 'Generar';
      ocultarProgresoGenerar();
      validarEstudio();
    }
  }

  /* ---------- selector de voz (diálogo) ---------- */
  let filtroVoz = '';
  async function renderDialogoVoz(busqueda) {
    const lista = $('lista-dialogo-voz');
    const todas = await SonoraStore.listarTodasLasVoces();
    const q = (busqueda || '').toLowerCase();
    const filtradas = todas.filter((v) => {
      if (filtroVoz && v.source !== filtroVoz) return false;
      if (q && !(v.name || '').toLowerCase().includes(q)) return false;
      return true;
    });
    lista.innerHTML = '';
    if (!filtradas.length) {
      const p = document.createElement('p');
      p.className = 'vacio';
      p.textContent = 'No hay voces que coincidan con esa búsqueda.';
      lista.append(p);
      return;
    }
    filtradas.forEach((v) => {
      const fila = document.createElement('div');
      fila.className = 'fila-voz' + (v.id === vozActiva.id ? ' activa' : '');
      const avatar = document.createElement('span');
      avatar.className = 'avatar';
      avatar.setAttribute('aria-hidden', 'true');
      avatar.textContent = (v.name || 'V').trim().charAt(0).toUpperCase();
      const txt = document.createElement('span');
      txt.className = 'fila-voz-texto';
      const nombre = document.createElement('strong');
      nombre.textContent = v.name;
      const meta = document.createElement('span');
      const origen = { fija: 'Fija', clonada: 'Clonada', disenada: 'Diseñada' }[v.source] || v.source;
      meta.textContent = origen + ' · ' + (MODELOS[v.model] ? MODELOS[v.model].nombre : v.model) + ' · ' + (v.language || 'es');
      txt.append(nombre, meta);
      const acciones = document.createElement('span');
      acciones.className = 'fila-acciones';
      const btnElegir = document.createElement('button');
      btnElegir.className = 'btn btn-secundario btn-pequeno';
      btnElegir.type = 'button';
      btnElegir.textContent = v.id === vozActiva.id ? 'Activa' : 'Elegir';
      btnElegir.disabled = v.id === vozActiva.id;
      btnElegir.addEventListener('click', () => {
        vozActiva = { id: v.id, name: v.name, source: v.source, model: v.model, language: v.language || 'es' };
        SonoraStore.guardarAjustes({ vozActivaId: v.id, vozActivaNombre: v.name, vozActivaOrigen: v.source, vozActivaModelo: v.model });
        pintarVozActiva();
        cerrarDialogo('dialogo-voz');
        toast('Voz elegida: ' + v.name);
      });
      acciones.append(btnElegir);
      fila.append(avatar, txt, acciones);
      lista.append(fila);
    });
  }

  function conectarSliders() {
    const pares = [
      ['slider-estabilidad', 'valor-estabilidad', 2, (v) => v + ' — voz consistente, menos expresiva.'],
      ['slider-similitud', 'valor-similitud', 2, (v) => v + ' — parecido a la voz de referencia.'],
      ['slider-velocidad', 'valor-velocidad', 2, (v) => v + ' — ritmo normal.'],
      ['slider-estilo', 'valor-estilo', 2, (v) => v + ' — sin exageración.'],
    ];
    pares.forEach(([sliderId, valorId, decimales, ayuda]) => {
      const slider = $(sliderId);
      const valor = $(valorId);
      const actualizar = () => {
        const n = Number(slider.value);
        valor.textContent = numeroEspanol(n, decimales);
        slider.setAttribute('aria-valuetext', numeroEspanol(n, decimales) + '. ' + ayuda(numeroEspanol(n, decimales)));
      };
      slider.addEventListener('input', actualizar);
      actualizar();
    });
  }

  function init() {
    const ajustes = SonoraStore.leerAjustes();
    vozActiva = {
      id: ajustes.vozActivaId || 'ef_dora',
      name: ajustes.vozActivaNombre || 'ef_dora',
      source: ajustes.vozActivaOrigen || 'fija',
      model: ajustes.vozActivaModelo || 'kokoro',
      language: ajustes.vozActivaIdioma || 'es',
    };
    $('sel-formato').value = ajustes.formatoDefecto || 'mp3';
    pintarVozActiva();
    conectarSliders();
    actualizarContadorTexto();

    $('texto-tts').addEventListener('input', actualizarContadorTexto);
    $('sel-modelo').addEventListener('change', aplicarModelo);
    $('btn-generar').addEventListener('click', generar);
    $('btn-limpiar-texto').addEventListener('click', () => { $('texto-tts').value = ''; actualizarContadorTexto(); $('texto-tts').focus(); });
    $('btn-ejemplo').addEventListener('click', () => {
      $('texto-tts').value = 'En un lugar de la Mancha, de cuyo nombre no quiero acordarme, vivía un hidalgo que soñaba con molinos gigantes. Sonora convierte estas palabras en voz, con la voz que tú elijas.';
      actualizarContadorTexto();
    });
    $('btn-pegar').addEventListener('click', async () => {
      try {
        const t = await navigator.clipboard.readText();
        if (t) { $('texto-tts').value = t.slice(0, 10000); actualizarContadorTexto(); }
      } catch (_) { toast('No se pudo leer el portapapeles. Pega el texto con una pulsación larga.'); }
    });
    $('sel-formato').addEventListener('change', () => SonoraStore.guardarAjustes({ formatoDefecto: $('sel-formato').value }));

    $('btn-cambiar-voz').addEventListener('click', () => { abrirDialogo('dialogo-voz'); renderDialogoVoz(''); });
    $('btn-cerrar-dialogo-voz').addEventListener('click', () => cerrarDialogo('dialogo-voz'));
    $('buscar-dialogo-voz').addEventListener('input', (e) => renderDialogoVoz(e.target.value));
    document.querySelectorAll('[data-filtro-voz]').forEach((b) => b.addEventListener('click', () => {
      filtroVoz = b.dataset.filtroVoz;
      document.querySelectorAll('[data-filtro-voz]').forEach((x) => x.classList.toggle('activo', x === b));
      renderDialogoVoz($('buscar-dialogo-voz').value);
    }));
    $('dialogo-voz').addEventListener('click', (e) => { if (e.target === $('dialogo-voz')) cerrarDialogo('dialogo-voz'); });

    $('estado-backend').addEventListener('click', () => {
      $('detalle-estado').textContent = estadoBackend.estado === 'online' ? 'En línea' : (SonoraApi.configurado() ? 'Sin conexión' : 'Sin configurar');
      $('detalle-url').textContent = SonoraStore.leerAjustes().backendUrl || '—';
      $('detalle-latencia').textContent = estadoBackend.latenciaMs != null ? estadoBackend.latenciaMs + ' ms' : '—';
      $('detalle-modelos').textContent = estadoBackend.modelos.length ? estadoBackend.modelos.join(', ') : '—';
      $('detalle-gpu').textContent = estadoBackend.gpu == null ? '—' : (estadoBackend.gpu ? 'Sí' : 'No (solo CPU)');
      abrirDialogo('dialogo-backend');
    });
    $('btn-cerrar-dialogo-backend').addEventListener('click', () => cerrarDialogo('dialogo-backend'));
    $('dialogo-backend').addEventListener('click', (e) => { if (e.target === $('dialogo-backend')) cerrarDialogo('dialogo-backend'); });
    $('btn-reintentar-backend').addEventListener('click', () => comprobarBackend(true));

    $('btn-mas').addEventListener('click', () => { abrirDialogo('menu-mas'); $('btn-mas').setAttribute('aria-expanded', 'true'); });
    $('btn-cerrar-menu-mas').addEventListener('click', () => { cerrarDialogo('menu-mas'); $('btn-mas').setAttribute('aria-expanded', 'false'); });
    $('menu-mas').addEventListener('click', (e) => { if (e.target === $('menu-mas')) cerrarDialogo('menu-mas'); });
    document.querySelectorAll('#menu-mas .nav-item').forEach((a) => a.addEventListener('click', () => cerrarDialogo('menu-mas')));

    $('dialogo-confirmar').addEventListener('click', (e) => { if (e.target === $('dialogo-confirmar')) $('btn-confirmar-cancelar').click(); });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        ['dialogo-voz', 'dialogo-backend', 'menu-mas', 'dialogo-confirmar'].forEach((id) => { if (!$(id).hidden) cerrarDialogo(id); });
      }
    });

    mostrarPantalla(rutaActual());
    pintarEstadoBackend();
    comprobarBackend(false);
    setInterval(() => { if (!document.hidden) comprobarBackend(false); }, 300000);
  }

  return {
    init, toast, confirmar, abrirDialogo, cerrarDialogo,
    formatearFecha, comprobarBackend, pintarEstadoBackend,
    get vozActiva() { return vozActiva; },
    setVozActiva(v) {
      vozActiva = v;
      SonoraStore.guardarAjustes({
        vozActivaId: v.id, vozActivaNombre: v.name,
        vozActivaOrigen: v.source, vozActivaModelo: v.model,
        vozActivaIdioma: v.language || 'es',
      });
      pintarVozActiva();
    },
    numeroEspanol,
  };
})();

document.addEventListener('DOMContentLoaded', () => {
  SonoraPantallas.init();
  SonoraApp.init();
});
