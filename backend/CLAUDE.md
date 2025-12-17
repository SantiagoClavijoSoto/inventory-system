# CONTEXTO BACKEND – DJANGO / DRF

## BACKEND AUTO-ENFORCE (SIEMPRE)

- Prioridad: multi-tenant seguro por Company.
- En cualquier cambio: verificar filtros por empresa, permisos (RBAC) y no mezclar datos.
- Optimización tokens: responder en pasos cortos, código directo, sin teoría.

## Stack
- Django 5.x
- Django REST Framework
- SimpleJWT
- MySQL / MariaDB
- Celery + Redis
- pytest

---

## Reglas multi-tenant (CRÍTICAS)
- Todo modelo de negocio tiene FK a Company
- Toda query debe filtrarse por empresa
- Validar acceso por empresa en:
  - Views
  - Serializers
  - Services
- Nunca mezclar datos entre tenants

---

## Arquitectura
- Views delgadas
- Lógica compleja en services
- Validaciones críticas en backend
- Señales solo cuando sea necesario

---

## Reglas de negocio
- Stock nunca negativo
- Inventario independiente por sucursal
- Ventas afectan stock en tiempo real
- Trazabilidad completa

---

## Testing
- pytest obligatorio para lógica crítica
- Tests deben considerar multi-tenancy

---

## Preferencias
- Código explícito
- Tipado claro
- Evitar magia innecesaria

