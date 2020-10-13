from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from banned_list.models import DataList, Parser

class CMTAdminSite(admin.AdminSite):
    site_header = 'CMT Administration'
    site_url = "https://www.compliance-mt.com"

class ParserAdmin(admin.ModelAdmin):
    fields = ('name', 'active')

admin_site = CMTAdminSite(name='cmtadmin')
admin_site.register(User, UserAdmin)
admin_site.register(Parser, ParserAdmin)

admin_site.register(DataList)