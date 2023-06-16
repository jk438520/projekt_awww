from rest_framework import serializers
from web_ide.models import *


class FileSerializer(serializers.ModelSerializer):
    content_by_sections = serializers.SerializerMethodField()
    compiled_content_by_sections = serializers.SerializerMethodField()

    def get_content_by_sections(self, obj):
        return obj.get_content_by_sections()

    def get_compiled_content_by_sections(self, obj):
        return obj.get_compiled_content_by_sections()

    class Meta:
        model = File
        fields = ['name',
                  'pk',
                  'description',
                  'content',
                  'content_by_sections',
                  'compiled_content',
                  'compiled_content_by_sections']
