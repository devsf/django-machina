# -*- coding: utf-8 -*-

# Standard library imports
# Third party imports
from django.db.models import get_model
from django.template import Context
from django.template import TemplateSyntaxError
from django.template.base import Template
from django.test import TestCase
from django.test.client import RequestFactory

# Local application / specific library imports
from machina.apps.forum_permission.middleware import ForumPermissionHandlerMiddleware
from machina.core.loading import get_class
from machina.test.factories import create_category_forum
from machina.test.factories import create_forum
from machina.test.factories import create_topic
from machina.test.factories import GroupFactory
from machina.test.factories import PostFactory
from machina.test.factories import TopicPollFactory
from machina.test.factories import UserFactory

Forum = get_model('forum', 'Forum')

PermissionHandler = get_class('forum_permission.handler', 'PermissionHandler')
assign_perm = get_class('forum_permission.shortcuts', 'assign_perm')


class TestGetPermissionTag(TestCase):
    def setUp(self):
        self.loadstatement = '{% load url from future %}{% load forum_permission_tags %}'
        self.request_factory = RequestFactory()

        self.g1 = GroupFactory.create()
        self.u1 = UserFactory.create()
        self.u2 = UserFactory.create()
        self.u1.groups.add(self.g1)
        self.u2.groups.add(self.g1)
        self.moderators = GroupFactory.create()
        self.moderator = UserFactory.create()
        self.moderator.groups.add(self.moderators)
        self.superuser = UserFactory.create(is_superuser=True)

        # Permission handler
        self.perm_handler = PermissionHandler()

        # Set up a top-level category
        self.top_level_cat = create_category_forum()

        # Set up some forums
        self.forum_1 = create_forum(parent=self.top_level_cat)
        self.forum_2 = create_forum(parent=self.top_level_cat)

        # Set up some topics and posts
        self.forum_1_topic = create_topic(forum=self.forum_1, poster=self.u1)
        self.forum_2_topic = create_topic(forum=self.forum_2, poster=self.u2)
        self.post_1 = PostFactory.create(topic=self.forum_1_topic, poster=self.u1)
        self.post_2 = PostFactory.create(topic=self.forum_2_topic, poster=self.u2)

    def test_can_tell_if_a_user_can_access_the_moderation_panel(self):
        # Setup
        def get_rendered(user):
            request = self.request_factory.get('/')
            request.user = user
            ForumPermissionHandlerMiddleware().process_request(request)
            t = Template(self.loadstatement + '{% get_permission \'can_access_moderation_panel\' request.user as user_can_access_moderation_panel %}'
                '{% if user_can_access_moderation_panel %}CAN_ACCESS{% else %}CANNOT_ACCESS{% endif %}')
            c = Context({'request': request})
            rendered = t.render(c)

            return rendered

        assign_perm('can_approve_posts', self.moderators, self.top_level_cat)

        # Run & check
        self.assertEqual(get_rendered(self.superuser), 'CAN_ACCESS')
        self.assertEqual(get_rendered(self.moderator), 'CAN_ACCESS')
        self.assertEqual(get_rendered(self.u1), 'CANNOT_ACCESS')

    def test_can_tell_if_a_user_can_download_files_attached_to_a_specific_post(self):
        # Setup
        def get_rendered(post, user):
            request = self.request_factory.get('/')
            request.user = user
            ForumPermissionHandlerMiddleware().process_request(request)
            t = Template(self.loadstatement + '{% get_permission \'can_download_files\' request.user post=post as user_can_download_files %}'
                '{% if user_can_download_files %}CAN_DOWNLOAD{% else %}CANNOT_DOWNLOAD{% endif %}')
            c = Context({'post': post, 'request': request})
            rendered = t.render(c)

            return rendered

        assign_perm('can_see_forum', self.g1, self.forum_1)
        assign_perm('can_read_forum', self.g1, self.forum_1)
        assign_perm('can_edit_own_posts', self.g1, self.forum_1)
        assign_perm('can_delete_own_posts', self.g1, self.forum_1)
        assign_perm('can_reply_to_topics', self.g1, self.forum_1)
        assign_perm('can_see_forum', self.moderators, self.forum_1)
        assign_perm('can_read_forum', self.moderators, self.forum_1)
        assign_perm('can_edit_own_posts', self.moderators, self.forum_1)
        assign_perm('can_delete_own_posts', self.moderators, self.forum_1)
        assign_perm('can_edit_posts', self.moderators, self.forum_1)
        assign_perm('can_delete_posts', self.moderators, self.forum_1)
        assign_perm('can_download_file', self.g1, self.forum_1)

        # Run & check
        self.assertEqual(get_rendered(self.post_1, self.u1), 'CAN_DOWNLOAD')
        self.assertEqual(get_rendered(self.post_2, self.u1), 'CANNOT_DOWNLOAD')
        self.assertEqual(get_rendered(self.post_1, self.superuser), 'CAN_DOWNLOAD')
        self.assertEqual(get_rendered(self.post_2, self.superuser), 'CAN_DOWNLOAD')

    def test_can_tell_if_the_user_can_edit_a_post(self):
        # Setup
        def get_rendered(post, user):
            request = self.request_factory.get('/')
            request.user = user
            ForumPermissionHandlerMiddleware().process_request(request)
            t = Template(self.loadstatement + '{% get_permission \'can_edit_post\' request.user post=post as user_can_edit_post %}'
                '{% if user_can_edit_post %}CAN_EDIT{% else %}CANNOT_EDIT{% endif %}')
            c = Context({'post': post, 'request': request})
            rendered = t.render(c)

            return rendered

        assign_perm('can_see_forum', self.u1, self.forum_1)
        assign_perm('can_read_forum', self.u1, self.forum_1)
        assign_perm('can_edit_own_posts', self.u1, self.forum_1)
        assign_perm('can_delete_own_posts', self.u1, self.forum_1)
        assign_perm('can_reply_to_topics', self.u1, self.forum_1)
        assign_perm('can_see_forum', self.moderators, self.forum_1)
        assign_perm('can_read_forum', self.moderators, self.forum_1)
        assign_perm('can_edit_own_posts', self.moderators, self.forum_1)
        assign_perm('can_delete_own_posts', self.moderators, self.forum_1)
        assign_perm('can_edit_posts', self.moderators, self.forum_1)
        assign_perm('can_delete_posts', self.moderators, self.forum_1)

        # Run & check
        self.assertEqual(get_rendered(self.post_1, self.u1), 'CAN_EDIT')
        self.assertEqual(get_rendered(self.post_1, self.u2), 'CANNOT_EDIT')
        self.assertEqual(get_rendered(self.post_1, self.moderator), 'CAN_EDIT')
        self.assertEqual(get_rendered(self.post_1, self.superuser), 'CAN_EDIT')

    def test_can_tell_if_the_user_can_edit_a_post(self):
        # Setup
        def get_rendered(post, user):
            request = self.request_factory.get('/')
            request.user = user
            ForumPermissionHandlerMiddleware().process_request(request)
            t = Template(self.loadstatement + '{% get_permission \'can_delete_post\' request.user post=post as user_can_delete_post %}'
                '{% if user_can_delete_post %}CAN_DELETE{% else %}CANNOT_DELETE{% endif %}')
            c = Context({'post': post, 'request': request})
            rendered = t.render(c)

            return rendered

        assign_perm('can_see_forum', self.u1, self.forum_1)
        assign_perm('can_read_forum', self.u1, self.forum_1)
        assign_perm('can_edit_own_posts', self.u1, self.forum_1)
        assign_perm('can_delete_own_posts', self.u1, self.forum_1)
        assign_perm('can_reply_to_topics', self.u1, self.forum_1)
        assign_perm('can_see_forum', self.moderators, self.forum_1)
        assign_perm('can_read_forum', self.moderators, self.forum_1)
        assign_perm('can_edit_own_posts', self.moderators, self.forum_1)
        assign_perm('can_delete_own_posts', self.moderators, self.forum_1)
        assign_perm('can_edit_posts', self.moderators, self.forum_1)
        assign_perm('can_delete_posts', self.moderators, self.forum_1)

        # Run & check
        self.assertEqual(get_rendered(self.post_1, self.u1), 'CAN_DELETE')
        self.assertEqual(get_rendered(self.post_1, self.u2), 'CANNOT_DELETE')
        self.assertEqual(get_rendered(self.post_1, self.moderator), 'CAN_DELETE')
        self.assertEqual(get_rendered(self.post_1, self.superuser), 'CAN_DELETE')

    def test_can_tell_if_the_user_can_reply_to_topics(self):
        # Setup
        def get_rendered(topic, user):
            request = self.request_factory.get('/')
            request.user = user
            ForumPermissionHandlerMiddleware().process_request(request)
            t = Template(self.loadstatement + '{% get_permission \'can_add_post\' request.user topic=topic as user_can_add_post %}'
                '{% if user_can_add_post %}CAN_ADD_POST{% else %}CANNOT_ADD_POST{% endif %}')
            c = Context({'topic': topic, 'request': request})
            rendered = t.render(c)

            return rendered

        assign_perm('can_see_forum', self.u1, self.forum_1)
        assign_perm('can_read_forum', self.u1, self.forum_1)
        assign_perm('can_edit_own_posts', self.u1, self.forum_1)
        assign_perm('can_delete_own_posts', self.u1, self.forum_1)
        assign_perm('can_reply_to_topics', self.u1, self.forum_1)
        assign_perm('can_see_forum', self.moderators, self.forum_1)
        assign_perm('can_read_forum', self.moderators, self.forum_1)
        assign_perm('can_edit_own_posts', self.moderators, self.forum_1)
        assign_perm('can_delete_own_posts', self.moderators, self.forum_1)
        assign_perm('can_edit_posts', self.moderators, self.forum_1)
        assign_perm('can_delete_posts', self.moderators, self.forum_1)

        # Run & check
        self.assertEqual(get_rendered(self.forum_1_topic, self.u1), 'CAN_ADD_POST')
        self.assertEqual(get_rendered(self.forum_2_topic, self.u1), 'CANNOT_ADD_POST')
        self.assertEqual(get_rendered(self.forum_1_topic, self.superuser), 'CAN_ADD_POST')
        self.assertEqual(get_rendered(self.forum_2_topic, self.superuser), 'CAN_ADD_POST')

    def test_can_tell_if_a_user_can_vote_in_a_poll(self):
        # Setup
        def get_rendered(poll, user):
            request = self.request_factory.get('/')
            request.user = user
            ForumPermissionHandlerMiddleware().process_request(request)
            t = Template(self.loadstatement + '{% get_permission \'can_vote_in_poll\' request.user poll=poll as user_can_vote_in_poll %}'
                '{% if user_can_vote_in_poll %}CAN_VOTE{% else %}CANNOT_VOTE{% endif %}')
            c = Context({'poll': poll, 'request': request})
            rendered = t.render(c)

            return rendered

        self.poll_1 = TopicPollFactory.create(topic=self.forum_1_topic)
        self.poll_2 = TopicPollFactory.create(topic=self.forum_2_topic)

        assign_perm('can_see_forum', self.g1, self.forum_1)
        assign_perm('can_read_forum', self.g1, self.forum_1)
        assign_perm('can_edit_own_posts', self.g1, self.forum_1)
        assign_perm('can_delete_own_posts', self.g1, self.forum_1)
        assign_perm('can_reply_to_topics', self.g1, self.forum_1)
        assign_perm('can_see_forum', self.moderators, self.forum_1)
        assign_perm('can_read_forum', self.moderators, self.forum_1)
        assign_perm('can_edit_own_posts', self.moderators, self.forum_1)
        assign_perm('can_delete_own_posts', self.moderators, self.forum_1)
        assign_perm('can_edit_posts', self.moderators, self.forum_1)
        assign_perm('can_delete_posts', self.moderators, self.forum_1)
        assign_perm('can_vote_in_polls', self.g1, self.forum_1)

        # Run & check
        self.assertEqual(get_rendered(self.poll_1, self.u1), 'CAN_VOTE')
        self.assertEqual(get_rendered(self.poll_2, self.u1), 'CANNOT_VOTE')
        self.assertEqual(get_rendered(self.poll_1, self.superuser), 'CAN_VOTE')
        self.assertEqual(get_rendered(self.poll_2, self.superuser), 'CAN_VOTE')

    def test_can_tell_if_a_user_can_create_topics(self):
        # Setup
        def get_rendered(forum, user):
            request = self.request_factory.get('/')
            request.user = user
            ForumPermissionHandlerMiddleware().process_request(request)
            t = Template(self.loadstatement + '{% get_permission \'can_add_topic\' request.user forum=forum as user_can_add_topic %}'
                '{% if user_can_add_topic %}CAN_START_TOPICS{% else %}CANNOT_START_TOPICS{% endif %}')
            c = Context({'forum': forum, 'request': request})
            rendered = t.render(c)

            return rendered

        assign_perm('can_start_new_topics', self.u1, self.forum_1)

        # Run & check
        self.assertEqual(get_rendered(self.forum_1, self.u1), 'CAN_START_TOPICS')
        self.assertEqual(get_rendered(self.forum_2, self.u2), 'CANNOT_START_TOPICS')


    def test_raises_if_the_required_arguments_are_not_passed(self):
        # Setup
        request = self.request_factory.get('/')
        request.user = self.u1
        ForumPermissionHandlerMiddleware().process_request(request)
        context = Context({'request': request})

        templates = [
            '{% get_permission \'can_download_files\' request.user as user_can_download_files %}'
                '{% if user_can_download_files %}CAN_DOWNLOAD{% else %}CANNOT_DOWNLOAD{% endif %}',

            '{% get_permission \'can_edit_post\' request.user as user_can_edit_post %}'
                '{% if user_can_edit_post %}CAN_EDIT{% else %}CANNOT_EDIT{% endif %}',

            '{% get_permission \'can_edit_post\' request.user as user_can_edit_post %}'
                '{% if user_can_edit_post %}CAN_EDIT{% else %}CANNOT_EDIT{% endif %}',

            '{% get_permission \'can_add_post\' request.user as user_can_add_post %}'
                '{% if user_can_add_post %}CAN_ADD_POST{% else %}CANNOT_ADD_POST{% endif %}',

            '{% get_permission \'can_vote_in_poll\' request.user as user_can_vote_in_poll %}'
                '{% if user_can_vote_in_poll %}CAN_VOTE{% else %}CANNOT_VOTE{% endif %}',
        ]

        # Run & check
        for raw_template in templates:
            t = Template(self.loadstatement + raw_template)
            with self.assertRaises(TemplateSyntaxError):
                t.render(context)
