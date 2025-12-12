import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '@/store/authStore'
import {
  authApi,
  usersApi,
  rolesApi,
  permissionsApi,
  type User,
  type Role,
  type Permission,
  type UpdateUserRequest,
  type ChangePasswordRequest,
  type CreateUserRequest,
} from '@/api/users'
import { alertPreferencesApi, type UserAlertPreference } from '@/api/alerts'
import { branchesApi, type BranchSimple } from '@/api/branches'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Input,
  Select,
  Badge,
  Modal,
  ModalFooter,
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
  Spinner,
} from '@/components/ui'
import {
  User as UserIcon,
  Lock,
  Bell,
  Users,
  Shield,
  Save,
  Plus,
  Edit2,
  Trash2,
  UserCheck,
  UserX,
  Key,
  AlertTriangle,
} from 'lucide-react'
import toast from 'react-hot-toast'

type SettingsTab = 'profile' | 'security' | 'preferences' | 'users' | 'roles'

export function Settings() {
  const { user, setUser } = useAuthStore()
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile')

  const isAdmin = user?.is_superuser || user?.role === 'admin'

  const tabs: { id: SettingsTab; label: string; icon: React.ReactNode; adminOnly?: boolean }[] = [
    { id: 'profile', label: 'Perfil', icon: <UserIcon className="h-4 w-4" /> },
    { id: 'security', label: 'Seguridad', icon: <Lock className="h-4 w-4" /> },
    { id: 'preferences', label: 'Preferencias', icon: <Bell className="h-4 w-4" /> },
    { id: 'users', label: 'Usuarios', icon: <Users className="h-4 w-4" />, adminOnly: true },
    { id: 'roles', label: 'Roles', icon: <Shield className="h-4 w-4" />, adminOnly: true },
  ]

  const visibleTabs = tabs.filter((tab) => !tab.adminOnly || isAdmin)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">Configuración</h1>
        <p className="text-secondary-500 mt-1">Administra tu cuenta y preferencias del sistema</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-secondary-200">
        <nav className="-mb-px flex space-x-8">
          {visibleTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-secondary-500 hover:text-secondary-700 hover:border-secondary-300'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'profile' && <ProfileSettings />}
        {activeTab === 'security' && <SecuritySettings />}
        {activeTab === 'preferences' && <PreferencesSettings />}
        {activeTab === 'users' && isAdmin && <UsersSettings />}
        {activeTab === 'roles' && isAdmin && <RolesSettings />}
      </div>
    </div>
  )
}

