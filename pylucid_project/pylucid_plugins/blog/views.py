# coding: utf-8

"""
    PyLucid blog plugin
    ~~~~~~~~~~~~~~~~~~~

    A simple blog system.

    http://feedvalidator.org/
    
    TODO:
        * Detail view, use BlogEntry.get_absolute_url()

    :copyleft: 2008-2012 by the PyLucid team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details
"""

import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.syndication.views import Feed
from django.core import urlresolvers
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect, \
    Http404
from django.utils.feedgenerator import Rss201rev2Feed, Atom1Feed
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect
from django.views.generic.date_based import archive_year, archive_month, \
    archive_day

from pylucid_project.apps.pylucid.decorators import render_to
from pylucid_project.apps.pylucid.system import i18n
from pylucid_project.middlewares.pylucid_objects import SuspiciousOperation404
from pylucid_project.utils.safe_obtain import safe_pref_get_integer

from blog.preference_forms import get_preferences
from blog.models import BlogEntry, BlogEntryContent
from blog.preference_forms import BlogPrefForm

# from django-tagging
from tagging.models import Tag, TaggedItem
from django.core.urlresolvers import reverse


def _add_breadcrumb(request, *args, **kwargs):
    """ shortcut for add breadcrumb link """
    try:
        breadcrumb_context_middlewares = request.PYLUCID.context_middlewares["breadcrumb"]
    except KeyError:
        # No breadcrumbs plugin installed?
        return
    breadcrumb_context_middlewares.add_link(*args, **kwargs)


def _get_max_tag_count():
    preferences = get_preferences()
    max_count = preferences.get("max_tag_count", 5)
    return max_count


def _split_tags(raw_tags):
    "simple split tags from url"
    tag_list = raw_tags.strip("/").split("/")

    max_count = _get_max_tag_count()
    tag_count = len(tag_list) - 1
    if tag_count == max_count:
        raise Http404(_("Too much tags given"))
    elif tag_count > max_count:
        # The maximum number of tag filters is exceeded.
        # This can't not happen by accident, because we didn't insert
        # more tag filter links than allowed.
        raise SuspiciousOperation404(_("Too much tags given"))

    tag_list.sort()
    canonical = "/".join(tag_list)

    return tag_list, canonical


class RssFeed(Feed):
    feed_type = Rss201rev2Feed
    filename = "feed.rss"
    title = _("Blog - RSS feed")
    link = "/"
    description_template = "blog/feed_description.html"

    def __init__(self, request, tags=None):
        self.request = request
        # client favored Language instance:
        lang_entry = request.PYLUCID.current_language
        self.language = lang_entry.code

        if tags is None:
            self.tags = None
        else:
            tags_list, canonical = _split_tags(tags)
            if tags != canonical:
                raise Http404("No canonical url.") # Should we redirect? How?
            self.tags = tags_list

        # Get max number of feed entries from request.GET["count"]
        # Validate/Limit it with information from DBPreferences 
        self.count, error = safe_pref_get_integer(
            request, "count", BlogPrefForm,
            default_key="initial_feed_count", default_fallback=5,
            min_key="initial_feed_count", min_fallback=5,
            max_key="max_feed_count", max_fallback=30
        )

    def description(self):
        if self.tags is None:
            return _("Last %s blog articles") % self.count
        else:
            return _(
                 "Last %(count)s blog articles tagged with: %(tags)s"
            ) % {"count":self.count, "tags": ",".join(self.tags)}

    def items(self):
        queryset = BlogEntryContent.objects.get_prefiltered_queryset(self.request, tags=self.tags, filter_language=True)
        return queryset[:self.count]

    def item_title(self, item):
        return item.headline

    def item_author_name(self, item):
        return item.createby

    def item_link(self, item):
        return item.get_absolute_url()


