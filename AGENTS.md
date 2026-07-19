# Agente IA Multi-tenant (WhatsApp)

## Arquitectura general

```
Meta WhatsApp Cloud API → Webhook (200 rápido) → Cola → Worker LangGraph → DB → WhatsApp API
```

- **Router** identifica `client_id` desde `phone_number_id` del webhook (primer paso antes de cualquier lógica).
- **Un solo motor LangGraph**, config-driven: prompt de sistema, tools habilitadas y parámetros del modelo se resuelven en runtime desde DB por `client_id`.
- **Registry central de tools**: una tool se programa una vez y se habilita por cliente vía configuración.
- **Nunca hardcodear lógica específica de cliente**. Agregar un cliente = fila en DB, no código nuevo.

## Atributos de calidad (prioridad estricta)

1. **Flexibilidad** — multi-tenant config-driven, no tocar código por cliente nuevo
2. **Observabilidad** — cada turno, tool elegida, argumentos, decisión queda registrado con `client_id`, `conversation_id`, timestamp. No es logging genérico de framework, es requisito de producto.
3. **Mantenibilidad** — responsabilidad única, una lógica core, personalización vive en configuración
4. **Performance** — latencia percibida importa (WhatsApp). Async/paralelismo. Logging asíncrono que no bloquea respuesta.
5. **Seguridad / Aislamiento multi-tenant** — toda query debe filtrar por `client_id` explícitamente. No negociable.

## Regla de consulta obligatoria

Consultar (y esperar confirmación) antes de DECISIONES ARQUITECTÓNICAS:
- Elegir o cambiar tecnología/librería/framework base
- Definir o modificar esquemas de DB, relaciones entre entidades
- Definir contratos de API que otros componentes consuman
- Decisiones que afecten a más de un tenant
- Trade-offs entre atributos de calidad
- Cualquier cosa difícil o costosa de revertir
- En duda, preguntar

Para implementación directa (funciones, tests, bugs, refactors siguiendo patrones acordados): proceder sin pedir permiso, explicar brevemente qué y por qué.

## Pendientes de decisión arquitectónica (no implementados aún)

- Mecanismo de cola (webhook → procesamiento asíncrono)
- Modelo de datos de configuración por cliente (prompt, tools, params)
- Modelo de datos de persistencia de conversaciones (para dashboard)
- Mecanismo de logging asíncrono
- Estructura de carpetas/módulos del proyecto

## Estado del proyecto

Greenfield. Sin código aún. En etapa de definición arquitectónica.
