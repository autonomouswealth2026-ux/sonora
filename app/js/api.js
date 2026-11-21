/* Sonora — cliente del backend FastAPI (FEATURE_MAP.md).
   Todas las llamadas van a la URL configurable en Ajustes.
   Sin secretos ni claves dentro del código. */
'use strict';

const SonoraApi = (() => {
  function baseUrl() {
    const s = SonoraStore.leerAjustes();
    return (s.backendUrl || '').replace(/\/+$/, '');
  }
  function configurado() { return Boolean(baseUrl()); }
  function headers(extra) {
    // ngrok (plan gratis) muestra una página de aviso en la primera
    // visita si falta esta cabecera; con ella responde JSON directo.
    // El backend ya la permite en CORS (main.py allow_headers), así
    // que no rompe el preflight. Vale también sin ngrok: el resto
    // de túneles la ignoran.
    const h = { 'ngrok-skip-browser-warning': 'true', ...(extra || {}) };
    const s = SonoraStore.leerAjustes();
    if (s.token) h.Authorization = 'Bearer ' + s.token;
    return h;
  }
  function url(ruta) { return baseUrl() + ruta; }

  async function pedir(ruta, opciones) {
    if (!configurado()) {
      const e = new Error('Backend sin configurar: pega la URL en Ajustes.');
      e.codigo = 'SIN_BACKEND';
      throw e;
    }
    let resp;
    try {
      resp = await fetch(url(ruta), opciones || {});
    } catch (err) {
      const e = new Error('No se pudo contactar con el backend. Revisa la URL en Ajustes.');
      e.codigo = 'SIN_CONEXION';
      e.causa = err;
      throw e;
    }
    if (resp.status === 503) {
      const e = new Error('El modelo GPU no está cargado. Arranca el backend GPU.');
      e.codigo = 'GPU_APAGADA';
      e.status = 503;
      throw e;
    }
    if (!resp.ok) {
      let detalle = '';
      try { const j = await resp.clone().json(); detalle = j.detail || j.message || ''; } catch (_) { /* no JSON */ }
      const e = new Error(detalle || ('El backend devolvió el error ' + resp.status + '.'));
      e.codigo = 'HTTP_' + resp.status;
      e.status = resp.status;
      throw e;
    }
    return resp;
  }

  async function health() {
    const inicio = performance.now();
    const resp = await pedir('/api/v1/health', { headers: headers() });
    const datos = await resp.json();
    return { ...datos, latenciaMs: Math.round(performance.now() - inicio) };
  }

  async function listarVoces() {
    const resp = await pedir('/api/v1/tts/voices', { headers: headers() });
    return resp.json();
  }

  // B8: descarga una URL relativa del backend con base + token y
  // devuelve una blob URL usable como <audio src> o para descargar.
  async function blobUrl(rutaRelativa) {
    const resp = await pedir(rutaRelativa, { headers: headers() });
    return URL.createObjectURL(await resp.blob());
  }

  // A8: biblioteca propia del backend (fijas + clonadas + diseñadas).
  async function listarBiblioteca() {
    const resp = await pedir('/api/v1/library/voices', { headers: headers() });
    return resp.json();
  }

  async function favoritoVoz(voiceId) {
    const resp = await pedir('/api/v1/library/voices/' + encodeURIComponent(voiceId) + '/favorite', { method: 'POST', headers: headers() });
    return resp.json();
  }

  /* POST /api/v1/tts — devuelve { blob, generationId, durationSeconds, model, voiceId } */
  async function tts(cuerpo) {
    const resp = await pedir('/api/v1/tts', {
      method: 'POST',
      headers: headers({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(cuerpo),
    });
    const blob = await resp.blob();
    return {
      blob,
      generationId: resp.headers.get('X-Generation-Id'),
      durationSeconds: Number(resp.headers.get('X-Duration-Seconds') || 0) || null,
      model: resp.headers.get('X-Model') || cuerpo.model,
      voiceId: resp.headers.get('X-Voice-Id') || cuerpo.voice_id,
    };
  }

  async function clonarVoz(formData) {
    const resp = await pedir('/api/v1/voices/instant-clone', { method: 'POST', headers: headers(), body: formData });
    return resp.json();
  }

  async function vistaPreviaVoz(voiceId) {
    const resp = await pedir('/api/v1/voices/' + encodeURIComponent(voiceId) + '/preview', { headers: headers() });
    return resp.blob();
  }

  async function borrarVoz(voiceId) {
    await pedir('/api/v1/voices/' + encodeURIComponent(voiceId), { method: 'DELETE', headers: headers() });
  }

  async function disenarVoz(cuerpo) {
    const resp = await pedir('/api/v1/voices/design', {
      method: 'POST',
      headers: headers({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(cuerpo),
    });
    return resp.json();
  }

  async function guardarCandidata(candidateId, nombre) {
    const resp = await pedir('/api/v1/voices/design/' + encodeURIComponent(candidateId) + '/save', {
      method: 'POST',
      headers: headers({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ name: nombre }),
    });
    return resp.json();
  }

  async function vozAVoz(formData) {
    const resp = await pedir('/api/v1/speech-to-speech', { method: 'POST', headers: headers(), body: formData });
    const blob = await resp.blob();
    return { blob, metodo: resp.headers.get('X-Method') || formData.get('method') };
  }

  async function iniciarDoblaje(formData) {
    const resp = await pedir('/api/v1/dubbing', { method: 'POST', headers: headers(), body: formData });
    return resp.json();
  }

  async function estadoDoblaje(jobId) {
    const resp = await pedir('/api/v1/dubbing/' + encodeURIComponent(jobId), { headers: headers() });
    return resp.json();
  }

  async function editarSegmentoDoblaje(jobId, n, texto, idioma) {
    const q = idioma ? '?language=' + encodeURIComponent(idioma) : '';
    const resp = await pedir('/api/v1/dubbing/' + encodeURIComponent(jobId) + '/segments/' + n + '/edit' + q, {
      method: 'POST',
      headers: headers({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ translated_text: texto }),
    });
    return resp.json();
  }

  function urlDescargaDoblaje(jobId, idioma, formato) {
    return url('/api/v1/dubbing/' + encodeURIComponent(jobId) + '/download?language=' + encodeURIComponent(idioma) + '&format=' + encodeURIComponent(formato || 'mp3'));
  }

  async function descargarDoblaje(jobId, idioma, formato) {
    const resp = await pedir('/api/v1/dubbing/' + encodeURIComponent(jobId) + '/download?language=' + encodeURIComponent(idioma) + '&format=' + encodeURIComponent(formato || 'mp3'), { headers: headers() });
    return resp.blob();
  }

  async function exportarDiccionario() {
    const resp = await pedir('/api/v1/pronunciation/export', { headers: headers() });
    return resp.blob();
  }

  async function sfx(cuerpo) {
    const resp = await pedir('/api/v1/sfx', {
      method: 'POST',
      headers: headers({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(cuerpo),
    });
    const tipo = resp.headers.get('Content-Type') || '';
    if (tipo.includes('application/json')) return resp.json();
    return { blob: await resp.blob() };
  }

  async function borrarHistorialRemoto(id) {
    await pedir('/api/v1/history/' + encodeURIComponent(id), { method: 'DELETE', headers: headers() });
  }

  async function listarDiccionario(idioma) {
    const resp = await pedir('/api/v1/pronunciation?language=' + encodeURIComponent(idioma || 'es'), { headers: headers() });
    return resp.json();
  }

  async function crearReglaDiccionario(regla) {
    const resp = await pedir('/api/v1/pronunciation', {
      method: 'POST',
      headers: headers({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(regla),
    });
    return resp.json();
  }

  async function borrarReglaDiccionario(ruleId) {
    await pedir('/api/v1/pronunciation/' + encodeURIComponent(ruleId), { method: 'DELETE', headers: headers() });
  }

  /* Mensajes de error del backend en inglés -> español en la UI. */
  function mensajeEnEspanol(err) {
    if (!err) return 'Ocurrió un error desconocido.';
    if (err.codigo === 'SIN_BACKEND') return 'Backend sin configurar: pega la URL en Ajustes.';
    if (err.codigo === 'SIN_CONEXION') return 'No se pudo contactar con el backend. Revisa la URL en Ajustes y que el notebook de Kaggle esté corriendo.';
    if (err.codigo === 'GPU_APAGADA') return 'El modelo GPU no está cargado. Arranca el backend GPU.';
    if (err.status === 501) return 'Esa función no está implementada en el backend todavía: ' + (err.message || 'usa la alternativa que indica el backend.');
    if (err.status === 404) return 'No se encontró ese recurso en el backend (voz o trabajo desconocido).';
    if (err.status === 400) return err.message || 'Petición no válida. Revisa los datos y reintenta.';
    if (err.status === 422) return 'El audio no pasó la validación del backend (duración, calidad o más de un hablante).';
    if (err.status === 413) return 'El archivo es demasiado grande para el backend.';
    return err.message || 'Ocurrió un error desconocido.';
  }

  return {
    configurado, health, listarVoces, listarBiblioteca, favoritoVoz,
    blobUrl, tts, clonarVoz, vistaPreviaVoz,
    borrarVoz, disenarVoz, guardarCandidata, vozAVoz, iniciarDoblaje,
    estadoDoblaje, editarSegmentoDoblaje, urlDescargaDoblaje,
    descargarDoblaje, sfx,
    borrarHistorialRemoto, listarDiccionario,
    crearReglaDiccionario, borrarReglaDiccionario,
    exportarDiccionario,
    mensajeEnEspanol,
  };
})();
