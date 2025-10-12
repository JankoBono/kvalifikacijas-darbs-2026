from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path("", views.index, name="index"),
    path('add-darijums/', views.addDarijums, name="add-darijums"),
    path('edit-darijums/<str:pk>/', views.editDarijums, name="edit-darijums"),
    path('delete-darijums/<str:pk>/', views.deleteDarijums, name="delete-darijums"),
]