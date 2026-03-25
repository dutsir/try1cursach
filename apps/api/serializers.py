from rest_framework import serializers

from apps.alerts.models import Notification, Subscription
from apps.analytics.models import Anomaly
from apps.prices.models import PriceHistory
from apps.products.models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'is_active')


class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    current_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'category', 'vendor_code',
            'url', 'image_url', 'is_active', 'last_parsed_at', 'current_price',
        )

    def get_current_price(self, obj: Product) -> str | None:
        record = (
            obj.price_history
            .filter(is_actual=True)
            .order_by('-timestamp')
            .first()
        )
        return str(record.price) if record else None


class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = ('id', 'price', 'old_price', 'timestamp', 'is_actual', 'source')


class ProductDetailSerializer(ProductListSerializer):
    price_history = PriceHistorySerializer(many=True, read_only=True)

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + ('price_history',)


class SubscriptionSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = Subscription
        fields = ('id', 'product', 'product_name', 'target_price', 'is_active', 'created_at')
        read_only_fields = ('is_active', 'created_at')

    def validate_product(self, value: Product) -> Product:
        user = self.context['request'].user
        if Subscription.objects.filter(user=user, product=value).exists():
            raise serializers.ValidationError('Подписка на этот товар уже существует.')
        return value

    def create(self, validated_data: dict) -> Subscription:
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'message', 'sent_at')


class AnomalySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = Anomaly
        fields = (
            'id', 'product', 'product_name', 'anomaly_type',
            'severity', 'description', 'detected_at', 'resolved',
        )
