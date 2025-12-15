# Inventory System - Contexto del Proyecto
# Sistema de Gestión de Inventario y Punto de Venta (POS) Multi-Tenant SaaS

## Propósito del Sistema

Sistema centralizado para gestionar inventario, ventas y operaciones de empresas con una o múltiples sucursales. Diseñado como producto **SaaS multi-tenant**.

### Problema que Resuelve
- Falta de control unificado de inventario y ventas
- Dificultad para gestionar múltiples sucursales
- Necesidad de reportes, alertas y control de stock en tiempo real
- Centralizar toda la operación del negocio en un solo sistema

### Usuarios Objetivo
| Rol | Descripción |
|-----|-------------|
| **Superadministrador** | Creador del software, administra el SaaS completo |
| **Administrador** | Dueño/gerente de empresa cliente |
| **Empleado** | Operador de POS, gestión limitada según permisos |

### Industrias Target
- Supermercados
- Tiendas minoristas (retail)
- Almacenes
- Negocios con punto de venta físico
- Empresas con múltiples sucursales

---

## Stack Técnico

### Backend
| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| Django | 5.0 | Framework web |
| Django REST Framework | 3.14 | API REST |
| SimpleJWT | 5.3 | Autenticación JWT |
| MySQL/MariaDB | - | Base de datos |
| Celery + Redis | 5.3 | Tareas asíncronas |
| drf-spectacular | 0.27 | Documentación API |
| pytest | 7.4 | Testing |
| ruff/black/isort | - | Code quality |

### Frontend
| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| React | 18.2 | UI Library |
| TypeScript | 5.2 | Tipado estático |
| Vite | 5.0 | Build tool |
| Tailwind CSS | 3.3 | Estilos |
| Zustand | 4.4 | Estado global |
| TanStack Query | 5.8 | Server state |
| React Router | 6.20 | Routing |
| Recharts | 2.10 | Gráficos |
| Lucide React | 0.294 | Iconos |
| Headless UI | 1.7 | Componentes accesibles |

### Infraestructura
- **Dev Environment**: Nix Flake (Python 3.12, Node.js 22)
- **Containerización**: Docker Compose
- **Base de datos**: MariaDB

---

## Estructura del Proyecto

```
inventory-system/
├── backend/
│   ├── apps/
│   │   ├── alerts/        # Sistema de alertas
│   │   ├── branches/      # Gestión de sucursales
│   │   ├── companies/     # Empresas (tenants)
│   │   ├── employees/     # Empleados y roles
│   │   ├── inventory/     # Productos y stock
│   │   ├── reports/       # Generación de reportes
│   │   ├── sales/         # Ventas y POS
│   │   ├── suppliers/     # Proveedores
│   │   └── users/         # Autenticación y usuarios
│   ├── config/            # Configuración Django
│   ├── core/              # Utilidades compartidas
│   └── manage.py
├── frontend/
│   └── src/               # Código React/TypeScript
├── docker-compose.yml
└── flake.nix              # Entorno de desarrollo Nix
```

---

## Módulos Funcionales

### Para Empresas (Administradores)

#### Dashboard
- Visualización de ventas
- Resúmenes de inventario
- Indicadores clave (KPIs)

#### Punto de Venta (POS)
- Registro de ventas
- Control de caja
- Búsqueda de productos por nombre o SKU
- Asociación de ventas a empleados y sucursales

#### Inventario
- Gestión de productos
- Control de stock **por sucursal**
- Actualización automática del stock con ventas

#### Empleados
- Creación y gestión de empleados
- Asignación de roles y permisos

#### Proveedores
- Registro y gestión de proveedores
- Relación proveedor-productos

#### Reportes
- Reportes de ventas
- Reportes de inventario
- Filtros por sucursal, empleado o período
- Exportación a PDF/Excel

#### Alertas
- Alertas de bajo stock
- Alertas operativas personalizables

#### Sucursales
- Creación y gestión de múltiples sucursales
- Control independiente de inventario por sucursal

#### Configuración
- Ajustes generales de la empresa
- Configuración de impuestos, moneda, etc.

### Para Superadministrador (Panel Exclusivo)
- Gestión de empresas clientes
- Creación y administración de empresas
- Gestión de planes/suscripciones
- Asignación de roles globales
- Personalización del sistema (branding)
- Control general del SaaS

---

## Reglas de Negocio Críticas

### Inventario
- **Stock nunca negativo**: El sistema debe prevenir ventas sin stock
- **Inventario por sucursal**: Cada sucursal maneja su propio stock
- **Actualización automática**: Las ventas descuentan stock automáticamente

