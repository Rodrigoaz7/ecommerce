from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^$', views.index, name='index'),
	url(r'^alterar-dados/$', views.update_user, name='update_user'),
	url(r'^alterar-senha/$', views.update_password, name='update_password'),
	url(r'^atualizar/$', views.register, name='register'),
	#url(r'^meus-pedidos/$', include('checkout.urls', namespace='checkout'))

]