/* Sonora — pantallas: Voice Lab, Voz a voz, Doblaje, Efectos, Historial, Ajustes. */
'use strict';

const SonoraPantallas = (() => {
  const $ = (id) => document.getElementById(id);
  let muestraAudio = null; // { file, durationS, nombre }
  let audioSts = null;
  let mediaRecorder = null;
  let grabando = null; // 'muestra' | null
  let chunksGrabacion = [];
  let intervaloGrabacion = null;
  let segundosGrabacion = 0;

  /* ---------- validación de audio ---------- */
  function validarArchivoAudio(file, minS, maxS, maxMB) {
    const tipos = ['audio/wav', 'audio/mpeg', 'audio/flac', 'audio/ogg', 'audio/x-wav', 'audio/mp4', 'audio/webm'];
    const extOk = /\.(wav|mp3|flac|ogg|webm)$/i.test(file.name || '');
    if (!tipos.includes(file.type) && !extOk) return 'Formato no soportado. Usa WAV, MP3, FLAC, OGG o WebM.';
    if (file.size > maxMB * 1024 * 1024) return 'El archivo supera los ' + maxMB + ' MB.';
    return null;
  }
  function duracionDeAudio(file) {
    return new Promise((resolver) => {
      const url = URL.createObjectURL(file);
      const a = new Audio();
      a.preload = 'metadata';
      a.onloadedmetadata = () => { URL.revokeObjectURL(url); resolver(a.duration || 0); };
      a.onerror = () => { URL.revokeObjectURL(url); resolver(0); };
      a.src = url;
    });
  }
  function formatoDuracion(s) {
    if (!s) return 'duración desconocida';
    return Math.round(s) + ' s';
  }

  /* ---------- Voice Lab: clonar ---------- */
  function validarClonar() {
    const btn = $('btn-clonar');
    const motivo = $('motivo-clonar');
    const okConsent = $('check-consentimiento').checked;
    const okNombre = $('nombre-voz').value.trim().length > 0;
    const okMuestra = Boolean(muestraAudio);
    const online = SonoraApi.configurado();
    if (!okConsent || !okNombre || !okMuestra) {
      btn.disabled = true;
      const faltan = [];
      if (!okNombre) faltan.push('ponle un nombre a la voz');
      if (!okMuestra) faltan.push('añade una muestra válida (3 s – 2 min)');
      if (!okConsent) faltan.push('marca el consentimiento');
      motivo.textContent = 'Para clonar: ' + faltan.join(', ') + '.';
      motivo.hidden = false;
      return false;
    }
    if (!online) {
      btn.disabled = true;
      motivo.textContent = 'Backend sin configurar: pega la URL en Ajustes.';
      motivo.hidden = false;
      return false;
    }
    btn.disabled = false;
    motivo.hidden = true;
    return true;
  }

  async function recibirMuestra(file) {
    const errEl = $('error-muestra');
    const infoEl = $('info-muestra');
    errEl.hidden = true;
    infoEl.hidden = true;
    const errFormato = validarArchivoAudio(file, 3, 120, 25);
    if (errFormato) { errEl.textContent = errFormato; errEl.hidden = false; muestraAudio = null; validarClonar(); return; }
    const dur = await duracionDeAudio(file);
    if (!dur) {
      errEl.textContent = 'No se pudo leer la duración de este audio. Sube un WAV o MP3 válido (la grabación WebM también vale).';
      errEl.hidden = false;
      muestraAudio = null;
      validarClonar();
      return;
    }
    if (dur < 3 || dur > 120) {
      errEl.textContent = 'La muestra dura ' + formatoDuracion(dur) + '. Tiene que durar entre 3 s y 2 min.';
      errEl.hidden = false;
      muestraAudio = null;
      validarClonar();
      return;
    }
    muestraAudio = { file, durationS: dur, nombre: file.name };
    infoEl.textContent = 'Audio: ' + formatoDuracion(dur) + ' · limpio · ' + file.name;
    infoEl.hidden = false;
    validarClonar();
  }

  function iniciarGrabacion() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      SonoraApp.toast('Este dispositivo o navegador no permite grabar con el micrófono. Sube un archivo.');
      return;
    }
    navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
      chunksGrabacion = [];
      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.ondataavailable = (e) => { if (e.data.size) chunksGrabacion.push(e.data); };
      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        clearInterval(intervaloGrabacion);
        const blob = new Blob(chunksGrabacion, { type: mediaRecorder.mimeType || 'audio/webm' });
        const file = new File([blob], 'muestra-grabada.webm', { type: blob.type });
        await recibirMuestra(file);
      };
      mediaRecorder.start();
      grabando = 'muestra';
      segundosGrabacion = 0;
      $('btn-grabar').textContent = 'Parar grabación';
      $('tiempo-grabacion').hidden = false;
      intervaloGrabacion = setInterval(() => {
        segundosGrabacion++;
        $('tiempo-grabacion').textContent = Math.floor(segundosGrabacion / 60) + ':' + String(segundosGrabacion % 60).padStart(2, '0');
        if (segundosGrabacion >= 120) pararGrabacion();
      }, 1000);
    }).catch(() => SonoraApp.toast('No se pudo acceder al micrófono. Revisa el permiso del navegador.'));
  }
  function pararGrabacion() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop();
    grabando = null;
    $('btn-grabar').textContent = 'Grabar muestra';
    $('tiempo-grabacion').hidden = true;
  }

  async function clonarVoz() {
    if (!validarClonar() || !muestraAudio) return;
    const nombre = $('nombre-voz').value.trim();
    const btn = $('btn-clonar');
    btn.disabled = true;
    btn.textContent = 'Clonando…';
    try {
      const fd = new FormData();
      fd.append('audio', muestraAudio.file);
      fd.append('name', nombre);
      fd.append('language', $('sel-idioma-muestra').value);
      fd.append('consent_note', 'Consentimiento confirmado en Voice Lab por el dueño de la voz, ' + new Date().toISOString() + '.');
      const res = await SonoraApi.clonarVoz(fd);
      const voz = {
        id: res.voice_id,
        name: res.name || nombre,
        source: 'clonada',
        model: res.model || 'qwen3-tts-1.7b',
        language: $('sel-idioma-muestra').value,
        createdAt: Date.now(),
        consentNote: 'Consentimiento confirmado en Voice Lab.',
        referenceDurationS: res.reference_duration_s || muestraAudio.durationS,
        favorite: false,
      };
      await SonoraStore.guardarVoz(voz);
      // Muestra de prueba: la puerta de narration_voice_design — solo la muestra aprobada es «la voz».
      const area = $('muestra-prueba');
      area.hidden = false;
      area.innerHTML = '';
      const tarjeta = document.createElement('div');
      tarjeta.className = 'tarjeta-audio';
      const p = document.createElement('p');
      p.textContent = 'Voz creada. Escucha la muestra de prueba y apruébala por oído antes de usarla.';
      tarjeta.append(p);
      area.append(tarjeta);
      try {
        const preview = await SonoraApi.vistaPreviaVoz(voz.id);
        const au = document.createElement('audio');
        au.controls = true;
        au.src = URL.createObjectURL(preview);
        tarjeta.append(au);
      } catch (_) {
        const aviso = document.createElement('p');
        aviso.className = 'ayuda';
        aviso.textContent = 'No se pudo cargar la muestra de prueba. Genera un texto en el Estudio con esta voz para escucharla.';
        tarjeta.append(aviso);
      }
      const btnAprobar = document.createElement('button');
      btnAprobar.className = 'btn btn-primario';
      btnAprobar.type = 'button';
      btnAprobar.textContent = 'Aprobar y usar en el Estudio';
      btnAprobar.addEventListener('click', async () => {
        voz.aprobada = true;
        await SonoraStore.guardarVoz(voz);
        SonoraApp.setVozActiva({ id: voz.id, name: voz.name, source: 'clonada', model: voz.model, language: voz.language });
        location.hash = '#/estudio';
        SonoraApp.toast('Voz aprobada: ' + voz.name);
      });
      tarjeta.append(btnAprobar);
      muestraAudio = null;
      $('info-muestra').hidden = true;
      await renderVoces();
      SonoraApp.toast('Voz clonada: ' + voz.name);
    } catch (err) {
      SonoraApp.toast(SonoraApi.mensajeEnEspanol(err));
    } finally {
      btn.disabled = false;
      btn.textContent = 'Clonar voz';
      validarClonar();
    }
  }

  /* ---------- Voice Lab: diseñar ---------- */
  async function disenarVoz() {
    const prompt = $('prompt-diseno').value.trim();
    const errEl = $('error-diseno');
    errEl.hidden = true;
    if (prompt.length < 20) { errEl.textContent = 'Describe la voz con al menos 20 caracteres.'; errEl.hidden = false; return; }
    const btn = $('btn-disenar');
    btn.disabled = true;
    btn.textContent = 'Generando…';
    try {
      const res = await SonoraApi.disenarVoz({ prompt, language: 'es', num_previews: 3 });
      const area = $('candidatas-diseno');
      area.innerHTML = '';
      (res.candidates || []).forEach(async (c) => {
        const tarjeta = document.createElement('div');
        tarjeta.className = 'tarjeta-audio';
        const p = document.createElement('p');
        p.textContent = c.description || 'Candidata';
        tarjeta.append(p);
        if (c.preview_url) {
          const au = document.createElement('audio');
          au.controls = true;
          try {
            au.src = await SonoraApi.blobUrl(c.preview_url);
          } catch (_) {
            const aviso = document.createElement('p');
            aviso.className = 'ayuda';
            aviso.textContent = 'No se pudo cargar esta muestra.';
            tarjeta.append(aviso);
          }
          tarjeta.append(au);
        }
        const guardar = document.createElement('button');
        guardar.className = 'btn btn-secundario';
        guardar.type = 'button';
        guardar.textContent = 'Guardar esta voz';
        guardar.addEventListener('click', async () => {
          const nombre = prompt.slice(0, 40) || 'Voz diseñada';
          try {
            const guardada = await SonoraApi.guardarCandidata(c.candidate_id, nombre);
            await SonoraStore.guardarVoz({
              id: guardada.voice_id, name: guardada.name || nombre, source: 'disenada',
              model: 'qwen3-tts-1.7b', language: 'es', createdAt: Date.now(), favorite: false,
            });
            await renderVoces();
            SonoraApp.toast('Voz diseñada guardada: ' + nombre);
          } catch (err) { SonoraApp.toast(SonoraApi.mensajeEnEspanol(err)); }
        });
        tarjeta.append(guardar);
        area.append(tarjeta);
      });
      if (!(res.candidates || []).length) SonoraApp.toast('El backend no devolvió candidatas.');
    } catch (err) {
      SonoraApp.toast(SonoraApi.mensajeEnEspanol(err));
    } finally {
      btn.disabled = false;
      btn.textContent = 'Generar 3 muestras';
    }
  }

  /* ---------- Voice Lab: lista ---------- */
  async function renderVoces() {
    const q = ($('buscar-voces').value || '').toLowerCase();
    const locales = await SonoraStore.listarVocesLocales();
    const porId = new Map();
    // Base: voces fijas locales (Kokoro + Qwen CustomVoice).
    (await SonoraStore.listarTodasLasVoces()).forEach((v) => porId.set(v.id, { ...v, remota: false }));
    // Biblioteca del backend, si hay conexión: trae favoritas y las
    // clonadas/diseñadas que este dispositivo aún no conoce.
    try {
      const bib = await SonoraApi.listarBiblioteca();
      (bib.voices || []).forEach((v) => {
        const id = v.voice_id;
        const prev = porId.get(id) || {};
        porId.set(id, {
          ...prev,
          id,
          name: v.name || id,
          source: v.source === 'kokoro' || v.source === 'qwen-customvoice' ? 'fija' : v.source,
          model: v.source === 'kokoro' ? 'kokoro' : (v.source === 'qwen-customvoice' ? 'qwen3-tts-1.7b-customvoice' : (prev.model || 'qwen3-tts-1.7b')),
          language: v.language || prev.language || 'es',
          favorite: Boolean(v.favorite || prev.favorite),
          remota: true,
        });
      });
    } catch (_) { /* sin backend: solo voces locales */ }
    locales.forEach((v) => {
      const prev = porId.get(v.id) || {};
      porId.set(v.id, { ...prev, ...v, favorite: Boolean(v.favorite || prev.favorite) });
    });
    const voces = [...porId.values()];
    const filtradas = voces.filter((v) => !q || (v.name || '').toLowerCase().includes(q));
    $('contador-voces').textContent = String(voces.length);
    $('voces-vacio').hidden = voces.length > 0;
    const lista = $('lista-voces');
    lista.innerHTML = '';
    filtradas.forEach((v) => {
      const fila = document.createElement('div');
      fila.className = 'fila-voz';
      const avatar = document.createElement('span');
      avatar.className = 'avatar';
      avatar.setAttribute('aria-hidden', 'true');
      avatar.textContent = (v.name || 'V').trim().charAt(0).toUpperCase();
      const txt = document.createElement('span');
      txt.className = 'fila-voz-texto';
      const nombre = document.createElement('strong');
      nombre.textContent = v.name + (v.aprobada ? '' : (v.source === 'clonada' || v.source === 'disenada' ? ' (sin aprobar)' : ''));
      const meta = document.createElement('span');
      const origen = { clonada: 'Clonada', disenada: 'Diseñada', fija: 'Fija' }[v.source] || v.source;
      meta.textContent = origen + ' · ' + v.model + ' · ' + (v.language || 'es') + (v.referenceDurationS ? ' · muestra ' + Math.round(v.referenceDurationS) + ' s' : '') + ' · ' + SonoraApp.formatearFecha(v.createdAt || Date.now());
      txt.append(nombre, meta);
      const acciones = document.createElement('span');
      acciones.className = 'fila-acciones';
      const btnFav = document.createElement('button');
      btnFav.className = 'btn btn-fantasma btn-pequeno';
      btnFav.type = 'button';
      btnFav.textContent = v.favorite ? '★' : '☆';
      btnFav.setAttribute('aria-label', (v.favorite ? 'Quitar de favoritas: ' : 'Marcar como favorita: ') + v.name);
      btnFav.addEventListener('click', async () => {
        const nuevo = !v.favorite;
        if (v.source === 'clonada' || v.source === 'disenada') {
          try { await SonoraApi.favoritoVoz(v.id); } catch (err) { SonoraApp.toast(SonoraApi.mensajeEnEspanol(err)); return; }
        }
        v.favorite = nuevo;
        await SonoraStore.guardarVoz(v);
        renderVoces();
      });
      const btnUsar = document.createElement('button');
      btnUsar.className = 'btn btn-secundario btn-pequeno';
      btnUsar.type = 'button';
      btnUsar.textContent = 'Usar';
      btnUsar.addEventListener('click', () => {
        SonoraApp.setVozActiva({ id: v.id, name: v.name, source: v.source, model: v.model, language: v.language || 'es' });
        location.hash = '#/estudio';
      });
      const btnRenombrar = document.createElement('button');
      btnRenombrar.className = 'btn btn-fantasma btn-pequeno';
      btnRenombrar.type = 'button';
      btnRenombrar.textContent = 'Renombrar';
      btnRenombrar.addEventListener('click', async () => {
        const nuevo = window.prompt('Nuevo nombre para la voz:', v.name);
        if (nuevo && nuevo.trim() && nuevo.trim() !== v.name) {
          v.name = nuevo.trim();
          await SonoraStore.guardarVoz(v);
          renderVoces();
        }
      });
      acciones.append(btnFav, btnUsar, btnRenombrar);
      if (v.source === 'clonada' || v.source === 'disenada') {
        const btnBorrar = document.createElement('button');
        btnBorrar.className = 'btn btn-peligro btn-pequeno';
        btnBorrar.type = 'button';
        btnBorrar.textContent = 'Borrar';
        btnBorrar.addEventListener('click', async () => {
          const r = await SonoraApp.confirmar('Borrar voz', 'Borrar "' + v.name + '" y su audio de referencia. Esta acción no se puede deshacer.', 'Borrar', false);
          if (!r) return;
          // A7: primero el backend; si falla, la voz local se queda
          // y se avisa, en vez de borrar en local y mentir con el toast.
          try { await SonoraApi.borrarVoz(v.id); } catch (err) {
            SonoraApp.toast('No se pudo borrar en el backend: ' + SonoraApi.mensajeEnEspanol(err));
            return;
          }
          await SonoraStore.borrarVozLocal(v.id);
          renderVoces();
          SonoraApp.toast('Voz borrada: ' + v.name);
        });
        acciones.append(btnBorrar);
      }
      fila.append(avatar, txt, acciones);
      lista.append(fila);
    });
  }

  /* ---------- selectores de voz (Voz a voz / Doblaje) ---------- */
  async function renderSelectoresVoz() {
    const voces = await SonoraStore.listarTodasLasVoces();
    const selDestino = $('sel-voz-destino');
    const actualDestino = selDestino.value;
    selDestino.innerHTML = '';
    voces.forEach((v) => {
      const o = document.createElement('option');
      o.value = v.id;
      o.textContent = v.name + ' (' + v.source + ')';
      selDestino.append(o);
    });
    if (actualDestino) selDestino.value = actualDestino;
    const selDoblaje = $('sel-voz-doblaje');
    const actualDoblaje = selDoblaje.value;
    selDoblaje.innerHTML = '';
    const o0 = document.createElement('option');
    o0.value = 'clone-original';
    o0.textContent = 'Clonar la original';
    selDoblaje.append(o0);
    voces.forEach((v) => {
      const o = document.createElement('option');
      o.value = v.id;
      o.textContent = v.name;
      selDoblaje.append(o);
    });
    if (actualDoblaje) selDoblaje.value = actualDoblaje;
  }

  /* ---------- Voz a voz ---------- */
  function validarSts() {
    const btn = $('btn-convertir');
    const motivo = $('motivo-sts');
    if (!audioSts) { btn.disabled = true; motivo.textContent = 'Sube un audio para convertir.'; motivo.hidden = false; return false; }
    if (!SonoraApi.configurado()) { btn.disabled = true; motivo.textContent = 'Backend sin configurar: pega la URL en Ajustes.'; motivo.hidden = false; return false; }
    btn.disabled = false;
    motivo.hidden = true;
    return true;
  }

  async function convertir() {
    if (!validarSts() || !audioSts) return;
    const btn = $('btn-convertir');
    btn.disabled = true;
    btn.textContent = 'Convirtiendo…';
    try {
      const fd = new FormData();
      fd.append('audio', audioSts.file);
      fd.append('target_voice_id', $('sel-voz-destino').value);
      fd.append('method', $('sel-metodo-sts').value);
      const res = await SonoraApi.vozAVoz(fd);
      const area = $('resultado-sts');
      area.innerHTML = '';
      const tarjeta = document.createElement('div');
      tarjeta.className = 'tarjeta-audio';
      const p = document.createElement('p');
      p.textContent = 'Método usado: ' + ($('sel-metodo-sts').value === 'voice-conversion' ? 'conversión de voz' : 'texto a voz (pierde la interpretación)');
      tarjeta.append(p);
      area.append(tarjeta);
      const item = {
        id: SonoraStore.nuevoId('hist'), createdAt: Date.now(), type: 'sts',
        text: 'Voz a voz → ' + $('sel-voz-destino').selectedOptions[0].textContent,
        voice_id: $('sel-voz-destino').value, voiceName: $('sel-voz-destino').selectedOptions[0].textContent,
        model: 'sts', duration_s: null, characters: 0, format: 'mp3', audioBlob: res.blob,
      };
      await SonoraStore.guardarHistorial(item);
      await SonoraPlayer.cargar(res.blob, 'Voz a voz · ' + item.voiceName, 'sonora-sts-' + item.id.slice(0, 8), 'mp3');
      SonoraApp.toast('Conversión lista y guardada en el Historial.');
    } catch (err) {
      SonoraApp.toast(SonoraApi.mensajeEnEspanol(err));
    } finally {
      btn.disabled = false;
      btn.textContent = 'Convertir';
      validarSts();
    }
  }

  /* ---------- Doblaje ---------- */
  let trabajoDoblaje = null; // { jobId, idioma }
  let intervaloDoblaje = null;

  async function iniciarDoblaje() {
    const file = $('input-doblaje').files[0];
    if (!file) { SonoraApp.toast('Sube primero un audio o vídeo.'); return; }
    const btn = $('btn-doblaje');
    btn.disabled = true;
    btn.textContent = 'Empezando…';
    try {
      const fd = new FormData();
      fd.append('media', file);
      fd.append('source_language', $('sel-origen-doblaje').value);
      fd.append('target_languages', $('sel-destino-doblaje').value);
      fd.append('voice_mode', $('sel-voz-doblaje').value);
      fd.append('keep_background_audio', String($('check-fondo').checked));
      const res = await SonoraApi.iniciarDoblaje(fd);
      trabajoDoblaje = { jobId: res.job_id, idioma: $('sel-destino-doblaje').value, esVideo: file.type.startsWith('video/') || /\.(mp4|webm)$/i.test(file.name || '') };
      $('doblaje-vacio').hidden = true;
      $('doblaje-progreso').hidden = false;
      intervaloDoblaje = setInterval(consultarDoblaje, 5000);
      consultarDoblaje();
      SonoraApp.toast('Doblaje en curso.');
    } catch (err) {
      SonoraApp.toast(SonoraApi.mensajeEnEspanol(err));
    } finally {
      btn.disabled = false;
      btn.textContent = 'Empezar doblaje';
    }
  }

  async function consultarDoblaje() {
    if (!trabajoDoblaje) return;
    try {
      const estado = await SonoraApi.estadoDoblaje(trabajoDoblaje.jobId);
      // B2: el backend guarda status 'done' y etapa 'synthesize'
      // (antes 'synthesize-{idioma}'); aquí se traduce a lo que
      // muestra la pantalla: 'completed' y las 4 etapas.
      const terminado = estado.status === 'completed' || estado.status === 'done';
      const etapa = (estado.stage || '').startsWith('synthesize') ? 'synthesize' : estado.stage;
      const etapas = ['transcribe', 'translate', 'synthesize', 'mix'];
      const indiceActual = etapas.indexOf(etapa);
      document.querySelectorAll('#etapas-doblaje li').forEach((li) => {
        const i = etapas.indexOf(li.dataset.etapa);
        li.classList.toggle('hecha', terminado || i < indiceActual);
        li.classList.toggle('en-curso', !terminado && i === indiceActual);
      });
      const pct = Math.round((estado.progress || 0) * 100);
      $('barra-doblaje-relleno').style.width = pct + '%';
      $('texto-progreso-doblaje').textContent = (terminado ? 'Doblaje terminado' : 'Etapa: ' + etapa) + ' · ' + pct + '%';
      const area = $('segmentos-doblaje');
      area.innerHTML = '';
      (estado.segments || []).forEach((seg, n) => {
        const div = document.createElement('div');
        div.className = 'segmento';
        const inicio = SonoraPlayer.formatoTiempo((seg.start_ms || 0) / 1000);
        const fin = SonoraPlayer.formatoTiempo((seg.end_ms || 0) / 1000);
        const linea = document.createElement('span');
        linea.className = 'segmento-texto';
        linea.textContent = inicio + '–' + fin + ' «' + (seg.source_text || '') + '» → «' + (seg.translated_text || '') + '»';
        div.append(linea);
        const ta = document.createElement('textarea');
        ta.className = 'input';
        ta.rows = 2;
        ta.value = seg.translated_text || '';
        ta.setAttribute('aria-label', 'Traducción del segmento ' + (n + 1));
        const btnRegen = document.createElement('button');
        btnRegen.className = 'btn btn-secundario btn-pequeno';
        btnRegen.type = 'button';
        btnRegen.textContent = 'Regenerar este segmento';
        btnRegen.addEventListener('click', async () => {
          try {
            await SonoraApi.editarSegmentoDoblaje(trabajoDoblaje.jobId, n, ta.value, trabajoDoblaje.idioma);
            SonoraApp.toast('Segmento ' + (n + 1) + ' regenerado.');
            consultarDoblaje();
          } catch (err) { SonoraApp.toast(SonoraApi.mensajeEnEspanol(err)); }
        });
        div.append(ta, btnRegen);
        area.append(div);
      });
      if (terminado) {
        clearInterval(intervaloDoblaje);
        const btnDl = $('btn-descargar-doblaje');
        btnDl.hidden = false;
        btnDl.textContent = trabajoDoblaje.esVideo ? 'Descargar vídeo doblado' : 'Descargar audio doblado';
        btnDl.onclick = async () => {
          // A4: descarga con token (fetch), formato según la entrada:
          // mp4 si era vídeo, mp3 si era audio (antes siempre mp4
          // y sin token: 400 con audio, 401 con token).
          const formato = trabajoDoblaje.esVideo ? 'mp4' : 'mp3';
          try {
            const blob = await SonoraApi.descargarDoblaje(trabajoDoblaje.jobId, trabajoDoblaje.idioma, formato);
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'doblaje-' + trabajoDoblaje.jobId + '.' + formato;
            a.click();
          } catch (err) { SonoraApp.toast(SonoraApi.mensajeEnEspanol(err)); }
        };
        SonoraApp.toast('Doblaje terminado. Puedes descargarlo.');
      }
      if (estado.status === 'failed') {
        clearInterval(intervaloDoblaje);
        SonoraApp.toast('El doblaje falló: ' + (estado.error || 'error desconocido'));
      }
    } catch (err) {
      clearInterval(intervaloDoblaje);
      SonoraApp.toast(SonoraApi.mensajeEnEspanol(err));
    }
  }

  /* ---------- Efectos de sonido ---------- */
  async function generarSfx() {
    const prompt = $('texto-sfx').value.trim();
    if (!prompt) { SonoraApp.toast('Describe el sonido que quieres generar.'); return; }
    const btn = $('btn-sfx');
    btn.disabled = true;
    btn.textContent = 'Generando…';
    try {
      const res = await SonoraApi.sfx({
        prompt,
        duration_s: Number($('slider-duracion-sfx').value),
        num_variants: Number($('sel-variantes-sfx').value),
        model: 'stable-audio-open-1.0',
      });
      const area = $('resultados-sfx');
      area.innerHTML = '';
      const variantes = res.variants || res.audios || (res.blob ? [res.blob] : []);
      variantes.forEach(async (v, i) => {
        const tarjeta = document.createElement('div');
        tarjeta.className = 'tarjeta-audio';
        const p = document.createElement('p');
        p.textContent = 'Variante ' + (i + 1) + ' · ' + $('slider-duracion-sfx').value + ' s';
        tarjeta.append(p);
        const au = document.createElement('audio');
        au.controls = true;
        if (v instanceof Blob) au.src = URL.createObjectURL(v);
        else if (typeof v === 'string') au.src = v;
        else if (v && v.audio_url) {
          try { au.src = await SonoraApi.blobUrl(v.audio_url); }
          catch (_) { au.src = v.audio_url; }
        }
        tarjeta.append(au);
        const dl = document.createElement('button');
        dl.className = 'btn btn-secundario btn-pequeno';
        dl.type = 'button';
        dl.textContent = 'Descargar';
        dl.addEventListener('click', () => {
          const a = document.createElement('a');
          a.href = au.src;
          a.download = 'efecto-' + (i + 1) + '.wav';
          a.click();
        });
        tarjeta.append(dl);
        area.append(tarjeta);
      });
      if (!variantes.length) SonoraApp.toast('El backend no devolvió audio.');
      else SonoraApp.toast('Efecto generado.');
    } catch (err) {
      SonoraApp.toast(SonoraApi.mensajeEnEspanol(err));
    } finally {
      btn.disabled = false;
      btn.textContent = 'Generar efecto';
    }
  }

  /* ---------- Historial ---------- */
  async function renderHistorial() {
    const q = ($('buscar-historial').value || '').toLowerCase();
    const tipo = $('filtro-tipo').value;
    const items = await SonoraStore.listarHistorialLocal();
    const filtrados = items.filter((it) => {
      if (tipo && it.type !== tipo) return false;
      if (q && !((it.text || '') + ' ' + (it.voiceName || '')).toLowerCase().includes(q)) return false;
      return true;
    });
    $('historial-vacio').hidden = filtrados.length > 0;
    const lista = $('lista-historial');
    lista.innerHTML = '';
    let caracteres = 0;
    let segundos = 0;
    const ahora = new Date();
    items.forEach((it) => {
      const f = new Date(it.createdAt || 0);
      if (f.getFullYear() === ahora.getFullYear() && f.getMonth() === ahora.getMonth()) {
        caracteres += it.characters || 0; segundos += it.duration_s || 0;
      }
    });
    $('contador-uso').textContent = 'Este mes: ' + SonoraApp.numeroEspanol(caracteres, 0) + ' caracteres · ' + Math.round(segundos / 60) + ' min de audio';
    filtrados.forEach((it) => {
      const fila = document.createElement('div');
      fila.className = 'fila-historial';
      const txt = document.createElement('span');
      txt.className = 'fila-historial-texto';
      const titulo = document.createElement('strong');
      titulo.textContent = (it.text || '(sin texto)').slice(0, 80);
      const meta = document.createElement('span');
      const tipoNombre = { tts: 'Texto a voz', sfx: 'Efecto', sts: 'Voz a voz', dubbing: 'Doblaje' }[it.type] || it.type;
      meta.textContent = tipoNombre + ' · ' + (it.voiceName || '') + ' · ' + (it.model || '') + (it.duration_s ? ' · ' + SonoraPlayer.formatoTiempo(it.duration_s) : '') + ' · ' + SonoraApp.formatearFecha(it.createdAt);
      txt.append(titulo, meta);
      const acciones = document.createElement('span');
      acciones.className = 'fila-acciones';
      if (it.audioBlob) {
        const btnPlay = document.createElement('button');
        btnPlay.className = 'btn btn-icono btn-secundario';
        btnPlay.type = 'button';
        btnPlay.textContent = '▸';
        btnPlay.setAttribute('aria-label', 'Reproducir ' + (it.text || '').slice(0, 40));
        btnPlay.addEventListener('click', () => SonoraPlayer.cargar(it.audioBlob, (it.voiceName || '') + ' · ' + (it.model || ''), 'sonora-' + it.id.slice(0, 8), it.format || 'mp3').then(() => SonoraPlayer.reproducir()));
        const btnDl = document.createElement('button');
        btnDl.className = 'btn btn-secundario btn-pequeno';
        btnDl.type = 'button';
        btnDl.textContent = 'Descargar';
        btnDl.addEventListener('click', () => {
          const a = document.createElement('a');
          a.href = URL.createObjectURL(it.audioBlob);
          a.download = 'sonora-' + it.id.slice(0, 8) + '.' + (it.format || 'mp3');
          a.click();
        });
        acciones.append(btnPlay, btnDl);
      }
      if (it.type === 'tts' && it.textoCompleto) {
        const btnRepetir = document.createElement('button');
        btnRepetir.className = 'btn btn-fantasma btn-pequeno';
        btnRepetir.type = 'button';
        btnRepetir.textContent = 'Repetir';
        btnRepetir.addEventListener('click', () => {
          $('texto-tts').value = it.textoCompleto;
          location.hash = '#/estudio';
          SonoraApp.toast('Texto cargado en el Estudio.');
        });
        acciones.append(btnRepetir);
      }
      const btnBorrar = document.createElement('button');
      btnBorrar.className = 'btn btn-peligro btn-pequeno';
      btnBorrar.type = 'button';
      btnBorrar.textContent = 'Borrar';
      btnBorrar.addEventListener('click', async () => {
        const r = await SonoraApp.confirmar('Borrar del historial', 'Borrar esta generación del historial.', 'Borrar', true, 'Borrar también el audio');
        if (!r) return;
        if (it.remoteId) {
          try { await SonoraApi.borrarHistorialRemoto(it.remoteId); }
          catch (_) { SonoraApp.toast('Borrado local; el backend no respondió al borrar su copia.'); }
        }
        await SonoraStore.borrarHistorialLocal(it.id);
        renderHistorial();
        SonoraApp.toast('Borrado del historial.');
      });
      acciones.append(btnBorrar);
      fila.append(txt, acciones);
      lista.append(fila);
    });
  }

  /* ---------- Ajustes ---------- */
  function renderAjustes() {
    const a = SonoraStore.leerAjustes();
    $('input-backend-url').value = a.backendUrl || '';
    $('input-token').value = a.token || '';
    $('sel-formato-defecto').value = a.formatoDefecto || 'mp3';
    $('sel-velocidad-repro').value = a.velocidadReproduccion || '1';
    $('check-normalizar').checked = a.normalizar !== false;
    renderDiccionario();
  }

  async function renderDiccionario() {
    const reglas = await SonoraStore.listarDiccionarioLocal();
    const lista = $('lista-diccionario');
    lista.innerHTML = '';
    reglas.forEach((r) => {
      const li = document.createElement('li');
      const span = document.createElement('span');
      span.textContent = r.word + ' → ' + r.replacement;
      const btn = document.createElement('button');
      btn.className = 'btn btn-fantasma btn-pequeno';
      btn.type = 'button';
      btn.textContent = 'Borrar';
      btn.addEventListener('click', async () => {
        if (r.remoteId) { try { await SonoraApi.borrarReglaDiccionario(r.remoteId); } catch (_) { /* la local se borra igual */ } }
        await SonoraStore.borrarReglaLocal(r.id); renderDiccionario();
      });
      li.append(span, btn);
      lista.append(li);
    });
  }

  async function probarConexion() {
    const url = $('input-backend-url').value.trim();
    const resEl = $('resultado-probar');
    if (!url) { resEl.textContent = 'Pega primero la URL del backend.'; resEl.hidden = false; return; }
    SonoraStore.guardarAjustes({ backendUrl: url, token: $('input-token').value });
    resEl.textContent = 'Probando conexión…';
    resEl.hidden = false;
    const ok = await SonoraApp.comprobarBackend(true);
    resEl.textContent = ok ? 'En línea. La conexión funciona.' : 'Sin conexión. Revisa la URL y que el notebook esté corriendo.';
  }

  async function exportarDatos() {
    const voces = await SonoraStore.listarVocesLocales();
    const historial = await SonoraStore.listarHistorialLocal();
    const datos = {
      exportado: new Date().toISOString(),
      voces: voces.map((v) => ({ ...v, muestra: undefined })),
      historial: historial.map((h) => ({ ...h, audioBlob: undefined })),
    };
    const blob = new Blob([JSON.stringify(datos, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'sonora-export.json';
    a.click();
    SonoraApp.toast('Datos exportados (sin audios).');
  }

  /* ---------- init ---------- */
  function init() {
    // Voice Lab: pestañas
    $('pestana-clonar').addEventListener('click', () => {
      $('pestana-clonar').classList.add('activa');
      $('pestana-disenar').classList.remove('activa');
      $('pestana-clonar').setAttribute('aria-selected', 'true');
      $('pestana-disenar').setAttribute('aria-selected', 'false');
      $('panel-clonar').hidden = false;
      $('panel-disenar').hidden = true;
    });
    $('pestana-disenar').addEventListener('click', () => {
      $('pestana-disenar').classList.add('activa');
      $('pestana-clonar').classList.remove('activa');
      $('pestana-disenar').setAttribute('aria-selected', 'true');
      $('pestana-clonar').setAttribute('aria-selected', 'false');
      $('panel-disenar').hidden = false;
      $('panel-clonar').hidden = true;
    });

    // Voice Lab: muestra
    const zona = $('zona-soltar');
    zona.addEventListener('click', (e) => { if (e.target.id !== 'btn-examinar') $('input-muestra').click(); });
    $('btn-examinar').addEventListener('click', (e) => { e.stopPropagation(); $('input-muestra').click(); });
    zona.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); $('input-muestra').click(); } });
    ['dragover', 'dragenter'].forEach((ev) => zona.addEventListener(ev, (e) => { e.preventDefault(); zona.classList.add('arrastrando'); }));
    ['dragleave', 'drop'].forEach((ev) => zona.addEventListener(ev, (e) => { e.preventDefault(); zona.classList.remove('arrastrando'); }));
    zona.addEventListener('drop', (e) => { const f = e.dataTransfer.files[0]; if (f) recibirMuestra(f); });
    $('input-muestra').addEventListener('change', (e) => { const f = e.target.files[0]; if (f) recibirMuestra(f); });
    $('btn-grabar').addEventListener('click', () => { if (grabando) pararGrabacion(); else iniciarGrabacion(); });
    $('nombre-voz').addEventListener('input', validarClonar);
    $('check-consentimiento').addEventListener('change', validarClonar);
    $('btn-clonar').addEventListener('click', clonarVoz);
    $('buscar-voces').addEventListener('input', renderVoces);

    // Voice Lab: diseñar
    $('prompt-diseno').addEventListener('input', () => {
      $('contador-diseno').textContent = SonoraApp.numeroEspanol($('prompt-diseno').value.length, 0) + ' / 1.000 caracteres';
    });
    $('btn-disenar').addEventListener('click', disenarVoz);

    // Voz a voz
    const zonaSts = $('zona-soltar-sts');
    zonaSts.addEventListener('click', (e) => { if (e.target.id !== 'btn-examinar-sts') $('input-sts').click(); });
    $('btn-examinar-sts').addEventListener('click', (e) => { e.stopPropagation(); $('input-sts').click(); });
    zonaSts.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); $('input-sts').click(); } });
    zonaSts.addEventListener('drop', (e) => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) recibirSts(f); });
    zonaSts.addEventListener('dragover', (e) => e.preventDefault());
    $('input-sts').addEventListener('change', (e) => { const f = e.target.files[0]; if (f) recibirSts(f); });
    $('btn-convertir').addEventListener('click', convertir);

    // Doblaje
    $('btn-doblaje').addEventListener('click', iniciarDoblaje);

    // Efectos
    $('slider-duracion-sfx').addEventListener('input', () => {
      $('valor-duracion-sfx').textContent = $('slider-duracion-sfx').value + ' s';
    });
    $('btn-sfx').addEventListener('click', generarSfx);

    // Historial
    $('buscar-historial').addEventListener('input', renderHistorial);
    $('filtro-tipo').addEventListener('change', renderHistorial);

    // Ajustes
    $('btn-probar').addEventListener('click', probarConexion);
    $('btn-guardar-backend').addEventListener('click', () => {
      SonoraStore.guardarAjustes({ backendUrl: $('input-backend-url').value.trim(), token: $('input-token').value });
      SonoraApp.comprobarBackend(true);
      SonoraApp.toast('Ajustes guardados.');
    });
    $('btn-mostrar-token').addEventListener('click', () => {
      const input = $('input-token');
      const mostrar = input.type === 'password';
      input.type = mostrar ? 'text' : 'password';
      $('btn-mostrar-token').textContent = mostrar ? 'Ocultar token' : 'Mostrar token';
      $('btn-mostrar-token').setAttribute('aria-pressed', String(mostrar));
    });
    $('sel-formato-defecto').addEventListener('change', () => SonoraStore.guardarAjustes({ formatoDefecto: $('sel-formato-defecto').value }));
    $('sel-velocidad-repro').addEventListener('change', () => SonoraStore.guardarAjustes({ velocidadReproduccion: $('sel-velocidad-repro').value }));
    $('check-normalizar').addEventListener('change', () => SonoraStore.guardarAjustes({ normalizar: $('check-normalizar').checked }));
    $('btn-dic-anadir').addEventListener('click', async () => {
      const palabra = $('dic-palabra').value.trim();
      const reemplazo = $('dic-reemplazo').value.trim();
      const errEl = $('error-diccionario');
      if (!palabra || !reemplazo) { errEl.textContent = 'Escribe la palabra y cómo debe sonar.'; errEl.hidden = false; return; }
      errEl.hidden = true;
      let remoteId = null;
      try {
        const creada = await SonoraApi.crearReglaDiccionario({ word: palabra, replacement: reemplazo, language: 'es' });
        remoteId = creada.rule_id || null;
      } catch (_) {
        SonoraApp.toast('Regla guardada solo en este dispositivo: el backend no respondió y no la aplicará al generar.');
      }
      await SonoraStore.guardarReglaLocal({ id: SonoraStore.nuevoId('dic'), remoteId, word: palabra, replacement: reemplazo, language: 'es' });
      $('dic-palabra').value = '';
      $('dic-reemplazo').value = '';
      renderDiccionario();
    });
    $('btn-dic-exportar').addEventListener('click', async () => {
      try {
        const blob = await SonoraApi.exportarDiccionario();
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'diccionario.pls';
        a.click();
      } catch (err) { SonoraApp.toast(SonoraApi.mensajeEnEspanol(err)); }
    });
    $('btn-exportar').addEventListener('click', exportarDatos);
    $('btn-borrar-todo').addEventListener('click', async () => {
      const r = await SonoraApp.confirmar('Borrar todos mis datos', 'Se borrarán las voces, el historial, el diccionario y los ajustes de este dispositivo. Esta acción no se puede deshacer.', 'Borrar todo', false);
      if (!r) return;
      const r2 = await SonoraApp.confirmar('¿Seguro?', 'Confirma de nuevo: se borrará todo, incluidas las voces clonadas.', 'Sí, borrar todo', false);
      if (!r2) return;
      await SonoraStore.borrarTodosLosDatos();
      location.hash = '#/estudio';
      location.reload();
    });
  }

  async function recibirSts(file) {
    const errEl = $('error-sts');
    const infoEl = $('info-sts');
    errEl.hidden = true;
    const errFormato = validarArchivoAudio(file, 0, 600, 100);
    if (errFormato) { errEl.textContent = errFormato; errEl.hidden = false; audioSts = null; validarSts(); return; }
    const dur = await duracionDeAudio(file);
    if (dur && dur > 600) { errEl.textContent = 'El audio dura más de 10 min.'; errEl.hidden = false; audioSts = null; validarSts(); return; }
    audioSts = { file, durationS: dur };
    infoEl.textContent = 'Audio: ' + formatoDuracion(dur) + ' · ' + file.name;
    infoEl.hidden = false;
    validarSts();
  }

  return { init, renderVoces, renderHistorial, renderAjustes, renderSelectoresVoz, validarClonar, validarSts };
})();
