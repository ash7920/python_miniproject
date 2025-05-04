# views.py
from django.db.models import Q

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import SignupForm, ProfileForm, NoteForm, TaskForm, MeetingForm
from .models import Profile, Connection, Note, Task, Meeting

def splash(request):
    return render(request, 'splash.html')

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            # Create the user first
            user = form.save()
            # Now save the additional profile information (first name, last name)
            profile_form = ProfileForm(request.POST)
            if profile_form.is_valid():
                profile_form.save(commit=False).user = user
                profile_form.save()
            login(request, user)
            return redirect('profile')  # Redirect to the profile page
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            return redirect('dashboard')
    else:
        form = ProfileForm()
    return render(request, 'profile.html', {'form': form})

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

@login_required
def connections(request):
    user_profile = request.user.profile

    all_profiles = Profile.objects.exclude(user=user_profile.user)

    pending_requests = Connection.objects.filter(to_user=user_profile.user, is_accepted=False)
    sent_requests = Connection.objects.filter(from_user=user_profile.user, is_accepted=False)

    user_connections = Connection.objects.filter(
        Q(from_user=user_profile.user) | Q(to_user=user_profile.user),
        is_accepted=True
    )

    connected_user_ids = set(
        list(user_connections.values_list('from_user', flat=True)) +
        list(user_connections.values_list('to_user', flat=True))
    )
    connected_user_ids.discard(user_profile.user.id)  # Remove self

    connected_profiles = Profile.objects.filter(user__id__in=connected_user_ids)

    # Get meetings for each connection
    for conn in user_connections:
        conn.meeting = Meeting.objects.filter(connection=conn).first()

    profiles_with_status = []
    for profile in all_profiles:
        status = 'No Request Sent'

        if Connection.objects.filter(from_user=request.user, to_user=profile.user, is_accepted=False).exists():
            status = 'Request Sent'
        elif Connection.objects.filter(from_user=profile.user, to_user=request.user, is_accepted=False).exists():
            status = 'Request Received'
        elif profile.user.id in connected_user_ids:
            continue  # Already connected; skip from "All Students"

        profiles_with_status.append((profile, status))

    return render(request, 'connections.html', {
        'user_profile': user_profile,
        'profiles_with_status': profiles_with_status,
        'pending_requests': pending_requests,
        'connected_profiles': connected_profiles,
        'all_connections': user_connections,
    })








@login_required
def send_request(request, user_id):
    user_to_connect = get_object_or_404(User, id=user_id)
    
    # Check if a request has already been sent or accepted
    existing_connection = Connection.objects.filter(from_user=request.user, to_user=user_to_connect, is_accepted=False)
    if existing_connection.exists():
        messages.error(request, "You have already sent a connection request to this user.")
        return redirect('connections')
    
    # Create a new connection request
    connection = Connection(from_user=request.user, to_user=user_to_connect, is_accepted=False)
    connection.save()

    messages.success(request, f"Connection request sent to {user_to_connect.username}")
    return redirect('connections')



@login_required
def accept_request(request, conn_id):
    connection = get_object_or_404(Connection, id=conn_id)

    # Check if the connection request is addressed to the current user
    if connection.to_user != request.user:
        messages.error(request, "You do not have permission to accept this request.")
        return redirect('connections')

    # Mark the request as accepted
    connection.is_accepted = True
    connection.save()

    # Create the reciprocal connection (i.e., from_user <-> to_user)
    Connection.objects.create(
        from_user=connection.to_user,
        to_user=connection.from_user,
        is_accepted=True
    )

    messages.success(request, f"You have accepted the connection request from {connection.from_user.username}.")
    return redirect('connections')


@login_required
def reject_request(request, conn_id):
    connection = get_object_or_404(Connection, id=conn_id)

    # Check if the connection request is addressed to the current user
    if connection.to_user != request.user:
        messages.error(request, "You do not have permission to reject this request.")
        return redirect('connections')

    # Reject the request by setting `is_accepted` to False
    connection.is_accepted = False
    connection.save()

    messages.success(request, f"You have rejected the connection request from {connection.from_user.username}.")
    return redirect('connections')


@login_required
def send_connection(request, profile_id):
    # Get the profile being connected to
    profile = get_object_or_404(Profile, id=profile_id)

    # Check if a connection already exists or if the request has been sent
    if Connection.objects.filter(from_user=request.user, to_user=profile.user).exists():
        messages.error(request, "You have already sent a connection request to this user.")
        return redirect('connections')

    # Create a new connection request
    connection = Connection(from_user=request.user, to_user=profile.user, is_accepted=False)
    connection.save()

    # Redirect back to the connections page with a success message
    messages.success(request, f"Connection request sent to {profile.user.username}")
    return redirect('connections')


@login_required
@login_required
def schedule_meeting(request, conn_id):
    connection = get_object_or_404(Connection, id=conn_id)

    # Ensure the user is part of the connection
    if connection.to_user != request.user and connection.from_user != request.user:
        messages.error(request, "You do not have permission to schedule a meeting for this connection.")
        return redirect('connections')

    # Get the subject from the connected user's profile
    if connection.from_user == request.user:
        subject = connection.to_user.profile.subject  # Get the subject of the other user
    else:
        subject = connection.from_user.profile.subject  # Get the subject of the other user

    # Check if the user already has 2 meetings scheduled
    existing_meetings = Meeting.objects.filter(
        Q(connection__from_user=request.user) | Q(connection__to_user=request.user)
    )
    if existing_meetings.count() >= 2:
        messages.error(request, "You can only schedule 2 meetings at a time.")
        return redirect('connections')

    # Handle form submission
    if request.method == 'POST':
        form = MeetingForm(request.POST)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.connection = connection
            meeting.save()

            # Mark the connection as having a scheduled meeting
            connection.meet_scheduled = True
            connection.save()

            messages.success(request, "Meeting scheduled successfully!")
            return redirect('connections')
    else:
        form = MeetingForm()

    return render(request, 'schedule_meeting.html', {
        'form': form,
        'connection': connection,
        'subject': subject  # Pass the subject here
    })






