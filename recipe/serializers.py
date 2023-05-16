from rest_framework import serializers
from core.models import Recipe, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only = ['id']


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'tags']
        read_only = ['id']

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(**validated_data)
        auth_user = self.context['request'].user

        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag
            )
            recipe.tags.add(tag_obj)

        return recipe


class RecipeDetailSerializer(RecipeSerializer):
    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        auth_user = self.context['request'].user
        recipe = super().update(instance, validated_data)
        instance.tags.clear()
        if tags is not None:
            for tag in tags:
                tag_obj, created = Tag.objects.get_or_create(
                    user=auth_user,
                    **tag
                )
                instance.tags.add(tag_obj)

        return recipe