### Multi-Tenancy
- **Aislamiento total**: Cada empresa está completamente aislada
- **Datos separados**: No hay filtración de datos entre empresas

### Roles y Permisos
| Rol | Capacidades |
|-----|-------------|
| Superadministrador | Crear/administrar empresas, gestión global del SaaS |
| Administrador | Crear empleados, proveedores, productos, configurar empresa |
| Empleado | Operar según rol asignado (ej: solo POS) |

### Ventas
- Toda venta debe estar asociada a: empleado, sucursal, empresa
- Las ventas impactan inventario en tiempo real

---

## Comandos de Desarrollo

### Entorno Nix
```bash
# Entrar al entorno de desarrollo
nix develop

# O con direnv
direnv allow
```

### Backend (Django)
```bash
cd backend

# Servidor de desarrollo
python manage.py runserver

# Migraciones
python manage.py makemigrations
python manage.py migrate

# Tests
pytest
pytest --cov=apps

# Linting
ruff check .
black .
```

### Frontend (Vite/React)
```bash
cd frontend

# Desarrollo
npm run dev

# Build
npm run build

# Linting
npm run lint
```

### Docker
```bash
# Levantar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f
```

---

## Convenciones de Código

### Backend (Python/Django)
- Usar type hints en funciones
- ViewSets de DRF para APIs REST
- Serializers para validación
- Factories con factory-boy para tests
- Nombres en inglés, comentarios pueden ser en español

### Frontend (TypeScript/React)
- Componentes funcionales con hooks
- Zustand para estado global
- TanStack Query para llamadas API
- Tailwind para estilos (no CSS custom)
- Tipos explícitos, evitar `any`

### API
- RESTful con versionado (`/api/v1/`)
- JWT para autenticación
- Respuestas consistentes con DRF

---

## Testing

### Backend
```bash
# Todos los tests
pytest

# Con coverage
pytest --cov=apps --cov-report=html

# Test específico
pytest apps/inventory/tests/test_models.py -v
```

### Markers de Pytest
```python
@pytest.mark.django_db  # Tests que usan DB
@pytest.mark.slow       # Tests lentos
```

---

## Estado Actual y Roadmap

### Completado
- [x] Estructura base del proyecto
- [x] Configuración Django + DRF
- [x] Configuración Vite + React + TypeScript
- [x] Docker Compose setup
- [x] Nix Flake para desarrollo
- [x] Apps base creadas

### En Progreso
- [ ] Modelo de datos completo
- [ ] Sistema de autenticación JWT
- [ ] Panel de Superadministrador
- [ ] Multi-tenancy

### Pendiente
- [ ] Dashboard con KPIs
- [ ] Módulo POS completo
- [ ] Gestión de inventario
- [ ] Sistema de alertas
- [ ] Reportes PDF/Excel

---

## Decisiones Arquitectónicas

### Multi-Tenancy
- Enfoque: **Shared database, shared schema** con discriminador `company_id`
- Cada modelo de empresa tiene FK a `Company`
- Filtrado automático por tenant en queries

### Autenticación
- JWT con refresh tokens
- Roles embebidos en token
- Permisos basados en roles (RBAC)

### Separación de Paneles
- **Panel Superadmin**: Rutas y vistas completamente separadas
- **Panel Empresa**: Acceso solo a datos de su tenant

---

## Variables de Entorno

Ver `.env.example` para la lista completa. Principales:

```env
# Database
DATABASE_URL=mysql://user:pass@localhost:3306/inventory_db

# Django
SECRET_KEY=...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# JWT
JWT_ACCESS_TOKEN_LIFETIME=60  # minutos
JWT_REFRESH_TOKEN_LIFETIME=7  # días

# Redis/Celery
REDIS_URL=redis://localhost:6379/0
```

---

## Notas para Claude Code

### Al trabajar en este proyecto:
1. **Siempre verificar** el contexto multi-tenant en queries
2. **Tests primero**: Crear tests antes de implementar features
3. **Inventario por sucursal**: Nunca asumir stock global
4. **Roles**: Verificar permisos en cada endpoint
5. **Aislamiento**: Validar que no haya filtración entre empresas

### Archivos clave a revisar:
- `backend/apps/companies/models.py` - Modelo de empresa/tenant
- `backend/apps/users/models.py` - Usuarios y roles
- `backend/config/settings.py` - Configuración Django
- `frontend/src/stores/` - Estado global Zustand