@login_required
def upload_note(request):
    if request.method == 'POST':
        form = NoteForm(request.POST, request.FILES)
        if form.is_valid():
            note = form.save(commit=False)
            note.uploaded_by = request.user
            note.save()
            messages.success(request, "Note uploaded successfully.")
            return redirect('view_notes')
    else:
        form = NoteForm()
    return render(request, 'upload_note.html', {'form': form})

@login_required
def view_notes(request):
    notes = Note.objects.all().order_by('-uploaded_at')  # To show everyone's notes
    return render(request, 'view_notes.html', {'notes': notes})

@login_required
@login_required
def tasks(request):
    tasks = Task.objects.filter(user=request.user)  # Fetch tasks for the logged-in user
    
    if request.method == 'POST':
        # Handle simple form submission with just a title field
        task_title = request.POST.get('title')
        if task_title:
            # Create new task with the provided title
            Task.objects.create(
                user=request.user,
                title=task_title,
                is_done=False
            )
            messages.success(request, "Task added successfully.")
            return redirect('tasks')
        else:
            messages.error(request, "Task title cannot be empty.")

    return render(request, 'tasks.html', {'tasks': tasks})


@login_required
def toggle_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if task.user != request.user:
        messages.error(request, "You do not have permission to update this task.")
        return redirect('tasks')
    
    task.is_done = not task.is_done
    task.save()
    messages.success(request, "Task status updated.")
    return redirect('tasks')

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if task.user != request.user:
        messages.error(request, "You do not have permission to delete this task.")
        return redirect('tasks')
    task.delete()
    messages.success(request, "Task deleted successfully.")
    return redirect('tasks')

from django.shortcuts import redirect, get_object_or_404
from .models import Profile, Connection



@login_required
def schedule_meeting(request, conn_id):
    connection = get_object_or_404(Connection, id=conn_id)
    if connection.to_user != request.user and connection.from_user != request.user:
        messages.error(request, "You do not have permission to schedule a meeting for this connection.")
        return redirect('connections')

    if connection.meet_scheduled:
        messages.error(request, "A meeting has already been scheduled for this connection.")
        return redirect('connections')

    if request.method == 'POST':
        form = MeetingForm(request.POST)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.connection = connection
            meeting.save()

            connection.meet_scheduled = True
            connection.save()

            messages.success(request, "Meeting scheduled successfully!")
            return redirect('connections')
    else:
        form = MeetingForm()

    return render(request, 'schedule_meeting.html', {'form': form})

from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Profile, Connection
from django.contrib import messages

@login_required
def get_unique_connections(request):
    user_profile = request.user.profile

    # Fetch all accepted connections (both directions)
    user_connections = Connection.objects.filter(
        Q(from_user=user_profile.user) | Q(to_user=user_profile.user),
        is_accepted=True
    )

    # Get a unique set of user connections using 'from_user' and 'to_user' fields
    connected_user_ids = set(
        list(user_connections.values_list('from_user', flat=True)) +
        list(user_connections.values_list('to_user', flat=True))
    ) - {user_profile.user.id}  # Exclude the current user's ID

    # Get the unique profiles for the connected users
    connected_profiles = Profile.objects.filter(user__id__in=connected_user_ids)

    return render(request, 'connections.html', {
        'user_profile': user_profile,
        'connected_profiles': connected_profiles,
    })

@login_required
def complete_meeting(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)

    # Ensure that the user is part of the meeting connection
    if meeting.connection.from_user != request.user and meeting.connection.to_user != request.user:
        messages.error(request, "You do not have permission to complete this meeting.")
        return redirect('connections')

    # Delete the meeting and reset the 'meet_scheduled' status
    connection = meeting.connection
    meeting.delete()
    
    connection.meet_scheduled = False
    connection.save()

    messages.success(request, "Meeting marked as completed and deleted.")
    return redirect('connections')

@login_required
def notes_dashboard(request):
    if request.method == 'POST':
        form = NoteForm(request.POST, request.FILES)
        if form.is_valid():
            note = form.save(commit=False)
            note.uploaded_by = request.user
            note.save()
            messages.success(request, "Note uploaded successfully.")
            return redirect('notes_dashboard')
    else:
        form = NoteForm()

    # Show own + connected users' notes
    connections = Connection.objects.filter(
        Q(from_user=request.user) | Q(to_user=request.user),
        is_accepted=True
    )
    connected_user_ids = set()
    for conn in connections:
        if conn.from_user != request.user:
            connected_user_ids.add(conn.from_user.id)
        if conn.to_user != request.user:
            connected_user_ids.add(conn.to_user.id)

    notes = Note.objects.filter(
        Q(uploaded_by=request.user) | Q(uploaded_by__id__in=connected_user_ids)
    )

    return render(request, 'notes_dashboard.html', {'form': form, 'notes': notes})

@login_required
def delete_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)

    if note.uploaded_by != request.user:
        return HttpResponseForbidden("You do not have permission to delete this note.")

    note.delete()
    messages.success(request, "Note deleted successfully.")
    return redirect('notes_dashboard')