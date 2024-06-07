from django.contrib import admin


class CustomAdminSite(admin.AdminSite):
    site_header = 'Administration'


# Register the custom admin site
admin_site = CustomAdminSite(name='customadmin')
admin.site.site_header = "AITechLand Administration"
admin.site.site_title = "AITechLand"
admin.site.index_title = "AITechLand"