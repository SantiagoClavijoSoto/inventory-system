# Inventory System

Sistema de Gestión de Inventario y Punto de Venta (POS) Multi-Tenant SaaS.

## Descripción

Sistema centralizado para gestionar inventario, ventas y operaciones de empresas con una o múltiples sucursales. Diseñado como producto **SaaS multi-tenant** con aislamiento completo de datos entre empresas.

### Problema que Resuelve

- Falta de control unificado de inventario y ventas
- Dificultad para gestionar múltiples sucursales
- Necesidad de reportes, alertas y control de stock en tiempo real
- Centralizar toda la operación del negocio en un solo sistema

### Usuarios Objetivo

| Rol | Descripción |
|-----|-------------|
| **Superadministrador** | Administra el SaaS completo, gestiona empresas clientes |
| **Administrador** | Dueño/gerente de empresa cliente |
| **Empleado** | Operador de POS, gestión limitada según permisos |

### Industrias Target

- Supermercados
- Tiendas minoristas (retail)
- Almacenes
- Negocios con punto de venta físico
- Empresas con múltiples sucursales

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
│   └── src/
│       ├── api/           # Capa de API
│       ├── components/    # Componentes UI
│       ├── pages/         # Páginas de la aplicación
│       ├── store/         # Estado global (Zustand)
│       └── types/         # Tipos TypeScript
├── docker-compose.yml
└── flake.nix              # Entorno de desarrollo Nix
```

## Módulos Funcionales

### Para Empresas (Administradores)

- **Dashboard**: Visualización de ventas, KPIs e indicadores
- **Punto de Venta (POS)**: Registro de ventas, control de caja, escaneo de códigos
- **Inventario**: Gestión de productos, control de stock por sucursal
- **Empleados**: Creación y gestión, asignación de roles
- **Proveedores**: Registro y gestión de proveedores
- **Reportes**: Ventas, inventario, filtros avanzados, exportación PDF/Excel
- **Alertas**: Bajo stock, alertas operativas personalizables
- **Sucursales**: CRUD de sucursales, inventario independiente
- **Configuración**: Ajustes generales, impuestos, moneda

### Para Superadministrador (Panel Exclusivo)

- Gestión de empresas clientes
- Gestión de planes/suscripciones
- Activación/desactivación de empresas
- Control general del SaaS

## Instalación

### Requisitos Previos

- Docker y Docker Compose
- Node.js 22+ (o usar Nix)
- Python 3.12+ (o usar Nix)

### Con Docker (Recomendado)

```bash
# Clonar el repositorio
git clone https://github.com/SantiagoClavijoSoto/inventory-system.git
cd inventory-system

# Levantar servicios
docker-compose up -d

# Aplicar migraciones
docker-compose exec backend python manage.py migrate

# Crear superusuario
docker-compose exec backend python manage.py createsuperuser

# Cargar datos de demostración (opcional)
docker-compose exec backend python manage.py seed_companies
```

### Con Nix (Desarrollo)

```bash
# Entrar al entorno de desarrollo
nix develop

# Backend
cd backend
python manage.py runserver

# Frontend (en otra terminal)
cd frontend
npm install
npm run dev
```

### Manual

```bash
# Backend
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend
cd frontend
npm install
npm run dev
```

## Variables de Entorno

Crear archivo `.env` basado en `.env.example`:

```env
# Database
DATABASE_URL=mysql://user:pass@localhost:3306/inventory_db

# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# JWT
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=7

# Redis/Celery
REDIS_URL=redis://localhost:6379/0
```

## Desarrollo

### Backend

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

### Frontend

```bash
cd frontend

# Desarrollo
npm run dev

# Build
npm run build

# Linting
npm run lint
```

## API Documentation

Una vez el backend esté corriendo:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Schema**: http://localhost:8000/api/schema/

## Testing

```bash
# Backend - Todos los tests
cd backend && pytest

# Backend - Con coverage
pytest --cov=apps --cov-report=html

# Frontend - Linting
cd frontend && npm run lint
```

## Arquitectura Multi-Tenant

- **Enfoque**: Shared database, shared schema con discriminador `company_id`
- **Aislamiento**: Cada modelo de empresa tiene FK a `Company`
- **Filtrado**: Automático por tenant en todas las queries
- **Seguridad**: Middleware valida acceso a recursos por empresa

## Reglas de Negocio

### Inventario
- Stock nunca negativo
- Inventario independiente por sucursal
- Actualización automática con ventas

### Ventas
- Asociadas a empleado, sucursal y empresa
- Impactan inventario en tiempo real

### Roles y Permisos
- RBAC (Role-Based Access Control)
- Permisos granulares por módulo
- Roles personalizables por empresa

## Licencia

Este proyecto es privado y propietario.

## Autor

Santiago Clavijo Soto
