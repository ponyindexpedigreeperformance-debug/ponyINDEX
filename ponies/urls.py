from django.urls import path
from . import views

app_name = 'ponies'

urlpatterns = [
    path('', views.index, name='index'),
    path('myindex/', views.myindex, name='myindex'),
    path('search/', views.pony_search, name='pony_search'),
    path('stallions/', views.stallions_at_stud, name='stallions_at_stud'),
    path('add/', views.add_pony, name='add_pony'),
    path('contact/', views.contact, name='contact'),

    path('import/ponies/', views.import_ponies, name='import_ponies'),

    path('pony/<int:pk>/', views.pony_detail, name='pony_detail'),
    path('pony-autocomplete/', views.pony_autocomplete, name='pony_autocomplete'),

    # Approval system
    path('approve-dashboard/', views.approve_dashboard, name='approve_dashboard'),
    path('approve-pony/<int:pony_id>/', views.approve_pony, name='approve_pony'),
    path('reject-pony/<int:pony_id>/', views.reject_pony, name='reject_pony'),
    path('approve-all/', views.approve_all_ponies, name='approve_all_ponies'),
]