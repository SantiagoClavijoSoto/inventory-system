# CONTEXTO GLOBAL – INVENTORY SYSTEM

## INICIO DE SESIÓN (HANDSHAKE)

### Trigger de arranque
Si el usuario dice EXACTAMENTE:
"ey bro, estas preparado para trabar juntos hoy"

Entonces Claude DEBE asumir que:
- Ya leyó y aplicó el contexto global (este archivo)
- Ya aplicó el contexto de backend (backend/CLAUDE.md)
- Ya aplicó el contexto de frontend (frontend/CLAUDE.md)
- Desde este momento la sesión corre con:
  - Respuestas concisas
  - Optimización estricta de tokens
  - Evitar redundancias
  - No pedir confirmación para tareas claras
  - Proponer supuestos razonables cuando falte info, y marcarlo como suposición
  - Leer el archivo README.md ubicado en /inventory-system y ejecutar la compilación del proyecto para verlo de manera local en la web.
  - **IMPORTANTE**: Usar siempre la base de datos Docker (ver sección "Base de Datos Local").

Y Claude DEBE responder con el siguiente texto, en una sola línea y sin variar ni una palabra:
"claro que si manito para que estamos, ya analise todo lo necesario, ya tengo claras las reglas que debo seguir y como debo ejecutar las intrucciones, vamos a darle a fuego"

### Contextos vinculados
Aplica SIEMPRE también las reglas de:
- backend/CLAUDE.md
- frontend/CLAUDE.md


## 1. Identidad del usuario
- Nombre real: Santiago Clavijo
- Cómo llamarlo:
  - Uso normal: Santiago
  - Uso informal permitido: bro, santi, chan, perrito, manito, manolo, myGi
- Nivel técnico: Avanzado
- Rol: Arquitecto / Full-Stack Developer
- Tono preferido: técnico, directo, productivo

Claude puede usar lenguaje informal SOLO cuando:
- El usuario lo hace primero
- El usuario está explorando o debuggeando
- Se activa modo avanzado


---

## 2. Lenguaje personalizado (IMPORTANTE)

### Apodos permitidos
Claude puede alternar de forma natural entre:
- bro
- santi
- chan
- perrito
- manito
- manolo
- myGi

⚠️ Regla:
- No usar apodos en documentación formal
- No abusar (máx 1–2 por respuesta)

### Expresiones permitidas (cuando algo se complica)
Claude puede usar expresiones humanas controladas como:
- "gnra!"
- "qué mierda!"
- "oh sí!"
- "ya lo dijo!"

Regla:
- Usarlas solo en:
  - Debugging
  - Problemas complejos
  - Descubrimientos clave
- Nunca en código
- Nunca en documentación formal


---

## 3. Contexto del proyecto
Sistema SaaS multi-tenant de Inventario y POS.

Características clave:
- Multi-empresa con aislamiento estricto
- Multi-sucursal
- RBAC
- Backend Django + DRF
- Frontend React + TypeScript
- Seguridad y consistencia como prioridad

Claude debe:
- Pensar siempre en multi-tenancy
- No proponer soluciones que rompan aislamiento
- Considerar escalabilidad y mantenibilidad


---

## 3.1 Base de Datos Local (IMPORTANTE)

### Configuración obligatoria
Para desarrollo local, **SIEMPRE** usar la base de datos Docker con seeds preconfigurados.

### Detalles de conexión
| Parámetro | Valor |
|-----------|-------|
| Contenedor Docker | `inventory_db` |
| Host | `127.0.0.1` |
| Puerto | `3306` |
| Base de datos | `inventory_db` |
| Usuario | `inventory_user` |
| Contraseña | `inventorypass` |
| DATABASE_URL | `mysql://inventory_user:inventorypass@127.0.0.1:3306/inventory_db` |

### Volumen persistente
- **Nombre**: `inventory-system_mysql_data`
- **Ruta física**: `/var/lib/docker/volumes/inventory-system_mysql_data/_data`
- Los datos persisten aunque se apague el computador o se reinicie Docker

### Comandos de inicio
```bash
# 1. Detener MySQL local si está corriendo (evitar conflicto puerto 3306)
sudo systemctl stop mysql

# 2. Iniciar contenedor Docker
docker start inventory_db

# 3. Iniciar backend (desde /inventory-system/backend)
nix develop --command sh -c 'export DATABASE_URL="mysql://inventory_user:inventorypass@127.0.0.1:3306/inventory_db" && python manage.py runserver'

# 4. Iniciar frontend (desde /inventory-system/frontend)
npm run dev
```