// Profile Settings Component
function ProfileSettings() {
  const queryClient = useQueryClient()
  const { user, setUser } = useAuthStore()
  const [formData, setFormData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: user?.email || '',
  })

  const updateMutation = useMutation({
    mutationFn: (data: UpdateUserRequest) => authApi.updateMe(data),
    onSuccess: (updatedUser) => {
      setUser(updatedUser)
      queryClient.invalidateQueries({ queryKey: ['me'] })
      toast.success('Perfil actualizado correctamente')
    },
    onError: () => toast.error('Error al actualizar perfil'),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    updateMutation.mutate(formData)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Información Personal</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6 max-w-lg">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Nombre"
              value={formData.first_name}
              onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
            />
            <Input
              label="Apellido"
              value={formData.last_name}
              onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
            />
          </div>
          <Input
            label="Email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          />
          <div className="pt-2">
            <p className="text-sm text-secondary-500 mb-4">
              Rol: <Badge variant="info">{user?.role_name || 'Sin rol'}</Badge>
            </p>
            <p className="text-sm text-secondary-500">
              Sucursal por defecto:{' '}
              <span className="font-medium">{user?.default_branch_name || 'No asignada'}</span>
            </p>
          </div>
          <Button type="submit" isLoading={updateMutation.isPending}>
            <Save className="h-4 w-4 mr-2" />
            Guardar Cambios
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}

// Security Settings Component
function SecuritySettings() {
  const [formData, setFormData] = useState<ChangePasswordRequest>({
    current_password: '',
    new_password: '',
    confirm_password: '',
  })
  const [error, setError] = useState('')

  const changePwdMutation = useMutation({
    mutationFn: authApi.changePassword,
    onSuccess: () => {
      toast.success('Contraseña actualizada correctamente')
      setFormData({ current_password: '', new_password: '', confirm_password: '' })
      setError('')
    },
    onError: () => {
      setError('Error al cambiar contraseña. Verifica tu contraseña actual.')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (formData.new_password !== formData.confirm_password) {
      setError('Las contraseñas no coinciden')
      return
    }

    if (formData.new_password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres')
      return
    }

    changePwdMutation.mutate(formData)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cambiar Contraseña</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6 max-w-lg">
          {error && (
            <div className="p-3 bg-danger-50 text-danger-700 rounded-lg text-sm">{error}</div>
          )}
          <Input
            label="Contraseña Actual"
            type="password"
            value={formData.current_password}
            onChange={(e) => setFormData({ ...formData, current_password: e.target.value })}
            required
          />
          <Input
            label="Nueva Contraseña"
            type="password"
            value={formData.new_password}
            onChange={(e) => setFormData({ ...formData, new_password: e.target.value })}
            required
          />
          <Input
            label="Confirmar Nueva Contraseña"
            type="password"
            value={formData.confirm_password}
            onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
            required
          />
          <Button type="submit" isLoading={changePwdMutation.isPending}>
            <Lock className="h-4 w-4 mr-2" />
            Cambiar Contraseña
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}

// Alert Preferences Settings Component
function PreferencesSettings() {
  const queryClient = useQueryClient()

  const { data: preferences, isLoading } = useQuery({
    queryKey: ['alert-preferences'],
    queryFn: alertPreferencesApi.get,
  })

  const [formData, setFormData] = useState<Partial<UserAlertPreference>>({})

  // Initialize form when data loads
  useEffect(() => {
    if (preferences) {
      setFormData(preferences)
    }
  }, [preferences])

  const updateMutation = useMutation({
    mutationFn: alertPreferencesApi.update,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-preferences'] })
      toast.success('Preferencias actualizadas')
    },
    onError: () => toast.error('Error al actualizar preferencias'),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    updateMutation.mutate(formData)
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    )
  }

  const currentPrefs = { ...preferences, ...formData }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Preferencias de Alertas</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6 max-w-lg">
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-secondary-700">Recibir alertas de:</h3>
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={currentPrefs.receive_low_stock ?? true}
                onChange={(e) =>
                  setFormData({ ...formData, receive_low_stock: e.target.checked })
                }
                className="rounded border-secondary-300"
              />
              <span className="text-sm text-secondary-700">Stock bajo</span>
            </label>
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={currentPrefs.receive_out_of_stock ?? true}
                onChange={(e) =>
                  setFormData({ ...formData, receive_out_of_stock: e.target.checked })
                }
                className="rounded border-secondary-300"
              />
              <span className="text-sm text-secondary-700">Sin stock</span>
            </label>
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={currentPrefs.receive_cash_difference ?? true}
                onChange={(e) =>
                  setFormData({ ...formData, receive_cash_difference: e.target.checked })
                }
                className="rounded border-secondary-300"
              />
              <span className="text-sm text-secondary-700">Diferencia de caja</span>
            </label>
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={currentPrefs.receive_void_alerts ?? true}
                onChange={(e) =>
                  setFormData({ ...formData, receive_void_alerts: e.target.checked })
                }
                className="rounded border-secondary-300"
              />
              <span className="text-sm text-secondary-700">Cancelaciones excesivas</span>
            </label>
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={currentPrefs.receive_shift_alerts ?? true}
                onChange={(e) =>
                  setFormData({ ...formData, receive_shift_alerts: e.target.checked })
                }
                className="rounded border-secondary-300"
              />
              <span className="text-sm text-secondary-700">Alertas de turno</span>
            </label>
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={currentPrefs.receive_system_alerts ?? true}
                onChange={(e) =>
                  setFormData({ ...formData, receive_system_alerts: e.target.checked })
                }
                className="rounded border-secondary-300"
              />
              <span className="text-sm text-secondary-700">Alertas del sistema</span>
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-2">
              Severidad mínima
            </label>
            <Select
              value={currentPrefs.minimum_severity || 'low'}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  minimum_severity: e.target.value as 'low' | 'medium' | 'high' | 'critical',
                })
              }
            >
              <option value="low">Baja (todas las alertas)</option>
              <option value="medium">Media</option>
              <option value="high">Alta</option>
              <option value="critical">Crítica (solo urgentes)</option>
            </Select>
          </div>

          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={currentPrefs.email_digest ?? false}
              onChange={(e) => setFormData({ ...formData, email_digest: e.target.checked })}
              className="rounded border-secondary-300"
            />
            <span className="text-sm text-secondary-700">Recibir resumen diario por email</span>
          </label>

          <Button type="submit" isLoading={updateMutation.isPending}>
            <Save className="h-4 w-4 mr-2" />
            Guardar Preferencias
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}

