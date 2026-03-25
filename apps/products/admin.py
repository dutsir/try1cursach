from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'dns_category_slug', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'vendor_code', 'is_active', 'last_parsed_at')
    list_filter = ('is_active', 'category')
    search_fields = ('name', 'vendor_code')
    raw_id_fields = ('category',)
    readonly_fields = ('last_parsed_at',)
