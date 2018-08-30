# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    #url(r'^get_geo/$', 'user_registration.views.get_geo', name='get_geo'),

    #url(r'^$', 'user_registration.views.user_settings', name='user_settings'),
    #url(r'^$', 'user_registration.views.user_main', name='user_main'),

    url(r'^card/$', 'user_registration.views.user_details', name='user_details'),
    url(r'^card/(?P<id>\d+)/$', 'user_registration.views.user_details', name='user_details'),
    url(r'^edit_person_name/(?P<user_id>\w+)/(?P<name_id>\w+)/$', 'user_registration.views.edit_person_name', name='edit_person_name'),
    url(r'^delete_person_name/(?P<uid>\w+)/(?P<nid>\w+)$', 'user_registration.views.delete_person_name', name='delete_person_name'),

    url(r'^login/$', 'user_registration.views.login', name='login'),
    url(r'^login/email_auth_send/$', 'user_registration.views.email_auth_send', name='email_auth_send'),
    url(r'^login/email/(?P<code>\w+)/$', 'user_registration.views.email_auth', name='email_auth'),
    url(r'^login/openid/$', 'django_openid_consumer.views.begin', name='openid'),
    url(r'^login/openid/auth/$', 'user_registration.views.openid_auth', name='openid_auth'),
    url(r'^login/openid/complete/$', 'django_openid_consumer.views.complete'),
    url(r'^login/openid/signout/$', 'django_openid_consumer.views.signout'),
    url(r'^login/lj_auth_send/$', 'user_registration.views.lj_auth_send', name='lj_auth_send'),

    # запрос авторизации на oauth сервер
    url(r'^login/oauth/$', 'user_registration.views.oauth_func', name='oauth'),
    # получение данных от
    url(r'^login/oauth/mailru/$', 'user_registration.views.mailru_oauth'),
    url(r'^login/oauth/twitter/$', 'user_registration.views.twitter_oauth'),
    url(r'^login/oauth/google/$', 'user_registration.views.google_oauth'),
    url(r'^login/oauth/facebook/$', 'user_registration.views.facebook_oauth'),
    url(r'^login/oauth/vkontakte/$', 'user_registration.views.vkontakte_oauth'),
    url(r'^login/oauth/yandex/$', 'user_registration.views.yandex_oauth'),

    
    #url(r'^adv_notification_sender/$', 'user_registration.views.adv_notification_sender', name='adv_notification_sender'),

    url(r'^logout/$', 'user_registration.views.logout', name='logout'),

    url(r'^profile/accounts_merger/$', 'user_registration.views.accounts_merger', name="accounts_merger"),
    url(r'^profile/accounts/$', 'user_registration.views.profile_accounts', name='profile_accounts'),
    

    url(r'^profile/job/$', 'user_registration.views.profile_job', name='profile_job'),
    url(r'^profile/job/add_action/$', 'user_registration.views.add_job_action', name='add_job_action'),
    
    url(r'^profile/(?P<id>\d+)/accounts/$', 'user_registration.views.profile_accounts', name='profile_accounts'),
    url(r'^profile/(?P<id>\d+)/job/$', 'user_registration.views.profile_job', name='profile_job'),
    
    url(r'^profile/(?P<id>\d+)/xjob/$', 'user_registration.views.profile_xjob', name='profile_xjob'),
    
    
    url(r'^profile/(?P<id>\d+)/recommend/$', 'user_registration.views.profile_recommend', name='profile_recommend'),
    url(r'^profile/(?P<id>\d+)/(?P<vid>\d+)/subscribers/$', 'user_registration.views.profile_subscribers', name='profile_subscribers'),
    url(r'^profile/(?P<id>\d+)/(?P<vid>\d+)/subscribers/log/$', 'user_registration.views.profile_subscribers_log', name='profile_subscribers_log'),

    
    url(r'^profile/view/(?P<vid>\d+)/post/(?P<id>\d+)/delete/$', 'letsgetrhythm.views.view_post_del', {'type': 'user'}, name='profile_view_post_del'),
    url(r'^profile/(?P<user_id>\d+)/view/(?P<vid>\d+)/$', 'user_registration.views.view_post', name='profile_view'),
    url(r'^profile/(?P<user_id>\d+)/view/(?P<vid>\d+)/post/(?P<id>\d+)/$', 'user_registration.views.view_post',  name='profile_view_post'),

    url(r'^profile/(?P<user_id>\d+)/gallery/(?P<vid>\d+)/$', 'user_registration.views.user_gallery', name='profile_gallery'),
    
    url(r'^profile/$', 'user_registration.views.profile', name='profile'),
    url(r'^profile/(?P<id>\d+)/$', 'user_registration.views.profile', name='profile'),

    #url(r'^profile/(?P<id>\d+)/background/$', 'user_registration.views.profile_background', name='profile_background'),
    #url(r'^profile/(?P<id>\d+)/adv_my_page/$', 'user_registration.views.profile_adv_mypage', name='profile_adv_mypage'),
    #url(r'^profile/(?P<id>\d+)/adv_site/$', 'user_registration.views.profile_adv_site', name='profile_adv_site'),
    url(r'^profile/(?P<id>\d+)/adv/$', 'user_registration.views.profile_adv', name='profile_adv'),
    url(r'^profile/(?P<id>\d+)/adv/(?P<adv>\d+)/$', 'user_registration.views.profile_adv_details', name='profile_adv_details'),

    url(r'^profile/(?P<id>\d+)/adv/(?P<adv>\d+)/report/budget/$', 'user_registration.views.profile_adv_report_budget', name='profile_adv_report_budget'),
    url(r'^profile/(?P<id>\d+)/adv/(?P<adv>\d+)/report/users/$', 'user_registration.views.profile_adv_report_users', name='profile_adv_report_users'),

    url(r'^profile/(?P<id>\d+)/booking/settings/$', 'user_registration.views.profile_booking_settings', name='profile_booking_settings'),

    url(r'^profile/adv_order_sender/$', 'user_registration.views.adv_order_sender', name='adv_order_sender'),


    url(r'^profile/change_page_type/(?P<user_id>\d+)/(?P<vid>\d+)/$', 'user_registration.views.user_change_page_type', name='user_change_page_type'),

    url(r'^user_permission_set/(?P<id>\d+)/$', 'user_registration.views.user_permission_set', name='user_permission_set'),
    
    url(r'^withdraw_user_money/(?P<id>\d+)/$', 'user_registration.views.withdraw_user_money', name='withdraw_user_money'),

    url(r'^subscriber_blog_sender/$', 'user_registration.views.subscriber_blog_sender', name='subscriber_blog_sender'),
    url(r'^subscriber_comments_sender/$', 'user_registration.views.subscriber_comments_sender', name='subscriber_comments_sender'),
    url(r'^subscriber_comments_author_blog_sender/$', 'user_registration.views.subscriber_comments_author_blog_sender', name='subscriber_comments_author_blog_sender'),
    url(r'^unsubscribe/(?P<code>\w+)/$', 'user_registration.views.unsubscribe', name='user_unsubscribe'),


    #url(r'^import_kinoafisha_users/$', 'user_registration.views.import_kinoafisha_users', name='import_kinoafisha_users'),
    #url(r'^clear_empty_users/$', 'user_registration.views.clear_empty_users', name='clear_empty_users'),
    #url(r'^replace_users_avatars/$', 'user_registration.views.replace_users_avatars', name='replace_users_avatars'),
    #url(r'^clear_empty_sessions/$', 'user_registration.views.clear_empty_sessions', name='clear_empty_sessions'),

    # test
    #url(r'^test_test/$', 'user_registration.ajax.test_test'),
    #url(r'^test_delete/$', 'user_registration.views.test_delete'),
    #url(r'^get_user_list/$', 'user_registration.views.get_user_list', name='get_user_list'),
    #url(r'^mailru_complete2/$', 'user_registration.views.mailru_complete2', name='mailru_complete2'),
    #url(r'^test_ava/$', 'user_registration.views.test_ava', name='test_ava'),


    #url(r'^messenger/$', 'user_registration.messenger.messenger', name='messenger'),
    

)