// Users Management Component (Admin)
function UsersSettings() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [isFormModalOpen, setIsFormModalOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [isResetPwdModalOpen, setIsResetPwdModalOpen] = useState(false)

  const { data: usersData, isLoading } = useQuery({
    queryKey: ['users', { search, page }],
    queryFn: () => usersApi.getAll({ search: search || undefined, page, page_size: 20 }),
  })

  const { data: roles } = useQuery({
    queryKey: ['roles'],
    queryFn: rolesApi.getAll,
  })

  const { data: branches } = useQuery({
    queryKey: ['branches-simple'],
    queryFn: branchesApi.getSimple,
  })

  const deleteMutation = useMutation({
    mutationFn: usersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      toast.success('Usuario eliminado')
      setIsDeleteModalOpen(false)
      setSelectedUser(null)
    },
    onError: () => toast.error('Error al eliminar usuario'),
  })

  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, activate }: { id: number; activate: boolean }) =>
      activate ? usersApi.activate(id) : usersApi.deactivate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      toast.success('Estado actualizado')
    },
    onError: () => toast.error('Error al actualizar estado'),
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <Input
          placeholder="Buscar usuarios..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value)
            setPage(1)
          }}
          className="w-64"
        />
        <Button
          onClick={() => {
            setSelectedUser(null)
            setIsFormModalOpen(true)
          }}
        >
          <Plus className="h-4 w-4 mr-2" />
          Nuevo Usuario
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Usuario</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Rol</TableHead>
                  <TableHead>Sucursal</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {usersData?.results.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell className="font-medium">{user.full_name}</TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      <Badge variant="info">{user.role_name || 'Sin rol'}</Badge>
                    </TableCell>
                    <TableCell>{user.default_branch_name || '-'}</TableCell>
                    <TableCell>
                      <Badge variant={user.is_active ? 'success' : 'secondary'}>
                        {user.is_active ? 'Activo' : 'Inactivo'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setSelectedUser(user)
                            setIsFormModalOpen(true)
                          }}
                          title="Editar"
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setSelectedUser(user)
                            setIsResetPwdModalOpen(true)
                          }}
                          title="Restablecer contraseña"
                        >
                          <Key className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            toggleActiveMutation.mutate({ id: user.id, activate: !user.is_active })
                          }
                          title={user.is_active ? 'Desactivar' : 'Activar'}
                        >
                          {user.is_active ? (
                            <UserX className="h-4 w-4" />
                          ) : (
                            <UserCheck className="h-4 w-4" />
                          )}
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setSelectedUser(user)
                            setIsDeleteModalOpen(true)
                          }}
                          title="Eliminar"
                        >
                          <Trash2 className="h-4 w-4 text-danger-500" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* User Form Modal */}
      <UserFormModal
        isOpen={isFormModalOpen}
        onClose={() => {
          setIsFormModalOpen(false)
          setSelectedUser(null)
        }}
        user={selectedUser}
        roles={roles || []}
        branches={branches || []}
      />

      {/* Delete Modal */}
      <Modal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        title="Eliminar Usuario"
      >
        <div className="py-4">
          <div className="flex items-center gap-3 p-4 bg-danger-50 rounded-lg mb-4">
            <AlertTriangle className="h-6 w-6 text-danger-500" />
            <p className="text-danger-800">Esta acción no se puede deshacer</p>
          </div>
          <p className="text-secondary-600">
            ¿Eliminar al usuario <strong>{selectedUser?.full_name}</strong>?
          </p>
        </div>
        <ModalFooter>
          <Button variant="outline" onClick={() => setIsDeleteModalOpen(false)}>
            Cancelar
          </Button>
          <Button
            variant="danger"
            onClick={() => selectedUser && deleteMutation.mutate(selectedUser.id)}
            isLoading={deleteMutation.isPending}
          >
            Eliminar
          </Button>
        </ModalFooter>
      </Modal>

      {/* Reset Password Modal */}
      <ResetPasswordModal
        isOpen={isResetPwdModalOpen}
        onClose={() => {
          setIsResetPwdModalOpen(false)
          setSelectedUser(null)
        }}
        user={selectedUser}
      />
    </div>
  )
}