class AtomFeed(RssFeed):
    """
    http://docs.djangoproject.com/en/dev/ref/contrib/syndication/#publishing-atom-and-rss-feeds-in-tandem
    """
    feed_type = Atom1Feed
    filename = "feed.atom"
    title = _("Blog - Atom feed")
    subtitle = RssFeed.description


FEEDS = (AtomFeed, RssFeed)
FEED_FILENAMES = (AtomFeed.filename, RssFeed.filename)



@render_to("blog/summary.html")
def summary(request):
    """
    Display summary list with all blog entries.
    """
    url = urlresolvers.reverse("Blog-summary")
    if url != request.path:
        # e.g.: request with wrong permalink: /en/blog/XXX/foobar-slug/
        return HttpResponseRedirect(url)

    # Get all blog entries, that the current user can see
    paginator = BlogEntryContent.objects.get_filtered_queryset(request, filter_language=True)

    # Calculate the tag cloud from all existing entries
    tag_cloud = BlogEntryContent.objects.get_tag_cloud(request)

    _add_breadcrumb(request, _("All articles."))

    # For adding page update information into context by pylucid context processor
    try:
        # Use the newest blog entry for date info
        request.PYLUCID.updateinfo_object = paginator.object_list[0]
    except IndexError:
        # No blog entries created, yet.
        pass

    context = {
        "entries": paginator,
        "tag_cloud": tag_cloud,
        "CSS_PLUGIN_CLASS_NAME": settings.PYLUCID.CSS_PLUGIN_CLASS_NAME,
        "filenames": FEED_FILENAMES,
        "page_robots": "noindex,follow",
    }
    return context


@render_to("blog/summary.html")
def tag_view(request, tags):
    """
    Display summary list with blog entries filtered by the given tags.
    """
    tag_list, canonical = _split_tags(tags)

    if tags != canonical:
        # Redirect to a canonical url
        # FIXME: The template should create links in a canonical way and not just +tag
        url = reverse('Blog-tag_view', kwargs={"tags":canonical})
        return HttpResponsePermanentRedirect(url)

    # Get all blog entries, that the current user can see
    paginator = BlogEntryContent.objects.get_filtered_queryset(request, tags=tag_list, filter_language=True)

    queryset = paginator.object_list
    if len(queryset) == 0:
        # There exist no blog entries for the given tags.
        # This can't happen by accident, because we didn't insert
        # tag filters without existing articles.
        raise Http404("No articles for the given tag filters")

    # Calculate the tag cloud from the current used queryset
    tag_cloud = BlogEntryContent.objects.cloud_for_queryset(queryset)

    # Add link to the breadcrumbs ;)
    text = _("All items tagged with: %s") % ", ".join(["'%s'" % tag for tag in tag_list])
    _add_breadcrumb(request, text)

    # For adding page update information into context by pylucid context processor
    try:
        # Use the newest blog entry for date info
        request.PYLUCID.updateinfo_object = paginator.object_list[0]
    except IndexError:
        # No blog entries created, yet.
        pass

    # Don't add links to tags, if the maximum tag filter count is reached:
    max_count = _get_max_tag_count()
    if len(tag_list) < max_count:
        add_tag_filter_link = True
    else:
        add_tag_filter_link = False

    context = {
        "entries": paginator,
        "tag_cloud": tag_cloud,
        "add_tag_filter_link": add_tag_filter_link,
        "CSS_PLUGIN_CLASS_NAME": settings.PYLUCID.CSS_PLUGIN_CLASS_NAME,
        "used_tags": tag_list,
        "tags": tags,
        "filenames": FEED_FILENAMES,
        "page_robots": "noindex,nofollow",
    }
    return context


