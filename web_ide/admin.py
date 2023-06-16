from django.contrib import admin

# Register your models here.

from .models import *

admin.site.register(FileSystemObject)
admin.site.register(Directory)
admin.site.register(File)
admin.site.register(FileSection)
