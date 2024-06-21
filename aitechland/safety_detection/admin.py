from django import forms
from django.contrib import admin

from .models import Camera, Permission, CameraCredential, DetectionClasses, ROICoordinates


@admin.register(DetectionClasses)
class DetectionClassesAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(CameraCredential)
class CameraCredentialAdmin(admin.ModelAdmin):
    list_display = ['credential_name', 'camera_login', 'camera_password']


class ROICoordinatesInline(admin.TabularInline):
    model = ROICoordinates
    extra = 1


@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display = ['area_name', 'ip_address', 'rtsp_port', 'channel_id', 'credential_for_ip']
    filter_horizontal = ('detect_names',)
    inlines = [ROICoordinatesInline]


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'camera']


class ROICoordinatesForm(forms.ModelForm):
    class Meta:
        model = ROICoordinates
        fields = '__all__'
        widgets = {
            'x1': forms.HiddenInput(),
            'y1': forms.HiddenInput(),
            'x2': forms.HiddenInput(),
            'y2': forms.HiddenInput(),
        }


class ROICoordinatesAdmin(admin.ModelAdmin):
    form = ROICoordinatesForm

    class Media:
        js = ('safety_detection/roi_draw.js',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return form

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['canvas'] = True  # Flag to render the canvas
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['canvas'] = True  # Flag to render the canvas
        return super().add_view(request, form_url, extra_context=extra_context)


admin.site.register(ROICoordinates, ROICoordinatesAdmin)
