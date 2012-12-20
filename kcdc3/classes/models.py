from django.db import models
from django.contrib.auth.models import User
import datetime

# a Session is a collection of classes
class Session(models.Model):
	title = models.CharField(max_length=200)
	long_title = models.CharField(max_length=200)
	slug = models.SlugField(unique=True)
	STATUS_CHOICES = (
		('CURRENT', 'Current'),
		('PAST', 'Past'),
		('HIDDEN', 'Hidden'),
	)
	status = models.CharField(max_length=9, choices=STATUS_CHOICES, default='CURRENT')

	description = models.TextField(blank=True)
	documentation = models.TextField(blank=True)

	REGISTRATION_STATUS_CHOICES = (
		('ALLOW', 'Allow'),
		('PREVENT', 'Prevent'),
	)
	registration_status = models.CharField(max_length=7, choices=REGISTRATION_STATUS_CHOICES, default='PREVENT')
	email_reminder_days = models.IntegerField('Send reminder emails this many days ahead of classes:', default=2)

	def __unicode__(self):
		return self.title

class Location(models.Model):
	name = models.CharField('Description', max_length=100, blank=True)
	neighborhood = models.CharField('Neighborhood', max_length=100, blank=True)
	address1 = models.CharField('Address', max_length=60, blank=True)
	address2 = models.CharField('Line two', max_length=60, blank=True)
	city = models.CharField('City', max_length=60, blank=True, default='Washington')
	state = models.CharField('State', max_length=2, blank=True, default='DC')
	zip = models.CharField('ZIP', max_length=5, blank=True)
	hint = models.CharField('Hint', max_length=300, blank=True)
	show_exact = models.BooleanField('Show details/exact address on public site?', default=True)
	def __unicode__(self):
		return self.name

class Bio(models.Model):
	name = models.CharField('Name', max_length=100, blank=False)
	description = models.TextField('Bio text', blank=True)
	website = models.URLField(blank=True)
	user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name='user')
	def __unicode__(self):
		return self.name

# an Event is a single class or other event
class Event(models.Model):
	
	title = models.CharField(max_length=200)
	slug = models.SlugField(unique=True)
	STATUS_CHOICES = (
		('PUBLISHED', 'Published'),
		('HIDDEN', 'Hidden'),
		('DRAFT', 'Draft'),
		('REMOVED', 'Removed'),
	)
	status = models.CharField(max_length=9, choices=STATUS_CHOICES, default='PUBLISHED')
	featured = models.BooleanField(default=False)
	
	session = models.ForeignKey(Session, blank=False, null=True, on_delete=models.SET_NULL, related_name='session')
	date = models.DateTimeField('First meeting')
	end_time = models.TimeField('End time', blank=True, null=True)
	additional_dates_text = models.TextField('Notes about additional meetings', blank=True)

	location = models.ForeignKey(Location, blank=True, null=True, on_delete=models.SET_NULL, related_name='location')
	
	#TODO: `type' keyword is reserved, and using it is considered naughty.
	TYPE_CHOICES = (
		('CLASS', 'Class'),
		('EVENT', 'Event'),
		('EXTERNAL', 'Non-KCDC Event'),
	)
	type = models.CharField(max_length=9, choices=TYPE_CHOICES, default='CLASS')

	summary = models.TextField(blank=True)
	description = models.TextField(blank=True)
	details = models.TextField('Pre-class details', blank=True)
	thumbnail = models.ImageField(upload_to='event_images', blank=True, null=True)
	main_image = models.ImageField(upload_to='event_images', blank=True, null=True)

	email_welcome_text = models.TextField('Extra text for welcome email', blank=True)
	email_reminder = models.BooleanField('Send reminder email?', default=True)
	email_reminder_text = models.TextField('Extra text for reminder email', blank=True)

	documentation = models.TextField(blank=True)
	
	max_students = models.IntegerField('Max students', blank=True, null=True, default=999)
	waitlist_status = models.BooleanField('Use waitlist', default=True)
	
	REGISTRATION_STATUS_CHOICES = (
		('AUTO', 'Auto'),
		('ALLOW', 'Allow (+)'),
		('PREVENT', 'Prevent (-)'),
		('HIDE', 'Hide forms'),
	)
	registration_status = models.CharField(max_length=7, choices=REGISTRATION_STATUS_CHOICES, default='AUTO')

	teacher_bios = models.ManyToManyField(Bio, blank=True, null=True, related_name='event')
	teacher_text = models.CharField('Teacher (text)', max_length=200, blank=True)
	teachers = models.ManyToManyField(User, blank=True, null=True, related_name='teachers')
	facilitators = models.ManyToManyField(User, blank=True, null=True, related_name='facilitators')
	students = models.ManyToManyField(User, through='Registration', blank=True, null=True, related_name='students')
		
	class Meta:
		ordering = ['-date']

	def __unicode__(self):
		return self.title

	def has_passed(self):
		""" Determines if the class date is before now."""
		return self.date < datetime.datetime.now()

	def get_registrations(self, waitlist=False, cancelled=False):
		""" Returns all the registrations associated with this event."""
		return Registration.objects.filter(
			event__slug=self.slug,
			waitlist=waitlist,
			cancelled=cancelled)

	def registration_count(self):
		""" Determines the total number of registrations for a class.
		This does not include the waitlist."""
		return self.get_registrations().count()

	def waitlist_count(self):
		""" Determines the total number of waitlisted registrations."""
		return self.get_registrations(waitlist=True).count()

	def add_to_waitlist(self):
		""" Checks to see if the class is full and has a waitlist.
		If it is full and has a waitlist it returns true, false 
		otherwise."""
		if self.get_registrations().count() >= self.max_students and self.waitlist_status:
			return True
		else:
			return False

	def num_teachers(self):
		""" Returns the number of bios associated with this event."""
		return self.teacher_bios.count()

	def is_registration_open(self):
		""" Returns whether a user can register for the class or not."""
		if self.date < datetime.datetime.now():
			return False
		elif self.registration_status == 'ALLOW':
			return True
		elif self.registration_status == 'AUTO' and self.session.registration_status == 'ALLOW':
			return True
		else: 
			return False

		
# Registrations connect Users with the Events they've signed up for		
class Registration(models.Model):
	student = models.ForeignKey(User, null=True)
	event = models.ForeignKey(Event, null=True)
	date_registered = models.DateTimeField(auto_now_add=True)
	waitlist = models.BooleanField()
	attended = models.NullBooleanField()
	cancelled = models.BooleanField(default=False)
	date_cancelled = models.DateTimeField(blank=True, null=True)

	class Meta:

		ordering = ['date_registered']

		#TODO this isn't being picked up by the admin
		permissions = (
			("view_students", "Can see enrolled students"),
			("record_attendance", "Can mark student attendance"),
			("edit_students", "Can add or remove students"),
		)
