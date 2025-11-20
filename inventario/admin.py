from django.contrib import admin
from .models import Producto

admin.site.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'precio', 'stock', 'stock_minimo', 'categoria', 'necesita_reabastecimiento']
    list_filter = ['categoria', 'necesita_reabastecimiento']
    search_fields = ['nombre', 'descripcion']
    list_editable = ['precio', 'stock']
    
    def necesita_reabastecimiento(self, obj):
        return obj.necesita_reabastecimiento()
    necesita_reabastecimiento.boolean = True
    necesita_reabastecimiento.short_description = '¿Necesita Reabastecer?'


from .models import Venta

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ['producto', 'cantidad', 'precio_venta', 'total_venta', 'fecha_venta', 'vendedor']
    list_filter = ['fecha_venta', 'vendedor', 'producto']
    search_fields = ['producto__nombre', 'vendedor']
    readonly_fields = ['fecha_venta', 'total_venta']
    list_editable = ['cantidad', 'precio_venta']
    
    fieldsets = (
        ('Información de Venta', {
            'fields': ('producto', 'cantidad', 'precio_venta', 'total_venta')
        }),
        ('Información Adicional', {
            'fields': ('vendedor', 'observaciones', 'fecha_venta')
        }),
    )