import os
import random
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.urls import reverse
import requests
from .models import Job, JobApplication, CustomUser
from .forms import CustomUserCreationForm, JobForm, JobApplicationForm
from decouple import config


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False   
            user.save()

            verification_code = random.randint(100000, 999999)
            request.session['verification_code'] = verification_code
            request.session['user_id'] = user.id

            send_mail(
                'Email Verification Code',
                f'Your verification code is: {verification_code}',
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            messages.success(request, 'A verification code has been sent to your email.')
            return redirect('verify_email')
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})


def verify_email(request):
    verification_code = request.session.get('verification_code')
    user_id = request.session.get('user_id')

    if not verification_code or not user_id:
        messages.error(request, 'Verification session has expired. Please register again.')
        return redirect('register')

    if request.method == 'POST':
        input_code = request.POST.get('code')

        if str(input_code) == str(verification_code):
            user = get_object_or_404(CustomUser, id=user_id)
            user.is_active = True
            user.save()

            del request.session['verification_code']
            del request.session['user_id']

            messages.success(request, 'Your email has been verified. You can now log in.')
            return redirect('login')
        else:
            messages.error(request, 'Invalid verification code. Please try again.')

    return render(request, 'emails/verify_email.html')


def home(request):
    if request.user.is_authenticated:
        if request.user.role == 'hire' or request.user.is_superuser:
            jobs = request.user.posted_jobs.all()
            return render(request, 'hire/home.html', {'jobs': jobs})
        elif request.user.role == 'worker':
            jobs = Job.objects.filter(fulfilled=False)
            return render(request, 'worker/home.html', {'jobs': jobs})
        else:
            return render(request, 'error.html', {'message': 'Invalid user role.'})
    else:
        return redirect('login')


def add_job(request):
    if not request.user.is_authenticated or request.user.role != 'hire':
        return redirect('home')

    form = JobForm()

    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
        
            job.latitude = request.POST.getlist('latitude')[0]
            job.longitude = request.POST.getlist('longitude')[0]
        
            job.save()
            messages.success(request, 'Job added successfully.')
            return redirect('home')
        else:
            messages.error(request, 'Form is invalid. Please check all fields.')

    return render(request, 'hire/add_jobs.html', {'form': form})


def search_jobs_by_location(request):
    query = request.GET.get('q', '')
    jobs = Job.objects.filter(location__icontains=query) if query else Job.objects.all()
    paginator = Paginator(jobs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'worker/search_jobs.html', {'jobs': page_obj, 'query': query})


def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.user.role == 'hire':
        return HttpResponse("Hirer cannot apply for jobs.")
    
    if job.fulfilled:
        return render(request, 'hire/job_unavailable.html', {'job': job})

    if JobApplication.objects.filter(job=job, worker=request.user).exists():
        return render(request, 'worker/job_already_applied.html', {'job': job})

    if request.method == 'POST':
        form = JobApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.worker = request.user
            application.job = job
            application.save()
            messages.success(request, 'Job application submitted successfully.')
            return redirect('home')
    else:
        form = JobApplicationForm(initial={
            'name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
        })

    return render(request, 'worker/apply_job.html', {'job': job, 'form': form})


def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    coordinates = {'x': job.longitude, 'y': job.latitude}

    return render(request, 'hire/job_detail.html', {'job': job, 'coordinates': coordinates})


def delete_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.user != job.posted_by:
        return HttpResponseForbidden("You are not allowed to delete this job.")

    if request.method == 'POST':
        job.delete()
        messages.success(request, 'Job deleted successfully.')
        return redirect('home')

    return render(request, 'hire/confirm_delete_job.html', {'job': job})


def jobApplicants(request):
    if request.user.role == 'hire':

        applicants = JobApplication.objects.all()
        context = {"applicants": applicants}
        return render(request, "applicants/applicants.html", context)


