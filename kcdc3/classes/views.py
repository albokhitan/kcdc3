from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from datetime import datetime
from django.views.generic import DetailView, TemplateView, ListView
from classes.models import Event, Registration, Bio
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.template import Context
from django.contrib.auth.decorators import login_required

# display a list of events
class EventListView(ListView):

	context_object_name = "event_list"
	model = Event
	
	def get_context_data(self, **kwargs):
		
		context = super(EventListView, self).get_context_data(**kwargs)

		return context


	
# display a single event	
class EventDetailView(DetailView):

	context_object_name = "event"
	model = Event
	
	def get_context_data(self, **kwargs):
		
		context = super(EventDetailView, self).get_context_data(**kwargs)

		if self.request.user.is_authenticated():
			context['user_is_authenticated'] = True
			r = UserRegistrationHelper(self.object,self.request.user)
		else:
			r = RegistrationHelper(self.object)
		context['registration_count'] = r.registration_count
		context['waitlist_count'] = r.waitlist_count
		context['user_is_waitlisted'] = r.user_is_waitlisted
		context['user_is_registered'] = r.user_is_registered
		context['is_registration_open'] = r.is_registration_open
		context['add_to_waitlist'] = r.add_to_waitlist

		# TODO: move this
		if self.request.user.is_authenticated():
			if Event.objects.filter(slug=self.object.slug, facilitators=self.request.user).count() > 0 or self.request.user.is_staff:
				context['show_facilitator'] = True
			
		return context
			


# handle registration/waitlist form
def register(request, slug):

	e = Event.objects.get(slug=slug)
	r = UserRegistrationHelper(e,request.user)

	# TODO shouldn't be setting this up by hand
	event = {
		'title': e.title,
		'slug': e.slug,
		'date': e.date,
		'end_time': e.end_time,
		'additional_dates_text': e.additional_dates_text,
		'location_name': e.location.name,
		'location_address1': e.location.address1,
		'location_address2': e.location.address2,
		'location_city': e.location.city,
		'location_state': e.location.state,
		'location_zip': e.location.zip,
		'location_neighborhood': e.location.neighborhood,
		'location_hint': e.location.hint,
		'details': e.details,
		'email_welcome_text': e.email_welcome_text,	
	}
	
	# if there are no non-cancelled registrations for this user/event and registration is possible
	if r.user_is_registered==False and r.user_is_waitlisted==False and r.is_registration_open==True:
		t = Registration(student=request.user, event=e, date_registered=datetime.now(), waitlist=r.add_to_waitlist)
		t.save()
		if r.add_to_waitlist == False:
			message_body = render_to_string('classes/email_registered.txt', event)
			message_subject = render_to_string('classes/email_registered_subject.txt', event)
			send_mail(message_subject, message_body, 'contact@knowledgecommonsdc.org', [request.user.email], fail_silently=False)
			return HttpResponseRedirect("/classes/response/registered")
		else:
			message_body = render_to_string('classes/email_waitlisted.txt', event)
			message_subject = render_to_string('classes/email_waitlisted_subject.txt', event)
			send_mail(message_subject, message_body, 'contact@knowledgecommonsdc.org', [request.user.email], fail_silently=False)
			send_mail(e.title, message_body, 'contact@knowledgecommonsdc.org', [request.user.email], fail_silently=False)
			return HttpResponseRedirect("/classes/response/waitlisted")
	else: 
		return HttpResponseRedirect("/classes/response/error")



# handle cancel form
def cancel(request, slug):
	
	e = Event.objects.get(slug=slug)
	r = UserRegistrationHelper(e,request.user)
	
	# TODO shouldn't be setting this up by hand
	event = {
		'title': e.title,
		'slug': e.slug,
		'date': e.date,
		'end_time': e.end_time,
		'additional_dates_text': e.additional_dates_text,
		'location_name': e.location.name,
		'location_address1': e.location.address1,
		'location_address2': e.location.address2,
		'location_city': e.location.city,
		'location_state': e.location.state,
		'location_zip': e.location.zip,
		'location_neighborhood': e.location.neighborhood,
		'location_hint': e.location.hint,
		'details': e.details,
		'email_welcome_text': e.email_welcome_text,	
	}

	if r.user_is_registered or r.user_is_waitlisted:
		for t in Registration.objects.filter(event=e, student=request.user, cancelled=False)[:1]:
			t.date_cancelled=datetime.now()
			t.cancelled=True
			t.save()
		if r.add_to_waitlist==True and e.waitlist_status==True:
		 	for w in Registration.objects.filter(event=e, waitlist=True, cancelled=False)[:1]:
				w.waitlist=False
				w.save()
				message_body = render_to_string('classes/email_promoted.txt', event)
				message_subject = render_to_string('classes/email_promoted_subject.txt', event)
				recipient = w.student.email
				send_mail(message_subject, message_body, 'contact@knowledgecommonsdc.org', [recipient], fail_silently=False)
		message_body = render_to_string('classes/email_cancelled.txt', event)
		message_subject = render_to_string('classes/email_cancelled_subject.txt', event)
		send_mail(message_subject, message_body, 'contact@knowledgecommonsdc.org', [request.user.email], fail_silently=False)
		return HttpResponseRedirect("/classes/response/cancelled")
	else: 
		return HttpResponseRedirect("/classes/response/error")



