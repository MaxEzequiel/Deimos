# Seguimiento de mensualidades

Abrí **Mensualidades** en el menú lateral (`/payments/`).

1. Como administrador, elegí **Generar cuotas del mes**, el mes calendario y el día de vencimiento (10 por defecto).
2. Se genera una cuota por cuenta activa con perfil en `Person`. Se utiliza el precio del plan del perfil; si no tiene plan, se utiliza el de su membresía. Las cuentas dadas de alta después de ese mes y los perfiles sin plan con precio positivo no generan cuota.
3. En **Registrar pago**, ingresá la fecha, el medio de pago y, opcionalmente, la referencia del comprobante. Se registra el pago completo del importe de la cuota y quién lo registró.
4. Filtrá por mes, socio o estado para consultar importes cobrados y pendientes. Una cuota impaga pasa a vencida al día siguiente de su vencimiento.

Los socios pueden consultar únicamente sus propias cuotas. Los superusuarios tienen acceso completo. Para delegar la gestión, asigná al grupo los permisos de **Mensualidades** desde la administración de grupos: **Ver** para consultar todas las cuotas, **Añadir** junto con **Ver** para generarlas, y **Cambiar** junto con **Ver** para registrar cobros.

La generación repetida no duplica cuotas ni actualiza sus importes históricos. Los cambios posteriores de precio del plan afectan a las nuevas cuotas. Las cuotas se generan manualmente cada mes; no se crea deuda histórica automáticamente. El pago se registra manualmente y no procesa cobros bancarios. No se contemplan pagos parciales ni cambios automáticos del estado de membresía.

Para instalar la tabla en otra copia del proyecto, desde la raíz del repositorio:

```powershell
.\venv\Scripts\python.exe crud_auth_original\manage.py migrate pagos
```

Para verificar el módulo:

```powershell
.\venv\Scripts\python.exe crud_auth_original\manage.py test payments
```
