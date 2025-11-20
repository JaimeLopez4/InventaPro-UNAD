from django.db import models 
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from .models import Producto, Venta
from django.contrib import messages
from django.db.models import Sum, Count, Avg
from datetime import datetime, timedelta
import json

def inicio(request):
    """Página de inicio del sistema con dashboard"""
    from django.utils import timezone
    from datetime import datetime
    
    # Métricas principales
    total_productos = Producto.objects.count()
    productos_stock_bajo = Producto.objects.filter(stock__lte=models.F('stock_minimo'))
    total_ventas = Venta.objects.count()
    
    # Ingresos del mes actual
    hoy = timezone.now()
    primer_dia_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ventas_mes = Venta.objects.filter(fecha_venta__gte=primer_dia_mes)
    ingresos_mes = sum(venta.total_venta() for venta in ventas_mes)
    
    # Últimas 5 ventas
    ultimas_ventas = Venta.objects.all().order_by('-fecha_venta')[:5]
    
    context = {
        'total_productos': total_productos,
        'productos_alerta': productos_stock_bajo.count(),
        'productos_stock_bajo': productos_stock_bajo,
        'total_ventas': total_ventas,
        'ingresos_mes': ingresos_mes,
        'ultimas_ventas': ultimas_ventas,
    }
    return render(request, 'inventario/inicio.html', context)

def lista_productos(request):
    """Vista para mostrar la lista de todos los productos con filtros"""
    # Obtener parámetros de búsqueda
    query = request.GET.get('q', '')
    categoria = request.GET.get('categoria', '')
    stock_bajo = request.GET.get('stock_bajo', '')
    
    productos = Producto.objects.all().order_by('nombre')
    
    # Aplicar filtros
    if query:
        productos = productos.filter(nombre__icontains=query)
    if categoria:
        productos = productos.filter(categoria=categoria)
    if stock_bajo:
        productos = productos.filter(stock__lte=models.F('stock_minimo'))
    
    # Productos que necesitan reabastecimiento
    productos_alerta = [p for p in productos if p.stock <= p.stock_minimo]
    
    # Categorías predefinidas para el filtro
    categorias_predefinidas = [
        'Frutas', 'Verduras', 'Lácteos', 'Carnes', 'Granos', 
        'Bebidas', 'Snacks', 'Limpieza', 'Higiene', 'Electrónicos', 
        'Ropa', 'General', 'Otros'
    ]
    
    context = {
        'productos': productos,
        'productos_alerta': productos_alerta,
        'total_productos': productos.count(),
        'total_alerta': len(productos_alerta),
        'categorias': categorias_predefinidas,
        'query_actual': query,
        'categoria_actual': categoria,
        'stock_bajo_actual': stock_bajo,
    }
    return render(request, 'inventario/lista_productos.html', context)

def reporte_ventas(request):
    """Reporte de ventas y estadísticas"""
    # Ventas de los últimos 7 días
    fecha_inicio = timezone.now() - timedelta(days=7)
    ventas_recientes = Venta.objects.filter(fecha_venta__gte=fecha_inicio)
    
    # Estadísticas
    total_ventas = ventas_recientes.count()
    ingreso_total = sum(venta.total_venta() for venta in ventas_recientes)
    
    # Producto más vendido
    productos_vendidos = Venta.objects.values('producto__nombre').annotate(
        total_vendido=Sum('cantidad')
    ).order_by('-total_vendido')
    
    producto_mas_vendido = productos_vendidos.first()
    
    context = {
        'ventas_recientes': ventas_recientes,
        'total_ventas': total_ventas,
        'ingreso_total': ingreso_total,
        'producto_mas_vendido': producto_mas_vendido,
        'productos_vendidos': productos_vendidos[:5]  # Top 5
    }
    return render(request, 'inventario/reporte_ventas.html', context)

def realizar_venta(request):
    """Página para registrar nuevas ventas"""
    productos = Producto.objects.filter(stock__gt=0)  # Solo productos con stock
    
    # Obtener últimas 10 ventas para mostrar en el panel
    ultimas_ventas = Venta.objects.all().order_by('-fecha_venta')[:10]
    
    if request.method == 'POST':
        producto_id = request.POST.get('producto')
        cantidad = int(request.POST.get('cantidad', 1))
        vendedor = request.POST.get('vendedor', 'Sistema')
        
        producto = Producto.objects.get(id=producto_id)
        
        # Verificar stock disponible
        if cantidad <= producto.stock:
            # Crear la venta
            venta = Venta(
                producto=producto,
                cantidad=cantidad,
                precio_venta=producto.precio,
                vendedor=vendedor
            )
            venta.save()
            
            return render(request, 'inventario/venta_exitosa.html', {
                'venta': venta,
                'producto': producto
            })
        else:
            return render(request, 'inventario/realizar_venta.html', {
                'productos': productos,
                'ultimas_ventas': ultimas_ventas,
                'error': f'Stock insuficiente. Solo hay {producto.stock} unidades disponibles.'
            })
    
    return render(request, 'inventario/realizar_venta.html', {
        'productos': productos,
        'ultimas_ventas': ultimas_ventas
    })