@csrf_protect
@render_to("blog/detail_view.html")
def detail_view(request, year, month, day, slug):
    """
    Display one blog entry with a comment form.
    """
    # Get all blog entries, that the current user can see
    queryset = BlogEntryContent.objects.get_prefiltered_queryset(request, filter_language=False)

    filter_kwargs = {
        "createtime__year":year,
        "createtime__month":month,
        "createtime__day":day,
        "slug":slug,
    }
    current_language = request.PYLUCID.current_language
    content_entry = None
    tried_languages = None
    try:
        queryset = queryset.filter(**filter_kwargs)
        content_entry, tried_languages = BlogEntryContent.objects.get_by_prefered_language(
            request, queryset, show_lang_errors=False
        )
    except BlogEntryContent.DoesNotExist, err:
        # TODO: Try to find a entry in other language, if not exist: redirect to day_archive() ?
        # It's possible that the user comes from a external link.
        msg = _("Entry for this url doesn't exist.")
        if settings.DEBUG or request.user.is_superuser:
            msg += " Filter kwargs: %r - Error: %s" % (repr(filter_kwargs), err)

        raise Http404(msg)

    if tried_languages and (settings.DEBUG or request.user.is_superuser):
        messages.debug(request, "Not found in these languages: %s" % ",".join(tried_languages))

    # Add link to the breadcrumbs ;)
    _add_breadcrumb(request, content_entry.headline, _("Article '%s'") % content_entry.headline)

    # Calculate the tag cloud from all existing entries
    tag_cloud = BlogEntryContent.objects.get_tag_cloud(request)

    # Change permalink from the blog root page to this entry detail view
    permalink = content_entry.get_permalink(request)
    request.PYLUCID.context["page_permalink"] = permalink # for e.g. the HeadlineAnchor

    # Add comments in this view to the current blog entry and not to PageMeta
    request.PYLUCID.object2comment = content_entry

    # For adding page update information into context by pylucid context processor
    request.PYLUCID.updateinfo_object = content_entry

    context = {
        "page_title": content_entry.headline, # Change the global title with blog headline
        "entry": content_entry,
        "tag_cloud": tag_cloud,
        "CSS_PLUGIN_CLASS_NAME": settings.PYLUCID.CSS_PLUGIN_CLASS_NAME,
        "page_permalink": permalink, # Change the permalink in the global page template
    }
    return context

#------------------------------------------------------------------------------

def permalink_view(request, id, slug=None):
    """ redirect to language depent blog entry """
    prefiltered_queryset = BlogEntryContent.objects.get_prefiltered_queryset(request, filter_language=False)

    preferred_languages = request.PYLUCID.languages

    prefiltered_queryset = prefiltered_queryset.filter(entry__id__exact=id)
    try:
        entry = prefiltered_queryset.filter(language__in=preferred_languages)[0]
    except (BlogEntry.DoesNotExist, IndexError):
        # wrong permalink -> display summary
        msg = "Blog entry doesn't exist."
        if settings.DEBUG or request.user.is_staff:
            msg += " (ID %r wrong.)" % id
        messages.error(request, msg)
        return summary(request)

    url = entry.get_absolute_url()
    return HttpResponsePermanentRedirect(url)

#------------------------------------------------------------------------------

def redirect_old_urls(request, id, title):
    """ permanent redirect old url's to new url scheme """
    prefiltered_queryset = BlogEntryContent.objects.get_prefiltered_queryset(request, filter_language=False)

    try:
        entry = prefiltered_queryset.get(pk=id)
    except BlogEntry.DoesNotExist:
        # It's possible that the user comes from a external link.
        msg = "Blog entry doesn't exist."
        if settings.DEBUG or request.user.is_staff:
            msg += " (ID %r wrong.)" % id
        messages.error(request, msg)
        return summary(request)

    url = entry.get_absolute_url()
    return HttpResponsePermanentRedirect(url)


#------------------------------------------------------------------------------

# FIXME: Disallow empty archive pages in all archive views:

