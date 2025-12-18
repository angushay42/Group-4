from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from expiry.forms import ForgotPassForm

urlpatterns = [
    path('', views.startup, name='startup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('settings/', views.settings, name='settings'),
    path('items/', views.items_list, name='items'),
    path('add-item/', views.add_item_view, name='add_item'),
    path("items/<int:item_id>/edit/", views.edit_item_view, name="edit_item"),
    # path("items/<int:item_id>/delete/", views.delete_item, name='delete_item'),   #todo might need again
    path('history/', views.history, name='history'),
    path('forgot_password/', 
        auth_views.PasswordResetView.as_view(
            template_name='expiry/forgot_password.html',  # your template
            form_class=ForgotPassForm,
            email_template_name='emails/password_reset_email.html',  # the email template
            subject_template_name='emails/password_reset_subject.txt',
            success_url='/forgot_password/done/'
        ), 
        name='password_reset'
    ),
    path('forgot_password/done/', 
        auth_views.PasswordResetDoneView.as_view(
            template_name='expiry/forgot_password_done.html'
        ), 
        name='password_reset_done'
    ),
    path('reset/<uidb64>/<token>/', 
        auth_views.PasswordResetConfirmView.as_view(
            template_name='expiry/forgot_password_confirm.html',
            success_url='/reset/done/'
        ), 
        name='password_reset_confirm'
    ),
    path('reset/done/', 
        auth_views.PasswordResetCompleteView.as_view(
            template_name='expiry/forgot_password_complete.html'
        ), 
        name='password_reset_complete'
    ),
]