def agregar_producto(request):
    """Vista para agregar nuevo producto"""
    if request.method == 'POST':
        # Procesar el formulario
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        precio = request.POST.get('precio')
        stock = request.POST.get('stock')
        stock_minimo = request.POST.get('stock_minimo')
        categoria = request.POST.get('categoria')
        
        # Crear el producto
        producto = Producto(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            stock=stock,
            stock_minimo=stock_minimo,
            categoria=categoria
        )
        producto.save()
        
        messages.success(request, f'Producto "{nombre}" agregado correctamente!')
        return redirect('lista_productos')
    
    # Si es GET, mostrar el formulario vacío
    return render(request, 'inventario/agregar_producto.html')

def editar_producto(request, producto_id):
    """Vista para editar producto existente"""
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        # Actualizar el producto
        producto.nombre = request.POST.get('nombre')
        producto.descripcion = request.POST.get('descripcion')
        producto.precio = request.POST.get('precio')
        producto.stock = request.POST.get('stock')
        producto.stock_minimo = request.POST.get('stock_minimo')
        producto.categoria = request.POST.get('categoria')
        producto.save()
        
        messages.success(request, f'Producto "{producto.nombre}" actualizado correctamente!')
        return redirect('lista_productos')
    
    # Si es GET, mostrar el formulario con datos actuales
    return render(request, 'inventario/editar_producto.html', {'producto': producto})

def eliminar_producto(request, producto_id):
    """Vista para eliminar producto"""
    producto = get_object_or_404(Producto, id=producto_id)
    nombre_producto = producto.nombre
    
    if request.method == 'POST':
        producto.delete()
        messages.success(request, f'Producto "{nombre_producto}" eliminado correctamente!')
        return redirect('lista_productos')
    
    # Si alguien intenta acceder por GET, redirigir a la lista
    return redirect('lista_productos')

def informe_personalizado(request):
    """Vista principal del informe personalizado"""
    # Fechas por defecto (últimos 30 días)
    fecha_inicio_default = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    fecha_fin_default = timezone.now().strftime('%Y-%m-%d')
    
    # Obtener fechas del formulario o usar defaults
    fecha_inicio = request.GET.get('fecha_inicio', fecha_inicio_default)
    fecha_fin = request.GET.get('fecha_fin', fecha_fin_default)
    
    # Convertir a objetos datetime
    try:
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
    except:
        fecha_inicio_dt = datetime.strptime(fecha_inicio_default, '%Y-%m-%d')
        fecha_fin_dt = datetime.strptime(fecha_fin_default, '%Y-%m-%d')
    
    # Filtrar ventas por el rango de fechas
    ventas_filtradas = Venta.objects.filter(
        fecha_venta__date__gte=fecha_inicio_dt,
        fecha_venta__date__lte=fecha_fin_dt
    )
    
    # Métricas principales
    total_ventas = ventas_filtradas.count()
    ingreso_total = sum(venta.total_venta() for venta in ventas_filtradas)
    productos_vendidos = ventas_filtradas.aggregate(total=Sum('cantidad'))['total'] or 0
    
    # Productos más vendidos
    top_productos = ventas_filtradas.values(
        'producto__nombre', 
        'producto__categoria'
    ).annotate(
        total_vendido=Sum('cantidad'),
        ingreso_total=Sum('precio_venta')
    ).order_by('-total_vendido')[:10]
    
    # Ventas por día (para gráfico)
    ventas_por_dia = ventas_filtradas.extra(
        select={'fecha': "date(fecha_venta)"}
    ).values('fecha').annotate(
        total=Count('id'),
        ingreso=Sum('precio_venta')
    ).order_by('fecha')
    
    # Ventas por categoría
    ventas_por_categoria = ventas_filtradas.values(
        'producto__categoria'
    ).annotate(
        total_ventas=Count('id'),
        total_ingreso=Sum('precio_venta'),
        cantidad_vendida=Sum('cantidad')
    ).order_by('-total_ingreso')
    
    # Productos con stock bajo
    productos_stock_bajo = Producto.objects.filter(
        stock__lte=models.F('stock_minimo')
    ).count()
    
    # Vendedores top
    top_vendedores = ventas_filtradas.values('vendedor').annotate(
        total_ventas=Count('id'),
        total_ingreso=Sum('precio_venta')
    ).order_by('-total_ingreso')[:5]
    
    # Preparar datos para gráficos
    datos_grafico_dias = {
        'fechas': [v['fecha'] for v in ventas_por_dia],
        'ventas': [v['total'] for v in ventas_por_dia],
        'ingresos': [float(v['ingreso'] or 0) for v in ventas_por_dia]
    }
    
    datos_grafico_categorias = {
        'categorias': [v['producto__categoria'] for v in ventas_por_categoria],
        'ingresos': [float(v['total_ingreso'] or 0) for v in ventas_por_categoria]
    }
    
    context = {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'total_ventas': total_ventas,
        'ingreso_total': ingreso_total,
        'productos_vendidos': productos_vendidos,
        'top_productos': top_productos,
        'ventas_por_categoria': ventas_por_categoria,
        'productos_stock_bajo': productos_stock_bajo,
        'top_vendedores': top_vendedores,
        'datos_grafico_dias': json.dumps(datos_grafico_dias),
        'datos_grafico_categorias': json.dumps(datos_grafico_categorias),
    }
    
    return render(request, 'inventario/informe_personalizado.html', context)