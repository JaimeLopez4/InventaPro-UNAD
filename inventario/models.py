from django.db import models

class Producto(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Producto")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    precio = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Precio Unitario"
    )
    stock = models.IntegerField(default=0, verbose_name="Cantidad en Stock")
    stock_minimo = models.IntegerField(default=5, verbose_name="Stock Mínimo")
    categoria = models.CharField(
        max_length=50, 
        default="General", 
        verbose_name="Categoría"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} (Stock: {self.stock})"
    
    def necesita_reabastecimiento(self):
        return self.stock <= self.stock_minimo
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        


class Venta(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, verbose_name="Producto Vendido")
    cantidad = models.IntegerField(verbose_name="Cantidad Vendida")
    precio_venta = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Precio de Venta"
    )
    fecha_venta = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Venta")
    vendedor = models.CharField(max_length=100, default="Sistema", verbose_name="Vendedor")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    
    def total_venta(self):
        return self.cantidad * self.precio_venta
    total_venta.short_description = "Total Venta"
    
    def __str__(self):
        return f"Venta: {self.producto.nombre} x{self.cantidad}"
    
    def save(self, *args, **kwargs):
        # Actualizar el stock automáticamente al guardar una venta
        if not self.pk:  # Solo si es una nueva venta
            self.producto.stock -= self.cantidad
            self.producto.save()
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-fecha_venta']