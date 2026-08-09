from rest_framework import serializers
from .models import Production, ProductionIngredient

class ProductionIngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionIngredient
        fields = ['id', 'ingredient_name', 'quantity_gallon']


class ProductionSerializer(serializers.ModelSerializer):
    ingredients = ProductionIngredientSerializer(many=True, required=False)

    class Meta:
        model = Production
        fields = [
            'id', 'product_name', 'quantity_produced_kg', 'batch_number',
            'quantity_milk_used_kg', 'note', 'ingredients',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients', [])
        production = Production.objects.create(**validated_data)
        for ing in ingredients_data:
            ProductionIngredient.objects.create(production=production, **ing)
        return production

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if ingredients_data is not None:
            instance.ingredients.all().delete()
            for ing in ingredients_data:
                ProductionIngredient.objects.create(production=instance, **ing)
        return instance