// User Form Modal
function UserFormModal({
  isOpen,
  onClose,
  user,
  roles,
  branches,
}: {
  isOpen: boolean
  onClose: () => void
  user: User | null
  roles: Role[]
  branches: BranchSimple[]
}) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<CreateUserRequest & { password_confirm?: string }>({
    email: '',
    password: '',
    password_confirm: '',
    first_name: '',
    last_name: '',
    role: undefined,
    default_branch: undefined,
    is_active: true,
  })

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      if (user) {
        setFormData({
          email: user.email,
          password: '',
          first_name: user.first_name,
          last_name: user.last_name,
          role: user.role?.id,
          default_branch: user.default_branch || undefined,
          is_active: user.is_active,
        })
      } else {
        setFormData({
          email: '',
          password: '',
          password_confirm: '',
          first_name: '',
          last_name: '',
          role: undefined,
          default_branch: undefined,
          is_active: true,
        })
      }
    }
  }, [isOpen, user])

  const createMutation = useMutation({
    mutationFn: usersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      toast.success('Usuario creado')
      onClose()
    },
    onError: () => toast.error('Error al crear usuario'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateUserRequest }) => usersApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      toast.success('Usuario actualizado')
      onClose()
    },
    onError: () => toast.error('Error al actualizar usuario'),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!user && formData.password !== formData.password_confirm) {
      toast.error('Las contraseñas no coinciden')
      return
    }

    if (user) {
      const { password, password_confirm, ...updateData } = formData
      updateMutation.mutate({ id: user.id, data: updateData })
    } else {
      const { password_confirm, ...createData } = formData
      createMutation.mutate(createData)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={user ? 'Editar Usuario' : 'Nuevo Usuario'}>
      <form onSubmit={handleSubmit}>
        <div className="space-y-4 py-4">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Nombre *"
              value={formData.first_name}
              onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              required
            />
            <Input
              label="Apellido *"
              value={formData.last_name}
              onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              required
            />
          </div>
          <Input
            label="Email *"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            required
          />
          {!user && (
            <>
              <Input
                label="Contraseña *"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
              />
              <Input
                label="Confirmar Contraseña *"
                type="password"
                value={formData.password_confirm || ''}
                onChange={(e) => setFormData({ ...formData, password_confirm: e.target.value })}
                required
              />
            </>
          )}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-secondary-700 mb-2">Rol</label>
              <Select
                value={formData.role || ''}
                onChange={(e) =>
                  setFormData({ ...formData, role: e.target.value ? Number(e.target.value) : undefined })
                }
              >
                <option value="">Sin rol</option>
                {roles.map((role) => (
                  <option key={role.id} value={role.id}>
                    {role.name}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary-700 mb-2">
                Sucursal por defecto
              </label>
              <Select
                value={formData.default_branch || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    default_branch: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
              >
                <option value="">Sin sucursal</option>
                {branches.map((branch) => (
                  <option key={branch.id} value={branch.id}>
                    {branch.name}
                  </option>
                ))}
              </Select>
            </div>
          </div>
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="rounded border-secondary-300"
            />
            <span className="text-sm text-secondary-700">Usuario activo</span>
          </label>
        </div>
        <ModalFooter>
          <Button type="button" variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" isLoading={createMutation.isPending || updateMutation.isPending}>
            {user ? 'Actualizar' : 'Crear'}
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  )
}

// Reset Password Modal
function ResetPasswordModal({
  isOpen,
  onClose,
  user,
}: {
  isOpen: boolean
  onClose: () => void
  user: User | null
}) {
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  const resetMutation = useMutation({
    mutationFn: (newPassword: string) => usersApi.resetPassword(user!.id, newPassword),
    onSuccess: () => {
      toast.success('Contraseña restablecida')
      onClose()
      setPassword('')
      setConfirmPassword('')
    },
    onError: () => toast.error('Error al restablecer contraseña'),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (password !== confirmPassword) {
      toast.error('Las contraseñas no coinciden')
      return
    }
    if (password.length < 8) {
      toast.error('La contraseña debe tener al menos 8 caracteres')
      return
    }
    resetMutation.mutate(password)
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Restablecer Contraseña">
      <form onSubmit={handleSubmit}>
        <div className="space-y-4 py-4">
          <p className="text-secondary-600">
            Establecer nueva contraseña para <strong>{user?.full_name}</strong>
          </p>
          <Input
            label="Nueva Contraseña"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <Input
            label="Confirmar Contraseña"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />
        </div>
        <ModalFooter>
          <Button type="button" variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" isLoading={resetMutation.isPending}>
            Restablecer
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  )
}

// Roles Management Component (Admin)
function RolesSettings() {
  const queryClient = useQueryClient()
  const [selectedRole, setSelectedRole] = useState<Role | null>(null)
  const [isFormModalOpen, setIsFormModalOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)

  const { data: roles, isLoading } = useQuery({
    queryKey: ['roles'],
    queryFn: rolesApi.getAll,
  })

  const { data: permissions } = useQuery({
    queryKey: ['permissions'],
    queryFn: permissionsApi.getAll,
  })

  const deleteMutation = useMutation({
    mutationFn: rolesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] })
      toast.success('Rol eliminado')
      setIsDeleteModalOpen(false)
      setSelectedRole(null)
    },
    onError: () => toast.error('Error al eliminar rol'),
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <Button
          onClick={() => {
            setSelectedRole(null)
            setIsFormModalOpen(true)
          }}
        >
          <Plus className="h-4 w-4 mr-2" />
          Nuevo Rol
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {roles?.map((role) => (
            <Card key={role.id}>
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-lg">{role.name}</CardTitle>
                    <Badge variant={role.role_type === 'system' ? 'secondary' : 'info'}>
                      {role.role_type === 'system' ? 'Sistema' : 'Personalizado'}
                    </Badge>
                  </div>
                  {role.role_type !== 'system' && (
                    <div className="flex gap-1">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedRole(role)
                          setIsFormModalOpen(true)
                        }}
                      >
                        <Edit2 className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedRole(role)
                          setIsDeleteModalOpen(true)
                        }}
                      >
                        <Trash2 className="h-4 w-4 text-danger-500" />
                      </Button>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-secondary-500 mb-3">{role.description || 'Sin descripción'}</p>
                <div className="text-xs text-secondary-400">
                  {role.permissions.length} permisos asignados
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Role Form Modal */}
      <RoleFormModal
        isOpen={isFormModalOpen}
        onClose={() => {
          setIsFormModalOpen(false)
          setSelectedRole(null)
        }}
        role={selectedRole}
        permissions={permissions || []}
      />

      {/* Delete Modal */}
      <Modal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        title="Eliminar Rol"
      >
        <div className="py-4">
          <p className="text-secondary-600">
            ¿Eliminar el rol <strong>{selectedRole?.name}</strong>?
          </p>
          <p className="text-sm text-secondary-500 mt-2">
            Los usuarios con este rol perderán sus permisos asociados.
          </p>
        </div>
        <ModalFooter>
          <Button variant="outline" onClick={() => setIsDeleteModalOpen(false)}>
            Cancelar
          </Button>
          <Button
            variant="danger"
            onClick={() => selectedRole && deleteMutation.mutate(selectedRole.id)}
            isLoading={deleteMutation.isPending}
          >
            Eliminar
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  )
}

// Role Form Modal
function RoleFormModal({
  isOpen,
  onClose,
  role,
  permissions,
}: {
  isOpen: boolean
  onClose: () => void
  role: Role | null
  permissions: Permission[]
}) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    permissions: [] as number[],
  })

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      if (role) {
        setFormData({
          name: role.name,
          description: role.description,
          permissions: role.permissions.map((p) => p.id),
        })
      } else {
        setFormData({ name: '', description: '', permissions: [] })
      }
    }
  }, [isOpen, role])

  const createMutation = useMutation({
    mutationFn: rolesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] })
      toast.success('Rol creado')
      onClose()
    },
    onError: () => toast.error('Error al crear rol'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Role> }) => rolesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] })
      toast.success('Rol actualizado')
      onClose()
    },
    onError: () => toast.error('Error al actualizar rol'),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (role) {
      updateMutation.mutate({ id: role.id, data: formData })
    } else {
      createMutation.mutate(formData)
    }
  }

  const togglePermission = (permId: number) => {
    setFormData((prev) => ({
      ...prev,
      permissions: prev.permissions.includes(permId)
        ? prev.permissions.filter((id) => id !== permId)
        : [...prev.permissions, permId],
    }))
  }

  // Group permissions by module
  const groupedPermissions = permissions.reduce(
    (acc, perm) => {
      if (!acc[perm.module]) acc[perm.module] = []
      acc[perm.module].push(perm)
      return acc
    },
    {} as Record<string, Permission[]>
  )

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={role ? 'Editar Rol' : 'Nuevo Rol'} size="lg">
      <form onSubmit={handleSubmit}>
        <div className="space-y-4 py-4">
          <Input
            label="Nombre *"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
          <Input
            label="Descripción"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-3">Permisos</label>
            <div className="space-y-4 max-h-64 overflow-y-auto border rounded-lg p-4">
              {Object.entries(groupedPermissions).map(([module, perms]) => (
                <div key={module}>
                  <h4 className="text-sm font-medium text-secondary-800 capitalize mb-2">
                    {module}
                  </h4>
                  <div className="grid grid-cols-2 gap-2">
                    {perms.map((perm) => (
                      <label key={perm.id} className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={formData.permissions.includes(perm.id)}
                          onChange={() => togglePermission(perm.id)}
                          className="rounded border-secondary-300"
                        />
                        <span className="text-sm text-secondary-600">{perm.description}</span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <ModalFooter>
          <Button type="button" variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" isLoading={createMutation.isPending || updateMutation.isPending}>
            {role ? 'Actualizar' : 'Crear'}
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  )
}