def mark_fulfilled(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.user != job.posted_by:
        return HttpResponseForbidden("You are not allowed to mark this job as fulfilled.")

    job.fulfilled = True
    job.save()
    messages.success(request, f"The job '{job.title}' has been marked as fulfilled.")
    return redirect('home')


def profile(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        profile_picture = request.FILES.get('profile_picture')

        if not username or not email:
            messages.error(request, 'Both username and email are required.')
            return redirect('profile')

        user = request.user
        user.username = username
        user.email = email

        if profile_picture:
            if user.profile_picture and os.path.exists(user.profile_picture.path):
                os.remove(user.profile_picture.path)
            user.profile_picture = profile_picture

        try:
            user.save()
            messages.success(request, 'Profile updated successfully.')
        except IntegrityError:
            messages.error(request, 'Username already exists. Please choose a different one.')
        return redirect('profile')

    return render(request, 'profile.html', {'user': request.user})


def initiateKhaltiPayment(request, applicant_id):
    if request.method == "POST":
        if not request.user.is_authenticated or request.user.role != 'hire':
            messages.error(request, "Only hirers can make payments.")
            return redirect("home")
        
        applicant = get_object_or_404(JobApplication, id=applicant_id)
        job = applicant.job

        url = config('api')
        payload = {
            "return_url": request.build_absolute_uri(reverse('payment_success')),  
            "website_url": "http://127.0.0.1:8000/applicants",
            "amount": (int(request.POST.get('amount'))*100),
            "total_amount": 1000,
            "purchase_order_id": f"hire_{applicant_id}",
            "purchase_order_name": f"Hire {applicant.name} for {job.title}",
            "customer_info": {
                "name": request.user.get_full_name() or request.user.username,
                "email": request.user.email,
                "phone":  applicant.phone_number
            },
       
        }

        # print(payload['amount'])
        headers = {
            'Authorization': config('Authorization_key'),
            'Content-Type': 'application/json',
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()

            if response.status_code == 200 and response_data.get("payment_url"):
                payment_url = response_data.get("payment_url")
                return redirect(payment_url)
            else:
                error_detail = response_data.get("detail", "Unknown error occurred.")
                messages.error(request, f"Error initiating payment: {error_detail}")

        except Exception as e:
            messages.error(request, f"An error occurred: {e}")

    return redirect('home')


def paymentSuccess(request):
    pidx = request.GET.get("pidx")
    transaction_id = request.GET.get("transaction_id")
    purchase_order_id = request.GET.get("purchase_order_id")
    status = request.GET.get("status")
    amount = request.GET.get("amount")
    mobile = request.GET.get("mobile")

    print(status)

    url = "https://dev.khalti.com/api/v2/epayment/lookup/"
    headers = {
        "Authorization":config('Authorization_key') ,
        'Content-Type': 'application/json',
    }
    payload = {
        'pidx': pidx,
    }

    print(headers['Authorization'])

    try:
        response = requests.post(url, headers=headers, json=payload)
        verify_data = response.json()

        if response.status_code == 200 and verify_data.get("status") == "Completed":

            applicant_id=purchase_order_id.split('_')[1]
            applicant = get_object_or_404(JobApplication, id=applicant_id)
            applicant.is_paid = True
            applicant.status='complete'
            applicant.save()
            context = {
                "status": status,
                "transaction_id": transaction_id,
                "purchase_order_id": purchase_order_id,
                "amount": (int(amount)/100),
                "mobile": mobile,
            }
        else:
            messages.error(request, f"Payment verification failed. Please contact support {status}")
            context = {
                "status": status,
            }
    except Exception as e:
        messages.error(request, f"An error occurred: {e}")
        context = {"status": status}

    return render(request, "payment_success.html", context)



def amounts(request,applicant_id):
    applicant = get_object_or_404(JobApplication, id=applicant_id)
    return render(request, "applicants/add_amount.html", {'applicant': applicant})