def year_archive(request, year):
    """
    Display year archive
    """
    year = int(year)

    # Add link to the breadcrumbs ;)
    _add_breadcrumb(request, _("%s archive") % year, _("All article from year %s") % year)

    context = {
        "CSS_PLUGIN_CLASS_NAME": settings.PYLUCID.CSS_PLUGIN_CLASS_NAME,
        "page_robots": "noindex,nofollow",
    }

    # Get next year
    now = datetime.datetime.now()
    if year < now.year:
        queryset = BlogEntryContent.objects.get_prefiltered_queryset(request, filter_language=False)
        next_year = datetime.datetime(year=year, month=12, day=31)
        try:
            entry_in_next_year = queryset.filter(createtime__gte=next_year).only("createtime").order_by("-createtime")[0]
        except IndexError:
            # no entries in next year
            pass
        else:
            context["next_year"] = entry_in_next_year.createtime.year

    # Get previous year
    queryset = BlogEntryContent.objects.get_prefiltered_queryset(request, filter_language=False)
    previous_year = datetime.datetime(year=year, month=1, day=1)
    try:
        entry_in_previous_year = queryset.filter(createtime__lte=previous_year).only("createtime").order_by("-createtime")[0]
    except IndexError:
        # no entries in previous year
        pass
    else:
        context["previous_year"] = entry_in_previous_year.createtime.year

    queryset = BlogEntryContent.objects.get_prefiltered_queryset(request, filter_language=False)
    return archive_year(
        request, year, queryset, date_field="createtime", extra_context=context,
        make_object_list=True,
        allow_empty=True
    )


def month_archive(request, year, month):
    """
    TODO: Set previous-/next-month by filtering
    """
    queryset = BlogEntryContent.objects.get_prefiltered_queryset(request, filter_language=False)

    # Add link to the breadcrumbs ;)
    _add_breadcrumb(request,
        _("%(month)s-%(year)s archive") % {"year":year, "month":month},
        _("All article from %(month)s.%(year)s") % {"year":year, "month":month}
    )

    context = {
        "CSS_PLUGIN_CLASS_NAME": settings.PYLUCID.CSS_PLUGIN_CLASS_NAME,
        "page_robots": "noindex,nofollow",
    }
    return archive_month(
        request, year, month, queryset, date_field="createtime", extra_context=context,
        month_format="%m", allow_empty=True
    )


def day_archive(request, year, month, day):
    """
    TODO: Set previous-/next-day by filtering
    """
    queryset = BlogEntryContent.objects.get_prefiltered_queryset(request, filter_language=False)

    # Add link to the breadcrumbs ;)
    _add_breadcrumb(request,
        _("%(day)s-%(month)s-%(year)s archive") % {"year":year, "month":month, "day":day},
        _("All article from %(day)s-%(month)s-%(year)s") % {"year":year, "month":month, "day":day}
    )

    context = {
        "CSS_PLUGIN_CLASS_NAME": settings.PYLUCID.CSS_PLUGIN_CLASS_NAME,
        "page_robots": "noindex,nofollow",
    }
    return archive_day(
        request, year, month, day, queryset, date_field="createtime", extra_context=context,
        month_format="%m", allow_empty=True
    )


#------------------------------------------------------------------------------


@render_to("blog/select_feed.html")
def select_feed(request):
    """
    Display a list with existing feed filenames.
    TODO: Set http robots ==> "noindex,follow"
    """
    context = {"filenames": FEED_FILENAMES}
    return context


def feed(request, filename, tags=None):
    """
    return RSS/Atom feed for all blog entries and filtered by tags. 
    Feed format is selected by filename.
    """
    for feed_class in FEEDS:
        if filename == feed_class.filename:
            break

    # client favoured Language instance:
    lang_entry = request.PYLUCID.current_language

    # Work-a-round for http://code.djangoproject.com/ticket/13896
    old_lang_code = settings.LANGUAGE_CODE
    settings.LANGUAGE_CODE = lang_entry.code

    feed = feed_class(request, tags)
    response = feed(request)

    settings.LANGUAGE_CODE = old_lang_code

    return response

