/* Sonora — ajustes en localStorage, voces e historial en IndexedDB.
   Nada sale de este dispositivo. Sin secretos en el código. */
'use strict';

const SonoraStore = (() => {
  const CLAVE_AJUSTES = 'sonora.ajustes.v1';
  const AJUSTES_DEFECTO = {
    backendUrl: '',
    token: '',
    formatoDefecto: 'mp3',
    velocidadReproduccion: '1',
    normalizar: true,
    vozActivaId: 'ef_dora',
    vozActivaNombre: 'ef_dora',
    vozActivaOrigen: 'fija',
    vozActivaModelo: 'kokoro',
  };

  function leerAjustes() {
    try {
      const raw = localStorage.getItem(CLAVE_AJUSTES);
      if (!raw) return { ...AJUSTES_DEFECTO };
      return { ...AJUSTES_DEFECTO, ...JSON.parse(raw) };
    } catch (_) { return { ...AJUSTES_DEFECTO }; }
  }
  function guardarAjustes(parcial) {
    const actual = leerAjustes();
    const nuevo = { ...actual, ...parcial };
    localStorage.setItem(CLAVE_AJUSTES, JSON.stringify(nuevo));
    return nuevo;
  }

  /* ---- IndexedDB ---- */
  const DB_NOMBRE = 'sonora';
  const DB_VERSION = 1;
  let dbPromise = null;

  function abrirDB() {
    if (dbPromise) return dbPromise;
    dbPromise = new Promise((resolver, rechazar) => {
      const req = indexedDB.open(DB_NOMBRE, DB_VERSION);
      req.onupgradeneeded = () => {
        const db = req.result;
        if (!db.objectStoreNames.contains('voces')) {
          db.createObjectStore('voces', { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains('historial')) {
          const h = db.createObjectStore('historial', { keyPath: 'id' });
          h.createIndex('createdAt', 'createdAt', { unique: false });
        }
        if (!db.objectStoreNames.contains('diccionario')) {
          db.createObjectStore('diccionario', { keyPath: 'id' });
        }
      };
      req.onsuccess = () => resolver(req.result);
      req.onerror = () => rechazar(req.error);
    });
    return dbPromise;
  }

  function tx(almacen, modo, fn) {
    return abrirDB().then((db) => new Promise((resolver, rechazar) => {
      const t = db.transaction(almacen, modo);
      const store = t.objectStore(almacen);
      const out = fn(store);
      t.oncomplete = () => resolver(out);
      t.onerror = () => rechazar(t.error);
    }));
  }

  function poner(almacen, valor) {
    return abrirDB().then((db) => new Promise((resolver, rechazar) => {
      const req = db.transaction(almacen, 'readwrite').objectStore(almacen).put(valor);
      req.onsuccess = () => resolver(valor);
      req.onerror = () => rechazar(req.error);
    }));
  }
  function borrar(almacen, id) {
    return abrirDB().then((db) => new Promise((resolver, rechazar) => {
      const req = db.transaction(almacen, 'readwrite').objectStore(almacen).delete(id);
      req.onsuccess = () => resolver(true);
      req.onerror = () => rechazar(req.error);
    }));
  }
  function listar(almacen) {
    return abrirDB().then((db) => new Promise((resolver, rechazar) => {
      const req = db.transaction(almacen, 'readonly').objectStore(almacen).getAll();
      req.onsuccess = () => resolver(req.result || []);
      req.onerror = () => rechazar(req.error);
    }));
  }
  function obtener(almacen, id) {
    return abrirDB().then((db) => new Promise((resolver, rechazar) => {
      const req = db.transaction(almacen, 'readonly').objectStore(almacen).get(id);
      req.onsuccess = () => resolver(req.result || null);
      req.onerror = () => rechazar(req.error);
    }));
  }
  function limpiar(almacen) {
    return abrirDB().then((db) => new Promise((resolver, rechazar) => {
      const req = db.transaction(almacen, 'readwrite').objectStore(almacen).clear();
      req.onsuccess = () => resolver(true);
      req.onerror = () => rechazar(req.error);
    }));
  }

  function nuevoId(prefijo) {
    return prefijo + '_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8);
  }

  /* ---- Voces ---- */
  const VOCES_FIJAS = [
    { id: 'ef_dora', name: 'ef_dora', source: 'fija', model: 'kokoro', language: 'es', tags: ['femenina', 'español'], nota: 'Voz fija de Kokoro' },
    { id: 'em_alex', name: 'em_alex', source: 'fija', model: 'kokoro', language: 'es', tags: ['masculina', 'español'], nota: 'Voz fija de Kokoro' },
    { id: 'em_santa', name: 'em_santa', source: 'fija', model: 'kokoro', language: 'es', tags: ['masculina', 'español'], nota: 'Voz fija de Kokoro' },
    // A8: las 9 voces fijas de Qwen3-TTS CustomVoice también existen
    // en el backend y no aparecían en ningún selector del frontend.
    { id: 'Vivian', name: 'Vivian', source: 'fija', model: 'qwen3-tts-1.7b-customvoice', language: 'zh', tags: ['femenina'], nota: 'Voz fija Qwen CustomVoice' },
    { id: 'Serena', name: 'Serena', source: 'fija', model: 'qwen3-tts-1.7b-customvoice', language: 'zh', tags: ['femenina'], nota: 'Voz fija Qwen CustomVoice' },
    { id: 'Uncle_Fu', name: 'Uncle_Fu', source: 'fija', model: 'qwen3-tts-1.7b-customvoice', language: 'zh', tags: ['masculina'], nota: 'Voz fija Qwen CustomVoice' },
    { id: 'Dylan', name: 'Dylan', source: 'fija', model: 'qwen3-tts-1.7b-customvoice', language: 'zh', tags: ['masculina'], nota: 'Voz fija Qwen CustomVoice' },
    { id: 'Eric', name: 'Eric', source: 'fija', model: 'qwen3-tts-1.7b-customvoice', language: 'zh', tags: ['masculina'], nota: 'Voz fija Qwen CustomVoice' },
    { id: 'Ryan', name: 'Ryan', source: 'fija', model: 'qwen3-tts-1.7b-customvoice', language: 'en', tags: ['masculina', 'inglés'], nota: 'Voz fija Qwen CustomVoice' },
    { id: 'Aiden', name: 'Aiden', source: 'fija', model: 'qwen3-tts-1.7b-customvoice', language: 'en', tags: ['masculina', 'inglés'], nota: 'Voz fija Qwen CustomVoice' },
    { id: 'Ono_Anna', name: 'Ono_Anna', source: 'fija', model: 'qwen3-tts-1.7b-customvoice', language: 'ja', tags: ['femenina'], nota: 'Voz fija Qwen CustomVoice' },
    { id: 'Sohee', name: 'Sohee', source: 'fija', model: 'qwen3-tts-1.7b-customvoice', language: 'ko', tags: ['femenina'], nota: 'Voz fija Qwen CustomVoice' },
  ];

  function guardarVoz(voz) { return poner('voces', voz); }
  function borrarVozLocal(id) { return borrar('voces', id); }
  function listarVocesLocales() { return listar('voces'); }
  function obtenerVozLocal(id) { return obtener('voces', id); }

  async function listarTodasLasVoces() {
    const locales = await listarVocesLocales();
    return [...VOCES_FIJAS, ...locales];
  }

  /* ---- Historial local ---- */
  function guardarHistorial(item) { return poner('historial', item); }
  function borrarHistorialLocal(id) { return borrar('historial', id); }
  function listarHistorialLocal() {
    return listar('historial').then((items) =>
      items.sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0)));
  }

  /* ---- Diccionario local ---- */
  function guardarReglaLocal(regla) { return poner('diccionario', regla); }
  function borrarReglaLocal(id) { return borrar('diccionario', id); }
  function listarDiccionarioLocal() { return listar('diccionario'); }

  async function borrarTodosLosDatos() {
    await Promise.all([limpiar('voces'), limpiar('historial'), limpiar('diccionario')]);
    localStorage.removeItem(CLAVE_AJUSTES);
  }

  return {
    leerAjustes, guardarAjustes, nuevoId,
    VOCES_FIJAS, guardarVoz, borrarVozLocal, listarVocesLocales,
    obtenerVozLocal, listarTodasLasVoces,
    guardarHistorial, borrarHistorialLocal, listarHistorialLocal,
    guardarReglaLocal, borrarReglaLocal, listarDiccionarioLocal,
    borrarTodosLosDatos,
  };
})();
