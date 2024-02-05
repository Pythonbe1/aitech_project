from django.contrib import admin


class CustomAdminSite(admin.AdminSite):
    site_header = 'Administration'


# Register the custom admin site
admin_site = CustomAdminSite(name='customadmin')
