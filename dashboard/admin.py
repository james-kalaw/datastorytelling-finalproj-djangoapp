from django.contrib import admin

from .models import Insight, PowerBIPage, Recommendation

admin.site.register(PowerBIPage)
admin.site.register(Insight)
admin.site.register(Recommendation)
