from django.conf.urls import patterns, include, url
from models import Event, Registration
from views import EventListView, EventDetailView, ResponseTemplateView, EventArchiveView, SessionView, RegistrationListView, SessionAdminListView, TeacherAdminListView, FilteredTeacherAdminListView, UserEventListView, JSONVizSessionAttendanceDataListView, tsv_events_by_location_data, csv_users_data, SocialListView
urlpatterns = patterns('kcdc3.apps.classes.views',

	url(r'^$', EventListView.as_view()),

	# staff dashboard
	url(r'^staff/$', SessionAdminListView.as_view()),
	url(r'^staff/teachers/$', TeacherAdminListView.as_view()),
	url(r'^staff/teachers/session/(?P<slug>[A-Za-z0-9_-]+)/$', FilteredTeacherAdminListView.as_view()),
	url(r'^staff/registrations/session/(?P<slug>[A-Za-z0-9_-]+)/$', RegistrationListView.as_view()),
	url(r'^staff/social/session/(?P<slug>[A-Za-z0-9_-]+)/$', SocialListView.as_view()),

	# data
	url(r'^data/attendance/session/(?P<slug>[A-Za-z0-9_-]+)/json/$', JSONVizSessionAttendanceDataListView.as_view()),
	url(r'^data/attendance/session/(?P<slug>[A-Za-z0-9_-]+)/csv/$', 'csv_session_attendance_data'),
	url(r'^data/registration/session/(?P<slug>[A-Za-z0-9_-]+)/csv/$', 'csv_session_registration_data'),
	url(r'^data/location/txt/$', 'txt_location_data'),
	url(r'^data/location/json/$', 'json_location_data'),
	url(r'^data/event_location/json/$', 'json_event_location_data'),
	url(r'^data/events_by_location/tsv/$', 'tsv_events_by_location_data'),
	url(r'^data/users/csv/$', 'csv_users_data'),

	url(r'^classes$', UserEventListView.as_view()),

	url(r'^(?P<slug>[0-9_-]+)/$', EventArchiveView.as_view()),
	url(r'^(?P<slug>[0-9_-]+)/background/$', SessionView.as_view()),

	url(r'^response/(?P<slug>[A-Za-z0-9_-]+)$', ResponseTemplateView.as_view()),

	url(r'^(?P<slug>[A-Za-z0-9_-]+)/$', EventDetailView.as_view(model=Event,)),
	url(r'^(?P<slug>[A-Za-z0-9_-]+)/register$', 'register'),
	url(r'^(?P<slug>[A-Za-z0-9_-]+)/cancel$', 'cancel'),
	url(r'^(?P<slug>[A-Za-z0-9_-]+)/facilitator$', 'facilitator'),

)