# redirect the user to a thank you/results sceen after they take an action
class ResponseTemplateView(TemplateView):

	template_name = "classes/response.html"
	 
	def get_context_data(self, **kwargs):
		if self.kwargs['slug'] == "registered":
			message_text = "You've been registered"
		elif self.kwargs['slug'] == "waitlisted":
			message_text = "You've been added to the waitlist"
		elif self.kwargs['slug'] == "cancelled":
			message_text = "Registration cancelled"
		else:
			message_text = "Error"
		return {'message': message_text}



# teacher/facilitator view
@login_required
def facilitator(request, slug):

	e = Event.objects.get(slug=slug)
	r = RegistrationHelper(e)

	context = Context()

	context['slug'] = slug
	context['title'] = e.title


	context['registration_count'] = r.registration_count
	context['waitlist_count'] = r.waitlist_count

	context['registered_students'] = Registration.objects.filter(event=e, waitlist=False, cancelled=False)
	context['waitlisted_students'] = Registration.objects.filter(event=e, waitlist=True, cancelled=False)

	# is the user staff or assigned as a facilitator for this class?
	if Event.objects.filter(slug=slug, facilitators=request.user).count() > 0 or request.user.is_staff:
		return render_to_response('classes/facilitator_event_detail.html',context)
	else:
		# TODO this should really return a 403
		return HttpResponse()


# provide information about all registrations for an event
# TODO much of this should probably be in the model
class RegistrationHelper:
		
	def __init__(self, event):

		self.e = event

		self.registration_count = Registration.objects.filter(event=self.e, waitlist=False, cancelled=False).count()
		self.waitlist_count = Registration.objects.filter(event=self.e, waitlist=True, cancelled=False).count()

		if self.registration_count >= self.e.max_students:
			self.add_to_waitlist = True
		else:
			self.add_to_waitlist = False	
	
		self.user_is_waitlisted = False
		self.user_is_registered = False
		
		# TODO - account for time offsets and session-wide control in automatically opening registration
 		if self.e.date < datetime.now():
			self.is_registration_open = False
		elif self.e.registration_status == 'ALLOW':
			self.is_registration_open = True
		elif self.e.registration_status == 'AUTO' and self.e.session.registration_status == 'ALLOW':
			self.is_registration_open = True
		else: 
			self.is_registration_open = False
		
		
# provide information about an event's registration status
# relative to a particular event and user
# TODO remove repetitive code in __init__
class UserRegistrationHelper(RegistrationHelper):
		
	def __init__(self, event, student):

		self.e = event
		self.s = student

		self.registration_count = Registration.objects.filter(event=self.e, waitlist=False, cancelled=False).count()
		self.waitlist_count = Registration.objects.filter(event=self.e, waitlist=True, cancelled=False).count()

		if self.registration_count >= self.e.max_students:
			self.add_to_waitlist = True
		else:
			self.add_to_waitlist = False	

		self.user_is_waitlisted = False
		self.user_is_registered = False
		if (Registration.objects.filter(event=self.e, student=self.s, waitlist=False, cancelled=False).count() > 0):
			self.user_is_registered = True
		elif (Registration.objects.filter(event=self.e, student=self.s, waitlist=True, cancelled=False).count() > 0):
			self.user_is_waitlisted = True

		# TODO - account for time offsets and session-wide control in automatically opening registration
 		if self.e.date < datetime.now():
			self.is_registration_open = False
		elif self.e.registration_status == 'ALLOW':
			self.is_registration_open = True
		elif self.e.registration_status == 'AUTO' and self.e.session.registration_status == 'ALLOW':
			self.is_registration_open = True
		else: 
			self.is_registration_open = False

