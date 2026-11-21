# Decisiones del proyecto Sonora (clon de ElevenLabs)

## 2026-11-20 — CraftAnything DESCARTADA como vía de construcción
- **Decisión (agente principal):** el frontend se construye A MANO con las skills de diseño. CraftAnything queda descartada para este clon.
- **Motivos:**
  1. El clon no es una app autocontenida: es un frontend conectado a un backend vivo con URL configurable, token, subidas de audio, streaming e IndexedDB — el código hecho a mano da control preciso sobre esa integración.
  2. La fidelidad REA + Replica-diff exige código auditable y correcciones quirúrgicas; cada corrección vía constructor es un turno nuevo con coste de re-orientación.
  3. La cuota de los proveedores del constructor está saturada ahora mismo (Coarena al límite con P1b relanzado; ApiNex free cerrado) y la orden de Carlos del 15 nov mantiene en pausa los rebuilds hasta que reclame los tokens.
- **Alcance:** CraftAnything sigue siendo la vía para piezas visuales autocontenidas, no para este clon.
- **Consecuencia:** se cerró el agente evaluador de CraftAnything sin esperar su veredicto; el agente de frontend sigue a mano.
