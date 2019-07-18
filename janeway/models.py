from django.db import models


class Author(models.Model):
    janeway_id = models.IntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=255)
    real_name = models.CharField(blank=True, max_length=255)
    real_name_hidden = models.BooleanField(default=False)
    is_group = models.BooleanField()
    country_code = models.CharField(max_length=5, blank=True)
    is_company = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Name(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='names')
    janeway_id = models.IntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255, blank=True)


class Membership(models.Model):
    group = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='member_memberships')
    member = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='group_memberships')
    since = models.DateField(blank=True, null=True)
    until = models.DateField(blank=True, null=True)
    founder = models.BooleanField(default=False)


SUPERTYPE_CHOICES = (
    ('production', 'Production'),
    ('graphics', 'Graphics'),
    ('music', 'Music'),
)

PLATFORM_CHOICES = (
    ('ocs', 'Amiga OCS/ECS'),
    ('aga', 'Amiga AGA'),
    ('ppc', 'Amiga PPC/RTG'),
)


class Release(models.Model):
    janeway_id = models.IntegerField(unique=True, db_index=True)
    title = models.CharField(max_length=255)
    supertype = models.CharField(max_length=20, choices=SUPERTYPE_CHOICES)
    author_names = models.ManyToManyField(Name, related_name='authored_releases')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, blank=True)


class ReleaseType(models.Model):
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name='types')
    type_name = models.CharField(max_length=255)


class Credit(models.Model):
    janeway_id = models.IntegerField(db_index=True)
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name='credits')
    name = models.ForeignKey(Name, on_delete=models.CASCADE, related_name='credits')
    category = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True)


class DownloadLink(models.Model):
    janeway_id = models.IntegerField(unique=True, db_index=True)
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name='download_links')
    url = models.URLField(max_length=255)
    comment = models.TextField(blank=True)


class PackContent(models.Model):
    pack = models.ForeignKey(Release, on_delete=models.CASCADE, related_name='pack_contents')
    content = models.ForeignKey(Release, on_delete=models.CASCADE, related_name='packed_in')


class SoundtrackLink(models.Model):
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name='soundtrack_links')
    soundtrack = models.ForeignKey(Release, on_delete=models.CASCADE, related_name='appearances_as_soundtrack')
