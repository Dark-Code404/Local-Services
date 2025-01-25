from django.urls import path
from jobs import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('register/', views.register, name='register'),
    path('', views.home, name='home'),
    path('add_job/', views.add_job, name='add_job'),
    path('jobs-nearby/', views.search_jobs_by_location, name='search_jobs_by_location'),
    path('apply-job/<int:job_id>/', views.apply_job, name='apply_job'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='log_out.html'), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('job_details/<int:job_id>/', views.job_detail, name='job_detail'),
    path('applicants', views.jobApplicants, name='applicants'),

    path('delete_job/<int:job_id>/', views.delete_job, name='delete_job'),
    path('job/<int:job_id>/mark_fulfilled/', views.mark_fulfilled, name='mark_fulfilled'),
    path('applicant/payment/<int:applicant_id>/hire/', views.initiateKhaltiPayment, name='initiate_khalti_payment'),
    path('payment_success/', views.paymentSuccess, name='payment_success'),
    path('amounts/<int:applicant_id>/', views.amounts, name='amounts'),


    


     path('register/', views.register, name='register'),
    path('verify-email/', views.verify_email, name='verify_email'),
]
