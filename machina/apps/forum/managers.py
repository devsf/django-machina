# -*- coding: utf-8 -*-

# Standard library imports
# Third party imports
from django.db.models import Q
from mptt.managers import TreeManager

# Local application / specific library imports


class ForumManager(TreeManager):
    def displayable_subforums(self, start_from=None):
        """
        Returns all the forums that can be seen from a forum at agiven level in the tree
        of forums. A forum can be seen if one of the following statements is true:

            The forum is a direct child of the starting forum for the considered level.

            The forum have a parent which is a category and this category is a direct
            child of the starting forum.

            The forum have its 'display_sub_forum_list' option set to True and have a
            parent which is another forum. The latter is a direct child of the starting
            forum.

            The forum have its 'display_sub_forum_list' option set to True and have a
            parent which is another forum. The latter have a parent which is a category and
            this category is a direct child of the starting forum.

        If not starting forum is provided, the returned forums are those that can be seen from
        the root of the forums tree.
        """
        parent_field = 'isnull' if start_from is None else 'pk'
        parent_value = True if start_from is None else start_from.pk
        parent_selector = lambda x: '__'.join(['parent' for _ in range(0, x)] + [parent_field, ])

        return super(ForumManager, self).get_query_set().filter(
            # Forums that have a top-level category has parent
            Q(parent__type=self.model.TYPE_CHOICES.forum_cat, **{parent_selector(2): parent_value}) |
            # Sub forums that can be displayed
            Q(display_sub_forum_list=True, **{parent_selector(2): parent_value}) |
            # Children of forums that have a category as parent
            Q(parent__parent__type=self.model.TYPE_CHOICES.forum_cat,
                parent__type=self.model.TYPE_CHOICES.forum_post,
                display_sub_forum_list=True,
                **{parent_selector(3): parent_value}) |
            # Category, top-level forums and links
            Q(**{parent_selector(1): parent_value}))