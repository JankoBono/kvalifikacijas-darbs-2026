from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path("", views.index, name="index"),
    path('add-darijums/', views.addDarijums, name="add-darijums"),
    path('edit-darijums/<str:pk>/', views.editDarijums, name="edit-darijums"),
    path('delete-darijums/<str:pk>/', views.deleteDarijums, name="delete-darijums"),
    path("plani/", views.planuLapa, name="plani"),
    path('add-plans/', views.addPlans, name="add-plans"),
    path('edit-plans/<str:pk>/', views.editPlans, name="edit-plans"),
    path('delete-plans/<str:pk>/', views.deletePlans, name="delete-plans"),
    path('veikala-plans/', views.veikalaPlans, name='veikala-plans'),
    path('mani-darijumi/', views.maniDarijumi, name='mani-darijumi'),
]