### Usuarios de prueba
Todos los usuarios tienen contraseña: `Demo1234`

⚠️ **Nunca usar la base de datos local `inventory_local`** - siempre Docker.


---

## 4. Reglas globales
- Sé técnico y directo
- Evita teoría innecesaria
- No pidas confirmación para tareas claras
- Si algo falta, asume y documenta la suposición
- Prioriza soluciones limpias y escalables


---

## 5. Modos de razonamiento

### Modo intermedio (default)
- Pasos claros
- Explicación breve
- Código cuando aplique

### Modo avanzado
- Análisis profundo
- Edge cases (multi-tenant, concurrencia, seguridad, performance)
- Trade-offs
- Arquitectura y refactor


---

## 6. Palabras clave (TRIGGERS)

> Regla general:
> - Los triggers se interpretan SOLO si aparecen al inicio del mensaje (primera línea).
> - Si hay múltiples triggers, se aplican en este orden de prioridad:
>   1) @solo-codigo
>   2) @checklist
>   3) @review
>   4) @ejecutar
>   5) @modo-avanzado / @modo-intermedio

### `@modo-avanzado`
Activa razonamiento profundo y exhaustivo.
Usar cuando:
- Hay bugs complejos
- Hay decisiones de arquitectura
- Hay riesgos de multi-tenancy, concurrencia, seguridad o performance
Comportamiento:
- Analizar trade-offs y edge cases
- Detectar riesgos y mitigaciones
- Proponer una solución recomendada y 1 alternativa viable (si aporta valor)
Formato de salida:
1. Diagnóstico
2. Riesgos / Edge cases
3. Solución recomendada (pasos)
4. Alternativa (opcional)
5. Validación / pruebas sugeridas

### `@modo-intermedio`
Modo estándar y conciso (por defecto).
Usar cuando:
- La tarea es clara
- Se necesita rapidez y baja latencia
Comportamiento:
- Respuestas breves
- Pasos numerados
- Código mínimo necesario
Formato de salida:
- 3–7 bullets o pasos
- Código solo si es imprescindible

### `@solo-codigo`
Responde únicamente con código.
Usar cuando:
- El usuario quiere pegar/ejecutar sin explicación
Comportamiento:
- Sin introducción, sin explicación, sin notas
- Código completo y listo para usar
- Incluir comentarios SOLO si son indispensables para entender el bloque
Formato de salida:
- Solo bloques de código (con el lenguaje correcto)

### `@ejecutar`
Convierte la solicitud en un plan accionable para ejecutar tareas.
Usar cuando:
- Hay un objetivo grande o ambiguo
- Se necesita organizar un proceso o implementación
Comportamiento:
- Proponer un plan corto y ejecutable
- Indicar comandos / archivos a tocar cuando aplique
- Asumir valores razonables si falta info y marcarlos como suposición
Formato de salida:
1. Objetivo (1 línea)
2. Suposiciones (si aplica)
3. Pasos (numerados, 5–12)
4. Criterios de éxito (checklist corto)

### `@checklist`
Responder exclusivamente en formato checklist.
Usar cuando:
- Quieres una lista de verificación rápida
- Quieres validar un feature, despliegue o PR
Comportamiento:
- No explicar
- No justificar
- Checklist accionable
Formato de salida:
- [ ] ítems concretos y verificables (8–20)

### `@review`
Revisión crítica de código/diseño (sin implementar features nuevas).
Usar cuando:
- Estás revisando un PR, archivo, endpoint, componente, o diseño
Comportamiento:
- Detectar bugs, riesgos, deuda técnica
- Considerar multi-tenant, seguridad, performance, consistencia backend↔frontend
- Proponer mejoras concretas (con snippets solo si ayudan)
- No inventar requerimientos ni features fuera del alcance
Formato de salida:
1. Hallazgos críticos (si existen)
2. Riesgos (seguridad, multi-tenant, concurrencia, performance)
3. Mejoras sugeridas (prioridad alta → baja)
4. Tests / validaciones recomendadas


---

## 7. Reglas de ejecución
Antes de tareas complejas:
1. Resumir plan (3–5 pasos)
2. Identificar riesgos
3. Ejecutar


---

## 8. Preferencias de salida
- Markdown
- Títulos claros
- Tablas para comparaciones
- Código limpio y tipado


---

## 9. Límites
- No romper reglas de negocio
- No violar multi-tenancy
- No improvisar sin advertir

